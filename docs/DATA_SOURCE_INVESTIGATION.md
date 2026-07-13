# Data Source Investigation

**Research date:** 13 July 2026  
**Status:** Two groups of aggregate government open data are approved and collected; no property-level listing or transaction source is approved.

## 1. Investigation objective

The long-term goal is a residential property-price estimator covering all Malaysian states and federal territories. Coverage must expand only where verified data, legal permission, geographic detail, and measured model performance support it.

Source quality must be established before collection code is written. A publicly visible page is not automatically licensed for bulk collection or machine-learning use, and `robots.txt` is not a substitute for terms, copyright review, or written permission. Official APIs and structured downloads should be preferred.

Asking prices and completed transaction prices measure different things. Asking prices reflect seller or agent expectations and may be duplicated, stale, or negotiable; completed transactions reflect registered sales but may be delayed or harder to obtain. They must remain separate, explicitly labelled targets.

State alone is too coarse. District, city, township, project, property type, size, tenure, and date are needed where available. Availability is unequal: urban listing markets produce more records than rural locations, while Sabah and Sarawak use administrative concepts and market structures that may not match Peninsular Malaysia exactly.

## 2. Minimum data requirements

### Essential fields

- Price
- Price type
- State or federal territory
- District
- Property type
- Built-up area or land area, as appropriate
- Stable record or source identifier
- Listing or transaction date where available

A source missing several essential fields is unsuitable as the sole property-level training source, even if it is useful for trend validation.

### Strongly recommended fields

- City
- Township
- Development or project name
- Property subtype
- Bedrooms
- Bathrooms
- Storeys
- Tenure

### Optional fields

- Furnishing
- Property age or completion year
- Latitude and longitude
- Description
- Minimal agent reference needed for provenance or deduplication

Agent, owner, and tenant names, phone numbers, personal email addresses, and other unnecessary personal information should not be collected. Descriptions should be stored only if permission and a specific deduplication or feature need are established.

## 3. Price-type definitions

| Price type | Definition | Potential modelling use |
| --- | --- | --- |
| Listing asking price | Advertised sale price before negotiation and completion | Suitable for a clearly labelled asking-price model; not market value by itself |
| Completed transaction price | Price recorded for a completed transfer or sale | Preferred market-value target when sufficiently detailed and licensed |
| Auction reserve price | Minimum or starting price announced before auction | Separate auction target or supporting feature only |
| Auction sale price | Successful price achieved at auction | Possible separate transaction target; do not mix with ordinary sales without evaluation |
| Rental price | Periodic payment for tenancy | Not suitable for the residential sale-price model |
| Median price | Middle price in an aggregated group | Useful baseline and validation statistic, not an individual record target |
| Average price | Arithmetic mean in an aggregated group | Useful trend statistic but sensitive to composition and outliers |
| Property price index | Relative change in a defined market basket over time | Useful for temporal validation or market-period features, not an absolute property price |

Completed transactions are the preferred target in principle. Asking-price records may be a practical first dataset only if their origin and use are permitted and the model is labelled accordingly. No price types should be combined into one target without explicit labels, separate evaluation, and a demonstrated reason.

## 4. Source comparison table

“Unclear — further review required” is used whenever current official material does not clearly authorise the intended automated or machine-learning use.

