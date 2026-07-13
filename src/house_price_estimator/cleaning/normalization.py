"""Controlled vocabulary normalisation."""

from __future__ import annotations

import re

MALAYSIAN_STATES = (
    "Johor", "Kedah", "Kelantan", "Melaka", "Negeri Sembilan", "Pahang",
    "Penang", "Perak", "Perlis", "Sabah", "Sarawak", "Selangor",
    "Terengganu", "Kuala Lumpur", "Putrajaya", "Labuan",
)

_STATE_ALIASES = {
    "kl": "Kuala Lumpur", "malacca": "Melaka", "pulau pinang": "Penang", "n sembilan": "Negeri Sembilan",
    "w p kuala lumpur": "Kuala Lumpur",
    "wp kuala lumpur": "Kuala Lumpur", "wilayah persekutuan kuala lumpur": "Kuala Lumpur",
    "w p putrajaya": "Putrajaya", "wp putrajaya": "Putrajaya",
    "w p labuan": "Labuan", "wp labuan": "Labuan",
}
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


def normalize_state(value: object) -> str:
    key = _key(value)
    canonical = {state.lower(): state for state in MALAYSIAN_STATES}
    canonical.update(_STATE_ALIASES)
    if key not in canonical:
        raise ValueError(f"unknown Malaysian state or federal territory: {value!r}")
    return canonical[key]


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
