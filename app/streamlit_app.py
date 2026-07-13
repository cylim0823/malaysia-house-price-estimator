"""Streamlit interface for licensed Malaysian area-level property data."""
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

from house_price_estimator.penang_district import PenangDistrictBundle
from house_price_estimator.regional_terraced import RegionalTerracedBundle


REGIONAL_MODEL_PATH = PROJECT_ROOT / "models" / "regional_terraced_bundle.pkl"
PENANG_MODEL_PATH = PROJECT_ROOT / "models" / "penang_district_bundle.pkl"
REGIONAL_DATASET_PATH = PROJECT_ROOT / "data" / "official" / "regional_terraced_area_prices.csv"
PENANG_DATASET_PATH = PROJECT_ROOT / "data" / "official" / "penang_district_transactions_2017.csv"
SOURCE_URL = "https://archive.data.gov.my/data/en_US/dataset/harga-rumah-teres-mengikut-daerahwilayahnegeri"
PENANG_SOURCE_URL = "https://archive.data.gov.my/data/en_US/dataset/pecahan-bilangan-pindah-milik-harta-kediaman-mengikut-jenis-dan-daerah-di-pulau-pinang"


@st.cache_resource
def load_models() -> tuple[RegionalTerracedBundle, PenangDistrictBundle]:
    """Load trusted repository-owned models once per app process."""
    return (
        RegionalTerracedBundle.load(REGIONAL_MODEL_PATH),
        PenangDistrictBundle.load(PENANG_MODEL_PATH),
    )


def assessment(asking: float, lower: float, upper: float) -> str:
    if asking < lower:
        return "Below estimated range"
    if asking > upper:
        return "Above estimated range"
    return "Within estimated range"


st.set_page_config(page_title="Malaysia House Price Explorer", layout="centered")
st.title("Malaysia House Price Explorer")
st.info(
    "Area-level historical prototype. Penang has five-district completed-transaction "
    "benchmarks for 2017. Other supported states have selected district/region terraced-house "
    "averages from 2016 Q1 through 2018 Q2."
)

if not REGIONAL_MODEL_PATH.is_file() or not PENANG_MODEL_PATH.is_file():
    st.error("A trained area-level model bundle is missing from this deployment.")
    st.stop()

regional_bundle, penang_bundle = load_models()

with st.expander("Data sources, CSV downloads, and accuracy"):
    st.markdown(
        f"Sources: [JPPH terraced prices by district/region]({SOURCE_URL}) and "
        f"[Penang district transaction counts]({PENANG_SOURCE_URL}). "
        "The government catalogue marks these datasets Creative Commons Attribution."
    )
    if REGIONAL_DATASET_PATH.is_file():
        st.download_button(
            "Download normalized regional terraced CSV",
            REGIONAL_DATASET_PATH.read_bytes(),
            file_name="regional_terraced_area_prices.csv",
            mime="text/csv",
        )
    if PENANG_DATASET_PATH.is_file():
        st.download_button(
            "Download normalized Penang district CSV",
            PENANG_DATASET_PATH.read_bytes(),
            file_name="penang_district_transactions_2017.csv",
            mime="text/csv",
        )
    st.write(
        f"Regional terraced held-out MAE: RM {regional_bundle.test_metrics['mae_rm']:,.0f}. "
        f"Penang district held-out MAE: RM {penang_bundle.test_metrics['mae_rm']:,.0f}."
    )
    st.caption(
        "These errors describe aggregate historical segments, not individual-home accuracy. "
        "Models were compared against simple area baselines before selection."
    )

st.subheader("Location and property")
state = st.selectbox(
    "State or federal territory",
    regional_bundle.states,
    index=regional_bundle.states.index("Penang"),
)

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
else:
    area = st.selectbox("District / region", regional_bundle.areas_by_state[state])
    st.text_input("Supported property type", "Terraced house", disabled=True)
    year = st.selectbox("Year", [2016, 2017, 2018], index=2)
    quarter_options = [1, 2] if year == 2018 else [1, 2, 3, 4]
    quarter = st.selectbox("Quarter", quarter_options)
    asking = st.number_input(
        "Optional comparison price (RM; 0 means omitted)", 0.0, value=0.0, step=10000.0
    )
    if st.button("Show regional terraced benchmark", type="primary", use_container_width=True):
        result = regional_bundle.predict(
            state=state, area=area, year=year, quarter=quarter
        )
        st.subheader("Area result")
        st.metric("Published terraced-house average", f"RM {result['observed_average']:,.0f}")
        st.metric("Model benchmark", f"RM {result['model_estimate']:,.0f}")
        st.write(f"Indicative model range: **RM {result['lower']:,.0f} - RM {result['upper']:,.0f}**")
        if asking:
            st.info(f"Comparison: {assessment(asking, result['lower'], result['upper'])}")

st.warning(
    "These are historical area averages, not individual-property valuations. The datasets "
    "do not include floor area, condition, tenure, project, street, or exact coordinates."
)
st.divider()
st.caption(
    "Educational and informational use only. Not financial advice, an official valuation, "
    "or a guaranteed sale price. Source: JPPH/Penang government open data."
)
