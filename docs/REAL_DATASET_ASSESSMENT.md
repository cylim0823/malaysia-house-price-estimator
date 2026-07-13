# Real Dataset Assessment

Assessment date: 13 July 2026

## Decision

No candidate met every approval rule for a property-level Malaysian residential estimator. Five historic JPPH workbooks were nevertheless approved for a limited aggregate prototype because Malaysia's government open-data catalogue explicitly marks them Creative Commons Attribution. The published application now estimates historical quarterly state/property-type averages only. No restricted portal was scraped, no uploader licence was treated as permission over third-party source data, and no individual-property accuracy claim is made.

| Candidate | Publisher / provenance | Access and licence evidence | Price type and coverage | Decision |
| --- | --- | --- | --- | --- |
| NAPIC Open Sales Data | National Property Information Centre / JPPH | Public embedded application; page states copyright reserved and does not expose a reusable structured download licence, complete field dictionary, or derived-model terms | Residential, commercial, and industrial transaction data; detailed coverage not confirmed | Not approved; permission and structured export terms required |
| Historic JPPH average-price workbooks | JPPH and Malaysia open-data archive | Government catalogue explicitly identifies five selected datasets as Creative Commons Attribution | 2,090 normalized quarterly state/property-type average observations, 2009 Q1-2018 Q2 | Approved and used for the limited historical-average prototype; unsuitable for individual-property training |
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
- Kaggle/Hugging Face dataset card and stated scraped provenance: https://huggingface.co/datasets/jienweng/housing-prices-malaysia-2025/blob/main/README.md
- Kaggle dataset mirror metadata: https://baselight.app/u/kaggle/dataset/tanshihjen_malaysia_property_for_sale

## Required path to a real model

The historical aggregate model is complete. To build the intended individual-property estimator, obtain written NAPIC/JPPH terms or another original-publisher licence covering property-level structured access, machine-learning training, derived model publication, public predictions, retention, and redistribution. The first authorised sample must then be reconciled against the canonical schema.
