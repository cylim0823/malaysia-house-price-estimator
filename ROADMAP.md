# Roadmap

The long-term goal is a validated residential sale-price estimator covering all Malaysian states and federal territories. Coverage will expand incrementally according to legal permission, verified data quality, local sample size, and demonstrated accuracy. No fixed completion dates are assigned.

## Status dimensions

- **Engineering complete:** the source-neutral component is implemented, tested with synthetic fixtures, documented, and locally runnable.
- **Limited real-data prototype complete:** licensed JPPH/NAPIC data now provides selected district/region terraced coverage for 14 states/territories and richer five-district Penang transaction aggregates. The regional expansion is local and not yet published.
- **Property-level validation pending:** individual-home conclusions and current estimates still require an approved property-level dataset.
- **GitHub publication complete:** the public repository is available under `cylim0823/malaysia-house-price-estimator`.
- **Public deployment complete:** the historical-average Streamlit prototype is live on Streamlit Community Cloud.

Current data decision: the JPPH district/region terraced workbook, four state-average workbooks, and two Penang district transaction datasets were approved because the government catalogue marks them Creative Commons Attribution. No clearly licensed property-level candidate passed provenance and reuse review; see `docs/REAL_DATASET_ASSESSMENT.md`.

The local engineering framework spans schema, structured-file ingestion, cleaning, duplicate/outlier review, synthetic generation, EDA, feature engineering, group/time-safe splitting, baseline and optional advanced models, evaluation reports, saved bundles, prediction service, Streamlit, optional FastAPI, configuration, and CLI. Original checkboxes below remain tied to real-data completion criteria and do not imply genuine market validation.

## Phase 0 — Project planning and documentation

**Objective:** Establish a consistent nationwide goal, constraints, principles, and working rules without adding runtime implementation.

### Tasks

- [x] Define project goal
- [x] Define nationwide Malaysia scope
- [x] Define intended users and initial limitations
- [x] Define proposed technology stack
- [x] Define data and modelling principles
- [x] Define repository rules
- [x] Create `README.md`
- [x] Create `ROADMAP.md`
- [x] Create `AGENTS.md`

### Completion criteria

- [x] All three documentation files exist and have consistent scope
- [x] No runtime implementation has been added

## Phase 1 — Malaysia data-source investigation

**Objective:** Identify legally and technically usable sources and establish realistic initial coverage before collection code is considered.

### Tasks

- [x] Investigate Malaysian official open-data sources and property transaction datasets
- [x] Investigate public listing sources and state-specific availability
- [x] Investigate geographic reference datasets
- [x] Review available terms of service, robots rules, licences, copyright, privacy, and access restrictions; record unavailable or unclear evidence
- [x] Identify asking-price versus transaction-price data
- [x] Record fields, update frequency, geographic coverage, and missing states or districts where public evidence permits
- [x] Classify source access as usable, restricted, or requiring further permission; do not assume approval
- [ ] Create a small manually verified sample dataset
- [x] Assess whether nationwide coverage is currently realistic and document evidence gaps
- [ ] Request a NAPIC e-Data sample schema, coverage counts, quotation, and written model-training/publication terms
- [ ] Request permission or a licensed data agreement before systematic listing-platform collection

### Completion criteria

- [x] Every investigated source has a documented legal and technical status, including explicit uncertainty where evidence is incomplete
- [x] No source is described as approved without verification
- [ ] Required property-level fields and nationwide coverage are confirmed from an approved source

## Phase 2 — Canonical data schema

**Objective:** Define a versioned, source-independent property record that preserves provenance and separates price types.

### Tasks

- [x] Define data types and required/optional status for every canonical field
- [x] Define source identifiers, price types, dates, validation states, rejection reasons, duplicate identifiers, and schema versioning
- [x] Define canonical Malaysian state and federal territory values, location concepts, property categories, and area units
- [x] Define missing-value and data-type rules
- [x] Define raw, interim, and processed data-layer responsibilities
- [x] Define outlier, duplicate-grouping, and model-eligibility metadata
- [ ] Reconcile the canonical schema against the first approved source's actual field dictionary
- [ ] Select and version an approved official district/code reference

