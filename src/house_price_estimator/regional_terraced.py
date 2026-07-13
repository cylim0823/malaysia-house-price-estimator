"""Area-level terraced-house benchmarks from licensed JPPH open data."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import pickle
from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


FEATURES = ["state", "area", "year", "quarter"]
STATE_ALIASES = {"Pulau Pinang": "Penang"}


def load_regional_terraced_prices(path: str | Path) -> pd.DataFrame:
    """Normalize the official wide workbook into area-quarter observations."""
    raw = pd.read_excel(path, header=3)
    data = raw.melt(
        id_vars=["State", "District/Region"],
        var_name="period_label",
        value_name="average_price_rm",
    )
    data = data.rename(columns={"State": "state", "District/Region": "area"})
    periods = data["period_label"].astype(str).str.extract(r"(\d{4})_Q(\d)")
    data["year"] = pd.to_numeric(periods[0], errors="coerce")
    data["quarter"] = pd.to_numeric(periods[1], errors="coerce")
    data["average_price_rm"] = pd.to_numeric(data["average_price_rm"], errors="coerce")
    data = data.dropna(subset=["state", "area", "year", "quarter", "average_price_rm"])
    data["state"] = data["state"].replace(STATE_ALIASES)
    data["year"] = data["year"].astype(int)
    data["quarter"] = data["quarter"].astype(int)
    data["property_type"] = "Terraced house"
    data["price_type"] = "published_average"
    data["period"] = data["year"] * 4 + data["quarter"]
    return data.sort_values(["period", "state", "area"]).reset_index(drop=True)


def _ridge() -> TransformedTargetRegressor:
    preprocessing = ColumnTransformer(
        [
            (
                "categories",
                OneHotEncoder(handle_unknown="ignore"),
                ["state", "area"],
            ),
            ("time", StandardScaler(), ["year", "quarter"]),
        ]
    )
    pipeline = Pipeline(
        [("preprocessing", preprocessing), ("regressor", Ridge(alpha=0.1))]
    )
    return TransformedTargetRegressor(
        regressor=pipeline, func=np.log1p, inverse_func=np.expm1
    )


def _metrics(actual: pd.Series, predicted: np.ndarray) -> dict[str, float]:
    return {
        "mae_rm": float(mean_absolute_error(actual, predicted)),
        "rmse_rm": float(mean_squared_error(actual, predicted) ** 0.5),
        "r2": float(r2_score(actual, predicted)),
    }


@dataclass
class AreaMedianModel:
    medians: dict[tuple[str, str], float]
    overall: float

    @classmethod
    def fit(cls, records: pd.DataFrame) -> "AreaMedianModel":
        values = records.groupby(["state", "area"])["average_price_rm"].median()
        return cls(
            {tuple(key): float(value) for key, value in values.items()},
            float(records["average_price_rm"].median()),
        )

    def predict(self, records: pd.DataFrame) -> np.ndarray:
        return np.asarray([
            self.medians.get((row.state, row.area), self.overall)
            for row in records.itertuples()
        ])


@dataclass
class RegionalTerracedBundle:
    """Selected model, strict coverage, and official observation lookup."""

    model: Any
    areas_by_state: dict[str, tuple[str, ...]]
    observations: dict[str, float]
    test_metrics: dict[str, float]
    residual_margin_rm: float
    selected_model: str
    dataset_version: str = "jpph-regional-terraced-2016-2018q2-v1"
    model_version: str = "regional-terraced-log-ridge-v1"

    @staticmethod
    def _key(state: str, area: str, year: int, quarter: int) -> str:
        return f"{state}|{area}|{year}|{quarter}"

    @property
    def states(self) -> tuple[str, ...]:
        return tuple(sorted(self.areas_by_state))

    def predict(self, *, state: str, area: str, year: int, quarter: int) -> dict[str, float]:
        if state not in self.areas_by_state:
            raise ValueError(f"Unsupported state: {state}")
        if area not in self.areas_by_state[state]:
            raise ValueError(f"Unsupported area for {state}: {area}")
        if year not in {2016, 2017, 2018}:
            raise ValueError("Regional terraced coverage is limited to 2016-2018")
        if quarter not in {1, 2, 3, 4} or (year == 2018 and quarter > 2):
            raise ValueError("The regional dataset ends at 2018 Q2")
        frame = pd.DataFrame([[state, area, year, quarter]], columns=FEATURES)
        estimate = max(0.0, float(self.model.predict(frame)[0]))
        observed = self.observations.get(self._key(state, area, year, quarter))
        return {
            "model_estimate": estimate,
            "lower": max(0.0, estimate - self.residual_margin_rm),
            "upper": estimate + self.residual_margin_rm,
            "observed_average": float(observed) if observed is not None else float("nan"),
        }

    def save(self, path: str | Path) -> None:
        output = Path(path); output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(pickle.dumps(self, protocol=pickle.HIGHEST_PROTOCOL))

    @classmethod
    def load(cls, path: str | Path) -> "RegionalTerracedBundle":
        value = pickle.loads(Path(path).read_bytes())
        if not isinstance(value, cls):
            raise TypeError("unexpected regional terraced bundle type")
        return value


def train_regional_terraced_model(data: pd.DataFrame) -> tuple[RegionalTerracedBundle, dict[str, Any]]:
    """Train through 2017 and evaluate once on 2018 Q1-Q2."""
    train = data[data["year"] < 2018]
    test = data[data["year"] == 2018]
    ridge = _ridge().fit(train[FEATURES], train["average_price_rm"])
    ridge_predicted = ridge.predict(test[FEATURES])
    median_model = AreaMedianModel.fit(train)
    median_predicted = median_model.predict(test[FEATURES])
    ridge_metrics = _metrics(test["average_price_rm"], ridge_predicted)
    median_metrics = _metrics(test["average_price_rm"], median_predicted)
    if ridge_metrics["mae_rm"] <= median_metrics["mae_rm"]:
        model: Any = ridge
        predicted = ridge_predicted
        selected_model = "log_ridge"
        selected_metrics = ridge_metrics
    else:
        model = median_model
        predicted = median_predicted
        selected_model = "area_median"
        selected_metrics = median_metrics
    residuals = np.abs(test["average_price_rm"].to_numpy() - predicted)
    areas_by_state = {
        state: tuple(sorted(group["area"].unique()))
        for state, group in data.groupby("state")
    }
    observations = {
        RegionalTerracedBundle._key(row.state, row.area, row.year, row.quarter): float(row.average_price_rm)
        for row in data.itertuples()
    }
    bundle = RegionalTerracedBundle(
        model=model,
        areas_by_state=areas_by_state,
        observations=observations,
        test_metrics=selected_metrics,
        residual_margin_rm=float(np.quantile(residuals, 0.8)),
        selected_model=selected_model,
    )
    report = {
        "dataset_rows": int(len(data)),
        "train_rows": int(len(train)),
        "test_rows": int(len(test)),
        "test_period": "2018 Q1-Q2",
        "selected_model": selected_model,
        "model": selected_metrics,
        "log_ridge": ridge_metrics,
        "area_median_baseline": median_metrics,
        "states": list(bundle.states),
        "area_count": sum(len(areas) for areas in areas_by_state.values()),
    }
    return bundle, report
