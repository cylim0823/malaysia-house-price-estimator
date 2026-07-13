"""Tests for the combined regional area-price dataset and model."""
from pathlib import Path
import tempfile
import unittest

from house_price_estimator.regional_area import (
    RegionalAreaBundle,
    load_regional_area_prices,
    train_regional_area_model,
)


ROOT = Path(__file__).parents[1]


class RegionalAreaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = ROOT / "data" / "external" / "napic_open_data"
        cls.data = load_regional_area_prices(
            source / "terraced_by_district.xlsx",
            source / "highrise_by_district.xlsx",
        )
        cls.bundle, cls.report = train_regional_area_model(cls.data)

    def test_combines_only_verified_source_rows(self):
        self.assertEqual(len(self.data), 600)
        self.assertEqual(self.report["rows_by_property_type"]["Terraced house"], 460)
        self.assertEqual(self.report["rows_by_property_type"]["High-rise unit"], 140)
        self.assertEqual(len(self.bundle.states), 14)
        self.assertNotIn("Malaysia", set(self.data["state"]))
        self.assertTrue((self.data["average_price_rm"] > 0).all())

    def test_model_is_compared_with_identical_holdout_baseline(self):
        self.assertEqual(self.report["test_period"], "2018 Q1-Q2")
        self.assertLessEqual(
            self.report["model"]["mae_rm"],
            self.report["location_property_median_baseline"]["mae_rm"],
        )

    def test_type_coverage_is_strict_and_bundle_round_trips(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "regional-area.pkl"
            self.bundle.save(path)
            loaded = RegionalAreaBundle.load(path)
            result = loaded.predict(
                state="Selangor",
                area="Petaling",
                property_type="High-rise unit",
                year=2018,
                quarter=2,
            )
            self.assertGreater(result["observed_average"], 0)
            self.assertLess(result["lower"], result["upper"])
            with self.assertRaises(ValueError):
                loaded.predict(
                    state="Perak",
                    area="Kinta/Ipoh",
                    property_type="High-rise unit",
                    year=2018,
                    quarter=2,
                )


if __name__ == "__main__":
    unittest.main()
