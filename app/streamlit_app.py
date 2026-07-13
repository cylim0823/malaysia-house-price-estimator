"""Streamlit UI for annual aggregate benchmarks and individual estimates."""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PROJECT_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

import streamlit as st

from house_price_estimator.aggregate_data import AggregateBenchmarkService
from house_price_estimator.artifacts import (
    HISTORICAL_DATA_PATH,
    INDIVIDUAL_PROPERTY_MODEL_PATH,
    ModelArtifactError,
    load_active_historical_model,
    load_individual_property_model,
)
from house_price_estimator.prediction import RealPropertyService
from house_price_estimator.data_pipeline import aggregate_property_type
from house_price_estimator.ui_contracts import (
    individual_field_visibility,
    normalize_individual_submission,
)


AGGREGATE_DATA_PATH = HISTORICAL_DATA_PATH
REAL_PROPERTY_MODEL_PATH = INDIVIDUAL_PROPERTY_MODEL_PATH
OPTIONAL_HELP = "Optional — leave blank when unknown."
APP_BUILD_ID = "generic-history-2026.07.13.1"


@st.cache_resource
def load_aggregate_service() -> AggregateBenchmarkService:
    active = load_active_historical_model()
    return AggregateBenchmarkService.from_csv(
        AGGREGATE_DATA_PATH, model_metadata=active.metadata
    )


@st.cache_resource
def load_real_property_service() -> RealPropertyService:
    return RealPropertyService(load_individual_property_model())


def property_type_label(value: str) -> str:
    return aggregate_property_type(value).property_type_label


def optional_number(
    label: str, *, key: str, minimum: float | int, step: float | int, integer: bool = False
) -> float | int | None:
    if not st.checkbox(f"I know the {label.lower()}", key=f"know-{key}"):
        return None
    value = st.number_input(
        label, min_value=minimum, value=None, step=step, placeholder=OPTIONAL_HELP, key=key
    )
    return int(value) if integer and value is not None else value


def render_historical_explorer(service: AggregateBenchmarkService) -> None:
    """Render dynamic year-level official completed-transaction benchmarks."""
    coverage = service.coverage
    st.subheader("Official completed-transaction history")
    st.caption(
        f"Validated coverage: {len(coverage.states)} states and federal territories, "
        "with available years generated from validated records. Publication periods "
        "are handled internally."
    )
    state = st.selectbox(
        "State or federal territory", coverage.states, key="history-state",
    )
    years = coverage.years(state)
    year = st.selectbox(
        "Year", years, index=0, key=f"history-year-{state}",
    )
    districts = coverage.districts(state, year)
    district = (
        st.selectbox(
            "District or area", districts, key=f"history-district-{state}-{year}",
        )
        if districts else None
    )
    st.caption(f"Coverage: {'District-level' if districts else 'State-level'}")
    property_types = coverage.property_types(state, year, district)
    property_type = st.selectbox(
        "Property type",
        property_types,
        format_func=property_type_label,
        key=f"history-type-{state}-{year}-{district or 'state'}",
    )
    comparison = optional_number(
        "Comparison price (RM)", key="history-comparison", minimum=1.0, step=10_000.0
    )
    if st.button("Show historical benchmark", type="primary", width="stretch"):
        result = service.benchmark(
            state=state, district=district, property_type=property_type, year=year
        )
        st.subheader("Historical market benchmark")
        st.caption(
            f"Coverage: {'District-level' if result.district_used is not None else 'State-level'}"
        )
        st.metric(result.display_label, f"RM {result.annual_average_price_rm:,.0f}")
        st.metric("Transactions represented", f"{result.transaction_count:,}")
        st.write(f"**Total transaction value:** RM {result.transaction_value_rm:,.0f}")
        st.write(f"**Year status:** {result.year_status.replace('_', ' ')}")
        st.write("**Periods included:** " + ", ".join(f"Q{q}" for q in result.periods_included))
        st.write(
            "**Missing periods:** "
            + (", ".join(f"Q{q}" for q in result.periods_missing) or "None")
        )
        st.write(f"**Coverage completeness:** {result.coverage_completeness:.0%}")
        st.write(f"**Coverage level:** {result.coverage_level.replace('_', ' ')}")
        st.write(
            f"**Available data period:** {result.available_period_start} to "
            f"{result.available_period_end}"
        )
        if result.fallback_reason:
            st.info(result.fallback_reason)
        st.write(f"**Source:** {result.source_name}")
        st.write(f"**Source document:** {result.source_document}")
        st.write(f"**Source file:** {result.source_file}")
        st.write(f"**Dataset version:** {result.dataset_version}")
        st.write(
            f"**Data age:** {result.data_age_days} days "
            f"(retrieved {result.retrieved_at})"
        )
        if comparison is not None:
            difference = comparison - result.annual_average_price_rm
            direction = "above" if difference >= 0 else "below"
            percent = abs(difference) / result.annual_average_price_rm * 100
            st.info(
                f"The comparison price is RM {abs(difference):,.0f} ({percent:.1f}%) "
                f"{direction} this historical average."
            )
        st.error(
            "Historical aggregate benchmark only; not an exact property value or official valuation."
        )
    with st.expander("Data source and limitations"):
        st.write("Publisher: **National Property Information Centre (NAPIC), JPPH**")
        st.markdown(
            "[Official open transaction source]"
            "(https://napic.jpph.gov.my/ms/data-transaksi?category=36&id=241)"
        )
        st.write("Licensed under Malaysian Government Open Data Terms of Use 1.0.")
        st.write(
            "Annual values equal total transaction value divided by total transaction count; "
            "quarterly averages are never averaged without weights."
        )


