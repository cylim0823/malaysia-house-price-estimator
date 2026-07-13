"""Streamlit interface for the licensed JPPH historical-average model."""
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


MODEL_PATH = PROJECT_ROOT / "models" / "official_average_bundle.pkl"
DATASET_PATH = PROJECT_ROOT / "data" / "official" / "jpph_historical_average_prices.csv"
SOURCE_URL = "https://archive.data.gov.my/data/en_US/organization/jabatan-penilaian-dan-perkhidmatan-harta-jpph?license_id=cc-by"


@st.cache_resource
def load_bundle() -> OfficialAverageBundle:
    """Load the repository-owned model once per app process."""
    return OfficialAverageBundle.load(MODEL_PATH)


st.set_page_config(page_title="Malaysia House Price Explorer", page_icon="🏠", layout="centered")
st.title("Malaysia House Price Explorer")
st.info(
    "Real-data historical prototype: estimates are quarterly state-level averages, "
    "not prices for individual homes. The official dataset ends at 2018 Q2."
)

if not MODEL_PATH.is_file():
    st.error("The trained official-average model is missing from this deployment.")
    st.stop()

bundle = load_bundle()

with st.expander("Data source, training, and accuracy", expanded=True):
    st.markdown(
        "Source: [JPPH/NAPIC datasets in Malaysia's government open-data archive]"
        f"({SOURCE_URL}), published under Creative Commons Attribution."
    )
    st.write(
        "The model uses 2,090 published quarterly average-price observations covering "
        "2009 Q1 through 2018 Q2. It uses state, property type, year, and quarter only."
    )
    st.code("python scripts/train_official_averages.py", language="powershell")
    if DATASET_PATH.is_file():
        st.download_button(
            "Download normalized official dataset (CSV)",
            DATASET_PATH.read_bytes(),
            file_name="jpph_historical_average_prices.csv",
            mime="text/csv",
        )
    st.metric("Held-out test MAE", f"RM {bundle.test_metrics['mae_rm']:,.0f}")
    st.caption(
        "The final two quarters were held out for testing. This error describes historical "
        "state averages and must not be interpreted as individual-home accuracy."
    )

st.subheader("Historical average estimate")
state = st.selectbox("State or federal territory", bundle.states)
property_type = st.selectbox("Property category", bundle.property_types)
year = st.selectbox("Year", list(range(bundle.minimum_year, bundle.maximum_year + 1)), index=bundle.maximum_year-bundle.minimum_year)
quarter_options = [1, 2] if year == bundle.maximum_year else [1, 2, 3, 4]
quarter = st.selectbox("Quarter", quarter_options)
asking = st.number_input("Optional comparison price (RM; 0 means omitted)", 0.0, value=0.0, step=10000.0)

if st.button("Estimate published average", type="primary", use_container_width=True):
    try:
        result = bundle.predict(
            state=state,
            property_type=property_type,
            year=year,
            quarter=quarter,
        )
        st.subheader("Model result")
        st.metric("Estimated quarterly average", f"RM {result['estimate']:,.0f}")
        st.write(f"Indicative model range: **RM {result['lower']:,.0f} - RM {result['upper']:,.0f}**")
        if asking:
            if asking < result["lower"]:
                assessment = "Below estimated range"
            elif asking > result["upper"]:
                assessment = "Above estimated range"
            else:
                assessment = "Within estimated range"
            st.info(f"Comparison: {assessment}")
        st.warning(
            "Do not use this historical aggregate as a valuation of a specific property. "
            "It has no floor area, bedroom, condition, tenure, project, or exact-location input."
        )
    except ValueError as exc:
        st.error(str(exc))

st.divider()
st.caption(
    "Educational and informational use only. Not financial advice, an official valuation, "
    "or a guaranteed sale price. Dataset: JPPH/NAPIC historical averages, CC Attribution."
)
