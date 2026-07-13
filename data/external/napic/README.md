# JPPH/NAPIC historical average house prices

Downloaded on 13 July 2026 from Malaysia's archived government open-data
catalogue. The catalogue identifies all six datasets as **Creative Commons
Attribution** and their publisher as Jabatan Penilaian dan Perkhidmatan Harta
(JPPH).

These workbooks contain aggregated average prices, not individual property
transactions. The deployed model uses the four state-level workbooks. The
district workbook is retained for future documented analysis and is not used
by model version `official-historical-average-ridge-v1`.

| Local file | Government dataset |
| --- | --- |
| `all_houses_by_state.xlsx` | [Harga Rumah Mengikut Negeri](https://archive.data.gov.my/data/en_US/dataset/harga-rumah-mengikut-negeri) |
| `terraced_by_state.xlsx` | [Harga Rumah Teres Mengikut Negeri](https://archive.data.gov.my/data/en_US/dataset/harga-rumah-teres-mengikut-negeri) |
| `semi_detached_by_state.xlsx` | [Harga Rumah Berkembar Mengikut Negeri](https://archive.data.gov.my/data/en_US/dataset/harga-rumah-berkembar-mengikut-negeri) |
| `detached_by_state.xlsx` | [Harga Rumah Sesebuah Mengikut Negeri](https://archive.data.gov.my/data/en_US/dataset/harga-rumah-sesebuah-mengikut-negeri) |
| `terraced_by_district.xlsx` | [Harga Rumah Teres Mengikut Daerah/Wilayah/Negeri](https://archive.data.gov.my/data/en_US/dataset/harga-rumah-teres-mengikut-daerahwilayahnegeri) |
| `highrise_by_district.xlsx` | [Harga Unit Bertingkat Tinggi Mengikut Daerah/Wilayah](https://archive.data.gov.my/data/en_US/dataset/harga-unit-bertingkat-tinggi-mengikut-daerah-wilayah) |

SHA-256 checksums:

```text
4F492C97174EF4D437B9785EDE7B290A9020FE55D51292C0A3B3AEDE69E1F371  all_houses_by_state.xlsx
69356B54646EA72C8003EA3976FF9AE806554D0857CB1D14E1FFF35C3B685CBC  detached_by_state.xlsx
15A8221EBC893E15A97C900E267527A4E4CB534FDAFE460939832B2FC8D84348  highrise_by_district.xlsx
D1D7BD5DEF67852C28B918A7BBAEFAC6A2D67F87F9E69B35658A40090C979333  semi_detached_by_state.xlsx
F11676CE57B97B5434691B19055EC3F881F69EEBB28B2BD5DF91BE1E3991F24B  terraced_by_district.xlsx
04E2EE7CC28BA5E9666BD485B4FCA90D2BBDF67E17F8E428077C2CEB558CD183  terraced_by_state.xlsx
```

Attribution: Jabatan Penilaian dan Perkhidmatan Harta (JPPH), Malaysia.
No endorsement by JPPH or NAPIC is implied.

## Current NAPIC publication tables

`scripts/download_napic_publication_tables.py` downloads the 16 Q1 2026 state and federal-territory transaction workbooks to `data/external/napic/2026/`. That directory is Git-ignored. The tracked `publication_manifest.json` records title, state, period, URL, retrieval time, file size, checksum, and licence decision for every workbook.

The portal and workbooks state copyright reserved and no compatible redistribution or model-use licence was found. They are retained for local technical validation only and are not the source of the committed aggregate dataset or model. The generic Excel importer successfully maps their residential count/value layouts without state-specific code.
