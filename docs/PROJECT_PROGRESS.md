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
| EDA | Reusable summaries complete | Real conclusions pending |
| Features and splitting | Complete; training-only fitting and duplicate-group safety tested | Real time-field reliability pending |
| Baseline and advanced modelling | Complete locally; CatBoost optional | Real comparison and final selection pending |
| Evaluation and prediction ranges | Complete with protected slices and residual quantiles | Real errors/ranges pending |
| Saved bundle and prediction service | Complete | Supported production coverage pending |
| CLI | Complete | Real-data commands require an approved mapping |
| Streamlit | Complete local synthetic MVP | Real model replacement pending |
| Optional FastAPI | Complete local adapter | Hosting pending |
| GitHub publication | Locally prepared and committed | Push blocked because GitHub CLI has no authenticated host |
| Streamlit deployment | Repository artifacts and instructions complete | One-time GitHub/Streamlit browser authorization and repository push required |
| Public monitoring | Not performed | Requires a deployed real-data application |

## Verification record

- Editable package installation: passed.
- Complete suite: 29 tests after framework expansion (final count recorded in completion report).
- End-to-end path: synthetic generation → preparation → deduplication/outliers → split → baseline/advanced comparison → evaluation → save → load → prediction.
- Generated metrics and charts are labelled synthetic.
- Model artifacts and generated reports are ignored and used only for local verification.
- Local Git branch: `main`; initial commit `a5f36e1` plus final deployment/CI metadata commit.

## Remaining limitations

- No approved property-level data or official district reference.
- No genuine Malaysian market accuracy, range calibration, or supported geographic coverage.
- Near-duplicate and outlier thresholds require source-specific review.
- Pickle bundles are trusted-local artifacts and must never be loaded from untrusted users.
- Public deployment, production monitoring, and retraining remain pending.
- No real dataset was selected after the 13 July 2026 licence/provenance review; see `REAL_DATASET_ASSESSMENT.md`.
