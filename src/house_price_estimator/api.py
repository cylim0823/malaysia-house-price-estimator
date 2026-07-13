"""Optional FastAPI adapter around the prediction service."""
from __future__ import annotations
import os
from pathlib import Path
try:
    from fastapi import FastAPI,HTTPException
except ImportError as exc:
    raise RuntimeError("Install optional API dependencies with: pip install -e .[api]") from exc
from .bundle import PredictionBundle
from .prediction import PredictionService
app=FastAPI(title="Malaysia House Price Estimator",version="0.1.0")
PROJECT_ROOT=Path(__file__).resolve().parents[2]
DEFAULT_MODEL_PATH=PROJECT_ROOT/"models"/"demo"/"demo_bundle.pkl"
def _service():
    configured=os.environ.get("HOUSE_PRICE_MODEL")
    path=Path(configured) if configured else DEFAULT_MODEL_PATH
    if not path.is_absolute():path=PROJECT_ROOT/path
    if not path.is_file():raise HTTPException(503,"model bundle is not available")
    return PredictionService(PredictionBundle.load(path,trusted=True))
@app.get("/health")
def health():return {"status":"ok"}
@app.get("/model-info")
def model_info():
    bundle=_service().bundle;return {"model_version":bundle.model_version,"schema_version":bundle.schema_version,"dataset_version":bundle.dataset_version,"is_synthetic":bundle.is_synthetic}
@app.post("/predict")
def predict(payload:dict):
    try:return _service().predict(payload).to_dict()
    except ValueError as exc:raise HTTPException(422,str(exc)) from exc
