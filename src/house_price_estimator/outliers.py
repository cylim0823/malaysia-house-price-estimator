"""Review-oriented outlier detection; records are never deleted."""

from __future__ import annotations

from collections import defaultdict
from statistics import median
from typing import Any, Iterable


def _percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    if not ordered: return float("nan")
    position = (len(ordered)-1)*fraction; low = int(position); high = min(low+1, len(ordered)-1)
    return ordered[low] + (ordered[high]-ordered[low])*(position-low)


def detect_outliers(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    output = [dict(record) for record in records]
    groups: dict[tuple[Any, Any], list[float]] = defaultdict(list)
    for record in output:
        price = record.get("price")
        if price and float(price) > 0: groups[(record.get("state"), record.get("property_type"))].append(float(price))
    for record in output:
        reasons: list[str] = []; methods: list[str] = []; scores: list[float] = []
        price = float(record.get("price") or 0); area = float(record.get("built_up_sqft") or 0)
        status = "not_outlier"; action = "retain"
        if price <= 0: status="confirmed_data_error"; reasons.append("non_positive_price"); action="exclude_from_model"
        if area < 100 and area > 0: reasons.append("suspiciously_small_area")
        if area > 100000: reasons.append("suspiciously_large_area")
        if area > 0 and price > 0:
            psf = price/area
            if psf < 10 or psf > 10000: reasons.append("suspicious_price_per_sqft")
        values = groups[(record.get("state"), record.get("property_type"))]
        if len(values) >= 4:
            q1, q3 = _percentile(values,.25), _percentile(values,.75); iqr=q3-q1
            if iqr and (price < q1-1.5*iqr or price > q3+1.5*iqr): reasons.append("group_iqr"); methods.append("iqr"); scores.append(abs(price-median(values))/iqr)
            med=median(values); deviations=[abs(v-med) for v in values]; mad=median(deviations)
            if mad:
                robust_z=.6745*(price-med)/mad
                if abs(robust_z)>3.5: reasons.append("group_robust_z"); methods.append("mad"); scores.append(abs(robust_z))
        if reasons and status == "not_outlier": status="possible_outlier"; action="manual_review"
        record.update({"outlier_status":status,"outlier_methods":methods or ["rules"],"outlier_score":max(scores,default=None),
                       "outlier_reasons":reasons,"outlier_review_required":bool(reasons),"outlier_suggested_action":action})
    return output

