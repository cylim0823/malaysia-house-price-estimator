"""Build the nationwide area-level terraced benchmark from licensed JPPH data."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from house_price_estimator.regional_terraced import (  # noqa: E402
    load_regional_terraced_prices,
    train_regional_terraced_model,
)


def main() -> None:
    source = ROOT / "data" / "external" / "napic" / "terraced_by_district.xlsx"
    processed = (
        ROOT / "data" / "processed" / "historical_prices" / "regional_terraced_area_prices.csv"
    )
    model_path = ROOT / "models" / "real" / "regional_terraced_bundle.pkl"
    report_path = ROOT / "reports" / "generated" / "real" / "regional_terraced_model_metrics.json"
    data = load_regional_terraced_prices(source)
    data.drop(columns=["period"]).to_csv(processed, index=False)
    bundle, report = train_regional_terraced_model(data)
    bundle.save(model_path)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
