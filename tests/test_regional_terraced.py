"""Tests for nationwide area-level terraced benchmarks."""
from pathlib import Path
import tempfile
import unittest

from house_price_estimator.regional_terraced import (
    RegionalTerracedBundle,
    load_regional_terraced_prices,
    train_regional_terraced_model,
)


ROOT = Path(__file__).parents[1]


class RegionalTerracedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_regional_terraced_prices(
            ROOT / "data" / "external" / "napic_open_data" / "terraced_by_district.xlsx"
        )
        cls.bundle, cls.report = train_regional_terraced_model(cls.data)

    def test_all_source_states_and_areas_are_normalized(self):
        self.assertEqual(len(self.data), 460)
        self.assertEqual(len(self.bundle.states), 14)
        self.assertEqual(sum(len(value) for value in self.bundle.areas_by_state.values()), 46)
        self.assertEqual(set(self.data["year"]), {2016, 2017, 2018})
        self.assertTrue((self.data["average_price_rm"] > 0).all())
        self.assertIn("Penang", self.bundle.states)

    def test_model_beats_area_median_on_untouched_2018(self):
        self.assertEqual(self.report["selected_model"], "log_ridge")
        self.assertLess(
            self.report["model"]["mae_rm"],
            self.report["area_median_baseline"]["mae_rm"],
        )

    def test_prediction_round_trip_and_unsupported_area(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "regional.pkl"
            self.bundle.save(path)
            loaded = RegionalTerracedBundle.load(path)
            result = loaded.predict(
                state="Selangor", area="Petaling", year=2018, quarter=2
            )
            self.assertGreater(result["observed_average"], 0)
            self.assertLess(result["lower"], result["upper"])
            with self.assertRaises(ValueError):
                loaded.predict(
                    state="Selangor", area="Unknown", year=2018, quarter=2
                )


if __name__ == "__main__":
    unittest.main()
