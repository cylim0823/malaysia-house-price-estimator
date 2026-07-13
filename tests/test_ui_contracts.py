import unittest
from datetime import date
from pathlib import Path

from house_price_estimator.bundle import PredictionBundle
from house_price_estimator.data_pipeline import AggregateTransactionBundle
from house_price_estimator.prediction import (
    SyntheticPropertyDemoService,
    limited_recency_message,
)
from house_price_estimator.ui_contracts import (
    AGGREGATE_PREDICTION_FIELDS,
    INDIVIDUAL_PROPERTY_FIELDS,
    aggregate_prediction_payload,
    build_information_disclosure,
    individual_field_visibility,
    normalize_individual_submission,
)


ROOT = Path(__file__).parents[1]


class AggregateUiContractTests(unittest.TestCase):
    def test_aggregate_payload_uses_only_supported_features(self):
        values = {
            "state": "Penang",
            "district": "Barat Daya",
            "property_type": "detached",
            "year": 2017,
            "quarter": 1,
        }
        payload = aggregate_prediction_payload(values)
        self.assertEqual(set(payload), AGGREGATE_PREDICTION_FIELDS)
        property_only_fields = set(INDIVIDUAL_PROPERTY_FIELDS) - AGGREGATE_PREDICTION_FIELDS
        self.assertTrue(property_only_fields.isdisjoint(payload))

    def test_unsupported_property_field_is_not_silently_ignored(self):
        values = {
            "state": "Penang",
            "district": "Barat Daya",
            "property_type": "detached",
            "year": 2017,
            "quarter": 1,
            "built_up_sqft": 1200,
        }
        with self.assertRaisesRegex(ValueError, "Unsupported aggregate fields: built_up_sqft"):
            aggregate_prediction_payload(values)

    def test_missing_aggregate_field_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Missing aggregate fields: quarter"):
            aggregate_prediction_payload(
                {
                    "state": "Penang",
                    "district": "Barat Daya",
                    "property_type": "detached",
                    "year": 2017,
                }
            )

    def test_existing_aggregate_result_is_unchanged(self):
        bundle = AggregateTransactionBundle.load(
            ROOT / "models" / "real" / "aggregate_transaction_bundle.pkl"
        )
        result = bundle.predict(
            **aggregate_prediction_payload(
                {
                    "state": "Penang",
                    "district": "Barat Daya",
                    "property_type": "one_to_one_half_storey_semi_detached",
                    "year": 2017,
                    "quarter": 1,
                }
            )
        )
        self.assertEqual(result["observed_average_price_rm"], 730000.0)
        self.assertEqual(result["transaction_count"], 1)
        self.assertIsNone(result["estimated_average_price_rm"])

    def test_property_specific_visibility_never_uses_zero_for_not_applicable(self):
        high_rise = individual_field_visibility("Condominium")
        landed = individual_field_visibility("Terraced House")
        self.assertFalse(high_rise["land_area_sqft"])
        self.assertFalse(high_rise["storeys"])
        self.assertTrue(high_rise["floor_level"])
        self.assertTrue(landed["land_area_sqft"])
        self.assertTrue(landed["storeys"])
        self.assertFalse(landed["floor_level"])
        self.assertTrue(all(isinstance(value, bool) for value in high_rise.values()))

    def test_complete_individual_contract_and_blank_optionals(self):
        expected = {
            "state", "district", "city", "township", "project_name",
            "property_type", "property_subtype", "built_up_sqft",
            "land_area_sqft", "bedrooms", "additional_bedrooms", "bathrooms",
            "car_parks", "storeys", "floor_level", "tenure", "furnishing",
            "completion_year", "property_age_years", "renovation_status",
            "property_condition", "asking_price",
        }
        self.assertEqual(set(INDIVIDUAL_PROPERTY_FIELDS), expected)
        submission = normalize_individual_submission(
            {"state": "Penang", "property_type": "Condominium"}
        )
        self.assertEqual(submission.statuses["district"], "unknown")
        self.assertEqual(submission.statuses["land_area_sqft"], "not_applicable")
        self.assertIsNone(submission.values["district"])
        self.assertIsNone(submission.values["land_area_sqft"])

    def test_zero_is_provided_and_residential_rules_are_enforced(self):
        studio = normalize_individual_submission(
            {
                "state": "Penang",
                "property_type": "Studio",
                "bedrooms": 0,
                "car_parks": 0,
                "floor_level": 0,
            }
        )
        self.assertEqual(studio.statuses["bedrooms"], "provided")
        self.assertEqual(studio.statuses["car_parks"], "provided")
        self.assertEqual(studio.values["floor_level"], 0)
        with self.assertRaisesRegex(ValueError, "Zero bedrooms"):
            normalize_individual_submission(
                {"state": "Penang", "property_type": "Condominium", "bedrooms": 0}
            )
        with self.assertRaisesRegex(ValueError, "Bathrooms must be greater"):
            normalize_individual_submission(
                {"state": "Penang", "property_type": "Condominium", "bathrooms": 0}
            )

    def test_provided_but_unused_information_is_disclosed(self):
        submission = normalize_individual_submission(
            {
                "state": "Penang",
                "property_type": "Terraced House",
                "city": "George Town",
                "car_parks": 0,
            }
        )
        disclosure = build_information_disclosure(
            submission, model_features={"state", "property_type"}
        )
        self.assertIn("City or township", disclosure.provided_but_not_used)
        self.assertIn("Car parks", disclosure.provided_but_not_used)
        self.assertIn("Floor level", disclosure.not_applicable)

    def test_synthetic_demo_accepts_missing_optionals_and_discloses_true_features(self):
        bundle = PredictionBundle.load(
            ROOT / "models" / "demo" / "demo_bundle.pkl", trusted=True
        )
        service = SyntheticPropertyDemoService(bundle)
        submission = normalize_individual_submission(
            {"state": "Penang", "property_type": "Condominium", "city": "George Town"}
        )
        result = service.predict(submission)
        self.assertGreater(result.estimate, 0)
        self.assertIn("built_up_sqft", result.model_features)
        self.assertIn("City or township", result.disclosure.provided_but_not_used)
        self.assertIn("Built-up area", result.disclosure.missing_optional)
        self.assertTrue(result.synthetic_segment.startswith("Fictional Segment"))

    def test_old_data_warning_uses_selected_segment_latest_period(self):
        self.assertEqual(
            limited_recency_message((2018, 2), as_of=date(2026, 7, 13)),
            "Limited recency: the latest validated data for this selection is from 2018 Q2.",
        )
        self.assertIsNone(
            limited_recency_message((2026, 1), as_of=date(2026, 7, 13))
        )


if __name__ == "__main__":
    unittest.main()
