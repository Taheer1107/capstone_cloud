import streamlit as st
from pathlib import Path
from utils.coverage_rules import RULES
from utils.pdf_generator import generate_admin_pdf
# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="Admin - Final Summary",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================
# LOAD CSS
# =====================================================

def load_css():

    css_path = (
        Path(__file__)
        .resolve()
        .parents[1]
        / "style.css"
    )

    if css_path.exists():

        with open(css_path, "r", encoding="utf-8") as f:

            st.markdown(
                f"<style>{f.read()}</style>",
                unsafe_allow_html=True
            )

load_css()

# =====================================================
# FLOW CHECK
# =====================================================

if "coverage" not in st.session_state:

    st.switch_page(
        "pages/admin_coverage_selection.py"
    )

coverage = st.session_state.coverage

patient = st.session_state.patient

gross = coverage["gross_bill"]

# =====================================================
# HEADER
# =====================================================

st.markdown(
    "<h1 style='margin:0;font-size:42px;'>Final Billing Summary</h1>",
    unsafe_allow_html=True
)

st.caption(
    "Complete billing overview"
)

st.progress(8 / 8)

st.caption("Step 8 of 8 - Final Summary")
# =====================================================
# PATIENT INFORMATION
# =====================================================

st.markdown("## Patient Information")

c1, c2, c3 = st.columns(3)

cards = [

    ("Patient ID", patient["hospital_id"]),

    ("Age", patient["age"]),

    ("Admission Date", patient["admission_date"]),

    ("Patient Name", patient["name"]),

    ("Gender", patient["gender"]),

    ("Discharge Date", patient["exit_date"])

]

for col, (title, value) in zip(
    [c1, c2, c3, c1, c2, c3],
    cards
):

    with col:

        st.markdown(
            f"""
            <div class="admin-payment-card">
                <div class="admin-payment-title">{title}</div>
                <div class="admin-payment-value">{value}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

# =====================================================
# GROSS BILL
# =====================================================

st.markdown("## Gross Bill Breakdown")
bill = st.session_state.coverage["gross_bill"]

items = [

    ("Procedure", bill["procedure"]),

    ("Diagnostics", bill["diagnostics"]),

    ("Medicines", bill["medicines"]),

    ("Consumables", bill["consumables"]),

    ("Room Charges", bill["room_charges"]),

    ("Doctor Charges", bill["doctor_charges"]),

    ("Gross Total", bill["total"])

]

rows = ""

for title, value in items:
    rows += f"""
    <div class="billing-row">
        <span>{title}</span>
        <span>₹{value:,.0f}</span>
    </div>
    """

st.markdown(
    f"""
    <div class="billing-card">
        {rows}
    </div>
    """,
    unsafe_allow_html=True,
)
# =====================================================
# COVERAGE WATERFALL
# =====================================================

st.markdown("<div class='main-card'>", unsafe_allow_html=True)

st.markdown("## Coverage Summary")

if len(coverage["waterfall"]) == 0:

    st.info("No healthcare coverage has been applied.")

else:
    for i, item in enumerate(coverage["waterfall"], start=1):

        with st.container(border=True):

            st.markdown(
                f"""
                <h2 style="
                    margin-bottom:4px;
                    font-size:34px;
                    font-weight:700;
                    color:#FFFFFF;
                ">
                    {i}. {item['scheme']}
                </h2>
                """,
                unsafe_allow_html=True,
            )
            st.caption("Coverage Applied")

            c1, c2, c3 = st.columns(3)

            with c1:
                st.markdown(
                    f"""
                    <div class="admin-payment-card">
                        <div class="admin-payment-title">
                            Eligible Amount
                        </div>
                        <div class="admin-payment-value">
                            ₹{item['eligible']:,.0f}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with c2:
                st.markdown(
                    f"""
                    <div class="admin-payment-card">
                        <div class="admin-payment-title">
                            Covered Amount
                        </div>
                        <div class="admin-payment-value" style="color:#86EFAC;">
                            ₹{item['covered']:,.0f}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with c3:
                st.markdown(
                    f"""
                    <div class="admin-payment-card">
                        <div class="admin-payment-title">
                            Remaining Bill
                        </div>
                        <div class="admin-payment-value" style="color:#60A5FA;">
                            ₹{item['remaining']:,.0f}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            st.markdown("<br>", unsafe_allow_html=True)
# =====================================================
# FINAL AMOUNT
# =====================================================

patient_amount = coverage["patient_pays"]

st.markdown("<div class='main-card'>", unsafe_allow_html=True)

if patient_amount == 0:

    st.success("Entire bill covered.")

    st.markdown(f"""
    <div style="
        background:#1E293B;
        border:1px solid #334155;
        border-left:5px solid #3B82F6;
        padding:30px;
        border-radius:14px;
        text-align:center;
        box-shadow:0 8px 20px rgba(0,0,0,.22);
    ">

    <h2 style="color:#CBD5E1;">
    Patient Pays
    </h2>

    <h1 style="color:#86EFAC;">
    ₹0
    </h1>

    </div>
    """,
    unsafe_allow_html=True)

else:

    st.warning("Partial coverage applied.")

    st.markdown(f"""
    <div style="
        background:#1E293B;
        border:1px solid #334155;
        border-left:5px solid #3B82F6;
        padding:30px;
        border-radius:14px;
        text-align:center;
        box-shadow:0 8px 20px rgba(0,0,0,.22);
    ">

    <h2 style="color:#CBD5E1;">
    Patient Pays
    </h2>

    <h1 style="color:#FCA5A5;">
    ₹{patient_amount:,.0f}
    </h1>

    </div>
    """,
    unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)
pdf_buffer = generate_admin_pdf(
    patient,
    coverage
)
# =====================================================
# NAVIGATION
# =====================================================
st.download_button(
    label="Download PDF Report",
    data=pdf_buffer,
    file_name="Hospital_Billing_Report.pdf",
    mime="application/pdf",
    use_container_width=True
)
