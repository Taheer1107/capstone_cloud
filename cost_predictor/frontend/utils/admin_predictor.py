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

API_URL = "http://127.0.0.1:8002/predict"

LOOKUP_PATH = (
    Path(__file__).resolve().parents[2]
    / "datasets"
    / "PROCEDURE_LOOKUP.csv"
)

lookup_df = pd.read_csv(LOOKUP_PATH)

procedure_options = sorted(
    lookup_df["procedure"].dropna().unique().tolist()
)


def get_specialty(procedure):

    row = lookup_df.loc[
        lookup_df["procedure"] == procedure,
        "specialty"
    ]

    if len(row) == 0:
        return ""

    return row.iloc[0]


def estimate_cost(
    procedure,
    specialty,
    city,
    hospital,
    ward,
    age
):

    payload = {

        "procedure": normalize_procedure(procedure),
        "specialty": normalize_specialty(specialty),
        "hospital_type": normalize_hospital(hospital),
        "city_tier": normalize_city(city),
        "ward_type": normalize_ward(ward),
        "age": age,
        "pmjay_flag": 0

    }

    try:

        r = requests.get(
            API_URL,
            params=payload,
            timeout=20
        )

        if r.status_code != 200:
            return False, None

        return True, r.json()

    except:
        return False, None