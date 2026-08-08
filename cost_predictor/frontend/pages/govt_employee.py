import streamlit as st
from pathlib import Path
from utils.coverage_engine import (
    start_coverage,
    apply_scheme,
    finish_coverage,
)
from utils.validators import get_allowed_schemes


# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="Government Coverage",
    layout="wide",
    initial_sidebar_state="expanded"
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
# SESSION
# =====================================================
base_cost = float(st.session_state.get("base_cost", 0))

# -------------------------------------------------
# Check whether estimation has been completed
# -------------------------------------------------
estimation_ready = (
    st.session_state.get("ready", False)
    and base_cost > 0
)
allowed = get_allowed_schemes()

if "CGHS / State Government Scheme" not in allowed:
    
    st.error(
        "Government coverage is not part of your selected coverage."
    )

    if st.button("← Back to Coverage Selection"):
        st.switch_page("pages/coverage_selection.py")

    st.stop()
def money(x):
    return f"₹{x:,.0f}"

# =====================================================
# SIDEBAR
# =====================================================
with st.sidebar:

    allowed = get_allowed_schemes()

    st.markdown("""
    <div class='brand-box'>
        <div class='brand-main'>HealthCare</div>
        <div class='brand-sub'>Cost Estimator</div>
    </div>
    """, unsafe_allow_html=True)

    # Always visible
    if st.button("Main", use_container_width=True):
        st.switch_page("pages/user.py")

    if st.button("Coverage Selection", use_container_width=True):
        st.switch_page("pages/coverage_selection.py")

    # Only show selected schemes
    if "Private Insurance" in allowed:
        if st.button("Insurance", use_container_width=True):
            st.switch_page("pages/insurance.py")

    if "Military / ECHS" in allowed:
        if st.button("Military", use_container_width=True):
            st.switch_page("pages/military.py")

    if "CGHS / State Government Scheme" in allowed:
        if st.button("Govt Employee", use_container_width=True):
            st.rerun()

    # Always visible
    if st.button("Summary", use_container_width=True):
        st.switch_page("pages/summary.py")

# =====================================================
# TITLE
# =====================================================
st.markdown("""
<div class='hero-box'>
<div>
<div class='hero-title'>Government Employee Coverage</div>
<div class='hero-sub'>CGHS / Govt scheme payout calculator</div>
</div>
</div>
""", unsafe_allow_html=True)
# =====================================================
# VALIDATION
# =====================================================
if not estimation_ready:

    st.info(
        "Estimate the treatment cost first from the Main page before calculating government healthcare coverage."
    )

    if st.button(
        "Go to Main Page",
        use_container_width=True
    ):
        st.switch_page("pages/user.py")

    st.stop()
# =====================================================
# FORM
# =====================================================
st.markdown("<div class='main-card'>", unsafe_allow_html=True)

with st.form("govt_form"):

    c1, c2, c3 = st.columns(3)

    with c1:
        scheme = st.selectbox(
            "Scheme",
             ["CGHS", "State Govt"]
        )

    with c2:
        employee_type = st.selectbox(
            "Employee Type",
            ["Active", "Retired", "Dependent"]
        )

    with c3:
        empanelled = st.selectbox(
            "Empanelled Hospital",
            ["Yes", "No"]
        )

    d1, d2 = st.columns(2)

    with d1:
        room = st.selectbox(
            "Room Type",
            ["General", "Semi Private", "Private"]
        )

    with d2:
        emergency = st.selectbox(
            "Emergency",
            ["No", "Yes"]
        )

    submitted = st.form_submit_button(
        "Calculate Coverage",
        use_container_width=True
    )

st.markdown("</div>", unsafe_allow_html=True)

# =====================================================
# LOGIC
# =====================================================
if submitted:
    scheme_type = (
    "Primary"
    if st.session_state.get("primary_scheme")
    in [
        "Government Healthcare",
        "CGHS / State Government Scheme"
    ]
    else "Top-up"
)

    coverage = st.session_state.get("coverage")

    if scheme_type == "Top-up" and coverage is not None:
        calculation_base = coverage["remaining_bill"]
    else:
        calculation_base = base_cost

    # scheme base
    if scheme == "CGHS":
        cover = calculation_base * 0.92
        daily = 8000
    else:
        cover = calculation_base * 0.78
        daily = 6000

    # employee type
    if employee_type == "Retired":
        cover *= 0.92
    elif employee_type == "Dependent":
        cover *= 0.82

    # non empanelled hospital
    if empanelled == "No":
        cover *= 0.80

    # room deductions
    if room == "Private":
        cover *= 0.88
    elif room == "Semi Private":
        cover *= 0.95

    # emergency support
    cover += calculation_base * 0.04

    cover = min(calculation_base, cover)

    patient = max(calculation_base - cover, 0)

    # ==========================================
    # BUILD COVERAGE OBJECT
    # ==========================================
    if st.session_state.get("govt_done", False):
        st.warning("Government coverage has already been calculated.")
        st.stop()

    if "coverage" not in st.session_state:
        from utils.coverage_engine import start_patient_coverage
        start_patient_coverage(base_cost)

    scheme_type = (
    "Primary"
    if st.session_state.get("primary_scheme")
    in [
        "Government Healthcare",
        "CGHS / State Government Scheme"
    ]
    else "Top-up"
)


    apply_scheme(
    "CGHS / State Government Scheme",
    cover,
    scheme_type,
    calculation_base
)
    
    st.session_state.govt_cover = cover
    st.session_state.patient_pay = patient
    st.session_state.govt_done = True

    
    # =================================================
    # RESULT CARDS
    # =================================================
    a, b, c = st.columns(3)

    with a:
        st.markdown(f"""
        <div class='metric-card'>
        <div class='metric-title'>LIMIT / DAY</div>
        <div class='metric-value'>{money(daily)}</div>
        </div>
        """, unsafe_allow_html=True)

    with b:
        st.markdown(f"""
        <div class='metric-card metric-green'>
        <div class='metric-title'>GOVT PAYS</div>
        <div class='metric-value'>{money(cover)}</div>
        </div>
        """, unsafe_allow_html=True)

    with c:
        st.markdown(f"""
        <div class='metric-card metric-purple'>
        <div class='metric-title'>YOU PAY</div>
        <div class='metric-value'>{money(patient)}</div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")

    # =================================================
    # STATUS
    # =================================================
    if patient == 0:
        st.success("Fully approved under government scheme.")

    elif cover > base_cost * 0.55:
        st.warning("Partially approved due to room caps / scheme limits.")

    else:
        st.error("Low eligibility under selected scheme.")

    st.write("")

    if st.button("Continue", use_container_width=True):
        st.write("Primary:", repr(st.session_state.get("primary_scheme")))
        st.write("Has Topup:", repr(st.session_state.get("has_topup")))
        st.write("Topup:", repr(st.session_state.get("topup_scheme")))
        st.write("Coverage Selection:", st.session_state.get("coverage_selection"))

        if (
            st.session_state.get("has_topup", False)
            and st.session_state.get("topup_scheme") is not None
        ):

            topup = st.session_state["topup_scheme"]

            if topup == "CGHS / State Government Scheme":
                st.switch_page("pages/govt_employee.py")

            elif topup == "Private Insurance":
                st.switch_page("pages/insurance.py")

            elif topup == "Military / ECHS":
                st.switch_page("pages/military.py")

        else:

            st.switch_page("pages/summary.py")
