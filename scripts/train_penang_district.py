"""Build the Penang district benchmark and model from licensed open data."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from house_price_estimator.penang_district import (  # noqa: E402
    load_penang_district_transactions,
    train_penang_district_model,
)


def main() -> None:
    data = load_penang_district_transactions(ROOT / "data" / "external" / "penang")
    processed = (
        ROOT / "data" / "processed" / "historical_prices" / "penang_district_transactions_2017.csv"
    )
    model_path = ROOT / "models" / "real" / "penang_district_bundle.pkl"
    report_path = ROOT / "reports" / "generated" / "real" / "penang_district_model_metrics.json"
    processed.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(processed, index=False)
    bundle, report = train_penang_district_model(data)
    bundle.save(model_path)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
