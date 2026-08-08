import streamlit as st
import pandas as pd
import requests
from pathlib import Path

# =====================================================
# CONFIG
# =====================================================
st.set_page_config(
    page_title="Admin Billing Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_URL = "http://127.0.0.1:8002/predict"

# =====================================================
# LOAD CSS (same style as your app)
# =====================================================
def load_css():
    css_path = Path(__file__).resolve().parents[1] / "style.css"
    if css_path.exists():
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# =====================================================
# SESSION STATE INIT
# =====================================================
if "admin_diag" not in st.session_state:
    st.session_state.admin_diag = []

if "admin_med" not in st.session_state:
    st.session_state.admin_med = []

if "admin_con" not in st.session_state:
    st.session_state.admin_con = []

# =====================================================
# LOAD DATA
# =====================================================
diag_df = pd.read_csv("../datasets/diagnostics_clean_final.csv")
med_df = pd.read_csv("../datasets/medicine_catalog.csv")
con_df = pd.read_csv("../datasets/consumable_catalog.csv")

# =====================================================
# HEADER
# =====================================================
st.markdown("""
<div class='hero-box'>
<div>
<div class='hero-title'>Admin Billing Dashboard</div>
<div class='hero-sub'>Hospital cost construction system</div>
</div>
</div>
""", unsafe_allow_html=True)

# =====================================================
# PATIENT INFO
# =====================================================
st.markdown("## Patient Info")

col1, col2, col3 = st.columns(3)

with col1:
    patient_id = st.text_input("Patient ID")

with col2:
    patient_name = st.text_input("Patient Name")

with col3:
    age = st.number_input("Age", 1, 100, 40)

st.divider()

# =====================================================
# PROCEDURE (ML COST)
# =====================================================
st.markdown("## Procedure Cost (ML Model)")

procedure = st.text_input("Enter Procedure Name")

if st.button("Predict Procedure Cost"):
    payload = {
        "procedure": procedure,
        "specialty": "General",
        "hospital_type": "Private",
        "city_tier": "Tier-1",
        "age": age,
        "ward_type": "general",
        "pmjay_flag": 0
    }

    try:
        r = requests.get(API_URL, params=payload)
        if r.status_code == 200:
            cost = r.json()["prediction"]["final_cost_inr"]
            st.session_state.admin_procedure_cost = cost
            st.success(f"Procedure Cost: ₹{cost:,.0f}")
        else:
            st.error("Prediction failed")
    except:
        st.error("Backend not running")

st.divider()

# =====================================================
# DIAGNOSTICS
# =====================================================
st.markdown("## Diagnostics")

search = st.text_input("Search Diagnostics")

filtered = diag_df[diag_df["procedure_name"].str.contains(search, case=False, na=False)] if search else diag_df.head(10)

for idx, row in filtered.iterrows():

    c1, c2, c3 = st.columns(3)

    with c1:
        st.write(row["procedure_name"])

    with c2:
        st.write(f"₹ {row['rate']}")

    with c3:
        if st.button("Add", key=f"d_{idx}"):
            st.session_state.admin_diag.append(row['rate'])

st.divider()

# =====================================================
# MEDICINES
# =====================================================
st.markdown("## Medicines")

search = st.text_input("Search Medicines")

filtered = med_df[med_df["medicine_name"].str.contains(search, case=False, na=False)] if search else med_df.head(10)

for idx, row in filtered.iterrows():

    c1, c2, c3 = st.columns(3)

    with c1:
        st.write(row["medicine_name"])

    with c2:
        st.write(f"₹ {row['unit_price']}")

    with c3:
        if st.button("Add", key=f"m_{idx}"):
            st.session_state.admin_med.append(row['unit_price'])

st.divider()

# =====================================================
# CONSUMABLES
# =====================================================
st.markdown("## Consumables")

search = st.text_input("Search Consumables")

filtered = con_df[con_df["item_name"].str.contains(search, case=False, na=False)] if search else con_df.head(10)

for idx, row in filtered.iterrows():

    c1, c2, c3 = st.columns(3)

    with c1:
        st.write(row["item_name"])

    with c2:
        st.write(f"₹ {row['unit_price']}")

    with c3:
        if st.button("Add", key=f"c_{idx}"):
            st.session_state.admin_con.append(row['unit_price'])

st.divider()

# =====================================================
# BILL CALCULATION
# =====================================================
st.markdown("## Live Bill Summary")

diag_total = sum(st.session_state.admin_diag)
med_total = sum(st.session_state.admin_med)
con_total = sum(st.session_state.admin_con)

procedure_cost = st.session_state.get("admin_procedure_cost", 0)

grand_total = diag_total + med_total + con_total + procedure_cost

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Procedure", f"₹{procedure_cost:,.0f}")

with col2:
    st.metric("Diagnostics", f"₹{diag_total:,.0f}")

with col3:
    st.metric("Medicines", f"₹{med_total:,.0f}")

with col4:
    st.metric("Consumables", f"₹{con_total:,.0f}")

st.subheader(f"Grand Total: ₹ {grand_total:,.0f}")

# =====================================================
# ACTIONS
# =====================================================
col1, col2 = st.columns(2)

with col1:
    if st.button("Reset Bill"):
        st.session_state.admin_diag = []
        st.session_state.admin_med = []
        st.session_state.admin_con = []
        st.session_state.admin_procedure_cost = 0
        st.rerun()

with col2:
    if st.button("Generate Final Bill"):

        st.session_state.admin_bill_generated = True

        st.success(
            "Bill generated successfully"
        )

        st.switch_page(
            "pages/admin_coverage_selection.py"
        )