Suggested fields:

```text
record_id
source_name
source_record_id
source_url
collected_at
listing_date
transaction_date
price
price_type
state
district
city
township
project_name
property_type
property_subtype
built_up_sqft
land_area_sqft
bedrooms
bathrooms
storeys
tenure
furnishing
property_age_years
latitude
longitude
description
is_duplicate
duplicate_group_id
validation_status
validation_notes
```

### Completion criteria

- [x] Every proposed field has a data type and required/optional status
- [x] Price types are clearly separated
- [x] All Malaysian state and federal territory values and location-level rules are documented

## Phase 3 — Data collection

**Objective:** Collect approved data reproducibly, conservatively, and one isolated source at a time.

### Tasks

- [ ] Prefer approved APIs and downloadable files; implement one source at a time
- [ ] Add conservative throttling, timeouts, bounded retries, and exponential backoff
- [ ] Add logging, collection timestamps, source identifiers, and permitted source URLs
- [ ] Add explicit record/page limits, stop conditions, and resumable collection
- [ ] Prevent uncontrolled crawling
- [ ] Save raw data without modification
- [ ] Track coverage by state and district

### Completion criteria

- [ ] Collection respects the approved source policy
- [ ] Raw records are reproducible and failures are logged
- [ ] Collection can be stopped and resumed safely

## Phase 4 — Data cleaning and validation

**Objective:** Produce traceable, reproducible cleaned data while preserving raw evidence and rejected records.

### Tasks

- [ ] Standardise state, federal territory, district, city, township, property type, tenure, and furnishing values (state and conservative property vocabularies implemented; lower-level geography awaits an approved reference)
- [x] Parse Malaysian ringgit values, including `RM650k`
- [x] Parse areas and consistently convert square metres to square feet while preserving original units
- [x] Parse bedroom and bathroom formats, including `4+1`
- [x] Handle missing values without fabrication
- [x] Detect impossible values and flag extreme outliers before removal
- [x] Detect and group duplicate listings
- [x] Preserve rejected rows with documented reasons
- [x] Produce quality and coverage reports by state and district
- [ ] Version cleaned datasets (version metadata implemented; persistent releases require an approved source and storage policy)

### Completion criteria

- [x] Raw data remains unchanged and invalid records are traceable
- [x] Duplicate and rejection rules are documented
- [x] Cleaning is reproducible and geographic coverage is reported

## Phase 5 — Exploratory data analysis

**Objective:** Understand distributions, relationships, imbalance, coverage, and data-quality risks before modelling.

### Tasks

- [ ] Analyse price and price-per-square-foot distributions
- [ ] Analyse price by state, district, city/township, property type, and tenure
- [ ] Analyse built-up area, land area, and price relationships
- [ ] Analyse missing values, outliers, and duplicates
- [ ] Analyse geographic and time coverage
- [ ] Analyse imbalance across states and districts
- [ ] Compare asking and transaction prices where valid paired evidence exists

### Completion criteria

- [ ] Major quality problems and coverage gaps are clear
- [ ] Modelling assumptions and unusable features are documented

## Phase 6 — Baseline modelling

**Objective:** Establish reproducible reference performance without leakage.

### Tasks

- [ ] Create national, state-level, and district/property-type median baselines
- [ ] Implement Linear Regression with reproducible preprocessing
- [ ] Use time-based splitting where possible
- [ ] Group duplicate properties before splitting
- [ ] Keep a final test set untouched
- [ ] Evaluate nationally and by state and district
- [ ] Produce a baseline report

### Completion criteria

- [ ] Every model is compared against a simple baseline
- [ ] No known duplicate or preprocessing leakage exists
- [ ] Metrics are consistent and weakly covered locations are identified

## Phase 7 — Advanced modelling

**Objective:** Compare stronger tabular models and feature strategies on identical splits.

### Tasks

