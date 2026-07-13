# Malaysia House Price Estimator

This repository contains two deliberately separate products:

1. **Historical Market Explorer** reports transaction-weighted annual or year-to-date completed-transaction averages for a selected state, optional district, property category, and year. Its aggregate preserves licensed 2017 history and covers all 16 Malaysian jurisdictions from 2021 through 2026 Q1. It is a historical benchmark, not an individual valuation.
2. **Individual Property Estimator** uses a separate model trained on 416,627 real NAPIC/JPPH open completed residential transactions across all 13 states and Kuala Lumpur, Putrajaya, and Labuan. Its source period is January 2021 through March 2026 (2026 Q1). Support is selected by state, district, and the property categories actually published for that district.

Neither output is an official valuation, guaranteed sale price, or financial advice.

## Where to start

- Streamlit entrypoint: `app/streamlit_app.py`
- Generic aggregate processing and annual benchmark service: `src/house_price_estimator/aggregate_data.py`
- NAPIC publication workbook adapter: `src/house_price_estimator/source_adapters/napic_excel.py`
- Generic aggregate model training: `scripts/train_aggregate_model.py`
- Evaluation and weighted metrics: `src/house_price_estimator/data_pipeline.py`
- Individual-property prediction service: `src/house_price_estimator/prediction.py`
- Tests: `tests/test_aggregate_data.py`, `tests/test_ui_contracts.py`, and `tests/test_framework.py`

## How official aggregate coverage works

The committed aggregate release is derived from the licensed NAPIC/JPPH Data Transaksi Terbuka state snapshots. Validated rows determine every state, year, district, and property-type option; the selector order is state, year, coverage/district, then property type. District input is hidden for state-level-only coverage. Users choose a year, not a publication quarter. The generated machine-readable coverage registry is `data/processed/aggregate_transactions/coverage_catalog.json`.

Property source text, stable public codes, and readable labels are defined once in
`data_pipeline.py`. The interface displays labels such as “1–1½-storey terrace
house” while the immutable raw snapshots retain the publisher's original text.

Annual averages are calculated as `sum(transaction_value_rm) / sum(transaction_count)`. A complete year has Q1-Q4; a historical year with missing periods is labelled partial; 2026 is labelled year to date through Q1. Missing periods and any state/property-type fallback are disclosed.

## Adding a state or year

1. Download the official source and retain its original values.
2. Add source URL, title, retrieval date, checksum, coverage, and licence metadata.
3. Run the generic importer or `scripts/process_napic_aggregate_transactions.py`.
4. Validate count/value arithmetic and retain rejected rows with reasons.
5. Generate the processed generic records.
6. Run the full test suite.
7. Refresh the generic aggregate bundle with `scripts/train_aggregate_model.py`.
8. Verify that Streamlit coverage and year status are data-driven.

Do not copy or create a state-specific cleaner, model, prediction service, or UI page.

## Real individual-property model

The model target is completed transaction price in Malaysian ringgit. The saved preprocessing/model uses:

- state, district, and published property type;
- built-up/main-floor area when supplied;
- land/parcel area when supplied;
- tenure when supplied;
- unit/floor level when applicable and supplied; and
- the source transaction year and month.

The form also visibly accepts city/township, project, subtype, bedrooms, helper bedrooms, bathrooms, car parks, storeys, furnishing, completion year, age, renovation, condition, and an optional asking price. NAPIC does not publish those physical/condition fields, so the application lists them under **Information provided but not used** or **Missing optional information** instead of silently pretending they affected the estimate. Unknown values remain null; not-applicable values remain distinct. Training-only medians handle missing numeric model fields.

The selected histogram-gradient-boosting log-price model was chosen against a hierarchical median baseline using pre-2025 training and 2025 Q1-Q3 validation. The untouched 2025 Q4-2026 Q1 test set contains 15,030 records and produced MAE RM127,910.56, median absolute error RM57,477.87, MAPE 22.31%, and R2 0.7414. Error varies substantially by location, type, and price band; Kuala Lumpur and high-value properties have materially larger absolute errors. See `reports/generated/evaluation/individual_property.json`.

## Model used by the application

The historical application explicitly loads the **Malaysia historical aggregate
weighted baseline** from `models/historical_aggregate/model_bundle.pkl`, selected
and validated by `models/historical_aggregate/metadata.json`. It uses official,
non-synthetic completed-transaction aggregates. It predicts district/property-type
quarter-group averages; displayed annual history is calculated directly from the
validated transaction totals and is not an individual-property valuation. Current
coverage is the preserved Penang 2017 release plus all 16 jurisdictions from 2021
through 2026 Q1, with uneven segment support.

