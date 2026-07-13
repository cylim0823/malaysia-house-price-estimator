# Project Blockers

Last updated: 13 July 2026

## Phases 1–3 — Approved property-level source

- Exact blocker: no property-level Malaysian residential sale dataset or listing source is approved for collection and machine-learning use.
- Why progress cannot safely continue: collection would require a purchase, contractual/licence decision, written permission, credentials, or unsupported scraping. The owner explicitly prohibited scraping iProperty, Mudah, PropertyGuru, and EdgeProp.
- Owner action required: obtain a NAPIC/JPPH sample schema, coverage counts, quotation, and written terms covering local model training, derived artefacts, publication, retention, and redistribution; alternatively provide a lawfully licensed property-level dataset and its field dictionary.
- Work completed: source investigation, legal/technical classifications, canonical schema, and source-independent cleaning core.
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
- Work completed: local demonstration framework through ingestion, cleaning, EDA, splitting, modelling, evaluation, saved bundle, prediction service, CLI, Streamlit, and optional API. Synthetic outputs carry an explicit disclaimer.
- Recommended next action: ingest a small authorised sample, reconcile its schema, then add source-specific validation before EDA.

## Phase 10 — Public deployment

- Exact blocker: publishing requires explicit approval and deployment credentials; no validated application exists yet.
- Why progress cannot safely continue: external publication is irreversible and could misrepresent model accuracy or data rights.
- Owner action required: only after model validation, select an approved host and provide deployment authority/credentials through a secure mechanism.
- Work completed: local Streamlit and optional FastAPI adapters are implemented and smoke-tested with the synthetic demonstration bundle.
- Recommended next action: defer public deployment until real-data validation and a separate deployment review are complete.

## GitHub publication — CLI authentication

- Exact blocker: the official portable GitHub CLI runs successfully but `gh auth status` reports that no GitHub host is authenticated.
- Why progress cannot safely continue: repository creation and push require the owner's GitHub browser/device authorization. Passwords, tokens, and verification codes must not be handled by an agent.
- Owner action required: run `gh auth login`, complete the browser flow for account `cylim0823`, and confirm with `gh auth status`.
- Work completed: dataset assessment, deployable synthetic bundle, Streamlit configuration, dependency file, security exclusions, tests, local Git initialization, and initial commit.
- Recommended next action: authenticate GitHub CLI, then create and push the public `malaysia-house-price-estimator` repository.

## Streamlit Community Cloud — one-time authorization

- Exact blocker: deployment requires the owner to sign in with GitHub and authorize Streamlit Community Cloud.
- Owner action required: follow `docs/STREAMLIT_DEPLOYMENT.md` after the GitHub push and return the resulting public URL.
- Work completed: the entrypoint, dependencies, repository-relative model path, small demo bundle, clear synthetic banner, and deployment instructions are ready.
