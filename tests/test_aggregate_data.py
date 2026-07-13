"""Multi-state tests for generic aggregate ingestion and annual benchmarks."""

from pathlib import Path
import tempfile
import unittest

import pandas as pd
from openpyxl import Workbook

from house_price_estimator.aggregate_data import (
    AggregateBenchmarkService,
    GENERIC_AGGREGATE_COLUMNS,
    STATE_LEVEL,
    build_coverage_catalog,
    classify_year,
)
from house_price_estimator.source_adapters.napic_excel import NapicExcelImporter


def record(
    state: str, district: str, property_type: str, year: int, quarter: int,
    count: int, value: float,
) -> dict[str, object]:
    period = pd.Period(year=year, quarter=quarter, freq="Q")
    values = {
        "state": state, "district": district, "district_notes": "",
        "property_type": property_type, "year": year, "period_type": "quarter",
        "period_number": quarter, "period_start": period.start_time.date().isoformat(),
        "period_end": period.end_time.date().isoformat(), "transaction_count": count,
        "transaction_value_rm": value, "average_price_rm": value / count,
        "price_type": "completed_transaction_average", "source_name": "Official test source",
        "source_dataset": "fixture", "source_file": f"{state}.csv", "source_sheet": "",
        "source_url": "https://example.test", "source_document": "fixture",
        "source_table": "fixture", "retrieved_at": "2026-07-13T00:00:00Z",
        "dataset_version": "fixture-v1", "schema_version": "aggregate-2.0.0",
        "validation_status": "valid", "validation_errors": "[]",
        "validation_warnings": "[]",
    }
    return {column: values[column] for column in GENERIC_AGGREGATE_COLUMNS}


