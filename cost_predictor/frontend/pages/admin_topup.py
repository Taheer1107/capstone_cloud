import streamlit as st
from pathlib import Path

from utils.coverage_engine import (
    apply_scheme,
    finish_coverage
)

from utils.topup_rules import (
    get_valid_topups
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


if "coverage" not in st.session_state:

    st.error(
        "Primary coverage must be completed first."
    )

    st.stop()



coverage = st.session_state.coverage



remaining = coverage["remaining_bill"]



# =====================================================
# HEADER
# =====================================================


st.markdown(
"""
<div class="hero-box">

<div class="hero-icon">
➕
</div>

<div>

<div class="hero-title">
Additional Top-up Coverage
</div>

<div class="hero-sub">
Apply secondary healthcare protection
</div>

</div>

</div>
""",
unsafe_allow_html=True
)




# =====================================================
# TOP-UP FORM
# =====================================================


st.markdown(
"<div class='main-card'>",
unsafe_allow_html=True
)



st.metric(
    "Remaining Hospital Bill",
    f"₹{remaining:,.0f}"
)



primary = st.session_state.get(
    "admin_primary_scheme",
    ""
)



available = get_valid_topups(
    primary
)



if len(available) == 0:

    st.info(
        "No compatible top-up schemes available."
    )

    selected = None


else:

    selected = st.selectbox(
        "Select Top-up Scheme",
        available
    )




st.markdown(
"</div>",
unsafe_allow_html=True
)




# =====================================================
# APPLY
# =====================================================






if st.button(
    "Continue ➜",
    use_container_width=True
):

    if selected is None:

        st.warning(
            "Please select a top-up scheme."
        )

    else:

        st.session_state.admin_topup_scheme = selected

        if selected in [
    "Government Healthcare",
    "CGHS / State Government Scheme"
]:

            st.switch_page(
                "pages/admin_govt_employee.py"
            )

        elif selected == "Military / ECHS":

            st.switch_page(
                "pages/admin_military.py"
            )

        elif selected == "Private Insurance":

            st.switch_page(
                "pages/admin_private_insurance.py"
            )
# =====================================================
# NAVIGATION
# =====================================================


st.divider()


col1,col2 = st.columns(2)



with col1:

    if st.button(
        "⬅ Previous",
        use_container_width=True
    ):

        st.switch_page(
            "pages/admin_coverage_selection.py"
        )



