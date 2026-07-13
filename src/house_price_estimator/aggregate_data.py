"""Generic Malaysian transaction aggregation and year-level benchmarks."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import json
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from .location_catalog import normalize_state
from .data_pipeline import aggregate_property_type


SCHEMA_VERSION = "aggregate-2.0.0"
STATE_LEVEL = "State-level only"
ALL_RESIDENTIAL = "all_residential"
GENERIC_AGGREGATE_COLUMNS = (
    "state", "district", "district_notes", "property_type", "year",
    "period_type", "period_number", "period_start", "period_end",
    "transaction_count", "transaction_value_rm", "average_price_rm", "price_type",
    "source_name", "source_dataset", "source_file", "source_sheet", "source_url",
    "source_document", "source_table", "retrieved_at", "dataset_version",
    "schema_version", "validation_status", "validation_errors", "validation_warnings",
)


@dataclass(frozen=True)
class AnnualBenchmark:
    annual_average_price_rm: float
    transaction_count: int
    transaction_value_rm: float
    periods_included: tuple[int, ...]
    periods_missing: tuple[int, ...]
    coverage_completeness: float
    year_status: str
    display_label: str
    coverage_level: str
    state_used: str
    district_used: str | None
    property_type_used: str
    year_used: int
    fallback_reason: str | None
    source_name: str
    source_document: str
    source_file: str
    dataset_version: str
    retrieved_at: str
    data_age_days: int
    available_period_start: str
    available_period_end: str


class AggregateCoverageCatalog:
    """Selector values derived only from validated aggregate rows."""

    def __init__(self, frame: pd.DataFrame) -> None:
        self.frame = frame.loc[frame["validation_status"].isin(["valid", "valid_with_warnings"])].copy()
        if self.frame.empty:
            raise ValueError("No validated aggregate records are available")

    @property
    def states(self) -> tuple[str, ...]:
        return tuple(sorted(self.frame["state"].unique()))

    def years(self, state: str) -> tuple[int, ...]:
        rows = self.frame[self.frame["state"].eq(state)]
        return tuple(sorted((int(value) for value in rows["year"].unique()), reverse=True))

    def districts(self, state: str, year: int) -> tuple[str, ...]:
        rows = self.frame[self.frame["state"].eq(state) & self.frame["year"].eq(year)]
        values = tuple(sorted(rows["district"].dropna().unique()))
        return values if len(values) > 1 or (values and values[0] not in {state, STATE_LEVEL}) else ()

    def property_types(
        self, state: str, year: int, district: str | None = None
    ) -> tuple[str, ...]:
        rows = self.frame[
            self.frame["state"].eq(state) & self.frame["year"].eq(year)
        ]
        if district:
            rows = rows[rows["district"].eq(district)]
        return tuple(sorted(rows["property_type"].unique()))

    def coverage_level(self, state: str, year: int) -> str:
        return "district" if self.districts(state, year) else "state"


class AggregateBenchmarkService:
    """Return transaction-weighted annual results with disclosed fallbacks."""

    def __init__(
        self, frame: pd.DataFrame, *, model_metadata: dict[str, Any] | None = None
    ) -> None:
        missing = set(GENERIC_AGGREGATE_COLUMNS) - set(frame.columns)
        if missing:
            raise ValueError("Missing generic aggregate columns: " + ", ".join(sorted(missing)))
        self.frame = frame.copy()
        self.coverage = AggregateCoverageCatalog(self.frame)
        self.model_metadata = model_metadata or {}

    @classmethod
    def from_csv(
        cls, path: str | Path, *, model_metadata: dict[str, Any] | None = None
    ) -> "AggregateBenchmarkService":
        return cls(pd.read_csv(path), model_metadata=model_metadata)

    def benchmark(
        self, *, state: str, district: str | None, property_type: str, year: int
    ) -> AnnualBenchmark:
        state = normalize_state(state)
        valid = self.frame[
            self.frame["validation_status"].isin(["valid", "valid_with_warnings"])
            & self.frame["state"].eq(state)
            & self.frame["year"].eq(year)
        ]
        fallback_reason: str | None = None
        coverage_level = "district"
        district_used: str | None = district
        selected = valid[valid["property_type"].eq(property_type)]
        if district:
            exact = selected[selected["district"].eq(district)]
        else:
            exact = pd.DataFrame()
        if not exact.empty:
            selected = exact
        elif district is None and not selected.empty:
            coverage_level = "state"
            district_used = None
        elif not selected.empty:
            coverage_level = "state"
            district_used = None
            fallback_reason = "District segment unavailable; used state property-type records"
        elif not valid.empty:
            selected = valid
            coverage_level = "state_all_residential"
            district_used = None
            fallback_reason = "Property type unavailable; used all validated residential records"
            property_type = ALL_RESIDENTIAL
        else:
            raise ValueError("Unsupported state and year combination")

        periods = tuple(sorted(int(value) for value in selected["period_number"].unique()))
        missing = tuple(value for value in (1, 2, 3, 4) if value not in periods)
        count = int(selected["transaction_count"].sum())
        value_rm = float(selected["transaction_value_rm"].sum())
        if count <= 0 or value_rm <= 0:
            raise ValueError("Selected aggregate records have no positive transaction support")
        status, label = classify_year(year, periods)
        available = self.frame[
            self.frame["validation_status"].isin(["valid", "valid_with_warnings"])
            & self.frame["state"].eq(state)
            & self.frame["property_type"].eq(property_type)
        ]
        if district_used is not None:
            available = available[available["district"].eq(district_used)]
        retrieved = pd.to_datetime(selected["retrieved_at"], utc=True, errors="coerce").dropna()
        latest_retrieved = retrieved.max()
        if pd.isna(latest_retrieved):
            raise ValueError("Selected aggregate records have no valid retrieval date")
        return AnnualBenchmark(
            annual_average_price_rm=value_rm / count,
            transaction_count=count,
            transaction_value_rm=value_rm,
            periods_included=periods,
            periods_missing=missing,
            coverage_completeness=len(periods) / 4,
            year_status=status,
            display_label=label,
            coverage_level=coverage_level,
            state_used=state,
            district_used=district_used,
            property_type_used=property_type,
            year_used=year,
            fallback_reason=fallback_reason,
            source_name="; ".join(sorted(selected["source_name"].astype(str).unique())),
            source_document="; ".join(
                sorted(selected["source_document"].astype(str).unique())
            ),
            source_file="; ".join(sorted(selected["source_file"].astype(str).unique())),
            dataset_version="; ".join(
                sorted(selected["dataset_version"].astype(str).unique())
            ),
            retrieved_at=latest_retrieved.date().isoformat(),
            data_age_days=max(0, (date.today() - latest_retrieved.date()).days),
            available_period_start=str(available["period_start"].min()),
            available_period_end=str(available["period_end"].max()),
        )


def classify_year(year: int, periods: Iterable[int], *, current_year: int | None = None) -> tuple[str, str]:
    included = tuple(sorted(set(int(value) for value in periods)))
    current = current_year or date.today().year
    labels = " and ".join(f"Q{value}" for value in included)
    if included == (1, 2, 3, 4):
        return "complete_year", "Annual completed-transaction average"
    if year == current and included:
        return "year_to_date", f"{year} year-to-date benchmark through Q{included[-1]}"
    return "partial_year", f"Partial-year completed-transaction benchmark ({labels})"


def build_coverage_catalog(frame: pd.DataFrame) -> dict[str, Any]:
    """Return machine-readable selector coverage generated from validated rows."""
    valid = frame[frame["validation_status"].isin(["valid", "valid_with_warnings"])].copy()
    records: list[dict[str, Any]] = []
    state_year_counts = valid.groupby(["state", "year"])["district"].nunique()
    for coordinates, rows in valid.groupby(
        ["state", "district", "property_type", "year"], sort=True
    ):
        state, district, storage_code, year = coordinates
        definition = aggregate_property_type(storage_code)
        is_state_level = int(state_year_counts.loc[(state, year)]) == 1 and district in {
            state, STATE_LEVEL
        }
        records.append(
            {
                "state": state,
                "district": None if is_state_level else district,
                "district_available": not is_state_level,
                "coverage_level": "state" if is_state_level else "district",
                "property_type_raw": definition.raw_value,
                "property_type_code": definition.property_type_code,
                "property_type_label": definition.property_type_label,
                "storage_code": storage_code,
                "year": int(year),
                "periods": sorted(int(value) for value in rows["period_number"].unique()),
                "transaction_count": int(rows["transaction_count"].sum()),
                "source_name": sorted(rows["source_name"].astype(str).unique()),
                "source_document": sorted(rows["source_document"].astype(str).unique()),
                "validation_warning": None if definition.known else "UNKNOWN_PROPERTY_TYPE",
            }
        )
    return {
        "catalog_version": "aggregate-coverage-1.0.0",
        "generated_from": "validated processed aggregate records",
        "states": sorted(valid["state"].unique()),
        "latest_period": {
            "year": int(valid["year"].max()),
            "period": int(valid.loc[valid["year"].eq(valid["year"].max()), "period_number"].max()),
        },
        "combinations": records,
    }


def aggregate_open_transaction_snapshots(
    raw_directory: str | Path,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Aggregate licensed per-state NAPIC CSV snapshots into quarter groups."""
    directory = Path(raw_directory)
    manifest = json.loads((directory / "metadata.json").read_text(encoding="utf-8"))
    snapshots = manifest.get("snapshots", manifest.get("states", []))
    metadata_by_name = {Path(item["path"]).name: item for item in snapshots}
    accepted: list[pd.DataFrame] = []
    rejected: list[pd.DataFrame] = []
    for path in sorted(directory.glob("*.csv")):
        metadata = metadata_by_name[path.name]
        raw = pd.read_csv(path)
        dates = pd.to_datetime(raw["Month, Year of Transaction Date"], format="%B %Y", errors="coerce")
        prices = pd.to_numeric(raw["Transaction Price  "], errors="coerce")
        districts = raw["District"].astype("string").str.strip()
        property_types = raw["Property Type"].astype("string").str.strip()
        valid = dates.notna() & prices.gt(0) & districts.notna() & districts.ne("") & property_types.notna() & property_types.ne("")
        if (~valid).any():
            bad = raw.loc[~valid].copy()
            bad.insert(0, "source_file", path.name)
            bad.insert(1, "validation_errors", "INVALID_DATE_PRICE_LOCATION_OR_TYPE")
            rejected.append(bad)
        property_definitions = property_types[valid].map(aggregate_property_type)
        rows = pd.DataFrame(
            {
                "state": normalize_state(metadata["requested_state"]),
                "district": districts[valid],
                "property_type": property_definitions.map(
                    lambda definition: definition.storage_code
                ),
                "unknown_property_type": property_definitions.map(
                    lambda definition: not definition.known
                ),
                "year": dates[valid].dt.year,
                "period_number": dates[valid].dt.quarter,
                "transaction_value_rm": prices[valid],
            }
        )
        grouped = rows.groupby(
            ["state", "district", "property_type", "year", "period_number"],
            as_index=False,
        ).agg(
            transaction_count=("transaction_value_rm", "size"),
            transaction_value_rm=("transaction_value_rm", "sum"),
            unknown_property_type=("unknown_property_type", "any"),
        )
        grouped["average_price_rm"] = grouped["transaction_value_rm"] / grouped["transaction_count"]
        grouped["district_notes"] = ""
        grouped["period_type"] = "quarter"
        periods = grouped.apply(lambda row: pd.Period(year=int(row["year"]), quarter=int(row["period_number"]), freq="Q"), axis=1)
        grouped["period_start"] = periods.map(lambda value: value.start_time.date().isoformat())
        grouped["period_end"] = periods.map(lambda value: value.end_time.date().isoformat())
        grouped["price_type"] = "completed_transaction_average"
        grouped["source_name"] = metadata["source_name"]
        grouped["source_dataset"] = "Data Transaksi Terbuka"
        grouped["source_file"] = path.name
        grouped["source_sheet"] = ""
        grouped["source_url"] = metadata["source_download_url"]
        grouped["source_document"] = "NAPIC/JPPH Open Transaction Data"
        grouped["source_table"] = "Per-state Tableau CSV export"
        grouped["retrieved_at"] = metadata["retrieved_at"]
        grouped["dataset_version"] = "napic-open-transactions-20260713-aggregate-v1"
        grouped["schema_version"] = SCHEMA_VERSION
        grouped["validation_status"] = "valid"
        grouped["validation_errors"] = "[]"
        grouped["validation_warnings"] = grouped["unknown_property_type"].map(
            lambda unknown: '["UNKNOWN_PROPERTY_TYPE"]' if unknown else "[]"
        )
        accepted.append(grouped[list(GENERIC_AGGREGATE_COLUMNS)])
    processed = pd.concat(accepted, ignore_index=True).sort_values(
        ["state", "district", "property_type", "year", "period_number"]
    ).reset_index(drop=True)
    rejected_frame = (
        pd.concat(rejected, ignore_index=True)
        if rejected
        else pd.DataFrame(columns=["source_file", "validation_errors"])
    )
    return processed, rejected_frame
