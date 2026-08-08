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
Military / ECHS Coverage
</div>

<div class="hero-sub">
Apply defence healthcare benefits
</div>

</div>

</div>
""",
unsafe_allow_html=True
)



# =====================================================
# INPUTS
# =====================================================

st.markdown(
"<div class='main-card'>",
unsafe_allow_html=True
)
with st.form("admin_military_form"):
# ---------- First Row ----------
    col1, col2, col3 = st.columns(3)

    with col1:
        status = st.selectbox(
            "Military Status",
            [
                "Serving",
                "Veteran",
                "Dependent"
            ]
        )

    with col2:
        echs_card = st.selectbox(
            "ECHS Card Available",
            [
                "Yes",
                "No"
            ]
        )

    with col3:
        emergency = st.selectbox(
            "Emergency Case",
            [
                "Yes",
                "No"
            ]
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ---------- Second Row ----------
    col4, col5 = st.columns(2)

    with col4:
        private_hospital = st.selectbox(
            "Private Hospital",
            [
                "Yes",
                "No"
            ]
        )

    with col5:
        if not st.session_state.get("admin_topup_scheme"):

            topup_available = st.selectbox(
                "Additional Top-up Available",
                [
                    "Available",
                    "Not Available"
                ]
            )

        else:

            topup_available = "Not Available"

    submitted = st.form_submit_button(
    "Calculate Military Coverage",
    use_container_width=True,
    disabled=st.session_state.get("military_done", False)
)
    st.markdown(
    "</div>",
    unsafe_allow_html=True
    )



# =====================================================
# CALCULATE
# =====================================================

if submitted:
    "Calculate Military Coverage",
    use_container_width=True,
    disabled=st.session_state.get("military_done", False)


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
    calculation_base = (
    remaining
    if st.session_state.get("admin_topup_scheme")
    else gross_total
)

    bill = st.session_state.coverage["gross_bill"]

    rule = RULES["Military / ECHS"]

    eligible_amount = sum(
        bill[item]
        for item in rule["covers"]
    )

    # Base eligibility

    if status == "Serving":

        cover = remaining * 0.95

        daily_limit = 9000


    elif status == "Veteran":

        cover = remaining * 0.82

        daily_limit = 7000


    else:

        cover = remaining * 0.70

        daily_limit = 5500



    # No ECHS card

    if echs_card == "No":

        cover *= 0.55



    # Private hospital deduction

    if private_hospital == "Yes":

        cover *= 0.88



    # Emergency benefit

    if emergency == "Yes":

        cover += remaining * 0.05



    # Extra top-up benefit

    if topup_available == "Available":

        cover += remaining * 0.10



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
    "Military / ECHS",
    cover,
    coverage_type,
    eligible_amount
)


    st.session_state.military_done = True
    st.session_state.military_result = {
    "bill": calculation_base,
    "eligible": eligible_amount,
    "paid": cover,
    "remaining": st.session_state.coverage["remaining_bill"]
}

    st.rerun()
st.markdown(
    "<div style='height:4px'></div>",
    unsafe_allow_html=True
)
if "military_result" in st.session_state:

    result = st.session_state.military_result

    st.success("Military coverage applied successfully.")

    c1, c2, c3, c4 = st.columns(4, gap="large")

    cards = [
    ("Hospital Bill", result["bill"], ""),
    ("Eligible Amount", result["eligible"], ""),
    ("Military Pays", result["paid"], "metric-green"),
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
