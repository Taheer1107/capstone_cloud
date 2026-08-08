import requests
import pandas as pd
from pathlib import Path

from utils.normalizer import (
    normalize_procedure,
    normalize_specialty,
    normalize_city,
    normalize_hospital,
    normalize_ward
)

# =====================================================
# CONFIG
# =====================================================
API_URL = "http://127.0.0.1:8002/predict"

# =====================================================
# LOAD LOOKUP (SINGLE SOURCE OF TRUTH)
# =====================================================
LOOKUP_PATH = (
    Path(__file__)
    .resolve()
    .parents[2]
    / "datasets"
    / "PROCEDURE_LOOKUP.csv"
)

lookup_df = pd.read_csv(LOOKUP_PATH)

procedure_options = sorted(
    lookup_df["procedure"].dropna().unique().tolist()
)

# =====================================================
# CORE PREDICTION ENGINE
# =====================================================
def predict_cost(
    procedure,
    specialty,
    city_tier,
    hospital_type,
    ward_type,
    age
):
    """
    Shared function used by BOTH:
    - user.py (patient side)
    - admin procedure page
    """

    payload = {
        "procedure": normalize_procedure(procedure),
        "specialty": normalize_specialty(specialty),
        "city_tier": normalize_city(city_tier),
        "hospital_type": normalize_hospital(hospital_type),
        "ward_type": normalize_ward(ward_type),
        "age": age,
        "pmjay_flag": 0
    }

    try:
        r = requests.get(API_URL, params=payload, timeout=20)

        if r.status_code != 200:
            return False, None, payload

        data = r.json()

        return True, data, payload

    except Exception as e:
        return False, str(e), payload