def render_disclosure(title: str, values: tuple[str, ...], empty: str = "None.") -> None:
    st.markdown(f"#### {title}")
    if values:
        for value in values:
            st.write(f"- {value}")
    else:
        st.write(empty)


def render_individual_estimator(service: RealPropertyService) -> None:
    """Render optional property details separately from aggregate benchmarks."""
    st.subheader("Individual Property Estimator")
    st.success(
        "Uses official NAPIC/JPPH completed residential transactions through 2026 Q1. "
        "This is an estimate, not an official valuation."
    )
    state = st.selectbox(
        "State or federal territory", service.bundle.states, index=None, key="property-state"
    )
    district = st.selectbox(
        "District", service.bundle.districts(state) if state else (), index=None,
        key="property-district",
    )
    property_type = st.selectbox(
        "Property type",
        service.bundle.property_types(state, district) if state and district else (),
        index=None,
        key="property-type",
    )
    visibility = individual_field_visibility(property_type) if property_type else None
    city = st.text_input("City or township", help=OPTIONAL_HELP)
    project = st.text_input("Development or project name", help=OPTIONAL_HELP)
    subtype = st.selectbox(
        "Property subtype", ["Unknown", "Intermediate", "Corner", "End lot", "Duplex", "Penthouse"]
    )
    built_up = optional_number("Built-up area (sq ft)", key="built-up", minimum=1.0, step=50.0)
    land_area = (
        optional_number("Land area (sq ft)", key="land-area", minimum=1.0, step=50.0)
        if visibility and visibility["land_area_sqft"] else "Not applicable" if visibility else None
    )
    if visibility and not visibility["land_area_sqft"]:
        st.info("Land area: Not applicable to an individual high-rise unit.")
    bedrooms = optional_number("Bedrooms", key="bedrooms", minimum=0, step=1, integer=True)
    additional_bedrooms = optional_number(
        "Additional/helper bedrooms", key="additional-bedrooms", minimum=0, step=1, integer=True
    )
    bathrooms = optional_number("Bathrooms", key="bathrooms", minimum=1, step=1, integer=True)
    car_parks = optional_number("Car parks", key="car-parks", minimum=0, step=1, integer=True)
    storeys = (
        optional_number("Storeys", key="storeys", minimum=0.5, step=0.5)
        if visibility and visibility["storeys"] else "Not applicable" if visibility else None
    )
    if visibility and not visibility["storeys"]:
        st.info("Storeys: Not applicable to an individual high-rise unit.")
    floor_level = (
        optional_number("Floor level", key="floor-level", minimum=0, step=1, integer=True)
        if visibility and visibility["floor_level"] else "Not applicable" if visibility else None
    )
    if visibility and not visibility["floor_level"]:
        st.info("Floor level: Not applicable to landed property.")
    tenure = st.selectbox("Tenure", ["Unknown", "Freehold", "Leasehold"])
    furnishing = st.selectbox("Furnishing", ["Unknown", "Unfurnished", "Partly Furnished", "Fully Furnished"])
    completion_year = optional_number(
        "Completion year", key="completion-year", minimum=1800, step=1, integer=True
    )
    property_age = optional_number(
        "Property age (years)", key="property-age", minimum=0, step=1, integer=True
    )
    renovation = st.selectbox(
        "Renovation status", ["Unknown", "Not renovated", "Partly renovated", "Fully renovated"]
    )
    condition = st.selectbox("Property condition", ["Unknown", "Needs repair", "Average", "Good", "Excellent"])
    asking_price = optional_number(
        "Asking price (RM)", key="asking-price", minimum=1.0, step=10_000.0
    )
    if st.button("Estimate completed transaction price", type="primary", width="stretch"):
        raw = {
            "state": state, "district": district, "city": city, "township": city,
            "project_name": project, "property_type": property_type,
            "property_subtype": subtype, "built_up_sqft": built_up,
            "land_area_sqft": land_area, "bedrooms": bedrooms,
            "additional_bedrooms": additional_bedrooms, "bathrooms": bathrooms,
            "car_parks": car_parks, "storeys": storeys, "floor_level": floor_level,
            "tenure": tenure, "furnishing": furnishing,
            "completion_year": completion_year, "property_age_years": property_age,
            "renovation_status": renovation, "property_condition": condition,
            "asking_price": asking_price,
        }
        try:
            result = service.predict(normalize_individual_submission(raw))
        except ValueError as exc:
            st.error(str(exc))
        else:
            st.metric("Estimated completed transaction price", f"RM {result.estimate:,.0f}")
            st.write(f"Estimated range: **RM {result.lower:,.0f} – RM {result.upper:,.0f}**")
            if result.price_per_sqft is not None:
                st.write(f"Estimated price per sq ft: **RM {result.price_per_sqft:,.0f}**")
            if result.asking_price_assessment:
                st.info(result.asking_price_assessment)
            st.write(f"Transactions in selected segment: **{result.support_count:,}**")
            render_disclosure("Information used", result.disclosure.used)
            render_disclosure("Information provided but not used", result.disclosure.provided_but_not_used)
            render_disclosure("Missing optional information", result.disclosure.missing_optional)
            render_disclosure("Not applicable", result.disclosure.not_applicable)
            st.error("Educational estimate only; not financial advice or an official valuation.")


st.set_page_config(page_title="Malaysia House Price Explorer", layout="centered")
st.title("Malaysia House Price Explorer")
if not AGGREGATE_DATA_PATH.is_file() or not REAL_PROPERTY_MODEL_PATH.is_file():
    st.error("A required processed dataset or model artefact is missing.")
    st.stop()

try:
    aggregate_service = load_aggregate_service()
    real_property_service = load_real_property_service()
except ModelArtifactError as exc:
    st.error(str(exc))
    st.stop()

history_tab, property_tab = st.tabs(["Historical Market Explorer", "Individual Property Estimator"])
with history_tab:
    st.warning("This mode does not estimate the exact value of a specific property.")
    render_historical_explorer(aggregate_service)
with property_tab:
    render_individual_estimator(real_property_service)

with st.expander("Technical details"):
    st.write(f"Application build: **{APP_BUILD_ID}**")
    st.write(
        "Historical model version: **"
        f"{aggregate_service.model_metadata.get('model_version', 'unavailable')}**"
    )
    st.write(
        "Historical dataset version: **"
        f"{aggregate_service.model_metadata.get('dataset_version', 'unavailable')}**"
    )

st.divider()
st.caption("Educational and informational use only. Not financial advice or an official valuation.")
