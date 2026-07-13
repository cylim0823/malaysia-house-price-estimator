"""Coverage for the licensed JPPH historical-average workflow."""
from pathlib import Path
import tempfile
import unittest

from house_price_estimator.official_averages import (
    OfficialAverageBundle,
    load_official_average_prices,
    train_official_average_model,
)


ROOT = Path(__file__).parents[1]


class OfficialAverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_official_average_prices(ROOT / "data" / "external" / "napic")
        cls.bundle, cls.report = train_official_average_model(cls.data)

    def test_official_workbooks_are_normalized(self):
        self.assertEqual(len(self.data), 2090)
        self.assertEqual(int(self.data["year"].min()), 2009)
        self.assertEqual(int(self.data["year"].max()), 2018)
        self.assertTrue((self.data["average_price_rm"] > 0).all())
        self.assertIn("Penang", set(self.data["state"]))

    def test_train_save_load_predict_and_reject_unsupported(self):
        self.assertLess(
            self.report["model"]["mae_rm"],
            self.report["overall_median_baseline"]["mae_rm"],
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "official.pkl"
            self.bundle.save(path)
            loaded = OfficialAverageBundle.load(path)
            result = loaded.predict(
                state="Selangor", property_type="Terraced house", year=2018, quarter=2
            )
            self.assertGreater(result["estimate"], 0)
            self.assertLess(result["lower"], result["upper"])
            with self.assertRaises(ValueError):
                loaded.predict(
                    state="Putrajaya", property_type="Terraced house", year=2018, quarter=2
                )
            with self.assertRaises(ValueError):
                loaded.predict(
                    state="Selangor", property_type="Terraced house", year=2026, quarter=1
                )


if __name__ == "__main__":
    unittest.main()
