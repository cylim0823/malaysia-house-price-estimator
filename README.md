# Malaysia House Price Estimator

This repository contains two deliberately separate products:

1. **Historical Market Explorer** reports real official aggregate averages for a selected location, property category, and historical quarter. The integrated aggregate sources cover Penang completed-transaction groups in 2017 and JPPH published regional averages through 2018 Q2. They are historical benchmarks, not individual valuations.
2. **Individual Property Estimator** uses a separate model trained on 416,627 real NAPIC/JPPH open completed residential transactions across all 13 states and Kuala Lumpur, Putrajaya, and Labuan. Its source period is January 2021 through March 2026 (2026 Q1). Support is selected by state, district, and the property categories actually published for that district.

Neither output is an official valuation, guaranteed sale price, or financial advice.

## Real individual-property model

The model target is completed transaction price in Malaysian ringgit. The saved preprocessing/model uses:

- state, district, and published property type;
- built-up/main-floor area when supplied;
- land/parcel area when supplied;
- tenure when supplied;
- unit/floor level when applicable and supplied; and
- the source transaction year and month.

The form also visibly accepts city/township, project, subtype, bedrooms, helper bedrooms, bathrooms, car parks, storeys, furnishing, completion year, age, renovation, condition, and an optional asking price. NAPIC does not publish those physical/condition fields, so the application lists them under **Information provided but not used** or **Missing optional information** instead of silently pretending they affected the estimate. Unknown values remain null; not-applicable values remain distinct. Training-only medians handle missing numeric model fields.

The selected histogram-gradient-boosting log-price model was chosen against a hierarchical median baseline using pre-2025 training and 2025 Q1-Q3 validation. The untouched 2025 Q4-2026 Q1 test set contains 15,030 records and produced MAE RM127,910.56, median absolute error RM57,477.87, MAPE 22.31%, and R2 0.7414. Error varies substantially by location, type, and price band; Kuala Lumpur and high-value properties have materially larger absolute errors. See `reports/generated/real/napic_property_evaluation.json`.

## Data source and storage

The individual dataset comes from NAPIC/JPPH's **Data Transaksi Terbuka** Tableau export. NAPIC introduced it as part of the Government Public Sector Open Data initiative. Reuse is recorded under Malaysian Government Open Data Terms of Use 1.0 with the attribution: “Data and information are subject to the Malaysian Government Open Data Terms of Use 1.0.” The feed contains no owner/person identifiers.

Raw snapshots are intentionally excluded from Git because the 16 CSVs total tens of megabytes and must retain immutable provenance. The repository includes the bounded, resumable downloader, exact schema validation, training code, saved model, quality/evaluation reports, and source documentation. Recreate the local raw dataset with:

```powershell
python scripts/download_napic_open_transactions.py `
  --output-dir data/raw/napic_open_transactions_YYYYMMDD
```

The July 2026 validated snapshot contains 416,627 rows, 129 published districts, 11 property categories, and all 16 jurisdictions. Main-floor area is absent on 107,740 rows; one land-area value is absent. All required price, state, district, property-type, and month fields were present. Statistical outliers are flagged and retained. Exact duplicate grouping runs before the time split; the current full published-attribute signature found no exact duplicate rows.

The separately published NAPIC aggregate XLSX workbooks were also investigated through Q1 2026P. They are technically suitable, but their files state copyright reserved and do not publish compatible model-training/redistribution terms. They were not integrated. Therefore the historical aggregate explorer still ends at 2018 Q2, while the separately licensed open individual feed ends at 2026 Q1.

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
  --model models/real/napic_property_bundle.pkl `
  --report reports/generated/real/napic_property_evaluation.json `
  --quality-report reports/generated/real/napic_property_quality.json
```

## Repository layout

```text
app/                              Streamlit entrypoint
data/external/                    Original licensed historical aggregate files
data/raw/                         Ignored immutable runtime snapshots
data/processed/                   Validated aggregate releases/catalogue
docs/                             Sources, architecture, progress, and blockers
models/demo/                      Clearly synthetic legacy demonstration bundle
models/real/                      Separate aggregate and real property bundles
reports/generated/real/           Committed quality and evaluation reports
scripts/                          Reproducible collection and training commands
src/house_price_estimator/        Core application and pipeline logic
tests/                            Unit, integration, regression, and UI tests
```

## Current limitations

- Published open transactions do not contain bedrooms, bathrooms, car parks, furnishing, completion year, condition, renovation, or a stable transaction identifier.
- District/type support and record volume vary. Low-support segments receive an explicit warning.
- The model does not use city, township, road, scheme/project, or coordinates, so it cannot capture every within-district difference.
- Prediction ranges are empirical validation-residual intervals, not guarantees.
- 2026 Q1 is recent but provisional; the source can also return transient empty Tableau exports, so collection is bounded, retried, and schema checked.
- Historical aggregate data remains older and legally separate from the open individual transaction feed.

See `docs/REAL_DATASET_ASSESSMENT.md`, `docs/RECENT_OFFICIAL_DATA_INVESTIGATION.md`, `docs/INDIVIDUAL_PROPERTY_DATA_REQUIREMENTS.md`, and `ROADMAP.md` for evidence and remaining work.
