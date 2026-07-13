"""Streamlit interface for licensed Malaysian historical property data."""
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

from house_price_estimator.official_averages import OfficialAverageBundle
from house_price_estimator.penang_district import PenangDistrictBundle


STATE_MODEL_PATH = PROJECT_ROOT / "models" / "official_average_bundle.pkl"
PENANG_MODEL_PATH = PROJECT_ROOT / "models" / "penang_district_bundle.pkl"
STATE_DATASET_PATH = PROJECT_ROOT / "data" / "official" / "jpph_historical_average_prices.csv"
PENANG_DATASET_PATH = PROJECT_ROOT / "data" / "official" / "penang_district_transactions_2017.csv"
SOURCE_URL = "https://archive.data.gov.my/data/en_US/organization/jabatan-penilaian-dan-perkhidmatan-harta-jpph?license_id=cc-by"
PENANG_SOURCE_URL = "https://archive.data.gov.my/data/en_US/dataset/pecahan-bilangan-pindah-milik-harta-kediaman-mengikut-jenis-dan-daerah-di-pulau-pinang"


@st.cache_resource
def load_models() -> tuple[OfficialAverageBundle, PenangDistrictBundle]:
    """Load trusted repository-owned models once per app process."""
    return (
        OfficialAverageBundle.load(STATE_MODEL_PATH),
        PenangDistrictBundle.load(PENANG_MODEL_PATH),
    )


def assessment(asking: float, lower: float, upper: float) -> str:
    """Return the project's neutral asking-price comparison label."""
    if asking < lower:
        return "Below estimated range"
    if asking > upper:
        return "Above estimated range"
    return "Within estimated range"


st.set_page_config(page_title="Malaysia House Price Explorer", layout="centered")
st.title("Malaysia House Price Explorer")
st.info(
    "Real-data historical prototype. Penang has district-level completed-transaction "
    "benchmarks for 2017; other supported locations use state-level averages through 2018 Q2."
)

if not STATE_MODEL_PATH.is_file() or not PENANG_MODEL_PATH.is_file():
    st.error("A trained model bundle is missing from this deployment.")
    st.stop()

state_bundle, penang_bundle = load_models()

with st.expander("Data source, downloads, and accuracy"):
    st.markdown(
        f"Sources: [JPPH/NAPIC open-data catalogue]({SOURCE_URL}) and "
        f"[Penang district transaction counts]({PENANG_SOURCE_URL}). "
        "The government catalogue marks the datasets Creative Commons Attribution."
    )
    if PENANG_DATASET_PATH.is_file():
        st.download_button(
            "Download normalized Penang district CSV",
            PENANG_DATASET_PATH.read_bytes(),
            file_name="penang_district_transactions_2017.csv",
            mime="text/csv",
        )
    if STATE_DATASET_PATH.is_file():
        st.download_button(
            "Download normalized state-average CSV",
            STATE_DATASET_PATH.read_bytes(),
            file_name="jpph_historical_average_prices.csv",
            mime="text/csv",
        )
    st.write(
        f"Penang district model held-out Q4 MAE: RM {penang_bundle.test_metrics['mae_rm']:,.0f}. "
        f"State model held-out MAE: RM {state_bundle.test_metrics['mae_rm']:,.0f}."
    )
    st.caption(
        "These errors describe aggregate historical segments, not individual-home accuracy. "
        "The Penang model selected a district/property-type median because it beat ridge regression."
    )

st.subheader("Location and property")
state = st.selectbox("State or federal territory", state_bundle.states, index=state_bundle.states.index("Penang"))
asking = 0.0

if state == "Penang":
    district = st.selectbox("District / area", penang_bundle.districts)
    available_types = sorted({
        key.split("|", 2)[1]
        for key in penang_bundle.observations
        if key.startswith(f"{district}|")
    })
    property_type = st.selectbox("Property type", available_types)
    available_quarters = sorted({
        int(key.rsplit("|", 1)[1])
        for key in penang_bundle.observations
        if key.startswith(f"{district}|{property_type}|")
    })
    quarter = st.selectbox("2017 quarter", available_quarters)
    asking = st.number_input(
        "Optional comparison price (RM; 0 means omitted)", 0.0, value=0.0, step=10000.0
    )
    if st.button("Show Penang district benchmark", type="primary", use_container_width=True):
        result = penang_bundle.predict(
            district=district, property_type=property_type, quarter=quarter
        )
        st.subheader("Penang district result")
        st.metric("Published average completed transaction price", f"RM {result['observed_average']:,.0f}")
        st.write(f"Transactions behind this average: **{result['transaction_count']}**")
        st.metric("Model benchmark", f"RM {result['model_estimate']:,.0f}")
        st.write(f"Indicative model range: **RM {result['lower']:,.0f} - RM {result['upper']:,.0f}**")
        if result["transaction_count"] < 20:
            st.warning("Low transaction count: treat the published average cautiously.")
        if asking:
            st.info(f"Comparison: {assessment(asking, result['lower'], result['upper'])}")
        st.warning(
            "District detail is more useful than a state average, but this is still an aggregate. "
            "It does not include floor area, condition, tenure, project, street, or exact coordinates."
        )
else:
    st.warning("Licensed district-level price data has not yet been validated for this state.")
    property_type = st.selectbox("Property category", state_bundle.property_types)
    year = st.selectbox(
        "Year",
        list(range(state_bundle.minimum_year, state_bundle.maximum_year + 1)),
        index=state_bundle.maximum_year - state_bundle.minimum_year,
    )
    quarter_options = [1, 2] if year == state_bundle.maximum_year else [1, 2, 3, 4]
    quarter = st.selectbox("Quarter", quarter_options)
    asking = st.number_input(
        "Optional comparison price (RM; 0 means omitted)", 0.0, value=0.0, step=10000.0
    )
    if st.button("Estimate state average", type="primary", use_container_width=True):
        result = state_bundle.predict(
            state=state, property_type=property_type, year=year, quarter=quarter
        )
        st.subheader("Historical state result")
        st.metric("Estimated quarterly average", f"RM {result['estimate']:,.0f}")
        st.write(f"Indicative model range: **RM {result['lower']:,.0f} - RM {result['upper']:,.0f}**")
        if asking:
            st.info(f"Comparison: {assessment(asking, result['lower'], result['upper'])}")

st.divider()
st.caption(
    "Educational and informational use only. Not financial advice, an official valuation, "
    "or a guaranteed sale price. Source: JPPH/Penang government open data."
)
