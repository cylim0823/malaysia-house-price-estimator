# Application model artefacts

## Active historical aggregate model

The authoritative manifest is `historical_aggregate/metadata.json`; it explicitly
selects `historical_aggregate/model_bundle.pkl`. Application code loads it through
`load_active_historical_model()`, validates its checksum, schema, model version,
dataset version, feature list, coverage, and non-synthetic status, and never scans
the directory for the first pickle file.

The bundle predicts an average completed transaction price for a
district/property-type/quarter aggregate group. Its target and evaluation are
aggregate, not individual-property valuation accuracy. The Streamlit historical
result remains the direct transaction-weighted observed annual benchmark; the
active bundle is loaded to make the historical model selection and compatibility
explicit.

- Data: licensed NAPIC/JPPH completed transactions plus preserved licensed 2017 groups
- Dataset version: `napic-open-transactions-20260713-aggregate-v1`
- Coverage: 16 jurisdictions, 129 published district labels, 11 categories, 2017 and 2021–2026 Q1
- Model: transaction-weighted district/property-type mean baseline
- Price type: completed-transaction aggregate average
- Evaluation: `historical_aggregate/evaluation_summary.json`
- Regeneration: `python scripts/process_napic_aggregate_transactions.py`, then `python scripts/train_aggregate_model.py`

## Separate individual-property application model

`individual_property/model_bundle.pkl` is genuinely distinct. It powers only the
Individual Property Estimator and targets a completed transaction price using the
published property-level NAPIC fields. It is not the historical aggregate model
and is therefore kept in its own role-named directory.

## Synthetic test fixture

The deterministic synthetic bundle is stored at
`tests/fixtures/synthetic/model_bundle.pkl`. Production loaders do not know this
path and reject synthetic historical metadata. Regenerate a temporary fixture with:

```powershell
python -m house_price_estimator train-synthetic-fixture --output-dir <temporary-directory> --count 240 --seed 42
```

## Experimental comparison models

The official-average, regional-area, and regional-terraced candidates remain
reproducible through their focused training scripts and tests. Their committed
pickle bundles were removed because no application loader used them. When those
scripts run, transient bundles go to ignored `build/experimental_models/` and
reports go to `reports/generated/evaluation/`.

## Migration decisions

| Old path | Purpose | Referenced by | Decision | New path |
|---|---|---|---|---|
| `models/real/aggregate_transaction_bundle.pkl` | Aggregate weighted baseline | Dataset catalog, trainer; now application startup | Moved; active | `models/historical_aggregate/model_bundle.pkl` |
| `models/real/napic_property_bundle.pkl` | Property-level completed-transaction estimator | Streamlit individual tab and tests | Moved; retained | `models/individual_property/model_bundle.pkl` |
| `models/demo/demo_bundle.pkl` | Deterministic synthetic engineering fixture | Synthetic service tests | Moved out of production models | `tests/fixtures/synthetic/model_bundle.pkl` |
| `models/real/official_average_bundle.pkl` | 2009–2018 state/type comparison | Training script only | Removed; reproducible experiment | Transient `build/experimental_models/official_average_bundle.pkl` |
| `models/real/regional_area_bundle.pkl` | 2016–2018 regional area comparison | Training script only | Removed; reproducible experiment | Transient `build/experimental_models/regional_area_bundle.pkl` |
| `models/real/regional_terraced_bundle.pkl` | 2016–2018 terraced comparison | Training script only | Removed; reproducible experiment | Transient `build/experimental_models/regional_terraced_bundle.pkl` |

Pickle files must be loaded only from trusted repository artefacts.
