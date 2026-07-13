"""Cleaning, time-safe training, and prediction for NAPIC open transactions."""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
from pathlib import Path
import pickle
from typing import Any, Iterable

import numpy as np
import pandas as pd

from .data_sources import NapicOpenTransactionAdapter
from .evaluation import regression_metrics
from .location_catalog import MALAYSIAN_STATES, normalize_state


NUMERIC_FEATURES = (
    "built_up_sqft",
    "land_area_sqft",
    "unit_level",
    "record_year",
    "record_month",
)
CATEGORICAL_FEATURES = ("state", "district", "property_type", "tenure")
MODEL_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES
SQM_TO_SQFT = 10.76391041671


@dataclass
class RealTransactionEncoder:
    """Training-only median and ordinal encoder with explicit unknown handling."""

    medians: dict[str, float] = field(default_factory=dict)
    categories: dict[str, tuple[str, ...]] = field(default_factory=dict)

    def fit(self, frame: pd.DataFrame) -> "RealTransactionEncoder":
        if frame.empty:
            raise ValueError("cannot fit an empty transaction frame")
        self.medians = {
            name: float(frame[name].median()) if frame[name].notna().any() else 0.0
            for name in NUMERIC_FEATURES
        }
        self.categories = {
            name: tuple(sorted(frame[name].fillna("__MISSING__").astype(str).unique()))
            for name in CATEGORICAL_FEATURES
        }
        return self

    def transform(self, frame: pd.DataFrame) -> np.ndarray:
        if not self.medians or not self.categories:
            raise RuntimeError("transaction encoder is not fitted")
        columns: list[np.ndarray] = []
        for name in NUMERIC_FEATURES:
            values = pd.to_numeric(frame.get(name), errors="coerce")
            columns.append(values.fillna(self.medians[name]).to_numpy(dtype=float))
        for name in CATEGORICAL_FEATURES:
            mapping = {value: index for index, value in enumerate(self.categories[name])}
            values = frame[name].fillna("__MISSING__").astype(str).map(mapping).fillna(-1)
            columns.append(values.to_numpy(dtype=float))
        return np.column_stack(columns)


@dataclass
class HierarchicalMedianModel:
    """Transparent state/district/property-type baseline with safe fallbacks."""

    overall: float | None = None
    groups: dict[tuple[str, ...], float] = field(default_factory=dict)

    def fit(self, frame: pd.DataFrame) -> "HierarchicalMedianModel":
        self.overall = float(frame["price"].median())
        self.groups = {}
        for fields in (("state",), ("state", "property_type"), ("state", "district", "property_type")):
            for key, value in frame.groupby(list(fields))["price"].median().items():
                normalized = key if isinstance(key, tuple) else (key,)
                self.groups[tuple(map(str, normalized))] = float(value)
        return self

    def predict(self, frame: pd.DataFrame) -> np.ndarray:
        if self.overall is None:
            raise RuntimeError("median model is not fitted")
        predictions: list[float] = []
        for row in frame.itertuples():
            keys = (
                (str(row.state), str(row.district), str(row.property_type)),
                (str(row.state), str(row.property_type)),
                (str(row.state),),
            )
            predictions.append(next((self.groups[key] for key in keys if key in self.groups), self.overall))
        return np.asarray(predictions)


@dataclass
class EncodedTransactionModel:
    estimator: Any
    encoder: RealTransactionEncoder = field(default_factory=RealTransactionEncoder)
    log_target: bool = True

    def fit(self, frame: pd.DataFrame) -> "EncodedTransactionModel":
        features = self.encoder.fit(frame).transform(frame)
        target = frame["price"].to_numpy(dtype=float)
        self.estimator.fit(features, np.log1p(target) if self.log_target else target)
        return self

    def predict(self, frame: pd.DataFrame) -> np.ndarray:
        values = np.asarray(self.estimator.predict(self.encoder.transform(frame)), dtype=float)
        return np.expm1(values) if self.log_target else values


@dataclass(frozen=True)
class RealPropertyPrediction:
    estimate: float
    lower: float
    upper: float
    support_count: int
    latest_period: str
    model_version: str
    dataset_version: str


