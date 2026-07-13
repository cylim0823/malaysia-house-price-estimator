# Canonical Property Data Schema

**Status:** Proposed schema design only. No source is approved, no records have been collected, and no implementation currently enforces this schema.

## 1. Purpose

Every future approved source should be converted into one canonical property-record schema so validation, deduplication, analysis, and modelling have consistent meanings. Source-specific fields may be retained, but they must not silently redefine canonical fields.

Raw values must remain available because parsing and mapping rules can be wrong or change later. Asking prices, completed transaction prices, auction prices, rental prices, and aggregates must remain distinguishable: they describe different events and cannot safely share an unlabelled target. Malaysian state, district, city, township, project, and address fields must also remain separate because they represent different geographic concepts.

Designing the schema before collection or cleaning code prevents each importer from inventing incompatible names, missing-value conventions, or price meanings. The design supports all Malaysian states and federal territories even while early approved data may cover only a subset. Schema support does not imply current data or prediction coverage.

## 2. Schema principles

1. Raw records must never be modified in place.
2. Raw and cleaned values must be stored separately where appropriate.
3. Every record must retain source and collection provenance.
4. Asking, transaction, auction, and rental prices must not be confused.
5. Rental records are outside the initial residential sale-price model.
6. State, district, city, township, project, and address are different concepts.
7. Missing information must not be fabricated.
8. Invalid or suspicious records must be preserved with validation reasons.
9. Duplicate records must be grouped before train, validation, and test splitting.
10. Outliers must be investigated rather than automatically deleted.
11. Every processed dataset must have a schema version and dataset version.
12. Unsupported or uncertain location mappings must be flagged for review.

## 3. Data layers

### Raw layer

The raw layer preserves imported source values and source payloads without correction. Examples include `RM 650k`, `1,800 sq.ft.`, `4+1`, `Semenyih/Kajang`, and `Freehold / Bumi Lot`. A collection timestamp and source identity accompany each record. Raw source files or payloads are immutable and versioned.

### Interim layer

The interim layer contains parsed and partially standardised values while preserving uncertainty. For example, `RM 650k` may yield a candidate numeric price of `650000`, while `Semenyih/Kajang` remains flagged as an ambiguous locality rather than being forced into a district.

### Processed layer

The processed layer contains validated, normalised, deduplicated fields suitable for analysis and possible model preparation. A processed record remains linked to its raw record, transformations, warnings, and duplicate group.

These layers are designs only. Storage and transformation pipelines will be implemented in later tasks.

## 4. Canonical property record

Types described as nullable allow a true null value. Required levels are schema expectations, not permission to fabricate a value. “Required” means a conforming usable record needs the field; source records lacking it remain traceable but may be model-ineligible.

### Record identity and provenance

| Field name | Data type | Required level | Data layer | Description | Example | Validation rules | Missing-value handling | Model usage | Privacy notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `record_id` | string | system-generated | multiple | Stable canonical record identifier | `rec_01J...` | Globally unique; never reused | Never null after ingestion | metadata | Must not encode personal data |
| `source_name` | string | required | multiple | Approved source name | `napic_edata` | Controlled source registry | Null makes record invalid | metadata | None |
| `source_type` | enum | required | multiple | Origin class | `government_transaction` | Controlled vocabulary | Null makes record invalid | metadata | None |
| `source_record_id` | nullable string | strongly recommended | multiple | Identifier assigned by source | `JH-2025-001234` | Preserve exactly; unique only within source if documented | Null if source supplies none | metadata/deduplication | Must not be a personal identifier |
| `source_url` | nullable string | optional | raw/metadata | Permitted record or dataset URL | `https://example.gov.my/dataset` | Valid URL; respect licence | Null if unavailable or prohibited | excluded | Remove tokens and private URLs |
| `source_file` | nullable string | optional | raw/metadata | Source filename or object key | `transactions_2025_q1.xlsx` | Safe relative/object identifier; no secret path | Null for non-file source | metadata | No personal local paths |
| `source_price_type` | nullable string | strongly recommended | raw/interim | Source's original price label | `Consideration` | Preserve source wording | Null if absent; warning | validation-only | None |
| `collected_at` | datetime | required | multiple | Import/collection time | `2026-07-13T03:15:00Z` | Timezone-aware; preferably UTC | Null makes provenance invalid | metadata | None |
| `source_published_at` | nullable datetime | optional | raw/interim | Source publication time | `2026-04-15T00:00:00+08:00` | Do not confuse with market-event date | Null if unknown | metadata | None |
| `source_updated_at` | nullable datetime | optional | raw/interim | Source update time | `2026-04-20T09:30:00+08:00` | Must be source-supplied | Null if unknown | metadata | None |
| `source_terms_version` | nullable string | strongly recommended | metadata | Terms version/date governing access | `terms_accessed_2026-07-13` | Link to source registry evidence | Null only with review warning | validation-only | None |
| `source_licence` | nullable string | strongly recommended | metadata | Licence or written permission reference | `CC-BY-4.0` | Must not infer a licence | Null means legal review incomplete | validation-only | No confidential agreement text |
| `source_access_method` | enum | required | metadata | Approved acquisition route | `manual_download` | e.g. API, download, licensed export, manual entry | Null makes legal review incomplete | validation-only | None |

URLs, terms details, and licence text may be unavailable for some approved structured datasets. Their absence must be explicit and reviewed, not silently replaced.

### Dataset and schema metadata

