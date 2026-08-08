from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import joblib
import pandas as pd


COMPLAINT_MAP = {
    "chest_pain": 0,
    "dyspnea": 1,
    "altered_ms": 2,
    "trauma": 3,
    "abdominal": 4,
    "cardiac": 5,
    "fever_infection": 6,
    "neurological": 7,
    "urological": 8,
    "psychiatric": 9,
    "pain_general": 10,
    "other": 11,
    "unknown": 12,
}
HIGH_ACUITY = {"chest_pain", "dyspnea", "altered_ms", "cardiac", "fever_infection"}
TRANSPORT_MAP = {"Ambulance": 0, "Walk-in": 1, "Police": 2, "Other": 3, "Unknown": 4}
GENDER_MAP = {"Male": 1, "Female": 0, "Unknown": 2}


DOCTORS = [
    {
        "name": "Dr. Asha Menon",
        "specialization": "Emergency Medicine",
        "available": True,
        "active_cases": 4,
        "experience_years": 13,
        "performance": 0.94,
    },
    {
        "name": "Dr. Rohan Mehta",
        "specialization": "Cardiology",
        "available": True,
        "active_cases": 2,
        "experience_years": 11,
        "performance": 0.96,
    },
    {
        "name": "Dr. Nisha Rao",
        "specialization": "Pulmonology",
        "available": True,
        "active_cases": 3,
        "experience_years": 9,
        "performance": 0.92,
    },
    {
        "name": "Dr. Karan Shah",
        "specialization": "Trauma Surgery",
        "available": False,
        "active_cases": 6,
        "experience_years": 15,
        "performance": 0.95,
    },
    {
        "name": "Dr. Farah Khan",
        "specialization": "Internal Medicine",
        "available": True,
        "active_cases": 1,
        "experience_years": 8,
        "performance": 0.90,
    },
]

DEPARTMENT_STATUS = {
    "er_occupancy": 72,
    "icu_beds_available": 4,
    "general_beds_available": 18,
    "ambulance_queue": 3,
    "average_wait_minutes": 26,
}


TOOLS = [
    {
        "name": "assess_patient_vitals",
        "description": "Assess vital signs, derived indices, critical flags, and vital stability.",
        "input_schema": {
            "type": "object",
            "properties": {
                "temperature": {"type": "number"},
                "heartrate": {"type": "number"},
                "resprate": {"type": "number"},
                "o2sat": {"type": "number"},
                "sbp": {"type": "number"},
                "dbp": {"type": "number"},
                "pain": {"type": "number"},
            },
            "required": ["temperature", "heartrate", "resprate", "o2sat", "sbp", "dbp"],
        },
    },
    {
        "name": "assess_patient_history",
        "description": "Assess age, comorbidities, prior admissions, and history-based risk.",
        "input_schema": {
            "type": "object",
            "properties": {
                "age_at_admission": {"type": "number"},
                "has_hypertension": {"type": "integer"},
                "has_diabetes": {"type": "integer"},
                "has_cardiac": {"type": "integer"},
                "has_respiratory": {"type": "integer"},
                "has_renal": {"type": "integer"},
                "has_sepsis": {"type": "integer"},
                "prior_admission_count": {"type": "integer"},
            },
            "required": ["age_at_admission"],
        },
    },
    {
        "name": "run_ml_model_prediction",
        "description": "Run the trained ER triage model, or clinical rules if the model is unavailable.",
        "input_schema": {
            "type": "object",
            "properties": {"patient_data": {"type": "object"}},
            "required": ["patient_data"],
        },
    },
    {
        "name": "determine_required_specialization",
        "description": "Choose the clinical specialization based on complaint, vitals, and shock index.",
        "input_schema": {
            "type": "object",
            "properties": {
                "complaint_group": {"type": "string"},
                "o2sat": {"type": "number"},
                "resprate": {"type": "number"},
                "shock_index": {"type": "number"},
            },
            "required": ["complaint_group"],
        },
    },
    {
        "name": "find_available_specialist",
        "description": "Rank available doctors using specialization match, load, experience, and performance.",
        "input_schema": {
            "type": "object",
            "properties": {
                "specialization": {"type": "string"},
                "severity_level": {"type": "string", "enum": ["Low", "Medium", "High"]},
            },
            "required": ["specialization"],
        },
    },
    {
        "name": "check_department_resources",
        "description": "Check ER load, bed availability, queue pressure, and routing options.",
        "input_schema": {
            "type": "object",
            "properties": {
                "severity_level": {"type": "string", "enum": ["Low", "Medium", "High"]},
                "label": {"type": "string"},
            },
            "required": ["severity_level"],
        },
    },
    {
        "name": "generate_triage_report",
        "description": "Generate the final triage decision, explanation, and action plan.",
        "input_schema": {
            "type": "object",
            "properties": {
                "patient_data": {"type": "object"},
                "vitals": {"type": "object"},
                "history": {"type": "object"},
                "prediction": {"type": "object"},
                "specialization": {"type": "object"},
                "doctor": {"type": "object"},
                "resources": {"type": "object"},
            },
            "required": ["patient_data", "vitals", "history", "prediction", "specialization", "doctor", "resources"],
        },
    },
]


