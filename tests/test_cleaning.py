from copy import deepcopy
from decimal import Decimal
import unittest

from house_price_estimator.cleaning.normalization import normalize_state
from house_price_estimator.cleaning.parsers import parse_area_sqft, parse_ringgit, parse_room_count, parse_rooms
from house_price_estimator.cleaning.pipeline import clean_records


class ParserTests(unittest.TestCase):
    def test_ringgit_formats(self):
        self.assertEqual(parse_ringgit("RM650k"), Decimal("650000.00"))
        self.assertEqual(parse_ringgit("RM 650,000"), Decimal("650000.00"))
        self.assertEqual(parse_ringgit(650000), Decimal("650000.00"))
        self.assertEqual(parse_ringgit("RM 1.2 million"), Decimal("1200000.00"))

    def test_ringgit_rejects_malformed(self):
        with self.assertRaises(ValueError):
            parse_ringgit("about RM650k")

    def test_area_conversion_and_unit_requirement(self):
        self.assertEqual(parse_area_sqft("100 sqm"), Decimal("1076.39"))
        self.assertEqual(parse_area_sqft("0.25 acre"), Decimal("10890.00"))
        self.assertEqual(parse_area_sqft("0.1 hectare"), Decimal("10763.91"))
        with self.assertRaises(ValueError):
            parse_area_sqft("100")

    def test_auxiliary_bedroom_is_not_full_bedroom(self):
        self.assertEqual(parse_room_count("4+1"), 4)
        self.assertEqual(parse_room_count("4+1", include_auxiliary=True), 5)
        self.assertEqual(parse_rooms("3 + 1"), (3, 1))
        self.assertEqual(parse_rooms("Studio"), (0, 0))
        self.assertEqual(parse_rooms("N/A"), (None, None))

    def test_state_alias(self):
        self.assertEqual(normalize_state("W.P. Kuala Lumpur"), "Kuala Lumpur")
        self.assertEqual(normalize_state("KL"), "Kuala Lumpur")
        self.assertEqual(normalize_state("N. Sembilan"), "Negeri Sembilan")


class PipelineTests(unittest.TestCase):
    def record(self, record_id="demo-1"):
        return {
            "record_id": record_id, "source_name": "synthetic_test_fixture",
            "price": "RM650k", "price_type": "asking", "state": "Selangor",
            "district": "Hulu Langat", "project_name": "Test Residence",
            "property_type": "condo", "built_up_area": "1000", "built_up_unit": "sqft",
            "bedrooms": "4+1", "bathrooms": "2", "tenure": "freehold",
        }

    def test_pipeline_preserves_raw_and_groups_duplicates(self):
        records = [self.record(), self.record("demo-2")]
        original = deepcopy(records)
        result = clean_records(records, dataset_version="synthetic-test-1")
        self.assertEqual(records, original)
        self.assertEqual(result.quality_report["duplicate_copy_count"], 1)
        self.assertTrue(result.accepted_records[0]["is_canonical_record"])
        self.assertFalse(result.accepted_records[1]["is_model_eligible"])

    def test_rejected_record_is_retained_with_reason(self):
        record = self.record()
        record["price"] = "unknown"
        result = clean_records([record], dataset_version="synthetic-test-1")
        self.assertEqual(len(result.rejected_records), 1)
        self.assertEqual(result.rejected_records[0]["raw_record"], record)
        self.assertIn("invalid ringgit", result.rejected_records[0]["rejection_reasons"][0])

    def test_quality_report_has_state_and_district_coverage(self):
        result = clean_records([self.record()], dataset_version="synthetic-test-1")
        self.assertEqual(result.quality_report["coverage_by_state"], {"Selangor": 1})
        self.assertEqual(result.quality_report["coverage_by_state_and_district"], {"Selangor|Hulu Langat": 1})

    def test_missing_required_field_is_rejected(self):
        record = self.record()
        record["state"] = None
        result = clean_records([record], dataset_version="synthetic-test-1")
        self.assertEqual(result.quality_report["rejected_count"], 1)


if __name__ == "__main__":
    unittest.main()
