"""Streamlit UI for real historical aggregates and a separate synthetic demo."""

from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PROJECT_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

try:
    import streamlit as st
except ImportError as exc:
    raise RuntimeError("Install UI dependencies with: pip install -e .[ui]") from exc

from house_price_estimator.data_sources import load_dataset_metadata, load_historical_bundle
from house_price_estimator.prediction import (
    HistoricalExplorer,
    RealPropertyService,
    limited_recency_message,
)
from house_price_estimator.real_transactions import RealPropertyBundle
from house_price_estimator.ui_contracts import (
    FIELD_LABELS,
    individual_field_visibility,
    normalize_individual_submission,
)


CATALOG_PATH = PROJECT_ROOT / "data" / "processed" / "dataset_catalog.json"
REAL_PROPERTY_MODEL_PATH = PROJECT_ROOT / "models" / "real" / "napic_property_bundle.pkl"
OPTIONAL_HELP = "Optional — leave blank when unknown."


@st.cache_resource
def load_explorers() -> tuple[HistoricalExplorer, ...]:
    """Load metadata and trusted repository-owned bundles once per process."""
    return tuple(
        HistoricalExplorer(metadata, load_historical_bundle(metadata, PROJECT_ROOT))
        for metadata in load_dataset_metadata(CATALOG_PATH)
    )


@st.cache_resource
def load_real_property_service() -> RealPropertyService:
    return RealPropertyService(RealPropertyBundle.load(REAL_PROPERTY_MODEL_PATH))


def property_type_label(value: str) -> str:
    return value.replace("_", " ").replace("one to one half", "1 to 1½").replace(
        "two to two half", "2 to 2½"
    ).title()


def _period_label(period: tuple[int, int]) -> str:
    return f"{period[0]} Q{period[1]}"


def _optional_number(
    label: str,
    *,
    key: str,
    min_value: float | int,
    step: float | int,
    integer: bool = False,
) -> float | int | None:
    known = st.checkbox(f"I know the {label.lower()}", key=f"know-{key}")
    if not known:
        return None
    value = st.number_input(
        label,
        min_value=min_value,
        value=None,
        step=step,
        placeholder=OPTIONAL_HELP,
        key=key,
    )
    if value is None:
        return None
    return int(value) if integer else float(value)


