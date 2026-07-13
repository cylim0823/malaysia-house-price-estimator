# Real Dataset Assessment

Assessment date: 13 July 2026

## Decision

NAPIC/JPPH's **Data Transaksi Terbuka** public Tableau feed is approved as a separate real completed-transaction source. Official launch material connects this product to the Government Public Sector Open Data initiative, and Malaysian Government Open Data Terms of Use 1.0 permit reuse with attribution. The validated July 2026 snapshot contains 416,627 residential transactions across all 16 jurisdictions and 129 districts from January 2021 through March 2026. No restricted listing portal was scraped.

The licensed NAPIC open transaction feed now also powers the derived nationwide aggregate explorer. Combined with preserved licensed 2017 source history, the release has 15,216 groups representing 428,443 transactions. Current NAPIC publication workbooks remain a different legal category: all 16 Q1 2026 files were inspected but state copyright reserved and were not integrated.

| Candidate | Publisher / provenance | Access and licence evidence | Price type and coverage | Decision |
| --- | --- | --- | --- | --- |
| NAPIC Data Transaksi Terbuka | NAPIC/JPPH official public Tableau view | Official launch aligns it with government public open data; Malaysian Government Open Data Terms of Use 1.0 permits reuse with attribution | 416,627 completed residential transactions, all 16 jurisdictions, 129 districts, 11 types, 2021-01 to 2026-03 | Approved for separate property-level training; raw snapshots remain out of Git because of size |
| NAPIC current publication XLSX files | National Property Information Centre / JPPH | Publicly downloadable but marked copyright reserved with no model/redistribution licence | Aggregate transaction and price tables through 2026 Q1P | Not approved; written permission required |
| Historic JPPH average-price workbooks | JPPH and Malaysia open-data archive | Government catalogue explicitly identifies five selected datasets as Creative Commons Attribution | 2,090 normalized quarterly state/property-type average observations, 2009 Q1-2018 Q2 | Approved and used for the limited historical-average prototype; unsuitable for individual-property training |
| JPPH terraced prices by district/region | JPPH and Malaysia open-data archive | Explicitly marked Creative Commons Attribution | 460 quarterly averages, 46 selected areas in 14 states/territories, 2016 Q1-2018 Q2 | Approved for local regional terraced benchmarks; no other property types or individual records |
| Penang residential transaction counts and values | Penang State Government and Malaysia open-data archive | Both datasets are explicitly marked Creative Commons Attribution | 212 joined 2017 quarter/property-type/district averages across all five Penang districts, representing 11,816 completed transactions | Approved for a validated aggregate explorer and provisional weighted baseline; not town/project/property-level data |
| data.gov.my catalogue | Government of Malaysia | Catalogue and its listed open datasets use CC BY 4.0; current catalogue contains supporting socioeconomic data but no suitable detailed residential price dataset | Supporting/aggregate coverage | Legally open but not sufficient for the estimator target |
| House Prices in Malaysia (2025) | Kaggle/Hugging Face uploader; README says data was scraped from iProperty and derived from Brickz | Uploader marks dataset MIT, but no evidence shows that iProperty/Brickz authorised scraping, redistribution, or relicensing | 2,000 aggregate township/project median rows; purported transaction medians | Rejected because original-source rights are unverified and iProperty scraping is prohibited by project policy |
| Malaysia Property For Sale/Invest | Kaggle uploader `tanshihjen`; mirrored by Baselight | Mirror reports Apache-2.0, but identifies only the Kaggle uploader and provides no original collection provenance or source permission | 1,250 asking-price rows; seven fields | Rejected because provenance and original-source rights are not established |
| University/research transaction studies | Individual research papers | Papers describe study data but do not provide a clearly licensed, automatically downloadable property-level dataset | Usually local, limited research samples | Not usable without the authors' dataset and reuse permission |

## Evidence reviewed

- NAPIC Open Sales Data: https://napic.jpph.gov.my/en/open-sales-data
- NAPIC property publications: https://napic.jpph.gov.my/en/archives/pasaran-harta-tanah
- NAPIC time-series data: https://napic.jpph.gov.my/en/time-series-data
- data.gov.my catalogue inventory and CC BY 4.0 licence: https://data.gov.my/data-catalogue/datasets
- Historic JPPH open-data publisher page: https://archive.data.gov.my/data/en_US/organization/jabatan-penilaian-dan-perkhidmatan-harta-jpph?res_format=XLS
- Penang residential counts: https://archive.data.gov.my/data/en_US/dataset/pecahan-bilangan-pindah-milik-harta-kediaman-mengikut-jenis-dan-daerah-di-pulau-pinang
- Penang residential values: https://archive.data.gov.my/data/en_US/dataset/pecahan-bilangan-pindah-milik-harta-kediaman-mengikut-jenis-dan-daerah-rm-juta-di-pulau-pinang
- Kaggle/Hugging Face dataset card and stated scraped provenance: https://huggingface.co/datasets/jienweng/housing-prices-malaysia-2025/blob/main/README.md
- Kaggle dataset mirror metadata: https://baselight.app/u/kaggle/dataset/tanshihjen_malaysia_property_for_sale

## Current model decision

The real property model is active only for state/district/property-type combinations with at least 30 published records. It uses areas, tenure, and unit level when available. The feed has no bedrooms, bathrooms, car parks, furnishing, age, condition, stable transaction ID, or coordinates; those remain explicit limitations. The untouched 2025 Q4-2026 Q1 test MAE is RM127,910.56 and must not be described as uniform accuracy across locations or price bands.
