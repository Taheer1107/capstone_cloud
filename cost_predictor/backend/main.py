from unittest import result

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ml_predictor import predict_cost, predict_with_explanation
from services.billing import Billing
app = FastAPI(title="Healthcare Cost Predictor API")

# -------------------------------------------------
# CORS
# -------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------
# HELPERS
# -------------------------------------------------
def contains_any(text, words):
    t = text.lower()
    return any(w in t for w in words)


def room_cost(hospital_type, ward_type, city_tier):

    govt = {
        "general": 50,
        "semi-private": 150,
        "private": 300,
        "icu": 1000,
        "deluxe": 1500
    }

    private = {
        "general": 5000,
        "semi-private": 8000,
        "private": 12000,
        "icu": 20000,
        "deluxe": 30000
    }

    if hospital_type == "Government":
        return govt.get(ward_type, 50)

    val = private.get(ward_type, 5000)

    if city_tier == "Tier-2":
        val *= 0.80
    elif city_tier == "Tier-3":
        val *= 0.60

    return int(val)


def private_factor(bank):
    data = {
        "SBI": 0.92,
        "HDFC": 0.95,
        "ICICI": 0.93
    }
    return data.get(bank, 0.0)


def network_factor(bank, tier):
    table = {
        "SBI": {
            "Tier-1": 1.00,
            "Tier-2": 0.97,
            "Tier-3": 0.95
        },
        "HDFC": {
            "Tier-1": 1.00,
            "Tier-2": 0.93,
            "Tier-3": 0.82
        },
        "ICICI": {
            "Tier-1": 1.00,
            "Tier-2": 0.92,
            "Tier-3": 0.80
        }
    }

    return table.get(bank, {}).get(tier, 0.85)


def procedure_cap(proc):
    p = proc.lower()

    if "knee" in p:
        return 250000

    if "hip" in p:
        return 250000

    if "cataract" in p:
        return 50000

    if "heart" in p or "bypass" in p:
        return 500000

    if "cancer" in p:
        return 1000000

    return 99999999


EXCLUDED = [
    "botox",
    "hair transplant",
    "cosmetic",
    "liposuction",
    "lasik",
    "teeth cleaning",
    "braces"
]

WAITING = [
    "maternity",
    "delivery",
    "pregnancy",
    "c-section",
    "cataract",
    "hernia",
    "knee replacement"
]

# -------------------------------------------------
# ROOT
# -------------------------------------------------
@app.get("/")
def root():
    return {"message": "API Running"}

@app.get("/health")
def health():
    return {"status": "ok"}

# -------------------------------------------------
# COST PREDICTION
# -------------------------------------------------
@app.get("/predict")
def predict(
    procedure: str,
    specialty: str,
    hospital_type: str,
    city_tier: str,
    age: int,
    ward_type: str,
    pmjay_flag: int = 0
):

    print("\n" + "="*60)
    print("PROCEDURE =", procedure)
    print("SPECIALTY =", specialty)
    print("HOSPITAL =", hospital_type)
    print("CITY =", city_tier)
    print("AGE =", age)

    result = predict_with_explanation(
    procedure=procedure,
    specialty=specialty,
    hospital_type=hospital_type,
    city_tier=city_tier,
    age=age
)

    base_cost = result["prediction"]

    # -------------------------------------------------
# BUSINESS PRICE ADJUSTMENT
# -------------------------------------------------

    # City Tier
    if city_tier == "Tier-1":
        base_cost *= 1.10
    elif city_tier == "Tier-2":
        base_cost *= 1.00
    elif city_tier == "Tier-3":
        base_cost *= 0.90

    # Hospital Type
    if hospital_type == "Government":
        base_cost *= 0.35
    elif hospital_type == "Private":
        base_cost *= 1.00

    # Ward Type
    if ward_type == "general":
        base_cost *= 1.00
    elif ward_type == "semi-private":
        base_cost *= 1.08
    elif ward_type == "private":
        base_cost *= 1.18
    elif ward_type == "icu":
        base_cost *= 1.45
    elif ward_type == "deluxe":
        base_cost *= 1.65

    base_cost = int(base_cost)
    print("\nEXPLANATION")
    print(result["explanation"])

    print("PREDICTION =", base_cost)
    print("="*60)

    return {
    "success": True,
    "prediction": {
        "final_cost_inr": int(base_cost)
    },
    "explanation": result["explanation"]
}
# -------------------------------------------------
# PRIVATE INSURANCE
# -------------------------------------------------
@app.get("/insurance")
def insurance(
    base_cost: float,
    hospital_type: str,
    city_tier: str,
    ward_type: str,
    bank: str,
    days: int,
    sum_insured: int,
    procedure: str,
    policy_years: str = "<1 Year",
    claim_mode: str = "Cashless"
):

    total = int(
        base_cost +
        room_cost(hospital_type, ward_type, city_tier) * days
    )

    proc = procedure.lower()

    if contains_any(proc, EXCLUDED):
        return {
            "status": "REJECTED",
            "reason": "Procedure excluded from policy.",
            "limit_day": room_cost(
                hospital_type, ward_type, city_tier
            ),
            "total_bill": total,
            "insurance_pays": 0,
            "patient_pays": total
        }

    if contains_any(proc, WAITING):
        if policy_years == "<1 Year":
            return {
                "status": "REJECTED",
                "reason": "Waiting period not completed.",
                "limit_day": room_cost(
                    hospital_type, ward_type, city_tier
                ),
                "total_bill": total,
                "insurance_pays": 0,
                "patient_pays": total
            }

    coverage = total
    coverage *= private_factor(bank)
    coverage *= network_factor(bank, city_tier)

    if claim_mode == "Reimbursement":
        coverage *= 0.92

    if ward_type == "deluxe":
        coverage *= 0.65
    elif ward_type == "private":
        coverage *= 0.90

    coverage = min(coverage, procedure_cap(proc))
    coverage = min(coverage, sum_insured)

    insurance_pays = int(max(0, coverage))
    patient = int(max(0, total - insurance_pays))

    status = "APPROVED"
    reason = "High coverage approved."

    if insurance_pays == 0:
        status = "REJECTED"
        reason = "No claim approved."
    elif patient > 0:
        status = "PARTIAL"
        reason = "Partial claim due to caps/rules."

    return {
        "status": status,
        "reason": reason,
        "limit_day": room_cost(
            hospital_type, ward_type, city_tier
        ),
        "total_bill": total,
        "insurance_pays": insurance_pays,
        "patient_pays": patient
    }

