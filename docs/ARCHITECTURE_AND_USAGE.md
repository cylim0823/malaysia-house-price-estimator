# Architecture and Local Usage

## Engineering status

The repository has one installable package at `src/house_price_estimator/` and
one Streamlit entrypoint at `app/streamlit_app.py`. Data is separated by
external/raw/processed stage, application models use role-based names, synthetic
artefacts are test-only, and generated reports are grouped by purpose.

## Runtime path

The Streamlit historical path is:

```text
app/streamlit_app.py
  -> artifacts.load_active_historical_model()
  -> models/historical_aggregate/metadata.json
  -> models/historical_aggregate/model_bundle.pkl
  -> AggregateBenchmarkService over the validated aggregate CSV
```

The bundle is explicitly selected and validated; the annual benchmark displayed
to users remains direct observed transaction value divided by transaction count.
The Individual Property Estimator has its own incompatible bundle and service.

Primary responsibilities:

1. `artifacts.py` centralises repository-relative production paths and validates active artefacts.
2. `aggregate_data.py` provides generic annual historical benchmarks.
3. `data_pipeline.py` validates aggregate data, evaluates baselines, and persists the aggregate bundle.
4. `data_sources.py` isolates source adapters and legal/coverage metadata.
5. `location_catalog.py` owns canonical Malaysian locations.
6. `real_transactions.py` trains and persists the distinct property-level bundle.
7. `prediction.py` provides UI-independent prediction contracts.

## Data, model, fixture, and report layout

```text
data/
  external/                         original licensed source files
  raw/                              immutable imported snapshots
  processed/                        validated datasets and catalog

models/
  historical_aggregate/             active bundle, manifest, evaluation summary
  individual_property/              separate property-level application bundle

tests/fixtures/synthetic/           deterministic test-only model bundle

reports/generated/
  evaluation/                       model evaluation reports
  data_quality/                     data-quality and EDA reports
```

Experimental comparison training writes transient bundles to ignored
`build/experimental_models/`; these are never selected by application runtime.

## Installation and commands

```powershell
python -m pip install -e ".[ml,ui,api,charts,dev]"
python -m house_price_estimator --help
python -m pytest -q
streamlit run app/streamlit_app.py
```

Rebuild the active aggregate artefact and its manifest:

```powershell
python scripts/process_napic_aggregate_transactions.py
python scripts/train_aggregate_model.py
```

Exercise the synthetic fixture workflow only in a temporary directory:

```powershell
python -m house_price_estimator generate-synthetic-data --output <temporary-directory>/records.json --count 240
python -m house_price_estimator train-synthetic-fixture --output-dir <temporary-directory>/model --count 240
python -m house_price_estimator evaluate --model <temporary-directory>/model/model_bundle.pkl
python -m house_price_estimator model-info --model <temporary-directory>/model/model_bundle.pkl
python -m house_price_estimator predict --model <temporary-directory>/model/model_bundle.pkl --input <input.json>
```

The optional API has no default model. `HOUSE_PRICE_MODEL` must explicitly name
a compatible non-synthetic `PredictionBundle`; synthetic fixtures are rejected
in production mode.

## Security

Bundles use pickle for trusted repository artefacts. Pickle can execute code, so
never load an uploaded or otherwise untrusted model file. Missing, incompatible,
synthetic, or checksum-mismatched active historical artefacts fail clearly rather
than falling back to a test fixture.
