"""Train and report the separate real NAPIC individual-transaction model."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

from house_price_estimator.real_transactions import (
    load_napic_snapshots,
    prepare_real_transactions,
    train_real_property_model,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--quality-report", type=Path, required=True)
    parser.add_argument("--dataset-version", default="napic-open-transactions-2026-07-13")
    args = parser.parse_args()
    prepared, quality = prepare_real_transactions(load_napic_snapshots(args.raw_dir))
    bundle, evaluation = train_real_property_model(
        prepared, dataset_version=args.dataset_version
    )
    report_metadata = {
        "dataset_name": "NAPIC/JPPH Data Transaksi Terbuka property records",
        "dataset_version": args.dataset_version,
        "synthetic": False,
        "model_version": bundle.model_version,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    evaluation = {**report_metadata, **evaluation}
    quality = {**report_metadata, **quality}
    bundle.save(args.model)
    for path, payload in ((args.report, evaluation), (args.quality_report, quality)):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({"quality": quality, "evaluation": evaluation}, indent=2))


if __name__ == "__main__":
    main()
