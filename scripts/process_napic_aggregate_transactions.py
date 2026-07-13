"""Build the generic aggregate dataset from licensed NAPIC open transactions."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

import pandas as pd

from house_price_estimator.aggregate_data import (
    GENERIC_AGGREGATE_COLUMNS,
    aggregate_open_transaction_snapshots,
    build_coverage_catalog,
)
from house_price_estimator.artifacts import GENERATED_DATA_QUALITY_DIRECTORY


def compatible_legacy_release(path: Path) -> pd.DataFrame:
    """Map any validated v1 quarter release without source-specific assumptions."""
    frame = pd.read_csv(path)
    frame = frame[frame["validation_status"].isin(["valid", "valid_with_warnings"])].copy()
    frame["period_type"] = "quarter"
    frame["period_number"] = frame["quarter"]
    frame["source_file"] = path.name
    frame["source_sheet"] = ""
    frame["source_table"] = frame["source_page_or_table"]
    frame["retrieved_at"] = frame["collected_at"]
    frame["schema_version"] = "aggregate-2.0.0"
    return frame[list(GENERIC_AGGREGATE_COLUMNS)]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw/napic_open_transactions_20260713"))
    parser.add_argument("--output", type=Path, default=Path("data/processed/aggregate_transactions/malaysia_aggregate_transactions_v1.csv"))
    parser.add_argument("--rejected", type=Path, default=Path("data/processed/aggregate_transactions/malaysia_aggregate_transactions_rejected_v1.csv"))
    parser.add_argument(
        "--coverage-catalog", type=Path,
        default=Path("data/processed/aggregate_transactions/coverage_catalog.json"),
    )
    args = parser.parse_args()
    processed, rejected = aggregate_open_transaction_snapshots(args.raw_dir)
    for release in sorted(args.output.parent.glob("*_aggregate_transactions_v1.csv")):
        if release.resolve() != args.output.resolve():
            processed = pd.concat(
                [processed, compatible_legacy_release(release)], ignore_index=True
            )
    processed = processed.sort_values(
        ["state", "district", "property_type", "year", "period_number"]
    ).reset_index(drop=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    processed.to_csv(args.output, index=False)
    rejected.to_csv(args.rejected, index=False)
    args.coverage_catalog.write_text(
        json.dumps(build_coverage_catalog(processed), indent=2), encoding="utf-8"
    )
    segment_periods = processed.groupby(
        ["state", "district", "property_type", "year"]
    )["period_number"].nunique()
    report_metadata = {
        "dataset_name": "Malaysia licensed completed-transaction aggregates",
        "dataset_version": "napic-open-transactions-20260713-aggregate-v1",
        "synthetic": False,
        "model_version": "aggregate-weighted-baseline-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    summary = {
        **report_metadata,
        "aggregate_rows": len(processed),
        "transactions": int(processed["transaction_count"].sum()),
        "transaction_value_rm": float(processed["transaction_value_rm"].sum()),
        "states": sorted(processed["state"].unique()),
        "state_count": int(processed["state"].nunique()),
        "district_count": int(processed["district"].nunique()),
        "property_types": sorted(processed["property_type"].unique()),
        "years": sorted(int(value) for value in processed["year"].unique()),
        "latest_period": [int(processed["year"].max()), int(processed.loc[processed["year"].eq(processed["year"].max()), "period_number"].max())],
        "complete_years_at_national_level": [2021, 2022, 2023, 2024, 2025],
        "year_to_date_years": [2026],
        "complete_segment_years": int(segment_periods.eq(4).sum()),
        "partial_segment_years": int(segment_periods.lt(4).sum()),
        "rejected_raw_rows": len(rejected),
    }
    report_dir = GENERATED_DATA_QUALITY_DIRECTORY
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "historical_aggregate.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    eda = {
        **report_metadata,
        "rows_by_state": {str(k): int(v) for k, v in processed["state"].value_counts().sort_index().items()},
        "transactions_by_year": {str(k): int(v) for k, v in processed.groupby("year")["transaction_count"].sum().items()},
        "average_price_rm_distribution": {str(k): float(v) for k, v in processed["average_price_rm"].describe().items()},
    }
    (report_dir / "historical_aggregate_eda.json").write_text(
        json.dumps(eda, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
