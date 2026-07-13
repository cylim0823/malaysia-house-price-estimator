"""Train one generic aggregate baseline bundle across all validated states."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from house_price_estimator.data_pipeline import train_aggregate_baselines, volume_support
from house_price_estimator.artifacts import (
    HISTORICAL_EVALUATION_PATH,
    HISTORICAL_MODEL_DIRECTORY,
    write_historical_model_metadata,
)


ROOT = Path(__file__).parents[1]


def main() -> int:
    source = ROOT / "data" / "processed" / "aggregate_transactions" / "malaysia_aggregate_transactions_v1.csv"
    data = pd.read_csv(source)
    data["quarter"] = data["period_number"].astype(int)
    data["model_eligible"] = data["validation_status"].isin(["valid", "valid_with_warnings"])
    data["volume_support"] = data["transaction_count"].map(lambda value: volume_support(int(value)))
    data["public_prediction_supported"] = data["transaction_count"].ge(20)
    bundle, report = train_aggregate_baselines(data)
    report["coverage_states"] = sorted(data["state"].unique())
    report["coverage_years"] = sorted(int(value) for value in data["year"].unique())
    report["aggregate_rows"] = int(len(data))
    report["transactions_represented"] = int(data["transaction_count"].sum())
    report["advanced_models_reason"] = "This task retains interpretable weighted baselines; advanced models remain a comparative experiment"
    report.update({
        "dataset_name": "Malaysia licensed completed-transaction aggregates",
        "synthetic": False,
        "model_version": bundle.model_version,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    })
    model_path = HISTORICAL_MODEL_DIRECTORY / "model_bundle.pkl"
    report_path = HISTORICAL_EVALUATION_PATH
    bundle.save(model_path)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_historical_model_metadata(bundle, report, model_path=model_path)
    print(json.dumps({"model": str(model_path), "selected_baseline": bundle.selected_baseline, "rows": len(data)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
