"""UI contracts that keep aggregate and property-level inputs separate."""

from __future__ import annotations

from collections.abc import Mapping
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
    "built_up_sqft",
    "land_area_sqft",
    "bedrooms",
    "bathrooms",
    "car_parks",
    "storeys",
    "floor_level",
    "tenure",
    "furnishing",
    "completion_year",
    "property_age_years",
    "asking_price",
)

HIGH_RISE_PROPERTY_TYPES = frozenset({"Apartment", "Condominium", "Flat"})
LANDED_PROPERTY_TYPES = frozenset(
    {"Bungalow", "Semi-Detached House", "Terraced House", "Townhouse"}
)


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
    """Describe property-type-specific fields for the future disabled form."""
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
    raise ValueError(f"Unsupported future property type: {property_type}")
