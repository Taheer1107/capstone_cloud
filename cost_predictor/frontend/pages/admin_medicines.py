import streamlit as st
import pandas as pd
from pathlib import Path

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="Admin - Medicines",
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

    st.switch_page("pages/admin_patient.py")

if "base_cost" not in st.session_state:

    st.switch_page("pages/admin_procedure.py")

# =====================================================
# LOAD DATASET
# =====================================================

DATA_PATH = (
    Path(__file__)
    .resolve()
    .parents[2]
    / "datasets"
    / "medicine_catalog.csv"
)

medicine_df = pd.read_csv(DATA_PATH)

medicine_df = medicine_df.sort_values("medicine_name")

medicine_options = (
    medicine_df["medicine_name"]
    .dropna()
    .drop_duplicates()
    .tolist()
)

# =====================================================
# SESSION
# =====================================================

if "medicines" not in st.session_state:

    st.session_state.medicines = []

# =====================================================
# HEADER
# =====================================================

st.markdown(
    "<h1 style='margin:0;font-size:42px;'>Medicines</h1>",
    unsafe_allow_html=True
)

st.caption(
    "Search and add prescribed medicines"
)

st.progress(4 / 8)

st.caption("Step 4 of 8 - Medicines")

# =====================================================
# SEARCH
# =====================================================
st.markdown("### Search Medicine")

st.caption(
    "Type part of the medicine name. The closest matches will appear automatically."
)



query = st.text_input(
    "",
    placeholder="Type at least 2 letters..."
)

selected_medicine = None

matches = pd.DataFrame()

if len(query) >= 2:

    matches = medicine_df[
        medicine_df["medicine_name"]
        .str.contains(
            query,
            case=False,
            na=False
        )
    ].head(20)

    if matches.empty:

        st.warning("No medicines found.")

    else:

        selected_medicine = st.selectbox(
            "Matching Medicines",
            matches["medicine_name"].tolist()
        )
        if selected_medicine:

            row = medicine_df[
                medicine_df["medicine_name"] == selected_medicine
            ].iloc[0]

            st.caption(
            f"Manufacturer: {row['manufacturer']} | "
            f"Pack: {row['pack_size']} | "
            f"\u20B9{row['unit_price']:,.2f}"
        )

            if st.button(
                "Add Medicine",
                use_container_width=True
            ):

                found = False

                for item in st.session_state.medicines:

                    if item["medicine_name"] == selected_medicine:

                        item["qty"] += 1
                        item["total"] = (
                            item["qty"] *
                            item["unit_price"]
                        )

                        found = True
                        break

                if not found:

                    st.session_state.medicines.append({

                        "medicine_name": row["medicine_name"],

                        "manufacturer": row["manufacturer"],

                        "pack_size": row["pack_size"],

                        "composition_1": row["composition_1"],

                        "composition_2": row["composition_2"],

                        "unit_price": float(row["unit_price"]),

                        "qty": 1,

                        "total": float(row["unit_price"])

                    })

                st.rerun()
st.markdown("</div>", unsafe_allow_html=True)
# =====================================================
# SELECTED MEDICINES
# =====================================================


st.markdown("## Selected Medicines")

subtotal = 0

if len(st.session_state.medicines) == 0:

    st.info(
        "No medicines have been added yet."
    )

else:

    h1, h2, h3, h4, h5 = st.columns([5,2,2,2,1])

    h1.markdown("**Medicine**")
    h2.markdown("**Qty**")
    h3.markdown("**Unit Price**")
    h4.markdown("**Total**")
    h5.markdown("**Remove**")

    st.divider()

    for i, item in enumerate(st.session_state.medicines):

        c1, c2, c3, c4, c5 = st.columns([5,2,2,2,1])

        # ---------------------------------------
        # MEDICINE NAME
        # ---------------------------------------

        c1.write(item["medicine_name"])

        # ---------------------------------------
        # QUANTITY
        # ---------------------------------------

        qcol, qspace = c2.columns([1, 1])

        new_qty = qcol.number_input(
            "Qty",
            min_value=1,
            max_value=99,
            value=item["qty"],
            key=f"qty_med_{i}",
            label_visibility="collapsed"
        )

        if new_qty != item["qty"]:
            item["qty"] = new_qty
            item["total"] = item["qty"] * item["unit_price"]
            st.rerun()

        # ---------------------------------------
        # UNIT PRICE
        # ---------------------------------------

        c3.write(
            f"₹{item['unit_price']:,.0f}"
        )

        # ---------------------------------------
        # TOTAL
        # ---------------------------------------

        c4.write(
            f"₹{item['total']:,.0f}"
        )

        subtotal += item["total"]

        # ---------------------------------------
        # REMOVE
        # ---------------------------------------

        if c5.button(
            "Remove",
            key=f"remove_med_{i}"
        ):

            st.session_state.medicines.pop(i)

            st.rerun()

st.markdown("</div>", unsafe_allow_html=True)

procedure_cost = st.session_state.get(
    "base_cost",
    0
)

diagnostics_cost = st.session_state.get(
    "diagnostics_total",
    0
)

medicines_cost = subtotal

gross_bill = (
    procedure_cost +
    diagnostics_cost +
    medicines_cost
)
# final cost thing 

st.markdown("## Current Bill")
running_total = (
    procedure_cost +
    diagnostics_cost
)

current_total = (
    procedure_cost +
    diagnostics_cost +
    medicines_cost
)

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
            <div class='estimated-cost-label'>Medicines Total</div>
            <div class='estimated-cost-value'>&#8377;{medicines_cost:,.0f}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with c3:

    st.markdown(
        f"""
        <div class='estimated-cost-card'>
            <div class='estimated-cost-label'>Current Total</div>
            <div class='estimated-cost-value'>&#8377;{current_total:,.0f}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

st.markdown("</div>", unsafe_allow_html=True)

st.session_state.medicines_total = medicines_cost

# =====================================================
# NAVIGATION
# =====================================================

left, right = st.columns(2)

with left:

    if st.button(
        "Previous",
        use_container_width=True
    ):

        st.switch_page(
            "pages/admin_diagnostics.py"
        )

with right:

    if st.button(
        "Next Consumables",
        use_container_width=True
    ):

        if (
            len(st.session_state.medicines) == 0
            and
            not st.session_state.get(
                "skip_medicine_warning",
                False
            )
        ):

            st.session_state.skip_medicine_warning = True

            st.warning(
                "No medicines have been added. Click Next again to continue without medicines."
            )

            st.stop()

        st.session_state.skip_medicine_warning = False

        st.switch_page(
            "pages/admin_consumables.py"
        )
