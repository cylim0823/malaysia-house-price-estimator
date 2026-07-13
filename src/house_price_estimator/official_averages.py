"""Training and prediction for licensed JPPH historical average-price data."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import pickle
from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.compose import TransformedTargetRegressor
from sklearn.preprocessing import OneHotEncoder, StandardScaler


SOURCE_FILES = {
    "All houses": "all_houses_by_state.xlsx",
    "Terraced house": "terraced_by_state.xlsx",
    "Semi-detached house": "semi_detached_by_state.xlsx",
    "Detached house": "detached_by_state.xlsx",
}
STATE_ALIASES = {"Pulau Pinang": "Penang"}
FEATURES = ["state", "property_type", "year", "quarter"]


def load_official_average_prices(directory: str | Path) -> pd.DataFrame:
    """Convert the four government workbooks into one tidy observation table."""
    root = Path(directory)
    frames: list[pd.DataFrame] = []
    for property_type, filename in SOURCE_FILES.items():
        path = root / filename
        raw = pd.read_excel(path, header=4)
        raw = raw.rename(columns={raw.columns[0]: "year", raw.columns[1]: "quarter_label"})
        value_columns = [column for column in raw.columns[2:] if column != "Malaysia"]
        tidy = raw.melt(
            id_vars=["year", "quarter_label"],
            value_vars=value_columns,
            var_name="state",
            value_name="average_price_rm",
        )
        tidy["property_type"] = property_type
        tidy["source_file"] = filename
        frames.append(tidy)
    data = pd.concat(frames, ignore_index=True)
    data["state"] = data["state"].replace(STATE_ALIASES)
    data["year"] = pd.to_numeric(data["year"], errors="coerce")
    data["quarter"] = data["quarter_label"].astype(str).str.extract(r"(\d)")[0]
    data["quarter"] = pd.to_numeric(data["quarter"], errors="coerce")
    data["average_price_rm"] = pd.to_numeric(data["average_price_rm"], errors="coerce")
    data = data.dropna(subset=["year", "quarter", "state", "average_price_rm"])
    data["year"] = data["year"].astype(int)
    data["quarter"] = data["quarter"].astype(int)
    data["period"] = data["year"] * 4 + data["quarter"]
    return data.sort_values(["period", "state", "property_type"]).reset_index(drop=True)


def _pipeline() -> TransformedTargetRegressor:
    categories = ["state", "property_type"]
    numbers = ["year", "quarter"]
    preprocessing = ColumnTransformer(
        [
            ("categories", OneHotEncoder(handle_unknown="ignore"), categories),
            ("numbers", StandardScaler(), numbers),
        ]
    )
    base = Pipeline([("preprocessing", preprocessing), ("regressor", Ridge(alpha=0.1))])
    return TransformedTargetRegressor(regressor=base, func=np.log1p, inverse_func=np.expm1)


def _metrics(actual: pd.Series, predicted: np.ndarray) -> dict[str, float]:
    return {
        "mae_rm": float(mean_absolute_error(actual, predicted)),
        "rmse_rm": float(mean_squared_error(actual, predicted) ** 0.5),
        "r2": float(r2_score(actual, predicted)),
    }


@dataclass
class OfficialAverageBundle:
    """Serializable model plus its strict historical coverage contract."""

    model: Any
    states: tuple[str, ...]
    property_types: tuple[str, ...]
    minimum_year: int
    maximum_year: int
    test_metrics: dict[str, float]
    residual_margin_rm: float
    dataset_version: str = "jpph-open-average-prices-2009-2018q2"
    model_version: str = "official-historical-average-ridge-v1"

    def predict(self, *, state: str, property_type: str, year: int, quarter: int) -> dict[str, Any]:
        if state not in self.states:
            raise ValueError(f"Unsupported state: {state}")
        if property_type not in self.property_types:
            raise ValueError(f"Unsupported property type: {property_type}")
        if not self.minimum_year <= year <= self.maximum_year:
            raise ValueError(f"Year must be between {self.minimum_year} and {self.maximum_year}")
        if quarter not in {1, 2, 3, 4} or (year == self.maximum_year and quarter > 2):
            raise ValueError("The official dataset ends at 2018 Q2")
        values = pd.DataFrame([[state, property_type, year, quarter]], columns=FEATURES)
        estimate = max(0.0, float(self.model.predict(values)[0]))
        return {
            "estimate": estimate,
            "lower": max(0.0, estimate - self.residual_margin_rm),
            "upper": estimate + self.residual_margin_rm,
        }

    def save(self, path: str | Path) -> None:
        output = Path(path); output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(pickle.dumps(self, protocol=pickle.HIGHEST_PROTOCOL))

    @classmethod
    def load(cls, path: str | Path) -> "OfficialAverageBundle":
        value = pickle.loads(Path(path).read_bytes())
        if not isinstance(value, cls):
            raise TypeError("unexpected official average bundle type")
        return value


def train_official_average_model(data: pd.DataFrame) -> tuple[OfficialAverageBundle, dict[str, Any]]:
    """Fit on older quarters and evaluate once on the final two quarters."""
    periods = sorted(data["period"].unique())
    if len(periods) < 8:
        raise ValueError("at least eight quarterly periods are required")
    test_periods = set(periods[-2:])
    train = data[~data["period"].isin(test_periods)]
    test = data[data["period"].isin(test_periods)]
    model = _pipeline().fit(train[FEATURES], train["average_price_rm"])
    predicted = model.predict(test[FEATURES])
    baseline = np.full(len(test), float(train["average_price_rm"].median()))
    segment_medians = train.groupby(["state", "property_type"])["average_price_rm"].median()
    segment_baseline = np.asarray([
        segment_medians.get((row.state, row.property_type), baseline[0])
        for row in test.itertuples()
    ])
    residuals = np.abs(test["average_price_rm"].to_numpy() - predicted)
    bundle = OfficialAverageBundle(
        model=model,
        states=tuple(sorted(data["state"].unique())),
        property_types=tuple(sorted(data["property_type"].unique())),
        minimum_year=int(data["year"].min()),
        maximum_year=int(data["year"].max()),
        test_metrics=_metrics(test["average_price_rm"], predicted),
        residual_margin_rm=float(np.quantile(residuals, 0.8)),
    )
    report = {
        "dataset_rows": int(len(data)),
        "train_rows": int(len(train)),
        "test_rows": int(len(test)),
        "test_periods": sorted(int(value) for value in test_periods),
        "model": bundle.test_metrics,
        "overall_median_baseline": _metrics(test["average_price_rm"], baseline),
        "state_property_type_median_baseline": _metrics(
            test["average_price_rm"], segment_baseline
        ),
        "states": list(bundle.states),
        "property_types": list(bundle.property_types),
    }
    return bundle, report
