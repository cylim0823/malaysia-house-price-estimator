"""Regional residential price benchmarks from licensed JPPH open data."""
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

from house_price_estimator.regional_terraced import load_regional_terraced_prices


FEATURES = ["state", "area", "property_type", "year", "quarter"]
HIGHRISE_LOCATIONS = {
    "Kuala Lumpur Central": ("Kuala Lumpur", "KL Central"),
    "Kuala Lumpur North": ("Kuala Lumpur", "KL North"),
    "Kuala Lumpur South": ("Kuala Lumpur", "KL South"),
    "Kuala Lumpur": ("Kuala Lumpur", "State average"),
    "Petaling": ("Selangor", "Petaling"),
    "Hulu Langat": ("Selangor", "Hulu Langat"),
    "Selangor": ("Selangor", "State average"),
    "Johor": ("Johor", "State average"),
    "Pulau Pinang (Island)": ("Penang", "Pulau Pinang (Island)"),
    "Seberang Perai": ("Penang", "Seberang Perai"),
    "Pulau Pinang": ("Penang", "State average"),
    "Negeri Sembilan": ("Negeri Sembilan", "State average"),
    "Melaka": ("Melaka", "State average"),
    "Sabah": ("Sabah", "State average"),
}


def load_highrise_prices(path: str | Path) -> pd.DataFrame:
    """Normalize the high-rise workbook and discard its national summary row."""
    raw = pd.read_excel(path, header=3)
    data = raw.melt(
        id_vars=["HIGH RISE"],
        var_name="period_label",
        value_name="average_price_rm",
    ).rename(columns={"HIGH RISE": "source_location"})
    data = data[data["source_location"].isin(HIGHRISE_LOCATIONS)].copy()
    locations = data["source_location"].map(HIGHRISE_LOCATIONS)
    data["state"] = locations.str[0]
    data["area"] = locations.str[1]
    periods = data["period_label"].astype(str).str.extract(r"(\d{4})_Q(\d)")
    data["year"] = pd.to_numeric(periods[0], errors="coerce")
    data["quarter"] = pd.to_numeric(periods[1], errors="coerce")
    data["average_price_rm"] = pd.to_numeric(data["average_price_rm"], errors="coerce")
    data = data.dropna(subset=["state", "area", "year", "quarter", "average_price_rm"])
    data["year"] = data["year"].astype(int)
    data["quarter"] = data["quarter"].astype(int)
    data["property_type"] = "High-rise unit"
    data["price_type"] = "published_average"
    return data[
        ["state", "area", "property_type", "year", "quarter", "average_price_rm", "price_type"]
    ].reset_index(drop=True)


def load_regional_area_prices(
    terraced_path: str | Path, highrise_path: str | Path
) -> pd.DataFrame:
    """Combine compatible terraced and high-rise official area observations."""
    terraced = load_regional_terraced_prices(terraced_path).drop(columns=["period"])
    highrise = load_highrise_prices(highrise_path)
    combined = pd.concat([terraced, highrise], ignore_index=True)
    combined["period"] = combined["year"] * 4 + combined["quarter"]
    return combined.sort_values(
        ["period", "state", "area", "property_type"]
    ).reset_index(drop=True)


def _ridge() -> TransformedTargetRegressor:
    preprocessing = ColumnTransformer(
        [
            (
                "categories",
                OneHotEncoder(handle_unknown="ignore"),
                ["state", "area", "property_type"],
            ),
            ("time", StandardScaler(), ["year", "quarter"]),
        ]
    )
    return TransformedTargetRegressor(
        regressor=Pipeline(
            [("preprocessing", preprocessing), ("regressor", Ridge(alpha=0.1))]
        ),
        func=np.log1p,
        inverse_func=np.expm1,
    )


def _metrics(actual: pd.Series, predicted: np.ndarray) -> dict[str, float]:
    return {
        "mae_rm": float(mean_absolute_error(actual, predicted)),
        "rmse_rm": float(mean_squared_error(actual, predicted) ** 0.5),
        "r2": float(r2_score(actual, predicted)),
    }


@dataclass
class LocationPropertyMedianModel:
    medians: dict[tuple[str, str, str], float]
    overall: float

    @classmethod
    def fit(cls, records: pd.DataFrame) -> "LocationPropertyMedianModel":
        values = records.groupby(
            ["state", "area", "property_type"]
        )["average_price_rm"].median()
        return cls(
            {tuple(key): float(value) for key, value in values.items()},
            float(records["average_price_rm"].median()),
        )

    def predict(self, records: pd.DataFrame) -> np.ndarray:
        return np.asarray(
            [
                self.medians.get(
                    (row.state, row.area, row.property_type), self.overall
                )
                for row in records.itertuples()
            ]
        )


