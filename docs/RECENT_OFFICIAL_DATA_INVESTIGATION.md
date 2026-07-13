# Recent Official Data Investigation

Investigation date: 13 July 2026

## Outcome

The newest official period found is **2026 Q1P**. NAPIC publishes Q1 2026 transaction workbooks for Malaysia and every state/federal territory, a Q1 2026 residential-price workbook, and MHPI Q1 2026P. Direct transaction tables are published in Q1 and Q3; Q2 and Q4 must be taken from half-year and annual reports. No half-year or annual total was divided into artificial quarters.

All 16 Q1 2026 state/federal-territory workbooks were downloaded locally, hashed, and validated with the same configurable Excel importer. The importer mapped 2,749 residential count/value comparison rows with no layout rejections. The workbooks were **not integrated into the committed model**: their files and portal state copyright reserved and do not provide terms covering model training, derived models, redistribution, or public predictions. Technical availability is not permission.

Therefore:

- newest aggregate period officially investigated: 2026 Q1P;
- newest aggregate period legally integrated: 2026 Q1 from the separately licensed open transaction feed;
- licensed aggregate coverage: all 16 jurisdictions, 129 published district labels, 2021-2026 Q1;
- publication-workbook rows integrated: none; and
- unsupported quarters fabricated: none.

## Separate open individual transaction feed

NAPIC's **Data Transaksi Terbuka** is a different source product. NAPIC's Q3 2023 media release describes it as an implementation aligned with the Government Public Sector Open Data initiative. The public Tableau view provides structured completed residential transactions, and Malaysian Government Open Data Terms of Use 1.0 permit reuse subject to attribution and exclusions. This evidence chain supports the separate individual-property pipeline; it does not grant rights to the copyright-reserved publication workbooks above.

The validated July 2026 snapshot contains 416,627 records across all 16 jurisdictions, 129 published district labels, 11 residential categories, and transaction months from January 2021 through March 2026. Raw CSVs remain ignored because they total tens of megabytes; collection is reproducible through `scripts/download_napic_open_transactions.py`, and hashes/coverage are stored in local raw metadata.

## Official references

- NAPIC latest publications: https://napic.jpph.gov.my/en/latest-publication
- NAPIC transaction archive and Q1/Q3 cadence: https://napic.jpph.gov.my/en/archives/jadual-data-transaksi-harta-tanah
- NAPIC open transaction page: https://napic.jpph.gov.my/ms/data-transaksi?category=36&id=241
- Open transaction Tableau export: https://public.tableau.com/views/NewPublishOpenDataMei2024/Dashboard1.csv?:showVizHome=no
- Q3 2023 NAPIC media release: https://napic2.jpph.gov.my/storage/app/media//1-mengenai/document/media/2023/15Nov2023%20Siaran%20Media%20Pasaran%20Harta%20Tanah%20Q3%202023-FINAL%2014.11.pdf
- Malaysian Government Open Data Terms of Use 1.0: https://www.mot.gov.my/my/Documents/Terms%20of%20Use%20Government%20Open%20Data%201.0.pdf

## Remaining legal action

To extend the aggregate explorer with the 2019-2026 publication workbooks, obtain written NAPIC/JPPH permission or a published compatible licence covering extraction, model training, derived artefacts, redistribution, and public predictions.
