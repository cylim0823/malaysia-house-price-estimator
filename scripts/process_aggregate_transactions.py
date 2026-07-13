"""Preserve, validate, report, and train the Penang aggregate transaction data."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from house_price_estimator.aggregate_transactions import (  # noqa: E402
    COLLECTED_AT,
    DATASET_VERSION,
    SCHEMA_VERSION,
    SOURCE_DOCUMENT,
    SOURCE_NAME,
    SOURCE_TABLE,
    SOURCE_URL,
    SOURCE_VALUE_URL,
    load_and_validate_aggregate_csv,
    train_aggregate_baselines,
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    imported = ROOT / "data" / "official" / "penang_district_transactions_2017.csv"
    raw_dir = ROOT / "data" / "raw" / "aggregate_transactions"
    raw_path = raw_dir / imported.name
    raw_dir.mkdir(parents=True, exist_ok=True)
    if not raw_path.exists():
        shutil.copyfile(imported, raw_path)
    if imported.read_bytes() != raw_path.read_bytes():
        raise RuntimeError("raw aggregate copy differs from the imported CSV")

    metadata = {
        "original_filename": imported.name,
        "file_size_bytes": raw_path.stat().st_size,
        "sha256": _sha256(raw_path),
        "import_date": COLLECTED_AT,
        "source_name": SOURCE_NAME,
        "source_url": SOURCE_URL,
        "source_urls": [SOURCE_URL, SOURCE_VALUE_URL],
        "source_document": SOURCE_DOCUMENT,
        "source_page_or_table": SOURCE_TABLE,
        "licence": "Creative Commons Attribution (catalogue label)",
        "price_type": "completed_transaction_average",
        "schema_version": SCHEMA_VERSION,
        "dataset_version": DATASET_VERSION,
        "row_meaning": "One aggregate state-district-property-type-year-quarter group",
    }
    (raw_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )

    result = load_and_validate_aggregate_csv(raw_path)
    processed_dir = ROOT / "data" / "processed" / "aggregate_transactions"
    processed_dir.mkdir(parents=True, exist_ok=True)
    processed_path = processed_dir / "penang_aggregate_transactions_v1.csv"
    rejected_path = processed_dir / "penang_aggregate_transactions_rejected_v1.csv"
    result.processed.to_csv(processed_path, index=False)
    result.rejected.to_csv(rejected_path, index=False)

    reports = ROOT / "reports"
    reports.mkdir(exist_ok=True)
    (reports / "aggregate_transaction_quality.json").write_text(
        json.dumps(result.quality_report, indent=2), encoding="utf-8"
    )
    eda = {
        "dataset_version": DATASET_VERSION,
        "row_meaning": "aggregate group, not an individual property transaction",
        "aggregate_rows": result.quality_report["aggregate_row_count"],
        "transactions_represented": result.quality_report["sum_of_transaction_count"],
        "transaction_value_rm": result.quality_report["sum_of_transaction_value_rm"],
        "coverage": {
            "states": result.quality_report["states"],
            "districts": result.quality_report["districts"],
            "property_types": result.quality_report["property_types"],
            "years": result.quality_report["years"],
            "quarters": result.quality_report["quarters"],
        },
        "volume_support_rows": result.quality_report["volume_support_rows"],
        "missing_combinations": result.quality_report["missing_combinations"],
        "suspicious_quarter_change_rows": result.quality_report[
            "suspicious_quarter_change_rows"
        ],
    }
    (reports / "aggregate_transaction_eda.json").write_text(
        json.dumps(eda, indent=2), encoding="utf-8"
    )

    bundle, model_report = train_aggregate_baselines(result.processed)
    bundle.save(ROOT / "models" / "aggregate_transaction_bundle.pkl")
    (reports / "aggregate_transaction_model_metrics.json").write_text(
        json.dumps(model_report, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "raw_metadata": metadata,
                "quality": result.quality_report,
                "model": model_report,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