| Field name | Data type | Required level | Data layer | Description | Example | Validation rules | Missing-value handling | Model usage | Privacy notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `schema_version` | string | system-generated | multiple | Canonical schema version | `1.0.0` | Semantic version format | Never null in interim/processed | metadata | None |
| `dataset_version` | string | system-generated | multiple | Immutable dataset release | `2026-07-13.1` | Unique, documented build | Never null in processed | metadata | None |
| `ingestion_batch_id` | string | system-generated | multiple | Links records imported together | `batch_20260713_001` | Stable and traceable | Never null after ingestion | metadata | None |
| `processing_version` | nullable string | system-generated | interim/processed | Cleaning pipeline/rules version | `cleaning-0.1.0` | Must identify reproducible rules | Null in raw only | metadata | None |
| `processed_at` | nullable datetime | system-generated | processed | Processing completion time | `2026-07-13T04:00:00Z` | Timezone-aware | Null before processing | metadata | None |

### Price fields

Allowed `price_type` values are `asking`, `completed_transaction`, `auction_reserve`, `auction_sale`, `rental`, `aggregate_median`, `aggregate_average`, and `unknown`.

| Field name | Data type | Required level | Data layer | Description | Example | Validation rules | Missing-value handling | Model usage | Privacy notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `price_raw` | nullable string | strongly recommended | raw/interim | Original price text | `RM 650k` | Never overwrite | Null if source provides only numeric data | validation-only | None |
| `price_amount` | nullable decimal | required | interim/processed | Parsed amount in `price_currency` | `650000.00` | Positive; plausible limits flagged, not silently removed | Null if parsing fails; invalid for model | target candidate | None |
| `price_currency` | enum | required | interim/processed | ISO currency | `MYR` | Initial Malaysian records must be `MYR`; do not infer foreign conversion | Null if unknown | metadata | None |
| `price_type` | enum | required | interim/processed | Meaning of price | `asking` | Must map from evidence; never default asking to transaction | `unknown` plus warning if unresolved | target selector | None |
| `price_period` | nullable enum | optional | interim/processed | Rental period | `monthly` | Required for rental; null for sale types | Null for non-rental | excluded initially | None |
| `price_per_sqft` | nullable decimal | optional/system-generated | processed | Derived price divided by appropriate square feet | `722.22` | Record numerator/denominator rule; positive | Null if price/area unusable | target/feature only in approved experiment | None |
| `valuation_date` | nullable date | optional | interim/processed | Date to which a valuation/aggregate applies | `2025-12-31` | Must be source-defined | Null if not valuation data | validation-only | None |

The initial model may use only approved residential sale records with a clearly selected target type. Rental prices require a period and must never enter the sale-price model.

### Malaysian location fields

Valid canonical `state` values are: `Johor`, `Kedah`, `Kelantan`, `Melaka`, `Negeri Sembilan`, `Pahang`, `Penang`, `Perak`, `Perlis`, `Sabah`, `Sarawak`, `Selangor`, `Terengganu`, `Kuala Lumpur`, `Putrajaya`, and `Labuan`.

| Field name | Data type | Required level | Data layer | Description | Example | Validation rules | Missing-value handling | Model usage | Privacy notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `address_raw` | nullable string | optional | raw/interim | Original address/locality text | `Jalan Ampang, KL` | Preserve; do not publish unit-level address by default | Null if absent/restricted | validation/deduplication only initially | Remove personal/unit details when required |
| `state_raw` | nullable string | strongly recommended | raw/interim | Original state text | `W.P. Kuala Lumpur` | Preserve exactly | Null if absent | validation-only | None |
| `state` | nullable enum | required | interim/processed | Canonical state/federal territory | `Kuala Lumpur` | Must match controlled list | Null with `MISSING_STATE` | feature | None |
| `state_code` | nullable string | strongly recommended | interim/processed | Versioned official/code-system value | `14` | Store code system/version in dictionary | Null until verified | feature/metadata | None |
| `district_raw` | nullable string | strongly recommended | raw/interim | Original district/division text | `Johor Bahru` | Preserve exactly | Null if absent | validation-only | None |
| `district` | nullable string | strongly recommended | interim/processed | Canonical district/division | `Johor Bahru` | Must be valid for state and code-list version | Null if absent/ambiguous; do not guess | feature | None |
| `district_code` | nullable string | optional | interim/processed | Official district/division code | `JH01` | Validate against code system | Null until verified | feature/metadata | None |
| `city_raw` | nullable string | optional | raw/interim | Original city text | `Kuching` | Preserve exactly | Null if absent | validation-only | None |
| `city` | nullable string | optional | interim/processed | Canonical city | `Kuching` | Mapping must be evidenced | Null if ambiguous | feature | None |
| `township_raw` | nullable string | optional | raw/interim | Original township/locality | `Bandar Sunway` | Preserve exactly | Null if absent | validation-only | None |
| `township` | nullable string | optional | interim/processed | Canonical township | `Bandar Sunway` | Do not merge names without validation | Null if ambiguous | feature | None |
| `project_name_raw` | nullable string | optional | raw/interim | Original development name | `Residensi Example` | Preserve exactly | Null if absent | validation/deduplication | Remove personal unit references |
| `project_name` | nullable string | optional | interim/processed | Normalised development name | `Residensi Example` | Mapping documented; no speculative match | Null if unresolved | feature | None |
| `postcode_raw` | nullable string | optional | raw/interim | Original postcode | `50450` | Preserve leading zeros | Null if absent | validation-only | None |
| `postcode` | nullable string | optional | interim/processed | Validated five-digit Malaysian postcode | `50450` | Exactly 5 digits and approved reference when available | Null if invalid/unverified | feature | Avoid unit-address linkage in releases |
| `latitude` | nullable float | optional | interim/processed | WGS84 latitude | `3.1579` | Between -90 and 90; validate Malaysian extent separately | Null if absent/unlicensed | feature | Reduce precision if privacy requires |
| `longitude` | nullable float | optional | interim/processed | WGS84 longitude | `101.7123` | Between -180 and 180; validate Malaysian extent | Null if absent/unlicensed | feature | Reduce precision if privacy requires |
| `location_confidence` | enum | system-generated | interim/processed | Mapping confidence | `medium` | `high`, `medium`, `low`, `unverified`; evidence-based | Default `unverified`, not null | validation/feature candidate | None |
| `location_validation_status` | enum | system-generated | interim/processed | Location check result | `ambiguous` | Controlled status with notes/codes | `not_validated` before checks | validation-only | None |
| `location_validation_notes` | nullable string | optional | interim/processed | Human-readable mapping context | `Could refer to Kajang or Semenyih` | Concise; no unsupported correction | Null if no note | excluded | Remove personal data |

