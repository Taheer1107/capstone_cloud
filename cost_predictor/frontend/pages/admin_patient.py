import streamlit as st
from datetime import date
import re
from pathlib import Path

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="Admin - Patient Details",
    layout="wide"
)

# =====================================================
# LOAD CSS
# =====================================================
def load_css():
    css_path = Path(__file__).resolve().parents[1] / "style.css"
    if css_path.exists():
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# =====================================================
# SESSION INIT
# =====================================================
if "patient" not in st.session_state:
    st.session_state.patient = {}

# Prevent duplicate submissions
if "patient_locked" not in st.session_state:
    st.session_state.patient_locked = False

# =====================================================
# HEADER
# =====================================================
st.title("Patient Details (Admin)")
st.caption("Enter patient details to start billing workflow")

# =====================================================
# BLOCK IF ALREADY FILLED
# =====================================================
if st.session_state.patient_locked:
    st.success("Patient already saved. Proceed to next step.")
    if st.button("Go to Procedure Page"):
        st.switch_page("pages/admin_procedure.py")
    st.stop()

# =====================================================
# FORM
# =====================================================
with st.form("patient_form"):

    # Row 1
    col1, col2, col3 = st.columns(3)

    with col1:
        patient_id = st.text_input(
            "Hospital Patient ID",
            placeholder="P12345"
        )

    with col2:
        first_name = st.text_input(
            "First Name",
            placeholder="Rahul"
        )

    with col3:
        last_name = st.text_input(
            "Last Name",
            placeholder="Sharma"
        )

    # Row 2
    col4, spacer, col5 = st.columns([1, 0.06, 1])

    with col4:
        gender = st.selectbox(
            "Gender",
            ["Male", "Female"],
        )

    with spacer:
        st.empty()

    with col5:
        age = st.number_input(
            "Age",
            min_value=0,
            max_value=120,
            value=40,
        )


    date_col1, spacer2, date_col2 = st.columns([1, 0.06, 1])

    with date_col1:
        admission_date = st.date_input(
            "Admission Date",
            value=date.today()
        )
    with spacer2:
        st.empty()

    with date_col2:
        exit_date = st.date_input(
            "Exit Date",
            value=date.today()
        )


    submitted = st.form_submit_button("Save & Continue")

# =====================================================
# SAVE LOGIC
# =====================================================
if submitted:

        # -----------------------------------------
    # REQUIRED FIELDS
    # -----------------------------------------

    patient_id = patient_id.strip()
    first_name = first_name.strip()
    last_name = last_name.strip()

    if not patient_id:

        st.error("Patient ID is required.")
        st.stop()

    if not first_name:

        st.error("First Name is required.")
        st.stop()

    if not last_name:

        st.error("Last Name is required.")
        st.stop()

    # -----------------------------------------
    # PATIENT ID FORMAT
    # Example: P12345
    # -----------------------------------------

    if not re.fullmatch(r"P\d{5}", patient_id):

        st.error(
            "Patient ID must be in the format P12345."
        )

        st.stop()

    # -----------------------------------------
    # PATIENT NAME
    # Letters and spaces only
    # -----------------------------------------

    if not re.fullmatch(r"[A-Za-z ]+", first_name):

        st.error(
            "First name should contain only letters."
        )

        st.stop()

    if not re.fullmatch(r"[A-Za-z ]+", last_name):

        st.error(
            "Last name should contain only letters."
        )

        st.stop()

    # store patient data
    st.session_state.patient = {
        "hospital_id": patient_id,
        "first_name": first_name,
        "last_name": last_name,
        "name": f"{first_name} {last_name}",
        "age": age,
        "gender": gender,
        "admission_date": str(admission_date),
        "exit_date": str(exit_date),
        "topup_schemes": []
    }

    # lock page (prevents re-entry bug you were facing)
    st.session_state.patient_locked = True

    # reset downstream data (important fix)
    for key in [
    "procedure",
    "diagnostics",
    "medicines",
    "consumables",
    "coverage",
    "gross_bill",
    "private_done",
    "govt_done",
    "military_done",
    "admin_primary_scheme",
    "admin_topup_scheme",
    "admin_has_topup"
]:
        st.session_state.pop(key, None)

    st.success("Patient details saved successfully")

    st.switch_page("pages/admin_procedure.py")
