# Real Aggregate Data Quality and EDA

## Dataset scale

The verified Penang 2017 dataset has 212 aggregate rows representing 11,816
completed transactions and RM5.172 billion in transaction value. Total CSV rows
is not equal to total property transactions.

All 212 rows pass blocking validation. Eighty-four rows have at least one
warning. There are no duplicate aggregate keys and no arithmetic mismatches.

## Transaction-count support

| Support | Aggregate rows |
| --- | ---: |
| Very low (1-4) | 26 |
| Low (5-19) | 57 |
| Medium (20-99) | 89 |
| High (100+) | 40 |

The median row represents 27.5 transactions, the mean is 55.7, and the range is
1 to 422. The 83 rows below 20 transactions are retained but excluded from
public predictive support.

## Coverage

Rows by district are Barat Daya 44, Timur Laut 44, Seberang Perai Utara 44,
Seberang Perai Tengah 43, and Seberang Perai Selatan 37. The dataset contains
11 controlled property types and all four quarters of 2017 overall, but eight
segment-quarter combinations are absent. Coverage is Penang-only and cannot
support nationwide claims or current 2026 estimates.

## Quarter-change review

Eight rows change by more than 75% from the preceding available quarter within
the same district/property segment. Examples include low-volume cluster-house
and low-cost-house groups and some detached-house groups. These are review
flags, not automatic errors: composition changes and one or two unusual sales
can materially move an aggregate mean. The raw value, transaction count, and
change percentage remain in the processed data and quality report.

The complete machine-readable report is
`reports/generated/data_quality/historical_aggregate.json`; its suspicious-row list provides
source row, location, category, period, count, average, and change percentage.
No flagged row is silently corrected or deleted.

## Limitations

Only one year is available. Four quarterly points per complete segment are too
few for reliable trend or future-price conclusions. The data is suitable for
historical exploration, arithmetic and pipeline validation, weighted
baselines, and a provisional Q4 holdout—not an individual-property model or a
current-market forecast.