Kuala Lumpur, Putrajaya, and Labuan are federal territories. Perlis and some federal territories do not use district structures in the same way as other states. Sabah and Sarawak require their own validated district/division mappings; Peninsular assumptions must not be applied automatically. Original location text always remains available, and ambiguous mappings are never guessed.

### Property classification

| Field name | Data type | Required level | Data layer | Description | Example | Validation rules | Missing-value handling | Model usage | Privacy notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `property_category_raw` | nullable string | strongly recommended | raw/interim | Original broad class | `Residential` | Preserve | Null if absent | validation-only | None |
| `property_category` | enum | required | interim/processed | Canonical broad class | `residential` | Initial eligible value must be residential | `unknown` with warning | feature/filter | None |
| `property_type_raw` | nullable string | strongly recommended | raw/interim | Original property type | `2-storey terrace` | Preserve | Null if absent | validation-only | None |
| `property_type` | enum | required | interim/processed | Canonical residential type | `terrace_house` | Controlled mapping | `unknown`; model-ineligible initially | feature | None |
| `property_subtype_raw` | nullable string | optional | raw/interim | Original subtype | `intermediate unit` | Preserve | Null if absent | validation-only | None |
| `property_subtype` | nullable enum/string | optional | interim/processed | Canonical subtype | `intermediate` | Versioned vocabulary | Null if unavailable | feature | None |
| `market_segment` | nullable enum | optional | processed | Evidence-based segment | `standard` | Do not infer luxury solely from price | Null/`unknown` | feature/filter | None |
| `sale_type` | enum | required | interim/processed | Sale/rent/auction context | `sale` | Initial eligible records require `sale` | `unknown` if unclear | filter/feature | None |
| `new_or_subsale` | nullable enum | strongly recommended | interim/processed | Primary launch or resale | `subsale` | `new`, `subsale`, `unknown` | `unknown` if not evidenced | feature | None |

Initial records use `property_category = residential` and `sale_type = sale`. Proposed property types are `terrace_house`, `semi_detached_house`, `detached_house`, `bungalow`, `townhouse`, `cluster_house`, `condominium`, `apartment`, `flat`, `serviced_residence`, `studio`, `other_residential`, and `unknown`. A serviced residence must not be treated as a condominium without a documented mapping rule.

### Property dimensions

Supported source units are `sqft`, `sqm`, `acre`, `hectare`, and `unknown`.

| Field name | Data type | Required level | Data layer | Description | Example | Validation rules | Missing-value handling | Model usage | Privacy notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `built_up_area_raw` | nullable string | strongly recommended | raw/interim | Original built-up text | `1,800 sq.ft.` | Preserve | Null if absent | validation-only | None |
| `built_up_area_value` | nullable decimal | strongly recommended | interim | Parsed source-unit value | `1800.0` | Positive; parsing traceable | Null on failure | validation-only | None |
| `built_up_area_unit` | enum | strongly recommended | interim/processed | Source unit | `sqft` | Controlled unit | `unknown` if unresolved | metadata | None |
| `built_up_sqft` | nullable decimal | strongly recommended | processed | Normalised built-up area | `1800.0` | Positive; conversion version recorded | Null if no reliable conversion | feature | None |
| `land_area_raw` | nullable string | strongly recommended for landed | raw/interim | Original land-area text | `22 x 75 ft` | Preserve dimensions/text | Null if absent | validation-only | None |
| `land_area_value` | nullable decimal | strongly recommended for landed | interim | Parsed source-unit area | `1650.0` | Must be actual area or documented derived area | Null on failure | validation-only | None |
| `land_area_unit` | enum | strongly recommended for landed | interim/processed | Source unit | `sqft` | Controlled unit | `unknown` if unresolved | metadata | None |
| `land_area_sqft` | nullable decimal | strongly recommended for landed | processed | Normalised land area | `1650.0` | Positive; conversion version recorded | Null if absent/unreliable, never zero | feature | None |
| `area_validation_status` | enum | system-generated | interim/processed | Area validity | `valid_with_warnings` | Controlled status | `not_validated` before checks | validation-only | None |
| `area_validation_notes` | nullable string | optional | interim/processed | Area issue explanation | `Possible sqm labelled as sqft` | Document evidence | Null if none | excluded | None |

