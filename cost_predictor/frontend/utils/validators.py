import streamlit as st

def get_allowed_schemes():

    allowed = []

    primary = st.session_state.get("primary_scheme")
    topup = st.session_state.get("topup_scheme")

    if primary:
        allowed.append(primary)

    if topup:
        allowed.append(topup)

    return allowed


def validate_page_access(required_scheme):

    allowed = get_allowed_schemes()

    if required_scheme not in allowed:

        st.error(
            f"{required_scheme} is not part of your selected coverage."
        )

        if st.button("← Back to Coverage Selection"):
            st.switch_page("pages/coverage_selection.py")

        st.stop()