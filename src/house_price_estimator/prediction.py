"""UI-independent validation, coverage, range, and prediction business logic."""
from __future__ import annotations
from dataclasses import dataclass,asdict
from datetime import date
from typing import Any
import numpy as np
from .bundle import PredictionBundle
from .cleaning.normalization import normalize_property_type,normalize_state
from .synthetic_data import SYNTHETIC_LABEL
from .data_sources import DatasetMetadata
from .location_catalog import CoverageCatalog
from .features import CATEGORICAL_FEATURES, NUMERIC_FEATURES
from .ui_contracts import (
    InformationDisclosure,
    PropertyFormSubmission,
    build_information_disclosure,
)
from .real_transactions import MODEL_FEATURES as REAL_PROPERTY_MODEL_FEATURES
from .real_transactions import RealPropertyBundle

@dataclass(frozen=True)
class PredictionResult:
    estimate:float; lower:float; upper:float; price_per_sqft:float|None; asking_price_assessment:str|None; support_status:str
    limitations:tuple[str,...]; model_metadata:dict[str,Any]; important_factors:tuple[str,...]; synthetic_disclaimer:str|None=None
    def to_dict(self):return asdict(self)

class PredictionService:
    def __init__(self,bundle:PredictionBundle):self.bundle=bundle
    def predict(self,values:dict[str,Any])->PredictionResult:
        missing=[k for k in ("state","district","property_type","built_up_sqft") if values.get(k) in (None,"")]
        if missing:raise ValueError("missing required inputs: "+", ".join(missing))
        state=normalize_state(values["state"]);kind=normalize_property_type(values["property_type"]);district=str(values["district"]).strip()
        if state not in self.bundle.supported_states:raise ValueError(f"unsupported state: {state}")
        if district not in self.bundle.supported_districts:raise ValueError(f"unsupported district: {district}")
        if kind not in self.bundle.supported_property_types:raise ValueError(f"unsupported property type: {kind}")
        area=float(values["built_up_sqft"])
        if area<=0 or area>100000:raise ValueError("built_up_sqft is outside valid input limits")
        record=dict(values,state=state,district=district,property_type=kind,price_type=self.bundle.supported_price_type)
        estimate=float(self.bundle.model.predict([record])[0]); low_q,high_q=self.bundle.residual_quantiles;lower=max(0,estimate+low_q);upper=max(lower,estimate+high_q)
        count=self.bundle.segment_counts.get(f"{state}|{district}|{kind}",0)
        if count == 0: raise ValueError("unsupported state, district, and property-type combination")
        support="high_support" if count>=100 else "medium_support" if count>=30 else "low_support"
        asking=values.get("asking_price");assessment=None
        if asking is not None:
            assessment="Below estimated range" if float(asking)<lower else "Above estimated range" if float(asking)>upper else "Within estimated range"
        return PredictionResult(estimate,lower,upper,estimate/area if area else None,assessment,support,
          ("Educational estimate; not an official valuation.","Coverage and error bands require validation with licensed real data."),
          {"model_version":self.bundle.model_version,"dataset_version":self.bundle.dataset_version,"schema_version":self.bundle.schema_version},
          ("built_up_sqft","state","district","property_type"),SYNTHETIC_LABEL if self.bundle.is_synthetic else None)


SYNTHETIC_FORM_MODEL_FEATURES = frozenset(
    (set(NUMERIC_FEATURES) | set(CATEGORICAL_FEATURES))
    & {
        "state",
        "district",
        "property_type",
        "property_subtype",
        "built_up_sqft",
        "land_area_sqft",
        "bedrooms",
        "additional_bedrooms",
        "bathrooms",
        "storeys",
        "property_age_years",
        "tenure",
        "furnishing",
    }
)


@dataclass(frozen=True)
class SyntheticPropertyDemoResult:
    """Explicitly synthetic result with a complete parameter-use audit."""

    estimate: float
    lower: float
    upper: float
    price_per_sqft: float | None
    asking_price_assessment: str | None
    support_status: str
    synthetic_segment: str
    disclosure: InformationDisclosure
    model_features: tuple[str, ...]