| Source | Source category | Price type | Property-level records | Geographic coverage | Geographic detail | Property coverage | Available fields | Format | Access method | Historical coverage | Update frequency | Login required | Cost | Licence | Terms reviewed | Robots reviewed | Automated collection status | Advantages | Limitations | Suitability | Recommendation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [NAPIC Open Sales Data](https://napic.jpph.gov.my/en/open-sales-data) | Government portal | Completed transaction | Partial/unknown from public page | Presented as Malaysia-wide | Public page does not expose a complete field dictionary | Residential, commercial, industrial | Public description confirms transaction data; detailed fields not documented on the page inspected | Web application/HTML | Webpage | Unknown | Unknown | Public page: no; linked systems may differ | Unclear | Copyright notice; reuse licence not stated | Public disclaimer/privacy links reviewed | [Unavailable in the research client](https://napic.jpph.gov.my/robots.txt) | Unclear — further review required | Official transaction origin | Embedded results and reuse conditions were not sufficiently documented | Medium pending clarification | Investigate further and ask NAPIC for field, export, and reuse details |
| [NAPIC/JPPH transaction tables](https://napic.jpph.gov.my/archives/jadual-data-transaksi-harta-tanah) | Government publications | Completed transaction aggregates | No/aggregated | All states and federal territories listed | State and some district/market tables depending on report | Mixed property sectors | Transaction volume/value and tabular market breakdowns; exact contents vary | Mainly PDF | Manual download | Search interface lists 2004–2026 | Q1 and Q3 tables; H1/annual reports cover other periods | No for publications | Free access | Copyright notice; no open-data licence found | Disclaimer reviewed | Unavailable | Not applicable for manual report use; automated reuse unclear | Long history, official nationwide trends | Aggregated and report-shaped; not enough individual features | High for validation, low for record-level training | Use for trend and geographic validation only |
| [NAPIC residential price tables and MHPI](https://napic.jpph.gov.my/archives/harga-kediaman-sukuantahunan-terkini) | Government publications | Median/average prices and index | No | Nationwide with state/type breakdowns depending on table | Primarily national/state; selected areas may appear | Residential | Price/index period, location and house type aggregates | PDF/tables | Manual download | Search page lists 2015–2026; related publications extend further | Quarterly/yearly | No | Free access | Copyright notice; no open-data licence found | Disclaimer reviewed | Unavailable | Not applicable for manual validation; automated reuse unclear | Authoritative housing trend benchmark | Cannot train a detailed property-level model alone | High for validation | Use for baselines, drift checks, and market-period context |
| [NAPIC PRISM 2.0 e-Data](https://napic.jpph.gov.my/ms/perkhidmatan/e-data) and [English manual](https://napic.jpph.gov.my/storage/app/media/0-utama/document/e-data/Manual_Pengguna_PRISM_2.0_-_Mengurus_Perkhidmatan_Data%20_Harta%20_Tanah_NonAdmin_ENGLISH.pdf) | Government paid data service | Completed transaction; also sales status, inventory, index | Yes for transaction products | Search supports states; nationwide availability must be confirmed | State, district, town/mukim, address preview and map options | Multiple property categories | Transaction category/date, property category, state, town/mukim, district, address and other preview columns | Purchased downloadable product; exact export format not confirmed | Registration, search, purchase, download; customised request | Self-generated searches limited to previous 10 years | Availability shown in system; update schedule not documented | Yes | Paid/quoted; public students and researchers can request customised products, while self-generated bulk/single is restricted to valuers and estate agents | Product-specific licence and ML/publication rights not found in public manual | Manual and access rules reviewed | Not applicable as a scrape; use only through authorised purchase/download | Best candidate for detailed official transaction data | Cost, eligibility, fields, export format, coverage, retention and model-training rights need written confirmation | Potentially high | Request a data quotation, sample schema, coverage counts, and written use/publication terms |
| [data.gov.my catalogue](https://data.gov.my/data-catalogue) / [dataset inventory](https://data.gov.my/data-catalogue/datasets) | Government open-data portal/API | No core property transaction dataset found | No core property-level housing records found in catalogue review | Nationwide for many auxiliary datasets | Often state/district | Mostly non-property auxiliary data | Dataset-specific; includes district population, income, schools, health, transport and other context | CSV, Parquet, JSON API | Direct download and documented API | Dataset-specific | Dataset-specific | No for downloads/API | Free | Catalogue datasets state licences individually; many inspected entries are CC BY 4.0 | Yes | Not applicable for official API/download | Permitted through documented download/API subject to dataset licence | Structured, documented, reusable auxiliary data | No identified detailed residential sale-price target | Medium as auxiliary; unsuitable alone | Use approved datasets for context and validation, not as the core target |
| [OpenDOSM district population](https://open.dosm.gov.my/data-catalogue/population_district) | Government downloadable dataset/API | None | No | Nationwide | 160 administrative districts including state-level treatment for Perlis and federal territories without subdivisions | Demographic | State, district, year, sex, age, ethnicity, population | CSV, Parquet, API | Direct download/API | 2020–2025 page metadata (description text mentions 2020–2024) | Annual | No | Free | Open-data portal licence applies; verify dataset page at use time | Yes | Not applicable | Permitted via official download/API subject to attribution | Canonical district vocabulary and socioeconomic context | No prices or property records; temporal mismatch possible | Medium as auxiliary | Use for location checks, coverage denominators, and later context features |
| [Sarawak Data](https://data.sarawak.gov.my/) | State government open-data portal | No core property price dataset found | No in reviewed highlights | Sarawak | District for some demographic data | Mixed government statistics | Population and socioeconomic indicators among highlighted datasets | Various, including documents and downloads | Portal/manual download | Dataset-specific; highlighted population series includes 2010–2020 projections | Dataset-specific/unknown | No for browsing; dataset-specific | Generally free/unclear by dataset | Dataset-specific; verify before reuse | Portal reviewed | Not applicable for approved downloads; otherwise unclear | Official East Malaysia auxiliary source | No confirmed detailed transaction target; some material is old or document-only | Low for core training, medium auxiliary | Search dataset-by-dataset; use only with explicit licence |
| [PropertyGuru Malaysia](https://www.propertyguru.com.my/) and [terms](https://www.propertyguru.com.my/customer-service/terms-of-service) | Listing portal | Asking, rental, new launch | Yes on visible listings | Broad Malaysia coverage | State, locality/project and maps; exact completeness varies | Residential and commercial, sale and rent | Asking price, property type, size, beds/baths and location commonly visible; listing-specific completeness | HTML with JavaScript-dependent components | Public webpage; account used for some user features | Live listings; historical availability unknown | Continuous/unknown | Browsing generally no; some features yes | Free browsing; commercial products exist | Copyright/third-party-content terms; no open bulk-training licence found | Yes | [File returned without readable directives](https://www.propertyguru.com.my/robots.txt) | Unclear — further review required | Large, detailed asking-price inventory | Duplicates, stale listings, missing dates, JS, copyright and no confirmed public bulk API/download | Potentially high technically, low until permission | Request written permission/data partnership; manual sampling only after confirmation |
| [iProperty Malaysia](https://www.iproperty.com.my/) and [terms](https://www.iproperty.com.my/terms-of-use) | Listing portal | Asking, auction, rental, new launch | Yes on visible listings | Broad Malaysia coverage | State, locality/project; listing-dependent | Residential/commercial | Asking price, location, project, type, size, beds/baths and tenure/furnishing where supplied | HTML/JavaScript; licensed API mentioned in terms | Public webpage; API only within issued scope | Live listings; historical availability unknown | Continuous/unknown | Browsing generally no; account for some features | Free browsing; API/commercial access unclear | Terms prohibit automated access, scraping/indexing, and building a property database without specific authorisation | Yes | [File returned without readable directives](https://www.iproperty.com.my/robots.txt) | **Prohibited without specific written authorisation** | Rich asking-price fields and wide coverage | Explicit automated/database restrictions, duplicates, stale records, no open dataset | Unsuitable without permission | Do not scrape; request a licensed API/data agreement if pursued |
| [EdgeProp Malaysia](https://www.edgeprop.my/) and [terms](https://api.edgeprop.my/terms-and-conditions) | Listing portal and analytics | Asking plus analytics derived from market data | Yes for listings; analytics may be aggregated | Broad Malaysia coverage | Location/project and some analytics | Residential/commercial | Price, location/project, type, size and listing attributes; analytics vary | HTML/JavaScript | Public webpage; some data access depends on user category | Live listings; analytics period varies | Unknown | Browsing generally no; enhanced access may require account | Free browsing/limited; paid categories possible | Terms protect listings/data compilations and restrict analytics to personal/internal use; no clear bulk ML permission found | Yes | [Unavailable](https://www.edgeprop.my/robots.txt) | Unclear — further review required | Listings plus market analytics and transaction context | Automated access not clearly authorised; analytics redistribution/use limited; duplicate risk | Low until permission | Ask for written permission or partnership; use published aggregates only within terms |
| [Mudah.my](https://www.mudah.my/) and [terms](https://www.mudah.my/about/terms-of-service/) | General listing marketplace | Asking, rental | Yes | Nationwide marketplace | State/locality; detail varies substantially by advert | Mixed; property sale/rent among many categories | User-entered price, location, type, size and other attributes when supplied | HTML/JavaScript | Public webpage; posting requires account | Live/expired advertisements; history unavailable | Continuous/unknown | No for browsing; yes for posting/contact features | Free browsing | Terms restrict reproduction, databases and spidering/scraping without prior written permission | Yes | [File returned without useful readable directives](https://www.mudah.my/robots.txt) | **Prohibited without prior written permission** | Potential owner and agent listings across regions | Variable quality, mixed categories, duplicates, personal information, explicit restrictions | Unsuitable without permission | Do not scrape; consider only a written data agreement |
| [MyGeoportal UPI](https://www.mygeoportal.gov.my/en/unique-parcel-identifier-upi) | Official geographic reference | None | No property prices | All 16 states/federal territories listed | State, district/division, subdistrict, town/land/village/section codes and names | Administrative geography | Canonical land administration codes and names | Excel/PDF through public UPI application | Public application/manual download | Documents published 2011 and 2023 | Irregular | No | Free public lookup/download | Spatial-data release remains provider-controlled; attribution/reuse terms need confirmation | FAQ and policy reviewed | Not applicable for manual downloads | Permitted public lookup/download; downstream licence unclear | Strong official vocabulary across Malaysia | No prices, postcodes, or open parcel records; spatial files require application | High for canonical names | Use Excel names/codes after licence confirmation; preserve source version |
| [MyGeoportal MyGeomap MapServer](https://mygos.mygeoportal.gov.my/gisserver/rest/services/MyGeomap/Msia_Coverage/MapServer) | Official geographic map service | None | No property prices | Peninsular Malaysia plus Sabah/Sarawak layers | State, district/jajahan, mukim, precinct, section, division | Administrative geography | Geometry and boundary-layer attributes | ArcGIS REST; JSON, GeoJSON, PBF queries supported | Map service | Current service; source vintage not clearly exposed | Unknown | No for visible service | Unclear | MyGDI release policy applies; public API visibility does not establish redistribution rights | MyGeoportal FAQ/policy reviewed | Not applicable | Unclear — further review required | Official machine-readable administrative boundaries | Licence, extraction rights, version and completeness need confirmation; formal spatial data may require application | Medium pending permission | Request reuse clarification before downloading or publishing boundaries |
| [OpenStreetMap copyright/licence](https://www.openstreetmap.org/copyright) | Open geographic dataset/API ecosystem | None | No property prices | Nationwide/global, community coverage | Roads, places, amenities, buildings and coordinates where mapped | Geographic/amenity | Coordinates, names, roads, POIs and tags | OSM XML/PBF; APIs and extracts | Download through suitable providers; editing API is not a bulk-download API | Continuously edited | Continuous | No for extracts | Free | Open Data Commons ODbL; attribution and share-alike obligations apply | Licence reviewed | Not applicable to approved extracts; follow provider limits | Permitted under ODbL and provider policy | Broad coordinates, roads and amenities | Community completeness varies; attribution/share-alike and geocoding policies matter | High for future geospatial enrichment | Use an approved extract with attribution; do not overload public services |

## 5. Official source findings

### NAPIC and JPPH

NAPIC is part of JPPH and is the central official property-market source found. Three different products must not be confused:

1. **Open Sales Data** identifies residential, commercial, and industrial transaction data, but the public page inspected did not expose a field dictionary, export mechanism, licence, history, or complete results outside its embedded application. It is promising but not yet an approved training source.
2. **Property transaction tables and market reports** cover every state and federal territory and provide a long quarterly/annual history. The archive search lists years from 2004 through 2026. These are mainly reports and aggregated tables: valuable for state/district trends, volume/value checks, and validation, but insufficient alone for a feature-rich property-level model.
3. **PRISM 2.0 e-Data** offers bulk and single transaction products, maps, and customised transaction, sales-status, inventory, and index requests. The July 2025 manual shows state, district, town/mukim, property category, date, address preview, record count, pricing, payment, and download workflows. Self-generated bulk/single products are restricted to registered valuers and estate agents; customised requests are shown for broader categories including public students and researchers. Searches cover at most the previous ten years. Exact fields, format, nationwide counts, prices, licence, model-training rights, derived-output rights, and publication constraints must be obtained from NAPIC before use.

No documented public NAPIC API was found. Official origin does not make the detailed records automatically open data.

### data.gov.my and DOSM

The official data.gov.my catalogue provides documented downloads and APIs, commonly as CSV, Parquet, and JSON, with dataset-specific metadata and licensing. The current catalogue review did not identify a detailed residential property transaction or listing dataset suitable as the primary target.

It does provide valuable supporting datasets. OpenDOSM district population is structured and nationwide; the wider catalogue includes district household income, schools, public health infrastructure, district GDP (older coverage), public transport ridership, and other socioeconomic data. These can support location validation, coverage denominators, later contextual features, and sanity checks, but not property-level price training by themselves.

### Official reports and state portals

NAPIC market reports, transaction tables, Malaysian House Price Index, residential price tables, stock, launch, and overhang publications are authoritative market evidence. Most are aggregated or report-oriented and should be used for baselines, trend comparisons, and drift monitoring.

The Sarawak Data portal was checked as an example of a state portal. It exposes demographic and socioeconomic datasets, including district population, but no current detailed property-sale dataset was confirmed in the reviewed catalogue highlights. State portals may help with regional context, but each dataset needs its own currency and licence check. No state portal should be assumed to fill a nationwide core-data gap.

## 6. Property-listing source findings

### Shared technical and data-quality issues

PropertyGuru, iProperty, EdgeProp, and Mudah display sale listings without requiring login for ordinary browsing. Listings commonly expose an asking price, location, property/development name, type, built-up or land area, bedrooms, bathrooms, and sometimes tenure and furnishing. Completeness varies by advert. Pages use modern web applications and some information is JavaScript-dependent.

Listing dates are less reliable than transaction dates: pages may show posting/update age rather than a stable original date, and historical expired listings are generally not offered as a downloadable archive. The same unit can be posted by multiple agents, reposted, edited, or advertised with slightly different prices. Project-level marketing listings can also be confused with individual subsale units. Deduplication would need project/location, size, bedrooms, bathrooms, price, text similarity, agent/source references, and time.

No open, documented public bulk-listings API or downloadable training dataset was confirmed for these four portals. Undocumented endpoints are not approved sources.

### Platform-specific status

- **PropertyGuru:** Rich visible residential sale and rental inventory with maps and detailed property pages. Its reviewed terms establish copyright and third-party content rules but did not provide clear permission for bulk ML collection. The robots response was not readable in the research client. Status: **Unclear — further review required**. Request permission before even a systematic educational sample.
- **iProperty:** The terms explicitly prohibit automated access, retrieval, scraping, indexing, and constructing a property-information database without specific authorisation. An API is mentioned, but access is governed by an issued scope and is not an open public API. Status: **prohibited without written authorisation**.
- **EdgeProp:** Listings and analytics are visible, but analytics access depends on user category and the terms limit downloaded analytics to personal/internal use with acknowledgement. No clear automated-collection licence was found, and robots could not be retrieved. Status: **Unclear — further review required**; written permission is necessary for systematic collection.
- **Mudah:** Property adverts are publicly browsable, but the terms expressly prohibit spidering/scraping and other reproduction without prior written permission. User-entered fields may be inconsistent and descriptions may contain personal information. Status: **prohibited without written permission**.

Manual sampling is not automatically allowed merely because it is manual. A very small sample may be considered only after confirming terms, copyright, storage, and research-use conditions. Large-scale collection requires a licence or written agreement.

## 7. Geographic data findings

### Canonical administrative names

MyGeoportal's public UPI application is the strongest official reference found for standard land-administration codes and names. It lists all 16 state/federal-territory units and provides Excel/PDF downloads for state, district/jajahan/division, subdistrict, town/land/village, and section/precinct concepts. It is suitable for canonical names and mapping tables once the specific download's reuse terms and version are recorded.

The MyGeoportal FAQ states that the public UPI application requires no signup, while formal spatial-data sharing is subject to application and provider approval. Public university students may apply through their dean; other public applicants may need to approach the data-provider agency.

### Boundaries and coordinates

The official MyGeomap ArcGIS service exposes state/district/mukim layers for Peninsular Malaysia and district/division layers for Sabah and Sarawak, with JSON, GeoJSON, and PBF query support. This is technically useful for point-in-polygon validation, but machine accessibility does not establish a licence to extract, redistribute, or publish the geometry. Obtain written clarification or formal access first.

OpenStreetMap is a practical open alternative for coordinates, roads, place names, and later amenity features. It requires OpenStreetMap attribution and compliance with the ODbL, including share-alike obligations where a derived database is distributed. Community completeness varies, so it should validate or enrich locations rather than override official Malaysian administrative mappings.

### Postcodes, cities, and townships

No authoritative, openly licensed, nationwide postcode-to-locality dataset was confirmed in this investigation. Postcode data should not be copied from an unlicensed web directory. A future task should ask Pos Malaysia or another authoritative provider for a licensed structured source.

City and township names do not always align cleanly with land-administration districts. Preserve the original text, store each geographic level separately, use official UPI names where applicable, and route ambiguous mappings to review rather than guessing.

### Future enhancement data

- **Population and local economics:** data.gov.my/OpenDOSM district population, household income, poverty, inequality, and selected GDP datasets.
- **Schools and hospitals:** data.gov.my has district-level education-institution and health-infrastructure aggregates. Point locations would need a separately verified source.
- **Public transport:** data.gov.my publishes Prasarana ridership and selected origin-destination datasets; station coordinates/routes need separate verification.
- **Roads, shopping, amenities, and coordinates:** OpenStreetMap may support later distance features under ODbL and provider-use policies.

These sources are secondary enhancements. They must not delay obtaining a lawful, property-level price target.

## 8. Nationwide feasibility assessment

Nationwide coverage remains a realistic **long-term objective**, but it is not currently demonstrated as a single ready-to-train dataset.

| Area | Assessment |
| --- | --- |
| Peninsular Malaysia | Official aggregated coverage is strong; property-level volume is likely concentrated in urban corridors. Detailed NAPIC e-Data counts must be requested. |
| Sabah | Official NAPIC tables exist, but district/division naming and lower listing density require separate coverage evaluation. Do not transfer Peninsular assumptions automatically. |
| Sarawak | Official NAPIC tables and a state data portal exist, but detailed property-level and rural coverage remain unconfirmed. Division/district structure needs explicit mapping. |
| Kuala Lumpur | Likely high listing and transaction density, especially high-rise, but this may create urban/high-rise bias. |
| Putrajaya | Small market and administrative special case; district-level population datasets may treat it as a single unit. Minimum sample rules are essential. |
| Labuan | Small market with likely sparse records; should remain unsupported until validated independently. |
| Urban/high-volume districts | Best candidates for initial evaluation, but duplicate agent listings and development-level repetition may inflate apparent sample size. |
| Rural/low-volume districts | Greater missingness, fewer listings, less consistent locality text, and wider property heterogeneity; predictions may need to be rejected. |

Listing volumes, official data access, and field completeness will be unequal. Landed and high-rise properties use different area concepts and market drivers. A single national model may be useful as a baseline, but regional or segment-specific models may later be necessary for East Malaysia, high-rise urban markets, landed markets, or distinct local conditions. That choice must be based on identical-split evaluation, not geography alone.

No nationwide-support claim is justified today. Actual support should be a published matrix of state × district × property type × price type, with record counts, date coverage, and validation metrics.

## 9. Recommended source strategy

### Primary training data

The most promising target is **authorised NAPIC/JPPH property-level completed transaction data**, obtained through PRISM e-Data or a customised educational/research request. Before purchase or request, obtain:

- A sample schema and data dictionary
- Counts by state, district, year, and residential property type
- Exact download format and update process
- Pricing and eligibility for a student project
- Licence for local model training
- Rules for GitHub, derived models, aggregate reports, and public predictions
- Retention, redistribution, attribution, and publication constraints

If suitable NAPIC access cannot be obtained, the fallback is a **separate asking-price dataset supplied under a written agreement** by a listing platform. It must be labelled as asking-price estimation, not completed market value.

### Official validation data

Use NAPIC transaction tables, Property Market Reports, residential price tables, MHPI, volume/value figures, stock, launch, and overhang statistics to compare state and district trends, medians, price indices, and transaction patterns. These reports validate aggregate behaviour but cannot replace property-level evaluation.

### Geographic reference data

Use MyGeoportal UPI codes/names for canonical official administrative vocabulary after confirming reuse terms. Seek approved MyGeoportal boundary access for spatial validation. Use OpenStreetMap extracts, with attribution and ODbL compliance, for roads, coordinates, place matching, and later amenities.

### Sources requiring permission

- NAPIC PRISM e-Data: purchase/request terms and ML/public-output rights
- NAPIC Open Sales Data: export, fields, history, and reuse terms
- PropertyGuru: systematic collection and model-training permission
- iProperty: licensed API/data access; scraping is explicitly restricted
- EdgeProp: systematic listing/analytics use
- Mudah: prior written permission; scraping is explicitly restricted
- MyGeoportal spatial boundaries: extraction, redistribution, and attribution terms
- An authoritative nationwide postcode dataset

### Sources to avoid

- iProperty or Mudah scraping without written permission
- Login-, CAPTCHA-, paywall-, or anti-bot bypasses
- Undocumented/private APIs or copied browser endpoints
- Aggregated reports as if they were individual-property training records
- Rental-only data for a sale-price target
- Auction reserves mixed with ordinary completed sales
- Unlicensed postcode or map compilations
- Old, unattributed, or unverifiable third-party datasets
- Any listing dataset containing unnecessary personal information

## 10. Recommended first dataset scope

Do not select a state merely because it is convenient. First obtain a legal source and request a coverage matrix. Then select a multi-region sample using evidence:

1. Include several states/federal territories with sufficient verified records rather than treating Selangor as the MVP.
2. If counts permit, include at least one East Malaysia urban market (for example a sufficiently represented district in Sabah or Sarawak) alongside several Peninsular markets.
3. Begin with residential sales only.
4. Keep completed transactions and asking-price records in separate datasets and experiments.
5. Separate high-rise strata properties from landed properties initially because built-up and land-area meanings differ.
6. Require a provisional minimum of **at least 500 usable, deduplicated records per district-property segment**, with **at least 100 later-period records reserved for testing**. These are starting thresholds, not proof of adequacy; revise them after learning-curve and error analysis.
7. Require sufficient temporal spread for time-based evaluation. Exclude or mark unsupported any segment that cannot meet the threshold or a stable baseline.
8. Include both high-volume and moderate-volume districts in validation so the model is not evaluated only on major urban centres.

The exact first states cannot responsibly be named until NAPIC or an authorised provider supplies counts and fields. This evidence-based gate protects the nationwide goal from becoming an unsupported marketing claim.

## 11. Risks

- Unclear scraping permission and changing terms
- Copyright, database, licence, and derived-model restrictions
- Duplicate listings and the same unit advertised by multiple agents
- Expired, reposted, or stale listings
- Asking-price inflation and negotiation gaps
- Missing or unreliable listing/transaction dates
- Missing or ambiguous district information
- Incorrect sizes and mixed square-foot/square-metre units
- Urban and high-rise bias
- Weak Sabah, Sarawak, Labuan, Putrajaya, and rural coverage
- Different administrative vocabulary across regions
- Website layout and dynamic JavaScript changes
- Data-source shutdown or loss of historical access
- Personal information embedded in descriptions
- Large storage, versioning, and refresh requirements
- Delayed official transaction reporting
- Licence terms that permit private research but prohibit redistribution or public prediction services

## 12. Open questions for the project owner

1. Should the project apply to NAPIC for a customised student/research transaction extract and accept possible fees or institutional paperwork?
2. If detailed transaction data is unavailable, should the first model explicitly target asking prices under a licensed platform agreement?
3. Should permission be requested from one or more listing platforms, and who will send or sign that request?
4. Should the first modelling dataset cover high-rise, landed, or both as separately evaluated segments?
5. May restrictively licensed data be used in a private local project if neither records nor derived artefacts can be published?
6. Should raw listing descriptions be excluded unless they are essential for deduplication and expressly licensed?
7. How much manual verification can the owner perform for an initial sample and duplicate groups?

## 13. Recommended next phase

Proceed to **Phase 2 — Canonical data schema** while contacting NAPIC for a sample schema, coverage counts, pricing, and written usage terms. The schema can define price types, provenance, Malaysian administrative levels, units, validation states, and duplicate groups without collecting records.

A small manually verified sample dataset should follow only after a source is approved. Do not implement a large-scale scraper unless automated collection is explicitly permitted.

## References reviewed

All links below were accessed on 13 July 2026.

### Property and official statistics

- [NAPIC official portal](https://napic.jpph.gov.my/en/)
- [NAPIC Open Sales Data](https://napic.jpph.gov.my/en/open-sales-data)
- [NAPIC transaction-table archive](https://napic.jpph.gov.my/archives/jadual-data-transaksi-harta-tanah)
- [NAPIC residential price tables](https://napic.jpph.gov.my/archives/harga-kediaman-sukuantahunan-terkini)
- [NAPIC latest publications](https://napic.jpph.gov.my/en/latest-publication)
- [NAPIC PRISM e-Data guide](https://napic.jpph.gov.my/ms/perkhidmatan/e-data)
- [PRISM 2.0 English e-Data manual](https://napic.jpph.gov.my/storage/app/media/0-utama/document/e-data/Manual_Pengguna_PRISM_2.0_-_Mengurus_Perkhidmatan_Data%20_Harta%20_Tanah_NonAdmin_ENGLISH.pdf)
- [data.gov.my catalogue](https://data.gov.my/data-catalogue)
- [data.gov.my dataset inventory and API example](https://data.gov.my/data-catalogue/datasets)
- [OpenDOSM district population](https://open.dosm.gov.my/data-catalogue/population_district)
- [Sarawak Data portal](https://data.sarawak.gov.my/)

### Listing platforms and policies

- [PropertyGuru Malaysia](https://www.propertyguru.com.my/)
- [PropertyGuru terms of service](https://www.propertyguru.com.my/customer-service/terms-of-service)
- [PropertyGuru robots.txt](https://www.propertyguru.com.my/robots.txt)
- [iProperty Malaysia](https://www.iproperty.com.my/)
- [iProperty terms of use](https://www.iproperty.com.my/terms-of-use)
- [iProperty robots.txt](https://www.iproperty.com.my/robots.txt)
- [EdgeProp Malaysia](https://www.edgeprop.my/)
- [EdgeProp terms and conditions](https://api.edgeprop.my/terms-and-conditions)
- [EdgeProp robots.txt](https://www.edgeprop.my/robots.txt)
- [Mudah.my](https://www.mudah.my/)
- [Mudah terms of service](https://www.mudah.my/about/terms-of-service/)
- [Mudah robots.txt](https://www.mudah.my/robots.txt)

### Geographic and future-enhancement sources

- [MyGeoportal UPI](https://www.mygeoportal.gov.my/en/unique-parcel-identifier-upi)
- [MyGeoportal FAQ and access rules](https://www.mygeoportal.gov.my/en/faq)
- [MyGeoportal policies and standards](https://www.mygeoportal.gov.my/en/policies-and-standards)
- [MyGeomap administrative-boundary MapServer](https://mygos.mygeoportal.gov.my/gisserver/rest/services/MyGeomap/Msia_Coverage/MapServer)
- [OpenStreetMap copyright and ODbL requirements](https://www.openstreetmap.org/copyright)

## Approved aggregate additions — 13 July 2026

The Malaysia government open-data catalogue explicitly marks two Penang 2017
residential datasets Creative Commons Attribution: transaction counts and
transaction values by quarter, property type, and five districts. They were
downloaded directly as CSV and joined only on identical source keys. Dividing
value by count produces 212 completed-transaction averages. This supports a
district benchmark but not town, project, street, or individual-property
training.

- [Penang transaction counts](https://archive.data.gov.my/data/en_US/dataset/pecahan-bilangan-pindah-milik-harta-kediaman-mengikut-jenis-dan-daerah-di-pulau-pinang)
- [Penang transaction values](https://archive.data.gov.my/data/en_US/dataset/pecahan-bilangan-pindah-milik-harta-kediaman-mengikut-jenis-dan-daerah-rm-juta-di-pulau-pinang)

The user later allowed collection in principle, but permission from the project
owner does not grant rights over third-party listing content. Manual copying is
not used to circumvent unclear automated-collection or machine-learning terms.
