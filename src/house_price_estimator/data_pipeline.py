"""Validation, reporting, weighted baselines, and lookup for aggregate transactions."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import itertools
import json
from pathlib import Path
import pickle
import re
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd

from .cleaning.normalization import normalize_state


REQUIRED_COLUMNS = (
    "state",
    "district",
    "property_type",
    "year",
    "quarter",
    "transaction_count",
    "transaction_value_rm",
    "average_price_rm",
    "price_type",
)
MODEL_FEATURES = ("state", "district", "property_type", "year", "quarter")
FORBIDDEN_MODEL_FEATURES = {"transaction_value_rm", "transaction_count"}
AGGREGATE_KEY = ("state", "district", "property_type", "year", "quarter")
SCHEMA_VERSION = "aggregate-1.0.0"
DATASET_VERSION = "unspecified-aggregate-dataset"
SOURCE_NAME = "Unspecified approved aggregate source"
SOURCE_URL = ""
SOURCE_VALUE_URL = ""
SOURCE_DOCUMENT = "Unspecified aggregate source document"
SOURCE_TABLE = "Unspecified source table"
COLLECTED_AT = ""

PROPERTY_TYPE_MAP = {
    "1 - 1 1/2 Storey Semi-Detached": "one_to_one_half_storey_semi_detached",
    "1 - 1 1/2 Storey Terraced": "one_to_one_half_storey_terraced",
    "2 - 2 1/2 Storey Semi-Detached": "two_to_two_half_storey_semi_detached",
    "2 - 2 1/2 Storey Terraced": "two_to_two_half_storey_terraced",
    "Cluster House": "cluster_house",
    "Condominium/Apartment": "condominium_apartment",
    "Detached": "detached",
    "Flat": "flat",
    "Low-Cost Flat": "low_cost_flat",
    "Low-Cost House": "low_cost_house",
    "Town House": "town_house",
}


def volume_support(count: int) -> str:
    if count < 5:
        return "very_low_volume"
    if count < 20:
        return "low_volume"
    if count < 100:
        return "medium_volume"
    return "high_volume"


def normalize_district(value: object) -> tuple[str, str | None]:
    """Separate a conservative parenthetical annotation from the district name."""
    raw = str(value).strip()
    if not raw:
        return "", None
    match = re.fullmatch(r"(.+?)\s*\((.+)\)\s*", raw)
    if not match:
        return raw, None
    return match.group(1).strip(), match.group(2).strip()


def normalize_aggregate_property_type(value: object) -> str:
    raw = str(value).strip()
    if raw not in PROPERTY_TYPE_MAP:
        raise ValueError(f"unknown aggregate property type: {raw!r}")
    return PROPERTY_TYPE_MAP[raw]


def _number(value: object) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if np.isfinite(result) else None


def _integer(value: object) -> int | None:
    number = _number(value)
    if number is None or not number.is_integer():
        return None
    return int(number)


def _period_bounds(year: int, quarter: int) -> tuple[str, str]:
    period = pd.Period(year=year, quarter=quarter, freq="Q")
    return period.start_time.date().isoformat(), period.end_time.date().isoformat()


@dataclass
class AggregateProcessingResult:
    processed: pd.DataFrame
    rejected: pd.DataFrame
    quality_report: dict[str, Any]


def validate_aggregate_frame(
    frame: pd.DataFrame, *, metadata: Mapping[str, Any] | None = None
) -> AggregateProcessingResult:
    """Validate and normalize aggregate rows without changing the input frame."""
    missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError("missing required aggregate columns: " + ", ".join(missing))

    source = dict(metadata or {})
    records: list[dict[str, Any]] = []
    for source_row, raw in frame.reset_index(drop=True).iterrows():
        errors: list[str] = []
        warnings: list[str] = []
        state_raw = "" if pd.isna(raw["state"]) else str(raw["state"]).strip()
        district_raw = "" if pd.isna(raw["district"]) else str(raw["district"]).strip()
        type_raw = "" if pd.isna(raw["property_type"]) else str(raw["property_type"]).strip()

        try:
            state = normalize_state(state_raw)
        except ValueError:
            state = ""
            errors.append("UNKNOWN_STATE")
        district, district_notes = normalize_district(district_raw)
        if not district_raw:
            errors.append("MISSING_DISTRICT")
        try:
            property_type = normalize_aggregate_property_type(type_raw)
        except ValueError:
            property_type = ""
            errors.append("MISSING_PROPERTY_TYPE" if not type_raw else "UNKNOWN_PROPERTY_TYPE")

        year = _integer(raw["year"])
        quarter = _integer(raw["quarter"])
        count = _integer(raw["transaction_count"])
        value = _number(raw["transaction_value_rm"])
        average = _number(raw["average_price_rm"])
        price_type_raw = "" if pd.isna(raw["price_type"]) else str(raw["price_type"]).strip()

        if year is None or year < 1900 or year > date.today().year:
            errors.append("INVALID_YEAR")
        if quarter not in {1, 2, 3, 4}:
            errors.append("INVALID_QUARTER")
        if count is None or count <= 0:
            errors.append("INVALID_TRANSACTION_COUNT")
        if value is None or value <= 0:
            errors.append("INVALID_TRANSACTION_VALUE")
        if average is None or average <= 0:
            errors.append("INVALID_AVERAGE_PRICE")
        if price_type_raw not in {
            "completed_transaction_average",
            "aggregate_completed_transaction_average",
        }:
            errors.append("INVALID_PRICE_TYPE")
        if count and count > 0 and value and value > 0 and average and average > 0:
            expected = value / count
            tolerance = max(0.01, abs(expected) * 1e-9)
            if abs(average - expected) > tolerance:
                errors.append("AVERAGE_CALCULATION_MISMATCH")
        support = volume_support(count) if count and count > 0 else "invalid_volume"
        if support in {"very_low_volume", "low_volume"}:
            warnings.append("LOW_TRANSACTION_VOLUME")
        period_start = period_end = ""
        if year is not None and quarter in {1, 2, 3, 4}:
            period_start, period_end = _period_bounds(year, quarter)

        records.append(
            {
                "source_row": int(source_row) + 2,
                "state_raw": state_raw,
                "state": state,
                "district_raw": district_raw,
                "district": district,
                "district_notes": district_notes,
                "property_type_raw": type_raw,
                "property_type": property_type,
                "year": year,
                "quarter": quarter,
                "period_start": period_start,
                "period_end": period_end,
                "transaction_count": count,
                "transaction_value_rm": value,
                "average_price_rm": average,
                "price_type": "completed_transaction_average",
                "volume_support": support,
                "source_name": source.get("source_name", SOURCE_NAME),
                "source_dataset": source.get("source_dataset", ""),
                "source_url": source.get("source_url", SOURCE_URL),
                "source_document": source.get("source_document", SOURCE_DOCUMENT),
                "source_page": source.get("source_page"),
                "source_page_or_table": source.get("source_page_or_table", SOURCE_TABLE),
                "collected_at": source.get("collected_at", COLLECTED_AT),
                "dataset_version": source.get("dataset_version", DATASET_VERSION),
                "schema_version": source.get("schema_version", SCHEMA_VERSION),
                "validation_errors": errors,
                "validation_warnings": warnings,
            }
        )

    output = pd.DataFrame(records)
    valid_keys = output[list(AGGREGATE_KEY)].notna().all(axis=1)
    duplicate_mask = output.loc[valid_keys].duplicated(list(AGGREGATE_KEY), keep=False)
    for index in output.loc[valid_keys].index[duplicate_mask]:
        output.at[index, "validation_errors"].append("DUPLICATE_AGGREGATE_ROW")

    eligible_for_change = output[output["validation_errors"].map(len).eq(0)].copy()
    eligible_for_change = eligible_for_change.sort_values(
        ["state", "district", "property_type", "year", "quarter"]
    )
    prior = eligible_for_change.groupby(
        ["state", "district", "property_type"], sort=False
    )["average_price_rm"].shift(1)
    changes = (eligible_for_change["average_price_rm"] - prior).abs() / prior
    output["quarter_change_percent"] = np.nan
    output.loc[eligible_for_change.index, "quarter_change_percent"] = changes * 100
    suspicious_indices = eligible_for_change.index[changes > 0.75]
    for index in suspicious_indices:
        output.at[index, "validation_warnings"].append("SUSPICIOUS_QUARTER_CHANGE")

    output["validation_status"] = output.apply(
        lambda row: (
            "invalid"
            if row["validation_errors"]
            else "valid_with_warnings"
            if row["validation_warnings"]
            else "valid"
        ),
        axis=1,
    )
    output["model_eligible"] = output["validation_status"].ne("invalid")
    output["public_prediction_supported"] = (
        output["model_eligible"] & output["transaction_count"].ge(20)
    )
    output["model_exclusion_reason"] = output.apply(
        lambda row: (
            ";".join(row["validation_errors"])
            if row["validation_errors"]
            else ""
        ),
        axis=1,
    )
    output["public_prediction_exclusion_reason"] = output.apply(
        lambda row: (
            "invalid_record"
            if not row["model_eligible"]
            else "low_transaction_volume"
            if not row["public_prediction_supported"]
            else ""
        ),
        axis=1,
    )
    output["validation_errors"] = output["validation_errors"].map(json.dumps)
    output["validation_warnings"] = output["validation_warnings"].map(json.dumps)
    output["validation_notes"] = output.apply(
        lambda row: json.dumps(
            {
                "errors": json.loads(row["validation_errors"]),
                "warnings": json.loads(row["validation_warnings"]),
            }
        ),
        axis=1,
    )

    processed = output[output["validation_status"].ne("invalid")].reset_index(drop=True)
    rejected = output[output["validation_status"].eq("invalid")].reset_index(drop=True)
    report = aggregate_quality_report(output)
    return AggregateProcessingResult(processed, rejected, report)


def load_and_validate_aggregate_csv(
    path: str | Path, *, metadata: Mapping[str, Any] | None = None
) -> AggregateProcessingResult:
    return validate_aggregate_frame(pd.read_csv(path), metadata=metadata)


def _count_by(frame: pd.DataFrame, column: str) -> dict[str, int]:
    return {str(key): int(value) for key, value in frame[column].value_counts().items()}


def aggregate_quality_report(frame: pd.DataFrame) -> dict[str, Any]:
    valid = frame[frame["validation_status"].ne("invalid")]
    warning_rows = frame[frame["validation_status"].eq("valid_with_warnings")]
    errors = list(itertools.chain.from_iterable(
        json.loads(value) if isinstance(value, str) else value
        for value in frame["validation_errors"]
    ))
    warnings = list(itertools.chain.from_iterable(
        json.loads(value) if isinstance(value, str) else value
        for value in frame["validation_warnings"]
    ))
    dimensions = [
        sorted(valid[column].dropna().unique().tolist())
        for column in ("state", "district", "property_type", "year", "quarter")
    ]
    actual_keys = {
        tuple(row) for row in valid[list(AGGREGATE_KEY)].itertuples(index=False, name=None)
    }
    expected_keys = set(itertools.product(*dimensions)) if all(dimensions) else set()
    missing = sorted(expected_keys - actual_keys)
    actual_periods = {
        (int(row.year), int(row.quarter)) for row in valid.itertuples()
    }
    if actual_periods:
        first_period = min(actual_periods)
        last_period = max(actual_periods)
        complete_periods = [
            (year, quarter)
            for year in range(first_period[0], last_period[0] + 1)
            for quarter in range(1, 5)
            if first_period <= (year, quarter) <= last_period
        ]
    else:
        first_period = last_period = None
        complete_periods = []
    missing_periods = [period for period in complete_periods if period not in actual_periods]
    actual_state_periods = {
        (str(row.state), int(row.year), int(row.quarter)) for row in valid.itertuples()
    }
    missing_state_periods = [
        (state, year, quarter)
        for state in sorted(valid["state"].dropna().unique().tolist())
        for year, quarter in complete_periods
        if (state, year, quarter) not in actual_state_periods
    ]
    years = sorted(int(value) for value in valid["year"].unique())
    missing_years = (
        sorted(set(range(years[0], years[-1] + 1)) - set(years)) if years else []
    )
    return {
        "dataset_version": (
            str(valid["dataset_version"].iloc[0]) if len(valid) else DATASET_VERSION
        ),
        "aggregate_row_count": int(len(frame)),
        "valid_row_count": int(len(valid)),
        "warning_row_count": int(len(warning_rows)),
        "rejected_row_count": int(frame["validation_status"].eq("invalid").sum()),
        "duplicate_combination_rows": int(errors.count("DUPLICATE_AGGREGATE_ROW")),
        "arithmetic_mismatch_rows": int(errors.count("AVERAGE_CALCULATION_MISMATCH")),
        "suspicious_quarter_change_rows": int(warnings.count("SUSPICIOUS_QUARTER_CHANGE")),
        "extraction_warning_count": sum(
            1 for warning in warnings if str(warning).startswith("EXTRACTION_")
        ),
        "suspicious_quarter_changes": [
            {
                "source_row": int(row.source_row),
                "state": row.state,
                "district": row.district,
                "property_type": row.property_type,
                "year": int(row.year),
                "quarter": int(row.quarter),
                "quarter_change_percent": float(row.quarter_change_percent),
                "transaction_count": int(row.transaction_count),
                "average_price_rm": float(row.average_price_rm),
                "status": "review_only_not_automatically_an_error",
            }
            for row in frame.itertuples()
            if "SUSPICIOUS_QUARTER_CHANGE" in (
                json.loads(row.validation_warnings)
                if isinstance(row.validation_warnings, str)
                else row.validation_warnings
            )
        ],
        "aggregate_row_count_is_not_transaction_count": True,
        "sum_of_transaction_count": int(valid["transaction_count"].sum()),
        "sum_of_transaction_value_rm": float(valid["transaction_value_rm"].sum()),
        "states": sorted(valid["state"].unique().tolist()),
        "districts": sorted(valid["district"].unique().tolist()),
        "property_types": sorted(valid["property_type"].unique().tolist()),
        "years": years,
        "quarters": sorted(int(value) for value in valid["quarter"].unique()),
        "earliest_year": int(valid["year"].min()) if len(valid) else None,
        "latest_year": int(valid["year"].max()) if len(valid) else None,
        "earliest_period": (
            {"year": first_period[0], "quarter": first_period[1]}
            if first_period else None
        ),
        "latest_period": (
            {"year": last_period[0], "quarter": last_period[1]}
            if last_period else None
        ),
        "missing_years": missing_years,
        "missing_quarters": [
            {"year": year, "quarter": quarter} for year, quarter in missing_periods
        ],
        "missing_state_period_combination_count": len(missing_state_periods),
        "missing_state_period_combinations": [
            {"state": state, "year": year, "quarter": quarter}
            for state, year, quarter in missing_state_periods
        ],
        "very_low_transaction_volume_rows": int(
            valid["volume_support"].eq("very_low_volume").sum()
        ),
        "volume_support_rows": _count_by(valid, "volume_support"),
        "transaction_count_distribution": {
            str(key): float(value)
            for key, value in valid["transaction_count"].describe().items()
        },
        "missing_combination_count": len(missing),
        "missing_combinations": [list(item) for item in missing],
        "coverage_by_state": _count_by(valid, "state"),
        "coverage_by_district": _count_by(valid, "district"),
        "coverage_by_property_type": _count_by(valid, "property_type"),
    }


def weighted_regression_metrics(
    actual: Iterable[float], predicted: Iterable[float], weights: Iterable[float]
) -> dict[str, float | None]:
    y = np.asarray(list(actual), dtype=float)
    p = np.asarray(list(predicted), dtype=float)
    w = np.asarray(list(weights), dtype=float)
    if not len(y) or len(y) != len(p) or len(y) != len(w):
        raise ValueError("actual, predicted, and weights must have equal non-zero length")
    if np.any(w <= 0):
        raise ValueError("weights must be positive")
    errors = y - p
    weighted_mean = float(np.average(y, weights=w))
    denominator = float(np.sum(w * (y - weighted_mean) ** 2))
    weighted_mape = float(np.average(np.abs(errors) / np.abs(y), weights=w) * 100)
    return {
        "mae_rm": float(np.mean(np.abs(errors))),
        "median_absolute_error_rm": float(np.median(np.abs(errors))),
        "rmse_rm": float(np.sqrt(np.mean(errors**2))),
        "mape_percent": float(np.mean(np.abs(errors) / np.abs(y)) * 100),
        "r2": (
            1 - float(np.sum(errors**2)) / float(np.sum((y - y.mean()) ** 2))
            if float(np.sum((y - y.mean()) ** 2))
            else None
        ),
        "weighted_mae_rm": float(np.average(np.abs(errors), weights=w)),
        "weighted_rmse_rm": float(np.sqrt(np.average(errors**2, weights=w))),
        "weighted_mape_percent": weighted_mape,
        "weighted_r2": (
            1 - float(np.sum(w * errors**2)) / denominator if denominator else None
        ),
        "aggregate_rows": int(len(y)),
        "transactions_represented": int(w.sum()),
    }


@dataclass
class WeightedMeanBaseline:
    group_fields: tuple[str, ...]
    group_values: dict[tuple[str, ...], float] | None = None
    overall: float | None = None

    def fit(self, records: pd.DataFrame) -> "WeightedMeanBaseline":
        if records.empty:
            raise ValueError("cannot train aggregate baseline on empty records")
        self.overall = float(
            np.average(records["average_price_rm"], weights=records["transaction_count"])
        )
        self.group_values = {}
        if self.group_fields:
            for key, group in records.groupby(list(self.group_fields)):
                normalized_key = key if isinstance(key, tuple) else (key,)
                self.group_values[tuple(map(str, normalized_key))] = float(
                    np.average(group["average_price_rm"], weights=group["transaction_count"])
                )
        return self

    def predict(self, records: pd.DataFrame) -> np.ndarray:
        if self.overall is None or self.group_values is None:
            raise RuntimeError("aggregate baseline is not fitted")
        return np.asarray(
            [
                self.group_values.get(
                    tuple(str(getattr(row, field)) for field in self.group_fields),
                    self.overall,
                )
                for row in records.itertuples()
            ]
        )


@dataclass
class PreviousPeriodBaseline:
    values: dict[tuple[str, str, str, int, int], float] | None = None
    fallback: WeightedMeanBaseline | None = None

    def fit(self, records: pd.DataFrame) -> "PreviousPeriodBaseline":
        self.values = {
            (
                str(row.state),
                str(row.district),
                str(row.property_type),
                int(row.year),
                int(row.quarter),
            ): float(row.average_price_rm)
            for row in records.itertuples()
        }
        self.fallback = WeightedMeanBaseline(
            ("state", "district", "property_type")
        ).fit(records)
        return self

    def predict(self, records: pd.DataFrame) -> np.ndarray:
        if self.values is None or self.fallback is None:
            raise RuntimeError("previous-period baseline is not fitted")
        fallback_values = self.fallback.predict(records)
        predictions: list[float] = []
        for index, row in enumerate(records.itertuples()):
            year, quarter = int(row.year), int(row.quarter) - 1
            if quarter == 0:
                year, quarter = year - 1, 4
            key = (str(row.state), str(row.district), str(row.property_type), year, quarter)
            predictions.append(self.values.get(key, float(fallback_values[index])))
        return np.asarray(predictions)


def aggregate_baseline_candidates() -> dict[str, Any]:
    return {
        "overall_weighted_average": WeightedMeanBaseline(()),
        "state_weighted_average": WeightedMeanBaseline(("state",)),
        "district_weighted_average": WeightedMeanBaseline(("state", "district")),
        "property_type_weighted_average": WeightedMeanBaseline(("property_type",)),
        "segment_weighted_average": WeightedMeanBaseline(
            ("state", "district", "property_type")
        ),
        "previous_quarter_average": PreviousPeriodBaseline(),
    }


@dataclass
class AggregateTransactionBundle:
    model: Any
    selected_baseline: str
    observations: dict[str, dict[str, Any]]
    test_metrics: dict[str, float | None]
    supported_test_period: str
    dataset_version: str = DATASET_VERSION
    model_version: str = "aggregate-weighted-baseline-v1"

    @staticmethod
    def _key(
        state: str, district: str, property_type: str, year: int, quarter: int
    ) -> str:
        return f"{state}|{district}|{property_type}|{year}|{quarter}"

    @property
    def states(self) -> tuple[str, ...]:
        return tuple(sorted({key.split("|", 1)[0] for key in self.observations}))

    def districts(self, state: str) -> tuple[str, ...]:
        values = {
            key.split("|")[1]
            for key in self.observations
            if key.startswith(f"{state}|")
        }
        if not values:
            raise ValueError(f"Unsupported aggregate state: {state}")
        return tuple(sorted(values))

    def property_types(self, state: str, district: str) -> tuple[str, ...]:
        prefix = f"{state}|{district}|"
        values = {key.split("|")[2] for key in self.observations if key.startswith(prefix)}
        if not values:
            raise ValueError(f"Unsupported aggregate district for {state}: {district}")
        return tuple(sorted(values))

    def periods(self, state: str, district: str, property_type: str) -> tuple[tuple[int, int], ...]:
        prefix = f"{state}|{district}|{property_type}|"
        values = {
            (int(key.split("|")[3]), int(key.split("|")[4]))
            for key in self.observations
            if key.startswith(prefix)
        }
        if not values:
            raise ValueError("Unsupported aggregate state/district/property-type combination")
        return tuple(sorted(values))

    def predict(
        self,
        *,
        state: str,
        district: str,
        property_type: str,
        year: int,
        quarter: int,
    ) -> dict[str, Any]:
        if state not in self.states:
            raise ValueError(f"Unsupported aggregate state: {state}")
        if district not in self.districts(state):
            raise ValueError(f"Unsupported aggregate district for {state}: {district}")
        if property_type not in self.property_types(state, district):
            raise ValueError("Unsupported aggregate property type for selected district")
        key = self._key(state, district, property_type, year, quarter)
        if key not in self.observations:
            raise ValueError("Unsupported aggregate period for selected segment")
        observed = self.observations[key]
        frame = pd.DataFrame(
            [[state, district, property_type, year, quarter]], columns=MODEL_FEATURES
        )
        estimate = (
            float(self.model.predict(frame)[0])
            if self.supported_test_period == f"{year} Q{quarter}"
            else None
        )
        nearby = [
            value
            for candidate, value in self.observations.items()
            if candidate.startswith(f"{state}|{district}|{property_type}|")
        ]
        return {
            "estimated_average_price_rm": estimate,
            "observed_average_price_rm": observed["average_price_rm"],
            "transaction_count": observed["transaction_count"],
            "volume_support": observed["volume_support"],
            "public_prediction_supported": observed["public_prediction_supported"],
            "baseline_used": self.selected_baseline,
            "available_date_range": (
                f"{min((item['year'], item['quarter']) for item in self.observations.values())[0]} "
                f"Q{min((item['year'], item['quarter']) for item in self.observations.values())[1]}–"
                f"{max((item['year'], item['quarter']) for item in self.observations.values())[0]} "
                f"Q{max((item['year'], item['quarter']) for item in self.observations.values())[1]}"
            ),
            "nearby_historical_quarters": sorted(
                nearby, key=lambda item: (item["year"], item["quarter"])
            ),
            "dataset_version": self.dataset_version,
            "prediction_meaning": (
                "Average completed transaction price for a district-property-type-period group; "
                "not a specific property's value."
            ),
        }

    def save(self, path: str | Path) -> None:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(pickle.dumps(self, protocol=pickle.HIGHEST_PROTOCOL))

    @classmethod
    def load(cls, path: str | Path) -> "AggregateTransactionBundle":
        value = pickle.loads(Path(path).read_bytes())
        if not isinstance(value, cls):
            raise TypeError("unexpected aggregate transaction bundle type")
        return value


def _slice_metrics(test: pd.DataFrame, predictions: np.ndarray) -> dict[str, Any]:
    report: dict[str, Any] = {}
    for column in ("state", "district", "property_type", "year", "quarter", "volume_support"):
        groups: dict[str, Any] = {}
        for value, indices in test.groupby(column).groups.items():
            positions = test.index.get_indexer(indices)
            group = test.loc[indices]
            if len(group) < 3 or int(group["transaction_count"].sum()) < 20:
                continue
            groups[str(value)] = weighted_regression_metrics(
                group["average_price_rm"], predictions[positions], group["transaction_count"]
            )
        report[column] = groups
    return report


def train_aggregate_baselines(
    processed: pd.DataFrame,
) -> tuple[AggregateTransactionBundle, dict[str, Any]]:
    """Evaluate the latest available period after fitting all earlier periods."""
    eligible = processed[processed["model_eligible"]].copy()
    periods = sorted({(int(row.year), int(row.quarter)) for row in eligible.itertuples()})
    if len(periods) < 2:
        raise ValueError("at least two periods are required for temporal evaluation")
    test_year, test_quarter = periods[-1]
    train_start_year, train_start_quarter = periods[0]
    train_end_year, train_end_quarter = periods[-2]
    if train_start_year == train_end_year:
        train_period_label = (
            f"{train_start_year}_q{train_start_quarter}_q{train_end_quarter}"
        )
    else:
        train_period_label = (
            f"{train_start_year}_q{train_start_quarter}_to_"
            f"{train_end_year}_q{train_end_quarter}"
        )
    is_test = eligible["year"].eq(test_year) & eligible["quarter"].eq(test_quarter)
    train = eligible[~is_test].reset_index(drop=True)
    test = eligible[is_test].reset_index(drop=True)
    if train.empty or test.empty:
        raise ValueError("Q1-Q3 training and Q4 test rows are required")
    metrics: dict[str, Any] = {}
    models: dict[str, Any] = {}
    predictions_by_name: dict[str, np.ndarray] = {}
    for name, candidate in aggregate_baseline_candidates().items():
        candidate.fit(train)
        predictions = candidate.predict(test)
        models[name] = candidate
        predictions_by_name[name] = predictions
        metrics[name] = weighted_regression_metrics(
            test["average_price_rm"], predictions, test["transaction_count"]
        )
    selected = min(metrics, key=lambda name: metrics[name]["weighted_mae_rm"])
    selected_predictions = predictions_by_name[selected]
    observations = {
        AggregateTransactionBundle._key(
            row.state, row.district, row.property_type, int(row.year), int(row.quarter)
        ): {
            "state": row.state,
            "district": row.district,
            "property_type": row.property_type,
            "year": int(row.year),
            "quarter": int(row.quarter),
            "average_price_rm": float(row.average_price_rm),
            "transaction_count": int(row.transaction_count),
            "volume_support": row.volume_support,
            "public_prediction_supported": bool(row.public_prediction_supported),
        }
        for row in eligible.itertuples()
    }
    bundle = AggregateTransactionBundle(
        model=models[selected],
        selected_baseline=selected,
        observations=observations,
        test_metrics=metrics[selected],
        supported_test_period=f"{test_year} Q{test_quarter}",
        dataset_version=str(eligible["dataset_version"].iloc[0]),
    )
    report = {
        "dataset_version": str(eligible["dataset_version"].iloc[0]),
        "prediction_target": "average_price_rm",
        "model_features": list(MODEL_FEATURES),
        "forbidden_model_features": sorted(FORBIDDEN_MODEL_FEATURES),
        "sample_weight": "transaction_count",
        "temporal_limitation": (
            "Latest-period evaluation is provisional and does not validate current-market "
            "or multi-year forecasting without suitable temporal coverage."
        ),
        "split_strategy": (
            f"train_{train_period_label}_test_{test_year}_q{test_quarter}"
        ),
        "train_aggregate_rows": int(len(train)),
        "train_transactions": int(train["transaction_count"].sum()),
        "test_aggregate_rows": int(len(test)),
        "test_transactions": int(test["transaction_count"].sum()),
        "selected_baseline": selected,
        "selected_metrics": metrics[selected],
        "baseline_metrics": metrics,
        "slice_metrics": _slice_metrics(test, selected_predictions),
        "advanced_models_trained": [],
        "advanced_models_reason": "Insufficient multi-year temporal coverage",
    }
    return bundle, report
