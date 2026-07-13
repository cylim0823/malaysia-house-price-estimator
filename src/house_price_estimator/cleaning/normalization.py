"""Controlled vocabulary normalisation."""

from __future__ import annotations

import re
from ..location_catalog import MALAYSIAN_STATES, normalize_state
_PROPERTY_TYPES = {
    "condo": "Condominium", "condominium": "Condominium", "apartment": "Apartment",
    "flat": "Flat", "terrace": "Terraced House", "terraced house": "Terraced House",
    "semi d": "Semi-Detached House", "semi detached": "Semi-Detached House",
    "semi detached house": "Semi-Detached House", "bungalow": "Bungalow",
    "detached house": "Bungalow", "townhouse": "Townhouse",
}
_TENURES = {"freehold": "Freehold", "leasehold": "Leasehold"}
_FURNISHING = {
    "unfurnished": "Unfurnished", "partly furnished": "Partly Furnished",
    "partially furnished": "Partly Furnished", "fully furnished": "Fully Furnished",
}


def _key(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value).strip().lower()).strip()


def normalize_property_type(value: object) -> str:
    key = _key(value)
    if key not in _PROPERTY_TYPES:
        raise ValueError(f"unknown property type: {value!r}")
    return _PROPERTY_TYPES[key]


def normalize_tenure(value: object) -> str | None:
    if value is None or not str(value).strip():
        return None
    key = _key(value)
    if key not in _TENURES:
        raise ValueError(f"unknown tenure: {value!r}")
    return _TENURES[key]


def normalize_furnishing(value: object) -> str | None:
    if value is None or not str(value).strip():
        return None
    key = _key(value)
    if key not in _FURNISHING:
        raise ValueError(f"unknown furnishing: {value!r}")
    return _FURNISHING[key]
