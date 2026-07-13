import unittest
from pathlib import Path

from house_price_estimator.aggregate_transactions import AggregateTransactionBundle
from house_price_estimator.ui_contracts import (
    AGGREGATE_PREDICTION_FIELDS,
    INDIVIDUAL_PROPERTY_FIELDS,
    aggregate_prediction_payload,
    individual_field_visibility,
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


if __name__ == "__main__":
    unittest.main()
