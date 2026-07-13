"""Reusable tabular quality and exploratory summaries."""

from __future__ import annotations
from collections import Counter
from statistics import median
from typing import Any, Iterable
from .synthetic import SYNTHETIC_LABEL

def dataset_summary(records: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rows=list(records); prices=[float(r["price"]) for r in rows if isinstance(r.get("price"),(int,float)) and float(r["price"])>0]
    psf=[float(r["price"])/float(r["built_up_sqft"]) for r in rows if isinstance(r.get("price"),(int,float)) and r.get("built_up_sqft")]
    dates=sorted(str(r["record_date"]) for r in rows if r.get("record_date"))
    missing={key:sum(r.get(key) in (None,"") for r in rows) for key in sorted({k for r in rows for k in r})}
    synthetic=bool(rows) and all(bool(r.get("is_synthetic")) for r in rows)
    return {"label":SYNTHETIC_LABEL if synthetic else "Dataset quality report", "record_count":len(rows),"missing_values":missing,
            "validation_status_counts":dict(Counter(str(r.get("validation_status","unknown")) for r in rows)),
            "duplicate_status_counts":dict(Counter(str(r.get("duplicate_status","unknown")) for r in rows)),
            "outlier_status_counts":dict(Counter(str(r.get("outlier_status","unknown")) for r in rows)),
            "records_by_state":dict(Counter(str(r.get("state","Unknown")) for r in rows)),
            "records_by_district":dict(Counter(str(r.get("district","Unknown")) for r in rows)),
            "records_by_property_type":dict(Counter(str(r.get("property_type","Unknown")) for r in rows)),
            "price":{"count":len(prices),"min":min(prices,default=None),"median":median(prices) if prices else None,"max":max(prices,default=None)},
            "price_per_sqft":{"count":len(psf),"median":median(psf) if psf else None},
            "date_coverage":{"start":dates[0] if dates else None,"end":dates[-1] if dates else None},
            "eligible_count":sum(bool(r.get("is_model_eligible",True)) for r in rows)}

