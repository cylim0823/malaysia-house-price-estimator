"""Dependency-free project configuration with JSON loading."""

from __future__ import annotations
from dataclasses import asdict, dataclass
import json
from pathlib import Path
from . import SCHEMA_VERSION

@dataclass(frozen=True)
class ProjectConfig:
    schema_version: str = SCHEMA_VERSION
    dataset_version: str = "synthetic-demo-v1"
    random_seed: int = 42
    duplicate_tolerance: float = .75
    validation_fraction: float = .2
    test_fraction: float = .2
    split_strategy: str = "time_group"
    minimum_segment_size: int = 10
    supported_target_type: str = "asking"
    model_candidates: tuple[str, ...] = ("median", "group_median", "linear")

    @classmethod
    def load(cls, path: str | Path) -> "ProjectConfig":
        values=json.loads(Path(path).read_text(encoding="utf-8")); values["model_candidates"]=tuple(values.get("model_candidates", cls.model_candidates))
        return cls(**values)
    def to_dict(self): return asdict(self)

