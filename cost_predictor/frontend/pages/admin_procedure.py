import streamlit as st
from pathlib import Path

from utils.admin_predictor import (
    procedure_options,
    get_specialty,
    estimate_cost
)

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="Admin - Procedure Cost",
    layout="wide",
    initial_sidebar_state="expanded"
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

    if css_path.exists():

        with open(css_path, "r", encoding="utf-8") as f:

            st.markdown(
                f"<style>{f.read()}</style>",
                unsafe_allow_html=True
            )

load_css()
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
# VALIDATION
# =====================================================

if "patient" not in st.session_state:

    st.warning("Complete Patient Details first.")

    st.switch_page("pages/admin_patient.py")

# =====================================================
# SESSION DEFAULTS
# =====================================================

patient = st.session_state.patient


age = patient["age"]
# =====================================================
# HEADER
# =====================================================

st.markdown(
    "<h1 style='margin:0;font-size:42px;'>Procedure Cost Prediction</h1>",
    unsafe_allow_html=True
)

st.caption(
    "Predict the base treatment cost before building the hospital bill"
)
# =====================================================
# PROGRESS
# =====================================================

st.progress(2 / 8)

st.caption(
    "Step 2 of 8 - Patient Details Complete - Procedure Cost"
)
# =====================================================
# FORM
# =====================================================

st.markdown("<div class='main-card'>", unsafe_allow_html=True)

with st.form("procedure_form"):

    col1, col2 = st.columns(2)

    with col1:

        procedure = st.selectbox(
        "Search Procedure",
        options=procedure_options,
        index=None,
        placeholder="Start typing to search procedures..."
        )

    with col2:

        if procedure:

            specialty = get_specialty(procedure)

        else:

            specialty = ""

        st.text_input(
            "Medical Specialty",
            value=specialty,
            disabled=True
        )

    col3, col4 = st.columns(2)

    with col3:

        city = st.selectbox(
            "City Tier",
            [
                "Tier-1",
                "Tier-2",
                "Tier-3"
            ]
        )

    with col4:

        hospital = st.selectbox(
            "Hospital Type",
            [
                "Private",
                "Government"
            ]
        )

    col5, col6 = st.columns(2)

    with col5:

        ward = st.selectbox(
            "Ward Type",
            [
                "general",
                "semi-private",
                "private",
                "ICU"
            ]
        )

    with col6:

        st.number_input(
            "Age",
            value=int(age),
            disabled=True
        )

    predict = st.form_submit_button(
        "Predict Procedure Cost",
        use_container_width=True
    )

st.markdown("</div>", unsafe_allow_html=True)
# =====================================================
# PREDICT COST
# =====================================================

if predict:

    # -----------------------------
    # Validation
    # -----------------------------
    if procedure == "":

        st.error(
            "Please select a procedure before predicting the treatment cost."
        )

    else:

        ok, data = estimate_cost(
            procedure,
            specialty,
            city,
            hospital,
            ward,
            age
        )

        if ok:

            cost = data["prediction"]["final_cost_inr"]

            # ----------------------------------------
            # RESET OLD BILL (NEW ADMIN CASE)
            # ----------------------------------------
            for key in [
                "diagnostics",
                "medicines",
                "consumables",
                "room",
                "doctor",
                "coverage"
            ]:

                if key in st.session_state:
                    del st.session_state[key]

            # ----------------------------------------
            # STORE PROCEDURE DETAILS
            # ----------------------------------------
            st.session_state.base_cost = cost

            st.session_state.procedure = procedure
            st.session_state.specialty = specialty
            st.session_state.city_tier = city
            st.session_state.hospital_type = hospital
            st.session_state.ward_type = ward

            st.session_state.ready = True

            # ----------------------------------------
            # RESULT CARD
            # ----------------------------------------
        
        else:

            st.error(
                "Unable to connect to the prediction service."
            )
            #PART-4
            # =====================================================
# SHOW PREDICTION IF AVAILABLE
# =====================================================

if st.session_state.get("ready", False):

    if "base_cost" in st.session_state:

        st.write("")

        st.markdown("## Procedure Details")

        row1_col1, row1_col2, row1_col3 = st.columns(3)

        with row1_col1:
            st.metric(
                "Predicted Procedure Cost",
                f"₹{format_inr(st.session_state.base_cost)}"
            )

        with row1_col2:
            st.metric(
                "Procedure",
                st.session_state.procedure
            )

        with row1_col3:
            st.metric(
                "Specialty",
                st.session_state.specialty
            )

        st.write("")

        row2_col1, row2_col2, row2_col3 = st.columns(3)

        with row2_col1:
            st.metric(
                "Hospital",
                st.session_state.hospital_type
            )

        with row2_col2:
            st.metric(
                "City",
                st.session_state.city_tier
            )

        with row2_col3:
            st.metric(
                "Ward",
                st.session_state.ward_type
            )
        st.success(
            "Procedure cost prediction completed successfully."
        )

        st.write("")

        left, right = st.columns(2)

        with left:

            if st.button(
                "Back to Patient Details",
                use_container_width=True
            ):

                st.switch_page(
                    "pages/admin_patient.py"
                )

        with right:

            if st.button(
                "Next Diagnostics",
                use_container_width=True
            ):

                st.switch_page(
                    "pages/admin_diagnostics.py"
                )
