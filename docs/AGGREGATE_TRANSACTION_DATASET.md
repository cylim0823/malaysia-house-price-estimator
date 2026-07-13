# Aggregate Transaction Dataset

## Current release

`data/processed/aggregate_transactions/malaysia_aggregate_transactions_v1.csv` contains 15,216 validated quarter groups representing 428,443 completed residential transactions. It combines preserved licensed 2017 history with NAPIC open data covering all 13 states and Kuala Lumpur, Putrajaya, and Labuan from January 2021 through March 2026. It contains 129 published district labels and 11 normalized residential categories.

The source is NAPIC/JPPH Data Transaksi Terbuka under Malaysian Government Open Data Terms of Use 1.0. The 16 original state CSV snapshots remain immutable and Git-ignored because of size. Their URLs, hashes, retrieval times, row counts, and coverage are in the local raw manifest. The processed aggregate release contains no personal data.

## Generic schema

Every compatible source maps to:

`state`, `district`, `district_notes`, `property_type`, `year`, `period_type`, `period_number`, `period_start`, `period_end`, `transaction_count`, `transaction_value_rm`, `average_price_rm`, `price_type`, `source_name`, `source_dataset`, `source_file`, `source_sheet`, `source_url`, `source_document`, `source_table`, `retrieved_at`, `dataset_version`, `schema_version`, `validation_status`, `validation_errors`, and `validation_warnings`.

One row is a state + district + property type + quarter group. It is not an individual sale. `average_price_rm` must reconcile to `transaction_value_rm / transaction_count`.

## Annual and year-to-date calculation

The UI groups validated rows for the selected year and calculates:

```text
annual_average_price_rm = sum(transaction_value_rm) / sum(transaction_count)
```

It never takes a simple mean of quarterly averages. A segment containing Q1-Q4 is `complete_year`; a historical segment missing a period is `partial_year`; 2026 is `year_to_date` through Q1. Included periods, missing periods, total transactions, total value, and completeness are returned.

## Dynamic coverage and fallback

Selectors are derived from validated data. The benchmark hierarchy is exact state + district + type + year, then state + type + year, then state + all residential + year. Any fallback is disclosed. An unsupported state/year returns no result.

## Official publication workbooks

All 16 NAPIC Q1 2026 state publication XLSX files were downloaded locally and processed by `NapicExcelImporter`. The importer found compatible residential count/value sheets and extracted 2,749 technically valid comparison rows with no rejected rows. These publication workbooks remain Git-excluded and are not used in the committed model because the portal and files state copyright reserved and no compatible redistribution/model-use licence was found. The reproducible URL/checksum list is `data/external/napic/publication_manifest.json`.

No Q2 or Q4 value was invented or derived from a cumulative report.

## Reproduction

```powershell
python scripts/download_napic_open_transactions.py --output-dir data/raw/napic_open_transactions_YYYYMMDD
python scripts/process_napic_aggregate_transactions.py --raw-dir data/raw/napic_open_transactions_YYYYMMDD
python scripts/train_aggregate_model.py
```

For local publication inspection only:

```powershell
python scripts/download_napic_publication_tables.py
```
