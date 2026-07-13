# State-Generalization Audit

Audit date: 13 July 2026

## Outcome

The active historical application uses one metadata-driven explorer for every
approved aggregate dataset. The state, area, property type, year, and quarter
selectors are derived from validated observation combinations. Adding another
dataset normally requires source files, a `data/processed/dataset_catalog.json`
entry, a source-column adapter when formats differ, and a pipeline run. It does
not require a state-specific cleaner, trainer, prediction service, or UI page.

The architecture recognizes all 13 states and Kuala Lumpur, Putrajaya, and
Labuan. This is engineering readiness, not validated price coverage. The UI
shows only states and combinations present in a selected validated dataset.

## Penang-reference classification

### Category A — legitimately source-specific

- `data/external/penang/`, its README, and the original source filenames.
- Penang provenance in `data/raw/aggregate_transactions/metadata.json` and the
  approved processed rows and reports.
- `PenangOpenDataAdapter` source filenames, Malay column labels, source district
  mappings, exclusions, fixed source year, and source state.
- Source-specific licence, catalogue URLs, dataset version, documents, and
  limitations in `data/processed/dataset_catalog.json`.
- Tests and documentation that assert the known source values and preserved
  fixed historical prediction.

### Category B — data represented as metadata or observed coverage

- Dataset title, publisher, price type, paths, licence and redistribution
  status, version, and limitations are in `dataset_catalog.json`.
- Supported states, areas, property types, earliest/latest period, and every
  selectable combination are generated from the model's validated observation
  keys by `CoverageCatalog`.
- The latest available selector values and displayed coverage are derived at
  runtime; Python UI code contains no Penang district list or fixed year list.

### Category C — removed from the active core

- Removed `render_penang_explorer` and Penang-specific main-UI wording.
- Removed fixed 2016/2017/2018 and Q1/Q2 selector logic.
- Removed Penang source/provenance defaults from aggregate validation.
- Replaced the hardcoded Q4 aggregate split with a latest-validated-period
  split that reproduces the existing Q1–Q3/Q4 result for the current dataset.
- Replaced regional fixed-year prediction checks with exact observed-combination
  validation.

Obsolete aggregate and synthetic import shims were removed; current code uses
`aggregate_data.py`, `data_pipeline.py`, and `synthetic_data.py`. The former
state-specific benchmark module and artefact were also removed.

## Primary runtime modules

- `data_pipeline.py`: generic aggregate validation, quality reporting, temporal
  split, weighted baselines, and bundle contract.
- `aggregate_data.py`: licensed snapshot aggregation, dynamic coverage, annual
  weighting, year status, and fallback disclosure.
- `source_adapters/napic_excel.py`: configurable NAPIC publication importer.
- `data_sources.py`: dataset metadata and source adapters.
- `location_catalog.py`: the 16 canonical locations and dynamic coverage.
- `modelling.py`: reusable individual-record model candidates.
- `evaluation.py`: reusable regression metrics and reports.
- `prediction.py`: property and historical prediction services.
- `synthetic_data.py`: clearly labelled synthetic engineering fixtures.

Focused schema, cleaning, persistence, CLI/API, and compatibility modules remain
separate where combining them would obscure a distinct contract or break saved
artifacts.
