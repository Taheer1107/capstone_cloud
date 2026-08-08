import streamlit as st


# =====================================================
# START COVERAGE
# =====================================================
def start_patient_coverage(procedure_cost):

    coverage = {

        "gross_bill": {
            "procedure": procedure_cost,
            "diagnostics": 0,
            "medicines": 0,
            "consumables": 0,
            "room_charges": 0,
            "doctor_charges": 0,
            "total": procedure_cost
        },

        "eligible_amount": procedure_cost,

        "covered_amount": 0,

        "remaining_bill": procedure_cost,

        "waterfall": [],

        "patient_pays": procedure_cost,

        "visit_type": "OPD",

        "is_valid": True,

        "validation_message": None
    }

    st.session_state.coverage = coverage

    return coverage
def start_coverage(
    procedure_cost,
    diagnostics_cost,
    medicines_cost,
    consumables_cost,
    room_charges,
    doctor_charges,
    visit_type="IPD"
):

    if "coverage" in st.session_state:
        return st.session_state.coverage
    gross_bill = (
    procedure_cost
    + diagnostics_cost
    + medicines_cost
    + consumables_cost
    + room_charges
    + doctor_charges
)

    coverage = {

    "gross_bill": {

    "procedure": procedure_cost,

    "diagnostics": diagnostics_cost,

    "medicines": medicines_cost,

    "consumables": consumables_cost,

    "room_charges": room_charges,

    "doctor_charges": doctor_charges,

    "total": gross_bill

},

    "eligible_amount": gross_bill,

    "covered_amount": 0,

    "remaining_bill": gross_bill,

    "waterfall": [],

    "patient_pays": gross_bill,

    "visit_type": visit_type,

    "is_valid": True,

    "validation_message": None
}
    st.session_state.coverage = coverage

    return coverage


# =====================================================
# APPLY SCHEME
# =====================================================
def apply_scheme(
    scheme_name,
    amount_paid,
    scheme_type,
    eligible_amount
):

    coverage = st.session_state.get("coverage")

    if coverage is None:
        raise Exception("Coverage has not been initialized.")
    for entry in coverage["waterfall"]:

        if (
            entry["scheme"] == scheme_name
            and entry["type"] == scheme_type
        ):
            return

    remaining = coverage["remaining_bill"]

    paid = min(amount_paid, remaining)

    remaining -= paid

    coverage["waterfall"].append({

    "scheme": scheme_name,
    "eligible": eligible_amount,

    "type": scheme_type,

    "covered": paid,

    "remaining": remaining

})

    coverage["remaining_bill"] = remaining
    coverage["covered_amount"] += paid
    coverage["patient_pays"] = remaining

    st.session_state.coverage = coverage


# =====================================================
# FINISH COVERAGE
# =====================================================
def finish_coverage():

    coverage = st.session_state.get("coverage")

    if coverage is None:
        raise Exception("Coverage has not been initialized.")

    coverage["patient_pays"] = coverage["remaining_bill"]

    st.session_state.coverage = coverage

    return coverage


# =====================================================
# BACKWARD COMPATIBILITY
# =====================================================
def build_coverage(
    gross_bill,
    primary_scheme,
    primary_paid,
    patient_pays,
    visit_type="IPD"
):
    """
    Keeps older pages working while everything
    migrates to start_coverage/apply_scheme.
    """

    if "coverage" in st.session_state:
        del st.session_state["coverage"]

    start_coverage(gross_bill, visit_type)

    start_coverage(
        procedure_cost=gross_bill,
        diagnostics_cost=0,
        medicines_cost=0,
        consumables_cost=0,
        room_charges=0,
        doctor_charges=0,
        visit_type=visit_type
    )

    apply_scheme(
        scheme_name=primary_scheme,
        amount_paid=primary_paid,
        scheme_type="Primary",
        eligible_amount=gross_bill
    )

    finish_coverage()

    return st.session_state.coverage