# =====================================================
# COMPONENTS COVERED BY EACH SCHEME
# =====================================================

PRIVATE_INSURANCE = {
    "covers": [
        "procedure",
        "diagnostics",
        "medicines",
        "room_charges",
        "doctor_charges"
    ],
    "excludes": [
        "consumables"
    ]
}

CGHS = {
    "covers": [
        "procedure",
        "diagnostics",
        "medicines",
        "consumables",
        "room_charges",
        "doctor_charges"
    ],
    "excludes": []
}

STATE_GOVT = {
    "covers": [
        "procedure",
        "diagnostics",
        "medicines",
        "consumables",
        "room_charges",
        "doctor_charges"
    ],
    "excludes": []
}

MILITARY_ECHS = {
    "covers": [
        "procedure",
        "diagnostics",
        "medicines",
        "consumables",
        "room_charges",
        "doctor_charges"
    ],
    "excludes": []
}


RULES = {
    "Private Insurance": PRIVATE_INSURANCE,
    "CGHS": CGHS,
    "State Govt": STATE_GOVT,
    "Military / ECHS": MILITARY_ECHS
}