import streamlit as st
import pandas as pd
from pathlib import Path

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="Admin - Diagnostics",
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
# FLOW VALIDATION
# =====================================================

if "patient" not in st.session_state:

    st.warning("Complete Patient Details first.")

    st.switch_page("pages/admin_patient.py")

if "base_cost" not in st.session_state:

    st.warning("Predict the procedure cost first.")

    st.switch_page("pages/admin_procedure.py")

# =====================================================
# LOAD DATASET
# =====================================================

DATA_PATH = (
    Path(__file__)
    .resolve()
    .parents[2]
    / "datasets"
    / "diagnostics_clean_final.csv"
)

diag_df = pd.read_csv(DATA_PATH)

diag_df = diag_df.sort_values("procedure_name")

# =====================================================
# SESSION
# =====================================================

if "diagnostics" not in st.session_state:

    st.session_state.diagnostics = []

# =====================================================
# HEADER
# =====================================================

st.markdown(
    "<h1 style='margin:0;font-size:42px;'>Diagnostics</h1>",
    unsafe_allow_html=True
)

st.caption(
    "Search and add diagnostic investigations"
)

st.progress(3/8)

st.caption("Step 3 of 8 - Diagnostics")
# =====================================================
# SEARCH DIAGNOSTICS
# =====================================================
st.markdown(
    """
    <h2 style='margin-bottom:6px;'>Search Diagnostic Investigation</h2>
    """,
    unsafe_allow_html=True
)

st.caption(
    "Type part of the diagnostic name. The closest matches will appear automatically."
)

# =====================================================
# SEARCH BAR
# =====================================================


selected_test = st.selectbox(
    "Search Diagnostic Investigation",
    options=sorted(
        diag_df["procedure_name"]
        .dropna()
        .unique()
    ),
    index=None,
    placeholder="Start typing to search diagnostics..."
)

# =====================================================
# ADD SELECTED DIAGNOSTIC
# =====================================================

if selected_test:

    row = diag_df[
        diag_df["procedure_name"] == selected_test
    ].iloc[0]

    if st.button(
        "Add Diagnostic",
        use_container_width=True
    ):

        found = False

        for item in st.session_state.diagnostics:

            if item["procedure_name"] == selected_test:

                item["qty"] += 1
                item["total"] = (
                    item["qty"] *
                    item["rate"]
                )

                found = True
                break

        if not found:

            st.session_state.diagnostics.append({

                "procedure_name": row["procedure_name"],

                "cghs_code": row["cghs_code"],

                "rate": float(row["rate"]),

                "qty": 1,

                "total": float(row["rate"])

            })

        st.rerun()

st.markdown("</div>", unsafe_allow_html=True)


# =====================================================
# SELECTED DIAGNOSTICS
# =====================================================

st.write("")


st.markdown("## Selected Diagnostics")

subtotal = 0

if len(st.session_state.diagnostics) == 0:

    st.info(
        "No diagnostic investigations have been added yet."
    )

else:

    h1, h2, h3, h4, h5 = st.columns([5,2,2,2,1])

    h1.markdown("**Diagnostic**")
    h2.markdown("**Qty**")
    h3.markdown("**Rate**")
    h4.markdown("**Total**")
    h5.markdown("**Remove**")

    st.divider()

    for i, item in enumerate(st.session_state.diagnostics):

        c1, c2, c3, c4, c5 = st.columns([5,2,2,2,1])

        # ---------------------------------------
        # NAME
        # ---------------------------------------

        c1.write(item["procedure_name"])

        # ---------------------------------------
        # QUANTITY INPUT
        # ---------------------------------------

        qcol, qspace = c2.columns([1, 1])

        new_qty = qcol.number_input(
            "Qty",
            min_value=1,
            max_value=99,
            value=item["qty"],
            key=f"qty_diag_{i}",
            label_visibility="collapsed"
        )

        if new_qty != item["qty"]:
            item["qty"] = new_qty
            item["total"] = item["qty"] * item["rate"]
            st.rerun()

        # ---------------------------------------
        # RATE
        # ---------------------------------------

        c3.write(
            f"₹{item['rate']:,.0f}"
        )

        # ---------------------------------------
        # TOTAL
        # ---------------------------------------

        c4.write(
            f"₹{item['rate']:,.0f}"
        )

        subtotal += item["total"]

        # ---------------------------------------
        # REMOVE
        # ---------------------------------------

        if c5.button(
            "Remove",
            key=f"remove_diag_{i}"
        ):

            st.session_state.diagnostics.pop(i)

            st.rerun()

st.markdown("</div>", unsafe_allow_html=True)


st.session_state.diagnostics_total = subtotal
# =====================================================
# LIVE BILL SUMMARY
# =====================================================

st.write("")

procedure_cost = st.session_state.get(
    "base_cost",
    0
)

diagnostics_cost = subtotal
running_total = procedure_cost
gross_bill = (
    procedure_cost +
    diagnostics_cost
)



st.session_state.diagnostics_total = diagnostics_cost
st.session_state.current_gross_bill = gross_bill

st.markdown("## Current Bill")

c1, c2, c3 = st.columns(3)

with c1:

    st.markdown(
        f"""
        <div class='estimated-cost-card'>
            <div class='estimated-cost-label'>Running Total</div>
            <div class='estimated-cost-value'>&#8377;{running_total:,.0f}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with c2:

    st.markdown(
        f"""
        <div class='estimated-cost-card'>
            <div class='estimated-cost-label'>Diagnostics Total</div>
            <div class='estimated-cost-value'>&#8377;{diagnostics_cost:,.0f}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with c3:

    st.markdown(
        f"""
        <div class='estimated-cost-card'>
            <div class='estimated-cost-label'>Current Total</div>
            <div class='estimated-cost-value'>&#8377;{gross_bill:,.0f}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


st.markdown("</div>", unsafe_allow_html=True)

# =====================================================
# NAVIGATION
# =====================================================

st.write("")

left, right = st.columns(2)

with left:

    if st.button(
        "Previous",
        use_container_width=True
    ):

        st.switch_page(
            "pages/admin_procedure.py"
        )

with right:

    if st.button(
        "Next Medicines",
        use_container_width=True
    ):

        if len(st.session_state.diagnostics) == 0:

            st.warning(
                "No diagnostics have been added.\n\n"
                "Click Next again if you want to continue without diagnostics."
            )

            if "skip_diagnostics_warning" not in st.session_state:

                st.session_state.skip_diagnostics_warning = True

                st.stop()

        st.session_state.skip_diagnostics_warning = False

        st.switch_page(
            "pages/admin_medicines.py"
        )
