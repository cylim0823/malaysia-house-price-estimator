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
| Aggregate transaction pipeline | Generic metadata-backed validation; 212 rows validated; 11,816 transactions represented | Current completed-transaction coverage is Penang 2017 only; forecasting remains provisional |
| Regional area prices | 600 quarterly averages across 53 state-area combinations and 14 states/territories | Terraced and partial high-rise coverage, 2016 Q1-2018 Q2 |
| EDA | Reusable summaries complete | Real conclusions pending |
| Features and splitting | Complete; training-only fitting and duplicate-group safety tested | Real time-field reliability pending |
| Baseline and advanced modelling | Complete locally; CatBoost optional | Real comparison and final selection pending |
| Evaluation and prediction ranges | Complete with protected slices and residual quantiles | Real errors/ranges pending |
| Saved bundle and prediction service | Complete | Supported production coverage pending |
| CLI | Complete | Real-data commands require an approved mapping |
| Streamlit | One metadata-driven historical form and disabled property-level preview complete locally | Individual-property model pending |
| Optional FastAPI | Complete local adapter | Hosting pending |
| GitHub publication | Public repository pushed | Complete for current prototype |
| Streamlit deployment | Live official-average prototype | Individual-property version pending |
| Public monitoring | Initial live boot verified | Ongoing monitoring not configured |
| Repository organization | Seven primary reusable modules plus focused contracts and compatibility shims | No data/model meaning changed |

## Verification record

- Editable package installation: passed.
- Complete suite: 63 tests passed. Aggregate coverage includes arithmetic, schema, source metadata, all 16 canonical locations, generic new-state onboarding, dynamic combinations, malformed inputs, duplicates, volume support, leakage exclusion, weighting, time ordering, persistence, unsupported input, UI field isolation, artifact integrity, and Streamlit paths.
- Official model: log-target ridge regression trained on 1,980 observations and tested on the final 110 observations (2018 Q1-Q2).
- Official holdout results: MAE RM94,268.28; RMSE RM276,407.99; R² 0.7670. State/property-type median baseline MAE RM101,457.44.
- Penang district holdout: Q4 2017, 54 observations. The selected district/property-type median achieved MAE RM55,154.82, beating log ridge at RM79,520.97.
- Regional terraced holdout: 2018 Q1-Q2, 92 observations. Selected log ridge MAE RM15,126.49 versus area-median baseline MAE RM22,236.17.
- Combined regional holdout: 2018 Q1-Q2, 120 observations. The selected location/property median achieved MAE RM19,397.46, RMSE RM29,576.51, and RÂ² 0.9782; log ridge MAE was RM20,507.33.
- End-to-end path: synthetic generation → preparation → deduplication/outliers → split → baseline/advanced comparison → evaluation → save → load → prediction.
- Generated metrics and charts are labelled synthetic.
- Deployable model artifacts, official normalized data, and the metrics report are versioned; temporary evaluation outputs remain ignored.
- Local Git branch: `agent/aggregate-transaction-explorer`; the verified aggregate-data commits are `2ff810a` and `3c8e6ee`.

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
- Current locations of the principal files created by that phase are `data/external/napic/highrise_by_district.xlsx`, `data/processed/historical_prices/regional_area_prices.csv`, `src/house_price_estimator/regional_area.py`, `scripts/train_regional_area.py`, `models/real/regional_area_bundle.pkl`, `reports/generated/real/regional_area_model_metrics.json`, and `tests/test_regional_area.py`.
- Files modified: `README.md`, `ROADMAP.md`, `app/streamlit_app.py`, the NAPIC source README, architecture/source/blocker documentation, and this progress log.
- Tests performed: focused `unittest` module, full `unittest` discovery, Python byte-code compilation, deterministic retraining, source checksum, and `git diff --check`.
- Test results: 41/41 tests passed. The 2018 Q1-Q2 holdout contains 120 rows; selected location/property median MAE is RM19,397.46, RMSE RM29,576.51, and RÂ² 0.9782. Log ridge MAE is RM20,507.33.
- Commit identifier: `aa7a8bb` (`feat: expand regional property training data`).
- Remaining limitations: published averages are historical aggregates without individual-home attributes. High-rise coverage is partial; Putrajaya and Labuan have no verified price observations. The model is not a current or individual-property valuation.
- Dependencies: Creative Commons Attribution JPPH terraced and high-rise workbooks from Malaysia's archived government open-data catalogue.
- Blockers: nationwide property-level training still requires a licensed record-level dataset; no listing scraper is approved.

