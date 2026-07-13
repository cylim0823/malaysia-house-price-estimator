"""UI-independent validation, coverage, range, and prediction business logic."""
from __future__ import annotations
from dataclasses import dataclass,asdict
from typing import Any
import numpy as np
from .bundle import PredictionBundle
from .cleaning.normalization import normalize_property_type,normalize_state
from .synthetic import SYNTHETIC_LABEL

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
