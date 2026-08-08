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
        "Generate bill before applying coverage."
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
Private Insurance Coverage
</div>

<div class="hero-sub">
Apply patient's primary insurance policy
</div>

</div>

</div>
""",
unsafe_allow_html=True
)
# =====================================================
# FORM
# =====================================================

st.markdown("<div class='main-card'>", unsafe_allow_html=True)
with st.form("admin_private_form"):

    # ---------- First Row ----------
    col1, col2, col3 = st.columns(3)

    with col1:
        provider = st.selectbox(
        "Insurance Provider",
        [
            "SBI",
            "HDFC Ergo",
            "ICICI Lombard"
        ],
    )

    with col2:
        days = st.number_input(
        "Hospital Stay (Days)",
        min_value=1,
        value=1,
    )

    with col3:
        sum_insured = st.number_input(
        "Sum Insured",
        min_value=0,
        value=500000,
        step=50000,
    )


    # ---------- Second Row ----------
    col4, col5 = st.columns(2)

    with col4:
        policy_age = st.selectbox(
            "Policy Age",
            [
                "<1 Year",
                "1-3 Years",
                "3+ Years"
            ],
        )

    with col5:
        claim_type = st.selectbox(
            "Claim Type",
            [
                "Cashless",
                "Reimbursement"
            ],
        )
    submitted = st.form_submit_button(
    "Calculate Coverage",
    use_container_width=True,
    type="primary",
    disabled=st.session_state.get("private_done", False)
)
    st.markdown("</div>", unsafe_allow_html=True)
# =====================================================
# CALCULATE
# =====================================================


if  submitted:
    "Calculate Coverage",
    use_container_width=True,
    type="primary",
    disabled=st.session_state.get("private_done", False)


    # start waterfall only once

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
    remaining = st.session_state.coverage["remaining_bill"]

    coverage_type = (
            "Top-up"
            if st.session_state.get("admin_topup_scheme")
            else "Primary"
        )

    calculation_base = (
            remaining
            if coverage_type == "Top-up"
            else st.session_state.coverage["gross_bill"]["total"]
        )




    bill = st.session_state.coverage["gross_bill"]

    rule = RULES["Private Insurance"]
    eligible_amount = sum(
    bill[component]
    for component in rule["covers"]
)

    cover = float(sum_insured)


    # loyalty

    if policy_age == "3+ Years":

        cover *= 1.05


    # reimbursement

    if claim_type == "Reimbursement":

        cover *= 0.95



    paid = min(
    eligible_amount,
    remaining,
    cover
)


    apply_scheme(
    "Private Insurance",
    paid,
    coverage_type,
    eligible_amount
)

    st.session_state.private_done = True
    st.session_state.private_result = {
    "bill": calculation_base,
    "eligible": eligible_amount,
    "paid": paid,
    "remaining": st.session_state.coverage["remaining_bill"]
}
    st.rerun()

st.markdown(
    "<div style='height:4px'></div>",
    unsafe_allow_html=True
)
if "private_result" in st.session_state:

    result = st.session_state.private_result
    st.success("Private insurance coverage applied successfully.")
    c1, c2, c3, c4 = st.columns(
    [1,1,1,1],
    gap="medium"
)

    cards = [
    ("Hospital Bill", result["bill"], ""),
    ("Eligible Amount", result["eligible"], ""),
    ("Insurance Pays", result["paid"], "metric-green"),
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



# =====================================================
# NAVIGATION
# =====================================================

st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
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

            topup = st.session_state.get(
                "admin_topup_scheme"
            )
            st.write("Has Topup:", st.session_state.get("admin_has_topup"))
            st.write("Topup Selected:", repr(st.session_state.get("admin_topup_scheme")))

            if st.session_state.get("admin_has_topup"):

                topup = st.session_state.get("admin_topup_scheme")

                if topup in [
    "Government Healthcare",
    "CGHS / State Government Scheme"
]:

                    st.switch_page(
                        "pages/admin_govt_employee.py"
                    )

                elif topup == "Military / ECHS":

                    st.switch_page(
                        "pages/admin_military.py"
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