## Aggregate completed-transaction integration - 13 July 2026

- Phase name: real aggregate transaction validation, weighting, evaluation, and UI integration.
- Start state: a 212-row derived Penang CSV and a simple unweighted district median model existed, but there was no separate aggregate schema, raw import metadata, arithmetic audit, volume support, weighted metrics, or dedicated UI mode.
- Completion state: the immutable CSV is preserved with checksum metadata; all rows are validated and normalized; quality, EDA, and weighted baseline reports are generated; and Streamlit has a separate aggregate explorer restricted to actual Penang 2017 combinations.
- Files created: aggregate source module, processing script, raw/processed aggregate releases, metadata, quality/EDA/model reports, aggregate bundle, test fixture/tests, and three aggregate documentation files.
- Files modified: application, README, roadmap, agent instructions, architecture, cleaning/schema, blockers, dataset assessment, deployment guide, and progress log.
- Tests performed: focused aggregate unit tests, end-to-end save/load/predict test, Streamlit aggregate/regional smoke tests, full test discovery, compile checks, deterministic rebuild, checksum comparison, and diff validation.
- Data results: 212 aggregate rows, 11,816 completed transactions, RM5,171,921,352 total represented value, zero arithmetic mismatches, zero duplicate keys, zero rejected rows, 84 warning rows, and eight missing combinations.
- Model results: Q1-Q3 training has 158 rows/8,646 transactions; Q4 test has 54 rows/3,170 transactions. Selected segment weighted average has unweighted MAE RM64,764.81 and transaction-weighted MAE RM36,676.57.
- Commit identifier: `2ff810a` (`feat: integrate aggregate transaction explorer`).
- Remaining limitations: one year, one state, aggregate categories, no individual-property attributes, no current-market validation, and no advanced model justification.
- Dependencies: two Penang government CSV releases labelled Creative Commons Attribution in the archived government catalogue.
- Blockers: additional licensed years/states are required for multi-year forecasting and nationwide aggregate support; property-level data remains separately blocked.

## Aggregate/property UI separation - 13 July 2026

- Phase name: Streamlit aggregate and individual-property mode separation.
- Start state: two aggregate sources appeared as peer explorer modes, so users could still mistake an aggregate benchmark for a specific-house estimate.
- Completion state: one clearly labelled historical market explorer contains both aggregate sources; a separate individual-property mode displays a disabled, property-type-aware form and cannot predict.
- Files created: `src/house_price_estimator/ui_contracts.py`, `tests/test_ui_contracts.py`, and `docs/INDIVIDUAL_PROPERTY_DATA_REQUIREMENTS.md`.
- Files modified: `app/streamlit_app.py`, `tests/test_framework.py`, `README.md`, `ROADMAP.md`, `docs/ARCHITECTURE_AND_USAGE.md`, and this progress log.
- Tests performed: focused UI contract and Streamlit integration tests, complete unit-test discovery, bundle checksum comparison, compile validation, local Streamlit HTTP startup, and diff validation.
- Test results: 57/57 tests passed; both trained bundle checksums were unchanged; Streamlit returned HTTP 200 locally; compile and diff checks passed.
- Commit identifier: `4be51aa` (`feat: separate aggregate and property estimator modes`).
- Remaining limitations: the app has no individual-property data or model, and the real aggregate sources remain historical (Penang 2017 and regional 2016–2018).
- Dependencies: existing repository-owned aggregate model bundles and licensed aggregate datasets; no new runtime dependency.
- Blockers: a legally usable, sufficiently representative property-level dataset is required before the second mode can predict.

## Repository structure cleanup - 13 July 2026

