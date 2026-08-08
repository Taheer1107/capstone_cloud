import streamlit as st
from pathlib import Path
from utils.coverage_engine import (
    start_coverage,
    apply_scheme,
    finish_coverage
)

from utils.validators import (
    validate_page_access,
    get_allowed_schemes
)
from utils.validators import validate_page_access


# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="Insurance Coverage",
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
procedure = st.session_state.get("procedure", "").lower()

# -------------------------------------------------
# Check whether estimation has been completed
# -------------------------------------------------
estimation_ready = (
    st.session_state.get("ready", False)
    and base_cost > 0
)
validate_page_access("Private Insurance")

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

    # Always available
    if st.button("Main", use_container_width=True):
        st.switch_page("pages/user.py")
    if st.button("Coverage Selection", use_container_width=True):
        st.switch_page("pages/coverage_selection.py")

    # Only show if selected
    if "Private Insurance" in allowed:
        if st.button("Insurance", use_container_width=True):
            st.rerun()

    if "Military / ECHS" in allowed:
        if st.button("Military", use_container_width=True):
            st.switch_page("pages/military.py")

    if "CGHS / State Government Scheme" in allowed:
        if st.button("Govt Employee", use_container_width=True):
            st.switch_page("pages/govt_employee.py")

    # Always available
    if st.button("Summary", use_container_width=True):
        st.switch_page("pages/summary.py")

# =====================================================
# TITLE
# =====================================================
st.markdown("""
<div class='hero-box'>
<div>
<div class='hero-title'>Insurance Coverage</div>
<div class='hero-sub'>Calculate insurer payout and your payable amount</div>
</div>
</div>
""", unsafe_allow_html=True)

# =====================================================
# VALIDATION
# =====================================================
if not estimation_ready:

    st.info(
        "Estimate the treatment cost first from the Main page before calculating insurance coverage."
    )

    if st.button("Go to Main Page", use_container_width=True):
        st.switch_page("pages/user.py")

    st.stop()

# =====================================================
# FORM
# =====================================================
st.markdown("<div class='main-card'>", unsafe_allow_html=True)

with st.form("insurance_form"):

    c1, c2, c3 = st.columns(3)

    with c1:
        provider = st.selectbox(
            "Insurance Provider",
            ["SBI", "HDFC Ergo", "ICICI Lombard"]
        )

    with c2:
        days = st.number_input(
            "Days Stayed",
            min_value=1,
            max_value=30,
            value=3
        )

    with c3:
        sum_insured = st.selectbox(
            "Sum Insured",
            [300000, 500000, 1000000]
        )

    d1, d2 = st.columns(2)

    with d1:
        policy_age = st.selectbox(
            "Policy Age",
            ["<1 Year", "1-3 Years", "3+ Years"]
        )

    with d2:
        claim_type = st.selectbox(
            "Claim Type",
            ["Cashless", "Reimbursement"]
        )

    submitted = st.form_submit_button(
        "Calculate Coverage",
        use_container_width=True
    )

st.markdown("</div>", unsafe_allow_html=True)

if submitted:
    # ==========================================
    # PROCEDURE EXCLUSION CHECK
    # ==========================================

    excluded = [
        "botox",
        "cosmetic",
        "hair transplant",
        "liposuction",
        "ivf",
        "fertility",
        "lasik",
        "braces",
    ]

    if any(word in procedure for word in excluded):

        cover = 0
        patient = base_cost
        reason = "Not covered by insurance policy (cosmetic / excluded procedure)."

    else:
        scheme_type = (
        "Primary"
        if st.session_state.get("primary_scheme") == "Private Insurance"
        else "Top-up"
    )

        coverage = st.session_state.get("coverage")

        if scheme_type == "Top-up" and coverage is not None:
            calculation_base = coverage["remaining_bill"]
        else:
            calculation_base = base_cost
        # normal insurance logic
        if provider == "SBI":
            room_limit = 5000
        elif provider == "HDFC Ergo":
            room_limit = 7000
        elif provider == "ICICI Lombard":
            room_limit = 9000
        else:
            room_limit = 10000

        max_cover = float(sum_insured)

        if policy_age == "3+ Years":
            max_cover *= 1.05

        if claim_type == "Reimbursement":
            max_cover *= 0.95

        allowed_room_total = room_limit * days

        if calculation_base > allowed_room_total * 2:
            cover = max_cover * 0.72
            reason = "Partial approval due to room caps / limits."
        else:
            cover = max_cover * 0.92
            reason = "Fully approved under policy coverage."

        cover = min(calculation_base, cover)
        patient = max(calculation_base - cover, 0)
        #new add ons
        # =====================================================
        # BUILD COVERAGE OBJECT
        # =====================================================

        

        scheme_type = (
            "Primary"
            if st.session_state.get("primary_scheme") == "Private Insurance"
            else "Top-up"
        )
        # Don't apply insurance twice
        if st.session_state.get("insurance_done", False):
            st.warning("Insurance has already been calculated.")
            st.stop()
        if "coverage" not in st.session_state:
            from utils.coverage_engine import start_patient_coverage
            start_patient_coverage(base_cost)

        apply_scheme(
        "Private Insurance",
        cover,
        scheme_type,
        calculation_base
    )

        if not (
            st.session_state.get("has_topup", False)
            and st.session_state.get("topup_scheme") is not None
        ):
            coverage = finish_coverage()

        st.session_state.insurance_done = True

        # Store insurance details for summary page
        st.session_state.insurance_cover = cover
        st.session_state.patient_pay = patient
        st.session_state.sum_insured = sum_insured
        st.session_state.insurance_provider = provider

        # =================================================
        # RESULT TOP CARDS
        # =================================================
        a, b, c = st.columns(3)

        with a:
            st.markdown(f"""
            <div class='metric-card'>
            <div class='metric-title'>LIMIT / DAY</div>
            <div class='metric-value'>{money(room_limit)}</div>
            </div>
            """, unsafe_allow_html=True)

        with b:
            st.markdown(f"""
            <div class='metric-card metric-green'>
            <div class='metric-title'>INSURANCE PAYS</div>
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
        # STATUS MESSAGE
        # =================================================
        if patient == 0:
            st.success("Fully approved under policy coverage.")

        elif cover > 0:
            st.warning(reason)

        else:
            st.error("Not covered by policy.")

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

                elif topup == "Military / ECHS":
                    st.switch_page("pages/military.py")

                elif topup == "Private Insurance":
                    st.switch_page("pages/insurance.py")

            else:

                st.switch_page("pages/summary.py")