class AggregateBenchmarkTests(unittest.TestCase):
    def test_preserved_2017_quarter_value_is_numerically_unchanged(self):
        frame = pd.read_csv(
            Path(__file__).parents[1] / "data" / "processed" / "aggregate_transactions"
            / "malaysia_aggregate_transactions_v1.csv"
        )
        row = frame[
            frame["state"].eq("Penang")
            & frame["district"].eq("Barat Daya")
            & frame["property_type"].eq("one_to_one_half_storey_semi_detached")
            & frame["year"].eq(2017)
            & frame["period_number"].eq(1)
        ].iloc[0]
        self.assertEqual(row["average_price_rm"], 730_000)
        self.assertEqual(row["transaction_count"], 1)

    def test_dynamic_multi_state_selectors_and_weighted_year(self):
        frame = pd.DataFrame([
            record("Johor", "Johor Bahru", "terraced", 2025, 1, 1, 100_000),
            record("Johor", "Johor Bahru", "terraced", 2025, 2, 9, 2_700_000),
            record("Johor", "Johor Bahru", "terraced", 2025, 3, 5, 1_500_000),
            record("Johor", "Johor Bahru", "terraced", 2025, 4, 5, 2_000_000),
            record("Selangor", "Petaling", "condominium", 2024, 1, 3, 1_800_000),
            record("Sabah", "Kota Kinabalu", "terraced", 2024, 1, 2, 800_000),
            record("Kuala Lumpur", "Kuala Lumpur", "condominium", 2026, 1, 4, 3_200_000),
        ])
        service = AggregateBenchmarkService(frame)
        self.assertEqual(
            service.coverage.states, ("Johor", "Kuala Lumpur", "Sabah", "Selangor")
        )
        self.assertEqual(service.coverage.districts("Johor", 2025), ("Johor Bahru",))
        self.assertEqual(service.coverage.property_types("Selangor", 2024, "Petaling"), ("condominium",))
        self.assertEqual(service.coverage.years("Johor"), (2025,))
        result = service.benchmark(
            state="Johor", district="Johor Bahru", property_type="terraced", year=2025
        )
        self.assertEqual(result.annual_average_price_rm, 315_000)
        self.assertNotEqual(result.annual_average_price_rm, 275_000)
        self.assertEqual(result.transaction_count, 20)
        self.assertEqual(result.year_status, "complete_year")
        self.assertEqual(result.dataset_version, "fixture-v1")
        self.assertEqual(result.retrieved_at, "2026-07-13")
        self.assertGreaterEqual(result.data_age_days, 0)
        self.assertEqual(result.available_period_start, "2025-01-01")
        self.assertEqual(result.available_period_end, "2025-12-31")
        self.assertEqual(result.source_document, "fixture")

    def test_year_first_coverage_handles_district_and_state_levels(self):
        frame = pd.DataFrame([
            record("Selangor", "Petaling", "terraced", 2025, 1, 2, 600_000),
            record("Selangor", STATE_LEVEL, "terraced", 2026, 1, 3, 1_200_000),
        ])
        service = AggregateBenchmarkService(frame)
        self.assertEqual(service.coverage.years("Selangor"), (2026, 2025))
        self.assertEqual(service.coverage.districts("Selangor", 2025), ("Petaling",))
        self.assertEqual(service.coverage.districts("Selangor", 2026), ())
        self.assertEqual(service.coverage.coverage_level("Selangor", 2026), "state")
        self.assertEqual(service.coverage.property_types("Selangor", 2026), ("terraced",))

    def test_machine_readable_coverage_is_generated_from_validated_rows(self):
        frame = pd.DataFrame([
            record("Johor", "Johor Bahru", "condominium_apartment", 2026, 1, 4, 2_000_000),
            record("Kuala Lumpur", "Kuala Lumpur", "detached", 2026, 1, 2, 3_000_000),
        ])
        catalog = build_coverage_catalog(frame)
        self.assertEqual(catalog["states"], ["Johor", "Kuala Lumpur"])
        self.assertEqual(catalog["latest_period"], {"year": 2026, "period": 1})
        johor = catalog["combinations"][0]
        self.assertEqual(johor["property_type_raw"], "Condominium/Apartment")
        self.assertEqual(johor["property_type_code"], "condominium_apartment")
        self.assertEqual(johor["property_type_label"], "Condominium / apartment")
        self.assertEqual(johor["transaction_count"], 4)

    def test_partial_year_ytd_missing_periods_and_fallback(self):
        frame = pd.DataFrame([
            record("Selangor", "Petaling", "terraced", 2023, 1, 2, 600_000),
            record("Selangor", "Petaling", "terraced", 2023, 3, 2, 1_000_000),
            record("Selangor", "Klang", "terraced", 2023, 1, 1, 200_000),
            record("Selangor", "Klang", "detached", 2023, 1, 1, 500_000),
        ])
        service = AggregateBenchmarkService(frame)
        partial = service.benchmark(
            state="Selangor", district="Petaling", property_type="terraced", year=2023
        )
        self.assertEqual(partial.year_status, "partial_year")
        self.assertEqual(partial.periods_missing, (2, 4))
        fallback = service.benchmark(
            state="Selangor", district="Missing district", property_type="terraced", year=2023
        )
        self.assertEqual(fallback.coverage_level, "state")
        self.assertIsNotNone(fallback.fallback_reason)
        self.assertEqual(classify_year(2026, (1,), current_year=2026), ("year_to_date", "2026 year-to-date benchmark through Q1"))

    def test_generic_excel_importer_supports_different_states(self):
        with tempfile.TemporaryDirectory() as directory:
            for state in ("Johor", "Sarawak"):
                path = Path(directory) / f"{state}.xlsx"
                workbook = Workbook()
                count = workbook.active
                count.title = "5.5"
                count.append(["Table"])
                count.append(["Breakdown Of Number Of Residential Property Transactions According To Type And District"])
                count.append([])
                count.append(["Property Type", "Quarter", "District A", "Total"])
                count.append([])
                count.append(["Single Storey Terrace", "Q1 2026 P", 2, 2])
                value = workbook.create_sheet("5.6")
                value.append(["Table"])
                value.append(["Breakdown Of Value Of Residential Property Transactions According To Type And District"])
                value.append(["(RM MILLION)"])
                value.append([])
                value.append(["Property Type", "Quarter", "District A", "Total"])
                value.append([])
                value.append(["Single Storey Terrace", "Q1 2026 P", 1.0, 1.0])
                workbook.save(path)
                imported, rejected = NapicExcelImporter().import_file(
                    path, state=state, source_url="https://example.test",
                    retrieved_at="2026-07-13", dataset_version="test-v1",
                )
                self.assertTrue(rejected.empty)
                self.assertEqual(imported.iloc[0]["state"], state)
                self.assertEqual(imported.iloc[0]["average_price_rm"], 500_000)


if __name__ == "__main__":
    unittest.main()
