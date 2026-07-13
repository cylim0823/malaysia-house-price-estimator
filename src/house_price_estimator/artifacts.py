"""Repository-relative application artefact selection and validation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from .data_pipeline import AggregateTransactionBundle, MODEL_FEATURES
from .real_transactions import RealPropertyBundle


PROJECT_ROOT = Path(__file__).resolve().parents[2]
HISTORICAL_MODEL_DIRECTORY = PROJECT_ROOT / "models" / "historical_aggregate"
HISTORICAL_MODEL_METADATA_PATH = HISTORICAL_MODEL_DIRECTORY / "metadata.json"
HISTORICAL_EVALUATION_PATH = HISTORICAL_MODEL_DIRECTORY / "evaluation_summary.json"
INDIVIDUAL_PROPERTY_MODEL_PATH = (
    PROJECT_ROOT / "models" / "individual_property" / "model_bundle.pkl"
)
HISTORICAL_DATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "aggregate_transactions"
    / "malaysia_aggregate_transactions_v1.csv"
)
GENERATED_EVALUATION_DIRECTORY = PROJECT_ROOT / "reports" / "generated" / "evaluation"
GENERATED_DATA_QUALITY_DIRECTORY = PROJECT_ROOT / "reports" / "generated" / "data_quality"
SUPPORTED_HISTORICAL_SCHEMA_VERSION = "aggregate-2.0.0"


class ModelArtifactError(RuntimeError):
    """Raised when an explicitly configured application artefact is unavailable or invalid."""


@dataclass(frozen=True)
class ActiveHistoricalModel:
    bundle: AggregateTransactionBundle
    metadata: dict[str, Any]
    path: Path


def _repository_path(relative_path: str, *, project_root: Path) -> Path:
    candidate = (project_root / relative_path).resolve()
    root = project_root.resolve()
    if candidate != root and root not in candidate.parents:
        raise ModelArtifactError("Configured model path must remain inside the repository")
    return candidate


def load_active_historical_model(
    metadata_path: str | Path = HISTORICAL_MODEL_METADATA_PATH,
    *,
    project_root: Path = PROJECT_ROOT,
) -> ActiveHistoricalModel:
    """Load the one manifest-selected, non-synthetic historical aggregate bundle."""
    manifest_path = Path(metadata_path)
    if not manifest_path.is_file():
        raise ModelArtifactError(f"Active historical model metadata is unavailable: {manifest_path}")
    try:
        metadata = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ModelArtifactError("Active historical model metadata is invalid") from exc
    required = {
        "artifact_path", "artifact_sha256", "model_version", "dataset_version",
        "schema_version", "model_type", "feature_names", "synthetic", "active",
    }
    missing = required - metadata.keys()
    if missing:
        raise ModelArtifactError(
            "Active historical model metadata is missing: " + ", ".join(sorted(missing))
        )
    if metadata["synthetic"] is not False or metadata["active"] is not True:
        raise ModelArtifactError("Production historical model must be active and non-synthetic")
    if metadata["schema_version"] != SUPPORTED_HISTORICAL_SCHEMA_VERSION:
        raise ModelArtifactError(
            f"Incompatible historical schema version: {metadata['schema_version']}"
        )
    if tuple(metadata["feature_names"]) != MODEL_FEATURES:
        raise ModelArtifactError("Historical model feature metadata is incompatible")
    path = _repository_path(metadata["artifact_path"], project_root=project_root)
    if not path.is_file():
        raise ModelArtifactError(f"Active historical model is unavailable: {path}")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != metadata["artifact_sha256"]:
        raise ModelArtifactError("Active historical model checksum does not match metadata")
    try:
        bundle = AggregateTransactionBundle.load(path)
    except (OSError, TypeError, ValueError) as exc:
        raise ModelArtifactError("Active historical model bundle is invalid") from exc
    if bundle.model_version != metadata["model_version"]:
        raise ModelArtifactError("Historical model version does not match metadata")
    if bundle.dataset_version != metadata["dataset_version"]:
        raise ModelArtifactError("Historical dataset version does not match metadata")
    if type(bundle.model).__name__ != metadata["model_type"]:
        raise ModelArtifactError("Historical model type does not match metadata")
    observations = tuple(bundle.observations.values())
    expected = metadata["coverage_counts"]
    actual = {
        "states": len({row["state"] for row in observations}),
        "districts": len({row["district"] for row in observations}),
        "property_types": len({row["property_type"] for row in observations}),
        "years": len({int(row["year"]) for row in observations}),
    }
    if actual != expected:
        raise ModelArtifactError("Historical model coverage does not match metadata")
    if sorted({row["state"] for row in observations}) != metadata["supported_states"]:
        raise ModelArtifactError("Historical supported states do not match metadata")
    if sorted({row["property_type"] for row in observations}) != metadata["supported_property_types"]:
        raise ModelArtifactError("Historical supported property types do not match metadata")
    if sorted({int(row["year"]) for row in observations}) != metadata["supported_years"]:
        raise ModelArtifactError("Historical supported years do not match metadata")
    return ActiveHistoricalModel(bundle=bundle, metadata=metadata, path=path)


def write_historical_model_metadata(
    bundle: AggregateTransactionBundle,
    report: dict[str, Any],
    *,
    model_path: Path = HISTORICAL_MODEL_DIRECTORY / "model_bundle.pkl",
    metadata_path: Path = HISTORICAL_MODEL_METADATA_PATH,
) -> None:
    """Write the authoritative manifest after a reproducible aggregate rebuild."""
    observations = tuple(bundle.observations.values())
    states = sorted({row["state"] for row in observations})
    districts = sorted({row["district"] for row in observations})
    property_types = sorted({row["property_type"] for row in observations})
    years = sorted({int(row["year"]) for row in observations})
    metadata = {
        "model_name": "Malaysia historical aggregate weighted baseline",
        "model_version": bundle.model_version,
        "model_type": type(bundle.model).__name__,
        "target": "average completed transaction price for a district/property-type/quarter group",
        "feature_names": list(MODEL_FEATURES),
        "dataset_name": "Malaysia licensed completed-transaction aggregates",
        "dataset_version": bundle.dataset_version,
        "price_type": "completed_transaction_average",
        "training_timestamp": datetime.now(timezone.utc).isoformat(),
        "schema_version": SUPPORTED_HISTORICAL_SCHEMA_VERSION,
        "artifact_path": model_path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix(),
        "artifact_sha256": hashlib.sha256(model_path.read_bytes()).hexdigest(),
        "evaluation_path": HISTORICAL_EVALUATION_PATH.resolve().relative_to(
            PROJECT_ROOT.resolve()
        ).as_posix(),
        "supported_states": states,
        "supported_districts": {
            "count": len(districts),
            "authoritative_source": "model_bundle.pkl observations",
        },
        "supported_property_types": property_types,
        "supported_years": years,
        "coverage_counts": {
            "states": len(states), "districts": len(districts),
            "property_types": len(property_types), "years": len(years),
        },
        "evaluation_summary": {
            "test_period": bundle.supported_test_period,
            **bundle.test_metrics,
        },
        "website_usage": (
            "Loaded and validated at application startup; displayed historical benchmarks "
            "remain direct transaction-weighted observations."
        ),
        "synthetic": False,
        "active": True,
    }
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def load_individual_property_model(
    path: str | Path = INDIVIDUAL_PROPERTY_MODEL_PATH,
) -> RealPropertyBundle:
    """Load the distinct individual-property application bundle without fallback."""
    model_path = Path(path)
    if not model_path.is_file():
        raise ModelArtifactError(f"Individual-property model is unavailable: {model_path}")
    try:
        bundle = RealPropertyBundle.load(model_path)
    except (OSError, TypeError, ValueError) as exc:
        raise ModelArtifactError("Individual-property model bundle is invalid") from exc
    if bundle.price_type != "completed_transaction":
        raise ModelArtifactError("Individual-property model has an incompatible price type")
    return bundle
