"""Traceable cleaning pipeline that never mutates raw input records."""

from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
from typing import Iterable, Mapping

from house_price_estimator import SCHEMA_VERSION
from .normalization import normalize_furnishing, normalize_property_type, normalize_state, normalize_tenure
from .parsers import parse_area_sqft, parse_ringgit, parse_room_count

ALLOWED_PRICE_TYPES = {"asking", "completed_transaction", "auction", "rental"}


@dataclass(frozen=True)
class CleanResult:
    raw_records: tuple[dict[str, object], ...]
    accepted_records: tuple[dict[str, object], ...]
    rejected_records: tuple[dict[str, object], ...]
    quality_report: dict[str, object]


def _duplicate_key(record: Mapping[str, object]) -> str:
    fields = ("state", "district", "project_name", "property_type", "built_up_sqft", "bedrooms", "bathrooms")
    normalized = "|".join(str(record.get(field) or "").strip().lower() for field in fields)
    return sha256(normalized.encode("utf-8")).hexdigest()[:16]


def _clean_one(raw: Mapping[str, object], dataset_version: str) -> dict[str, object]:
    required = ("record_id", "source_name", "price", "price_type", "state", "property_type")
    missing = [field for field in required if raw.get(field) is None or str(raw.get(field)).strip() == ""]
    if missing:
        raise ValueError("missing required fields: " + ", ".join(missing))
    price_type = str(raw["price_type"]).strip().lower()
    if price_type not in ALLOWED_PRICE_TYPES:
        raise ValueError(f"unknown price_type: {price_type!r}")
    cleaned: dict[str, object] = {
        "record_id": str(raw["record_id"]), "source_name": str(raw["source_name"]),
        "price": parse_ringgit(raw["price"]), "price_type": price_type,
        "state": normalize_state(raw["state"]),
        "district": str(raw.get("district") or "").strip() or None,
        "city": str(raw.get("city") or "").strip() or None,
        "township": str(raw.get("township") or "").strip() or None,
        "project_name": str(raw.get("project_name") or "").strip() or None,
        "property_type": normalize_property_type(raw["property_type"]),
        "tenure": normalize_tenure(raw.get("tenure")),
        "furnishing": normalize_furnishing(raw.get("furnishing")),
        "built_up_sqft": parse_area_sqft(raw.get("built_up_area"), raw.get("built_up_unit")) if raw.get("built_up_area") is not None else None,
        "land_area_sqft": parse_area_sqft(raw.get("land_area"), raw.get("land_area_unit")) if raw.get("land_area") is not None else None,
        "bedrooms": parse_room_count(raw.get("bedrooms")),
        "bathrooms": parse_room_count(raw.get("bathrooms")),
        "schema_version": SCHEMA_VERSION, "dataset_version": dataset_version,
        "validation_status": "valid", "validation_notes": [], "is_model_eligible": price_type in {"asking", "completed_transaction"},
    }
    price = cleaned["price"]
    if not isinstance(price, Decimal) or price <= 0:
        raise ValueError("price must be greater than zero")
    if cleaned["built_up_sqft"] and cleaned["built_up_sqft"] > Decimal("100000"):
        cleaned["validation_status"] = "review"
        cleaned["validation_notes"] = ["extreme_built_up_area_review"]
        cleaned["is_model_eligible"] = False
    return cleaned


def clean_records(records: Iterable[Mapping[str, object]], *, dataset_version: str) -> CleanResult:
    """Clean records, retain failures, group duplicates, and report coverage."""
    if not dataset_version.strip():
        raise ValueError("dataset_version is required")
    raw_records = tuple(deepcopy(dict(record)) for record in records)
    accepted: list[dict[str, object]] = []
    rejected: list[dict[str, object]] = []
    for raw in raw_records:
        try:
            accepted.append(_clean_one(raw, dataset_version))
        except (ValueError, TypeError) as exc:
            rejected.append({"raw_record": deepcopy(raw), "validation_status": "rejected", "rejection_reasons": [str(exc)]})

    groups: dict[str, list[dict[str, object]]] = defaultdict(list)
    for record in accepted:
        groups[_duplicate_key(record)].append(record)
    duplicate_count = 0
    for group_id, group in groups.items():
        is_duplicate = len(group) > 1
        for index, record in enumerate(group):
            record.update({
                "is_duplicate": is_duplicate, "duplicate_group_id": group_id if is_duplicate else None,
                "duplicate_match_method": "exact_normalized_fields" if is_duplicate else None,
                "duplicate_match_confidence": Decimal("1.00") if is_duplicate else None,
                "is_canonical_record": index == 0,
            })
            if is_duplicate and index > 0:
                record["is_model_eligible"] = False
                duplicate_count += 1

    state_counts = Counter(str(record["state"]) for record in accepted)
    district_counts = Counter(f"{record['state']}|{record.get('district') or 'Unknown'}" for record in accepted)
    quality_report: dict[str, object] = {
        "dataset_version": dataset_version, "input_count": len(raw_records),
        "accepted_count": len(accepted), "rejected_count": len(rejected),
        "duplicate_copy_count": duplicate_count, "review_count": sum(r["validation_status"] == "review" for r in accepted),
        "coverage_by_state": dict(sorted(state_counts.items())),
        "coverage_by_state_and_district": dict(sorted(district_counts.items())),
    }
    return CleanResult(raw_records, tuple(accepted), tuple(rejected), quality_report)

