import streamlit as st

from pathlib import Path
from utils.topup_rules import get_valid_topups

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


# ==============================
# PAGE
# ==============================

st.markdown(
    """
    <div class='hero-box'>
        <div>
            <div class='hero-title'>
                Coverage Selection
            </div>
            <div class='hero-sub'>
                Select the patient's primary healthcare coverage and optional top-up coverage.
</div>
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

if "admin_primary_scheme" not in st.session_state:
    st.session_state.admin_primary_scheme = "Private Insurance"
options = [
    "Private Insurance",
    "Government Healthcare",
    "Military / ECHS",
    "Self Pay"
]

row1_col1, row1_col2 = st.columns(2)
row2_col1, row2_col2 = st.columns(2)

button_positions = [
    (row1_col1, "Private Insurance"),
    (row1_col2, "Government Healthcare"),
    (row2_col1, "Military / ECHS"),
    (row2_col2, "Self Pay"),
]

for col, option in button_positions:

    with col:

        selected = (
            st.session_state.admin_primary_scheme == option
        )

        if st.button(
            ("✓ " if selected else "") + option,
            key=f"coverage_{option}",
            use_container_width=True,
            type="primary" if selected else "secondary",
        ):
            st.session_state.admin_primary_scheme = option
            st.rerun()

primary = st.session_state.admin_primary_scheme
st.markdown(
    "</div>",
    unsafe_allow_html=True
)
st.markdown(
    "<div class='main-card'>",
    unsafe_allow_html=True
)


st.markdown(
    "<div class='section-title'>ADDITIONAL TOP-UP COVERAGE</div>",
    unsafe_allow_html=True
)

if "admin_has_topup" not in st.session_state:
    st.session_state.admin_has_topup = "No"

st.write("Need Additional Top-up Coverage?")

col1, col2 = st.columns(2)

with col1:

    selected = st.session_state.admin_has_topup == "No"

    if st.button(
        ("✓ " if selected else "") + "No",
        key="topup_no",
        use_container_width=True,
        type="primary" if selected else "secondary"
    ):
        st.session_state.admin_has_topup = "No"
        st.rerun()

with col2:

    selected = st.session_state.admin_has_topup == "Yes"

    if st.button(
        ("✓ " if selected else "") + "Yes",
        key="topup_yes",
        use_container_width=True,
        type="primary" if selected else "secondary"
    ):
        st.session_state.admin_has_topup = "Yes"
        st.rerun()

has_topup = st.session_state.admin_has_topup
st.markdown(
    "<div style='height:2px'></div>",
    unsafe_allow_html=True
)

selected_topup = None


if has_topup == "Yes":

    valid_topups = get_valid_topups(primary)

    if len(valid_topups) == 0:

        st.info(
            "No valid top-up schemes are available for the selected primary scheme."
        )

    else:

        selected_topup = st.selectbox(
            "Top-up Scheme",
            valid_topups
        )
st.markdown(
    "<div style='height:12px'></div>",
    unsafe_allow_html=True
)
if st.button(
    "Continue to Coverage",
    use_container_width=True
):

    st.session_state.admin_primary_scheme = primary

    st.session_state.admin_has_topup = (
        has_topup == "Yes"
    )

    st.session_state.admin_topup_scheme = (
        selected_topup
        if has_topup == "Yes"
        else None
)

    if primary == "Private Insurance":

        st.switch_page(
            "pages/admin_private_insurance.py"
        )


    elif primary == "Government Healthcare":

        st.switch_page(
            "pages/admin_govt_employee.py"
        )


    elif primary == "Military / ECHS":

        st.switch_page(
            "pages/admin_military.py"
        )


    else:

        st.switch_page(
            "pages/admin_summary.py"
        )
st.markdown(
    "</div>",
    unsafe_allow_html=True
)