"""Deterministic exact and near-duplicate grouping with retained evidence."""

from __future__ import annotations

from collections import defaultdict
from hashlib import sha256
from typing import Any, Iterable


def _text(value: Any) -> str:
    return " ".join(str(value or "").lower().split())


def similarity(left: dict[str, Any], right: dict[str, Any]) -> tuple[float, list[str]]:
    evidence: list[str] = []
    score = 0.0
    if left.get("source_record_id") and left.get("source_record_id") == right.get("source_record_id"):
        return 1.0, ["same_source_record_id"]
    for key, weight in (("state", .1), ("district", .15), ("project_name", .2), ("property_type", .1)):
        if _text(left.get(key)) and _text(left.get(key)) == _text(right.get(key)):
            score += weight; evidence.append(f"same_{key}")
    for key, tolerance, weight in (("price", .03, .15), ("built_up_sqft", .03, .15), ("land_area_sqft", .05, .05)):
        a, b = left.get(key), right.get(key)
        if a not in (None, 0) and b not in (None, 0) and abs(float(a)-float(b))/max(abs(float(a)), abs(float(b))) <= tolerance:
            score += weight; evidence.append(f"close_{key}")
    for key, weight in (("bedrooms", .05), ("bathrooms", .05)):
        if left.get(key) is not None and left.get(key) == right.get(key):
            score += weight; evidence.append(f"same_{key}")
    return min(score, 1.0), evidence


def group_duplicates(records: Iterable[dict[str, Any]], *, threshold: float = .75) -> list[dict[str, Any]]:
    output = [dict(record) for record in records]
    parent = list(range(len(output)))
    evidence_map: dict[int, list[str]] = defaultdict(list)
    method_map: dict[int, str] = {}
    confidence_map: dict[int, float] = {}
    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i
    def union(i: int, j: int) -> None:
        a, b = find(i), find(j)
        if a != b: parent[b] = a
    for i in range(len(output)):
        for j in range(i + 1, len(output)):
            score, evidence = similarity(output[i], output[j])
            exact = score == 1.0 or all(f"same_{k}" in evidence or f"close_{k}" in evidence for k in ("state", "district", "project_name", "property_type", "price", "built_up_sqft", "bedrooms", "bathrooms"))
            if exact or score >= threshold:
                union(i, j); evidence_map[i].extend(evidence); confidence_map[i] = max(score, confidence_map.get(i, 0)); method_map[i] = "exact" if exact else "near"
    groups: dict[int, list[int]] = defaultdict(list)
    for i in range(len(output)): groups[find(i)].append(i)
    for root, members in groups.items():
        group_id = "dup_" + sha256("|".join(str(output[i].get("record_id")) for i in members).encode()).hexdigest()[:12]
        canonical = str(output[members[0]].get("record_id"))
        for position, i in enumerate(members):
            duplicate = len(members) > 1
            output[i].update({"duplicate_status": ("exact_duplicate" if method_map.get(root)=="exact" else "possible_duplicate") if duplicate else "unique",
                              "duplicate_group_id": group_id if duplicate else f"unique_{output[i].get('record_id')}",
                              "duplicate_method": method_map.get(root) if duplicate else None,
                              "duplicate_confidence": confidence_map.get(root) if duplicate else None,
                              "canonical_record_id": canonical, "is_canonical_record": position == 0,
                              "duplicate_evidence": sorted(set(evidence_map.get(root, [])))})
    return output

