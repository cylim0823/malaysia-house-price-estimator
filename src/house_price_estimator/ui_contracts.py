"""UI-independent contracts for aggregate and optional property inputs."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


AGGREGATE_PREDICTION_FIELDS = frozenset(
    {"state", "district", "property_type", "year", "quarter"}
)

INDIVIDUAL_PROPERTY_FIELDS = (
    "state",
    "district",
    "city",
    "township",
    "project_name",
    "property_type",
    "property_subtype",
    "built_up_sqft",
    "land_area_sqft",
    "bedrooms",
    "additional_bedrooms",
    "bathrooms",
    "car_parks",
    "storeys",
    "floor_level",
    "tenure",
    "furnishing",
    "completion_year",
    "property_age_years",
    "renovation_status",
    "property_condition",
    "asking_price",
)

FIELD_LABELS = {
    "state": "State or federal territory",
    "district": "District",
    "city": "City or township",
    "township": "Township",
    "project_name": "Development or project name",
    "property_type": "Property type",
    "property_subtype": "Property subtype",
    "built_up_sqft": "Built-up area",
    "land_area_sqft": "Land area",
    "bedrooms": "Bedrooms",
    "additional_bedrooms": "Additional/helper bedrooms",
    "bathrooms": "Bathrooms",
    "car_parks": "Car parks",
    "storeys": "Storeys",
    "floor_level": "Floor level",
    "tenure": "Tenure",
    "furnishing": "Furnishing",
    "completion_year": "Completion year",
    "property_age_years": "Property age",
    "renovation_status": "Renovation status",
    "property_condition": "Property condition",
    "asking_price": "Asking price",
}

HIGH_RISE_PROPERTY_TYPES = frozenset(
    {"Apartment", "Condominium", "Condominium/Apartment", "Flat", "Low-Cost Flat", "Studio"}
)
LANDED_PROPERTY_TYPES = frozenset(
    {
        "Bungalow", "Semi-Detached House", "Terraced House", "Townhouse",
        "Detached", "Cluster House", "Low-Cost House", "Town House",
        "1 - 1 1/2 Storey Semi-Detached", "2 - 2 1/2 Storey Semi-Detached",
        "1 - 1 1/2 Storey Terraced", "2 - 2 1/2 Storey Terraced",
    }
)

VALUE_PROVIDED = "provided"
VALUE_UNKNOWN = "unknown"
VALUE_NOT_APPLICABLE = "not_applicable"
UNKNOWN_TOKENS = {"", "unknown", "not sure"}


@dataclass(frozen=True)
class PropertyFormSubmission:
    """Normalized values plus explicit missing-value semantics."""

    values: dict[str, Any]
    statuses: dict[str, str]


@dataclass(frozen=True)
class InformationDisclosure:
    """Human-readable audit of how a submission was handled."""

    used: tuple[str, ...]
    provided_but_not_used: tuple[str, ...]
    missing_optional: tuple[str, ...]
    not_applicable: tuple[str, ...]


def aggregate_prediction_payload(values: Mapping[str, Any]) -> dict[str, Any]:
    """Return an exact aggregate-model payload, rejecting missing or extra fields."""
    supplied = set(values)
    missing = AGGREGATE_PREDICTION_FIELDS - supplied
    unsupported = supplied - AGGREGATE_PREDICTION_FIELDS
    if missing:
        raise ValueError(f"Missing aggregate fields: {', '.join(sorted(missing))}")
    if unsupported:
        raise ValueError(
            f"Unsupported aggregate fields: {', '.join(sorted(unsupported))}"
        )
    return {name: values[name] for name in sorted(AGGREGATE_PREDICTION_FIELDS)}


def individual_field_visibility(property_type: str) -> dict[str, bool]:
    """Describe property-type-specific fields without encoding absence as zero."""
    if property_type in HIGH_RISE_PROPERTY_TYPES:
        return {
            "built_up_sqft": True,
            "land_area_sqft": False,
            "storeys": False,
            "floor_level": True,
            "car_parks": True,
        }
    if property_type in LANDED_PROPERTY_TYPES:
        return {
            "built_up_sqft": True,
            "land_area_sqft": True,
            "storeys": True,
            "floor_level": False,
            "car_parks": True,
        }
    raise ValueError(f"Unsupported property type: {property_type}")


def _normalize_optional(value: Any) -> tuple[Any, str]:
    if value is None:
        return None, VALUE_UNKNOWN
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.lower() in UNKNOWN_TOKENS:
            return None, VALUE_UNKNOWN
        if stripped.lower() == "not applicable":
            return None, VALUE_NOT_APPLICABLE
        return stripped, VALUE_PROVIDED
    return value, VALUE_PROVIDED


def normalize_individual_submission(
    raw: Mapping[str, Any],
) -> PropertyFormSubmission:
    """Validate an optional property form while retaining missing-value meaning."""
    state, state_status = _normalize_optional(raw.get("state"))
    property_type, property_type_status = _normalize_optional(raw.get("property_type"))
    if state_status != VALUE_PROVIDED:
        raise ValueError("State or federal territory is required")
    if property_type_status != VALUE_PROVIDED:
        raise ValueError("Property type is required")
    visibility = individual_field_visibility(str(property_type))

    values: dict[str, Any] = {}
    statuses: dict[str, str] = {}
    for field in INDIVIDUAL_PROPERTY_FIELDS:
        if field in visibility and not visibility[field]:
            values[field] = None
            statuses[field] = VALUE_NOT_APPLICABLE
            continue
        values[field], statuses[field] = _normalize_optional(raw.get(field))

    positive_fields = {
        "built_up_sqft",
        "land_area_sqft",
        "bathrooms",
        "storeys",
        "completion_year",
        "asking_price",
    }
    nonnegative_fields = {
        "bedrooms",
        "additional_bedrooms",
        "car_parks",
        "floor_level",
        "property_age_years",
    }
    for field in positive_fields:
        if statuses[field] == VALUE_PROVIDED and float(values[field]) <= 0:
            raise ValueError(f"{FIELD_LABELS[field]} must be greater than zero")
    for field in nonnegative_fields:
        if statuses[field] == VALUE_PROVIDED and float(values[field]) < 0:
            raise ValueError(f"{FIELD_LABELS[field]} cannot be negative")
    if (
        statuses["bedrooms"] == VALUE_PROVIDED
        and int(values["bedrooms"]) == 0
        and property_type != "Studio"
    ):
        raise ValueError("Zero bedrooms is valid only for a studio")
    return PropertyFormSubmission(values, statuses)


def build_information_disclosure(
    submission: PropertyFormSubmission,
    *,
    model_features: set[str] | frozenset[str],
    additionally_used: tuple[str, ...] = (),
) -> InformationDisclosure:
    """Disclose used, ignored, unknown, and not-applicable form fields."""
    used_fields = set(additionally_used)
    used_fields.update(
        field
        for field, status in submission.statuses.items()
        if status == VALUE_PROVIDED and field in model_features
    )
    unused_fields = {
        field
        for field, status in submission.statuses.items()
        if status == VALUE_PROVIDED and field not in used_fields
    }
    missing = {
        field
        for field, status in submission.statuses.items()
        if status == VALUE_UNKNOWN and field not in {"state", "property_type"}
    }
    not_applicable = {
        field
        for field, status in submission.statuses.items()
        if status == VALUE_NOT_APPLICABLE
    }
    labels = lambda fields: tuple(FIELD_LABELS[field] for field in sorted(fields))
    return InformationDisclosure(
        labels(used_fields), labels(unused_fields), labels(missing), labels(not_applicable)
    )
