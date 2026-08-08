import streamlit as st
from utils.topup_rules import get_valid_topups
# =====================================================
# PAGE CONFIG
# =====================================================
from pathlib import Path

# ==============================
# CSS
# ==============================

def load_css():

    css_path = (
        Path(__file__)
        .resolve()
        .parents[1]
        / "style.css"
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

st.markdown(
    """
    <div class='hero-box'>
        <div>
            <div class='hero-title'>
                Coverage Selection
            </div>
            <div class='hero-sub'>
                Select your primary healthcare coverage and optional top-up coverage.
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)
st.markdown(
    "<div class='main-card'>",
    unsafe_allow_html=True
)

st.markdown(
    "<div class='section-title'>PRIMARY COVERAGE</div>",
    unsafe_allow_html=True
)
# =====================================================
# PRIMARY SCHEME
# =====================================================
if "primary_scheme" not in st.session_state:
    st.session_state.primary_scheme = "Private Insurance"

options = [
    "Private Insurance",
    "CGHS / State Government Scheme",
    "Military / ECHS",
    "Self Pay"
]

for option in options:

    selected = (
        st.session_state.primary_scheme == option
    )

    button_type = "primary" if selected else "secondary"

    if st.button(
        ("✓  " if selected else "") + option,
        key=f"coverage_{option}",
        use_container_width=True,
        type=button_type
    ):
        st.session_state.primary_scheme = option
        st.rerun()

primary = st.session_state.primary_scheme
st.markdown(
    "</div>",
    unsafe_allow_html=True
)
st.markdown(
    "<div class='main-card'>",
    unsafe_allow_html=True
)

st.markdown(
    "<div class='section-title'>OPTIONAL TOP-UP COVERAGE</div>",
    unsafe_allow_html=True
)

# =====================================================
# TOP-UP SELECTION
# =====================================================
if "has_topup" not in st.session_state:
    st.session_state.has_topup = "No"

st.write("Need Additional Top-up Coverage?")

col1, col2 = st.columns(2)

with col1:

    selected = st.session_state.has_topup == "No"

    if st.button(
        ("✓ " if selected else "") + "No",
        key="topup_no",
        use_container_width=True,
        type="primary" if selected else "secondary"
    ):
        st.session_state.has_topup = "No"
        st.rerun()

with col2:

    selected = st.session_state.has_topup == "Yes"

    if st.button(
        ("✓ " if selected else "") + "Yes",
        key="topup_yes",
        use_container_width=True,
        type="primary" if selected else "secondary"
    ):
        st.session_state.has_topup = "Yes"
        st.rerun()

has_topup = st.session_state.has_topup
st.markdown(
    "</div>",
    unsafe_allow_html=True
)

topup = None

if has_topup == "Yes":

    valid_topups = get_valid_topups(primary)

    if len(valid_topups) == 0:

        st.info("No valid top-up schemes are available for the selected primary scheme.")

    else:

        topup = st.selectbox(
            "Top-up Scheme",
            valid_topups,
            key="topup_scheme_select"
        )

# =====================================================
# VALIDATION
# =====================================================
if has_topup == "Yes" and not topup:
    st.warning("Please select a valid top-up scheme before continuing.")
    st.stop()

# =====================================================
# CONTINUE
# =====================================================
if st.button("Continue", use_container_width=True):

    # Individual values
    st.session_state.primary_scheme = primary
    st.session_state.has_topup = (has_topup == "Yes")
    st.session_state.topup_scheme = topup

    # Future-proof object (DB integration later)
    st.session_state.coverage_selection = {
        "primary": primary,
        "has_topup": has_topup == "Yes",
        "topup": topup
    }

    # Navigate to selected primary scheme
    if primary == "Private Insurance":
        st.switch_page("pages/insurance.py")

    elif primary == "Military / ECHS":
        st.switch_page("pages/military.py")

    elif primary == "CGHS / State Government Scheme":
        st.switch_page("pages/govt_employee.py")
    else:
        st.switch_page("pages/summary.py")