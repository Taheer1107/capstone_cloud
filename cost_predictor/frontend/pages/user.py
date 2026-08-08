import streamlit as st
import requests
from pathlib import Path
import pandas as pd
import plotly.express as px
from utils.coverage_engine import start_patient_coverage
from utils.normalizer import (
    normalize_procedure,
    normalize_specialty,
    normalize_city,
    normalize_hospital,
    normalize_ward
)

# =====================================================
# CONFIG
# =====================================================
st.set_page_config(
    page_title="Healthcare Cost Estimator",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_URL = "http://127.0.0.1:8002/predict"
# =====================================================
# LOAD PROCEDURE LOOKUP
# =====================================================

LOOKUP_PATH = (
    Path(__file__)
    .resolve()
    .parents[2]
    / "datasets"
    / "PROCEDURE_LOOKUP.csv"
)

lookup_df = pd.read_csv(LOOKUP_PATH)

procedure_options = sorted(
    lookup_df["procedure"].unique().tolist()
)

# =====================================================
# LOAD CSS
# =====================================================
def load_css():
    css_path = (
        Path(__file__)
        .resolve()
        .parents[1]
        / "style.css"
    )

    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(
            f"<style>{f.read()}</style>",
            unsafe_allow_html=True
        )

load_css()
#HELPER - INDIAN CURRENCY FORMAT
def format_inr(number):

    number = int(round(number))

    s = str(number)

    if len(s) <= 3:
        return s

    last3 = s[-3:]
    rest = s[:-3]

    parts = []

    while len(rest) > 2:
        parts.insert(0, rest[-2:])
        rest = rest[:-2]

    if rest:
        parts.insert(0, rest)

    return ",".join(parts + [last3])
# =====================================================
# SESSION DEFAULTS
# =====================================================
if "ready" not in st.session_state:
    st.session_state.ready = False

# =====================================================
# BACKEND
# =====================================================
def estimate_cost(payload):
    try:
        r = requests.get(API_URL, params=payload, timeout=20)
        if r.status_code == 200:
            return True, r.json()
        return False, "Backend error"
    except:
        return False, "Backend not running"

# =====================================================
# SIDEBAR
# =====================================================
with st.sidebar:

    st.markdown("""
    <div class='brand-box'>
        <div class='brand-main'>HealthCare</div>
        <div class='brand-sub'>Cost Estimator</div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Main", use_container_width=True):
        st.rerun()

    if st.button("Insurance", use_container_width=True):
        st.switch_page("pages/insurance.py")

    if st.button("Military", use_container_width=True):
        st.switch_page("pages/military.py")

    if st.button("Government Employee", use_container_width=True):
        st.switch_page("pages/govt_employee.py")

    if st.button("Summary", use_container_width=True):
        st.switch_page("pages/summary.py")

# =====================================================
# HEADER
# =====================================================
st.markdown("""
<div class='hero-box'>
    <div>
        <div class='hero-title'>Healthcare Cost Estimation</div>
        <div class='hero-sub'>Estimate your treatment cost in a few simple steps</div>
    </div>
</div>
""", unsafe_allow_html=True)

# =====================================================
# FORM
# =====================================================
st.markdown("## Treatment Details")

with st.form("main_form"):

    a, b = st.columns(2)

    with a:

        procedure = st.selectbox(
            "Procedure",
            [""] + procedure_options
        )

    with b:

        if procedure:

            specialty = lookup_df.loc[
                lookup_df["procedure"] == procedure,
                "specialty"
            ].iloc[0]

        else:
            specialty = ""

        st.text_input(
            "Medical Specialty",
            value=specialty,
            disabled=True
        )

    c, d = st.columns(2) 

    with c:
        city = st.selectbox(
            "City Tier",
            ["Tier-1", "Tier-2", "Tier-3"]
        )

    with d:
        hospital = st.selectbox(
            "Hospital Type",
            ["Private", "Government"]
        )

    e, f = st.columns(2)

    with e:
        ward = st.selectbox(
            "Ward Type",
            ["general", "semi-private", "private"]
        )

    with f:
        age = st.number_input(
            "Age",
            1, 100, 40
        )

    submit = st.form_submit_button(
        "Estimate Treatment Cost",
        use_container_width=True
    )


# =====================================================
# SUBMIT
# =====================================================
if submit:

    # -----------------------------------------
    # Validation
    # -----------------------------------------
    if procedure == "":

        st.error(
            "Please select a treatment procedure before estimating the treatment cost."
        )

    else:

        payload = {
            "procedure": normalize_procedure(procedure),
            "specialty": normalize_specialty(specialty),
            "hospital_type": normalize_hospital(hospital),
            "city_tier": normalize_city(city),
            "age": age,
            "ward_type": normalize_ward(ward),
            "pmjay_flag": 0
        }

        ok, data = estimate_cost(payload)

        if ok:

            cost = data["prediction"]["final_cost_inr"]
            st.session_state.explanation = data.get(
            "explanation",
            {}
        )

# -------------------------------------------------
# RESET OLD COVERAGE (IMPORTANT FIX)
# -------------------------------------------------
            if "coverage" in st.session_state:
                del st.session_state.coverage

            
            st.session_state.base_cost = cost
                        # START COVERAGE ONLY ONCE PER CASE
            from utils.coverage_engine import start_coverage

            start_patient_coverage(cost)
            st.session_state.ready = True

            st.session_state.procedure = payload["procedure"]
            st.session_state.specialty = payload["specialty"]
            st.session_state.city_tier = payload["city_tier"]
            st.session_state.hospital_type = payload["hospital_type"]
            st.session_state.ward_type = payload["ward_type"]
            st.session_state.age = age
            st.success("Treatment cost estimated successfully.")
            st.markdown(
                f"""
                <div class='estimated-cost-card'>
                    <div class='estimated-cost-label'>Estimated Procedure Cost</div>
                    <div class='estimated-cost-value'>₹{format_inr(cost)}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        else:

            st.error(
                "Unable to estimate the treatment cost. Please ensure the backend service is running and try again."
            )
# =====================================================
# EXPLAINABLE AI
# =====================================================

if st.button(
    "Continue to Coverage Selection",
    use_container_width=True
):
    st.switch_page("pages/coverage_selection.py")
