"""Source-neutral ingestion of approved structured files."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from . import SCHEMA_VERSION
from .schema import RawRecord

SYNTHETIC_LABEL = "Synthetic demonstration data — not real Malaysian property market data."


@dataclass(frozen=True)
class IngestionResult:
    records: tuple[RawRecord, ...]
    rejected_rows: tuple[dict[str, Any], ...]
    summary: dict[str, Any]


def _read(path: Path, encoding: str) -> list[dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        with path.open(encoding=encoding, newline="") as handle:
            return list(csv.DictReader(handle))
    if suffix == ".json":
        value = json.loads(path.read_text(encoding=encoding))
        if not isinstance(value, list):
            raise ValueError("JSON input must contain a list of objects")
        return value
    if suffix in {".jsonl", ".ndjson"}:
        return [json.loads(line) for line in path.read_text(encoding=encoding).splitlines() if line.strip()]
    if suffix == ".parquet":
        try:
            import pandas as pd
            return pd.read_parquet(path).to_dict(orient="records")
        except ImportError as exc:
            raise RuntimeError("Parquet support requires pandas and pyarrow") from exc
    raise ValueError(f"unsupported input format: {suffix}")


def ingest_file(path: str | Path, *, source_name: str, dataset_version: str,
                required_columns: tuple[str, ...] = ("record_id", "price", "price_type", "state", "property_type"),
                encoding: str = "utf-8-sig") -> IngestionResult:
    input_path = Path(path)
    if not input_path.is_file():
        raise FileNotFoundError(input_path)
    if not source_name.strip() or not dataset_version.strip():
        raise ValueError("source_name and dataset_version are required")
    rows = _read(input_path, encoding)
    batch_id = f"ing_{uuid4().hex}"
    imported_at = datetime.now(timezone.utc)
    accepted: list[RawRecord] = []
    rejected: list[dict[str, Any]] = []
    for number, row in enumerate(rows, start=2 if input_path.suffix.lower() == ".csv" else 1):
        if not isinstance(row, dict):
            rejected.append({"row_number": number, "original_row": row, "error_codes": ["ROW_NOT_OBJECT"], "processing_stage": "ingestion"})
            continue
        missing = [column for column in required_columns if row.get(column) in (None, "")]
        if missing:
            rejected.append({"row_number": number, "original_row": row, "error_codes": ["MISSING_REQUIRED_COLUMNS"],
                             "rejection_reason": ", ".join(missing), "processing_stage": "ingestion", "review_required": True})
            continue
        accepted.append(RawRecord(str(row["record_id"]), source_name, dict(row), imported_at, batch_id,
                                  dataset_version, is_synthetic=bool(row.get("is_synthetic", False))))
    summary = {"input_path": str(input_path), "source_name": source_name, "ingestion_batch_id": batch_id,
               "schema_version": SCHEMA_VERSION, "dataset_version": dataset_version, "input_rows": len(rows),
               "accepted_rows": len(accepted), "rejected_rows": len(rejected)}
    return IngestionResult(tuple(accepted), tuple(rejected), summary)