The separate Individual Property Estimator loads
`models/individual_property/model_bundle.pkl`; it is not a fallback for the
historical mode. Synthetic models are test fixtures only.

## Data source and storage

The individual dataset comes from NAPIC/JPPH's **Data Transaksi Terbuka** Tableau export. NAPIC introduced it as part of the Government Public Sector Open Data initiative. Reuse is recorded under Malaysian Government Open Data Terms of Use 1.0 with the attribution: “Data and information are subject to the Malaysian Government Open Data Terms of Use 1.0.” The feed contains no owner/person identifiers.

Raw snapshots are intentionally excluded from Git because the 16 CSVs total tens of megabytes and must retain immutable provenance. The repository includes the bounded, resumable downloader, exact schema validation, training code, saved model, quality/evaluation reports, and source documentation. Recreate the local raw dataset with:

```powershell
python scripts/download_napic_open_transactions.py `
  --output-dir data/raw/napic_open_transactions_YYYYMMDD
```

The July 2026 validated snapshot contains 416,627 rows, 129 published districts, 11 property categories, and all 16 jurisdictions. Main-floor area is absent on 107,740 rows; one land-area value is absent. All required price, state, district, property-type, and month fields were present. Statistical outliers are flagged and retained. Exact duplicate grouping runs before the time split; the current full published-attribute signature found no exact duplicate rows.

The separately published NAPIC aggregate XLSX workbooks were investigated and all 16 Q1 2026 state files were downloaded locally for importer validation. They state copyright reserved and do not publish compatible model-training/redistribution terms, so the originals are Git-excluded and are not the committed benchmark source. Their URLs and checksums are recorded in `data/external/napic/publication_manifest.json`.

## Run locally

Use Python 3.11 or newer:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[ml,ui,api,charts,dev]"
streamlit run app/streamlit_app.py
```

Run validation:

```powershell
python -m unittest discover -s tests -v
python -m compileall -q src app scripts tests
```

Retrain after recreating a raw snapshot:

```powershell
python scripts/train_napic_open_transactions.py `
  --raw-dir data/raw/napic_open_transactions_YYYYMMDD `
  --model models/individual_property/model_bundle.pkl `
  --report reports/generated/evaluation/individual_property.json `
  --quality-report reports/generated/data_quality/individual_property.json
```

Regenerate the multi-state aggregate data and model:

```powershell
python scripts/process_napic_aggregate_transactions.py
python scripts/train_aggregate_model.py
```

## Repository layout

```text
app/                              Streamlit entrypoint
data/external/                    Original licensed historical aggregate files
data/raw/                         Ignored immutable runtime snapshots
data/processed/                   Validated aggregate releases/catalogue
docs/                             Sources, architecture, progress, and blockers
models/historical_aggregate/      Explicit active aggregate bundle and manifest
models/individual_property/       Separate property-level application bundle
reports/generated/evaluation/     Role-labelled evaluation output
reports/generated/data_quality/   Role-labelled quality and EDA output
scripts/                          Reproducible collection and training commands
src/house_price_estimator/        Core application and pipeline logic
tests/fixtures/synthetic/         Deterministic test-only model fixture
tests/                            Unit, integration, regression, and UI tests
```

## Current limitations

- Published open transactions do not contain bedrooms, bathrooms, car parks, furnishing, completion year, condition, renovation, or a stable transaction identifier.
- District/type support and record volume vary. Low-support segments receive an explicit warning.
- The model does not use city, township, road, scheme/project, or coordinates, so it cannot capture every within-district difference.
- Prediction ranges are empirical validation-residual intervals, not guarantees.
- 2026 Q1 is recent but provisional; the source can also return transient empty Tableau exports, so collection is bounded, retried, and schema checked.
- The 2026 aggregate is year to date through Q1, not a complete annual figure.
- Some rare district/property-type/year combinations are partial because no transaction was published in one or more periods.

See `docs/REAL_DATASET_ASSESSMENT.md`, `docs/RECENT_OFFICIAL_DATA_INVESTIGATION.md`, `docs/INDIVIDUAL_PROPERTY_DATA_REQUIREMENTS.md`, and `ROADMAP.md` for evidence and remaining work.
