"""Build the deployable model from the committed JPPH open-data workbooks."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from house_price_estimator.official_averages import (  # noqa: E402
    load_official_average_prices,
    train_official_average_model,
)


def main() -> None:
    source = ROOT / "data" / "external" / "napic_open_data"
    processed = ROOT / "data" / "official" / "jpph_historical_average_prices.csv"
    model_path = ROOT / "models" / "official_average_bundle.pkl"
    report_path = ROOT / "reports" / "official_average_model_metrics.json"
    data = load_official_average_prices(source)
    processed.parent.mkdir(parents=True, exist_ok=True)
    data.drop(columns=["period"]).to_csv(processed, index=False)
    bundle, report = train_official_average_model(data)
    bundle.save(model_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
