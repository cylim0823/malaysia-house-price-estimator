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

Seven primary modules define the reusable runtime:

1. `data_pipeline.py` validates the generic aggregate schema, preserves rejected
   rows, reports quality, derives the temporal holdout, trains weighted
   baselines, and saves the aggregate bundle.
2. `data_sources.py` loads dataset metadata and isolates source-column adapters.
3. `location_catalog.py` owns the 16 canonical Malaysian locations and builds
   exact selector coverage from validated observation combinations.
4. `modelling.py` contains reusable individual-record candidate models.
5. `evaluation.py` contains reusable regression metrics and report writers.
6. `prediction.py` provides source-neutral historical and future property
   prediction contracts outside Streamlit.
7. `synthetic_data.py` generates clearly labelled test/demo records only.

Focused schema, ingestion, cleaning, duplicate/outlier review, persistence,
CLI/API, and UI-contract modules remain separate because they express distinct
contracts. `aggregate_transactions.py` and `synthetic.py` are tiny compatibility
imports for existing bundles and callers. Older licensed benchmark modules are
kept loadable because repository pickle artifacts record their module paths;
new source onboarding does not copy those modules.

The Streamlit file contains presentation only. It iterates over
`data/processed/dataset_catalog.json`, loads a `HistoricalExplorer`, and renders
the same form for every dataset. There is no state-specific page or state
conditional in the active application.

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

Rebuild the active real aggregate datasets, models, and reports:

```powershell
python scripts/train_regional_area.py
python scripts/process_aggregate_transactions.py
```

The other training scripts reproduce legacy comparison artifacts and are not
templates for adding a state. New sources use an adapter, catalog metadata, and
the generic aggregate pipeline.

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