@dataclass
class RealPropertyBundle:
    model: Any
    model_name: str
    residual_quantiles: tuple[float, float]
    segment_counts: dict[str, int]
    supported_combinations: tuple[tuple[str, str, str], ...]
    evaluation: dict[str, Any]
    dataset_version: str
    latest_period: str
    model_version: str = "napic-open-transactions-v1"
    price_type: str = "completed_transaction"

    @property
    def states(self) -> tuple[str, ...]:
        return tuple(sorted({item[0] for item in self.supported_combinations}))

    def districts(self, state: str) -> tuple[str, ...]:
        canonical = normalize_state(state)
        return tuple(sorted({item[1] for item in self.supported_combinations if item[0] == canonical}))

    def property_types(self, state: str, district: str) -> tuple[str, ...]:
        canonical = normalize_state(state)
        return tuple(sorted({item[2] for item in self.supported_combinations if item[:2] == (canonical, district)}))

    def predict(self, values: dict[str, Any]) -> RealPropertyPrediction:
        state = normalize_state(values.get("state"))
        district = str(values.get("district") or "").strip()
        property_type = str(values.get("property_type") or "").strip()
        if (state, district, property_type) not in self.supported_combinations:
            raise ValueError("Unsupported state, district, and property-type combination")
        frame = pd.DataFrame([{
            "state": state,
            "district": district,
            "property_type": property_type,
            "tenure": values.get("tenure"),
            "built_up_sqft": values.get("built_up_sqft"),
            "land_area_sqft": values.get("land_area_sqft"),
            "unit_level": values.get("floor_level"),
            "record_year": 2026,
            "record_month": 3,
        }])
        estimate = max(0.0, float(self.model.predict(frame)[0]))
        lower = max(0.0, estimate + self.residual_quantiles[0])
        upper = max(lower, estimate + self.residual_quantiles[1])
        key = "|".join((state, district, property_type))
        return RealPropertyPrediction(
            estimate, lower, upper, self.segment_counts.get(key, 0), self.latest_period,
            self.model_version, self.dataset_version,
        )

    def save(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(pickle.dumps(self, protocol=pickle.HIGHEST_PROTOCOL))

    @classmethod
    def load(cls, path: str | Path) -> "RealPropertyBundle":
        value = pickle.loads(Path(path).read_bytes())
        if not isinstance(value, cls):
            raise TypeError("unexpected real property bundle type")
        return value


def load_napic_snapshots(directory: str | Path) -> pd.DataFrame:
    root = Path(directory)
    frames = []
    for state in MALAYSIAN_STATES:
        path = root / f"{state.lower().replace(' ', '_')}.csv"
        if not path.is_file():
            raise FileNotFoundError(f"missing NAPIC state snapshot: {path}")
        frames.append(NapicOpenTransactionAdapter(state).parse(path.read_bytes()))
    return pd.concat(frames, ignore_index=True)


def prepare_real_transactions(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Create model fields, traceable duplicate groups, flags, and exclusions."""
    frame = raw.copy()
    frame["price"] = frame["transaction_price_rm"]
    frame["built_up_sqft"] = frame["main_floor_area_sqm"] * SQM_TO_SQFT
    frame["land_area_sqft"] = frame["land_parcel_area_sqm"] * SQM_TO_SQFT
    frame["record_year"] = frame["transaction_date"].dt.year
    frame["record_month"] = frame["transaction_date"].dt.month
    frame["record_date"] = frame["transaction_date"].dt.date.astype(str)
    duplicate_fields = [
        "state", "district_raw", "mukim_raw", "property_type_raw", "road_name_raw",
        "scheme_name_area_raw", "tenure_raw", "transaction_month_raw",
        "transaction_price_rm_raw", "land_parcel_area_raw", "main_floor_area_raw",
        "unit_level_raw",
    ]
    signatures = frame[duplicate_fields].fillna("").astype(str).agg("|".join, axis=1)
    frame["duplicate_group_id"] = signatures.map(
        lambda value: "napic-" + hashlib.sha256(value.encode("utf-8")).hexdigest()[:20]
    )
    group_sizes = frame.groupby("duplicate_group_id")["duplicate_group_id"].transform("size")
    frame["duplicate_status"] = np.where(group_sizes > 1, "exact_duplicate", "unique")
    frame["duplicate_matching_method"] = "exact_full_published_attributes"
    frame["duplicate_matching_confidence"] = np.where(group_sizes > 1, 1.0, 0.0)
    frame["canonical_record"] = ~frame.duplicated("duplicate_group_id", keep="first")
    invalid = (
        frame["price"].isna() | frame["price"].le(0) | frame["district"].isna()
        | frame["property_type"].isna() | frame["transaction_date"].isna()
    )
    frame["model_exclusion_reason"] = np.where(invalid, "invalid_required_field", "")
    frame.loc[~frame["canonical_record"], "model_exclusion_reason"] = "exact_duplicate_noncanonical"
    frame["model_eligible"] = frame["model_exclusion_reason"].eq("")
    quartiles = frame.groupby("property_type")["price"].transform(
        lambda values: (values - values.median()).abs() > 6 * (values.quantile(.75) - values.quantile(.25))
    )
    frame["outlier_status"] = np.where(quartiles, "possible_outlier_retained", "not_flagged")
    report = {
        "raw_rows": int(len(frame)),
        "model_eligible_rows": int(frame["model_eligible"].sum()),
        "states": sorted(frame["state"].unique().tolist()),
        "district_count": int(frame["district"].nunique()),
        "property_types": sorted(frame["property_type"].unique().tolist()),
        "earliest_transaction_month": frame["transaction_date"].min().date().isoformat(),
        "latest_transaction_month": frame["transaction_date"].max().date().isoformat(),
        "exact_duplicate_rows": int(frame["duplicate_status"].eq("exact_duplicate").sum()),
        "possible_outlier_rows_retained": int(frame["outlier_status"].eq("possible_outlier_retained").sum()),
        "missing_main_floor_area_rows": int(frame["built_up_sqft"].isna().sum()),
        "missing_land_area_rows": int(frame["land_area_sqft"].isna().sum()),
        "source_warning_rows": int(frame["validation_status"].eq("needs_review").sum()),
    }
    return frame, report


def _slice_metrics(frame: pd.DataFrame, predictions: Iterable[float]) -> dict[str, Any]:
    values = frame.copy()
    values["prediction"] = list(predictions)
    values["price_band"] = pd.cut(
        values["price"], [0, 200_000, 500_000, 1_000_000, 2_000_000, np.inf],
        labels=["<=200k", "200k-500k", "500k-1m", "1m-2m", ">2m"],
    )
    report: dict[str, Any] = {}
    for field in ("state", "district", "property_type", "price_band"):
        report[field] = {
            str(name): {"count": int(len(group)), **regression_metrics(group["price"], group["prediction"])}
            for name, group in values.groupby(field, observed=True)
            if len(group) >= 20
        }
    return report


def train_real_property_model(
    prepared: pd.DataFrame, *, dataset_version: str
) -> tuple[RealPropertyBundle, dict[str, Any]]:
    eligible = prepared[prepared["model_eligible"]].copy()
    train = eligible[eligible["transaction_date"] < "2025-01-01"].copy()
    validation = eligible[
        (eligible["transaction_date"] >= "2025-01-01")
        & (eligible["transaction_date"] < "2025-10-01")
    ].copy()
    test = eligible[eligible["transaction_date"] >= "2025-10-01"].copy()
    if min(len(train), len(validation), len(test)) == 0:
        raise ValueError("time split requires pre-2025, 2025 Q1-Q3, and 2025 Q4+ records")

    candidates: dict[str, Any] = {
        "hierarchical_median": HierarchicalMedianModel().fit(train)
    }
    try:
        from sklearn.ensemble import HistGradientBoostingRegressor

        estimator = HistGradientBoostingRegressor(
            learning_rate=0.08, max_iter=180, max_leaf_nodes=31,
            l2_regularization=1.0, random_state=42,
            categorical_features=list(range(len(NUMERIC_FEATURES), len(MODEL_FEATURES))),
        )
        candidates["hist_gradient_boosting_log"] = EncodedTransactionModel(estimator).fit(train)
    except ImportError:
        pass
    validation_metrics = {
        name: regression_metrics(validation["price"], model.predict(validation))
        for name, model in candidates.items()
    }
    selected_name = min(validation_metrics, key=lambda name: validation_metrics[name]["mae"])
    selected = candidates[selected_name]
    validation_predictions = selected.predict(validation)
    residuals = validation["price"].to_numpy(dtype=float) - validation_predictions
    test_predictions = selected.predict(test)
    test_metrics = regression_metrics(test["price"], test_predictions)
    counts = eligible.groupby(["state", "district", "property_type"]).size()
    supported_counts = counts[counts >= 30]
    combinations = tuple(tuple(map(str, key)) for key in supported_counts.index.tolist())
    bundle = RealPropertyBundle(
        model=selected,
        model_name=selected_name,
        residual_quantiles=(float(np.quantile(residuals, .1)), float(np.quantile(residuals, .9))),
        segment_counts={"|".join(map(str, key)): int(value) for key, value in counts.items()},
        supported_combinations=combinations,
        evaluation=test_metrics,
        dataset_version=dataset_version,
        latest_period="2026 Q1",
    )
    report = {
        "dataset_version": dataset_version,
        "target": "completed_transaction_price_rm",
        "model_features": list(MODEL_FEATURES),
        "split_strategy": "train_through_2024_validation_2025_q1_q3_test_2025_q4_to_2026_q1",
        "train_rows": len(train), "validation_rows": len(validation), "test_rows": len(test),
        "validation_metrics": validation_metrics,
        "selected_model": selected_name,
        "residual_quantiles_from_validation": list(bundle.residual_quantiles),
        "test_metrics": test_metrics,
        "minimum_supported_segment_records": 30,
        "supported_segment_count": len(supported_counts),
        "test_slices": _slice_metrics(test, test_predictions),
        "limitations": [
            "No bedrooms, bathrooms, car parks, furnishing, age, renovation, or condition fields are published.",
            "Ranges are empirical validation residual intervals, not guarantees.",
            "The final test period is only six months and includes provisional 2026 Q1 data.",
            "District/property-type combinations with fewer than 30 records are not selectable.",
        ],
    }
    return bundle, report
