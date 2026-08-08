import streamlit as st
from pathlib import Path
import sys

print("=" * 60)
print("Python executable:", sys.executable)
print("Python version:", sys.version)
print("=" * 60)
st.set_page_config(
    page_title="Healthcare Cost Predictor",
    layout="wide"
)

# -------------------------
# CSS
# -------------------------
css_path = Path(__file__).resolve().parent / "style.css"

if css_path.exists():
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(
            f"<style>{f.read()}</style>",
            unsafe_allow_html=True
        )

# -------------------------
# HEADER
# -------------------------

st.markdown("""
<div class='hero-box'>
<div class='hero-icon'>🏥</div>
<div>
<div class='hero-title'>
Healthcare Cost Predictor
</div>
<div class='hero-sub'>
Choose how you would like to continue
</div>
</div>
</div>
""", unsafe_allow_html=True)

st.write("")
st.write("")

left, right = st.columns(2)

# -------------------------
# USER
# -------------------------

with left:

    st.markdown("""
    <div class='lift-card'>
        <div class='card-icon'>👤</div>
        <div class='card-title'>
            Patient / User
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button(
        "Open User Portal",
        use_container_width=True
    ):
        st.switch_page("pages/user.py")

# -------------------------
# ADMIN
# -------------------------

with right:

    st.markdown("""
    <div class='lift-card'>
        <div class='card-icon'>🩺</div>
        <div class='card-title'>
            Hospital Admin
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button(
        "Open Admin Portal",
        use_container_width=True
    ):
        st.switch_page("pages/admin_patient.py")