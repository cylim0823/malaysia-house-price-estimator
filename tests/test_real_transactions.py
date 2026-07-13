"""Tests for the real NAPIC transaction preparation and bundle contract."""

from __future__ import annotations

from pathlib import Path
import unittest

import pandas as pd

from house_price_estimator.real_transactions import RealPropertyBundle, prepare_real_transactions


class RealTransactionPreparationTests(unittest.TestCase):
    def test_duplicates_are_grouped_before_modelling_and_raw_values_remain(self):
        row = {
            "state": "Johor", "district": "Johor Bahru", "district_raw": "Johor Bahru",
            "mukim_raw": "Bandar", "property_type": "Detached", "property_type_raw": "Detached",
            "road_name_raw": "Jalan A", "scheme_name_area_raw": "Taman A", "tenure_raw": "Freehold",
            "transaction_month_raw": "January 2024", "transaction_price_rm_raw": "500000",
            "land_parcel_area_raw": "100", "main_floor_area_raw": "80", "unit_level_raw": "-",
            "transaction_price_rm": 500000.0, "land_parcel_area_sqm": 100.0,
            "main_floor_area_sqm": 80.0, "unit_level": None, "tenure": "Freehold",
            "transaction_date": pd.Timestamp("2024-01-01"), "validation_status": "imported_unvalidated",
        }
        prepared, report = prepare_real_transactions(pd.DataFrame([row, row]))
        self.assertEqual(report["exact_duplicate_rows"], 2)
        self.assertEqual(prepared["duplicate_group_id"].nunique(), 1)
        self.assertEqual(int(prepared["model_eligible"].sum()), 1)
        self.assertEqual(prepared.iloc[1]["model_exclusion_reason"], "exact_duplicate_noncanonical")
        self.assertEqual(prepared.iloc[0]["transaction_price_rm_raw"], "500000")

    def test_repository_real_bundle_predicts_only_supported_segments(self):
        bundle = RealPropertyBundle.load(
            Path(__file__).parents[1] / "models" / "real" / "napic_property_bundle.pkl"
        )
        self.assertEqual(len(bundle.states), 16)
        district = bundle.districts("Penang")[0]
        property_type = bundle.property_types("Penang", district)[0]
        result = bundle.predict(
            {"state": "Penang", "district": district, "property_type": property_type}
        )
        self.assertGreater(result.estimate, 0)
        self.assertLessEqual(result.lower, result.upper)
        with self.assertRaisesRegex(ValueError, "Unsupported"):
            bundle.predict(
                {"state": "Penang", "district": "Atlantis", "property_type": property_type}
            )


if __name__ == "__main__":
    unittest.main()
