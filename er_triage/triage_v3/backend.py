from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import uvicorn
try:
    from triage_v3.agent import run_agentic_triage
except ImportError:
    from agent import run_agentic_triage

app = FastAPI(title="Triage Classification API", version="1.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

MODEL = None
FEATURES = None
THRESHOLD = None

COMPLAINT_MAP = {
    "chest_pain": 0, "dyspnea": 1, "altered_ms": 2, "trauma": 3, "abdominal": 4,
    "cardiac": 5, "fever_infection": 6, "neurological": 7, "urological": 8,
    "psychiatric": 9, "pain_general": 10, "other": 11, "unknown": 12,
}
HIGH_ACUITY = {"chest_pain", "dyspnea", "altered_ms", "cardiac", "fever_infection"}
TRANSPORT_MAP = {"Ambulance": 0, "Walk-in": 1, "Police": 2, "Other": 3, "Unknown": 4}
GENDER_MAP = {"Male": 1, "Female": 0, "Unknown": 2}

DOCTORS = [
    {"name": "Dr. Asha Menon", "specialization": "Emergency Medicine", "available": True, "active_cases": 4, "experience_years": 13, "performance": 0.94},
    {"name": "Dr. Rohan Mehta", "specialization": "Cardiology", "available": True, "active_cases": 2, "experience_years": 11, "performance": 0.96},
    {"name": "Dr. Nisha Rao", "specialization": "Pulmonology", "available": True, "active_cases": 3, "experience_years": 9, "performance": 0.92},
    {"name": "Dr. Karan Shah", "specialization": "Trauma Surgery", "available": False, "active_cases": 6, "experience_years": 15, "performance": 0.95},
    {"name": "Dr. Farah Khan", "specialization": "Internal Medicine", "available": True, "active_cases": 1, "experience_years": 8, "performance": 0.90},
]

DEPARTMENT_STATUS = {
    "er_occupancy": 72,
    "icu_beds_available": 4,
    "general_beds_available": 18,
    "ambulance_queue": 3,
    "average_wait_minutes": 26,
}


class PatientInput(BaseModel):
    temperature: float = Field(..., example=37.2)
    heartrate: float = Field(..., example=88)
    resprate: float = Field(..., example=18)
    o2sat: float = Field(..., example=97)
    sbp: float = Field(..., example=122)
    dbp: float = Field(..., example=78)
    pain: float = Field(..., example=5)
    complaint_group: Optional[str] = Field("unknown", example="chest_pain")
    gender: Optional[str] = Field("Unknown", example="Male")
    arrival_transport: Optional[str] = Field("Unknown", example="Ambulance")
    age_at_admission: Optional[float] = Field(45, example=54)
    height_cm: Optional[float] = Field(None, example=170)
    weight_kg: Optional[float] = Field(None, example=70)
    bmi: Optional[float] = Field(None, example=24.5)
    acuity: Optional[float] = Field(3, example=2)
    has_hypertension: Optional[int] = Field(0, example=1)
    has_diabetes: Optional[int] = Field(0, example=0)
    has_cardiac: Optional[int] = Field(0, example=0)
    has_respiratory: Optional[int] = Field(0, example=0)
    has_renal: Optional[int] = Field(0, example=0)
    has_sepsis: Optional[int] = Field(0, example=0)
    prior_admission_count: Optional[int] = Field(0, example=2)


class BatchInput(BaseModel):
    patients: List[PatientInput]


@app.on_event("startup")
def load_model():
    global MODEL, FEATURES, THRESHOLD
    base_dir = Path(__file__).resolve().parent
    try:
        MODEL = joblib.load(base_dir / "stacking_final.pkl")
        FEATURES = joblib.load(base_dir / "features_final.pkl")
        THRESHOLD = joblib.load(base_dir / "threshold_final.pkl")
        print(f"Model loaded. Features: {len(FEATURES)}  Threshold: {THRESHOLD:.2f}")
    except Exception as exc:
        print(f"Model not loaded: {exc}")


def compute_bmi(p: PatientInput) -> float:
    if p.bmi is not None and p.bmi > 0:
        return float(p.bmi)
    if p.height_cm and p.weight_kg and p.height_cm > 0:
        return float(p.weight_kg / ((p.height_cm / 100) ** 2))
    return 24.9


def build_row(p: PatientInput) -> dict:
    bmi_value = compute_bmi(p)
    complaint = (p.complaint_group or "unknown").lower()
    return {
        "temperature": p.temperature,
        "heartrate": p.heartrate,
        "resprate": p.resprate,
        "o2sat": p.o2sat,
        "sbp": p.sbp,
        "dbp": p.dbp,
        "pain": p.pain,
        "pulse_pressure": p.sbp - p.dbp,
        "shock_index": p.heartrate / p.sbp if p.sbp > 0 else 0,
        "map": (p.sbp + 2 * p.dbp) / 3,
        "complaint_enc": COMPLAINT_MAP.get(complaint, 12),
        "high_acuity_complaint": int(complaint in HIGH_ACUITY),
        "gender_enc": GENDER_MAP.get(p.gender or "Unknown", 2),
        "arrival_transport_enc": TRANSPORT_MAP.get(p.arrival_transport or "Unknown", 4),
        "has_hypertension": int(p.has_hypertension or 0),
        "has_diabetes": int(p.has_diabetes or 0),
        "has_cardiac": int(p.has_cardiac or 0),
        "has_respiratory": int(p.has_respiratory or 0),
        "has_renal": int(p.has_renal or 0),
        "has_sepsis": int(p.has_sepsis or 0),
        "age_at_admission": float(p.age_at_admission or 45),
        "prior_admission_count": int(p.prior_admission_count or 0),
        "acuity": float(p.acuity or 3),
        "height_cm": float(p.height_cm or 0),
        "weight_kg": float(p.weight_kg or 0),
        "bmi": bmi_value,
        "bmi_risk": 1 if bmi_value >= 30 else 0,
    }


def risk(prob: float) -> str:
    return "HIGH" if prob >= 0.75 else "MEDIUM" if prob >= 0.50 else "LOW"


def is_critical_case(row: pd.Series) -> bool:
    return (
        row["heartrate"] <= 40 or row["heartrate"] >= 140 or
        row["sbp"] <= 80 or row["sbp"] >= 180 or
        row["o2sat"] <= 90 or
        row["resprate"] <= 10 or row["resprate"] >= 30 or
        row["temperature"] <= 35 or row["temperature"] >= 39.5 or
        row["shock_index"] > 1.2 or
        row["pulse_pressure"] <= 20 or
        row["bmi"] >= 40
    )


def adjust_probability(prob: float, row: pd.Series):
    override = is_critical_case(row)
    if override:
        return max(prob, 0.98), True
    return prob, False


def run_inference(df: pd.DataFrame) -> np.ndarray:
    # Try to detect the feature names expected by the loaded model (XGBoost or sklearn wrappers).
    model_feature_names = None
    try:
        # XGBoost Booster exposes feature_names on the booster
        booster = MODEL.get_booster()
        if booster is not None and hasattr(booster, "feature_names"):
            model_feature_names = list(booster.feature_names)
    except Exception:
        model_feature_names = None

    if model_feature_names is None and hasattr(MODEL, "feature_names_in_"):
        try:
            model_feature_names = list(getattr(MODEL, "feature_names_in_"))
        except Exception:
            model_feature_names = None

    # Fall back to the saved FEATURES list if model does not expose names
    if not model_feature_names:
        model_feature_names = FEATURES or []

    # Normalize column names: trim whitespace to avoid subtle mismatches
    model_feature_names = [str(c).strip() for c in model_feature_names]
    df_columns = [str(c).strip() for c in df.columns]

    # Ensure all expected features exist in the DataFrame (fill missing with 0)
    for col in model_feature_names:
        if col not in df_columns:
            df[col] = 0
            df_columns.append(col)

    # Reorder the DataFrame to the model's expected column order where possible
    cols_to_use = [c for c in model_feature_names if c in df.columns]
    if not cols_to_use:
        # If nothing matches, fall back to FEATURES saved list
        cols_to_use = [c for c in (FEATURES or []) if c in df.columns]
    if not cols_to_use:
        # Last resort: use all dataframe columns
        cols_to_use = list(df.columns)

    return MODEL.predict_proba(df[cols_to_use])[:, 1]


def rule_based_probability(row: pd.Series) -> float:
    score = 0.12
    score += 0.26 if row["high_acuity_complaint"] else 0
    score += 0.18 if row["o2sat"] <= 92 else 0.10 if row["o2sat"] < 95 else 0
    score += 0.12 if row["heartrate"] >= 120 or row["heartrate"] <= 50 else 0.06 if row["heartrate"] >= 100 else 0
    score += 0.12 if row["sbp"] <= 90 or row["sbp"] >= 180 else 0.05 if row["sbp"] <= 100 or row["sbp"] >= 160 else 0
    score += 0.10 if row["resprate"] >= 26 or row["resprate"] <= 10 else 0.05 if row["resprate"] >= 22 else 0
    score += 0.08 if row["temperature"] >= 39 or row["temperature"] <= 35.5 else 0.04 if row["temperature"] >= 38.3 else 0
    score += 0.07 if row["pain"] >= 8 else 0.03 if row["pain"] >= 6 else 0
    score += 0.06 if row["shock_index"] > 1.0 else 0.03 if row["shock_index"] > 0.8 else 0
    score += 0.04 if row["age_at_admission"] >= 70 else 0
    score += 0.04 if row["has_cardiac"] or row["has_respiratory"] or row["has_sepsis"] or row["has_renal"] else 0
    return min(0.99, max(0.01, score))


def predict_probability(row_df: pd.DataFrame) -> tuple[float, str, float]:
    if MODEL is not None and FEATURES:
        return float(run_inference(row_df)[0]), "ensemble_model", float(THRESHOLD)
    return rule_based_probability(row_df.iloc[0]), "clinical_rules_fallback", 0.50


def required_specialization(p: PatientInput, row: pd.Series) -> str:
    complaint = (p.complaint_group or "unknown").lower()
    if complaint in {"chest_pain", "cardiac"} or row["shock_index"] > 1.0:
        return "Cardiology"
    if complaint == "dyspnea" or row["o2sat"] < 94 or row["resprate"] >= 24:
        return "Pulmonology"
    if complaint == "trauma":
        return "Trauma Surgery"
    if complaint in {"fever_infection", "abdominal", "urological"}:
        return "Internal Medicine"
    return "Emergency Medicine"


def severity_score(row: pd.Series, prob: float) -> dict:
    score = int(round(prob * 45))
    score += 12 if row["high_acuity_complaint"] else 0
    score += 10 if row["o2sat"] <= 92 else 5 if row["o2sat"] < 95 else 0
    score += 8 if row["heartrate"] >= 120 or row["heartrate"] <= 50 else 0
    score += 8 if row["sbp"] <= 90 or row["sbp"] >= 180 else 0
    score += 7 if row["resprate"] >= 26 or row["resprate"] <= 10 else 0
    score += 6 if row["temperature"] >= 39 or row["temperature"] <= 35.5 else 0
    score += 5 if row["pain"] >= 8 else 0
    score += 5 if row["bmi"] >= 40 else 0
    score = max(0, min(score, 100))
    level = "High" if score >= 70 else "Medium" if score >= 40 else "Low"
    description = {
        "High": "Immediate emergency intervention required",
        "Medium": "Requires prompt medical attention",
        "Low": "Routine care recommended",
    }[level]
    return {"score": score, "level": level, "description": description}


def factor_contributions(p: PatientInput, row: pd.Series) -> List[dict]:
    factors = []

    def add(name: str, impact: float, detail: str):
        factors.append({"feature": name, "impact": round(float(impact), 3), "detail": detail})

    if row["o2sat"] < 95:
        add("Oxygen saturation", (95 - row["o2sat"]) / 25, f"O2 saturation is {row['o2sat']:.1f}%.")
    if row["heartrate"] >= 100 or row["heartrate"] <= 60:
        add("Heart rate", abs(row["heartrate"] - 80) / 120, f"Heart rate is {row['heartrate']:.0f} bpm.")
    if row["sbp"] <= 100 or row["sbp"] >= 160:
        add("Systolic blood pressure", abs(row["sbp"] - 120) / 140, f"Systolic BP is {row['sbp']:.0f} mmHg.")
    if row["resprate"] >= 22 or row["resprate"] <= 12:
        add("Respiratory rate", abs(row["resprate"] - 16) / 45, f"Respiratory rate is {row['resprate']:.0f}/min.")
    if row["temperature"] >= 38.3 or row["temperature"] <= 36:
        add("Temperature", abs(row["temperature"] - 37) / 8, f"Temperature is {row['temperature']:.1f} C.")
    if row["pain"] >= 7:
        add("Pain score", row["pain"] / 20, f"Pain score is {row['pain']:.0f}/10.")
    if row["shock_index"] > 0.9:
        add("Shock index", row["shock_index"] / 2, f"Shock index is {row['shock_index']:.2f}.")
    if row["high_acuity_complaint"]:
        complaint = (p.complaint_group or "unknown").replace("_", " ")
        add("Chief complaint", 0.35, f"{complaint} is a high-acuity complaint.")
    if row["age_at_admission"] >= 70:
        add("Age", 0.2, f"Patient age is {row['age_at_admission']:.0f}.")
    if row["has_cardiac"] or row["has_respiratory"] or row["has_sepsis"] or row["has_renal"]:
        add("Comorbidities", 0.25, "Significant comorbidities are present.")

    if not factors:
        add("Stable vitals", -0.2, "Vitals are within routine triage ranges.")
    return sorted(factors, key=lambda item: abs(item["impact"]), reverse=True)[:6]


def prediction_reason(label: str, factors: List[dict], severity: dict) -> str:
    positive = [f["feature"].lower() for f in factors if f["impact"] > 0]
    if label == "Needs ER":
        if positive:
            joined = ", ".join(positive[:3])
            return f"Patient classified as ER due to {joined}, with {severity['level'].lower()} severity."
        return f"Patient classified as ER because model probability exceeded the clinical threshold with {severity['level'].lower()} severity."
    if positive:
        return f"Patient classified as Non-ER because overall risk remains below threshold, though {', '.join(positive[:2])} should be reviewed."
    return "Patient classified as Non-ER because vital signs and available clinical indicators are stable."


def clinical_actions(label: str, severity: dict, override: bool) -> List[str]:
    if override or severity["level"] == "High":
        return [
            "Move patient to monitored emergency bay.",
            "Alert senior clinician and prepare rapid assessment.",
            "Repeat vitals and obtain focused history immediately.",
        ]
    if label == "Needs ER" or severity["level"] == "Medium":
        return [
            "Prioritize clinician review within the next queue cycle.",
            "Repeat abnormal vitals and monitor symptom progression.",
            "Prepare specialty consult if risk factors persist.",
        ]
    return [
        "Proceed with routine care pathway.",
        "Provide discharge safety advice if clinician confirms low risk.",
        "Reassess if symptoms worsen or new red flags appear.",
    ]


def recommend_doctor(p: PatientInput, row: pd.Series, severity: dict) -> dict:
    needed = required_specialization(p, row)
    ranked = []
    for doctor in DOCTORS:
        specialty_score = 35 if doctor["specialization"] == needed else 15 if doctor["specialization"] == "Emergency Medicine" else 0
        availability_score = 30 if doctor["available"] else -20
        workload_score = max(0, 20 - doctor["active_cases"] * 3)
        experience_score = min(10, doctor["experience_years"] / 2)
        performance_score = doctor["performance"] * 10
        severity_bonus = 8 if severity["level"] == "High" and doctor["available"] else 0
        score = specialty_score + availability_score + workload_score + experience_score + performance_score + severity_bonus
        ranked.append({**doctor, "match_score": round(score, 1), "required_specialization": needed})
    ranked = sorted(ranked, key=lambda item: item["match_score"], reverse=True)
    return {"recommended": ranked[0], "alternates": ranked[1:4]}


def resource_plan(severity: dict, label: str) -> dict:
    occupancy = DEPARTMENT_STATUS["er_occupancy"]
    if severity["level"] == "High":
        priority = "Immediate bed assignment"
        area = "Resuscitation / monitored ER bay"
    elif label == "Needs ER":
        priority = "Priority ER queue"
        area = "Acute care bay"
    else:
        priority = "Routine queue"
        area = "Fast-track or outpatient review"

    recommendations = []
    if occupancy >= 85:
        recommendations.append("Activate overflow protocol and discharge-ready review.")
    if severity["level"] == "High" and DEPARTMENT_STATUS["icu_beds_available"] <= 4:
        recommendations.append("Notify ICU coordinator early due to limited critical-care capacity.")
    if DEPARTMENT_STATUS["ambulance_queue"] > 2:
        recommendations.append("Reserve handoff capacity for ambulance arrivals.")
    if not recommendations:
        recommendations.append("Current department capacity can support standard routing.")

    return {
        "department_status": DEPARTMENT_STATUS,
        "priority": priority,
        "recommended_area": area,
        "recommendations": recommendations,
    }


def triage_payload(p: PatientInput, prob: float, override: bool, pred: int, row: pd.Series) -> dict:
    label = "Needs ER" if pred else "Non-ER"
    severity = severity_score(row, prob)
    factors = factor_contributions(p, row)
    doctor = recommend_doctor(p, row, severity)
    resources = resource_plan(severity, label)
    return {
        "severity": severity,
        "explanation": prediction_reason(label, factors, severity),
        "top_factors": factors,
        "doctor_recommendation": doctor,
        "clinical_actions": clinical_actions(label, severity, override),
        "resource_allocation": resources,
        "agent_summary": {
            "triage_agent": "Patient data reviewed and critical fields validated.",
            "prediction_agent": f"Model returned {prob:.1%} ER probability.",
            "explainability_agent": "Top clinical contributors generated for review.",
            "doctor_agent": f"Best match selected: {doctor['recommended']['name']}.",
            "resource_agent": f"Routing recommendation: {resources['recommended_area']}.",
        },
    }


@app.get("/")
def root():
    return {"status": "Triage API running", "version": "1.1.0"}


@app.get("/health")
def health():
    return {
        "status": "ok",
        "model_loaded": MODEL is not None,
        "features": len(FEATURES) if FEATURES else 0,
        "threshold": float(THRESHOLD) if THRESHOLD else None,
        "mode": "ensemble_model" if MODEL is not None and FEATURES else "clinical_rules_fallback",
        "agents": ["triage", "prediction", "explainability", "doctor_recommendation", "resource_management"],
    }


@app.post("/predict")
def predict(p: PatientInput):
    row = pd.DataFrame([build_row(p)])
    prob, mode, threshold = predict_probability(row)
    prob, override = adjust_probability(prob, row.iloc[0])
    pred = int(prob >= threshold)
    intelligence = triage_payload(p, prob, override, pred, row.iloc[0])
    return {
        "prediction": pred,
        "label": "Needs ER" if pred else "Non-ER",
        "probability_er": round(prob, 4),
        "probability_non_er": round(1 - prob, 4),
        "risk_level": risk(prob),
        "threshold": float(threshold),
        "mode": mode,
        "override": override,
        **intelligence,
    }


@app.post("/predict/batch")
def predict_batch(batch: BatchInput):
    df = pd.DataFrame([build_row(p) for p in batch.patients])
    if MODEL is not None and FEATURES:
        probs = run_inference(df)
        threshold = float(THRESHOLD)
        mode = "ensemble_model"
    else:
        probs = np.array([rule_based_probability(row) for _, row in df.iterrows()])
        threshold = 0.50
        mode = "clinical_rules_fallback"
    results = []
    for index, row in df.iterrows():
        prob = float(probs[index])
        prob, override = adjust_probability(prob, row)
        pred = int(prob >= threshold)
        label = "Needs ER" if pred else "Non-ER"
        severity = severity_score(row, prob)
        factors = factor_contributions(batch.patients[index], row)
        results.append({
            "index": index,
            "label": label,
            "probability_er": round(float(prob), 4),
            "risk_level": risk(float(prob)),
            "mode": mode,
            "override": override,
            "severity_score": severity["score"],
            "severity_level": severity["level"],
            "explanation": prediction_reason(label, factors, severity),
        })
    return {
        "total": len(results),
        "needs_er": int(sum(1 for item in results if item["label"] == "Needs ER")),
        "non_er": int(sum(1 for item in results if item["label"] == "Non-ER")),
        "results": results,
    }


@app.post("/triage/agent")
def triage_agent(p: PatientInput):
    return predict(p)


@app.post("/triage/agentic")
def triage_agentic(p: PatientInput):
    patient_data = {
        "temperature": p.temperature,
        "heartrate": p.heartrate,
        "resprate": p.resprate,
        "o2sat": p.o2sat,
        "sbp": p.sbp,
        "dbp": p.dbp,
        "pain": p.pain,
        "complaint_group": p.complaint_group or "unknown",
        "gender": p.gender or "Unknown",
        "arrival_transport": p.arrival_transport or "Unknown",
        "age_at_admission": p.age_at_admission or 45,
        "height_cm": p.height_cm,
        "weight_kg": p.weight_kg,
        "bmi": p.bmi,
        "acuity": p.acuity or 3,
        "has_hypertension": p.has_hypertension or 0,
        "has_diabetes": p.has_diabetes or 0,
        "has_cardiac": p.has_cardiac or 0,
        "has_respiratory": p.has_respiratory or 0,
        "has_renal": p.has_renal or 0,
        "has_sepsis": p.has_sepsis or 0,
        "prior_admission_count": p.prior_admission_count or 0,
    }
    try:
        result = run_agentic_triage(patient_data)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Agentic triage failed: {exc}") from exc

    return {
        **result,
        "patient_summary": patient_data,
        "features": [
            "Multi-step autonomous planning",
            "Tool calling for vitals, history, ML prediction, doctor routing, and resources",
            "Short-term memory of observations and tool outputs",
            "Auditable plan and tool trace",
            "Optional Gemini orchestration when GEMINI_API_KEY or GOOGLE_API_KEY is configured",
        ],
    }


@app.get("/compare/agentic-vs-traditional")
def compare_agentic_vs_traditional():
    return {
        "traditional_approach": {
            "endpoint": "/predict",
            "architecture": "Input -> feature row -> model/rules -> response",
            "iterations": 1,
            "tools": [],
            "memory": False,
            "planning": False,
        },
        "agentic_ai_approach": {
            "endpoint": "/triage/agentic",
            "architecture": "Input -> plan -> tool loop -> memory -> final decision",
            "iterations": "multiple tool steps",
            "tools": [
                "assess_patient_vitals",
                "assess_patient_history",
                "run_ml_model_prediction",
                "determine_required_specialization",
                "find_available_specialist",
                "check_department_resources",
                "generate_triage_report",
            ],
            "memory": True,
            "planning": True,
            "llm_orchestration": "Optional via Google Gemini when GEMINI_API_KEY or GOOGLE_API_KEY is configured",
        },
    }


@app.get("/resources")
def resources():
    return {"department_status": DEPARTMENT_STATUS, "doctors": DOCTORS}


@app.get("/model/info")
def model_info():
    return {
        "model": "Stacking Ensemble (CatBoost + LightGBM + XGBoost + RF -> Logistic Regression)",
        "dataset": "MIMIC-IV ED",
        "records": 387835,
        "features": FEATURES or [],
        "threshold": float(THRESHOLD) if THRESHOLD else None,
        "decision_support": [
            "Human-readable prediction reasoning",
            "Severity score and triage level",
            "Doctor recommendation",
            "Resource allocation guidance",
            "Multi-agent workflow summary",
        ],
    }


if __name__ == "__main__":
    uvicorn.run("backend:app", host="0.0.0.0", port=8000, reload=True)
