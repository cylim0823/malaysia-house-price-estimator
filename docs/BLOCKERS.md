# Project Blockers

Last updated: 13 July 2026

## Phases 1–3 — Approved property-level source

- Exact blocker: no property-level Malaysian residential sale dataset or listing source is approved for collection and machine-learning use.
- Why progress cannot safely continue: collection would require a purchase, contractual/licence decision, written permission, credentials, or unsupported scraping. The owner explicitly prohibited scraping iProperty, Mudah, PropertyGuru, and EdgeProp.
- Owner action required: obtain a NAPIC/JPPH sample schema, coverage counts, quotation, and written terms covering local model training, derived artefacts, publication, retention, and redistribution; alternatively provide a lawfully licensed property-level dataset and its field dictionary.
- Work completed: source investigation, legal/technical classifications, canonical schema, source-independent cleaning core, licensed state aggregates, a five-district Penang benchmark, and terraced-house benchmarks for 46 selected areas across 14 states/territories. Manual copying or automated scraping of listing portals remains excluded unless the original source grants compatible collection and model-use permission.
- Recommended next action: make an institutional/owner-authenticated NAPIC enquiry without purchasing or accepting terms until the response is reviewed.

## Phases 2 and 4 — Official geographic reference

- Exact blocker: no versioned, approved official district/code reference with confirmed reuse terms is stored in the repository.
- Why progress cannot safely continue: district, division, city, and township relationships vary, especially in Sabah and Sarawak; guessing would violate the location rules.
- Owner action required: confirm reuse permission and provide/version the applicable MyGeoportal UPI district/code download or another authoritative licensed reference.
- Work completed: all 16 state/federal-territory names and conservative aliases are implemented; lower-level text is preserved without guessed mappings.
- Recommended next action: review the exact reference release and licence alongside the first source dictionary.

## Phases 5–11 — Real-data validation dependency

- Exact blocker: no approved, cleaned, deduplicated real dataset exists.
- Why progress cannot safely continue: engineering can be exercised synthetically, but real EDA conclusions, accuracy, ranges, model selection, supported coverage, and nationwide expansion cannot be validated with fabricated market data.
- Owner action required: resolve the approved-source blocker and provide the authorised data locally with licence metadata.
- Work completed: the source-neutral framework plus a licensed JPPH historical aggregate model and public Streamlit app. This does not resolve the property-level dependency.
- Recommended next action: ingest a small authorised sample, reconcile its schema, then add source-specific validation before EDA.

## Phase 10 — Individual-property public deployment

- Exact blocker: the published historical-average prototype cannot become an individual-property estimator without licensed property-level records.
- Why progress cannot safely continue: aggregate state averages do not contain the required property attributes or transaction-level target.
- Owner action required: provide or authorize a clearly licensed property-level dataset.
- Work completed: public GitHub repository and Streamlit historical-average prototype are live.
- Recommended next action: onboard a licensed transaction-level sample and keep the aggregate prototype clearly separated.

## Resolved — GitHub publication

- Resolution: GitHub Desktop credentials were used to connect the local history safely; the public repository is https://github.com/cylim0823/malaysia-house-price-estimator.

## Resolved — Streamlit Community Cloud authorization

- Resolution: repository access was authorized and the app was deployed at https://malaysia-house-price-estimator-nnddkdymt6prvwdtkfww5y.streamlit.app.
