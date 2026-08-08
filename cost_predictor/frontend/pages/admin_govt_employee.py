import streamlit as st
from pathlib import Path
from utils.coverage_rules import RULES
from utils.coverage_engine import (
    start_coverage,
    apply_scheme,
    finish_coverage
)


# =====================================================
# CSS
# =====================================================

def load_css():

    css_path = (
        Path(__file__)
        .resolve()
        .parents[1]
        /
        "style.css"
    )

    if css_path.exists():

        with open(
            css_path,
            "r",
            encoding="utf-8"
        ) as f:

            st.markdown(
                f"<style>{f.read()}</style>",
                unsafe_allow_html=True
            )


load_css()



# =====================================================
# VALIDATION
# =====================================================

if "gross_bill" not in st.session_state:

    st.error(
        "Generate hospital bill first."
    )

    st.stop()



gross_total = st.session_state.gross_bill["total"]



# =====================================================
# HEADER
# =====================================================

st.markdown(
"""
<div class="hero-box">

<div>

<div class="hero-title">
Government Healthcare Coverage
</div>

<div class="hero-sub">
Apply CGHS / State Government benefits
</div>

</div>

</div>
""",
unsafe_allow_html=True
)



# =====================================================
# COVERAGE FORM
# =====================================================

st.markdown(
"<div class='main-card'>",
unsafe_allow_html=True
)
with st.form("admin_govt_form"):
# ---------- First Row ----------
    col1, col2, col3 = st.columns(3)

    with col1:
        scheme = st.selectbox(
            "Government Scheme",
            [
                "CGHS",
                "State Govt"
            ]
        )

    with col2:
        employee_type = st.selectbox(
            "Beneficiary Type",
            [
                "Serving Employee",
                "Retired Employee",
                "Dependent"
            ]
        )

    with col3:
        empanelled = st.selectbox(
            "Empanelled Hospital",
            [
                "Yes",
                "No"
            ]
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ---------- Second Row ----------
    col4, col5 = st.columns(2)

    with col4:
        room_type = st.selectbox(
            "Room Type",
            [
                "General",
                "Semi Private",
                "Private"
            ]
        )

    with col5:
        emergency = st.selectbox(
            "Emergency Case",
            [
                "Yes",
                "No"
            ]
        )

# =====================================================
# CALCULATE
# =====================================================


    submitted = st.form_submit_button(
        "Calculate Government Coverage",
        use_container_width=True,
        disabled=st.session_state.get("govt_done", False)
    )
st.markdown(
    "</div>",
    unsafe_allow_html=True
)
if submitted:
    if "coverage" not in st.session_state:
        procedure_cost = st.session_state.get("base_cost", 0)

        diagnostics_cost = st.session_state.get("diagnostics_total", 0)

        medicines_cost = st.session_state.get("medicines_total", 0)

        consumables_cost = st.session_state.get("consumables_total", 0)

        room_charges = st.session_state.get("room_charges", 0)

        doctor_charges = st.session_state.get("doctor_charges", 0)

        start_coverage(
        procedure_cost,
        diagnostics_cost,
        medicines_cost,
        consumables_cost,
        room_charges,
        doctor_charges
    )



    remaining = (
        st.session_state.coverage["remaining_bill"]
    )

    bill = st.session_state.coverage["gross_bill"]

    rule = RULES[scheme]

    eligible_amount = sum(
        bill[item]
        for item in rule["covers"]
    )


    # Base coverage

    if scheme == "CGHS":

        cover = remaining * 0.92

        daily_limit = 8000


    else:

        cover = remaining * 0.78

        daily_limit = 6000



    # Beneficiary adjustment

    if employee_type == "Retired Employee":

        cover *= 0.92


    elif employee_type == "Dependent":

        cover *= 0.82



    # Hospital adjustment

    if empanelled == "No":

        cover *= 0.80



    # Room adjustment

    if room_type == "Private":

        cover *= 0.88


    elif room_type == "Semi Private":

        cover *= 0.95



    # Emergency benefit

    if emergency == "Yes":

        cover += remaining * 0.04



    cover = min(
    eligible_amount,
    remaining,
    cover
)



    coverage_type = (
    "Top-up"
    if st.session_state.get("admin_topup_scheme")
    else "Primary"
    )

    apply_scheme(
    scheme,
    cover,
    coverage_type,
    eligible_amount
)



    st.session_state.govt_done = True
    st.session_state.govt_result = {
    "bill": remaining if coverage_type == "Top-up" else gross_total,
    "eligible": eligible_amount,
    "paid": cover,
    "remaining": st.session_state.coverage["remaining_bill"]
}
    st.rerun()

if "govt_result" in st.session_state:

    result = st.session_state.govt_result

    st.success("Government coverage applied successfully.")
    c1, c2, c3, c4 = st.columns(
    [1, 1, 1, 1],
    gap="medium"
)
    cards = [
    ("Hospital Bill", result["bill"], ""),
    ("Eligible Amount", result["eligible"], ""),
    ("CGHS / Govt Pays", result["paid"], "metric-green"),
    ("Remaining Bill", result["remaining"], "metric-purple"),
]

    for col, (title, value, extra_class) in zip([c1, c2, c3, c4], cards):
        with col:
            st.markdown(
                f"""
                <div class="metric-card {extra_class}">
                    <div class="metric-title">{title}</div>
                    <div class="metric-value">₹{value:,.0f}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    st.markdown(
    "<div style='height:18px'></div>",
    unsafe_allow_html=True
)
# =====================================================
# NAVIGATION
# =====================================================


col1,col2 = st.columns(2)



with col1:

    if st.button(
        "Previous",
        use_container_width=True
    ):

        st.switch_page(
    "pages/admin_coverage_selection.py"
)


with col2:

    if st.button(
        "Continue",
        use_container_width=True
    ):

        if st.session_state.get("admin_has_topup"):

            topup = st.session_state.get("admin_topup_scheme")

            if topup == "Private Insurance":

                st.switch_page(
                    "pages/admin_private_insurance.py"
                )

            else:

                finish_coverage()

                st.switch_page(
                    "pages/admin_summary.py"
                )

        else:

            finish_coverage()

            st.switch_page(
                "pages/admin_summary.py"
            )
