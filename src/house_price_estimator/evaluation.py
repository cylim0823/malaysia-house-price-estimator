"""Metrics, protected slices, and synthetic-labelled reports."""
from __future__ import annotations
import csv,json,math
from pathlib import Path
from statistics import median
from typing import Any,Iterable
import numpy as np
from .synthetic import SYNTHETIC_LABEL

def regression_metrics(actual:Iterable[float],predicted:Iterable[float])->dict[str,float|None]:
    y=np.asarray(list(actual),float); p=np.asarray(list(predicted),float)
    if len(y)==0 or len(y)!=len(p): raise ValueError("actual and predicted must have equal non-zero length")
    errors=y-p; denom=np.where(y!=0,np.abs(y),np.nan); ss=float(np.sum((y-y.mean())**2))
    return {"mae":float(np.mean(np.abs(errors))),"median_absolute_error":float(np.median(np.abs(errors))),"rmse":float(np.sqrt(np.mean(errors**2))),
            "mape":float(np.nanmean(np.abs(errors)/denom)*100) if np.any(y!=0) else None,"r2":1-float(np.sum(errors**2))/ss if ss else None}

def evaluate_records(records:list[dict[str,Any]],predictions:Iterable[float],*,minimum_segment_size=10)->dict[str,Any]:
    preds=list(map(float,predictions)); overall=regression_metrics([float(r["price"]) for r in records],preds); slices={}
    for field in ("state","district","property_type","price_type","coverage_level"):
        groups={}
        for r,p in zip(records,preds):groups.setdefault(str(r.get(field) or "Unknown"),[]).append((float(r["price"]),p))
        slices[field]={key:{"count":len(values),"metrics":regression_metrics([v[0] for v in values],[v[1] for v in values])} for key,values in groups.items() if len(values)>=minimum_segment_size}
    return {"label":SYNTHETIC_LABEL if records and all(r.get("is_synthetic") for r in records) else "Model evaluation metrics","overall":overall,"slices":slices,"minimum_segment_size":minimum_segment_size,
            "prediction_points":[{"actual":float(r["price"]),"predicted":p,"residual":float(r["price"])-p} for r,p in zip(records,preds)]}

def write_evaluation(report:dict[str,Any],directory:str|Path)->dict[str,str]:
    out=Path(directory);out.mkdir(parents=True,exist_ok=True); json_path=out/"metrics.json";csv_path=out/"metrics.csv";md_path=out/"evaluation.md"
    json_path.write_text(json.dumps(report,indent=2),encoding="utf-8")
    with csv_path.open("w",newline="",encoding="utf-8") as h:
        writer=csv.writer(h);writer.writerow(["scope","segment","count","mae","median_absolute_error","rmse","mape","r2"]); writer.writerow(["overall","all","",*[report["overall"].get(k) for k in ("mae","median_absolute_error","rmse","mape","r2")]])
        for scope,groups in report["slices"].items():
            for segment,value in groups.items():writer.writerow([scope,segment,value["count"],*[value["metrics"].get(k) for k in ("mae","median_absolute_error","rmse","mape","r2")]])
    md_path.write_text(f"# Evaluation\n\n**{report['label']}**\n\nOverall MAE: RM {report['overall']['mae']:,.2f}\n\nThese results do not establish real Malaysian market accuracy.\n",encoding="utf-8")
    paths={"json":str(json_path),"csv":str(csv_path),"markdown":str(md_path)}
    try:
        import os, tempfile
        os.environ.setdefault("MPLCONFIGDIR",str(Path(tempfile.gettempdir())/"house_price_estimator_matplotlib"))
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        points=report.get("prediction_points",[]);actual=[p["actual"] for p in points];predicted=[p["predicted"] for p in points];residual=[p["residual"] for p in points]
        charts=(("actual_vs_predicted.png",actual,predicted,"Actual price","Predicted price"),("residuals.png",predicted,residual,"Predicted price","Residual"))
        for filename,x,y,xlabel,ylabel in charts:
            fig,ax=plt.subplots(figsize=(6,4));ax.scatter(x,y,alpha=.7);ax.set(xlabel=xlabel,ylabel=ylabel,title=report["label"]);fig.tight_layout();fig.savefig(out/filename,dpi=120);plt.close(fig);paths[filename]=str(out/filename)
        fig,ax=plt.subplots(figsize=(6,4));ax.hist(residual,bins=min(20,max(5,len(residual)//2)));ax.set(xlabel="Residual",ylabel="Count",title=report["label"]);fig.tight_layout();fig.savefig(out/"error_distribution.png",dpi=120);plt.close(fig);paths["error_distribution.png"]=str(out/"error_distribution.png")
    except ImportError: pass
    return paths
