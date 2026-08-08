import streamlit as st
import pandas as pd
from pathlib import Path

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="Admin - Consumables",
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
    / "consumable_catalog.csv"
)

consumable_df = pd.read_csv(DATA_PATH)

consumable_df = consumable_df.sort_values("item_name")

# =====================================================
# SESSION
# =====================================================

if "consumables" not in st.session_state:
    st.session_state.consumables = []

# =====================================================
# HEADER
# =====================================================

st.markdown(
    "<h1 style='margin:0;font-size:42px;'>Consumables</h1>",
    unsafe_allow_html=True
)

st.caption(
    "Search and add consumables used during treatment"
)

st.progress(5 / 8)

st.caption("Step 5 of 8 - Consumables")

# =====================================================
# SEARCH
# =====================================================
st.markdown("### Search Consumable")

st.caption(
    "Search and add consumables used during treatment."
)

selected_item = st.selectbox(
    "Search Consumable",
    options=sorted(
        consumable_df["item_name"]
        .dropna()
        .unique()
    ),
    index=None,
    placeholder="Start typing to search consumables..."
)

if selected_item:

    row = consumable_df[
        consumable_df["item_name"] == selected_item
    ].iloc[0]

    
    unit_price = float(row["unit_price"])

    st.caption(
        f"Unit Price: ₹{unit_price:,.2f}"
    )
    

    if st.button(
        "Add Consumable",
        use_container_width=True
    ):

        found = False

        for item in st.session_state.consumables:

            if item["item_name"] == selected_item:

                item["qty"] += 1

                item["total"] = (
                    item["qty"] *
                    item["unit_price"]
                )

                found = True
                break

        if not found:

            st.session_state.consumables.append({

                "item_name": row["item_name"],

                "unit_price": float(row["unit_price"]),

                "qty": 1,

                "total": float(row["unit_price"])

            })

        st.rerun()

st.markdown("</div>", unsafe_allow_html=True)
# =====================================================
# SELECTED CONSUMABLES
# =====================================================

st.write("")


st.markdown("## Selected Consumables")

subtotal = 0

if len(st.session_state.consumables) == 0:

    st.info(
        "No consumables have been added yet."
    )

else:

    h1, h2, h3, h4, h5 = st.columns([5,2,2,2,1])

    h1.markdown("**Consumable**")
    h2.markdown("**Qty**")
    h3.markdown("**Unit Price**")
    h4.markdown("**Total**")
    h5.markdown("**Remove**")

    st.divider()

    for i, item in enumerate(st.session_state.consumables):

        c1, c2, c3, c4, c5 = st.columns([5,2,2,2,1])

        c1.write(item["item_name"])

        # ----------------------------------------
        # Quantity
        # ----------------------------------------

        

        with c2:
            
            qcol, qspace = c2.columns([1, 1])

            new_qty = qcol.number_input(
                "Qty",
                min_value=1,
                max_value=99,
                value=item["qty"],
                key=f"qty_cons_{i}",
                label_visibility="collapsed"
            )

            if new_qty != item["qty"]:
                item["qty"] = new_qty
                item["total"] = item["qty"] * item["unit_price"]
                st.rerun()
            

        if new_qty != item["qty"]:
            item["qty"] = new_qty
            item["total"] = item["qty"] * item["unit_price"]
            st.rerun()

        # ----------------------------------------
        # Unit Price
        # ----------------------------------------

        c3.write(
            f"₹{item['unit_price']:,.0f}"
        )

        # ----------------------------------------
        # Total
        # ----------------------------------------

        c4.write(
            f"₹{item['total']:,.0f}"
        )

        subtotal += item["total"]

        # ----------------------------------------
        # Remove
        # ----------------------------------------

        if c5.button(
            "Remove",
            key=f"remove_cons_{i}"
        ):

            st.session_state.consumables.pop(i)

            st.rerun()

st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='main-card'>", unsafe_allow_html=True)
procedure_cost = st.session_state.get(
    "base_cost",
    0
)

diagnostics_cost = st.session_state.get(
    "diagnostics_total",
    0
)

medicines_cost = st.session_state.get(
    "medicines_total",
    0
)

consumables_cost = subtotal



st.session_state.consumables_total = consumables_cost

st.markdown("## Current Bill")

running_total = (
    procedure_cost +
    diagnostics_cost +
    medicines_cost
)

current_total = (
    procedure_cost +
    diagnostics_cost +
    medicines_cost +
    consumables_cost
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
            <div class='estimated-cost-label'>Consumables Total</div>
            <div class='estimated-cost-value'>&#8377;{consumables_cost:,.0f}</div>
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
            "pages/admin_medicines.py"
        )

with right:

    if st.button(
        "Next Room & Doctor Charges",
        use_container_width=True
    ):

        if (
            len(st.session_state.consumables) == 0
            and
            not st.session_state.get(
                "skip_consumable_warning",
                False
            )
        ):

            st.session_state.skip_consumable_warning = True

            st.warning(
                "No consumables have been added. Click Next again if you wish to continue."
            )

            st.stop()

        st.session_state.skip_consumable_warning = False

        st.switch_page(
            "pages/admin_room_doctor.py"
        )