@dataclass
class AgentMemory:
    observations: dict[str, Any] = field(default_factory=dict)
    tool_trace: list[dict[str, Any]] = field(default_factory=list)
    plan: list[dict[str, str]] = field(default_factory=list)

    def remember_tool(self, tool_name: str, tool_input: dict[str, Any], result: dict[str, Any]) -> None:
        self.observations[tool_name] = result
        self.tool_trace.append(
            {
                "step": len(self.tool_trace) + 1,
                "tool": tool_name,
                "input": tool_input,
                "observation": result,
            }
        )


class ToolExecutor:
    def __init__(self, base_dir: Path | None = None):
        self.base_dir = base_dir or Path(__file__).resolve().parent
        self.doctors = [doctor.copy() for doctor in DOCTORS]
        self.department_status = DEPARTMENT_STATUS.copy()
        self._model = None
        self._features = None
        self._threshold = None

    def assess_patient_vitals(
        self,
        temperature: float,
        heartrate: float,
        resprate: float,
        o2sat: float,
        sbp: float,
        dbp: float,
        pain: float = 0,
    ) -> dict[str, Any]:
        critical_flags = []
        warning_flags = []
        shock_index = heartrate / sbp if sbp > 0 else 0
        pulse_pressure = sbp - dbp
        mean_arterial_pressure = (sbp + 2 * dbp) / 3

        if heartrate <= 40 or heartrate >= 140:
            critical_flags.append(f"Critical heart rate: {heartrate:.0f} bpm")
        elif heartrate <= 50 or heartrate >= 120:
            warning_flags.append(f"Abnormal heart rate: {heartrate:.0f} bpm")

        if sbp <= 80 or sbp >= 180:
            critical_flags.append(f"Critical blood pressure: {sbp:.0f}/{dbp:.0f} mmHg")
        elif sbp <= 90 or sbp >= 160:
            warning_flags.append(f"Concerning systolic pressure: {sbp:.0f} mmHg")

        if o2sat <= 90:
            critical_flags.append(f"Severe hypoxemia: O2 saturation {o2sat:.1f}%")
        elif o2sat < 95:
            warning_flags.append(f"Low oxygen saturation: {o2sat:.1f}%")

        if resprate <= 10 or resprate >= 30:
            critical_flags.append(f"Critical respiratory rate: {resprate:.0f}/min")
        elif resprate <= 12 or resprate >= 24:
            warning_flags.append(f"Abnormal respiratory rate: {resprate:.0f}/min")

        if temperature <= 35 or temperature >= 39.5:
            critical_flags.append(f"Critical temperature: {temperature:.1f} C")
        elif temperature <= 36 or temperature >= 38.3:
            warning_flags.append(f"Abnormal temperature: {temperature:.1f} C")

        if shock_index > 1.2:
            critical_flags.append(f"High shock index: {shock_index:.2f}")
        elif shock_index > 0.9:
            warning_flags.append(f"Elevated shock index: {shock_index:.2f}")

        if pulse_pressure <= 20:
            warning_flags.append(f"Narrow pulse pressure: {pulse_pressure:.0f} mmHg")
        if pain >= 8:
            warning_flags.append(f"Severe pain score: {pain:.0f}/10")

        return {
            "critical_flags": critical_flags,
            "warning_flags": warning_flags,
            "is_critical": bool(critical_flags),
            "vitals_stability": "Unstable" if critical_flags else "Guarded" if warning_flags else "Stable",
            "shock_index": round(shock_index, 3),
            "pulse_pressure": round(pulse_pressure, 1),
            "map": round(mean_arterial_pressure, 1),
        }

    def assess_patient_history(
        self,
        age_at_admission: float = 45,
        has_hypertension: int = 0,
        has_diabetes: int = 0,
        has_cardiac: int = 0,
        has_respiratory: int = 0,
        has_renal: int = 0,
        has_sepsis: int = 0,
        prior_admission_count: int = 0,
    ) -> dict[str, Any]:
        comorbidities = []
        if has_hypertension:
            comorbidities.append("Hypertension")
        if has_diabetes:
            comorbidities.append("Diabetes")
        if has_cardiac:
            comorbidities.append("Cardiac disease")
        if has_respiratory:
            comorbidities.append("Respiratory disease")
        if has_renal:
            comorbidities.append("Renal disease")
        if has_sepsis:
            comorbidities.append("Sepsis")

        risk_points = len(comorbidities) * 8
        risk_points += 12 if age_at_admission >= 70 else 5 if age_at_admission >= 60 else 0
        risk_points += 8 if prior_admission_count >= 3 else 3 if prior_admission_count else 0

        return {
            "age_risk": "High" if age_at_admission >= 70 else "Moderate" if age_at_admission >= 60 else "Low",
            "comorbidities": comorbidities,
            "comorbidity_count": len(comorbidities),
            "prior_admission_count": prior_admission_count,
            "history_risk_points": risk_points,
        }

    def run_ml_model_prediction(self, patient_data: dict[str, Any]) -> dict[str, Any]:
        row = self._build_feature_row(patient_data)
        model, features, threshold = self._load_model()
        model_error = None
        if model is not None and features:
            try:
                df = pd.DataFrame([row])
                for column in features:
                    if column not in df.columns:
                        df[column] = 0
                probability = float(model.predict_proba(df[features])[0, 1])
                source = "ensemble_model"
            except Exception as exc:
                probability = self._rule_based_probability(row)
                threshold = 0.50
                source = "clinical_rules_fallback_after_model_error"
                model_error = str(exc)
        else:
            probability = self._rule_based_probability(row)
            threshold = 0.50
            source = "clinical_rules_fallback"

        override = self._is_critical_case(row)
        if override:
            probability = max(probability, 0.98)

        return {
            "probability_er": round(probability, 4),
            "probability_non_er": round(1 - probability, 4),
            "threshold": float(threshold),
            "label": "Needs ER" if probability >= float(threshold) else "Non-ER",
            "risk_level": "HIGH" if probability >= 0.75 else "MEDIUM" if probability >= 0.50 else "LOW",
            "model_source": source,
            "model_error": model_error,
            "critical_override": override,
            "feature_snapshot": {
                "shock_index": round(row["shock_index"], 3),
                "pulse_pressure": round(row["pulse_pressure"], 1),
                "bmi": round(row["bmi"], 1),
                "high_acuity_complaint": bool(row["high_acuity_complaint"]),
            },
        }

    def determine_required_specialization(
        self,
        complaint_group: str,
        o2sat: float = 95,
        resprate: float = 16,
        shock_index: float = 0.8,
    ) -> dict[str, Any]:
        complaint = (complaint_group or "unknown").lower()
        if complaint in {"chest_pain", "cardiac"} or shock_index > 1.0:
            specialization = "Cardiology"
            reason = "Cardiac complaint or hemodynamic instability."
        elif complaint == "dyspnea" or o2sat < 94 or resprate >= 24:
            specialization = "Pulmonology"
            reason = "Respiratory complaint or oxygenation concern."
        elif complaint == "trauma":
            specialization = "Trauma Surgery"
            reason = "Trauma presentation requires surgical readiness."
        elif complaint in {"fever_infection", "abdominal", "urological"}:
            specialization = "Internal Medicine"
            reason = "Medical presentation fits internal medicine review."
        else:
            specialization = "Emergency Medicine"
            reason = "General emergency triage pathway."
        return {"specialization": specialization, "reason": reason}

    def find_available_specialist(self, specialization: str, severity_level: str = "Medium") -> dict[str, Any]:
        ranked = []
        for doctor in self.doctors:
            specialty_score = 40 if doctor["specialization"] == specialization else 18 if doctor["specialization"] == "Emergency Medicine" else 0
            availability_score = 30 if doctor["available"] else -25
            workload_score = max(0, 18 - doctor["active_cases"] * 3)
            experience_score = min(12, doctor["experience_years"] / 1.5)
            performance_score = doctor["performance"] * 12
            severity_bonus = 6 if severity_level == "High" and doctor["available"] else 0
            ranked.append(
                {
                    **doctor,
                    "required_specialization": specialization,
                    "match_score": round(
                        specialty_score
                        + availability_score
                        + workload_score
                        + experience_score
                        + performance_score
                        + severity_bonus,
                        1,
                    ),
                }
            )

        ranked.sort(key=lambda doctor: doctor["match_score"], reverse=True)
        return {
            "recommended": ranked[0],
            "alternates": ranked[1:4],
            "assignment_status": "assigned" if ranked[0]["available"] else "queue_required",
        }

    def check_department_resources(self, severity_level: str = "Medium", label: str = "Non-ER") -> dict[str, Any]:
        if severity_level == "High":
            priority = "Immediate bed assignment"
            recommended_area = "Resuscitation / monitored ER bay"
            recommended_bed_type = "ICU"
        elif label == "Needs ER":
            priority = "Priority ER queue"
            recommended_area = "Acute care bay"
            recommended_bed_type = "General"
        else:
            priority = "Routine queue"
            recommended_area = "Fast-track or outpatient review"
            recommended_bed_type = "General"

        recommendations = []
        if self.department_status["er_occupancy"] >= 85:
            recommendations.append("Activate overflow protocol.")
        if severity_level == "High" and self.department_status["icu_beds_available"] <= 4:
            recommendations.append("Notify ICU coordinator early due to limited critical-care beds.")
        if self.department_status["ambulance_queue"] > 2:
            recommendations.append("Reserve handoff capacity for ambulance arrivals.")
        if not recommendations:
            recommendations.append("Current department capacity supports standard routing.")

        bed_available = (
            self.department_status["icu_beds_available"] > 0
            if recommended_bed_type == "ICU"
            else self.department_status["general_beds_available"] > 0
        )

        return {
            "department_status": self.department_status,
            "priority": priority,
            "recommended_area": recommended_area,
            "recommended_bed_type": recommended_bed_type,
            "bed_available": bed_available,
            "recommendations": recommendations,
        }

    def generate_triage_report(
        self,
        patient_data: dict[str, Any],
        vitals: dict[str, Any],
        history: dict[str, Any],
        prediction: dict[str, Any],
        specialization: dict[str, Any],
        doctor: dict[str, Any],
        resources: dict[str, Any],
    ) -> dict[str, Any]:
        if "recommended" not in doctor:
            doctor = {"recommended": doctor, "alternates": [], "assignment_status": "assigned"}

        severity = self._severity(vitals, history, prediction, patient_data)
        label = prediction["label"]
        critical_findings = vitals["critical_flags"]
        top_factors = self._top_factors(patient_data, vitals, history, prediction)

        if severity["level"] == "High":
            actions = [
                "Move patient to monitored emergency bay.",
                "Alert senior clinician and assigned specialist.",
                "Repeat vitals and prepare escalation resources.",
            ]
        elif label == "Needs ER":
            actions = [
                "Prioritize clinician review in the next queue cycle.",
                "Repeat abnormal vitals and monitor symptom progression.",
                "Prepare specialty consult if risk factors persist.",
            ]
        else:
            actions = [
                "Proceed with routine care pathway.",
                "Provide safety-net advice after clinician review.",
                "Reassess if symptoms worsen or new red flags appear.",
            ]

        return {
            "prediction": 1 if label == "Needs ER" else 0,
            "label": label,
            "probability_er": prediction["probability_er"],
            "probability_non_er": prediction["probability_non_er"],
            "risk_level": prediction["risk_level"],
            "threshold": prediction["threshold"],
            "mode": prediction["model_source"],
            "override": prediction["critical_override"],
            "severity": severity,
            "explanation": self._explain_decision(label, severity, top_factors, critical_findings),
            "top_factors": top_factors,
            "clinical_actions": actions,
            "doctor_recommendation": doctor,
            "resource_allocation": resources,
            "critical_findings": critical_findings,
            "required_specialization": specialization,
        }

    def execute(self, tool_name: str, tool_input: dict[str, Any]) -> dict[str, Any]:
        tool: Callable[..., dict[str, Any]] | None = getattr(self, tool_name, None)
        if tool is None:
            return {"error": f"Unknown tool: {tool_name}"}
        return tool(**tool_input)

    def _load_model(self) -> tuple[Any, list[str] | None, float]:
        if self._model is not None or self._features is not None:
            return self._model, self._features, self._threshold or 0.50
        try:
            self._model = joblib.load(self.base_dir / "stacking_final.pkl")
            self._features = joblib.load(self.base_dir / "features_final.pkl")
            self._threshold = float(joblib.load(self.base_dir / "threshold_final.pkl"))
        except Exception:
            self._model = None
            self._features = None
            self._threshold = 0.50
        return self._model, self._features, self._threshold

    def _build_feature_row(self, patient_data: dict[str, Any]) -> dict[str, Any]:
        bmi = self._compute_bmi(patient_data)
        complaint = (patient_data.get("complaint_group") or "unknown").lower()
        sbp = float(patient_data.get("sbp") or 0)
        dbp = float(patient_data.get("dbp") or 0)
        heartrate = float(patient_data.get("heartrate") or 0)
        return {
            "temperature": float(patient_data.get("temperature") or 37),
            "heartrate": heartrate,
            "resprate": float(patient_data.get("resprate") or 16),
            "o2sat": float(patient_data.get("o2sat") or 98),
            "sbp": sbp,
            "dbp": dbp,
            "pain": float(patient_data.get("pain") or 0),
            "pulse_pressure": sbp - dbp,
            "shock_index": heartrate / sbp if sbp > 0 else 0,
            "map": (sbp + 2 * dbp) / 3 if sbp and dbp else 0,
            "complaint_enc": COMPLAINT_MAP.get(complaint, 12),
            "high_acuity_complaint": int(complaint in HIGH_ACUITY),
            "gender_enc": GENDER_MAP.get(patient_data.get("gender") or "Unknown", 2),
            "arrival_transport_enc": TRANSPORT_MAP.get(patient_data.get("arrival_transport") or "Unknown", 4),
            "has_hypertension": int(patient_data.get("has_hypertension") or 0),
            "has_diabetes": int(patient_data.get("has_diabetes") or 0),
            "has_cardiac": int(patient_data.get("has_cardiac") or 0),
            "has_respiratory": int(patient_data.get("has_respiratory") or 0),
            "has_renal": int(patient_data.get("has_renal") or 0),
            "has_sepsis": int(patient_data.get("has_sepsis") or 0),
            "age_at_admission": float(patient_data.get("age_at_admission") or 45),
            "prior_admission_count": int(patient_data.get("prior_admission_count") or 0),
            "acuity": float(patient_data.get("acuity") or 3),
            "height_cm": float(patient_data.get("height_cm") or 0),
            "weight_kg": float(patient_data.get("weight_kg") or 0),
            "bmi": bmi,
            "bmi_risk": 1 if bmi >= 30 else 0,
        }

    def _compute_bmi(self, patient_data: dict[str, Any]) -> float:
        bmi = patient_data.get("bmi")
        if bmi is not None and float(bmi) > 0:
            return float(bmi)
        height_cm = patient_data.get("height_cm")
        weight_kg = patient_data.get("weight_kg")
        if height_cm and weight_kg and float(height_cm) > 0:
            return float(weight_kg) / ((float(height_cm) / 100) ** 2)
        return 24.9

    def _rule_based_probability(self, row: dict[str, Any]) -> float:
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

    def _is_critical_case(self, row: dict[str, Any]) -> bool:
        return (
            row["heartrate"] <= 40
            or row["heartrate"] >= 140
            or row["sbp"] <= 80
            or row["sbp"] >= 180
            or row["o2sat"] <= 90
            or row["resprate"] <= 10
            or row["resprate"] >= 30
            or row["temperature"] <= 35
            or row["temperature"] >= 39.5
            or row["shock_index"] > 1.2
            or row["pulse_pressure"] <= 20
            or row["bmi"] >= 40
        )

    def _severity(
        self,
        vitals: dict[str, Any],
        history: dict[str, Any],
        prediction: dict[str, Any],
        patient_data: dict[str, Any],
    ) -> dict[str, Any]:
        score = int(round(prediction["probability_er"] * 45))
        score += 20 if vitals["is_critical"] else 8 if vitals["warning_flags"] else 0
        score += min(18, history["history_risk_points"])
        if (patient_data.get("complaint_group") or "unknown").lower() in HIGH_ACUITY:
            score += 10
        score = max(0, min(score, 100))
        level = "High" if score >= 70 else "Medium" if score >= 40 else "Low"
        description = {
            "High": "Immediate emergency intervention required",
            "Medium": "Requires prompt medical attention",
            "Low": "Routine care recommended",
        }[level]
        return {"score": score, "level": level, "description": description}

    def _top_factors(
        self,
        patient_data: dict[str, Any],
        vitals: dict[str, Any],
        history: dict[str, Any],
        prediction: dict[str, Any],
    ) -> list[dict[str, Any]]:
        factors = []
        for flag in vitals["critical_flags"]:
            factors.append({"feature": "Critical vital sign", "impact": 0.45, "detail": flag})
        for flag in vitals["warning_flags"]:
            factors.append({"feature": "Abnormal vital sign", "impact": 0.22, "detail": flag})
        complaint = (patient_data.get("complaint_group") or "unknown").lower()
        if complaint in HIGH_ACUITY:
            factors.append(
                {
                    "feature": "Chief complaint",
                    "impact": 0.35,
                    "detail": f"{complaint.replace('_', ' ')} is a high-acuity complaint.",
                }
            )
        if history["comorbidities"]:
            factors.append(
                {
                    "feature": "Comorbidities",
                    "impact": 0.25,
                    "detail": ", ".join(history["comorbidities"]),
                }
            )
        if history["age_risk"] != "Low":
            factors.append(
                {
                    "feature": "Age",
                    "impact": 0.18,
                    "detail": f"Age risk is {history['age_risk'].lower()}.",
                }
            )
        factors.append(
            {
                "feature": "ER probability",
                "impact": round(prediction["probability_er"], 3),
                "detail": f"{prediction['model_source']} estimated {prediction['probability_er']:.1%} ER probability.",
            }
        )
        return sorted(factors, key=lambda factor: abs(factor["impact"]), reverse=True)[:6]

    def _explain_decision(
        self,
        label: str,
        severity: dict[str, Any],
        top_factors: list[dict[str, Any]],
        critical_findings: list[str],
    ) -> str:
        if critical_findings:
            return (
                f"Patient classified as {label} with {severity['level'].lower()} severity "
                f"because critical findings were detected: {critical_findings[0]}"
            )
        positive = [factor["feature"].lower() for factor in top_factors if factor["impact"] > 0]
        if positive:
            return (
                f"Patient classified as {label} with {severity['level'].lower()} severity "
                f"based on {', '.join(positive[:3])}."
            )
        return f"Patient classified as {label} because available clinical indicators remain stable."


