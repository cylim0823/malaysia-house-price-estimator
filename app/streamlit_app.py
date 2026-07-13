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

from house_price_estimator.aggregate_transactions import AggregateTransactionBundle
from house_price_estimator.regional_area import RegionalAreaBundle
from house_price_estimator.schema import State
from house_price_estimator.ui_contracts import (
    aggregate_prediction_payload,
    individual_field_visibility,
)


AGGREGATE_MODEL_PATH = PROJECT_ROOT / "models" / "aggregate_transaction_bundle.pkl"
REGIONAL_MODEL_PATH = PROJECT_ROOT / "models" / "regional_area_bundle.pkl"
AGGREGATE_DATASET_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "aggregate_transactions"
    / "penang_aggregate_transactions_v1.csv"
)
REGIONAL_DATASET_PATH = PROJECT_ROOT / "data" / "official" / "regional_area_prices.csv"
TERRACED_SOURCE_URL = "https://archive.data.gov.my/data/en_US/dataset/harga-rumah-teres-mengikut-daerahwilayahnegeri"
HIGHRISE_SOURCE_URL = "https://archive.data.gov.my/data/en_US/dataset/harga-unit-bertingkat-tinggi-mengikut-daerah-wilayah"
PENANG_SOURCE_URL = "https://archive.data.gov.my/data/en_US/dataset/pecahan-bilangan-pindah-milik-harta-kediaman-mengikut-jenis-dan-daerah-di-pulau-pinang"

MODE_HISTORICAL = "Historical Market Explorer"
MODE_INDIVIDUAL = "Individual Property Estimator — Data Pending"
SOURCE_PENANG = "Penang completed-transaction groups"
SOURCE_REGIONAL = "Published regional historical averages"