class SyntheticPropertyDemoService:
    """Run the fictional property bundle with optional, nullable form values."""

    def __init__(self, bundle: PredictionBundle) -> None:
        if not bundle.is_synthetic:
            raise ValueError("synthetic property demo requires a synthetic bundle")
        self.bundle = bundle

    def _segment(self, state: str, property_type: str) -> tuple[str, int]:
        candidates: list[tuple[str, int]] = []
        for key, count in self.bundle.segment_counts.items():
            candidate_state, district, candidate_type = key.split("|", 2)
            if candidate_state == state and candidate_type == property_type:
                candidates.append((district, int(count)))
        if not candidates:
            raise ValueError(
                "The synthetic demo has no fictional segment for this state and property type"
            )
        return max(candidates, key=lambda item: (item[1], item[0]))

    def predict(
        self, submission: PropertyFormSubmission
    ) -> SyntheticPropertyDemoResult:
        values = submission.values
        state = normalize_state(values["state"])
        property_type = normalize_property_type(values["property_type"])
        if state not in self.bundle.supported_states:
            raise ValueError(f"unsupported synthetic state: {state}")
        if property_type not in self.bundle.supported_property_types:
            raise ValueError(f"unsupported synthetic property type: {property_type}")
        synthetic_segment, count = self._segment(state, property_type)
        record = {
            feature: values.get(feature) for feature in SYNTHETIC_FORM_MODEL_FEATURES
        }
        record.update(
            {
                "state": state,
                "district": synthetic_segment,
                "property_type": property_type,
                "price_type": self.bundle.supported_price_type,
                "record_year": None,
                "record_month": None,
            }
        )
        estimate = float(self.bundle.model.predict([record])[0])
        low_q, high_q = self.bundle.residual_quantiles
        lower = max(0.0, estimate + low_q)
        upper = max(lower, estimate + high_q)
        asking = values.get("asking_price")
        asking_assessment = None
        if asking is not None:
            asking_assessment = (
                "Below estimated range"
                if float(asking) < lower
                else "Above estimated range"
                if float(asking) > upper
                else "Within estimated range"
            )
        area = values.get("built_up_sqft")
        disclosure = build_information_disclosure(
            submission,
            model_features=SYNTHETIC_FORM_MODEL_FEATURES,
            additionally_used=("asking_price",) if asking is not None else (),
        )
        return SyntheticPropertyDemoResult(
            estimate=estimate,
            lower=lower,
            upper=upper,
            price_per_sqft=estimate / float(area) if area is not None else None,
            asking_price_assessment=asking_assessment,
            support_status=(
                "high_support" if count >= 100 else "medium_support" if count >= 30 else "low_support"
            ),
            synthetic_segment=synthetic_segment,
            disclosure=disclosure,
            model_features=tuple(sorted(SYNTHETIC_FORM_MODEL_FEATURES)),
        )


@dataclass(frozen=True)
class RealPropertyEstimateResult:
    estimate: float
    lower: float
    upper: float
    price_per_sqft: float | None
    asking_price_assessment: str | None
    support_status: str
    support_count: int
    disclosure: InformationDisclosure
    model_features: tuple[str, ...]
    latest_period: str
    model_version: str
    dataset_version: str


class RealPropertyService:
    """Validate and disclose predictions from the separate real transaction model."""

    FORM_MODEL_FEATURES = frozenset(
        {"state", "district", "property_type", "tenure", "built_up_sqft", "land_area_sqft", "floor_level"}
    )

    def __init__(self, bundle: RealPropertyBundle) -> None:
        self.bundle = bundle

    def predict(self, submission: PropertyFormSubmission) -> RealPropertyEstimateResult:
        values = submission.values
        if not values.get("district"):
            raise ValueError("District is required by the active real property model")
        prediction = self.bundle.predict(values)
        asking = values.get("asking_price")
        assessment = None
        if asking is not None:
            assessment = (
                "Below estimated range" if float(asking) < prediction.lower
                else "Above estimated range" if float(asking) > prediction.upper
                else "Within estimated range"
            )
        area = values.get("built_up_sqft")
        disclosure = build_information_disclosure(
            submission,
            model_features=self.FORM_MODEL_FEATURES,
            additionally_used=("asking_price",) if asking is not None else (),
        )
        return RealPropertyEstimateResult(
            estimate=prediction.estimate,
            lower=prediction.lower,
            upper=prediction.upper,
            price_per_sqft=prediction.estimate / float(area) if area else None,
            asking_price_assessment=assessment,
            support_status=(
                "high_support" if prediction.support_count >= 100
                else "medium_support" if prediction.support_count >= 30
                else "low_support"
            ),
            support_count=prediction.support_count,
            disclosure=disclosure,
            model_features=tuple(REAL_PROPERTY_MODEL_FEATURES),
            latest_period=prediction.latest_period,
            model_version=prediction.model_version,
            dataset_version=prediction.dataset_version,
        )