class TriageAgent:
    def __init__(self, use_llm: bool | None = None):
        self.tool_executor = ToolExecutor()
        self.memory = AgentMemory()
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.use_llm = bool(self.api_key) if use_llm is None else use_llm
        self.model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")

    def triage_patient(self, patient_data: dict[str, Any]) -> dict[str, Any]:
        self.memory.plan = self._create_plan()
        if self.use_llm:
            try:
                return self._triage_with_gemini(patient_data)
            except Exception as exc:
                self.memory.tool_trace.append(
                    {
                        "step": len(self.memory.tool_trace) + 1,
                        "tool": "llm_agent",
                        "input": {"provider": "google_gemini", "model": self.model},
                        "observation": {"fallback": "local_agent", "reason": str(exc)},
                    }
                )
        return self._triage_locally(patient_data, provider="local_tool_agent")

    def _create_plan(self) -> list[dict[str, str]]:
        return [
            {"step": "Assess immediate vital risk", "status": "pending"},
            {"step": "Evaluate history and comorbidities", "status": "pending"},
            {"step": "Run predictive triage model", "status": "pending"},
            {"step": "Select specialization and doctor", "status": "pending"},
            {"step": "Check department resources", "status": "pending"},
            {"step": "Generate triage report", "status": "pending"},
        ]

    def _mark_plan(self, step_index: int, status: str = "completed") -> None:
        self.memory.plan[step_index]["status"] = status

    def _call_tool(self, tool_name: str, tool_input: dict[str, Any]) -> dict[str, Any]:
        result = self.tool_executor.execute(tool_name, tool_input)
        self.memory.remember_tool(tool_name, tool_input, result)
        return result

    def _triage_locally(self, patient_data: dict[str, Any], provider: str) -> dict[str, Any]:
        vitals = self._call_tool(
            "assess_patient_vitals",
            {
                "temperature": patient_data.get("temperature"),
                "heartrate": patient_data.get("heartrate"),
                "resprate": patient_data.get("resprate"),
                "o2sat": patient_data.get("o2sat"),
                "sbp": patient_data.get("sbp"),
                "dbp": patient_data.get("dbp"),
                "pain": patient_data.get("pain", 0),
            },
        )
        self._mark_plan(0)

        history = self._call_tool(
            "assess_patient_history",
            {
                "age_at_admission": patient_data.get("age_at_admission", 45),
                "has_hypertension": patient_data.get("has_hypertension", 0),
                "has_diabetes": patient_data.get("has_diabetes", 0),
                "has_cardiac": patient_data.get("has_cardiac", 0),
                "has_respiratory": patient_data.get("has_respiratory", 0),
                "has_renal": patient_data.get("has_renal", 0),
                "has_sepsis": patient_data.get("has_sepsis", 0),
                "prior_admission_count": patient_data.get("prior_admission_count", 0),
            },
        )
        self._mark_plan(1)

        prediction = self._call_tool("run_ml_model_prediction", {"patient_data": patient_data})
        self._mark_plan(2)

        specialization = self._call_tool(
            "determine_required_specialization",
            {
                "complaint_group": patient_data.get("complaint_group", "unknown"),
                "o2sat": patient_data.get("o2sat", 95),
                "resprate": patient_data.get("resprate", 16),
                "shock_index": vitals["shock_index"],
            },
        )

        severity_level = "High" if prediction["risk_level"] == "HIGH" or vitals["is_critical"] else "Medium" if prediction["risk_level"] == "MEDIUM" else "Low"
        doctor = self._call_tool(
            "find_available_specialist",
            {
                "specialization": specialization["specialization"],
                "severity_level": severity_level,
            },
        )
        self._mark_plan(3)

        resources = self._call_tool(
            "check_department_resources",
            {"severity_level": severity_level, "label": prediction["label"]},
        )
        self._mark_plan(4)

        report = self._call_tool(
            "generate_triage_report",
            {
                "patient_data": patient_data,
                "vitals": vitals,
                "history": history,
                "prediction": prediction,
                "specialization": specialization,
                "doctor": doctor,
                "resources": resources,
            },
        )
        self._mark_plan(5)

        return {
            **report,
            "is_agentic": True,
            "agent_type": "multi_step_tool_agent",
            "llm_provider": provider,
            "memory": {
                "observations": self.memory.observations,
                "tool_trace": self.memory.tool_trace,
            },
            "agent_plan": self.memory.plan,
            "reasoning_summary": self._reasoning_summary(report, provider),
            "available_tools": [tool["name"] for tool in TOOLS],
        }

    def _triage_with_gemini(self, patient_data: dict[str, Any]) -> dict[str, Any]:
        if not self.api_key:
            raise RuntimeError("Set GEMINI_API_KEY or GOOGLE_API_KEY to enable Gemini orchestration.")

        contents: list[dict[str, Any]] = [
            {
                "role": "user",
                "parts": [
                    {
                        "text": (
                            "You are a medical triage decision-support agent. Use function calls "
                            "to assess vitals, history, prediction, doctor assignment, resources, "
                            "and final report. Do not reveal hidden chain-of-thought; return concise "
                            "clinical rationale and call generate_triage_report when ready.\n\n"
                            f"Patient data:\n{json.dumps(patient_data, indent=2)}"
                        )
                    }
                ],
            }
        ]
        tool_config = {
            "tools": [
                {
                    "function_declarations": [
                        {
                            "name": tool["name"],
                            "description": tool["description"],
                            "parameters": tool["input_schema"],
                        }
                        for tool in TOOLS
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 2048,
            },
        }

        for _ in range(10):
            response = self._gemini_generate(contents, tool_config)
            parts = (
                response.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [])
            )
            function_calls = [part["functionCall"] for part in parts if "functionCall" in part]
            if not function_calls:
                break

            contents.append({"role": "model", "parts": parts})
            function_response_parts = []
            for function_call in function_calls:
                tool_name = function_call["name"]
                tool_input = function_call.get("args", {})
                result = self._call_tool(tool_name, tool_input)
                function_response_parts.append(
                    {"functionResponse": {"name": tool_name, "response": result}}
                )
            contents.append({"role": "function", "parts": function_response_parts})

            if "generate_triage_report" in self.memory.observations:
                report = self.memory.observations["generate_triage_report"]
                for plan_item in self.memory.plan:
                    plan_item["status"] = "completed"
                return {
                    **report,
                    "is_agentic": True,
                    "agent_type": "llm_tool_agent",
                    "llm_provider": "google_gemini",
                    "memory": {
                        "observations": self.memory.observations,
                        "tool_trace": self.memory.tool_trace,
                    },
                    "agent_plan": self.memory.plan,
                    "reasoning_summary": self._reasoning_summary(report, "google_gemini"),
                    "available_tools": [tool["name"] for tool in TOOLS],
                }

        return self._triage_locally(patient_data, provider="local_tool_agent_after_llm")

    def _gemini_generate(self, contents: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, Any]:
        query = urllib.parse.urlencode({"key": self.api_key})
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?{query}"
        payload = {"contents": contents, **config}
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Gemini API error {exc.code}: {detail}") from exc

    def _reasoning_summary(self, report: dict[str, Any], provider: str) -> str:
        doctor_recommendation = report["doctor_recommendation"]
        recommended_doctor = doctor_recommendation.get("recommended", doctor_recommendation)
        doctor = recommended_doctor.get("name", "Triage Queue")
        area = report["resource_allocation"]["recommended_area"]
        return (
            f"{provider} completed {len(self.memory.tool_trace)} tool steps. "
            f"Decision: {report['label']} at {report['severity']['level'].lower()} severity. "
            f"Assigned route: {doctor}, {area}."
        )


def run_agentic_triage(patient_data: dict[str, Any], use_llm: bool | None = None) -> dict[str, Any]:
    agent = TriageAgent(use_llm=use_llm)
    return agent.triage_patient(patient_data)
