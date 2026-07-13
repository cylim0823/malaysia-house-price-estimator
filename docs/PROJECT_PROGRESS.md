# Project Progress

Last updated: 13 July 2026

| Area | Engineering status | Real-data status |
| --- | --- | --- |
| Planning and source investigation | Complete | Source approval pending |
| Canonical schema | Complete and versioned | First-source reconciliation pending |
| Structured-file ingestion | Complete for CSV, JSON, JSONL, and Parquet | No approved file imported |
| Cleaning and validation | Complete as a conservative framework | Source-specific and district validation pending |
| Duplicate and outlier review | Complete as deterministic initial methods | Threshold calibration pending |
| Synthetic demonstration generator | Complete | Not market evidence |
| Licensed JPPH historical averages | 2,090 rows normalized and versioned | Aggregated 2009 Q1-2018 Q2 only |
| EDA | Reusable summaries complete | Real conclusions pending |
| Features and splitting | Complete; training-only fitting and duplicate-group safety tested | Real time-field reliability pending |
| Baseline and advanced modelling | Complete locally; CatBoost optional | Real comparison and final selection pending |
| Evaluation and prediction ranges | Complete with protected slices and residual quantiles | Real errors/ranges pending |
| Saved bundle and prediction service | Complete | Supported production coverage pending |
| CLI | Complete | Real-data commands require an approved mapping |
| Streamlit | Public historical-average MVP deployed | Individual-property model pending |
| Optional FastAPI | Complete local adapter | Hosting pending |
| GitHub publication | Public repository pushed | Complete for current prototype |
| Streamlit deployment | Live official-average prototype | Individual-property version pending |
| Public monitoring | Initial live boot verified | Ongoing monitoring not configured |

## Verification record

- Editable package installation: passed.
- Complete suite: 31 tests, including official-workbook normalization, training, persistence, prediction, and Streamlit smoke coverage.
- Official model: log-target ridge regression trained on 1,980 observations and tested on the final 110 observations (2018 Q1-Q2).
- Official holdout results: MAE RM94,268.28; RMSE RM276,407.99; R² 0.7670. State/property-type median baseline MAE RM101,457.44.
- End-to-end path: synthetic generation → preparation → deduplication/outliers → split → baseline/advanced comparison → evaluation → save → load → prediction.
- Generated metrics and charts are labelled synthetic.
- Deployable model artifacts, official normalized data, and the metrics report are versioned; temporary evaluation outputs remain ignored.
- Local Git branch: `main`; official historical-average dataset/model/app phase committed as `ef53310`.

## Remaining limitations

- No approved property-level data or official district reference.
- No genuine Malaysian market accuracy, range calibration, or supported geographic coverage.
- Near-duplicate and outlier thresholds require source-specific review.
- Pickle bundles are trusted-local artifacts and must never be loaded from untrusted users.
- The live model is limited to historical state/property-type averages and must not be used as an individual-property valuation.
- No property-level real dataset was selected after the 13 July 2026 licence/provenance review; see `REAL_DATASET_ASSESSMENT.md`.