- Phase name: behavior-preserving structural maintenance.
- Start state: publisher folders had long `_open_data` suffixes; normalized datasets were in an ambiguous `data/official` layer; synthetic and real models shared one folder; generated reports were split between `reports/` and `models/evaluation/`; and an ignored nested Git clone duplicated repository metadata.
- Completion state: one package and one Streamlit entrypoint remain; data is grouped by external/raw/processed stage; models and reports are separated into demo/real categories; all paths are repository-relative and platform-neutral.
- Files moved: `data/external/napic_open_data` to `data/external/napic`; `data/external/penang_open_data` to `data/external/penang`; `data/official` to `data/processed/historical_prices`; six bundles to `models/demo` or `models/real`; seven JSON reports to `reports/generated/real`; local synthetic evaluation outputs to `reports/generated/demo/evaluation`.
- Files merged or renamed internally: none; algorithms and Python module paths were deliberately retained for clarity and pickle compatibility.
- Files deleted: the untracked `malaysia-house-price-estimator/` nested clone, after confirming its only working-tree file duplicated the root `.gitattributes` and its initial commit already existed in the outer object database. The Codex runtime may recreate an empty untracked `.agents/` directory, so it is ignored rather than treated as project structure.
- Files modified: path-bearing app/API/scripts/tests, `.gitignore`, CI compilation scope, README, roadmap, model guide, aggregate/EDA/evaluation/architecture documentation, and this progress log.
- Tests performed: pre/post full suites, compilation, package import, CLI help, five real-data rebuild scripts, fixed aggregate prediction, model loading, artifact checksums, Streamlit AppTest and HTTP startup, obsolete/absolute path scans, and Git diff validation.
- Test results: 57/57 tests passed before refactoring; 58/58 pass after adding the artifact-layout regression. All source, processed-data, and model checksums match their pre-move values. The fixed historical prediction and published metrics are unchanged.
- Commit identifier: `43607d8` (`refactor: simplify repository structure`).
- Remaining limitations: the package retains focused helper and source-specific modules rather than collapsing them into a monolith; this preserves independent testing and existing pickle import paths. The local Codex runtime may show an ignored empty `.agents/` directory. Individual-property data/model blockers are unchanged.
- Dependencies and blockers: no dependency changed and no new blocker was introduced.

## Nationwide-ready aggregate architecture - 13 July 2026

- Phase name: behavior-preserving state generalization and runtime consolidation.
- Start state: the active UI had separate Penang/regional render functions,
  Penang source facts in core validation, fixed historical selectors, and a
  hardcoded Q4 aggregate prediction rule.
- Completion state: seven primary reusable modules define pipeline, sources,
  locations, modelling, evaluation, prediction, and synthetic data. One
  metadata-driven Streamlit form handles both datasets. Exact selector options
  come from validated observation keys, and a synthetic Johor fixture proves a
  new state can use the generic CSV adapter and pipeline.
- Files created: `data/processed/dataset_catalog.json`,
  `src/house_price_estimator/data_pipeline.py`, `data_sources.py`,
  `location_catalog.py`, `synthetic_data.py`, `tests/test_location_catalog.py`,
  and `docs/STATE_GENERALIZATION.md`.
- Files modified: application, aggregate processing script, compatibility
  modules/imports, regional period validation, normalized aggregate outputs,
  aggregate model/report, tests, README, roadmap, agent instructions,
  architecture/validation/deployment/model documentation, and this log.
- Tests performed: focused catalog/pipeline/artifact tests, complete unit-test
  discovery, deterministic real rebuild twice, fixed prediction comparison,
  model metric comparison, byte-code compilation, diff validation, and local
  Streamlit HTTP startup.
- Test results: 63/63 tests pass; Streamlit returns HTTP 200; the real rebuild
  remains at 212 valid rows, 11,816 transactions, zero rejects/duplicates/
  arithmetic mismatches, MAE RM64,764.81, and weighted MAE RM36,676.57. The
  fixed RM730,000 historical result is unchanged. Rebuilt bundle SHA-256 is
  `3620E5B736812D625FE397F2238CAB06AC66F892BF76E7ADD047638DCC700A0C`.
- Commit identifier: `48ae072` (`refactor: generalize aggregate workflow nationwide`).
- Remaining limitations: reusable code recognizes all 16 locations, but actual
  completed-transaction coverage remains Penang 2017 and regional published
  averages omit Putrajaya and Labuan. This is not nationwide price validation.
- Dependencies and blockers: no dependency changed. Existing licensed-data,
  district-reference, multi-year, and property-level blockers remain.
