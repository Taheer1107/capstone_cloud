import requests
import pandas as pd
from pathlib import Path

API_URL = "http://127.0.0.1:8002/predict"

# Load lookup only for admin
LOOKUP_PATH = (
    Path(__file__)
    .resolve()
    .parents[2]
    / "datasets"
    / "PROCEDURE_LOOKUP.csv"
)

lookup_df = pd.read_csv(LOOKUP_PATH)

procedure_options = sorted(
    lookup_df["procedure"].unique().tolist()
)

def estimate_cost_admin(payload):

    try:
        r = requests.get(API_URL, params=payload, timeout=20)

        if r.status_code == 200:
            return True, r.json()

        return False, "Backend error"

    except:
        return False, "Backend not running"


def build_payload_admin(
    procedure,
    specialty,
    hospital,
    city,
    ward,
    age
):

    return {
        "procedure": procedure,
        "specialty": specialty,
        "hospital_type": hospital,
        "city_tier": city,
        "ward_type": ward,
        "age": age,
        "pmjay_flag": 0
    }