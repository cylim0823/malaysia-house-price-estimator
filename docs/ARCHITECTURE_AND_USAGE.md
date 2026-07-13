# Architecture and Local Usage

## Engineering status

The repository has one installable Python package at
`src/house_price_estimator/`, one Streamlit entrypoint at
`app/streamlit_app.py`, and separate folders for external/raw/processed data,
demo/real models, and demo/real generated reports.

The real datasets are historical aggregates. They do not establish
individual-property accuracy, current coverage, or an official valuation.
Synthetic records remain limited to engineering tests and demonstrations.

## Package responsibilities

The package is organized into four groups:

1. **Data pipeline:** `schema.py`, `ingestion.py`, and `cleaning/` define typed
   records, structured-file import, parsing, normalization, and rejected-row
   retention. `duplicates.py`, `outliers.py`, and `eda.py` provide independent
   review and reporting stages.
2. **Modelling and prediction:** `features.py`, `splitting.py`, `modelling.py`,
   `evaluation.py`, `bundle.py`, `prediction.py`, and `workflow.py` implement
   training-only preprocessing, group-safe splits, model comparison, metrics,
   persistence, and safe prediction contracts.
3. **Licensed aggregate sources:** `official_averages.py`,
   `penang_district.py`, `regional_terraced.py`, `regional_area.py`, and
   `aggregate_transactions.py` preserve the distinct source schemas and model
   meanings. They remain separate because they are independently reproducible
   and existing pickle artefacts refer to their module paths.
4. **Interfaces:** `cli.py` is the command-line interface, `api.py` is the
   optional FastAPI adapter, and `ui_contracts.py` prevents property-level
   inputs from entering an aggregate model. Business logic remains outside the
   Streamlit file.

No duplicate implementation or compatibility wrapper is retained. Keeping the
small source-specific modules avoids a monolithic data pipeline and preserves
saved-model compatibility.

## Data, model, and report layout

```text
data/
├── external/napic/                 original JPPH/NAPIC workbooks
├── external/penang/                original Penang count/value CSVs
├── raw/aggregate_transactions/     immutable imported aggregate snapshot
└── processed/
    ├── aggregate_transactions/     validated and rejected aggregate rows
    └── historical_prices/          normalized historical datasets

models/
├── demo/                           synthetic engineering bundle
└── real/                           licensed aggregate bundles

reports/generated/
├── demo/                           synthetic evaluation output
└── real/                           real aggregate quality/model reports
```

Raw and external file contents are never modified by training scripts. Every
entrypoint resolves the repository root with `pathlib.Path`; it does not embed
a developer's absolute path.

## Installation and commands

```powershell
python -m pip install -e ".[ml,ui,api,charts,dev]"
python -m house_price_estimator --help
python -m unittest discover -s tests -v
streamlit run app/streamlit_app.py
```

Rebuild real aggregate datasets, models, and reports:

```powershell
python scripts/train_official_averages.py
python scripts/train_penang_district.py
python scripts/train_regional_terraced.py
python scripts/train_regional_area.py
python scripts/process_aggregate_transactions.py
```

Exercise the source-neutral synthetic workflow:

```powershell
python -m house_price_estimator generate-demo-data --output reports/generated/demo/records.json --count 240
python -m house_price_estimator clean --input reports/generated/demo/records.json --output reports/generated/demo/cleaned.json
python -m house_price_estimator eda --input reports/generated/demo/records.json --output reports/generated/demo/eda.json
python -m house_price_estimator train-demo --output-dir models/demo --count 240
python -m house_price_estimator evaluate --model models/demo/demo_bundle.pkl
python -m house_price_estimator model-info --model models/demo/demo_bundle.pkl
python -m house_price_estimator predict --model models/demo/demo_bundle.pkl --input <input.json>
```

Optional API:

```powershell
$env:HOUSE_PRICE_MODEL = "models/demo/demo_bundle.pkl"
python -m uvicorn house_price_estimator.api:app --reload
```

Endpoints are `GET /health`, `GET /model-info`, and `POST /predict`. GitHub
Pages cannot execute this Python API or model.

## Security and troubleshooting

Bundles use pickle for trusted repository artefacts. Pickle can execute code,
so never load an uploaded or otherwise untrusted model file. Use Python 3.11+
and install the relevant optional dependency group. Parquet requires `pyarrow`.
An unsupported coverage error means the requested combination was absent from
the applicable training dataset.
