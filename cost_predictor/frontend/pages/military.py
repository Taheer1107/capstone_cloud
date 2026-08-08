import streamlit as st
from pathlib import Path


from utils.validators import (
    validate_page_access,
    get_allowed_schemes
)
from utils.coverage_engine import (
    start_coverage,
    apply_scheme,
    finish_coverage
)



# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="Military Coverage",
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
validate_page_access("Military / ECHS")

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

    # Show only selected schemes
    if "Private Insurance" in allowed:
        if st.button("Insurance", use_container_width=True):
            st.switch_page("pages/insurance.py")

    if "Military / ECHS" in allowed:
        if st.button("Military", use_container_width=True):
            st.rerun()

    if "CGHS" in allowed or "State Govt" in allowed:
        if st.button("Govt Employee", use_container_width=True):
            st.switch_page("pages/govt_employee.py")

    # Always visible
    if st.button("Summary", use_container_width=True):
        st.switch_page("pages/summary.py")
# =====================================================
# TITLE
# =====================================================
st.markdown("""
<div class='hero-box'>
<div>
<div class='hero-title'>Military / Defence Coverage</div>
<div class='hero-sub'>ECHS / service benefits payout calculator</div>
</div>
</div>
""", unsafe_allow_html=True)
# =====================================================
# VALIDATION
# =====================================================
if not estimation_ready:

    st.info(
        "Estimate the treatment cost first from the Main page before calculating military or ECHS coverage."
    )

    if st.button("Go to Main Page", use_container_width=True):
        st.switch_page("pages/user.py")

    st.stop()
# =====================================================
# FORM
# =====================================================
st.markdown("<div class='main-card'>", unsafe_allow_html=True)

with st.form("military_form"):

    c1, c2, c3 = st.columns(3)

    with c1:
        status = st.selectbox(
            "Status",
            ["Serving", "Veteran", "Dependent"]
        )

    with c2:
        echs = st.selectbox(
            "ECHS Card",
            ["Yes", "No"]
        )

    with c3:
        emergency = st.selectbox(
            "Emergency Case",
            ["No", "Yes"]
        )

    d1, d2 = st.columns(2)

    with d1:
        private_hospital = st.selectbox(
            "Private Hospital",
            ["No", "Yes"]
        )

    with d2:
        topup = st.selectbox(
            "Top-Up Insurance",
            ["None", "Available"]
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
    if st.session_state.get("primary_scheme") == "Military / ECHS"
    else "Top-up"
)

    coverage = st.session_state.get("coverage")

    if scheme_type == "Top-up" and coverage is not None:
        calculation_base = coverage["remaining_bill"]
    else:
        calculation_base = base_cost

    # base eligibility
    if status == "Serving":
        cover = calculation_base * 0.95
        daily = 9000
    elif status == "Veteran":
        cover = calculation_base * 0.82
        daily = 7000
    else:
        cover = calculation_base * 0.70
        daily = 5500

    # no echs
    if echs == "No":
        cover *= 0.55

    # private hospital deductions
    if private_hospital == "Yes":
        cover *= 0.88

    # emergency bonus
    if emergency == "Yes":
        cover += calculation_base * 0.05

    # topup
    if topup == "Available":
        cover += calculation_base * 0.10

    cover = min(calculation_base, cover)
    patient = max(calculation_base - cover, 0)

    # =====================================================
        # ADD TO COVERAGE WATERFALL
        # =====================================================

    # =====================================================
# ADD TO COVERAGE WATERFALL
# =====================================================
    if st.session_state.get("military_done", False):
        st.warning("Military coverage has already been calculated.")
        st.stop()

    if "coverage" not in st.session_state:
        from utils.coverage_engine import start_patient_coverage
        start_patient_coverage(base_cost)
    scheme_type = (
        "Primary"
        if st.session_state.get("primary_scheme") == "Military / ECHS"
        else "Top-up"
    )


    apply_scheme(
    "Military / ECHS",
    cover,
    scheme_type,
    calculation_base
)

    coverage = finish_coverage()
    st.session_state.coverage = coverage
    st.session_state.military_cover = cover
    st.session_state.patient_pay = patient
    st.session_state.military_done = True
# Temporary (until full migration)
    
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
        <div class='metric-title'>MILITARY PAYS</div>
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
        st.success("Fully approved under ECHS / Defence coverage.")

    elif cover > base_cost * 0.55:
        st.warning("Partially approved due to caps / private hospital deductions.")

    else:
        st.error("Low eligibility. Large patient payable remains.")

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

            if topup in [
    "Government Healthcare",
    "CGHS / State Government Scheme"
]:
                st.switch_page("pages/govt_employee.py")

            elif topup == "Private Insurance":
                st.switch_page("pages/insurance.py")

            elif topup == "Military / ECHS":
                st.switch_page("pages/military.py")

        else:

            st.switch_page("pages/summary.py")
