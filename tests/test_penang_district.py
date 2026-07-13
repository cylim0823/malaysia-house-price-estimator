"""Tests for the licensed Penang district transaction workflow."""
from pathlib import Path
import tempfile
import unittest

from house_price_estimator.penang_district import (
    PenangDistrictBundle,
    load_penang_district_transactions,
    train_penang_district_model,
)


ROOT = Path(__file__).parents[1]


class PenangDistrictTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_penang_district_transactions(
            ROOT / "data" / "external" / "penang_open_data"
        )
        cls.bundle, cls.report = train_penang_district_model(cls.data)

    def test_counts_and_values_create_completed_transaction_averages(self):
        self.assertEqual(len(self.data), 212)
        self.assertEqual(set(self.data["year"]), {2017})
        self.assertEqual(len(set(self.data["district"])), 5)
        self.assertTrue((self.data["transaction_count"] > 0).all())
        self.assertTrue((self.data["average_price_rm"] > 0).all())
        self.assertTrue(
            (self.data["price_type"] == "completed_transaction_average").all()
        )

    def test_simple_model_is_selected_and_prediction_has_traceability(self):
        self.assertEqual(self.report["selected_model"], "district_property_type_median")
        self.assertLess(
            self.report["model"]["mae_rm"],
            self.report["log_ridge"]["mae_rm"],
        )
        result = self.bundle.predict(
            district="Timur Laut (George Town / northeast island)",
            property_type="Condominium/Apartment",
            quarter=4,
        )
        self.assertGreater(result["observed_average"], 0)
        self.assertGreater(result["transaction_count"], 0)
        self.assertLess(result["lower"], result["upper"])

    def test_bundle_round_trip_and_unsupported_area(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "penang.pkl"
            self.bundle.save(path)
            loaded = PenangDistrictBundle.load(path)
            with self.assertRaises(ValueError):
                loaded.predict(
                    district="Unknown",
                    property_type="Condominium/Apartment",
                    quarter=1,
                )


if __name__ == "__main__":
    unittest.main()