@dataclass(frozen=True)
class HistoricalResult:
    """Source-neutral result returned by every historical explorer."""

    observed_average_price_rm: float
    model_estimate_rm: float | None
    lower_rm: float | None
    upper_rm: float | None
    transaction_count: int | None
    volume_support: str | None
    public_prediction_supported: bool
    nearby_periods: tuple[dict[str, Any], ...]
    model_name: str
    dataset_version: str


class HistoricalExplorer:
    """Reusable selectors and prediction interface for historical datasets."""

    def __init__(self, metadata: DatasetMetadata, bundle: Any) -> None:
        self.metadata = metadata
        self.bundle = bundle
        self.coverage = CoverageCatalog.from_observation_keys(bundle.observations)

    def latest_period(
        self, state: str, area: str, property_type: str
    ) -> tuple[int, int]:
        periods = [
            (item.year, item.quarter)
            for item in self.coverage.combinations
            if item.state == state
            and item.area == area
            and item.property_type == property_type
        ]
        if not periods:
            raise ValueError("Unsupported state/area/property-type combination")
        return max(periods)

    def history(
        self, state: str, area: str, property_type: str
    ) -> tuple[dict[str, Any], ...]:
        prefix = f"{state}|{area}|{property_type}|"
        history: list[dict[str, Any]] = []
        for key, observation in self.bundle.observations.items():
            if not key.startswith(prefix):
                continue
            _, _, _, year, quarter = key.split("|", 4)
            if isinstance(observation, dict):
                history.append(
                    {
                        "year": int(year),
                        "quarter": int(quarter),
                        "average_price_rm": float(observation["average_price_rm"]),
                        "transaction_count": int(observation["transaction_count"]),
                        "volume_support": str(observation["volume_support"]),
                    }
                )
            else:
                history.append(
                    {
                        "year": int(year),
                        "quarter": int(quarter),
                        "average_price_rm": float(observation),
                        "transaction_count": None,
                        "volume_support": None,
                    }
                )
        return tuple(sorted(history, key=lambda item: (item["year"], item["quarter"])))

    def predict(
        self,
        *,
        state: str,
        area: str,
        property_type: str,
        year: int,
        quarter: int,
    ) -> HistoricalResult:
        if quarter not in self.coverage.quarters(state, area, property_type, year):
            raise ValueError("Unsupported historical combination")
        if self.metadata.model_kind == "aggregate_transactions":
            raw = self.bundle.predict(
                state=state,
                district=area,
                property_type=property_type,
                year=year,
                quarter=quarter,
            )
            estimate = raw["estimated_average_price_rm"]
            return HistoricalResult(
                observed_average_price_rm=float(raw["observed_average_price_rm"]),
                model_estimate_rm=float(estimate) if estimate is not None else None,
                lower_rm=None,
                upper_rm=None,
                transaction_count=int(raw["transaction_count"]),
                volume_support=str(raw["volume_support"]),
                public_prediction_supported=bool(raw["public_prediction_supported"]),
                nearby_periods=self.history(state, area, property_type),
                model_name=str(raw["baseline_used"]),
                dataset_version=str(raw["dataset_version"]),
            )
        if self.metadata.model_kind == "published_averages":
            raw = self.bundle.predict(
                state=state,
                area=area,
                property_type=property_type,
                year=year,
                quarter=quarter,
            )
            return HistoricalResult(
                observed_average_price_rm=float(raw["observed_average"]),
                model_estimate_rm=float(raw["model_estimate"]),
                lower_rm=float(raw["lower"]),
                upper_rm=float(raw["upper"]),
                transaction_count=None,
                volume_support=None,
                public_prediction_supported=True,
                nearby_periods=self.history(state, area, property_type),
                model_name=str(self.bundle.selected_model),
                dataset_version=str(self.bundle.dataset_version),
            )
        raise ValueError(f"Unsupported historical model kind: {self.metadata.model_kind}")


def period_age_months(period: tuple[int, int], *, as_of: date | None = None) -> int:
    """Return whole-month age from the end of a calendar quarter."""
    today = as_of or date.today()
    year, quarter = period
    end_month = quarter * 3
    return max(0, (today.year - year) * 12 + today.month - end_month)


def limited_recency_message(
    period: tuple[int, int], *, as_of: date | None = None
) -> str | None:
    """Warn when the latest validated segment observation is over 12 months old."""
    if period_age_months(period, as_of=as_of) <= 12:
        return None
    return (
        "Limited recency: the latest validated data for this selection is from "
        f"{period[0]} Q{period[1]}."
    )