Expected conversions include 1 sqm ≈ 10.7639 sqft, 1 acre = 43,560 sqft, and 1 hectare ≈ 107,639.104 sqft; the future implementation must use tested, documented constants. High-rise properties may have no meaningful private land area. Landed properties may require both built-up and land area. Zero/negative values are invalid; extreme values are flagged, not automatically deleted.

### Rooms and structure

| Field name | Data type | Required level | Data layer | Description | Example | Validation rules | Missing-value handling | Model usage | Privacy notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `bedrooms_raw` | nullable string | strongly recommended | raw/interim | Original bedroom value | `4+1` | Preserve | Null if absent | validation-only | None |
| `bedrooms` | nullable integer | strongly recommended | interim/processed | Main bedrooms | `4` | Non-negative; no helper-room inflation | Null if unresolved | feature | None |
| `bedrooms_additional` | nullable integer | optional | interim/processed | Additional/helper rooms | `1` | Non-negative; keep separate | Null if not stated | feature candidate | None |
| `bathrooms_raw` | nullable string | strongly recommended | raw/interim | Original bathroom value | `3+1` | Preserve | Null if absent | validation-only | None |
| `bathrooms` | nullable integer | strongly recommended | interim/processed | Main bathrooms | `3` | Non-negative | Null if unresolved | feature | None |
| `car_parks_raw` | nullable string | optional | raw/interim | Original parking text | `2 covered bays` | Preserve | Null if absent | validation-only | None |
| `car_parks` | nullable integer | optional | interim/processed | Parking spaces | `2` | Non-negative | Null if unknown | feature | None |
| `storeys_raw` | nullable string | optional | raw/interim | Original storey text | `2.5 storeys` | Preserve | Null if absent | validation-only | None |
| `storeys` | nullable decimal | optional | interim/processed | Property storeys | `2.5` | Positive; applies mainly to landed unit | Null if irrelevant/unknown | feature | None |
| `floor_level_raw` | nullable string | optional | raw/interim | Original unit floor | `High floor` | Preserve | Null if absent | validation-only | None |
| `floor_level` | nullable integer | optional | interim/processed | Numeric unit floor when exact | `28` | Integer; ground floor may map to 0 only by rule | Null for qualitative/unknown | feature | None |
| `total_building_floors` | nullable integer | optional | interim/processed | Building height in floors | `35` | Positive and ≥ floor level when both exact | Null if unknown | feature | None |

`4+1 bedrooms` becomes `bedrooms = 4`, `bedrooms_additional = 1`, while retaining `bedrooms_raw`. `3+1 bathrooms` follows the same separation if the source meaning is known. `2.5 storeys` may be stored as decimal `2.5`. `High floor` remains in `floor_level_raw` with numeric `floor_level = null` unless a source-specific documented band exists. `Ground floor` may map to 0 under a documented convention. Helper rooms are never silently counted as full bedrooms.

### Ownership and legal characteristics

| Field name | Data type | Required level | Data layer | Description | Example | Validation rules | Missing-value handling | Model usage | Privacy notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `tenure_raw` | nullable string | strongly recommended | raw/interim | Original tenure text | `Freehold / Bumi Lot` | Preserve | Null if absent | validation-only | None |
| `tenure` | enum | strongly recommended | interim/processed | `freehold`, `leasehold`, `unknown` | `freehold` | Evidence-based; do not infer | `unknown` | feature | None |
| `lease_expiry_year` | nullable integer | optional | interim/processed | Lease expiry year | `2085` | Plausible four-digit year; leasehold only | Null if unknown/not applicable | feature | None |
| `land_title_raw` | nullable string | optional | raw/interim | Original land-title text | `Residential title` | Preserve | Null if absent | validation-only | None |
| `land_title` | nullable enum/string | optional | interim/processed | Canonical land-use/title class | `residential` | Versioned vocabulary; no legal inference | `unknown`/null | feature candidate | None |
| `title_type_raw` | nullable string | optional | raw/interim | Original title type | `Strata title` | Preserve | Null if absent | validation-only | None |
| `title_type` | enum | optional | interim/processed | `individual`, `strata`, `master`, `unknown` | `strata` | Evidence-based | `unknown` | feature | None |
| `lot_restriction_raw` | nullable string | optional | raw/interim | Original restriction text | `Bumi Lot` | Preserve | Null if absent | validation-only | Avoid owner identity |
| `lot_restriction` | enum | optional | interim/processed | `none`, `bumi_lot`, `malay_reserved`, `other`, `unknown` | `bumi_lot` | Do not infer from incomplete marketing text | `unknown` | feature/filter subject to legal review | None |

### Property condition and characteristics

