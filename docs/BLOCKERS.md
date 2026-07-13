# Project Blockers

Last updated: 13 July 2026

## Recent aggregate publications (blocked)

- Blocked phase: aggregate historical extension through 2026 Q1P.
- Exact blocker: NAPIC's current transaction, residential-price, and MHPI XLSX publications state copyright reserved and publish no compatible model-training, derived-model, redistribution, or public-prediction licence.
- Why progress cannot safely continue: public download access alone is not permission to copy the tables into a training dataset or public repository.
- Owner action required: obtain written NAPIC/JPPH permission or point to an explicit compatible published licence.
- Completed before stopping: confirmed the Q1/Q3 cadence, inspected the state count/value workbook structure, verified MHPI coverage from 2019 Q1 through 2026 Q1P, and confirmed Q1 2026 publications for all 16 jurisdictions.
- Recommended next action: request rights for the structured XLSX files; PDF extraction is unnecessary.

## Fine-grained property attributes (partially blocked)

- Affected work: bedroom, bathroom, car-park, furnishing, completion-year/age, renovation, condition, city/township, and project-level adjustments.
- Exact blocker: the approved NAPIC open transaction feed does not publish these fields.
- Why it matters: the active real model cannot truthfully use information absent from training data.
- Owner action required: supply or license an original-publisher dataset containing those attributes and completed transaction prices.
- Completed before stopping: the full optional UI is implemented and every supplied value is disclosed as used or unused. District, published property type, areas, tenure, and floor level are supported where present.

## Resolved: approved property-level source

The former property-source blocker is resolved for the fields published by NAPIC Data Transaksi Terbuka. The official open-data feed supplied 416,627 completed residential transactions across all 16 jurisdictions through 2026 Q1. Paid PRISM data and restricted listing sources remain out of scope.

## Superseded property-level source blocker

This blocker was resolved on 13 July 2026 by the separately licensed NAPIC Data Transaksi Terbuka feed. The older notes below are retained only as decision history and no longer describe current source availability.

- Exact blocker: no property-level Malaysian residential sale dataset or listing source is approved for collection and machine-learning use.
- Why progress cannot safely continue: collection would require a purchase, contractual/licence decision, written permission, credentials, or unsupported scraping. The owner explicitly prohibited scraping iProperty, Mudah, PropertyGuru, and EdgeProp.
- Owner action required: obtain a NAPIC/JPPH sample schema, coverage counts, quotation, and written terms covering local model training, derived artefacts, publication, retention, and redistribution; alternatively provide a lawfully licensed property-level dataset and its field dictionary.
- Work completed: source investigation, legal/technical classifications, canonical schema, source-independent cleaning core, licensed state aggregates, a five-district Penang benchmark, and 600 terraced/high-rise regional observations. Terraced coverage spans all 13 states plus Kuala Lumpur. Manual copying or automated scraping of listing portals remains excluded unless the original source grants compatible collection and model-use permission.
- Recommended next action: make an institutional/owner-authenticated NAPIC enquiry without purchasing or accepting terms until the response is reviewed.

The Q1 2026 NAPIC publication index confirms that tables exist for Putrajaya,
Labuan, and every state, but the site marks its content copyright reserved and
does not state compatible bulk/model-training reuse terms. Public visibility is
not treated as permission to transcribe or train on those tables.

## Phases 2 and 4 — Official geographic reference

- Exact blocker: no versioned, approved official district/code reference with confirmed reuse terms is stored in the repository.
- Why progress cannot safely continue: district, division, city, and township relationships vary, especially in Sabah and Sarawak; guessing would violate the location rules.
- Owner action required: confirm reuse permission and provide/version the applicable MyGeoportal UPI district/code download or another authoritative licensed reference.
- Work completed: all 16 state/federal-territory names and conservative aliases are implemented; lower-level text is preserved without guessed mappings.
- Recommended next action: review the exact reference release and licence alongside the first source dictionary.

## Phases 5–11 — Real-data validation dependency

- Resolved data blocker: the approved NAPIC open transaction snapshot contains 416,627 cleaned completed transactions across all 16 jurisdictions.
- Remaining limitation: source fields omit bedrooms, bathrooms, parking, furnishing, condition, renovation, and stable transaction identifiers.
- Recommended next action: seek an authorised richer official sample and compare it without mixing incompatible targets.

## Phase 10 — Individual-property public deployment

- Resolved data blocker: the licensed NAPIC open transaction feed supports a separate individual-property estimator across all 16 jurisdictions.
- Remaining blocker: the public deployment has not been refreshed and optional physical/condition attributes remain unavailable from the source.
- Recommended next action: refresh deployment after regression verification, then monitor source and model drift.

## Aggregate forecasting and publication-workbook reuse

- Resolved coverage issue: the derived licensed aggregate dataset now contains 15,216 groups representing 428,443 transactions, including all 16 jurisdictions from 2021 through 2026 Q1.
- Remaining modelling limitation: nationwide engineering coverage does not establish equal district/type support or future-price accuracy. Rare segments can be partial.
- Remaining legal blocker: NAPIC publication XLSX files are publicly downloadable but state copyright reserved; compatible redistribution/model-use permission was not found.
- Work completed: all 16 Q1 2026 files were downloaded locally, hashed, and validated through one importer, while remaining Git-excluded and unused by the model.
- Recommended next action: compare stronger time-aware models on the licensed open feed and request written permission before integrating publication workbook values.

## Resolved — GitHub publication

- Resolution: GitHub Desktop credentials were used to connect the local history safely; the public repository is https://github.com/cylim0823/malaysia-house-price-estimator.

## Resolved — Streamlit Community Cloud authorization

- Resolution: repository access was authorized and the app was deployed at https://malaysia-house-price-estimator-nnddkdymt6prvwdtkfww5y.streamlit.app.
