"""Tests for nationwide location readiness and metadata-driven coverage."""

from pathlib import Path
import tempfile
import unittest

import pandas as pd

from house_price_estimator.data_sources import (
    CsvAggregateAdapter,
    load_dataset_metadata,
    load_historical_bundle,
)
from house_price_estimator.data_pipeline import validate_aggregate_frame
from house_price_estimator.location_catalog import (
    CoverageCatalog,
    MALAYSIAN_STATES,
    normalize_state,
)
from house_price_estimator.prediction import HistoricalExplorer


ROOT = Path(__file__).parents[1]


class LocationCatalogTests(unittest.TestCase):
    def test_all_states_and_federal_territories_are_canonical(self):
        self.assertEqual(len(MALAYSIAN_STATES), 16)
        self.assertEqual({normalize_state(value) for value in MALAYSIAN_STATES}, set(MALAYSIAN_STATES))
        self.assertEqual(normalize_state("Pulau Pinang"), "Penang")
        self.assertEqual(normalize_state("W.P. Labuan"), "Labuan")

    def test_coverage_options_follow_actual_combinations(self):
        coverage = CoverageCatalog.from_observation_keys(
            {
                "Johor|Johor Bahru|terraced_house|2024|4": 1,
                "Johor|Muar|terraced_house|2023|2": 1,
                "Sabah|Kota Kinabalu|high_rise|2024|1": 1,
            }
        )
        self.assertEqual(coverage.states, ("Johor", "Sabah"))
        self.assertEqual(coverage.areas("Johor"), ("Johor Bahru", "Muar"))
        self.assertEqual(coverage.years("Johor", "Muar", "terraced_house"), (2023,))
        self.assertEqual(coverage.quarters("Sabah", "Kota Kinabalu", "high_rise", 2024), (1,))
        with self.assertRaises(ValueError):
            coverage.quarters("Johor", "Muar", "terraced_house", 2024)

    def test_repository_catalog_and_legacy_bundles_share_generic_contract(self):
        metadata = load_dataset_metadata(ROOT / "data" / "processed" / "dataset_catalog.json")
        self.assertEqual(len(metadata), 2)
        explorers = [
            HistoricalExplorer(item, load_historical_bundle(item, ROOT)) for item in metadata
        ]
        self.assertEqual(explorers[0].coverage.states, ("Penang",))
        self.assertIn("Selangor", explorers[1].coverage.states)
        self.assertNotIn("Putrajaya", explorers[1].coverage.states)
        for explorer in explorers:
            self.assertTrue(explorer.metadata.licence_status)
            self.assertTrue(explorer.metadata.redistribution_allowed)

    def test_new_state_csv_uses_generic_adapter_and_pipeline(self):
        metadata = load_dataset_metadata(
            ROOT / "data" / "processed" / "dataset_catalog.json"
        )[0]
        frame = pd.read_csv(ROOT / "tests" / "fixtures" / "aggregate_transactions_small.csv")
        frame["state"] = "Johor"
        frame["district"] = "Johor Bahru"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "approved_johor.csv"
            frame.to_csv(path, index=False)
            loaded = CsvAggregateAdapter(path, metadata).load()
        result = validate_aggregate_frame(
            loaded,
            metadata={
                "source_name": metadata.source_name,
                "source_dataset": "approved-johor-test",
                "dataset_version": "approved-johor-test-v1",
            },
        )
        self.assertEqual(result.quality_report["states"], ["Johor"])
        self.assertEqual(result.quality_report["districts"], ["Johor Bahru"])


if __name__ == "__main__":
    unittest.main()