| Field name | Data type | Required level | Data layer | Description | Example | Validation rules | Missing-value handling | Model usage | Privacy notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `furnishing_raw` | nullable string | optional | raw/interim | Original furnishing text | `Partly furnished` | Preserve | Null if absent | validation-only | None |
| `furnishing` | enum | optional | interim/processed | `unfurnished`, `partially_furnished`, `fully_furnished`, `unknown` | `partially_furnished` | Document mapping | `unknown` | feature | None |
| `completion_year` | nullable integer | optional | interim/processed | Construction/completion year | `2018` | Plausible and not after record year without warning | Null if unknown | feature | None |
| `property_age_years` | nullable decimal | optional/system-generated | processed | Age at effective date | `7.0` | Derive from dates with documented precision | Null if inputs unavailable | feature | None |
| `condition_raw` | nullable string | optional | raw/interim | Original condition text | `Well maintained` | Preserve if licensed | Null if absent | validation-only | Remove personal content |
| `condition` | nullable enum/string | optional | interim/processed | Normalised condition | `good` | Subjective; source/rule required | `unknown` | feature candidate | None |
| `renovation_status_raw` | nullable string | optional | raw/interim | Original renovation text | `Newly renovated` | Preserve if licensed | Null if absent | validation-only | Remove personal content |
| `renovation_status` | nullable enum/string | optional | interim/processed | Normalised renovation status | `renovated` | Do not infer quality/cost | `unknown` | feature candidate | None |
| `occupancy_status_raw` | nullable string | optional | raw/interim | Original occupancy text | `Owner occupied` | Preserve only when allowed | Null if absent | validation-only | Avoid occupant identity |
| `occupancy_status` | nullable enum/string | optional | interim/processed | Normalised occupancy | `owner_occupied` | Controlled and non-personal | `unknown` | feature candidate | No occupant details |

Condition and renovation quality are subjective and frequently unavailable. They require documented vocabularies and should not become initial features without reliability analysis.

### Record dates

| Field name | Data type | Required level | Data layer | Description | Example | Validation rules | Missing-value handling | Model usage | Privacy notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `listing_date` | nullable date | strongly recommended for asking | interim/processed | Listing market date | `2026-06-15` | Source-derived; not collection date | Null if unavailable; model-ineligible may result | temporal feature/split | None |
| `transaction_date` | nullable date | strongly recommended for transaction | interim/processed | Completed/registered sale date | `2025-11-20` | Source-derived | Null if unavailable | temporal feature/split | None |
| `auction_date` | nullable date | strongly recommended for auction | interim/processed | Auction event date | `2026-02-10` | Source-derived | Null if unavailable | temporal feature/split | None |
| `record_effective_date` | nullable date | required for model eligibility | processed | Date selected by price meaning | `2025-11-20` | Asking→listing; transaction→transaction; auction→auction; aggregate→valuation/period | Null if no reliable event date | temporal feature/split | None |
| `date_precision` | enum | required | interim/processed | `exact_day`, `month`, `quarter`, `year`, `unknown` | `quarter` | Must reflect evidence | `unknown` | validation/temporal handling | None |

An exact date must never be fabricated from a quarter or year. A quarter/year may be represented by an agreed period anchor for storage only if precision is retained and modelling treats it accordingly.

### Listing and description fields

| Field name | Data type | Required level | Data layer | Description | Example | Validation rules | Missing-value handling | Model usage | Privacy notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `title_raw` | nullable string | optional | raw/interim | Original listing title | `Condo for sale near LRT` | Store only when licensed | Null if prohibited/absent | deduplication only initially | Redact personal data |
| `description_raw` | nullable string | optional | raw | Original description | `Corner unit...` | Store only with explicit permission/need | Null by default | excluded initially | Detect/redact names, phones, emails |
| `description_clean` | nullable string | optional | interim/processed | Permitted redacted/normalised text | `Corner unit...` | Must link to raw and redaction rules | Null if descriptions excluded | deduplication; not initial feature | Personal data removed |
| `listing_status` | nullable enum | optional | interim/processed | Listing state | `active` | e.g. active, expired, withdrawn, sold, unknown | `unknown` | validation/metadata | None |
| `listing_agent_reference` | nullable string | optional | raw/interim | Non-personal source-side agent reference | `agent_hash_abc` | Only if permitted and necessary | Null by default | deduplication only | Hash/pseudonymise; no names/contact details |

Description text is excluded unless storage is permitted and needed for deduplication or later approved work. It is not an initial ML feature.

### Duplicate handling

| Field name | Data type | Required level | Data layer | Description | Example | Validation rules | Missing-value handling | Model usage | Privacy notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `duplicate_status` | enum | system-generated | interim/processed | Duplicate state | `possible_duplicate` | `not_checked`, `unique`, `possible_duplicate`, `confirmed_duplicate`, `canonical_record` | Default `not_checked` | validation-only | None |
| `duplicate_group_id` | nullable string | system-generated | processed | Group of likely same property/event | `dup_00042` | Same group cannot cross splits | Null until grouped/unique policy | excluded | None |
| `duplicate_confidence` | nullable enum/float | system-generated | processed | Match confidence | `high` | Method/version documented | Null if not checked | validation-only | None |
| `duplicate_method` | nullable string | system-generated | processed | Rule/model version | `rules_v1` | Reproducible definition | Null if not checked | validation-only | None |
| `canonical_record_id` | nullable string | system-generated | processed | Representative record in group | `rec_01J...` | Must reference valid group member | Null for ungrouped/unique | excluded | None |

Detection may consider source ID, project, location, price, built-up/land area, rooms, listing date, description similarity, and permitted agent/source references. Duplicates are grouped first, not blindly deleted.

### Validation and rejection

