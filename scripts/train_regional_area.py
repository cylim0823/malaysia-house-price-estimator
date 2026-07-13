"""Build the multi-property regional benchmark from licensed JPPH data."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from house_price_estimator.regional_area import (  # noqa: E402
    load_regional_area_prices,
    train_regional_area_model,
)


def main() -> None:
    source_dir = ROOT / "data" / "external" / "napic"
    processed = (
        ROOT / "data" / "processed" / "historical_prices" / "regional_area_prices.csv"
    )
    model_path = ROOT / "models" / "real" / "regional_area_bundle.pkl"
    report_path = ROOT / "reports" / "generated" / "real" / "regional_area_model_metrics.json"
    data = load_regional_area_prices(
        source_dir / "terraced_by_district.xlsx",
        source_dir / "highrise_by_district.xlsx",
    )
    data.drop(columns=["period"]).to_csv(processed, index=False)
    bundle, report = train_regional_area_model(data)
    bundle.save(model_path)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
