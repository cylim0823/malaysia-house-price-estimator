"""Build the deployable model from the committed JPPH open-data workbooks."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from house_price_estimator.official_averages import (  # noqa: E402
    load_official_average_prices,
    train_official_average_model,
)
from house_price_estimator.artifacts import GENERATED_EVALUATION_DIRECTORY  # noqa: E402


def main() -> None:
    source = ROOT / "data" / "external" / "napic"
    processed = (
        ROOT / "data" / "processed" / "historical_prices" / "jpph_historical_average_prices.csv"
    )
    model_path = ROOT / "build" / "experimental_models" / "official_average_bundle.pkl"
    report_path = GENERATED_EVALUATION_DIRECTORY / "experimental_official_average.json"
    data = load_official_average_prices(source)
    processed.parent.mkdir(parents=True, exist_ok=True)
    data.drop(columns=["period"]).to_csv(processed, index=False)
    bundle, report = train_official_average_model(data)
    report = {
        "dataset_name": "JPPH published state/property-type averages",
        "dataset_version": bundle.dataset_version,
        "synthetic": False,
        "model_version": bundle.model_version,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        **report,
    }
    bundle.save(model_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