| Field name | Data type | Required level | Data layer | Description | Example | Validation rules | Missing-value handling | Model usage | Privacy notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `validation_status` | enum | system-generated | interim/processed | `not_validated`, `valid`, `valid_with_warnings`, `invalid` | `valid_with_warnings` | Derived from codes/rules | Default `not_validated` | validation-only | None |
| `validation_error_codes` | list[string] | system-generated | interim/processed | Blocking errors | `["INVALID_PRICE"]` | Controlled, deduplicated codes | Empty list, not null | validation-only | None |
| `validation_warning_codes` | list[string] | system-generated | interim/processed | Non-blocking concerns | `["POSSIBLE_OUTLIER"]` | Controlled codes | Empty list, not null | validation-only | None |
| `validation_notes` | nullable string | optional | interim/processed | Review explanation | `Price token could not be parsed` | No hidden correction | Null if unnecessary | excluded | Remove personal data |
| `rejection_status` | enum | system-generated | processed | `not_rejected`, `temporarily_excluded`, `permanently_excluded` | `temporarily_excluded` | Must align with reason | Default `not_rejected` | filter | None |
| `rejection_reason` | nullable string | system-generated | processed | Documented exclusion reason | `Missing reliable target date` | Required when rejected | Null only when not rejected | validation-only | None |
| `review_required` | boolean | system-generated | interim/processed | Manual review flag | `true` | True for unresolved blocking/suspicious cases | Default false only after rules run | validation-only | None |

Initial codes include `MISSING_PRICE`, `UNKNOWN_PRICE_TYPE`, `INVALID_PRICE`, `MISSING_STATE`, `UNKNOWN_STATE`, `AMBIGUOUS_DISTRICT`, `MISSING_PROPERTY_TYPE`, `INVALID_BUILT_UP_AREA`, `INVALID_LAND_AREA`, `POSSIBLE_UNIT_ERROR`, `MISSING_RECORD_DATE`, `POSSIBLE_DUPLICATE`, `POSSIBLE_OUTLIER`, and `PERSONAL_INFORMATION_DETECTED`. Rejected records remain traceable to their raw record and reasons.

### Outlier handling

| Field name | Data type | Required level | Data layer | Description | Example | Validation rules | Missing-value handling | Model usage | Privacy notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `outlier_status` | enum | system-generated | interim/processed | Outlier state | `possible_outlier` | Controlled statuses | Default `not_checked` | filter/validation | None |
| `outlier_methods` | list[string] | system-generated | processed | Detection methods/versions | `["price_psf_iqr_v1"]` | Reproducible | Empty list | validation-only | None |
| `outlier_score` | nullable float | system-generated | processed | Method-specific score | `4.2` | Meaning tied to method | Null if not scored | validation-only | None |
| `outlier_reason` | nullable string | system-generated | processed | Explanation | `Built-up area unusually small` | Evidence-based | Null if none | validation-only | None |
| `outlier_review_status` | nullable enum | system-generated | processed | Review outcome/progress | `pending` | Controlled workflow | Null if not reviewed | validation-only | None |

`outlier_status` values are `not_checked`, `not_outlier`, `possible_outlier`, `confirmed_data_error`, `legitimate_outlier`, and `excluded_from_model`. The process is: detect; check parsing/unit conversion; check source consistency; correct clear derived errors while retaining raw values; flag suspicious records; preserve legitimate luxury/unusual properties; exclude only by documented rules; and consider separate segments when justified. There is no universal statistical cutoff that automatically deletes records.

### Model-preparation fields

| Field name | Data type | Required level | Data layer | Description | Example | Validation rules | Missing-value handling | Model usage | Privacy notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `model_eligible` | boolean | system-generated | processed | Passes current technical/legal eligibility policy | `true` | Rule version documented | False until evaluated | filter | None |
| `model_exclusion_reason` | nullable string | system-generated | processed | Why not eligible | `Unsupported district segment` | Required when false after evaluation | Null only when eligible/not evaluated | validation-only | None |
| `split_group_id` | string | system-generated | processed | Atomic group for splitting | `dup_00042` | Duplicate/property group remains intact | Generate before split | split metadata | None |
| `data_split` | enum | system-generated | processed | `unassigned`, `train`, `validation`, `test` | `train` | Assign after cleaning/deduplication | Default `unassigned` | split metadata | None |
| `target_name` | nullable string | system-generated | processed | Explicit selected target | `completed_transaction_price` | Must match approved experiment | Null before model preparation | metadata | None |
| `target_value` | nullable decimal | system-generated | processed | Target copied/derived under target definition | `650000.00` | Must trace to price field/rule | Null if ineligible/unassigned | target | None |
| `feature_set_version` | nullable string | system-generated | processed | Feature-contract version | `features-1.0.0` | Immutable for trained artefact | Null before preparation | metadata | None |

Splits are assigned only after cleaning and duplicate grouping. Duplicate groups cannot cross splits. Time-based splitting is preferred when dates are reliable, and the final test set remains untouched during model selection. `model_eligible` describes pipeline eligibility, not permission to publish the record.

## 5. Essential fields for model eligibility

### Asking-price model

At minimum, a record needs a valid `price_amount` with `price_type = asking`, canonical state, district or another validated detailed location, residential property type, appropriate reliable size, stable source identity, listing/effective date, and approved data-use status. It must also pass validation, duplicate grouping, and segment-coverage rules.

### Completed-transaction model

At minimum, a record needs a valid `price_amount` with `price_type = completed_transaction`, canonical state, district or another validated detailed location, residential property type, appropriate reliable size, stable source identity, transaction/effective date, and approved data-use status. It must pass the same validation, grouping, and coverage gates.

Exact minimums may change after approved source schemas are inspected. For example, a landed record may require land area while a strata record may rely on built-up area.

