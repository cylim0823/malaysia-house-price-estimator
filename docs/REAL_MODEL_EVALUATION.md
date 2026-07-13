# Aggregate Baseline Evaluation

## Target and split

The aggregate target is average completed transaction price for a state, district, property type, year, and internal quarter. The user-facing historical explorer selects a year and computes the observed annual or year-to-date benchmark directly from totals.

The generic baseline trains on validated 2021 Q1-2025 Q4 groups and evaluates provisionally on 2026 Q1. The selected model is the state + district + property-type transaction-weighted mean because it has the lowest weighted MAE among the registered simple baselines. Full results are in `models/historical_aggregate/evaluation_summary.json`.

## Leakage controls

Model features are state, district, property type, year, and internal quarter. Transaction value and transaction count are forbidden as ordinary features. Count is used only as sample weight/support. Annual observed benchmarks use transaction value solely as the numerator of the published arithmetic identity; they are not model predictions.

## Baselines

- Overall transaction-weighted average
- State weighted average
- State/district weighted average
- Property-type weighted average
- State/district/property-type weighted average
- Previous-period average with a training-only segment fallback

Advanced models were not selected by default. They remain a future comparison on identical time splits.

## Coverage and interpretation

The release has 15,216 aggregate rows representing 428,443 completed transactions. It preserves licensed 2017 history and covers all 16 jurisdictions from 2021 through 2026 Q1, with 129 district labels and 11 normalized categories. Results vary materially by segment support. Aggregate performance never establishes individual-property accuracy.

The historical service reports direct transaction-weighted observations, periods included/missing, coverage status, attribution, and fallbacks. A complete year requires Q1-Q4; 2026 is year to date through Q1. No missing period is invented.
