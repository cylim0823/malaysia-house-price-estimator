# Architecture and Local Usage

## Engineering status

The repository contains a source-neutral property-level engineering framework plus a separate licensed historical-average pipeline. The deployed Streamlit app uses JPPH/NAPIC aggregate data; synthetic records remain limited to framework tests and demonstrations.

The official model estimates quarterly state/property-type averages for 2009 Q1 through 2018 Q2. It does not establish individual-property accuracy, current coverage, or an official valuation.

## Pipeline

1. `schema.py` defines versioned canonical enums and records.
2. `ingestion.py` reads CSV, JSON, JSON Lines, and optional Parquet files without collecting web data.
3. `cleaning/` parses and normalises conservative values while retaining failures.
4. `duplicates.py` adds exact/near duplicate groups and evidence without deleting records.
5. `outliers.py` adds review-oriented rule, IQR, and robust-z findings.
6. `eda.py` produces reusable quality and distribution summaries.
7. `features.py` fits numeric and categorical preprocessing on training data only.
8. `splitting.py` keeps duplicate groups together while preferring time order.
9. `modelling.py` provides median, grouped-median, linear ridge, Random Forest, Histogram Gradient Boosting, log-target, and optional KNN candidates. CatBoost activates only when installed.
10. `evaluation.py` creates protected metrics, tables, and charts.
11. `bundle.py` saves model and compatibility/coverage metadata.
12. `prediction.py` validates coverage and produces a central estimate, residual-quantile demonstration range, support level, and neutral asking-price comparison.
13. `app/streamlit_app.py`, `api.py`, and `cli.py` adapt the service for users.

The official aggregate path is intentionally separate: `official_averages.py` normalizes four JPPH workbooks, `scripts/train_official_averages.py` creates the normalized CSV, performs a time-based final holdout, compares baselines, and writes `models/official_average_bundle.pkl`, which the Streamlit app loads.

`penang_district.py` joins licensed transaction counts and values at identical quarter/property-type/district keys, calculates completed-transaction averages, holds out Q4 2017, compares a grouped median with log ridge, and saves the better model. The Streamlit app uses this richer path whenever Penang is selected.

`regional_area.py` combines the licensed JPPH terraced and high-rise district/region workbooks into 600 genuine observations, trains through 2017, preserves 2018 Q1-Q2 as the final test, and compares a location/property median with log ridge. Terraced data covers all 13 states plus Kuala Lumpur; high-rise options appear only for the seven state markets in the source. Putrajaya and Labuan remain unsupported.

## Installation and commands

```powershell
python -m pip install -e ".[ml,ui,api,charts,dev]"
python -m house_price_estimator --help
python -m house_price_estimator generate-demo-data --output reports/generated/demo.json --count 240
python -m house_price_estimator clean --input reports/generated/demo.json --output reports/generated/cleaned.json
python -m house_price_estimator eda --input reports/generated/demo.json --output reports/generated/eda.json
python -m house_price_estimator train-demo --output-dir models --count 240
python -m house_price_estimator evaluate --model models/demo_bundle.pkl
python -m house_price_estimator model-info --model models/demo_bundle.pkl
python -m house_price_estimator predict --model models/demo_bundle.pkl --input example_prediction.json
python scripts/train_official_averages.py
python scripts/train_penang_district.py
python scripts/train_regional_area.py
python -m streamlit run app/streamlit_app.py
```

Optional API:

```powershell
$env:HOUSE_PRICE_MODEL = "models/demo_bundle.pkl"
python -m uvicorn house_price_estimator.api:app --reload
```

Endpoints are `GET /health`, `GET /model-info`, and `POST /predict`. GitHub Pages cannot execute this Python API or model.

## Security and troubleshooting

Bundles use pickle for trusted local artifacts. Pickle can execute code while loading, so `PredictionBundle.load` requires explicit `trusted=True`. Never load user-uploaded or otherwise untrusted model files.

Use Python 3.11+, install the relevant optional dependency group, and generate `models/demo_bundle.pkl` before Streamlit or API startup. Parquet requires `pyarrow`. An unsupported coverage error means the exact state/district/property-type combination was absent from training.