## 6. Required, recommended, and optional features

| Classification | Fields/field groups | Initial treatment |
| --- | --- | --- |
| Required for training eligibility | approved source/use status, `price_amount`, `price_currency`, `price_type`, `state`, detailed usable location, `property_category`, `property_type`, appropriate area, source identity, `record_effective_date`, validation and grouping status | Eligibility/target/features as defined; exact rule versioned |
| Strongly recommended | district, city/township, project, subtype, bedrooms, bathrooms, storeys, tenure, `new_or_subsale`, coordinates, reliable date precision | Candidate features after coverage/quality analysis |
| Optional | furnishing, parking, floor level, title, restriction, completion year/age, condition, renovation, occupancy | Use only after reliability, ethics, and leakage review |
| Metadata only | record/source IDs, source/file/URL, licence/terms, schema/dataset/batch/processing versions, timestamps, validation method versions | Never prediction features |
| Excluded from initial modelling | raw description/title, agent reference, URLs, validation notes/codes, rejection reasons, duplicate IDs, canonical IDs, split IDs, personal/address details, rental records | Retain only as permitted for provenance, validation, privacy-safe deduplication, or auditing |

Source URL, agent details, identifiers, validation notes, and duplicate IDs must never be prediction features. They can leak the target or encode source-specific shortcuts.

## 7. Enumerations and controlled vocabularies

These values are initial proposals and may be revised after approved data is examined. Any revision must be versioned and mapped.

| Vocabulary | Proposed values |
| --- | --- |
| State | `Johor`, `Kedah`, `Kelantan`, `Melaka`, `Negeri Sembilan`, `Pahang`, `Penang`, `Perak`, `Perlis`, `Sabah`, `Sarawak`, `Selangor`, `Terengganu`, `Kuala Lumpur`, `Putrajaya`, `Labuan` |
| Price type | `asking`, `completed_transaction`, `auction_reserve`, `auction_sale`, `rental`, `aggregate_median`, `aggregate_average`, `unknown` |
| Property category | `residential`, `commercial`, `industrial`, `agricultural`, `land`, `mixed`, `unknown` (only residential initially eligible) |
| Property type | `terrace_house`, `semi_detached_house`, `detached_house`, `bungalow`, `townhouse`, `cluster_house`, `condominium`, `apartment`, `flat`, `serviced_residence`, `studio`, `other_residential`, `unknown` |
| Property subtype | Initial examples: `intermediate`, `corner`, `end_lot`, `duplex`, `penthouse`, `walk_up`, `other`, `unknown`; revise from evidence |
| Sale type | `sale`, `rent`, `auction`, `unknown` |
| Tenure | `freehold`, `leasehold`, `unknown` |
| Furnishing | `unfurnished`, `partially_furnished`, `fully_furnished`, `unknown` |
| Title type | `individual`, `strata`, `master`, `unknown` |
| Lot restriction | `none`, `bumi_lot`, `malay_reserved`, `other`, `unknown` |
| Validation status | `not_validated`, `valid`, `valid_with_warnings`, `invalid` |
| Duplicate status | `not_checked`, `unique`, `possible_duplicate`, `confirmed_duplicate`, `canonical_record` |
| Outlier status | `not_checked`, `not_outlier`, `possible_outlier`, `confirmed_data_error`, `legitimate_outlier`, `excluded_from_model` |
| Date precision | `exact_day`, `month`, `quarter`, `year`, `unknown` |

## 8. Missing-value rules

- Use nulls rather than empty strings in structured interim and processed data.
- Never use zero to mean a missing price, area, bedroom, bathroom, parking, storey, or age value.
- Use `unknown` only for a categorical field with a documented `unknown` member.
- Distinguish source-missing, not-applicable, and genuinely unknown where that distinction affects validation; use companion status/code fields rather than invented values.
- Future feature imputation occurs inside the training pipeline, fitted on training data only.
- Never impute a target.
- Preserve raw missingness and add versioned missingness indicators only when useful and leakage-safe.

## 9. Data-type rules

- Store Malaysian ringgit as decimal/numeric amounts without `RM`, separators, or shorthand. Avoid binary floating-point for authoritative currency storage.
- Store parsed source area as decimal plus its unit; store normalised areas in square feet while preserving raw value and original unit.
- Store room/parking/floor counts as integers when inherently whole; store `storeys` as decimal when half-storey values are supported.
- Store WGS84 coordinates as decimal degrees with documented precision.
- Store market-event dates as local calendar dates; never add a time that the source did not provide.
- Store collection/processing datetimes as UTC or timezone-aware timestamps.
- Store booleans as true/false, not strings or 0/1 where a typed format exists.
- Store categorical values from versioned controlled vocabularies.
- Store validation-code collections as typed string arrays where supported, or in an equivalent lossless representation.
- Use stable string identifiers, not positional row numbers.

No database engine is selected by this schema.

## 10. Example records

The following are fictional conceptual examples, not collected properties or claims about real market prices. Fields are abbreviated to keep the examples readable.

### Example 1 — Valid Kuala Lumpur asking-price condominium