# -------------------------------------------------
# MILITARY / ECHS
# -------------------------------------------------
@app.get("/military")
def military(
    base_cost: float,
    procedure: str,
    hospital_type: str,
    ward_type: str,
    city_tier: str,
    military_status: str,
    echs: str,
    emergency: str,
    days: int,
    private_bank: str,
    relation: str
):

    total = int(
        base_cost +
        room_cost(hospital_type, ward_type, city_tier) * days
    )

    military_cover = 0
    private_cover = 0

    # Serving personnel
    if military_status == "Serving Personnel":
        if hospital_type == "Government":
            military_cover = total
        else:
            military_cover = int(total * 0.90)

    # Veteran / Dependent with ECHS
    elif echs == "Yes":
        if hospital_type == "Government":
            military_cover = total
        else:
            military_cover = int(total * 0.85)

    # Emergency private
    if emergency == "Yes":
        military_cover = max(
            military_cover,
            int(total * 0.80)
        )

    # Additional private insurance for remaining
    remaining = total - military_cover

    if private_bank != "None" and remaining > 0:
        private_cover = int(
            remaining *
            private_factor(private_bank) *
            network_factor(private_bank, city_tier)
        )

    total_cover = military_cover + private_cover

    if total_cover > total:
        total_cover = total

    patient = total - total_cover

    status = "APPROVED"
    reason = "Military benefits applied."

    if patient > 0:
        status = "PARTIAL"
        reason = "Partial balance payable."

    return {
        "status": status,
        "reason": reason,
        "total_bill": total,
        "military_cover": military_cover,
        "private_cover": private_cover,
        "patient_pay": patient
    }

# -------------------------------------------------
# GOVT EMPLOYEE / CGHS
# -------------------------------------------------
@app.get("/govt")
def govt(
    base_cost: float,
    procedure: str,
    hospital_type: str,
    ward_type: str,
    city_tier: str,
    category: str,
    cghs: str,
    empanelled: str,
    emergency: str,
    days: int,
    private_bank: str
):

    total = int(
        base_cost +
        room_cost(hospital_type, ward_type, city_tier) * days
    )

    govt_cover = 0
    private_cover = 0

    if cghs == "Yes":

        if empanelled == "Yes":
            govt_cover = int(total * 0.95)

        elif emergency == "Yes":
            govt_cover = int(total * 0.80)

        else:
            govt_cover = int(total * 0.60)

    remaining = total - govt_cover

    if private_bank != "None" and remaining > 0:
        private_cover = int(
            remaining *
            private_factor(private_bank) *
            network_factor(private_bank, city_tier)
        )

    total_cover = govt_cover + private_cover

    if total_cover > total:
        total_cover = total

    patient = total - total_cover

    status = "APPROVED"
    reason = "Government benefits applied."

    if patient > 0:
        status = "PARTIAL"
        reason = "Partial payable after CGHS."

    return {
        "status": status,
        "reason": reason,
        "total_bill": total,
        "govt_cover": govt_cover,
        "private_cover": private_cover,
        "patient_pay": patient
    }
@app.post("/admin/bill/create")
def create_bill(payload: dict):

    bill = Billing()

    # -----------------------------
    # 1. PROCEDURE COST (ML)
    # -----------------------------
    from ml_predictor import predict_cost

    procedure_cost = predict_cost(
        procedure=payload["procedure"],
        specialty=payload["specialty"],
        hospital_type=payload["hospital_type"],
        city_tier=payload["city_tier"],
        age=payload["age"]
    )

    bill.set_procedure_cost(procedure_cost)

    # -----------------------------
    # 2. DIAGNOSTICS
    # -----------------------------
    for d in payload.get("diagnostics", []):
        bill.add_diagnostic(
            d["diagnostic_id"],
            d["quantity"]
        )

    # -----------------------------
    # 3. MEDICINES
    # -----------------------------
    for m in payload.get("medicines", []):
        bill.add_medicine(
            m["medicine_id"],
            m["quantity"]
        )

    # -----------------------------
    # 4. CONSUMABLES
    # -----------------------------
    for c in payload.get("consumables", []):
        bill.add_consumable(
            c["consumable_id"],
            c["quantity"]
        )

    # -----------------------------
    # 5. OTHER CHARGES
    # -----------------------------
    for o in payload.get("other_charges", []):
        bill.add_other_charge(
            o["name"],
            o["amount"]
        )

    # -----------------------------
    # FINAL RESPONSE
    # -----------------------------
    result = bill.summary()

    return {
        "success": True,
        "patient_id": payload.get("patient_id"),
        "bill": result
    }