# Cleaning and Validation Pipeline

## Status and scope

The repository now contains a source-independent cleaning and validation core. It is tested only with clearly labelled synthetic fixtures. No real property data has been collected, no source adapter exists, and no output is suitable for model training yet.

The core implementation lives under `src/house_price_estimator/cleaning/` and does not modify caller-owned records. Source-neutral ingestion, duplicate grouping, outlier review, EDA, and modelling are documented in `ARCHITECTURE_AND_USAGE.md`.

## Implemented rules

- Ringgit parsing accepts numeric values and explicit formats such as `RM650k`, `RM 650,000`, `RM 1.2 million`, and `0.65m`. Malformed, free-text, negative, and zero record prices are rejected.
- Areas require an explicit square-foot, square-metre, acre, or hectare unit. Converted square feet are stored separately while raw values remain available.
- A bedroom value such as `4+1` produces four primary bedrooms by default. The auxiliary room is not silently counted as a full bedroom.
- The 13 states and three federal territories use canonical names. A small, documented spelling/abbreviation map handles values such as `Malacca`, `Pulau Pinang`, and `W.P. Kuala Lumpur`.
- Property type, tenure, and furnishing use conservative controlled mappings. Unknown values are rejected for review instead of guessed.
- Missing optional values remain null. Required record, source, price, price-type, state, and property-type fields cause rejection when absent.
- Asking, completed-transaction, auction, and rental records remain explicitly labelled. Only asking and completed-transaction records can initially be model-eligible, and they must still be kept in separate modelling datasets.

District, city, township, and project text is trimmed but not guessed or mapped. Full geographic standardisation is blocked until a versioned official district/code reference is approved.

## Duplicate grouping

Duplicate candidates are grouped after cleaning and before any future split assignment. The current exact method hashes normalized state, district, project, property type, built-up area, bedrooms, and bathrooms. Each grouped record retains:

- duplicate status and group identifier;
- matching method and confidence;
- canonical-record decision; and
- model-eligibility decision.

The first record in a group is retained as canonical. No record is deleted. A deterministic near-candidate score also considers small price/area differences plus matching location, project, type, and room evidence. Thresholds require real-source calibration and manual evaluation.

## Outliers and rejected records

Parsing and impossible-value failures retain the complete raw record and a rejection reason. Built-up areas above 100,000 square feet are flagged for review and made model-ineligible, not deleted. This threshold is a defensive parsing check, not a claim that legitimate luxury or unusual properties cannot exceed it.

Future source-specific validation must check original units, source consistency, property segment, and source documentation before correcting or excluding an outlier. Corrections must retain raw values and record the transformation.

## Dataset versions and reports

Every pipeline call requires an explicit dataset version and adds schema version `1.0.0`. Its in-memory quality report contains input, accepted, rejected, review, and duplicate-copy counts plus coverage by state and state/district. Persistent immutable dataset releases and report files will be added only after an approved source defines storage and licensing constraints.

## Verification

Run the standard-library tests from the repository root:

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests -v
```

The fixtures are synthetic unit-test examples and are not Malaysian market observations.
