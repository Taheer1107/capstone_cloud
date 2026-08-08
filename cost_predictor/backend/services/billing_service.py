from ml_predictor import predict_cost
from services import diagnostics_service
from services import medicine_service
from services import consumable_service

# ----------------------------------
# MAIN BILLING ENGINE
# ----------------------------------

def generate_bill(payload):
    """
    payload format:

    {
        "procedure": "...",
        "specialty": "...",
        "hospital_type": "...",
        "city_tier": "...",
        "age": 45,
        "ward_type": "...",

        "diagnostics": [
            {"procedure_name": "CBC", "quantity": 1}
        ],

        "medicines": [
            {"generic_name": "Paracetamol", "quantity": 10}
        ],

        "consumables": [
            {"item_name": "Syringe", "quantity": 5}
        ],

        "other_charges": 0
    }
    """

    # ----------------------------------
    # 1. ML PROCEDURE COST
    # ----------------------------------

    procedure_cost = predict_cost(
        procedure=payload["procedure"],
        specialty=payload["specialty"],
        hospital_type=payload["hospital_type"],
        city_tier=payload["city_tier"],
        age=payload["age"]
    )

    # ----------------------------------
    # 2. DIAGNOSTICS TOTAL
    # ----------------------------------

    diagnostics_result = diagnostics_service.calculate_total(
        payload.get("diagnostics", [])
    )

    diagnostics_total = diagnostics_result["total"]

    # ----------------------------------
    # 3. MEDICINES TOTAL
    # ----------------------------------

    medicine_result = medicine_service.calculate_total(
        payload.get("medicines", [])
    )

    medicine_total = medicine_result["total"]

    # ----------------------------------
    # 4. CONSUMABLES TOTAL
    # ----------------------------------

    consumable_result = consumable_service.calculate_total(
        payload.get("consumables", [])
    )

    consumable_total = consumable_result["total"]

    # ----------------------------------
    # 5. OTHER CHARGES
    # ----------------------------------

    other_total = payload.get("other_charges", 0)

    # ----------------------------------
    # 6. GROSS BILL
    # ----------------------------------

    gross_bill = (
        procedure_cost +
        diagnostics_total +
        medicine_total +
        consumable_total +
        other_total
    )

    # ----------------------------------
    # FINAL STRUCTURED OUTPUT
    # ----------------------------------

    return {
        "procedure_cost": round(procedure_cost, 2),

        "diagnostics": diagnostics_result,
        "medicines": medicine_result,
        "consumables": consumable_result,

        "other_charges": other_total,

        "gross_bill": round(gross_bill, 2)
    }