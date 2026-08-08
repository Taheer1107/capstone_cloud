"""
Reusable coverage calculation functions.

Both the Patient module and the Admin module should call these
functions so that the payout calculation always remains identical.
"""

# ==========================================================
# PRIVATE INSURANCE
# ==========================================================

def calculate_private(
    gross_total: float,
    procedure: str,
    provider: str,
    days: int,
    sum_insured: float,
    policy_age: str,
    claim_type: str
):

    procedure = procedure.lower()

    excluded = [
        "botox",
        "cosmetic",
        "hair transplant",
        "liposuction",
        "ivf",
        "fertility",
        "lasik",
        "braces",
    ]

    if any(word in procedure for word in excluded):

        return {
            "cover": 0,
            "patient": gross_total,
            "room_limit": 0,
            "reason":
                "Not covered by insurance policy "
                "(cosmetic / excluded procedure)."
        }

    # --------------------------------------------------
    # Provider room limits
    # --------------------------------------------------

    if provider == "SBI":

        room_limit = 5000

    elif provider == "HDFC Ergo":

        room_limit = 7000

    elif provider == "ICICI Lombard":

        room_limit = 9000

    else:

        room_limit = 10000
        # --------------------------------------------------
    # Maximum cover based on sum insured
    # --------------------------------------------------

    max_cover = float(sum_insured)

    # Loyalty benefit
    if policy_age == "3+ Years":
        max_cover *= 1.05

    # Reimbursement usually results in a slightly lower payout
    if claim_type == "Reimbursement":
        max_cover *= 0.95

    # --------------------------------------------------
    # Room rent restriction
    # --------------------------------------------------

    allowed_room_total = room_limit * days

    if gross_total > allowed_room_total * 2:

        cover = max_cover * 0.72

        reason = (
            "Partial approval due to room rent cap / "
            "policy limits."
        )

    else:

        cover = max_cover * 0.92

        reason = (
            "Fully approved under policy coverage."
        )

    # --------------------------------------------------
    # Final adjustment
    # --------------------------------------------------

    cover = min(gross_total, cover)

    patient = max(
        gross_total - cover,
        0
    )

    return {

        "cover": cover,

        "patient": patient,

        "room_limit": room_limit,

        "reason": reason

    }
# ==========================================================
# MILITARY / ECHS
# ==========================================================

def calculate_military(
    gross_total: float,
    status: str,
    echs_card: str,
    emergency: str,
    private_hospital: str,
    topup_available: str
):

    # --------------------------------------------------
    # Base Eligibility
    # --------------------------------------------------

    if status == "Serving":

        cover = gross_total * 0.95
        daily = 9000

    elif status == "Veteran":

        cover = gross_total * 0.82
        daily = 7000

    else:

        cover = gross_total * 0.70
        daily = 5500

    # --------------------------------------------------
    # No ECHS Card
    # --------------------------------------------------

    if echs_card == "No":

        cover *= 0.55

    # --------------------------------------------------
    # Private Hospital Deduction
    # --------------------------------------------------

    if private_hospital == "Yes":

        cover *= 0.88

    # --------------------------------------------------
    # Emergency Bonus
    # --------------------------------------------------

    if emergency == "Yes":

        cover += gross_total * 0.05

    # --------------------------------------------------
    # Additional Top-up
    # --------------------------------------------------

    if topup_available == "Available":

        cover += gross_total * 0.10

    # --------------------------------------------------
    # Final Adjustment
    # --------------------------------------------------

    cover = min(
        gross_total,
        cover
    )

    patient = max(
        gross_total - cover,
        0
    )

    # --------------------------------------------------
    # Status Message
    # --------------------------------------------------

    if patient == 0:

        reason = (
            "Fully approved under ECHS / Defence coverage."
        )

    elif cover > gross_total * 0.55:

        reason = (
            "Partially approved due to caps / "
            "private hospital deductions."
        )

    else:

        reason = (
            "Low eligibility. Large patient payable remains."
        )

    return {

        "cover": cover,

        "patient": patient,

        "daily_limit": daily,

        "reason": reason

    }
# ==========================================================
# GOVERNMENT / CGHS
# ==========================================================

def calculate_govt(
    gross_total: float,
    scheme: str,
    employee_type: str,
    empanelled: str,
    room: str,
    emergency: str
):

    # --------------------------------------------------
    # Base Scheme
    # --------------------------------------------------

    if scheme == "CGHS":

        cover = gross_total * 0.92
        daily = 8000

    else:

        cover = gross_total * 0.78
        daily = 6000

    # --------------------------------------------------
    # Employee Type
    # --------------------------------------------------

    if employee_type == "Retired":

        cover *= 0.92

    elif employee_type == "Dependent":

        cover *= 0.82

    # --------------------------------------------------
    # Empanelled Hospital
    # --------------------------------------------------

    if empanelled == "No":

        cover *= 0.80

    # --------------------------------------------------
    # Room Type Deduction
    # --------------------------------------------------

    if room == "Private":

        cover *= 0.88

    elif room == "Semi Private":

        cover *= 0.95

    # --------------------------------------------------
    # Emergency Bonus
    # --------------------------------------------------

    if emergency == "Yes":

        cover += gross_total * 0.04

    # --------------------------------------------------
    # Final Adjustment
    # --------------------------------------------------

    cover = min(
        gross_total,
        cover
    )

    patient = max(
        gross_total - cover,
        0
    )

    # --------------------------------------------------
    # Status Message
    # --------------------------------------------------

    if patient == 0:

        reason = (
            "Fully approved under government scheme."
        )

    elif cover > gross_total * 0.55:

        reason = (
            "Partially approved due to room caps / "
            "scheme limits."
        )

    else:

        reason = (
            "Low eligibility under selected scheme."
        )

    return {

        "cover": cover,

        "patient": patient,

        "daily_limit": daily,

        "reason": reason

    }
