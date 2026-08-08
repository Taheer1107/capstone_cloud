import streamlit as st
from pathlib import Path
from datetime import datetime, date

from utils.config import ROOM_RATES

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="Admin - Room & Doctor Charges",
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

# =====================================================
# FLOW VALIDATION
# =====================================================

if "patient" not in st.session_state:

    st.switch_page("pages/admin_patient.py")

if "base_cost" not in st.session_state:

    st.switch_page("pages/admin_procedure.py")

# =====================================================
# READ SESSION
# =====================================================

patient = st.session_state.patient

procedure_cost = st.session_state.get(
    "base_cost",
    0
)

diagnostics_cost = st.session_state.get(
    "diagnostics_total",
    0
)

medicines_cost = st.session_state.get(
    "medicines_total",
    0
)

consumables_cost = st.session_state.get(
    "consumables_total",
    0
)

hospital_type = st.session_state.get(
    "hospital_type",
    "Private"
)

city_tier = st.session_state.get(
    "city_tier",
    "Tier-2"
)

ward_type = st.session_state.get(
    "ward_type",
    "General"
)


admission_date = datetime.strptime(
    patient["admission_date"],
    "%Y-%m-%d"
).date()
today = date.today()

exit_date = datetime.strptime(
    patient["exit_date"],
    "%Y-%m-%d"
).date()

days = max(
    1,
    (exit_date - admission_date).days + 1
)

# =====================================================
# HEADER
# =====================================================
st.markdown(
    """
    <h1 style='margin:0;font-size:42px;'>Doctor & Consultation Charges</h1>
    """,
    unsafe_allow_html=True
)

st.progress(6/8)

st.caption(
    "Step 6 of 8 - Doctor & Consultation Charges"
)

# =====================================================
# AUTO INFORMATION
# 

# =====================================================
# ROOM CHARGES
# =====================================================
WARD_MAP = {
    "general": "General",
    "semi-private": "Semi-Private",
    "semiprivate": "Semi-Private",
    "private": "Private",
    "icu": "ICU"
}

ward_type = WARD_MAP.get(
    str(ward_type).strip().lower(),
    ward_type
)

room_rate = ROOM_RATES[
    hospital_type
][
    city_tier
][
    ward_type
]

room_total = room_rate * days
# =====================================================
# DOCTOR CHARGES
# =====================================================

st.markdown("<div class='main-card'>", unsafe_allow_html=True)


d1, d2 = st.columns(2)

with d1:

    consultant_fee = st.number_input(
        "Consultant Fee",
        min_value=0.0,
        value=0.0,
        step=500.0
    )

    surgeon_fee = st.number_input(
        "Surgeon Fee",
        min_value=0.0,
        value=0.0,
        step=1000.0
    )

with d2:

    anaesthetist_fee = st.number_input(
        "Anaesthetist Fee",
        min_value=0.0,
        value=0.0,
        step=500.0
    )

doctor_total = (
    consultant_fee +
    surgeon_fee +
    anaesthetist_fee
)

st.markdown("</div>", unsafe_allow_html=True)

# =====================================================
# GST
# =====================================================
gross_bill = (
    procedure_cost +
    diagnostics_cost +
    medicines_cost +
    consumables_cost +
    room_total +
    doctor_total
)
# =====================================================
# BILL BREAKDOWN
# =====================================================

st.markdown("<div class='main-card'>", unsafe_allow_html=True)

st.markdown("## Current Bill")

running_total = (
    procedure_cost +
    diagnostics_cost +
    medicines_cost +
    consumables_cost
)

c1, c2, c3 = st.columns(3)

cards = [
    ("Running Total", running_total),
    ("Consultation Charges", doctor_total),
    ("Current Total", gross_bill),
]

for col, (title, value) in zip([c1, c2, c3], cards):

    with col:

        st.markdown(f"""
<div class="summary-card">
<div class="summary-title">{title}</div>
<div class="summary-value">₹{value:,.0f}</div>
</div>
""", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)
# =====================================================
# SAVE TO SESSION
# =====================================================

st.session_state.room = {

    "type": ward_type,

    "rate_per_day": room_rate,

    "days": days,

    "subtotal": room_total

}

st.session_state.doctor = {

    "consultant": consultant_fee,

    "surgeon": surgeon_fee,

    "anaesthetist": anaesthetist_fee,

    "subtotal": doctor_total

}

# =====================================================
# BUILD GROSS BILL
# =====================================================

gross_bill_object = {

    "procedure": procedure_cost,

    "diagnostics": diagnostics_cost,

    "medicines": medicines_cost,

    "consumables": consumables_cost,

    "room_charges": room_total,

    "doctor_charges": doctor_total,

    "total": gross_bill

}

# Save for Coverage Page
st.session_state.gross_bill = gross_bill_object

# =====================================================
# NAVIGATION
# =====================================================

left, right = st.columns(2)

with left:

    if st.button(
        "Previous",
        use_container_width=True
    ):

        st.switch_page(
            "pages/admin_consumables.py"
        )

with right:

    if st.button(
        "Next Coverage",
        use_container_width=True
    ):

        # Reset any old coverage calculation
        if "coverage" in st.session_state:
            del st.session_state.coverage

        from utils.coverage_engine import start_coverage

        coverage = start_coverage(
        procedure_cost,
        diagnostics_cost,
        medicines_cost,
        consumables_cost,
        room_total,
        doctor_total,
    )


        st.session_state.coverage = coverage

        st.switch_page(
            "pages/admin_coverage_selection.py"
        )
