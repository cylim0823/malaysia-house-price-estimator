# Aggregate Baseline Evaluation

## Prediction target and split

The target is average completed transaction price for a selected Penang
district, source property category, year, and quarter. Training uses 158
aggregate rows (8,646 transactions) from 2017 Q1-Q3. The untouched provisional
test uses 54 Q4 rows representing 3,170 transactions.

This within-year split is time ordered, but it does not validate multi-year
forecasting, current 2026 accuracy, or a specific property's value.

## Leakage controls

Features are `state`, `district`, `property_type`, `year`, and `quarter`.
`transaction_value_rm` and `transaction_count` are explicitly forbidden as
ordinary model features. Count is used as sample weight and support metadata.
Preprocessing cannot derive the target from total value.

## Baselines compared

- Overall transaction-weighted average
- State weighted average
- District weighted average
- Property-type weighted average
- State + district + property-type weighted average
- Previous-quarter average with a training-only segment fallback

The segment weighted average achieved the lowest Q4 transaction-weighted MAE
and was selected. No advanced model was trained because the dataset has only
one year; complexity would not repair the missing temporal evidence.

## Provisional Q4 metrics

| Metric | Result |
| --- | ---: |
| Unweighted MAE | RM64,764.81 |
| Median absolute error | RM28,201.59 |
| Unweighted RMSE | RM103,787.95 |
| Unweighted MAPE | 17.79% |
| R² | 0.9499 |
| Transaction-weighted MAE | RM36,676.57 |
| Transaction-weighted RMSE | RM69,133.96 |
| Transaction-weighted MAPE | 8.00% |
| Weighted R² | 0.9730 |

Unweighted metrics treat every aggregate group equally. Weighted metrics give
greater influence to groups representing more completed transactions. The
difference is expected because many large errors occur in low-volume groups.
Slice metrics are emitted only for groups with at least three aggregate rows
and 20 represented transactions.

## Public support policy

The Streamlit explorer exposes only actual dataset combinations. It shows the
published historical average and transaction count for all retained groups,
but suppresses predictive support below 20 transactions. A provisional
baseline estimate is shown only for Q4, the evaluated period. Q1-Q3 are shown
as historical inputs to the evaluation, not retroactive predictions.

The full metrics and baseline comparison are stored in
`reports/aggregate_transaction_model_metrics.json`.

