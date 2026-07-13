"""Trusted-local model bundle persistence and compatibility checks."""
from __future__ import annotations
from dataclasses import dataclass,field
from datetime import datetime,timezone
from pathlib import Path
import pickle
from typing import Any
from . import SCHEMA_VERSION

@dataclass
class PredictionBundle:
    model:Any; model_version:str; dataset_version:str; supported_price_type:str
    supported_states:tuple[str,...]; supported_districts:tuple[str,...]; supported_property_types:tuple[str,...]
    validation_metrics:dict[str,Any]; residual_quantiles:tuple[float,float]; segment_counts:dict[str,int]
    schema_version:str=SCHEMA_VERSION; feature_set_version:str="1.0.0"; training_timestamp:str=field(default_factory=lambda:datetime.now(timezone.utc).isoformat()); is_synthetic:bool=False
    def save(self,path:str|Path)->None:
        target=Path(path);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(pickle.dumps(self,protocol=pickle.HIGHEST_PROTOCOL))
    @classmethod
    def load(cls,path:str|Path,*,trusted:bool=False)->"PredictionBundle":
        if not trusted: raise ValueError("refusing to load pickle without trusted=True; never load untrusted model files")
        value=pickle.loads(Path(path).read_bytes())
        if not isinstance(value,cls):raise ValueError("file is not a prediction bundle")
        if value.schema_version!=SCHEMA_VERSION:raise ValueError(f"incompatible schema version: {value.schema_version}")
        return value

