"""Streamlit explorers for licensed Malaysian aggregate property data."""
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
MODE_AGGREGATE = "Real aggregate transaction explorer"
MODE_REGIONAL = "Published regional price averages"


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


st.set_page_config(page_title="Malaysia House Price Explorer", layout="centered")
st.title("Malaysia House Price Explorer")
st.warning(
    "Historical aggregate explorer—not a specific-house estimator and not a current 2026 "
    "market valuation. The data has no property size, address, bedrooms, tenure, condition, "
    "project, or renovation features."
)

if not AGGREGATE_MODEL_PATH.is_file() or not REGIONAL_MODEL_PATH.is_file():
    st.error("A required trained aggregate model bundle is missing from this deployment.")
    st.stop()

aggregate_bundle, regional_bundle = load_models()
mode = st.radio("Explorer mode", [MODE_AGGREGATE, MODE_REGIONAL])

if mode == MODE_AGGREGATE:
    st.header("Real aggregate completed transactions")
    st.info(
        "Each row represents multiple completed transactions grouped by state, district, "
        "property type, year, and quarter. The data covers Penang in 2017 only."
    )
    state = st.selectbox("State", aggregate_bundle.states)
    district = st.selectbox("District", aggregate_bundle.districts(state))
    property_type = st.selectbox(
        "Property type",
        aggregate_bundle.property_types(state, district),
        format_func=property_type_label,
    )
    periods = aggregate_bundle.periods(state, district, property_type)
    years = sorted({year for year, _ in periods})
    year = st.selectbox("Year", years)
    quarters = [quarter for candidate_year, quarter in periods if candidate_year == year]
    quarter = st.selectbox("Quarter", quarters)

    if st.button("Show aggregate result", type="primary", width="stretch"):
        result = aggregate_bundle.predict(
            state=state,
            district=district,
            property_type=property_type,
            year=year,
            quarter=quarter,
        )
        st.subheader("Completed-transaction group result")
        st.metric(
            "Published average completed transaction price",
            f"RM {result['observed_average_price_rm']:,.0f}",
        )
        st.metric("Transactions represented", f"{result['transaction_count']:,}")
        st.write(f"Volume support: **{result['volume_support'].replace('_', ' ')}**")
        if not result["public_prediction_supported"]:
            st.warning(
                "This group has fewer than 20 transactions. It remains visible for historical "
                "transparency, but is excluded from public predictive support."
            )
        elif result["estimated_average_price_rm"] is not None:
            st.metric(
                "Provisional weighted-baseline estimate",
                f"RM {result['estimated_average_price_rm']:,.0f}",
            )
            st.caption(
                "Evaluated only by training on 2017 Q1–Q3 and testing on Q4. This is not "
                "multi-year or current-market validation."
            )
        else:
            st.info(
                "No predictive estimate is shown for Q1–Q3. These periods are the historical "
                "training portion of the provisional Q4 baseline evaluation."
            )
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
            "This estimate represents an average for a district-property-type-period group. "
            "It is not an estimate of a specific property's value."
        )
        st.caption(
            f"Dataset: {result['dataset_version']} · Baseline: {result['baseline_used']} · "
            f"Available range: {result['available_date_range']}"
        )

    with st.expander("Aggregate source, download, and evaluation"):
        st.markdown(
            f"Source: [Penang residential transaction counts]({PENANG_SOURCE_URL}) and the "
            "matching government transaction-value table. The archive catalogue marks both "
            "Creative Commons Attribution."
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

else:
    st.header("Published regional historical averages")
    st.info(
        "Terraced averages cover all 13 states plus Kuala Lumpur from 2016 Q1 to "
        "2018 Q2. High-rise coverage is partial. Putrajaya and Labuan are unsupported."
    )
    state = st.selectbox("State or federal territory", regional_bundle.states)
    area = st.selectbox("District / region", regional_bundle.areas_by_state[state])
    property_type = st.selectbox(
        "Property type", regional_bundle.property_types(state, area)
    )
    year = st.selectbox("Year", [2016, 2017, 2018], index=2)
    quarter_options = [1, 2] if year == 2018 else [1, 2, 3, 4]
    quarter = st.selectbox("Quarter", quarter_options)
    asking = st.number_input(
        "Optional comparison price (RM; 0 means omitted)",
        0.0,
        value=0.0,
        step=10000.0,
    )
    if st.button("Show regional benchmark", type="primary", width="stretch"):
        result = regional_bundle.predict(
            state=state,
            area=area,
            property_type=property_type,
            year=year,
            quarter=quarter,
        )
        st.subheader("Area-average result")
        st.metric("Published historical average", f"RM {result['observed_average']:,.0f}")
        st.metric("Historical model benchmark", f"RM {result['model_estimate']:,.0f}")
        st.write(
            f"Indicative historical range: **RM {result['lower']:,.0f} – "
            f"RM {result['upper']:,.0f}**"
        )
        if asking:
            st.info(f"Comparison: {assessment(asking, result['lower'], result['upper'])}")

    with st.expander("Regional sources and CSV download"):
        st.markdown(
            f"Sources: [JPPH terraced prices]({TERRACED_SOURCE_URL}) and "
            f"[JPPH high-rise prices]({HIGHRISE_SOURCE_URL})."
        )
        if REGIONAL_DATASET_PATH.is_file():
            st.download_button(
                "Download normalized regional area-price CSV",
                REGIONAL_DATASET_PATH.read_bytes(),
                file_name="regional_area_prices.csv",
                mime="text/csv",
            )

st.divider()
st.caption(
    "Educational and informational use only. Not financial advice, an official valuation, "
    "a guaranteed market price, or an estimate of a specific property."
)
