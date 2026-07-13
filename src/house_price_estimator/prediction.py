"""UI-independent validation, coverage, range, and prediction business logic."""
from __future__ import annotations
from dataclasses import dataclass,asdict
from typing import Any
import numpy as np
from .bundle import PredictionBundle
from .cleaning.normalization import normalize_property_type,normalize_state
from .synthetic_data import SYNTHETIC_LABEL
from .data_sources import DatasetMetadata
from .location_catalog import CoverageCatalog

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
                nearby_periods=tuple(raw["nearby_historical_quarters"]),
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
                nearby_periods=(),
                model_name=str(self.bundle.selected_model),
                dataset_version=str(self.bundle.dataset_version),
            )
        raise ValueError(f"Unsupported historical model kind: {self.metadata.model_kind}")