```json
{
  "record_id": "example_asking_001",
  "source_name": "approved_listing_source_example",
  "source_record_id": "LIST-001",
  "collected_at": "2026-07-13T03:15:00Z",
  "schema_version": "1.0.0",
  "price_raw": "RM 780,000",
  "price_amount": 780000.00,
  "price_currency": "MYR",
  "price_type": "asking",
  "state": "Kuala Lumpur",
  "district": "Kuala Lumpur",
  "city": "Kuala Lumpur",
  "township": "Mont Kiara",
  "project_name": "Example Residence",
  "property_category": "residential",
  "property_type": "condominium",
  "built_up_area_raw": "1,050 sq.ft.",
  "built_up_sqft": 1050.0,
  "bedrooms": 3,
  "bathrooms": 2,
  "listing_date": "2026-06-15",
  "record_effective_date": "2026-06-15",
  "date_precision": "exact_day",
  "validation_status": "valid",
  "duplicate_status": "unique",
  "outlier_status": "not_outlier"
}
```

### Example 2 — Valid Johor completed landed transaction

```json
{
  "record_id": "example_transaction_001",
  "source_name": "approved_transaction_source_example",
  "source_record_id": "TX-JH-001",
  "schema_version": "1.0.0",
  "price_amount": 620000.00,
  "price_currency": "MYR",
  "price_type": "completed_transaction",
  "state": "Johor",
  "district": "Johor Bahru",
  "property_category": "residential",
  "property_type": "terrace_house",
  "property_subtype": "intermediate",
  "built_up_sqft": 1800.0,
  "land_area_raw": "22 x 75 ft",
  "land_area_sqft": 1650.0,
  "bedrooms": 4,
  "bathrooms": 3,
  "storeys": 2.0,
  "tenure": "freehold",
  "transaction_date": "2025-11-20",
  "record_effective_date": "2025-11-20",
  "date_precision": "exact_day",
  "validation_status": "valid"
}
```

### Example 3 — Sarawak record with uncertain mapping

```json
{
  "record_id": "example_sarawak_ambiguous_001",
  "source_name": "approved_source_example",
  "price_amount": 450000.00,
  "price_currency": "MYR",
  "price_type": "asking",
  "state_raw": "Sarawak",
  "state": "Sarawak",
  "district_raw": "Kuching/Samarahan area",
  "district": null,
  "city_raw": "Kuching",
  "city": "Kuching",
  "location_confidence": "low",
  "location_validation_status": "ambiguous",
  "location_validation_notes": "District cannot be selected without stronger source evidence.",
  "validation_status": "valid_with_warnings",
  "validation_warning_codes": ["AMBIGUOUS_DISTRICT"],
  "review_required": true,
  "model_eligible": false,
  "model_exclusion_reason": "Unresolved administrative mapping"
}
```

### Example 4 — Suspicious unit or parsing error

```json
{
  "record_id": "example_invalid_001",
  "source_name": "approved_source_example",
  "price_raw": "RM 650k",
  "price_amount": 650000.00,
  "price_currency": "MYR",
  "price_type": "asking",
  "state": "Selangor",
  "property_type": "condominium",
  "built_up_area_raw": "95 m2",
  "built_up_area_value": 95.0,
  "built_up_area_unit": "sqft",
  "built_up_sqft": 95.0,
  "area_validation_status": "invalid",
  "validation_status": "invalid",
  "validation_error_codes": ["POSSIBLE_UNIT_ERROR", "INVALID_BUILT_UP_AREA"],
  "outlier_status": "possible_outlier",
  "outlier_reason": "Raw text indicates sqm but parsed unit is sqft.",
  "review_required": true,
  "model_eligible": false
}
```

The fourth record is preserved. A later correction could set the unit to `sqm` and derive approximately `1022.57` sqft while retaining the original raw text and the history of the correction.

## 11. Schema evolution

- Use semantic versions: major for breaking field/meaning changes, minor for backward-compatible fields or enum additions, patch for clarifications that do not change stored meaning.
- Readers should support the documented current version and explicitly reject or migrate incompatible major versions.
- Every breaking change needs a tested migration specification before implementation, including old-to-new mappings and treatment of unmappable values.
- Update the data dictionary, controlled vocabularies, examples, validation rules, and migration notes together.
- Add new property or price types through reviewed enum changes; never repurpose an existing value.
- Existing field meanings, units, null semantics, and derivation rules must not change silently.
- Dataset releases record both schema and processing versions.
- Every trained model records its dataset version, schema version, processing version, feature-set version, and target definition.

## 12. Relationship to future implementation

```text
Approved source importer or scraper
        ↓
Raw record
        ↓
Schema validation
        ↓
Cleaning and normalisation
        ↓
Duplicate grouping
        ↓
Outlier investigation
        ↓
Processed dataset
        ↓
Train/validation/test split
        ↓
Model training
```

The schema will provide the contract for importers, validation, cleaning, deduplication, outlier review, splitting, and feature selection. No part of this pipeline is implemented by this task, and “scraper” applies only if a source later explicitly permits automated collection.

## 13. Open decisions

- Exact NAPIC transaction fields, export format, identifier stability, and data-use terms
- Whether address-level information may be stored or must be generalised
- Whether project names are consistently available and legally reusable
- Whether listing descriptions may be retained for privacy-safe deduplication
- Whether an authoritative, approved postcode dataset can be obtained
- Minimum records and time coverage required per district/property segment
- Whether asking-price and transaction models use one physical implementation of this logical schema
- Whether landed and high-rise records require different mandatory size/title fields
- Which official code system/version will define state and district codes
- How qualitative floor bands and source-specific property subtypes should be standardised
- Whether lot restriction, occupancy, and other sensitive/legal characteristics should be model features
