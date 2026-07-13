"""Streamlit explorers for licensed aggregate data and future property inputs."""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PROJECT_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

try:
    import streamlit as st
except ImportError as exc:
    raise RuntimeError("Install UI dependencies with: pip install -e .[ui]") from exc

from house_price_estimator.data_sources import (
    load_dataset_metadata,
    load_historical_bundle,
)
from house_price_estimator.prediction import HistoricalExplorer
from house_price_estimator.schema import State
from house_price_estimator.ui_contracts import individual_field_visibility


CATALOG_PATH = PROJECT_ROOT / "data" / "processed" / "dataset_catalog.json"
MODE_HISTORICAL = "Historical Market Explorer"
MODE_INDIVIDUAL = "Individual Property Estimator — Data Pending"


@st.cache_resource
def load_explorers() -> tuple[HistoricalExplorer, ...]:
    """Load metadata and trusted repository-owned bundles once per process."""
    return tuple(
        HistoricalExplorer(metadata, load_historical_bundle(metadata, PROJECT_ROOT))
        for metadata in load_dataset_metadata(CATALOG_PATH)
    )


def assessment(asking: float, lower: float, upper: float) -> str:
    if asking < lower:
        return "Below estimated range"
    if asking > upper:
        return "Above estimated range"
    return "Within estimated range"


def property_type_label(value: str) -> str:
    return value.replace("_", " ").replace("one to one half", "1 to 1½").replace(
        "two to two half", "2 to 2½"
    ).title()


def show_comparison(asking: float, historical_average: float) -> None:
    if not asking:
        return
    difference = asking - historical_average
    direction = "above" if difference >= 0 else "below"
    percent = abs(difference) / historical_average * 100
    st.info(
        f"The comparison price is RM {abs(difference):,.0f} ({percent:.1f}%) {direction} "
        "this historical group average. This is context, not a property valuation."
    )


def _period_label(period: tuple[int, int]) -> str:
    return f"{period[0]} Q{period[1]}"


def render_historical_explorer(explorer: HistoricalExplorer) -> None:
    """Render one metadata-driven form for every approved aggregate dataset."""
    metadata = explorer.metadata
    coverage = explorer.coverage
    st.subheader(metadata.title)
    st.caption(
        f"Validated data: {len(coverage.states)} state/territory market(s) · "
        f"{len(coverage.combinations)} selectable combinations · "
        f"{_period_label(coverage.earliest_period)}–{_period_label(coverage.latest_period)}"
    )

    state = st.selectbox("State or federal territory", coverage.states)
    area = st.selectbox(metadata.area_label, coverage.areas(state))
    property_type = st.selectbox(
        "Aggregate property category",
        coverage.property_types(state, area),
        format_func=property_type_label,
    )
    years = coverage.years(state, area, property_type)
    year = st.selectbox("Historical year", years, index=len(years) - 1)
    quarter = st.selectbox(
        "Historical quarter", coverage.quarters(state, area, property_type, year)
    )
    comparison = st.number_input(
        "Optional comparison price (RM)",
        min_value=0.0,
        value=0.0,
        step=10_000.0,
        help="Leave at zero to omit. This does not turn the result into a property valuation.",
    )

    if st.button(
        "Show historical quarterly average",
        type="primary",
        width="stretch",
        key=f"show-{metadata.dataset_id}",
    ):
        result = explorer.predict(
            state=state,
            area=area,
            property_type=property_type,
            year=year,
            quarter=quarter,
        )
        st.subheader("Historical quarterly group result")
        st.metric(metadata.observed_price_label, f"RM {result.observed_average_price_rm:,.0f}")
        if result.transaction_count is not None:
            st.metric("Completed transactions represented", f"{result.transaction_count:,}")
            st.write(
                "Transaction-volume support: "
                f"**{(result.volume_support or 'unknown').replace('_', ' ')}**"
            )
        else:
            st.write("Transactions represented: **not published in this aggregate source**")
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
                if comparison:
                    st.info(assessment(comparison, result.lower_rm, result.upper_rm))
        else:
            st.info("This is a historical training period; no predictive estimate is shown.")

        st.write(
            f"**Selection:** {state} · {area} · {property_type_label(property_type)} · "
            f"{year} Q{quarter}"
        )
        show_comparison(comparison, result.observed_average_price_rm)
        if result.nearby_periods:
            st.write("Nearby historical quarters")
            st.dataframe(
                [
                    {
                        "period": f"{item['year']} Q{item['quarter']}",
                        "average_price_rm": item["average_price_rm"],
                        "transactions": item["transaction_count"],
                        "volume_support": item["volume_support"],
                    }
                    for item in result.nearby_periods
                ],
                width="stretch",
                hide_index=True,
            )
        st.error(
            "This is a historical aggregate benchmark, not a current valuation or an estimate "
            "for a specific property."
        )
        st.caption(
            f"Dataset: {result.dataset_version} · Model: {result.model_name} · "
            f"Coverage: {_period_label(coverage.earliest_period)}–"
            f"{_period_label(coverage.latest_period)}"
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
                key=f"download-{metadata.dataset_id}",
            )


