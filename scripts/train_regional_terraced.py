"""Build the nationwide area-level terraced benchmark from licensed JPPH data."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from house_price_estimator.regional_terraced import (  # noqa: E402
    load_regional_terraced_prices,
    train_regional_terraced_model,
)
from house_price_estimator.artifacts import GENERATED_EVALUATION_DIRECTORY  # noqa: E402


def main() -> None:
    source = ROOT / "data" / "external" / "napic" / "terraced_by_district.xlsx"
    processed = (
        ROOT / "data" / "processed" / "historical_prices" / "regional_terraced_area_prices.csv"
    )
    model_path = ROOT / "build" / "experimental_models" / "regional_terraced_bundle.pkl"
    report_path = GENERATED_EVALUATION_DIRECTORY / "experimental_regional_terraced.json"
    data = load_regional_terraced_prices(source)
    data.drop(columns=["period"]).to_csv(processed, index=False)
    bundle, report = train_regional_terraced_model(data)
    report = {
        "dataset_name": "JPPH published regional terraced-house averages",
        "dataset_version": bundle.dataset_version,
        "synthetic": False,
        "model_version": bundle.model_version,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        **report,
    }
    model_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    bundle.save(model_path)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
