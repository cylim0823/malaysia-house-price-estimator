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
| Penang district transactions | 212 district/property-type/quarter averages | Aggregated 2017 completed transactions only |
| Regional area prices | 600 quarterly averages across 53 state-area combinations and 14 states/territories | Terraced and partial high-rise coverage, 2016 Q1-2018 Q2 |
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
- Complete suite: 41 tests passed. The regional-area module includes 3 focused tests for nationwide normalization, strict property-type coverage, identical-holdout model selection, persistence, and unsupported-type rejection.
- Official model: log-target ridge regression trained on 1,980 observations and tested on the final 110 observations (2018 Q1-Q2).
- Official holdout results: MAE RM94,268.28; RMSE RM276,407.99; R² 0.7670. State/property-type median baseline MAE RM101,457.44.
- Penang district holdout: Q4 2017, 54 observations. The selected district/property-type median achieved MAE RM55,154.82, beating log ridge at RM79,520.97.
- Regional terraced holdout: 2018 Q1-Q2, 92 observations. Selected log ridge MAE RM15,126.49 versus area-median baseline MAE RM22,236.17.
- Combined regional holdout: 2018 Q1-Q2, 120 observations. The selected location/property median achieved MAE RM19,397.46, RMSE RM29,576.51, and RÂ² 0.9782; log ridge MAE was RM20,507.33.
- End-to-end path: synthetic generation → preparation → deduplication/outliers → split → baseline/advanced comparison → evaluation → save → load → prediction.
- Generated metrics and charts are labelled synthetic.
- Deployable model artifacts, official normalized data, and the metrics report are versioned; temporary evaluation outputs remain ignored.
- Local Git branch: `main`; official historical-average phase `ef53310`, Penang district phase `749be64`, and unpublished regional area phase `a4a242e`.

## Remaining limitations

- No approved individual-property data or nationwide official district-code reference. Penang has validated source district labels only.
- No genuine Malaysian market accuracy, range calibration, or supported geographic coverage.
- Near-duplicate and outlier thresholds require source-specific review.
- Pickle bundles are trusted-local artifacts and must never be loaded from untrusted users.
- The local app provides Penang district benchmarks and regional terraced/partial high-rise benchmarks across 14 state/territory markets; neither is an individual-property valuation. Putrajaya and Labuan remain unsupported.
- No property-level real dataset was selected after the 13 July 2026 licence/provenance review; see `REAL_DATASET_ASSESSMENT.md`.

## Regional multi-property expansion - 13 July 2026

- Phase name: regional area-data expansion and model retraining.
- Start state: 460 terraced observations covered 46 areas; high-rise data had not been imported and most app locations exposed one property type.
- Completion state: 600 licensed quarterly observations cover 53 state-area combinations. Terraced houses span all 13 states plus Kuala Lumpur; 140 high-rise rows were added for the seven state markets published by JPPH.
- Files created: `data/external/napic_open_data/highrise_by_district.xlsx`, `data/official/regional_area_prices.csv`, `src/house_price_estimator/regional_area.py`, `scripts/train_regional_area.py`, `models/regional_area_bundle.pkl`, `reports/regional_area_model_metrics.json`, and `tests/test_regional_area.py`.
- Files modified: `README.md`, `ROADMAP.md`, `app/streamlit_app.py`, the NAPIC source README, architecture/source/blocker documentation, and this progress log.
- Tests performed: focused `unittest` module, full `unittest` discovery, Python byte-code compilation, deterministic retraining, source checksum, and `git diff --check`.
- Test results: 41/41 tests passed. The 2018 Q1-Q2 holdout contains 120 rows; selected location/property median MAE is RM19,397.46, RMSE RM29,576.51, and RÂ² 0.9782. Log ridge MAE is RM20,507.33.
- Commit identifier: pending local commit.
- Remaining limitations: published averages are historical aggregates without individual-home attributes. High-rise coverage is partial; Putrajaya and Labuan have no verified price observations. The model is not a current or individual-property valuation.
- Dependencies: Creative Commons Attribution JPPH terraced and high-rise workbooks from Malaysia's archived government open-data catalogue.
- Blockers: nationwide property-level training still requires a licensed record-level dataset; no listing scraper is approved.