def render_historical_explorer(explorer: HistoricalExplorer) -> None:
    """Render the real official aggregate-data explorer."""
    metadata = explorer.metadata
    coverage = explorer.coverage
    st.subheader(metadata.title)
    st.caption("Uses real official aggregate transaction data.")
    st.caption(
        f"Validated coverage: {len(coverage.states)} state/territory market(s) · "
        f"{len(coverage.combinations)} selectable combinations · "
        f"{_period_label(coverage.earliest_period)}–{_period_label(coverage.latest_period)}"
    )

    state = st.selectbox("State or federal territory", coverage.states, key="history-state")
    area = st.selectbox(metadata.area_label, coverage.areas(state), key="history-area")
    property_type = st.selectbox(
        "Aggregate property category",
        coverage.property_types(state, area),
        format_func=property_type_label,
        key="history-type",
    )
    years = coverage.years(state, area, property_type)
    year = st.selectbox("Historical year", years, index=len(years) - 1, key="history-year")
    quarter = st.selectbox(
        "Historical quarter",
        coverage.quarters(state, area, property_type, year),
        key="history-quarter",
    )
    comparison = _optional_number(
        "Comparison price (RM)",
        key="history-comparison",
        min_value=1.0,
        step=10_000.0,
    )

    if st.button("Show historical quarterly average", type="primary", width="stretch"):
        result = explorer.predict(
            state=state,
            area=area,
            property_type=property_type,
            year=year,
            quarter=quarter,
        )
        history = result.nearby_periods
        latest_period = explorer.latest_period(state, area, property_type)
        latest = next(
            item
            for item in reversed(history)
            if (item["year"], item["quarter"]) == latest_period
        )
        st.subheader("Historical market result")
        st.write(
            "Historical average completed transaction price for the selected location, "
            "property category, and period."
        )
        st.metric(metadata.observed_price_label, f"RM {result.observed_average_price_rm:,.0f}")
        st.metric("Latest known average", f"RM {latest['average_price_rm']:,.0f}")
        st.write(f"**Selected period:** {year} Q{quarter}")
        st.write(f"**Source:** {metadata.source_name}")
        st.write(f"**Dataset version:** {result.dataset_version}")
        st.write(
            f"**Available periods:** {_period_label(coverage.earliest_period)} to "
            f"{_period_label(coverage.latest_period)}"
        )
        if result.transaction_count is not None:
            st.metric("Transactions represented", f"{result.transaction_count:,}")
            st.write(
                "Transaction-volume support: "
                f"**{(result.volume_support or 'unknown').replace('_', ' ')}**"
            )
        else:
            st.write("Transactions represented: **not published by this source**")
            st.write("Transaction-volume support: **not available**")

        if not result.public_prediction_supported:
            st.warning(
                "Fewer than 20 transactions support this group. It is retained as history but "
                "is excluded from public predictive support."
            )
        elif result.model_estimate_rm is not None:
            st.metric(metadata.prediction_label, f"RM {result.model_estimate_rm:,.0f}")
            if result.lower_rm is not None and result.upper_rm is not None:
                st.write(
                    f"Historical baseline range: **RM {result.lower_rm:,.0f} – "
                    f"RM {result.upper_rm:,.0f}**"
                )
        else:
            st.info("This is a historical training period; no predictive estimate is shown.")

        if comparison is not None:
            difference = comparison - result.observed_average_price_rm
            direction = "above" if difference >= 0 else "below"
            percent = abs(difference) / result.observed_average_price_rm * 100
            st.info(
                f"The comparison price is RM {abs(difference):,.0f} ({percent:.1f}%) "
                f"{direction} this historical average."
            )

        recency = limited_recency_message(latest_period)
        if recency:
            st.warning(recency)
        if len(history) >= 3:
            trend = pd.DataFrame(
                {
                    "Period": [f"{item['year']} Q{item['quarter']}" for item in history],
                    "Average price (RM)": [item["average_price_rm"] for item in history],
                }
            )
            st.write("Historical trend")
            st.line_chart(trend, x="Period", y="Average price (RM)")
            st.dataframe(trend, hide_index=True, width="stretch")
        st.error(
            "This is a historical aggregate benchmark, not the exact value of a particular "
            "house or a current official valuation."
        )

    with st.expander("Data sources, download, model, and limitations"):
        st.write(f"Publisher: **{metadata.source_name}**")
        for index, url in enumerate(metadata.source_urls, start=1):
            st.markdown(f"[Source catalogue entry {index}]({url})")
        st.write(
            f"Licence status: **{metadata.licence_status}** · "
            f"Redistribution allowed: **{'yes' if metadata.redistribution_allowed else 'no'}**"
        )
        for limitation in metadata.limitations:
            st.write(f"- {limitation}")
        data_path = PROJECT_ROOT / metadata.processed_data_path
        if metadata.redistribution_allowed and data_path.is_file():
            st.download_button(
                "Download validated aggregate CSV",
                data_path.read_bytes(),
                file_name=data_path.name,
                mime="text/csv",
            )


def _disclosure_list(title: str, values: tuple[str, ...], empty: str) -> None:
    st.markdown(f"#### {title}")
    if values:
        for value in values:
            st.write(f"- {value}")
    else:
        st.write(empty)