def render_individual_pending() -> None:
    st.header(MODE_INDIVIDUAL)
    st.warning(
        "Individual-property prediction is not yet available because the current real dataset "
        "contains aggregate historical groups and does not contain size, room, tenure, "
        "car-park, or project-level attributes."
    )
    st.info("The disabled fields below show the planned property-level input design only.")

    st.subheader("Location")
    st.selectbox("State", [state.value for state in State], disabled=True, key="future_state")
    st.text_input("District", disabled=True, key="future_district")
    st.text_input("City or township", disabled=True)
    st.text_input("Project / development name", disabled=True)

    st.subheader("Property details")
    property_type = st.selectbox(
        "Property type",
        [
            "Terraced House",
            "Semi-Detached House",
            "Bungalow",
            "Townhouse",
            "Condominium",
            "Apartment",
            "Flat",
        ],
        key="future_property_type",
    )
    visible = individual_field_visibility(property_type)
    st.number_input("Built-up area (sq ft) — required", min_value=1.0, disabled=True)
    if visible["land_area_sqft"]:
        st.number_input("Land area (sq ft) — strongly recommended", min_value=1.0, disabled=True)
    else:
        st.caption("Land area: not normally applicable to a high-rise unit.")
    st.number_input("Bedrooms", min_value=0, disabled=True)
    st.number_input("Bathrooms", min_value=0, disabled=True)
    st.number_input("Car parks", min_value=0, disabled=True)
    if visible["storeys"]:
        st.number_input("Storeys", min_value=1, disabled=True)
    else:
        st.caption("Storeys: not normally applicable to an individual high-rise unit.")
    if visible["floor_level"]:
        st.number_input("Floor level", min_value=0, disabled=True)
    else:
        st.caption("Floor level: not applicable to landed property.")

    st.subheader("Ownership and condition")
    st.selectbox("Tenure", ["Freehold", "Leasehold", "Unknown"], disabled=True)
    st.selectbox(
        "Furnishing",
        ["Unfurnished", "Partly Furnished", "Fully Furnished", "Unknown"],
        disabled=True,
    )
    st.number_input("Completion year", min_value=1800, max_value=2026, disabled=True)
    st.number_input("Optional asking price (RM)", min_value=0.0, disabled=True)
    st.button("Property-level dataset required", disabled=True, width="stretch")
    st.error(
        "No estimate is produced in this mode. A licensed property-level dataset and validated "
        "property-level model are required first."
    )


st.set_page_config(page_title="Malaysia House Price Explorer", layout="centered")
st.title("Malaysia House Price Explorer")

if not CATALOG_PATH.is_file():
    st.error("The validated dataset catalog is missing from this deployment.")
    st.stop()

explorers = load_explorers()
mode = st.radio("Application mode", [MODE_HISTORICAL, MODE_INDIVIDUAL])

if mode == MODE_HISTORICAL:
    st.header("Malaysia Historical Residential Market Explorer")
    st.warning(
        "This tool estimates or displays the average completed transaction price for a district, "
        "property type, and quarter. It does not estimate the value of a specific property."
    )
    titles = {explorer.metadata.title: explorer for explorer in explorers}
    selected_title = st.selectbox("Historical aggregate dataset", tuple(titles))
    render_historical_explorer(titles[selected_title])
else:
    render_individual_pending()

st.divider()
st.caption(
    "Educational and informational use only. Not financial advice, an official valuation, "
    "a guaranteed market price, or an estimate of a specific property."
)
