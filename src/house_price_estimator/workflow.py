"""Small end-to-end synthetic workflow used by the CLI and integration tests."""
from __future__ import annotations
from collections import Counter
from pathlib import Path
from typing import Any, Iterable
import numpy as np
from .bundle import PredictionBundle
from .duplicates import group_duplicates
from .evaluation import evaluate_records,regression_metrics,write_evaluation
from .modelling import all_candidates
from .outliers import detect_outliers
from .splitting import split_records
from .synthetic_data import generate_synthetic_records

def prepare(records):
    rows=[]
    for raw in records:
        try:
            price=float(raw["price"]);built=float(str(raw["built_up_area"]).split()[0]);land=float(raw["land_area"]) if raw.get("land_area") else None
        except (ValueError,TypeError):continue
        row=dict(raw,price=price,built_up_sqft=built,land_area_sqft=land,record_year=int(raw["record_date"][:4]),record_month=int(raw["record_date"][5:7]),additional_bedrooms=0,is_model_eligible=True)
        rows.append(row)
    return detect_outliers(group_duplicates(rows))

def train_demo(*, count: int = 240, seed: int = 42,
               output_dir: str | Path | None = None,
               records: Iterable[dict[str, Any]] | None = None):
    """Train the demonstration bundle from supplied synthetic rows or the generator."""
    source_rows = list(records) if records is not None else generate_synthetic_records(
        count, seed=seed, include_anomalies=True
    )
    if not source_rows or not all(bool(row.get("is_synthetic")) for row in source_rows):
        raise ValueError("train-demo accepts only clearly labelled synthetic records")
    rows=[r for r in prepare(source_rows) if r["outlier_status"]!="confirmed_data_error"]
    split=split_records(rows,seed=seed,use_time=True); candidates=all_candidates(seed); scores={}
    for name,model in candidates.items():model.fit(list(split.train));scores[name]=regression_metrics([r["price"] for r in split.validation],model.predict(list(split.validation)))["mae"]
    best=min(scores.values()); complexity=("overall_median","state_median","segment_median","linear_ridge","hist_gradient_boosting","random_forest","hist_gradient_boosting_log","knn_experiment","catboost")
    selected_name=next(name for name in complexity if name in scores and scores[name] <= best*1.05)
    model=candidates[selected_name];validation_predictions=model.predict(list(split.validation));residual=np.asarray([r["price"] for r in split.validation])-validation_predictions
    report=evaluate_records(list(split.validation),validation_predictions,minimum_segment_size=3)
    segment_counts=Counter(f"{r['state']}|{r['district']}|{r['property_type']}" for r in split.train)
    bundle=PredictionBundle(model,"synthetic-demo-model-v1","synthetic-demo-v1","asking",tuple(sorted({r["state"] for r in split.train})),tuple(sorted({r["district"] for r in split.train})),tuple(sorted({r["property_type"] for r in split.train})),report,(float(np.quantile(residual,.1)),float(np.quantile(residual,.9))),dict(segment_counts),is_synthetic=True)
    paths={}
    if output_dir:
        out=Path(output_dir);out.mkdir(parents=True,exist_ok=True);bundle.save(out/"demo_bundle.pkl");paths=write_evaluation(report,out/"evaluation")
    return bundle,{"selected_model":selected_name,"validation_mae":scores[selected_name],"candidate_mae":scores,"split":split.report,"reports":paths},split
