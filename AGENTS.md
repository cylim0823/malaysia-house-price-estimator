# Instructions for Codex Agents

## Project overview

This project aims to estimate Malaysian residential property sale prices. Its intended final scope is all Malaysian states and federal territories, but coverage will expand incrementally as verified data and evaluation permit. Python is the primary planned language, and Streamlit is the planned first interface.

The repository contains a locally testable engineering framework, a clearly labelled synthetic demonstration workflow, and licensed historical aggregate-data explorers. The Penang dataset contains grouped completed-transaction statistics, not individual records; the JPPH path contains published regional averages. Neither establishes individual-property accuracy or current-market coverage. Engineering completion never implies individual-property validation.

## Required reading

Before changing the repository:

1. Read `README.md`.
2. Read `ROADMAP.md`.
3. Read this `AGENTS.md` completely.
4. Inspect the repository and its current status.
5. Inspect all files relevant to the requested change.
6. Confirm the current roadmap phase and task scope.

## General development rules

- Keep every task narrow, reviewable, and testable; do not implement unrelated improvements.
- Do not silently change architecture. Explain important architectural changes.
- Do not create unnecessary files or placeholder modules without a current purpose.
- Prefer simple, maintainable solutions and focused modules. Do not put the whole project in one Python file.
- Use clear names, Python type hints, and concise docstrings where useful.
- Avoid comments that merely repeat code.
- Preserve working behaviour unless the requested change requires otherwise.
- Do not claim completion without verification or mark future roadmap work complete.
- Update documentation when actual behaviour, architecture, sources, or limitations change.

## Scope rules

- The long-term product covers all 13 Malaysian states and Kuala Lumpur, Putrajaya, and Labuan.
- Implementation may begin with a smaller verified subset, but no single state represents all of Malaysia.
- Never claim nationwide support unless every claimed region is actually supported and validated.
- Never predict for an unsupported area. Reject it or show an explicit weak-data warning according to validated policy.
- Regional models may be used only when justified by comparative evaluation.

## Data rules

- Never modify raw data in place. Keep raw, interim, cleaned, and processed data separate.
- Preserve provenance, collection dates, source identifiers, original values, price type, validation status, and dataset version.
- Do not mix asking, completed-transaction, rental, or auction records without explicit labels. Do not include rentals in the sales model.
- Do not fabricate missing values or silently discard invalid rows. Preserve rejected rows and reasons.
- Deduplicate before splitting. Copies of one property must not enter different dataset splits.
- Avoid unnecessary agent, owner, or tenant personal data.
- Do not commit large datasets without approval or publicly release data with unclear licensing.

## Malaysian location rules

- Use canonical state and federal territory names in cleaned data while preserving original location text in raw data.
- Keep state, district, city, township, and project name as distinct concepts.
- Do not guess a district or merge similarly named townships when evidence is ambiguous.
- Treat Kuala Lumpur, Putrajaya, and Labuan as federal territories.
- Do not assume Peninsular Malaysia patterns apply equally to Sabah and Sarawak.
- Validate geographic mappings before modelling and record uncertain mappings for review.

## Scraping and collection rules

- Before implementing collection, review terms of service, robots rules, licensing, copyright, privacy, and access controls.
- Prefer a documented API or downloadable dataset.
- Never claim that a website permits scraping until permission and rules are verified.
- Never bypass logins, CAPTCHAs, paywalls, anti-bot protections, or other technical restrictions.
- Never rotate identities or proxies to evade blocking or automate login without explicit approval.
- Use conservative request rates, timeouts, bounded retries, exponential backoff, page/record limits, and clear stop conditions.
- Log collection and make it safely resumable. Stop when a site blocks access or objects.
- Isolate each source-specific collector. Scraper changes must not automatically alter model logic.

## Data-cleaning rules

- Cleaning must be reproducible. Preserve raw values and record normalised values separately where appropriate.
- Parse Malaysian ringgit carefully, including `RM650k`, `RM 650,000`, and `650000`.
- Preserve original area units and convert square metres and square feet consistently.
- Handle bedroom formats such as `4+1`; do not count helper rooms as full bedrooms without a documented rule.
- Standardise property types using documented mappings.
- Flag extreme values before removal, preserve rejected rows, and record reasons.
- Generate quality and coverage summaries by state and district.

## Machine-learning rules

- Treat this as supervised regression and implement meaningful simple baselines first.
- Compare advanced models against the same baselines and identical evaluation splits.
- Use reproducible seeds and prefer time-based splitting for time-sensitive records.
- Fit preprocessing only on training data and prevent target, duplicate, temporal, and geographic leakage.
- Keep the final test set untouched until final evaluation.
- Evaluate nationally and by state, district, property type, price band, data coverage, and rare category.
- Report MAE in Malaysian ringgit. Do not rely only on R², and interpret MAPE carefully for low prices.
- Complexity does not imply quality. Do not use deep learning before simpler models are evaluated.
- Do not preselect CatBoost. K-Nearest Neighbours may be an experiment but is not automatically a production model.
- Record model parameters, feature definitions, dataset version, model version, training date, and evaluation results.

## Prediction rules

- Validate every input and do not silently replace invalid values.
- Handle unknown categories and unsupported states, districts, and property types explicitly.
- Return no prediction outside validated coverage.
- Where supported, return a central estimate and range without describing either as guaranteed.
- Include limitations, coverage information, confidence context, and model-version metadata.
- Use only these neutral asking-price assessments: `Below estimated range`, `Within estimated range`, and `Above estimated range`.
- Never say `Guaranteed bargain`, `Guaranteed profit`, `Official valuation`, or `Guaranteed market price`.

## UI rules

- Keep the first Streamlit interface simple, mobile-readable, and focused on clear validation.
- Show unsupported locations and low-confidence warnings prominently.
- Avoid unnecessary charts and never hide limitations.
- Do not imply nationwide support before validation.
- Keep data, model, and business logic outside the UI where practical.

## Security and repository rules

Never commit:

- Passwords, API keys, session cookies, authentication headers, private URLs, or personal information
- Unlicensed or large raw datasets
- Trained models without a size and licensing review
- Virtual environments, Python caches, logs, temporary files, or notebook checkpoints
- Local databases containing private data

Use environment variables for secrets. Add a `.gitignore` in a future implementation task when runtime files begin to exist; do not add it speculatively during documentation-only work.

## Testing rules

- Add tests alongside meaningful implementation.
- Test valid, malformed, missing, and impossible inputs, including prices and areas.
- Test unknown states/districts, location normalisation, duplicate detection, and cleaning transformations.
- Test model loading, preprocessing consistency, unsupported categories, and prediction output contracts.
- Run relevant tests before claiming completion and clearly report anything that could not be run.

## Documentation rules

- Update `ROADMAP.md` only after work and completion criteria are verified; written code alone is insufficient.
- Keep `README.md`, `ROADMAP.md`, and `AGENTS.md` consistent.
- Record architecture changes, approved data sources, and known limitations.
- Do not add unsupported accuracy claims or claim nationwide coverage before it exists.
- Keep documentation clear enough for a student developer.

## Required completion report

Every future Codex completion response must summarise:

1. Files inspected
2. Files created
3. Files modified
4. Main changes
5. Tests or validation performed
6. Tasks not completed
7. Remaining limitations
8. Recommended next task
