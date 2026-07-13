"""Strict parsers for common Malaysian property values."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

SQM_TO_SQFT = Decimal("10.7639104167")
ACRE_TO_SQFT = Decimal("43560")
HECTARE_TO_SQFT = Decimal("107639.104167")


def parse_ringgit(value: object) -> Decimal | None:
    """Parse a non-negative ringgit value without inventing missing values."""
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    text = str(value).strip().lower().replace("rm", "").replace(",", "").replace(" ", "")
    text = text.replace("million", "m")
    multiplier = Decimal("1")
    if text.endswith("k"):
        multiplier, text = Decimal("1000"), text[:-1]
    elif text.endswith("m"):
        multiplier, text = Decimal("1000000"), text[:-1]
    if not re.fullmatch(r"\d+(?:\.\d+)?", text):
        raise ValueError(f"invalid ringgit value: {value!r}")
    try:
        result = Decimal(text) * multiplier
    except InvalidOperation as exc:
        raise ValueError(f"invalid ringgit value: {value!r}") from exc
    if result < 0:
        raise ValueError("price cannot be negative")
    return result.quantize(Decimal("0.01"))


def parse_area_sqft(value: object, unit: str | None = None) -> Decimal | None:
    """Parse an area and convert square metres to square feet."""
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    text = str(value).strip().lower().replace(",", "")
    detected = unit.lower().strip() if unit else None
    unit_patterns = {
        "sqm": r"(?:sq\.?\s*m|m2|m²|sqm)$",
        "sqft": r"(?:sq\.?\s*ft|ft2|ft²|sqft)$",
        "acre": r"(?:acres?|ac)$",
        "hectare": r"(?:hectares?|ha)$",
    }
    for canonical, pattern in unit_patterns.items():
        if re.search(pattern, text):
            detected = canonical
            text = re.sub(pattern, "", text).strip()
            break
    aliases = {"square metres": "sqm", "square meters": "sqm", "m2": "sqm", "m²": "sqm",
               "square feet": "sqft", "ft2": "sqft", "ft²": "sqft"}
    detected = aliases.get(detected or "", detected)
    if detected not in {"sqm", "sqft", "acre", "hectare"}:
        raise ValueError("area unit must be explicitly sqft, sqm, acre, or hectare")
    if not re.fullmatch(r"\d+(?:\.\d+)?", text):
        raise ValueError(f"invalid area value: {value!r}")
    area = Decimal(text)
    if area <= 0:
        raise ValueError("area must be greater than zero")
    if detected == "sqm":
        area *= SQM_TO_SQFT
    elif detected == "acre":
        area *= ACRE_TO_SQFT
    elif detected == "hectare":
        area *= HECTARE_TO_SQFT
    return area.quantize(Decimal("0.01"))


def parse_room_count(value: object, *, include_auxiliary: bool = False) -> int | None:
    """Parse room counts such as ``4+1``; auxiliary rooms are excluded by default."""
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    text = str(value).strip().lower()
    if text in {"n/a", "na", "unknown", ""}:
        return None
    if text == "studio":
        return 0
    match = re.fullmatch(r"(\d+)(?:\s*\+\s*(\d+))?", text)
    if not match:
        raise ValueError(f"invalid room count: {value!r}")
    primary = int(match.group(1))
    auxiliary = int(match.group(2) or 0)
    return primary + auxiliary if include_auxiliary else primary


def parse_rooms(value: object) -> tuple[int | None, int | None]:
    """Return primary and auxiliary room counts separately."""
    if value is None or str(value).strip().lower() in {"", "n/a", "na", "unknown"}:
        return None, None
    if str(value).strip().lower() == "studio":
        return 0, 0
    match = re.fullmatch(r"(\d+)(?:\s*\+\s*(\d+))?", str(value).strip())
    if not match:
        raise ValueError(f"invalid room count: {value!r}")
    return int(match.group(1)), int(match.group(2) or 0)
