"""Baseline-first regression models and validation comparison."""
from __future__ import annotations
from dataclasses import dataclass,field
from datetime import datetime,timezone
from statistics import median
from typing import Any,Protocol
import numpy as np
from .features import FeatureEncoder

class Regressor(Protocol):
    def fit(self,records:list[dict[str,Any]])->Any: ...
    def predict(self,records:list[dict[str,Any]])->np.ndarray: ...

@dataclass
class MedianRegressor:
    group_fields:tuple[str,...]=(); overall:float|None=None; groups:dict[tuple[str,...],float]=field(default_factory=dict)
    def fit(self,records):
        if not records: raise ValueError("cannot train on empty records")
        self.overall=float(median(float(r["price"]) for r in records)); grouped={}
        for r in records: grouped.setdefault(tuple(str(r.get(k) or "") for k in self.group_fields),[]).append(float(r["price"]))
        self.groups={k:float(median(v)) for k,v in grouped.items()}; return self
    def predict(self,records):
        if self.overall is None: raise RuntimeError("model is not fitted")
        return np.asarray([self.groups.get(tuple(str(r.get(k) or "") for k in self.group_fields),self.overall) for r in records])

@dataclass
class LinearRegressor:
    alpha:float=1.0; encoder:FeatureEncoder=field(default_factory=FeatureEncoder); coefficients:np.ndarray|None=None
    def fit(self,records):
        x=self.encoder.fit(records).transform(records); y=np.asarray([float(r["price"]) for r in records]); x=np.column_stack([np.ones(len(x)),x])
        penalty=np.eye(x.shape[1])*self.alpha; penalty[0,0]=0; self.coefficients=np.linalg.pinv(x.T@x+penalty)@x.T@y; return self
    def predict(self,records):
        if self.coefficients is None: raise RuntimeError("model is not fitted")
        x=self.encoder.transform(records); return np.column_stack([np.ones(len(x)),x])@self.coefficients

@dataclass
class EncodedSklearnRegressor:
    estimator: Any
    encoder: FeatureEncoder = field(default_factory=FeatureEncoder)
    log_target: bool = False
    def fit(self, records):
        x=self.encoder.fit(records).transform(records); y=np.asarray([float(r["price"]) for r in records]);self.estimator.fit(x,np.log1p(y) if self.log_target else y);return self
    def predict(self, records):
        values=np.asarray(self.estimator.predict(self.encoder.transform(records)),float);return np.expm1(values) if self.log_target else values

def optional_sklearn_models(seed:int=42)->dict[str,Any]:
    try:
        from sklearn.ensemble import HistGradientBoostingRegressor,RandomForestRegressor
        from sklearn.neighbors import KNeighborsRegressor
        return {"random_forest":EncodedSklearnRegressor(RandomForestRegressor(n_estimators=100,max_depth=12,random_state=seed,n_jobs=-1)),
                "hist_gradient_boosting":EncodedSklearnRegressor(HistGradientBoostingRegressor(max_iter=100,random_state=seed)),
                "hist_gradient_boosting_log":EncodedSklearnRegressor(HistGradientBoostingRegressor(max_iter=100,random_state=seed),log_target=True),
                "knn_experiment":EncodedSklearnRegressor(KNeighborsRegressor(n_neighbors=7))}
    except ImportError:return {}

def optional_catboost_model(seed:int=42)->dict[str,Any]:
    try:
        from catboost import CatBoostRegressor
        return {"catboost":EncodedSklearnRegressor(CatBoostRegressor(iterations=200,depth=6,verbose=False,random_seed=seed))}
    except ImportError:return {}

@dataclass
class ModelMetadata:
    model_version:str; schema_version:str; feature_set_version:str; dataset_version:str; trained_at:str; model_name:str

def baseline_candidates()->dict[str,Regressor]:
    return {"overall_median":MedianRegressor(),"state_median":MedianRegressor(("state",)),"segment_median":MedianRegressor(("state","district","property_type")),"linear_ridge":LinearRegressor()}

def all_candidates(seed:int=42)->dict[str,Regressor]:
    return baseline_candidates() | optional_sklearn_models(seed) | optional_catboost_model(seed)
