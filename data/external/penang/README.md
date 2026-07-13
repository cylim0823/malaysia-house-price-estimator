# Penang district residential transactions (2017)

Downloaded on 13 July 2026 from Malaysia's archived government open-data
catalogue. Both datasets are published by the Penang state government and are
marked **Creative Commons Attribution**.

- [Residential transaction counts by property type and district](https://archive.data.gov.my/data/en_US/dataset/pecahan-bilangan-pindah-milik-harta-kediaman-mengikut-jenis-dan-daerah-di-pulau-pinang)
- [Residential transaction values by property type and district](https://archive.data.gov.my/data/en_US/dataset/pecahan-bilangan-pindah-milik-harta-kediaman-mengikut-jenis-dan-daerah-rm-juta-di-pulau-pinang)

The processing script divides total completed-transaction value by transaction
count for the same quarter, property type, and district. This produces an
aggregate historical average, not an individual-property record or valuation.

District labels in the source are Timur Laut, Barat Daya, Utara, Tengah, and
Selatan. The application clarifies the latter three as Seberang Perai districts
and provides geographic context for the two island districts without claiming
town-level source precision.

SHA-256 checksums:

```text
BE4DCBE8D39E6E9D2B1F49B4023765033FE81036BB52E14D01172F289F22A05F  residential_transaction_counts_2017.csv
B8FA8408C72C25901AE7444413EA659E1906DF264745AFF35E9A7C34B3446AB8  residential_transaction_values_rm_million_2017.csv
```

Attribution: Penang State Government / Malaysia Government Open Data.
