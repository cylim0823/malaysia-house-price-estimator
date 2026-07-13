"""Local Streamlit demonstration UI; all prediction logic lives in the package."""
from pathlib import Path
try:
    import streamlit as st
except ImportError as exc:
    raise RuntimeError("Install the optional UI dependencies with: pip install -e .[ui]") from exc
from house_price_estimator.bundle import PredictionBundle
from house_price_estimator.prediction import PredictionService
from house_price_estimator.synthetic import SYNTHETIC_LABEL

st.set_page_config(page_title="Malaysia House Price Estimator",layout="centered")
st.title("Malaysia House Price Estimator")
st.warning("Synthetic demonstration only — not real Malaysian property-market data and not an official property valuation.")
model_path=Path(__file__).resolve().parents[1]/"models"/"demo_bundle.pkl"
if not model_path.exists():st.error("Generate the local demonstration model first: python -m house_price_estimator train-demo --output-dir models");st.stop()
bundle=PredictionBundle.load(model_path,trusted=True);service=PredictionService(bundle)
st.caption(f"Dataset: synthetic-demo-v1 · Price type: {bundle.supported_price_type} · Model: {bundle.model_version}")
state=st.selectbox("State or federal territory",bundle.supported_states);district=st.selectbox("District / fictional demo segment",bundle.supported_districts)
property_type=st.selectbox("Property type",bundle.supported_property_types);city=st.text_input("City or township");project=st.text_input("Project name")
built=st.number_input("Built-up area (sq ft)",100.0,100000.0,1000.0);land=st.number_input("Land area (sq ft, optional)",0.0,500000.0,0.0)
bedrooms=st.number_input("Bedrooms",0,20,3);additional=st.number_input("Additional bedrooms",0,10,0);bathrooms=st.number_input("Bathrooms",0,20,2);storeys=st.number_input("Storeys",1,10,1)
tenure=st.selectbox("Tenure",["Freehold","Leasehold","Unknown"]);furnishing=st.selectbox("Furnishing",["Unfurnished","Partly Furnished","Fully Furnished","Unknown"])
age=st.number_input("Property age (years)",0,200,10);asking=st.number_input("Optional asking price (RM; 0 means omitted)",0.0,value=0.0)
if st.button("Estimate"):
    try:
        result=service.predict({"state":state,"district":district,"city":city,"project_name":project,"property_type":property_type,"built_up_sqft":built,
          "land_area_sqft":land or None,"bedrooms":bedrooms,"additional_bedrooms":additional,"bathrooms":bathrooms,"storeys":storeys,"tenure":tenure,
          "furnishing":furnishing,"property_age_years":age,"record_year":2026,"record_month":7,"asking_price":asking or None})
        st.metric("Synthetic central estimate",f"RM {result.estimate:,.0f}");st.write(f"Estimated demonstration range: RM {result.lower:,.0f} – RM {result.upper:,.0f}")
        st.write(f"Price per square foot: RM {result.price_per_sqft:,.2f}");st.write(f"Support: {result.support_status}")
        if result.asking_price_assessment:st.write(result.asking_price_assessment)
        st.caption("Model: "+result.model_metadata["model_version"]);st.info(" ".join(result.limitations))
    except ValueError as exc:st.error(str(exc))
st.divider();st.caption("Educational and informational use only. Not financial advice, an official valuation, or a guaranteed sale price.")
