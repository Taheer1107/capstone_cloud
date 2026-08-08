from pathlib import Path
import json
import pickle

import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"

MODEL_PATH = MODELS_DIR / "XGBoost_Current_Week_Detection.pkl"
STATE_ENCODER_PATH = MODELS_DIR / "label_encoder_state.pkl"
DISEASE_ENCODER_PATH = MODELS_DIR / "label_encoder_disease.pkl"
FEATURE_LIST_PATH = MODELS_DIR / "feature_list.json"
TRAINING_SNAPSHOT_PATH = MODELS_DIR / "training_snapshot.csv"


class CurrentWeekDetectionRequest(BaseModel):
    state: str = Field(..., min_length=1)
    disease: str = Field(..., min_length=1)
    year: int = Field(..., ge=1900)
    week_of_year: int = Field(..., ge=1, le=53)
    cases: float = Field(..., ge=0)
    deaths: float = Field(..., ge=0)
    previous_week_cases: float = Field(..., ge=0)
    cases_lag2: float = Field(..., ge=0)
    cases_lag3: float = Field(..., ge=0)
    cases_lag4: float = Field(..., ge=0)
    rolling_mean_3: float = Field(..., ge=0)
    rolling_mean_5: float = Field(..., ge=0)
    rolling_std_3: float = Field(..., ge=0)


def load_pickle(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"Required model artifact not found: {path}")

    with path.open("rb") as file:
        return pickle.load(file)


def load_feature_list() -> list[str]:
    if not FEATURE_LIST_PATH.exists():
        raise FileNotFoundError(f"Feature list not found: {FEATURE_LIST_PATH}")

    with FEATURE_LIST_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_week_lookup() -> dict[tuple[int, int], int]:
    if not TRAINING_SNAPSHOT_PATH.exists():
        raise FileNotFoundError(f"Training snapshot not found: {TRAINING_SNAPSHOT_PATH}")

    snapshot = pd.read_csv(
        TRAINING_SNAPSHOT_PATH,
        usecols=["year", "week_of_year", "global_week"],
    )
    week_lookup = (
        snapshot[["year", "week_of_year", "global_week"]]
        .drop_duplicates()
        .set_index(["year", "week_of_year"])["global_week"]
        .to_dict()
    )
    return {
        (int(year), int(week)): int(global_week)
        for (year, week), global_week in week_lookup.items()
    }


# ---------------- LOAD ARTIFACTS ----------------
clf_model = load_pickle(MODEL_PATH)
le_state = load_pickle(STATE_ENCODER_PATH)
le_disease = load_pickle(DISEASE_ENCODER_PATH)
FEATURE_LIST = load_feature_list()
WEEK_LOOKUP = load_week_lookup()


def month_group_from_week(week_of_year: int) -> int:
    return min(((int(week_of_year) - 1) // 4) + 1, 12)


def encode_known_value(encoder, value: str, field_name: str) -> int:
    cleaned_value = value.strip()
    known_values = set(encoder.classes_)

    if cleaned_value not in known_values:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown {field_name}: {cleaned_value}",
        )

    return int(encoder.transform([cleaned_value])[0])


def get_global_week(year: int, week_of_year: int) -> int:
    key = (int(year), int(week_of_year))

    if key not in WEEK_LOOKUP:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unknown year/week combination for this trained model: "
                f"{year}-W{week_of_year:02d}"
            ),
        )

    return WEEK_LOOKUP[key]


def build_feature_row(payload: CurrentWeekDetectionRequest) -> pd.DataFrame:
    state_enc = encode_known_value(le_state, payload.state, "state")
    disease_enc = encode_known_value(le_disease, payload.disease, "disease")
    global_week = get_global_week(payload.year, payload.week_of_year)

    previous_2_week_average = (
        payload.previous_week_cases + payload.cases_lag2
    ) / 2
    growth_rate = (
        (payload.cases - payload.previous_week_cases) / payload.previous_week_cases
        if payload.previous_week_cases > 0
        else 0
    )
    peak_flag = int(
        payload.cases
        > (payload.rolling_mean_3 + 2 * payload.rolling_std_3)
    )
    case_fatality_rate = (
        payload.deaths / payload.cases
        if payload.cases > 0
        else 0
    )

    feature_values = {
        "global_week": global_week,
        "week_of_year": payload.week_of_year,
        "state_enc": state_enc,
        "disease_enc": disease_enc,
        "cases": payload.cases,
        "previous_week_cases": payload.previous_week_cases,
        "previous_2_week_average": previous_2_week_average,
        "cases_lag2": payload.cases_lag2,
        "cases_lag3": payload.cases_lag3,
        "cases_lag4": payload.cases_lag4,
        "rolling_mean_3": payload.rolling_mean_3,
        "rolling_mean_5": payload.rolling_mean_5,
        "rolling_std_3": payload.rolling_std_3,
        "growth_rate": growth_rate,
        "peak_flag": peak_flag,
        "month_group": month_group_from_week(payload.week_of_year),
        "case_fatality_rate": case_fatality_rate,
    }

    missing_features = [
        feature for feature in FEATURE_LIST if feature not in feature_values
    ]
    if missing_features:
        raise HTTPException(
            status_code=500,
            detail=f"Backend cannot construct features: {missing_features}",
        )

    return pd.DataFrame(
        [[feature_values[feature] for feature in FEATURE_LIST]],
        columns=FEATURE_LIST,
    )


def risk_level_from_probability(probability: float) -> str:
    if probability > 0.7:
        return "high"
    if probability >= 0.3:
        return "medium"
    return "low"


def outbreak_probability(feature_row: pd.DataFrame) -> float:
    if not hasattr(clf_model, "predict_proba"):
        raise HTTPException(
            status_code=500,
            detail="Loaded model does not support probability output.",
        )

    class_labels = list(clf_model.classes_)
    if 1 not in class_labels:
        raise HTTPException(
            status_code=500,
            detail="Loaded model does not expose outbreak class label 1.",
        )

    outbreak_class_index = class_labels.index(1)
    return float(clf_model.predict_proba(feature_row)[0][outbreak_class_index])


@app.get("/")
def home():
    return {"message": "Outbreak Detection API Running"}


@app.get("/health")
def health():
    return {
        "api_running": True,
        "model_loaded": clf_model is not None,
        "feature_count": len(FEATURE_LIST),
        "model_type": "current_week_detection",
    }


# ---------------- PREDICT ----------------
@app.post("/predict")
def predict(payload: CurrentWeekDetectionRequest):
    feature_row = build_feature_row(payload)

    probability = outbreak_probability(feature_row)
    prediction = int(probability >= 0.5)

    return {
        "outbreak": prediction,
        "outbreak_probability": probability,
        "risk_level": risk_level_from_probability(probability),
        "model_type": "current_week_detection",
    }
