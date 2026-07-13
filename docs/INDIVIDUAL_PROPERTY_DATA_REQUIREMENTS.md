# Individual Property Dataset Requirements

## Why the estimator is data-pending

The current real datasets contain quarterly averages grouped by location and
property category. They do not contain individual homes or the physical and
ownership attributes needed to estimate one property's price. The Streamlit
property form is therefore a disabled design preview and never calls an
aggregate model.

An individual-property model may be enabled only after a legally usable source
has been validated, deduplicated before splitting, evaluated by time and
location, and shown to support the requested inputs. Asking prices and completed
transaction prices must remain separate.

## Minimum record schema

| Priority | Columns | Purpose |
| --- | --- | --- |
| Essential | `source_name`, `source_record_id`, `price`, `price_type`, `state`, `district`, `property_type`, `built_up_sqft` or another appropriate size field, `listing_date` or `transaction_date` | Identifies, dates, locates, sizes, and labels the target record |
| Strongly recommended | `township`, `project_name`, `land_area_sqft` for landed homes, `bedrooms`, `bathrooms`, `car_parks`, `tenure`, `storeys` | Captures major within-district and physical differences |
| Optional | `city`, `floor_level`, `furnishing`, `completion_year`, `property_age_years`, `condition`, `renovation_status`, `latitude`, `longitude` | Adds context when consistently and lawfully available |

The canonical intake should support these explicit columns:

```text
source_name
source_record_id
price
price_type
state
district
city
township
project_name
property_type
built_up_sqft
land_area_sqft
bedrooms
bathrooms
car_parks
storeys
floor_level
tenure
furnishing
completion_year
property_age_years
listing_date
transaction_date
```

Source identifiers and dates are essential for provenance, time-safe splitting,
and duplicate grouping. A missing, not-applicable value must remain missing; it
must not be encoded as zero.

## Property-type rules

For a high-rise unit, built-up area is required; floor level and car parks are
useful; land area and the unit's number of storeys are normally not applicable.
For a landed home, built-up area is required; land area is strongly recommended;
storeys are important; floor level is not applicable; and car parks may still be
useful.

The future form follows those rules by hiding not-applicable fields instead of
submitting zero. Before modelling, source-specific definitions, missingness,
units, legal-use conditions, coverage, and data quality must be documented.