@st.cache_resource
def load_models() -> tuple[AggregateTransactionBundle, RegionalAreaBundle]:
    """Load trusted repository-owned bundles once per app process."""
    return (
        AggregateTransactionBundle.load(AGGREGATE_MODEL_PATH),
        RegionalAreaBundle.load(REGIONAL_MODEL_PATH),
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


def render_penang_explorer(aggregate_bundle: AggregateTransactionBundle) -> None:
    st.subheader("Penang district completed-transaction groups")
    st.caption("Validated coverage: Penang · five districts · 11 property groups · 2017 Q1–Q4")
    state = st.selectbox("State", aggregate_bundle.states)
    district = st.selectbox("District", aggregate_bundle.districts(state))
    property_type = st.selectbox(
        "Aggregate property category",
        aggregate_bundle.property_types(state, district),
        format_func=property_type_label,
    )
    periods = aggregate_bundle.periods(state, district, property_type)
    years = sorted({candidate_year for candidate_year, _ in periods})
    year = st.selectbox("Historical year", years)
    quarters = [quarter for candidate_year, quarter in periods if candidate_year == year]
    quarter = st.selectbox("Historical quarter", quarters)
    asking = st.number_input(
        "Optional comparison price (RM)",
        min_value=0.0,
        value=0.0,
        step=10_000.0,
        help="Leave at zero to omit. This does not turn the result into a property valuation.",
    )

    if st.button("Show historical quarterly average", type="primary", width="stretch"):
        payload = aggregate_prediction_payload(
            {
                "state": state,
                "district": district,
                "property_type": property_type,
                "year": year,
                "quarter": quarter,
            }
        )
        result = aggregate_bundle.predict(**payload)
        st.subheader("Historical quarterly group result")
        st.metric(
            "Recorded quarterly average completed transaction price",
            f"RM {result['observed_average_price_rm']:,.0f}",
        )
        st.metric("Completed transactions represented", f"{result['transaction_count']:,}")
        st.write(f"Transaction-volume support: **{result['volume_support'].replace('_', ' ')}**")
        st.write(
            f"**Selection:** {state} · {district} · {property_type_label(property_type)} · "
            f"{year} Q{quarter}"
        )
        if not result["public_prediction_supported"]:
            st.warning(
                "Fewer than 20 transactions support this group. It is retained as history but "
                "is excluded from public predictive support."
            )
        elif result["estimated_average_price_rm"] is not None:
            st.metric(
                "Provisional Q4 aggregate baseline",
                f"RM {result['estimated_average_price_rm']:,.0f}",
            )
            st.caption("Baseline: 2017 Q1–Q3 segment-weighted training; Q4 evaluation only.")
        else:
            st.info("Q1–Q3 are historical training periods; no predictive estimate is shown.")
        show_comparison(asking, result["observed_average_price_rm"])
        nearby = [
            {
                "period": f"{item['year']} Q{item['quarter']}",
                "average_price_rm": item["average_price_rm"],
                "transactions": item["transaction_count"],
                "volume_support": item["volume_support"],
            }
            for item in result["nearby_historical_quarters"]
        ]
        st.write("Nearby historical quarters")
        st.dataframe(nearby, width="stretch", hide_index=True)
        st.error(
            "This is a 2017 district/property-group average. It is not a current 2026 value "
            "and does not estimate a specific property."
        )
        st.caption(
            f"Dataset: {result['dataset_version']} · Baseline: {result['baseline_used']} · "
            f"Coverage: {result['available_date_range']}"
        )

    with st.expander("Data source, download, model, and limitations"):
        st.markdown(
            f"Source: [Penang residential transaction counts]({PENANG_SOURCE_URL}) and the "
            "matching government transaction-value table; both catalogue entries are labelled "
            "Creative Commons Attribution."
        )
        st.write(
            "Rows are aggregate district/property-type/quarter groups. They do not contain "
            "size, rooms, tenure, exact project, address, condition, or individual sale records."
        )
        if AGGREGATE_DATASET_PATH.is_file():
            st.download_button(
                "Download validated aggregate CSV",
                AGGREGATE_DATASET_PATH.read_bytes(),
                file_name="penang_aggregate_transactions_v1.csv",
                mime="text/csv",
            )
        metrics = aggregate_bundle.test_metrics
        st.write(
            f"Provisional Q4 unweighted MAE: RM {metrics['mae_rm']:,.0f}; "
            f"transaction-weighted MAE: RM {metrics['weighted_mae_rm']:,.0f}."
        )


def render_regional_explorer(regional_bundle: RegionalAreaBundle) -> None:
    st.subheader("Published regional quarterly averages")
    st.caption(
        "Validated coverage: 53 state-area combinations · terraced and partial high-rise · "
        "2016 Q1–2018 Q2"
    )
    state = st.selectbox("State or federal territory", regional_bundle.states)
    area = st.selectbox("District / published region", regional_bundle.areas_by_state[state])
    property_type = st.selectbox(
        "Aggregate property category", regional_bundle.property_types(state, area)
    )
    year = st.selectbox("Historical year", [2016, 2017, 2018], index=2)
    quarter_options = [1, 2] if year == 2018 else [1, 2, 3, 4]
    quarter = st.selectbox("Historical quarter", quarter_options)
    asking = st.number_input(
        "Optional comparison price (RM)", 0.0, value=0.0, step=10_000.0
    )
    if st.button("Show historical regional average", type="primary", width="stretch"):
        result = regional_bundle.predict(
            state=state,
            area=area,
            property_type=property_type,
            year=year,
            quarter=quarter,
        )
        st.subheader("Historical quarterly group result")
        st.metric("Published historical quarterly average", f"RM {result['observed_average']:,.0f}")
        st.metric("Historical aggregate baseline", f"RM {result['model_estimate']:,.0f}")
        st.write(f"Historical baseline range: **RM {result['lower']:,.0f} – RM {result['upper']:,.0f}**")
        st.write(f"**Selection:** {state} · {area} · {property_type} · {year} Q{quarter}")
        st.write("Transactions represented: **not published in this aggregate source**")
        st.write("Transaction-volume support: **not available**")
        if asking:
            st.info(f"Comparison: {assessment(asking, result['lower'], result['upper'])}")
        st.error(
            "These 2016–2018 published averages are historical regional benchmarks, not a "
            "current 2026 valuation or an estimate for a specific property."
        )

    with st.expander("Data sources, download, model, and limitations"):
        st.markdown(
            f"Sources: [JPPH terraced prices]({TERRACED_SOURCE_URL}) and "
            f"[JPPH high-rise prices]({HIGHRISE_SOURCE_URL}), labelled Creative Commons "
            "Attribution in the government archive."
        )
        st.write(
            "Terraced coverage spans all 13 states plus Kuala Lumpur. High-rise coverage is "
            "partial; Putrajaya and Labuan are unsupported. Rows are published area averages."
        )
        if REGIONAL_DATASET_PATH.is_file():
            st.download_button(
                "Download normalized regional aggregate CSV",
                REGIONAL_DATASET_PATH.read_bytes(),
                file_name="regional_area_prices.csv",
                mime="text/csv",
            )


def render_individual_pending() -> None:
    st.header("Individual Property Estimator — Data Pending")
    st.warning(
        "Individual-property prediction is not yet available because the current real dataset "
        "contains district-level quarterly aggregates and does not contain size, room, tenure, "
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

if not AGGREGATE_MODEL_PATH.is_file() or not REGIONAL_MODEL_PATH.is_file():
    st.error("A required trained aggregate model bundle is missing from this deployment.")
    st.stop()

aggregate_bundle, regional_bundle = load_models()
mode = st.radio("Application mode", [MODE_HISTORICAL, MODE_INDIVIDUAL])

if mode == MODE_HISTORICAL:
    st.header("Malaysia Historical Residential Market Explorer")
    st.warning(
        "This tool estimates or displays the average completed transaction price for a district, "
        "property type, and quarter. It does not estimate the value of a specific property."
    )
    source = st.selectbox("Historical aggregate dataset", [SOURCE_PENANG, SOURCE_REGIONAL])
    if source == SOURCE_PENANG:
        render_penang_explorer(aggregate_bundle)
    else:
        render_regional_explorer(regional_bundle)
else:
    render_individual_pending()

st.divider()
st.caption(
    "Educational and informational use only. Not financial advice, an official valuation, "
    "a guaranteed market price, or an estimate of a specific property."
)
