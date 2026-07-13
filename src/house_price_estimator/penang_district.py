"""Legacy Penang benchmark retained only for existing pickle compatibility.

New ingestion uses :class:`data_sources.PenangOpenDataAdapter`; new modelling
uses the generic aggregate workflow in :mod:`data_pipeline`.
"""
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


DISTRICT_COLUMNS = {
    "Daerah Timur Laut": "Timur Laut (George Town / northeast island)",
    "Daerah Barat Daya": "Barat Daya (southwest island / Teluk Bahang)",
    "Daerah Utara": "Seberang Perai Utara",
    "Daerah Tengah": "Seberang Perai Tengah",
    "Daerah Selatan": "Seberang Perai Selatan",
}
EXCLUDED_TYPES = {"Vacant Plot", "Others", "Total"}
FEATURES = ["district", "property_type", "quarter"]


@dataclass
class DistrictPropertyMedianModel:
    """Transparent baseline that predicts a training median for each segment."""

    medians: dict[tuple[str, str], float]
    overall: float

    @classmethod
    def fit(cls, records: pd.DataFrame) -> "DistrictPropertyMedianModel":
        values = records.groupby(["district", "property_type"])["average_price_rm"].median()
        return cls(
            {tuple(key): float(value) for key, value in values.items()},
            float(records["average_price_rm"].median()),
        )

    def predict(self, records: pd.DataFrame) -> np.ndarray:
        return np.asarray([
            self.medians.get((row.district, row.property_type), self.overall)
            for row in records.itertuples()
        ])


def load_penang_district_transactions(directory: str | Path) -> pd.DataFrame:
    """Join transaction counts and values and calculate average completed prices."""
    root = Path(directory)
    counts = pd.read_csv(root / "residential_transaction_counts_2017.csv", skiprows=2)
    values = pd.read_csv(
        root / "residential_transaction_values_rm_million_2017.csv", skiprows=2
    )
    observations: list[dict[str, Any]] = []
    for row_number, count_row in counts.iterrows():
        property_type = str(count_row["PRO_TYPE"]).strip()
        if property_type in EXCLUDED_TYPES:
            continue
        quarter = int(str(count_row["QUARTER"]).split()[0].removeprefix("Q"))
        value_row = values.iloc[row_number]
        for source_column, district in DISTRICT_COLUMNS.items():
            count = pd.to_numeric(count_row[source_column], errors="coerce")
            total_value = pd.to_numeric(value_row[source_column], errors="coerce")
            if pd.isna(count) or pd.isna(total_value) or count <= 0 or total_value <= 0:
                continue
            observations.append(
                {
                    "state": "Penang",
                    "district": district,
                    "property_type": property_type,
                    "year": 2017,
                    "quarter": quarter,
                    "transaction_count": int(count),
                    "transaction_value_rm": float(total_value),
                    "average_price_rm": float(total_value) / float(count),
                    "price_type": "completed_transaction_average",
                }
            )
    return pd.DataFrame(observations).sort_values(FEATURES).reset_index(drop=True)


def _model() -> TransformedTargetRegressor:
    preprocessing = ColumnTransformer(
        [
            (
                "categories",
                OneHotEncoder(handle_unknown="ignore"),
                ["district", "property_type"],
            ),
            ("quarter", StandardScaler(), ["quarter"]),
        ]
    )
    pipeline = Pipeline(
        [("preprocessing", preprocessing), ("regressor", Ridge(alpha=1.0))]
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
class PenangDistrictBundle:
    """Model and observed district benchmark lookup."""

    model: Any
    districts: tuple[str, ...]
    property_types: tuple[str, ...]
    observations: dict[str, dict[str, float | int]]
    test_metrics: dict[str, float]
    residual_margin_rm: float
    dataset_version: str = "penang-open-transactions-2017-v1"
    model_version: str = "penang-district-median-v1"

    @staticmethod
    def _key(district: str, property_type: str, quarter: int) -> str:
        return f"{district}|{property_type}|{quarter}"

    def predict(self, *, district: str, property_type: str, quarter: int) -> dict[str, Any]:
        if district not in self.districts:
            raise ValueError(f"Unsupported Penang district: {district}")
        if property_type not in self.property_types:
            raise ValueError(f"Unsupported property type: {property_type}")
        if quarter not in {1, 2, 3, 4}:
            raise ValueError("Quarter must be between 1 and 4")
        frame = pd.DataFrame([[district, property_type, quarter]], columns=FEATURES)
        estimate = max(0.0, float(self.model.predict(frame)[0]))
        observed = self.observations.get(self._key(district, property_type, quarter))
        return {
            "model_estimate": estimate,
            "lower": max(0.0, estimate - self.residual_margin_rm),
            "upper": estimate + self.residual_margin_rm,
            "observed_average": observed["average_price_rm"] if observed else None,
            "transaction_count": observed["transaction_count"] if observed else 0,
        }

    def save(self, path: str | Path) -> None:
        output = Path(path); output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(pickle.dumps(self, protocol=pickle.HIGHEST_PROTOCOL))

    @classmethod
    def load(cls, path: str | Path) -> "PenangDistrictBundle":
        value = pickle.loads(Path(path).read_bytes())
        if not isinstance(value, cls):
            raise TypeError("unexpected Penang district bundle type")
        return value


def train_penang_district_model(data: pd.DataFrame) -> tuple[PenangDistrictBundle, dict[str, Any]]:
    """Train on Q1-Q3 and preserve Q4 as the final model test."""
    train = data[data["quarter"] < 4]
    test = data[data["quarter"] == 4]
    ridge = _model().fit(train[FEATURES], train["average_price_rm"])
    ridge_predicted = ridge.predict(test[FEATURES])
    overall = np.full(len(test), float(train["average_price_rm"].median()))
    segment_model = DistrictPropertyMedianModel.fit(train)
    segment_predicted = segment_model.predict(test[FEATURES])
    ridge_metrics = _metrics(test["average_price_rm"], ridge_predicted)
    segment_metrics = _metrics(test["average_price_rm"], segment_predicted)
    if segment_metrics["mae_rm"] <= ridge_metrics["mae_rm"]:
        model: Any = segment_model
        predicted = segment_predicted
        selected_model = "district_property_type_median"
        selected_metrics = segment_metrics
    else:
        model = ridge
        predicted = ridge_predicted
        selected_model = "log_ridge"
        selected_metrics = ridge_metrics
    residuals = np.abs(test["average_price_rm"].to_numpy() - predicted)
    observations = {
        PenangDistrictBundle._key(row.district, row.property_type, row.quarter): {
            "average_price_rm": float(row.average_price_rm),
            "transaction_count": int(row.transaction_count),
        }
        for row in data.itertuples()
    }
    bundle = PenangDistrictBundle(
        model=model,
        districts=tuple(sorted(data["district"].unique())),
        property_types=tuple(sorted(data["property_type"].unique())),
        observations=observations,
        test_metrics=selected_metrics,
        residual_margin_rm=float(np.quantile(residuals, 0.8)),
    )
    return bundle, {
        "dataset_rows": int(len(data)),
        "train_rows": int(len(train)),
        "test_rows": int(len(test)),
        "test_period": "2017 Q4",
        "selected_model": selected_model,
        "model": bundle.test_metrics,
        "log_ridge": ridge_metrics,
        "overall_median_baseline": _metrics(test["average_price_rm"], overall),
        "district_property_type_median_baseline": segment_metrics,
        "districts": list(bundle.districts),
        "property_types": list(bundle.property_types),
    }