@dataclass
class RegionalAreaBundle:
    """Selected model, strict location/type coverage, and observation lookup."""

    model: Any
    property_types_by_location: dict[str, tuple[str, ...]]
    observations: dict[str, float]
    test_metrics: dict[str, float]
    residual_margin_rm: float
    selected_model: str
    dataset_version: str = "jpph-regional-area-2016-2018q2-v1"
    model_version: str = "regional-area-log-ridge-v1"

    @staticmethod
    def _location_key(state: str, area: str) -> str:
        return f"{state}|{area}"

    @staticmethod
    def _observation_key(
        state: str, area: str, property_type: str, year: int, quarter: int
    ) -> str:
        return f"{state}|{area}|{property_type}|{year}|{quarter}"

    @property
    def states(self) -> tuple[str, ...]:
        return tuple(sorted({key.split("|", 1)[0] for key in self.property_types_by_location}))

    @property
    def areas_by_state(self) -> dict[str, tuple[str, ...]]:
        return {
            state: tuple(
                sorted(
                    key.split("|", 1)[1]
                    for key in self.property_types_by_location
                    if key.startswith(f"{state}|")
                )
            )
            for state in self.states
        }

    def property_types(self, state: str, area: str) -> tuple[str, ...]:
        try:
            return self.property_types_by_location[self._location_key(state, area)]
        except KeyError as exc:
            raise ValueError(f"Unsupported area for {state}: {area}") from exc

    def predict(
        self,
        *,
        state: str,
        area: str,
        property_type: str,
        year: int,
        quarter: int,
    ) -> dict[str, float]:
        if state not in self.states:
            raise ValueError(f"Unsupported state: {state}")
        if property_type not in self.property_types(state, area):
            raise ValueError(
                f"Unsupported property type for {state}, {area}: {property_type}"
            )
        if year not in {2016, 2017, 2018}:
            raise ValueError("Regional coverage is limited to 2016-2018")
        if quarter not in {1, 2, 3, 4} or (year == 2018 and quarter > 2):
            raise ValueError("The regional datasets end at 2018 Q2")
        frame = pd.DataFrame(
            [[state, area, property_type, year, quarter]], columns=FEATURES
        )
        estimate = max(0.0, float(self.model.predict(frame)[0]))
        observed = self.observations.get(
            self._observation_key(state, area, property_type, year, quarter)
        )
        return {
            "model_estimate": estimate,
            "lower": max(0.0, estimate - self.residual_margin_rm),
            "upper": estimate + self.residual_margin_rm,
            "observed_average": (
                float(observed) if observed is not None else float("nan")
            ),
        }

    def save(self, path: str | Path) -> None:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(pickle.dumps(self, protocol=pickle.HIGHEST_PROTOCOL))

    @classmethod
    def load(cls, path: str | Path) -> "RegionalAreaBundle":
        value = pickle.loads(Path(path).read_bytes())
        if not isinstance(value, cls):
            raise TypeError("unexpected regional area bundle type")
        return value


def train_regional_area_model(
    data: pd.DataFrame,
) -> tuple[RegionalAreaBundle, dict[str, Any]]:
    """Train through 2017 and evaluate once on the 2018 Q1-Q2 holdout."""
    train = data[data["year"] < 2018]
    test = data[data["year"] == 2018]
    ridge = _ridge().fit(train[FEATURES], train["average_price_rm"])
    ridge_predicted = ridge.predict(test[FEATURES])
    median_model = LocationPropertyMedianModel.fit(train)
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
        selected_model = "location_property_median"
        selected_metrics = median_metrics
    residuals = np.abs(test["average_price_rm"].to_numpy() - predicted)
    property_types_by_location = {
        RegionalAreaBundle._location_key(state, area): tuple(
            sorted(group["property_type"].unique())
        )
        for (state, area), group in data.groupby(["state", "area"])
    }
    observations = {
        RegionalAreaBundle._observation_key(
            row.state, row.area, row.property_type, row.year, row.quarter
        ): float(row.average_price_rm)
        for row in data.itertuples()
    }
    bundle = RegionalAreaBundle(
        model=model,
        property_types_by_location=property_types_by_location,
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
        "location_property_median_baseline": median_metrics,
        "states": list(bundle.states),
        "state_count": len(bundle.states),
        "location_count": len(property_types_by_location),
        "rows_by_property_type": {
            str(key): int(value)
            for key, value in data["property_type"].value_counts().items()
        },
    }
    return bundle, report