- [ ] Evaluate Random Forest, suitable Histogram Gradient Boosting, and CatBoost
- [ ] Run optional K-Nearest Neighbours, log-price, and price-per-square-foot experiments
- [ ] Engineer location-frequency, coordinate, property-age, and market-period features
- [ ] Tune hyperparameters without exposing the final test set
- [ ] Analyse feature importance and residuals
- [ ] Analyse error by state, district, property type, price band, and rare location

### Completion criteria

- [ ] Models use identical evaluation splits
- [ ] Selection uses several metrics and considers geographic coverage
- [ ] The selected model clearly outperforms relevant baselines

## Phase 8 — Prediction pipeline

**Objective:** Provide safe, reproducible predictions only within validated coverage.

### Tasks

- [ ] Save preprocessing and model together
- [ ] Validate and standardise user and location inputs
- [ ] Handle unknown categories and reject unsupported property types or areas
- [ ] Return central estimate, estimated range, price per square foot, and neutral asking-price assessment
- [ ] Return confidence, important factors, model version, and data-coverage information

### Completion criteria

- [ ] Training and prediction use identical preprocessing
- [ ] Unsupported inputs are handled safely
- [ ] Prediction metadata is complete and results are reproducible

## Phase 9 — Streamlit web MVP

**Objective:** Provide a simple, mobile-readable interface that communicates uncertainty and limitations.

### Tasks

- [ ] Add state, district, city/township, and project-name inputs
- [ ] Add property type, built-up area, land area, bedroom, bathroom, storey, tenure, furnishing, and property-age inputs
- [ ] Add optional asking-price input
- [ ] Display estimated price, range, price per square foot, asking-price assessment, confidence, and coverage warning
- [ ] Display model limitations and disclaimer
- [ ] Add friendly validation and a mobile-readable layout

### Completion criteria

- [ ] Users can enter supported details and invalid inputs are explained
- [ ] Unsupported locations receive no misleading prediction
- [ ] The required disclaimer is visible

## Phase 10 — Testing and deployment

**Objective:** Make the supported application verifiable, reproducible, and safe to demonstrate publicly.

### Tasks

- [ ] Add unit, data-validation, cleaning, duplicate-detection, model-loading, and prediction tests
- [ ] Add smoke, regression, unknown-location, unknown-category, and Streamlit integration tests
- [ ] Lock dependencies and document deployment
- [ ] Prepare the GitHub repository and public demo
- [ ] Add dependency monitoring and basic application logging

### Completion criteria

- [ ] Relevant tests pass and deployment is reproducible
- [ ] Secrets are excluded
- [ ] Public documentation and demo limitations are accurate

## Phase 11 — Nationwide expansion

**Objective:** Expand actual support only when each region meets verified data and evaluation thresholds.

### Tasks

- [ ] Measure sufficiency for every state and federal territory
- [ ] Add missing states, districts, and property types gradually
- [ ] Retrain as coverage improves
- [ ] Compare national and regional models
- [ ] Consider separate East Malaysia and distinct-market models
- [ ] Add regional evaluation reports and coverage maps
- [ ] Mark unsupported and low-confidence locations

### Completion criteria

- [ ] Each supported region has sufficient verified data and meets minimum evaluation requirements
- [ ] Unsupported areas are clearly identified
- [ ] Nationwide claims match actual coverage

## Phase 12 — Future improvements

**Objective:** Explore enhancements after the core estimator is reliable.

### Tasks

- [ ] Integrate suitable official transaction data
- [ ] Add comparable-property search and historical price trends
- [ ] Add an interactive map, nearby amenities, transport, school, and hospital proximity
- [ ] Investigate geospatial modelling
- [ ] Consider FastAPI and a custom HTML/CSS/JavaScript frontend
- [ ] Consider an optional C# WPF client and ONNX export
- [ ] Consider user accounts and saved comparisons
- [ ] Add automated refresh, scheduled retraining, and model-drift monitoring

### Completion criteria

- [ ] Each enhancement has an approved need, data basis, security review, tests, and updated documentation
