"""Tests for the separate aggregate completed-transaction workflow."""
from pathlib import Path
import tempfile
import unittest

import pandas as pd

from house_price_estimator.data_pipeline import (
    AggregateTransactionBundle,
    aggregate_property_type,
    FORBIDDEN_MODEL_FEATURES,
    MODEL_FEATURES,
    WeightedMeanBaseline,
    load_and_validate_aggregate_csv,
    normalize_aggregate_property_type,
    normalize_district,
    train_aggregate_baselines,
    validate_aggregate_frame,
    volume_support,
    weighted_regression_metrics,
)


ROOT = Path(__file__).parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "aggregate_transactions_small.csv"


class AggregateValidationTests(unittest.TestCase):
    def test_csv_import_arithmetic_and_normalisation(self):
        result = load_and_validate_aggregate_csv(FIXTURE)
        self.assertEqual(len(result.processed), 8)
        self.assertEqual(len(result.rejected), 0)
        first = result.processed.iloc[0]
        self.assertEqual(first["district_raw"], "Timur Laut (George Town / northeast island)")
        self.assertEqual(first["district"], "Timur Laut")
        self.assertEqual(first["district_notes"], "George Town / northeast island")
        self.assertEqual(first["property_type"], "flat")
        self.assertEqual(result.quality_report["arithmetic_mismatch_rows"], 0)
        self.assertEqual(result.quality_report["sum_of_transaction_count"], 120)
        self.assertEqual(
            result.quality_report["earliest_period"], {"year": 2017, "quarter": 1}
        )
        self.assertEqual(
            result.quality_report["latest_period"], {"year": 2017, "quarter": 4}
        )
        self.assertEqual(result.quality_report["missing_years"], [])
        self.assertEqual(result.quality_report["missing_quarters"], [])
        self.assertIn("missing_state_period_combinations", result.quality_report)
        self.assertIn("very_low_transaction_volume_rows", result.quality_report)
        self.assertEqual(result.quality_report["extraction_warning_count"], 0)

    def test_source_metadata_is_injected_without_state_specific_core_defaults(self):
        result = load_and_validate_aggregate_csv(
            FIXTURE,
            metadata={
                "source_name": "Approved test source",
                "source_dataset": "test-dataset",
                "dataset_version": "test-v1",
                "source_document": "Test document",
            },
        )
        first = result.processed.iloc[0]
        self.assertEqual(first["source_name"], "Approved test source")
        self.assertEqual(first["source_dataset"], "test-dataset")
        self.assertEqual(first["dataset_version"], "test-v1")
        self.assertIn("warnings", first["validation_notes"])

    def test_required_columns_and_controlled_property_type(self):
        with self.assertRaisesRegex(ValueError, "missing required"):
            validate_aggregate_frame(pd.DataFrame({"state": ["Penang"]}))
        self.assertEqual(normalize_aggregate_property_type("Low-Cost Flat"), "low_cost_flat")
        unknown = aggregate_property_type("Made Up Type")
        self.assertFalse(unknown.known)
        self.assertEqual(unknown.raw_value, "Made Up Type")
        self.assertEqual(unknown.property_type_label, "Made up type")
        self.assertEqual(normalize_aggregate_property_type("Made Up Type"), "other_made_up_type")

    def test_property_type_catalog_preserves_raw_code_and_friendly_label(self):
        definition = aggregate_property_type("1 - 1 1/2 Storey Semi-Detached")
        self.assertEqual(definition.raw_value, "1 - 1 1/2 Storey Semi-Detached")
        self.assertEqual(definition.property_type_code, "semi_detached_1_to_1_5_storey")
        self.assertEqual(definition.property_type_label, "1–1½-storey semi-detached house")

    def test_invalid_values_duplicates_and_mismatch_are_preserved(self):
        frame = pd.read_csv(FIXTURE).iloc[:2].copy()
        duplicate = frame.iloc[[0]].copy()
        bad = frame.iloc[[1]].copy()
        bad["state"] = "Unknown"
        bad["quarter"] = 5
        bad["average_price_rm"] = 1
        result = validate_aggregate_frame(pd.concat([frame, duplicate, bad], ignore_index=True))
        codes = " ".join(result.rejected["validation_errors"])
        self.assertIn("DUPLICATE_AGGREGATE_ROW", codes)
        self.assertIn("UNKNOWN_STATE", codes)
        self.assertIn("INVALID_QUARTER", codes)
        self.assertIn("AVERAGE_CALCULATION_MISMATCH", codes)

    def test_missing_and_nonpositive_fields_are_rejected_with_codes(self):
        bad = pd.read_csv(FIXTURE).iloc[[0]].copy()
        bad["district"] = ""
        bad["property_type"] = ""
        bad["transaction_count"] = 0
        bad["transaction_value_rm"] = -1
        bad["average_price_rm"] = 0
        bad["price_type"] = "asking"
        result = validate_aggregate_frame(bad)
        codes = result.rejected.iloc[0]["validation_errors"]
        for expected in (
            "MISSING_DISTRICT",
            "MISSING_PROPERTY_TYPE",
            "INVALID_TRANSACTION_COUNT",
            "INVALID_TRANSACTION_VALUE",
            "INVALID_AVERAGE_PRICE",
            "INVALID_PRICE_TYPE",
        ):
            self.assertIn(expected, codes)

    def test_volume_flags_and_district_without_annotation(self):
        self.assertEqual(volume_support(1), "very_low_volume")
        self.assertEqual(volume_support(5), "low_volume")
        self.assertEqual(volume_support(20), "medium_volume")
        self.assertEqual(volume_support(100), "high_volume")
        self.assertEqual(normalize_district("Seberang Perai Tengah"), ("Seberang Perai Tengah", None))


class AggregateModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.processed = load_and_validate_aggregate_csv(FIXTURE).processed
        cls.bundle, cls.report = train_aggregate_baselines(cls.processed)

    def test_target_leakage_contract(self):
        self.assertEqual(
            set(self.report["model_features"]),
            {"state", "district", "property_type", "year", "quarter"},
        )
        self.assertTrue(FORBIDDEN_MODEL_FEATURES.isdisjoint(MODEL_FEATURES))
        self.assertEqual(self.report["sample_weight"], "transaction_count")

    def test_weighted_average_and_metrics(self):
        model = WeightedMeanBaseline(()).fit(self.processed.iloc[:2])
        expected = (200000 * 10 + 210000 * 12) / 22
        self.assertAlmostEqual(float(model.predict(self.processed.iloc[:1])[0]), expected)
        metrics = weighted_regression_metrics([100, 200], [90, 150], [1, 9])
        self.assertAlmostEqual(metrics["mae_rm"], 30)
        self.assertAlmostEqual(metrics["weighted_mae_rm"], 46)

    def test_time_safe_split_and_bundle_round_trip(self):
        self.assertEqual(self.report["split_strategy"], "train_2017_q1_q3_test_2017_q4")
        self.assertEqual(self.report["advanced_models_trained"], [])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "aggregate.pkl"
            self.bundle.save(path)
            loaded = AggregateTransactionBundle.load(path)
            result = loaded.predict(
                state="Penang", district="Timur Laut", property_type="flat", year=2017, quarter=4
            )
            self.assertEqual(result["transaction_count"], 20)
            self.assertIsNotNone(result["estimated_average_price_rm"])
            self.assertIn("not a specific property's value", result["prediction_meaning"])

    def test_unsupported_state_and_period_are_rejected(self):
        with self.assertRaises(ValueError):
            self.bundle.predict(
                state="Johor", district="Timur Laut", property_type="flat", year=2017, quarter=4
            )
        with self.assertRaises(ValueError):
            self.bundle.predict(
                state="Penang", district="Timur Laut", property_type="flat", year=2026, quarter=1
            )

    def test_low_volume_history_is_retained_without_public_prediction_support(self):
        result = self.bundle.predict(
            state="Penang",
            district="Seberang Perai Tengah",
            property_type="detached",
            year=2017,
            quarter=1,
        )
        self.assertEqual(result["transaction_count"], 2)
        self.assertFalse(result["public_prediction_supported"])
        self.assertIsNone(result["estimated_average_price_rm"])


if __name__ == "__main__":
    unittest.main()
