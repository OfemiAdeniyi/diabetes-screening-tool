import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000/screen-diabetes"

# -------------------------------
# Page Setup
# -------------------------------
st.set_page_config(page_title="Diabetes Risk Screening", layout="centered")

st.markdown("## 🩺 Diabetes Risk Screening Tool")
st.markdown(
    """
    **Purpose:** Early identification of individuals who may be at risk of diabetes.  
    This tool is designed for **community health centers and medical outreaches**.
    
    ⚠️ *This is a screening tool, not a diagnostic test.*
    """
)

st.divider()


# Initialize session state defaults
defaults = {
    "age": 0,
    "gender": "Male",
    "height": 0.0,
    "weight": 0.0,
    "smoking_history": "never",
    "hypertension": "No",
    "heart_disease": "No",
    "screening_result": None
}

for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# Reset button
if st.button("🔄 Reset Form"):
    for key in defaults:
        st.session_state[key] = defaults[key]

# Form
age = st.number_input("Age (years)", value=st.session_state.age, key="age")
gender = st.selectbox("Gender", ["Male","Female","Other"], index=["Male","Female","Other"].index(st.session_state.gender), key="gender")
height = st.number_input("Height (m)", value=st.session_state.height, step=0.01, key="height")
weight = st.number_input("Weight (kg)", value=st.session_state.weight, step=0.5, key="weight")
smoking_history = st.selectbox("Smoking History", ["never","former","current","ever","not current"], index=["never","former","current","ever","not current"].index(st.session_state.smoking_history), key="smoking_history")
hypertension = st.radio("Hypertension?", ["No","Yes"], index=["No","Yes"].index(st.session_state.hypertension), key="hypertension")
heart_disease = st.radio("Heart Disease?", ["No","Yes"], index=["No","Yes"].index(st.session_state.heart_disease), key="heart_disease")

# Compute BMI
bmi = round(weight / (height ** 2), 2) if height > 0 else 0
st.info(f"📊 Calculated BMI: **{bmi} kg/m²**")

# Screening
if st.button("🔍 Screen for Diabetes Risk"):
    if age == 0 or height == 0 or weight == 0:
        st.warning("⚠️ Please fill age, height, and weight before screening.")
    else:
        payload = {
            "age": age,
            "gender": gender,
            "height": height,
            "weight": weight,
            "smoking_history": smoking_history,
            "hypertension": hypertension,
            "heart_disease": heart_disease
        }
        try:
            response = requests.post(API_URL, json=payload)
            result = response.json()
            if response.status_code == 200:
                st.session_state.screening_result = result
                st.subheader("📊 Screening Result")
                st.write(f"**Diabetes Risk Probability:** {result['diabetes_risk_probability']}")
                st.write(f"**Screening Result:** {result['screening_result']}")
                st.write(f"**Threshold Used:** {result['screening_threshold']}")
            else:
                st.error(f"API Error: {response.status_code}")
        except requests.exceptions.ConnectionError:
            st.error("❌ Could not connect to the FastAPI server.")