def render_individual_estimator(service: RealPropertyService) -> None:
    """Render the complete optional form without implying real model accuracy."""
    st.subheader("Individual Property Estimator")
    st.caption("Uses validated real property-level data")
    st.success(
        "Uses official NAPIC/JPPH completed residential transactions through 2026 Q1. "
        "This is an estimate, not an official valuation."
    )
    st.write(
        "State, district, and property type identify the supported market segment. All "
        "other details are optional; leave them blank when unknown."
    )

    with st.expander("Location", expanded=True):
        state = st.selectbox(
            "State or federal territory",
            service.bundle.states,
            index=None,
            placeholder="Select a state or federal territory",
            key="property-state",
        )
        district_options = service.bundle.districts(state) if state else ()
        district = st.selectbox(
            "District", district_options, index=None,
            placeholder="Select a district", key="property-district",
        )
        city = st.text_input("City or township", value="", help=OPTIONAL_HELP)
        project = st.text_input("Development or project name", value="", help=OPTIONAL_HELP)

    with st.expander("Property size", expanded=True):
        property_type = st.selectbox(
            "Property type",
            service.bundle.property_types(state, district) if state and district else (),
            index=None,
            placeholder="Select a property type",
            key="property-type",
        )
        subtype = st.selectbox(
            "Property subtype",
            ["Unknown", "Intermediate", "Corner", "End lot", "Duplex", "Penthouse"],
            help=OPTIONAL_HELP,
        )
        visibility = individual_field_visibility(property_type) if property_type else None
        built_up = _optional_number(
            "Built-up area (sq ft)", key="built-up", min_value=1.0, step=50.0
        )
        if visibility and visibility["land_area_sqft"]:
            land_area = _optional_number(
                "Land area (sq ft)", key="land-area", min_value=1.0, step=50.0
            )
        else:
            land_area = "Not applicable" if visibility else None
            if visibility:
                st.info("Land area: Not applicable to an individual high-rise unit.")

    with st.expander("Rooms and parking"):
        bedrooms = _optional_number(
            "Bedrooms", key="bedrooms", min_value=0, step=1, integer=True
        )
        additional_bedrooms = _optional_number(
            "Additional/helper bedrooms",
            key="additional-bedrooms",
            min_value=0,
            step=1,
            integer=True,
        )
        bathrooms = _optional_number(
            "Bathrooms", key="bathrooms", min_value=1, step=1, integer=True
        )
        car_parks = _optional_number(
            "Car parks", key="car-parks", min_value=0, step=1, integer=True
        )
        if visibility and visibility["storeys"]:
            storeys = _optional_number(
                "Storeys", key="storeys", min_value=0.5, step=0.5
            )
        else:
            storeys = "Not applicable" if visibility else None
            if visibility:
                st.info("Storeys: Not applicable to an individual high-rise unit.")
        if visibility and visibility["floor_level"]:
            floor_level = _optional_number(
                "Floor level", key="floor-level", min_value=0, step=1, integer=True
            )
        else:
            floor_level = "Not applicable" if visibility else None
            if visibility:
                st.info("Floor level: Not applicable to landed property.")

    with st.expander("Ownership and condition"):
        tenure = st.selectbox("Tenure", ["Unknown", "Freehold", "Leasehold"], help=OPTIONAL_HELP)
        furnishing = st.selectbox(
            "Furnishing",
            ["Unknown", "Unfurnished", "Partly Furnished", "Fully Furnished"],
            help=OPTIONAL_HELP,
        )
        completion_year = _optional_number(
            "Completion year", key="completion-year", min_value=1800, step=1, integer=True
        )
        property_age = _optional_number(
            "Property age (years)", key="property-age", min_value=0, step=1, integer=True
        )
        renovation = st.selectbox(
            "Renovation status",
            ["Unknown", "Not renovated", "Partly renovated", "Fully renovated"],
            help=OPTIONAL_HELP,
        )
        condition = st.selectbox(
            "Property condition",
            ["Unknown", "Needs repair", "Average", "Good", "Excellent"],
            help=OPTIONAL_HELP,
        )

    with st.expander("Comparison price"):
        asking_price = _optional_number(
            "Asking price (RM)", key="asking-price", min_value=1.0, step=10_000.0
        )

    if st.button("Estimate completed transaction price", type="primary", width="stretch"):
        raw = {
            "state": state,
            "district": district,
            "city": city,
            "township": city,
            "project_name": project,
            "property_type": property_type,
            "property_subtype": subtype,
            "built_up_sqft": built_up,
            "land_area_sqft": land_area,
            "bedrooms": bedrooms,
            "additional_bedrooms": additional_bedrooms,
            "bathrooms": bathrooms,
            "car_parks": car_parks,
            "storeys": storeys,
            "floor_level": floor_level,
            "tenure": tenure,
            "furnishing": furnishing,
            "completion_year": completion_year,
            "property_age_years": property_age,
            "renovation_status": renovation,
            "property_condition": condition,
            "asking_price": asking_price,
        }
        try:
            submission = normalize_individual_submission(raw)
            result = service.predict(submission)
        except ValueError as exc:
            st.error(str(exc))
        else:
            st.subheader("Individual property estimate")
            st.metric("Estimated completed transaction price", f"RM {result.estimate:,.0f}")
            st.write(f"Estimated range: **RM {result.lower:,.0f} – RM {result.upper:,.0f}**")
            if result.price_per_sqft is not None:
                st.write(f"Estimated price per sq ft: **RM {result.price_per_sqft:,.0f}**")
            if result.asking_price_assessment:
                st.info(result.asking_price_assessment)
            st.write(f"Transactions in selected segment: **{result.support_count:,}**")
            if result.support_status != "high_support":
                st.warning(
                    f"Limited segment support: {result.support_count:,} records. "
                    "Treat this estimate with extra caution."
                )
            else:
                st.write("Data support: **high support**")
            st.write(f"Latest source period: **{result.latest_period}**")
            st.write(f"Model version: **{result.model_version}**")
            st.write(f"Dataset version: **{result.dataset_version}**")
            st.write("True model input fields: " + ", ".join(result.model_features))
            _disclosure_list(
                "Information used",
                result.disclosure.used,
                "No optional user-supplied information was used.",
            )
            _disclosure_list(
                "Information provided but not used",
                result.disclosure.provided_but_not_used,
                "None.",
            )
            _disclosure_list(
                "Missing optional information",
                result.disclosure.missing_optional,
                "None.",
            )
            _disclosure_list(
                "Not applicable",
                result.disclosure.not_applicable,
                "None.",
            )
            st.error(
                "Educational estimate only. Not financial advice, a guaranteed sale price, "
                "or an official valuation."
            )

    with st.expander("Individual-model source and limitations"):
        st.markdown(
            "Source: [NAPIC/JPPH Data Transaksi Terbuka]"
            "(https://napic.jpph.gov.my/ms/data-transaksi?category=36&id=241)"
        )
        st.markdown(
            "Terms: [Malaysian Government Open Data Terms of Use 1.0]"
            "(https://www.mot.gov.my/my/Documents/Terms%20of%20Use%20Government%20Open%20Data%201.0.pdf)"
        )
        st.write(
            "Data and information are subject to the Malaysian Government Open Data "
            "Terms of Use 1.0."
        )
        st.write(
            "The source does not publish bedrooms, bathrooms, car parks, furnishing, "
            "completion year, renovation, condition, or a stable transaction identifier."
        )
        st.write(
            "Performance varies by state, district, property type, and price range. "
            "The estimated range is empirical and is not a guarantee."
        )


st.set_page_config(page_title="Malaysia House Price Explorer", layout="centered")
st.title("Malaysia House Price Explorer")

if not CATALOG_PATH.is_file() or not REAL_PROPERTY_MODEL_PATH.is_file():
    st.error("A required repository dataset catalog or real property model is missing.")
    st.stop()

historical_tab, property_tab = st.tabs(
    ["Historical Market Explorer", "Individual Property Estimator"]
)
with historical_tab:
    st.header("Historical Market Explorer")
    st.caption("Uses real official aggregate transaction data.")
    st.warning(
        "This mode reports historical aggregate averages. It does not estimate the exact value "
        "of a specific property."
    )
    explorers = load_explorers()
    titles = {explorer.metadata.title: explorer for explorer in explorers}
    selected_title = st.selectbox("Historical aggregate dataset", tuple(titles))
    render_historical_explorer(titles[selected_title])

with property_tab:
    render_individual_estimator(load_real_property_service())

st.divider()
st.caption(
    "Educational and informational use only. Not financial advice, an official valuation, "
    "or a guaranteed market price."
)
