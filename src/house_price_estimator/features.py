"""Training-only feature encoder with stable unknown-category handling."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
import numpy as np

NUMERIC_FEATURES=("built_up_sqft","land_area_sqft","bedrooms","additional_bedrooms","bathrooms","storeys","property_age_years","record_year","record_month")
CATEGORICAL_FEATURES=("state","district","property_type","property_subtype","tenure","furnishing","price_type")
FORBIDDEN_FEATURES={"price","source_url","record_id","price_per_sqft","validation_notes","duplicate_group_id","data_split"}

@dataclass
class FeatureEncoder:
    categories: dict[str,tuple[str,...]]=field(default_factory=dict); medians: dict[str,float]=field(default_factory=dict); fitted: bool=False
    def fit(self, records:list[dict[str,Any]]) -> "FeatureEncoder":
        if not records: raise ValueError("cannot fit features on empty records")
        for key in NUMERIC_FEATURES:
            values=sorted(float(r[key]) for r in records if r.get(key) is not None); self.medians[key]=values[len(values)//2] if values else 0.0
        for key in CATEGORICAL_FEATURES: self.categories[key]=tuple(sorted({str(r.get(key) or "__MISSING__") for r in records}))
        self.fitted=True; return self
    def transform(self, records:list[dict[str,Any]]) -> np.ndarray:
        if not self.fitted: raise RuntimeError("feature encoder must be fitted on training data")
        rows=[]
        for record in records:
            row=[float(record.get(k) if record.get(k) is not None else self.medians[k]) for k in NUMERIC_FEATURES]
            for key in CATEGORICAL_FEATURES:
                value=str(record.get(key) or "__MISSING__"); row.extend(1.0 if value==category else 0.0 for category in self.categories[key])
            rows.append(row)
        return np.asarray(rows,dtype=float)
    def feature_names(self)->list[str]: return list(NUMERIC_FEATURES)+[f"{key}={cat}" for key in CATEGORICAL_FEATURES for cat in self.categories.get(key,())]

