# Aggregate Completed-Transaction Dataset

## 2026 recency investigation

NAPIC aggregate publication workbooks were inspected through 2026 Q1P. State transaction XLSX files contain compatible count/value sheets, but the current files state copyright reserved and publish no compatible reuse/model licence. They were not integrated, and no quarter was inferred from half-year or annual totals. The aggregate explorer therefore still ends at 2018 Q2 (regional averages) and 2017 Q4 (Penang count/value groups). See `RECENT_OFFICIAL_DATA_INVESTIGATION.md`.

The separately licensed Data Transaksi Terbuka feed is individual transaction data and is intentionally handled by a different pipeline/model.

## Meaning and scope

**Each dataset row is an aggregate statistic, not one property transaction.**

One row represents a `state + district + property_type + year + quarter` group.
`transaction_count` is the number of completed transfers represented by the
row, `transaction_value_rm` is their combined value, and `average_price_rm` is
their arithmetic average. The dataset cannot describe or estimate a specific
house because it has no size, address, project, rooms, tenure, furnishing,
condition, floor, land size, or renovation fields.

## Source and preservation

- Imported CSV: `data/processed/historical_prices/penang_district_transactions_2017.csv`
- Immutable raw copy: `data/raw/aggregate_transactions/penang_district_transactions_2017.csv`
- Original source files: the transaction-count and transaction-value CSVs in `data/external/penang/`
- Publisher: Penang State Government through Malaysia's archived government open-data catalogue
- Source documents: 2017 residential transaction counts and values by property type, quarter, and district
- Source table: quarter/property-type/district tables
- Accessed: 13 July 2026
- Licence: Creative Commons Attribution, as labelled by the catalogue for both source datasets
- Counts source: https://archive.data.gov.my/data/en_US/dataset/pecahan-bilangan-pindah-milik-harta-kediaman-mengikut-jenis-dan-daerah-di-pulau-pinang
- Values source: https://archive.data.gov.my/data/en_US/dataset/pecahan-bilangan-pindah-milik-harta-kediaman-mengikut-jenis-dan-daerah-rm-juta-di-pulau-pinang
- Raw file size: 26,404 bytes
- Raw SHA-256: `DAFF6F0A4EBB08548CAD6581CE1E687B6D66398CBD1ECC003DCF86020275BF47`
- Dataset version: `penang-completed-transaction-aggregates-2017-v2`
- Aggregate schema version: `aggregate-1.0.0`
- Price type: `completed_transaction_average`

Machine-readable provenance is stored in
`data/raw/aggregate_transactions/metadata.json`. The raw copy is compared byte
for byte with the imported CSV before processing and is never modified in
place.

## Verified coverage

- Aggregate rows: 212
- Underlying completed transactions: 11,816
- Total transaction value represented: RM5,171,921,352
- State: Penang only
- Districts: Barat Daya, Timur Laut, Seberang Perai Utara, Seberang Perai Tengah, and Seberang Perai Selatan
- Years: 2017 only
- Quarters: Q1, Q2, Q3, and Q4
- Earliest/latest year: 2017/2017
- Controlled property types: 11
- Duplicate aggregate combinations: 0
- Arithmetic mismatches: 0
- Rejected rows: 0
- Missing combinations in the observed state × district × type × year × quarter grid: 8

The missing combinations are four condominium/apartment quarters in Seberang
Perai Selatan, Q1-Q3 flat rows in Seberang Perai Selatan, and the Q3 town-house
row in Seberang Perai Tengah. A missing group is not interpreted as zero
transactions unless the source explicitly says so.

## Normalisation

Raw fields are preserved alongside controlled fields. Parenthetical district
context is separated without guessing:

- `Timur Laut (George Town / northeast island)` becomes district `Timur Laut`
  and note `George Town / northeast island`.
- `Barat Daya (southwest island / Teluk Bahang)` becomes district `Barat Daya`
  and note `southwest island / Teluk Bahang`.

The source category `Condominium/Apartment` remains the single controlled value
`condominium_apartment`; the pipeline does not pretend that its condominium and
apartment components are independently known. Flat and low-cost flat remain
separate. Detached is not renamed bungalow.

## Validation and support rules

For every row, the pipeline verifies
`average_price_rm ≈ transaction_value_rm / transaction_count`, with a one-cent
or tighter proportional tolerance. Counts must be positive integers; prices and
values must be positive; year and quarter must be valid; locations and types
must be present and controlled; and the price type must map to completed-
transaction average.

Volume support is provisional:

- `very_low_volume`: 1-4 transactions
- `low_volume`: 5-19
- `medium_volume`: 20-99
- `high_volume`: 100 or more

Low-volume rows are retained and flagged. Rows below 20 transactions are shown
for historical transparency but excluded from public predictive support.

## Leakage protection

The target is `average_price_rm`. Model features are limited to state,
district, property type, year, and quarter. `transaction_value_rm` is forbidden
because it algebraically determines the target when divided by count.
`transaction_count` is not a prediction feature; it is used only as a training
and evaluation weight and as support metadata.
