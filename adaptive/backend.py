import os
import io
import csv
import traceback
import shutil
import stat
from datetime import datetime, timedelta, time

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from sqlalchemy import UniqueConstraint
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import bcrypt
import bleach
import json
import os
from dotenv import load_dotenv

load_dotenv()
try:
    import google.generativeai as genai
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel("gemini-1.5-flash")
    else:
        gemini_model = None
except ImportError:
    gemini_model = None

# Extraction libs
try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    import docx
except ImportError:
    docx = None

try:
    from PIL import Image
    import pytesseract
except ImportError:
    Image, pytesseract = None, None

try:
    if os.getenv("ENABLE_TRANSFORMER_SUMMARIZER") == "1":
        from transformers import pipeline
        print("Loading summarizer model (this might take a minute)...")
        summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6", revision="a4f8f3e")
        print("Model loaded.")
    else:
        summarizer = None
except Exception as e:
    print(f"Transformer model unavailable: {e}. Falling back to heuristic.")
    summarizer = None


app = Flask(__name__)
CORS(app)

app.config["JWT_SECRET_KEY"] = "super-secure-secret-capstone"
jwt = JWTManager(app)

DEFAULT_DB_PATH = os.path.abspath("hospital_runtime_fresh.db")
os.makedirs(os.path.dirname(DEFAULT_DB_PATH), exist_ok=True)
if not os.getenv("DATABASE_URL") and os.path.exists(DEFAULT_DB_PATH):
    try:
        os.chmod(DEFAULT_DB_PATH, stat.S_IREAD | stat.S_IWRITE)
    except OSError as e:
        print(f"Could not make SQLite DB writable: {e}")

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///" + DEFAULT_DB_PATH.replace("\\", "/"))
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "connect_args": {"timeout": 30, "check_same_thread": False}
}
app.config["REPORT_DIR"] = os.path.join("instance", "reports")
os.makedirs(app.config["REPORT_DIR"], exist_ok=True)

db = SQLAlchemy(app)


@app.errorhandler(Exception)
def handle_unexpected_error(e):
    db.session.rollback()
    print("Unhandled backend error:")
    traceback.print_exc()
    return jsonify({"message": "Backend error. Check the backend terminal for details."}), 500

# -------------------- DB MODELS --------------------

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.LargeBinary, nullable=False)
    role = db.Column(db.String(20), nullable=False) # 'patient' or 'doctor'

class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    name = db.Column(db.String(100), nullable=False)
    mobile = db.Column(db.String(20))
    specialty = db.Column(db.String(100))
    department = db.Column(db.String(100))
    license_number = db.Column(db.String(100))
    max_daily_slots = db.Column(db.Integer, default=8)
    is_available = db.Column(db.Boolean, default=True)
    on_leave = db.Column(db.Boolean, default=False)

    def workload_today(self):
        today = datetime.now().date()
        return Appointment.query.filter(
            Appointment.doctor_id == self.id,
            Appointment.slot_time >= datetime.combine(today, datetime.min.time()),
            Appointment.slot_time < datetime.combine(today + timedelta(days=1), datetime.min.time()),
            Appointment.status == "scheduled"
        ).count()

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    patient_code = db.Column(db.String(50), unique=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    mobile = db.Column(db.String(20))
    symptom = db.Column(db.String(250))
    body_part = db.Column(db.String(50))
    department = db.Column(db.String(100))
    priority = db.Column(db.String(20), default="normal")
    preferred_doctor_id = db.Column(db.Integer, db.ForeignKey("doctor.id"), nullable=True)
    report_path = db.Column(db.String(255), nullable=True)
    report_summary = db.Column(db.Text, nullable=True)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"))
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctor.id"))
    slot_time = db.Column(db.DateTime)
    status = db.Column(db.String(20), default="scheduled") # scheduled | cancelled | completed
    cancelled_by = db.Column(db.String(50), nullable=True)
    cancel_reason = db.Column(db.String(255), nullable=True)
    fine_applied = db.Column(db.Integer, default=0)
    recommended_tests = db.Column(db.String(255), nullable=True)

class DoctorAvailability(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctor.id"))
    date = db.Column(db.Date)
    start_time = db.Column(db.Time)
    end_time = db.Column(db.Time)
    slot_minutes = db.Column(db.Integer, default=30)

with app.app_context():
    db.create_all()

def sanitize(input_str):
    if not input_str:
        return ""
    return bleach.clean(str(input_str), tags=[], strip=True)

# -------------------- PIPELINE HELPERS --------------------

def extract_text(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    text = ""
    try:
        if ext == ".pdf" and pdfplumber:
            with pdfplumber.open(file_path) as pdf:
                text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
        elif ext == ".docx" and docx:
            doc = docx.Document(file_path)
            text = "\n".join([para.text for para in doc.paragraphs])
        elif ext in [".png", ".jpg", ".jpeg"] and Image and pytesseract:
            text = pytesseract.image_to_string(Image.open(file_path))
        else:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
    except Exception as e:
        print(f"Extraction error: {e}")
    return text.strip()

def AI_summarize(text: str) -> str:

    if gemini_model and text:
        try:
            r = gemini_model.generate_content("Summarize this medical report for a doctor plainly:\n\n" + text[:2000])
            if r.text: return r.text.strip()
        except Exception as e:
            print("Gemini summarization fallback triggers.")
    if not text:
        return "No text could be extracted."
    if summarizer:
        try:
            # simple truncation for input max length
            short_text = " ".join(text.split()[:500])
            out = summarizer(short_text, max_length=130, min_length=30, do_sample=False)
            return out[0]['summary_text']
        except Exception as e:
            print(f"AI summarization failed, falling back context: {e}")
    
    sentences = [s.strip() for s in text.replace("\n", " ").split(".") if s.strip()]
    if not sentences:
        return text[:200]
    return ". ".join(sentences[:3]) + "."


# -------------------- ALLOCATION CORE RULES (AI DRIVEN) --------------------

import json

BODY_PART_SPECIALTY_MAP = {
    "Head": "Neurologist",
    "Chest": "Cardiologist",
    "Abdomen": "Gastroenterologist",
    "Pelvis": "Urologist",
    "Legs": "Orthopedist",
    "Arms": "Orthopedist",
    "Skin": "Dermatologist",
}

SYSTEMIC_SYMPTOM_KEYWORDS = ["fever", "weakness", "cold", "cough", "fatigue", "body ache"]
URGENT_SYMPTOM_KEYWORDS = ["chest pain", "breathing", "shortness of breath", "bleeding", "severe", "fainting"]


def find_next_available_slot(doc_id, priority="normal"):
    today = datetime.now().date()
    windows = DoctorAvailability.query.filter_by(doctor_id=doc_id, date=today).all()
    start = (datetime.min + timedelta(hours=9)).time()
    end = (datetime.min + timedelta(hours=17)).time()
    if not windows:
        windows = [type("W", (), {"date": today, "start_time": start, "end_time": end, "slot_minutes": 30})]

    for w in windows:
        start_dt = datetime.combine(w.date, w.start_time)
        end_dt = datetime.combine(w.date, w.end_time)
        step = timedelta(minutes=w.slot_minutes)
        current = start_dt
        while current < end_dt:
            if not Appointment.query.filter_by(doctor_id=doc_id, slot_time=current, status="scheduled").first():
                return current
            current += step

    if priority == "emergency":
        return datetime.now() + timedelta(minutes=15)
    return None


# -------------------- VITALS SHARING --------------------
class Vitals(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.String(120), index=True, nullable=True)
    data = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()


@app.route("/vitals", methods=["POST"])
@jwt_required()
def save_vitals():
    try:
        payload = request.get_json() or {}
        profile_id = payload.get("profile_id") or get_jwt_identity()
        vitals = payload.get("vitals") or payload
        record = Vitals(profile_id=profile_id, data=json.dumps(vitals), timestamp=datetime.utcnow())
        db.session.add(record)
        db.session.commit()
        return jsonify({"status": "ok", "profile_id": profile_id}), 201
    except Exception as e:
        traceback.print_exc()
        return jsonify({"message": "Failed to save vitals", "error": str(e)}), 500


@app.route("/vitals/<profile_id>", methods=["GET"])
def get_vitals(profile_id):
    try:
        record = Vitals.query.filter_by(profile_id=profile_id).order_by(Vitals.timestamp.desc()).first()
        if not record:
            return jsonify({"found": False}), 404
        return jsonify({"found": True, "profile_id": profile_id, "vitals": json.loads(record.data), "timestamp": record.timestamp.isoformat()})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"message": "Failed to fetch vitals", "error": str(e)}), 500


@app.route("/vitals/public", methods=["POST"])
def save_vitals_public():
    try:
        payload = request.get_json() or {}
        profile_id = payload.get("profile_id")
        vitals = payload.get("vitals") or payload
        record = Vitals(profile_id=profile_id, data=json.dumps(vitals), timestamp=datetime.utcnow())
        db.session.add(record)
        db.session.commit()
        return jsonify({"status": "ok", "profile_id": profile_id}), 201
    except Exception as e:
        traceback.print_exc()
        return jsonify({"message": "Failed to save vitals", "error": str(e)}), 500


def infer_department(patient_details):
    symptom_lower = patient_details.get("symptom", "").lower()
    body_part = patient_details.get("body_part")
    department = BODY_PART_SPECIALTY_MAP.get(body_part, "General Physician")
    reason = f"body area '{body_part or 'not specified'}' maps to {department}"

    if any(keyword in symptom_lower for keyword in SYSTEMIC_SYMPTOM_KEYWORDS):
        department = "General Physician"
        reason = "systemic symptoms such as fever/cough/weakness are best routed to General Physician first"
    if "rash" in symptom_lower or "skin" in symptom_lower or body_part == "Skin":
        department = "Dermatologist"
        reason = "skin/rash signals are best routed to Dermatologist"

    return department, reason

class LegacyTriageAgent:
    def __init__(self, gemini_model=None):
        self.model = gemini_model

    def run_triage(self, patient_details, available_doctors):
        """
        Runs triage logic. Parses symptoms, determines required specialty, balances workloads, 
        and produces a step-by-step Explainable AI (XAI) reasoning trace.
        """
        # 1. Try proper Agentic AI via Gemini if API key is configured
        if self.model and available_doctors:
            docs_json = json.dumps([
                {
                    "id": d["id"], 
                    "name": d["name"], 
                    "specialty": d["specialty"], 
                    "workload_today": d["workload_today"],
                    "max_daily_slots": d.get("max_daily_slots", 8)
                } for d in available_doctors
            ])
            
            prompt = f"""You are an expert Clinical Triage Agent. Your goal is to allocate the best doctor for a patient and provide a detailed, explainable AI (XAI) rationale.
            
Patient details:
- Symptoms: {patient_details.get("symptom")}
- Affected Body Part: {patient_details.get("body_part")}
- Priority Level: {patient_details.get("priority", "normal")}

Available Doctors:
{docs_json}

Triage Agent Workflow:
1. **Analyze Symptoms**: Match the patient's symptoms/body part to the correct department/specialty (e.g. Chest -> Cardiologist, Head -> Neurologist, Abdomen -> Gastroenterologist, Pelvis -> Urologist, Legs/Arms -> Orthopedist, Skin -> Dermatologist, Fever/Cold/Cough -> General Physician).
2. **Workload Analysis**: Check the workload_today vs max_daily_slots of the specialists. Choose the doctor with the least workload to balance capacity. Fallback to General Physician if no specialist is available.
3. **Reasoning Trace**: Explain exactly why this allocation is made, detailing the symptom matching, department alignment, and workload considerations.

You must respond ONLY with a valid JSON block containing the following keys (do not include any conversational text outside the JSON block):
{{
  "doctor_id": <int>,
  "confidence": <float between 0.0 and 1.0>,
  "priority": "<High or Normal>",
  "department": "<Specialty name>",
  "explanation": "<A detailed markdown description of the decision-making process, including steps 1, 2, and 3 of the workflow>"
}}"""
            try:
                resp = self.model.generate_content(prompt)
                out = resp.text.strip().replace('```json', '').replace('```', '').strip()
                parsed = json.loads(out)
                
                selected_doc = next((d for d in available_doctors if d['id'] == parsed.get('doctor_id')), None)
                if selected_doc:
                    return {
                        "doctor_id": selected_doc["id"],
                        "doctor_name": f"Dr. {selected_doc['name']}",
                        "specialization": selected_doc['specialty'],
                        "department": parsed.get("department", selected_doc['specialty']),
                        "confidence": parsed.get("confidence", 0.95),
                        "priority": parsed.get("priority", "Normal"),
                        "explanation": parsed.get("explanation", "Reasoning generated successfully by AI.")
                    }
            except Exception as e:
                print(f"Gemini Triage Agent failed, running fallback: {e}")

        # 2. Proper Heuristic-Based Triage Agent with identical Workflow & Explainable AI output
        mapping = {
            "Head": "Neurologist", "Chest": "Cardiologist", "Abdomen": "Gastroenterologist",
            "Pelvis": "Urologist", "Legs": "Orthopedist", "Arms": "Orthopedist", "Skin": "Dermatologist"
        }
        
        symptom_lower = patient_details.get("symptom", "").lower()
        body_part = patient_details.get("body_part")
        
        # Specialty classification logic
        department = mapping.get(body_part, "General Physician")
        specialty_reason = f"mapped body area '{body_part}' to specialist department '{department}'"
        
        if any(x in symptom_lower for x in ["fever", "weakness", "cold", "cough"]):
            department = "General Physician"
            specialty_reason = f"triage rules redirected patient to General Physician due to systemic symptoms (fever/cold/cough)"
        if "rash" in symptom_lower or "skin" in symptom_lower:
            department = "Dermatologist"
            specialty_reason = f"triage rules matched skin symptoms/rash to Dermatologist"
            
        # Capacity and availability checks
        candidates = [d for d in available_doctors if d["specialty"] == department]
        fallback_used = False
        if not candidates:
            candidates = [d for d in available_doctors if d["specialty"] == "General Physician"]
            if candidates:
                fallback_used = True
                specialty_reason += f". No {department} available; falling back to General Physician"
            else:
                candidates = available_doctors
                if candidates:
                    fallback_used = True
                    specialty_reason += f". No {department} or GP available; falling back to first available doctor"
        
        if not candidates:
            return None
            
        # Load balancing logic
        candidates.sort(key=lambda d: d["workload_today"])
        selected_doc = candidates[0]
        
        confidence = 0.95
        if fallback_used:
            confidence -= 0.15
        if patient_details.get("priority") == "emergency":
            priority_label = "High"
        else:
            priority_label = "Normal"
            
        explanation = f"""#### 🧠 AI Clinical Triage Agent Reasoning Report

**1. Symptom & Specialty Analysis**
- **Symptom:** `{patient_details.get("symptom")}`
- **Anatomical Body Area:** `{body_part}`
- **Specialty Decision:** Selected **{department}** department.
- **Triage Logic:** The agent {specialty_reason}.

**2. Workload & Capacity Evaluation**
- **Target Doctor:** **Dr. {selected_doc['name']}** ({selected_doc['specialty']})
- **Workload Metrics:** Currently has **{selected_doc['workload_today']}** scheduled appointment(s) today (Max Limit: {selected_doc.get('max_daily_slots', 8)}).
- **Load Balancing:** Selected Dr. {selected_doc['name']} as they have the optimal load and available slots to prevent doctor burnout and minimize wait times.

**3. Allocation Decision & Urgency Triaging**
- **Priority Assigned:** `{priority_label} Priority` based on patient priority preference (`{patient_details.get("priority")}`).
- **Confidence Rating:** **{int(confidence * 100)}%**
"""
        return {
            "doctor_id": selected_doc["id"],
            "doctor_name": f"Dr. {selected_doc['name']}",
            "specialization": selected_doc['specialty'],
            "department": department,
            "confidence": confidence,
            "priority": priority_label,
            "explanation": explanation
        }


class TriageAgent:
    def __init__(self, gemini_model=None):
        self.model = gemini_model

    def _score_doctors(self, patient_details, available_doctors):
        department, specialty_reason = infer_department(patient_details)
        symptom_lower = patient_details.get("symptom", "").lower()
        patient_priority = patient_details.get("priority", "normal")
        priority_label = "High" if patient_priority == "emergency" or any(k in symptom_lower for k in URGENT_SYMPTOM_KEYWORDS) else "Normal"
        scored = []

        for doctor in available_doctors:
            max_slots = doctor.get("max_daily_slots", 8) or 8
            workload = doctor.get("workload_today", 0) or 0
            remaining = max(max_slots - workload, 0)
            load_ratio = min(workload / max_slots, 1)
            specialty_match = doctor["specialty"] == department
            gp_fallback = doctor["specialty"] == "General Physician" and not specialty_match
            next_slot = find_next_available_slot(doctor["id"], patient_priority)

            score = 0
            score += 55 if specialty_match else 18 if gp_fallback else 6
            score += max(0, 25 - int(load_ratio * 25))
            score += 12 if next_slot else 0
            score += min(8, remaining)
            if patient_priority == "emergency" and next_slot:
                score += 6

            reasons = [
                "specialty match" if specialty_match else "general fallback" if gp_fallback else "lower specialty fit",
                f"{remaining} slot(s) remaining today",
                "has a bookable slot" if next_slot else "no regular slot found",
            ]

            scored.append({
                **doctor,
                "score": score,
                "department_match": specialty_match,
                "remaining_slots": remaining,
                "load_ratio": load_ratio,
                "next_slot": next_slot.isoformat() if next_slot else None,
                "reasons": reasons,
            })

        scored.sort(key=lambda d: (-d["score"], d["workload_today"], d["name"]))
        if scored and not any(d["department_match"] for d in scored):
            specialty_reason += f"; no {department} doctor was currently available, so fallback doctors were evaluated"

        return department, specialty_reason, priority_label, scored

    def _ask_llm_to_audit(self, patient_details, department, scored_doctors):
        if not self.model or not scored_doctors:
            return None
        docs_json = json.dumps([
            {
                "id": d["id"],
                "name": d["name"],
                "specialty": d["specialty"],
                "score": d["score"],
                "workload_today": d["workload_today"],
                "max_daily_slots": d.get("max_daily_slots", 8),
                "next_slot": d.get("next_slot"),
                "reasons": d["reasons"],
            } for d in scored_doctors[:5]
        ])

        prompt = f"""You are a clinical scheduling agent auditing a deterministic triage ranking.
Patient symptoms: {patient_details.get("symptom")}
Body part: {patient_details.get("body_part")}
Inferred department: {department}
Ranked doctor candidates:
{docs_json}

Choose the safest allocation from the candidates. Respect specialty match, available slot, and workload balancing.
Return only JSON:
{{
  "doctor_id": <int>,
  "confidence": <float between 0 and 1>,
  "audit_note": "<one concise explanation of whether the ranked choice is appropriate>"
}}"""
        try:
            resp = self.model.generate_content(prompt)
            out = resp.text.strip().replace("```json", "").replace("```", "").strip()
            parsed = json.loads(out)
            if any(d["id"] == parsed.get("doctor_id") for d in scored_doctors[:5]):
                return parsed
        except Exception as e:
            print(f"Gemini triage audit failed, continuing with deterministic agent: {e}")
        return None

    def run_triage(self, patient_details, available_doctors):
        if not available_doctors:
            return None

        department, specialty_reason, priority_label, scored_doctors = self._score_doctors(patient_details, available_doctors)
        if not scored_doctors:
            return None

        llm_audit = self._ask_llm_to_audit(patient_details, department, scored_doctors)
        if llm_audit:
            selected_doc = next(d for d in scored_doctors if d["id"] == llm_audit["doctor_id"])
            audit_note = llm_audit.get("audit_note", "Gemini audit accepted the ranked allocation.")
            confidence = float(llm_audit.get("confidence", 0.9))
        else:
            selected_doc = scored_doctors[0]
            audit_note = "Deterministic agent ranking used because no Gemini API audit was available."
            confidence = 0.94 if selected_doc["department_match"] else 0.78

        alternatives = [d for d in scored_doctors if d["id"] != selected_doc["id"]][:4]
        alt_lines = "\n".join([
            f"- Dr. {d['name']} ({d['specialty']}): score {d['score']}; {', '.join(d['reasons'])}."
            for d in alternatives
        ]) or "- No other currently available doctors met the capacity filter."
        selected_reasons = ", ".join(selected_doc["reasons"])

        explanation = f"""#### AI Clinical Triage Agent Reasoning Report

**1. Observe**
- **Symptom:** `{patient_details.get("symptom")}`
- **Anatomical Body Area:** `{patient_details.get("body_part")}`
- **Priority Signal:** `{priority_label}`

**2. Plan**
- Inferred required department: **{department}**
- Reason: {specialty_reason}.

**3. Act: Doctor Scoring**
- **Target Doctor:** **Dr. {selected_doc['name']}** ({selected_doc['specialty']})
- **Score:** `{selected_doc['score']}`
- **Why this doctor:** {selected_reasons}.
- **Workload:** {selected_doc['workload_today']}/{selected_doc.get('max_daily_slots', 8)} booked today.
- **Next Available Slot:** {selected_doc.get('next_slot') or 'emergency override / no regular slot'}

**4. Explainable Alternatives**
{alt_lines}

**5. Audit**
- {audit_note}
- **Confidence Rating:** **{int(confidence * 100)}%**
"""
        return {
            "doctor_id": selected_doc["id"],
            "doctor_name": f"Dr. {selected_doc['name']}",
            "specialization": selected_doc["specialty"],
            "department": department,
            "confidence": confidence,
            "priority": priority_label,
            "slot": selected_doc.get("next_slot"),
            "explanation": explanation,
            "recommended_doctors": [
                {
                    "doctor_name": f"Dr. {d['name']}",
                    "specialty": d["specialty"],
                    "score": d["score"],
                    "workload": f"{d['workload_today']}/{d.get('max_daily_slots', 8)}",
                    "next_slot": d.get("next_slot"),
                    "reasons": d["reasons"],
                    "selected": d["id"] == selected_doc["id"],
                } for d in scored_doctors[:5]
            ],
            "agent_trace": [
                "Observed patient symptoms, selected body area, priority, doctor capacity, and availability windows.",
                f"Inferred target department: {department}.",
                "Scored every currently available doctor using specialty fit, workload balance, slot availability, and remaining daily capacity.",
                "Selected the highest-ranked safe candidate and exposed the next-best alternatives for explainability.",
            ],
        }


def ai_allocate_doctor(patient_details, available_doctors, prompt):
    agent = TriageAgent(gemini_model=gemini_model)
    triage_result = agent.run_triage(patient_details, available_doctors)
    if not triage_result:
        return None

    slot_time = datetime.fromisoformat(triage_result["slot"]) if triage_result.get("slot") else None
    if not slot_time:
        return None

    triage_result["slot"] = slot_time.isoformat()
    return triage_result

def check_custom_slot(doctor_id: int, slot_time: datetime) -> bool:
    date = slot_time.date()
    windows = DoctorAvailability.query.filter_by(doctor_id=doctor_id, date=date).all()
    if not windows:
        start = datetime.combine(date, (datetime.min + timedelta(hours=9)).time())
        end = datetime.combine(date, (datetime.min + timedelta(hours=17)).time())
        return start <= slot_time <= end
    for w in windows:
        start_dt = datetime.combine(w.date, w.start_time)
        end_dt = datetime.combine(w.date, w.end_time)
        if start_dt <= slot_time <= end_dt:
            return True
    return False

# -------------------- ROUTES (AUTH) --------------------

@app.route("/register/patient", methods=["POST"])
def register_patient():
    data = request.json
    email = sanitize(data.get("email"))
    password = sanitize(data.get("password"))
    
    if User.query.filter_by(email=email).first():
        return jsonify({"message": "Email already registered"}), 400
        
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    user = User(email=email, password_hash=hashed, role="patient")
    db.session.add(user)
    db.session.commit()
    
    code = f"PAT-{int(datetime.now().timestamp())}"
    patient = Patient(
        user_id=user.id,
        patient_code=code,
        name=sanitize(data.get("name")),
        age=data.get("age"),
        gender=sanitize(data.get("gender")),
        mobile=sanitize(data.get("mobile"))
    )
    db.session.add(patient)
    db.session.commit()
    return jsonify({"message": "Patient registered successfully."}), 201

@app.route("/register/doctor", methods=["POST"])
def register_doctor():
    data = request.json
    email = sanitize(data.get("email"))
    password = sanitize(data.get("password"))
    
    if User.query.filter_by(email=email).first():
        return jsonify({"message": "Email already registered"}), 400
        
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    user = User(email=email, password_hash=hashed, role="doctor")
    db.session.add(user)
    db.session.commit()
    
    doctor = Doctor(
        user_id=user.id,
        name=sanitize(data.get("name")),
        specialty=sanitize(data.get("specialty")),
        department=sanitize(data.get("department")),
        license_number=sanitize(data.get("license_number")),
        mobile=sanitize(data.get("mobile")),
        max_daily_slots=data.get("max_daily_slots", 8)
    )
    db.session.add(doctor)
    db.session.commit()
    return jsonify({"message": "Doctor registered successfully."}), 201


@app.route("/register/nurse", methods=["POST"])
def register_nurse():
    data = request.json
    email = sanitize(data.get("email"))
    password = sanitize(data.get("password"))
    if User.query.filter_by(email=email).first():
        return jsonify({"message": "Email already registered"}), 400
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    user = User(email=email, password_hash=hashed, role="nurse")
    db.session.add(user)
    db.session.commit()
    # reuse Doctor table for basic contact info storage
    doctor = Doctor(
        user_id=user.id,
        name=sanitize(data.get("name")),
        mobile=sanitize(data.get("mobile")),
        specialty=sanitize(data.get("department", "Nursing")),
        department=sanitize(data.get("department", "Nursing")),
        license_number=sanitize(data.get("license_number", "")),
    )
    db.session.add(doctor)
    db.session.commit()
    return jsonify({"message": "Nurse registered successfully."}), 201


@app.route("/register/admin", methods=["POST"])
def register_admin():
    data = request.json
    email = sanitize(data.get("email"))
    password = sanitize(data.get("password"))
    if User.query.filter_by(email=email).first():
        return jsonify({"message": "Email already registered"}), 400
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    user = User(email=email, password_hash=hashed, role="admin")
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "Admin registered successfully."}), 201

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    email = sanitize(data.get("email"))
    password = sanitize(data.get("password"))
    user = User.query.filter_by(email=email).first()
    if not user or not bcrypt.checkpw(password.encode('utf-8'), user.password_hash):
        return jsonify({"message": "Invalid credentials"}), 401
    
    import json
    token = create_access_token(identity=json.dumps({"id": user.id, "role": user.role}))
    
    # Retrieve profile details to send back
    profile_id = None
    name = email
    if user.role == "patient":
        p = Patient.query.filter_by(user_id=user.id).first()
        if p:
            profile_id = p.id
            name = p.name
    else:
        d = Doctor.query.filter_by(user_id=user.id).first()
        if d:
            profile_id = d.id
            name = d.name

    return jsonify({"token": token, "role": user.role, "profile_id": profile_id, "name": name}), 200

# -------------------- ROUTES (CORE) --------------------

@app.route("/upload_report", methods=["POST"])
def upload_report():
    patient_id = request.form.get("patient_id")
    if not patient_id:
        return jsonify({"error": "patient_id required"}), 400
        
    patient = Patient.query.get(patient_id)
    if not patient:
         return jsonify({"error": "Invalid patient"}), 404
         
    file = request.files.get("report_file")
    if not file:
        return jsonify({"error": "No file part"}), 400

    filename = sanitize(file.filename)
    path = os.path.join(app.config["REPORT_DIR"], f"{patient.patient_code}_{filename}")
    file.save(path)

    text = extract_text(path)
    summary = AI_summarize(text)
    patient.report_path = path
    patient.report_summary = summary
    db.session.commit()

    return jsonify({"message": "Report uploaded", "summary": summary, "extracted_text_snippet": text[:100]})

@app.route("/allocate", methods=["POST"])
@jwt_required()
def allocate():
    current_user = json.loads(get_jwt_identity())
    if current_user["role"] != "patient":
        return jsonify({"message": "Action restricted strictly to Patients"}), 403

    data = request.json
    patient_id = data.get("patient_id")
    body_part = sanitize(data.get("body_part"))
    symptom = sanitize(data.get("symptom"))
    priority = sanitize(data.get("priority", "normal"))
    preferred_doctor_id = data.get("preferred_doctor_id")
    desired_slot = data.get("slot_time")

    patient = Patient.query.get(patient_id)
    
    # Validation against XSS on large fields
    patient.symptom = bleach.clean(symptom)
    patient.body_part = bleach.clean(body_part)
    # Load all available doctors matching conditions
    docs = Doctor.query.filter_by(is_available=True, on_leave=False).all()
    available_docs = []
    today = datetime.now().date()
    # if no availability rows exist for today, create default 9-17 windows
    if DoctorAvailability.query.filter_by(date=today).count() == 0:
        default_start = datetime.combine(today, (datetime.min + timedelta(hours=9)).time()).time()
        default_end = datetime.combine(today, (datetime.min + timedelta(hours=17)).time()).time()
        for d in docs:
            db.session.add(DoctorAvailability(
                doctor_id=d.id,
                date=today,
                start_time=default_start,
                end_time=default_end,
                slot_minutes=30
            ))
        db.session.commit()
    
    for d in docs:
        if d.workload_today() < d.max_daily_slots or priority == "emergency":
            available_docs.append({
                "id": d.id, "name": d.name, "specialty": d.specialty,
                "workload_today": d.workload_today(),
                "max_daily_slots": d.max_daily_slots
            })

    # Execute system prompt / AI analysis
    ai_result = ai_allocate_doctor(
        patient_details={"body_part": body_part, "symptom": symptom, "priority": priority},
        available_doctors=available_docs,
        prompt="You are an intelligent hospital triage... Return result in JSON format"
    )
    
    if not ai_result:
        db.session.rollback()
        return jsonify({"message": "No Doctor Available for required specialization/time"}), 404

    # If priority doctor was provided, override AI 
    selected_doc_id = ai_result["doctor_id"]
    if preferred_doctor_id:
        pref = Doctor.query.get(preferred_doctor_id)
        if pref and (pref.workload_today() < pref.max_daily_slots or priority == "emergency"):
            selected_doc_id = pref.id
            ai_result["doctor_name"] = f"Dr. {pref.name}"
            ai_result["specialization"] = pref.specialty
            preferred_slot = find_next_available_slot(pref.id, priority)
            if preferred_slot:
                ai_result["slot"] = preferred_slot.isoformat()
            elif not desired_slot:
                db.session.rollback()
                return jsonify({"message": "Preferred doctor has no available slot today"}), 404
            ai_result["explanation"] += f"\n\n**Patient Preference Override:** The agent's ranked recommendation was reviewed, but the patient manually requested **Dr. {pref.name}**. The system still verified this doctor's capacity and slot availability before booking."

    doctor = Doctor.query.get(selected_doc_id)
    slot_time = datetime.fromisoformat(ai_result["slot"])
    
    # Handle manual custom slot selection
    if desired_slot:
        custom_dt = datetime.fromisoformat(desired_slot)
        if Appointment.query.filter_by(doctor_id=doctor.id, slot_time=custom_dt, status="scheduled").first():
            db.session.rollback()
            return jsonify({"message": "Requested slot already booked"}), 409
        if not check_custom_slot(doctor.id, custom_dt):
            db.session.rollback()
            return jsonify({"message": "Requested slot outside doctor's availability"}), 400
        slot_time = custom_dt

    patient.department = ai_result["department"]
    
    appointment = Appointment(
        patient_id=patient.id,
        doctor_id=doctor.id,
        slot_time=slot_time,
        status="scheduled"
    )
    db.session.add(appointment)
    db.session.commit()

    room_no = (doctor.id % 10) + 200

    # Ensure response exact keys requested
    return jsonify({
        "doctor_name": ai_result["doctor_name"],
        "specialization": ai_result["specialization"],
        "department": ai_result["department"], # passed back to UI
        "slot": slot_time.strftime("%I:%M %p, %b %d"),
        "priority": ai_result["priority"],
        "confidence": ai_result["confidence"],
        "room": f"Room {room_no}",
        "report_summary": patient.report_summary,
        "explanation": ai_result.get("explanation", "No explanation available."),
        "recommended_doctors": ai_result.get("recommended_doctors", []),
        "agent_trace": ai_result.get("agent_trace", [])
    })


@app.route("/cancel_appointment", methods=["POST"])
@jwt_required()
def cancel_appointment():
    data = request.json
    appt_id = data.get("appointment_id")
    reason = sanitize(data.get("reason"))
    current_user = json.loads(get_jwt_identity())
    
    appointment = Appointment.query.get(appt_id)
    if not appointment:
        return jsonify({"message": "Not found"}), 404
        
    fine = 0
    delta = appointment.slot_time - datetime.now()
    if delta.days < 7:
        fine = 500

    appointment.status = "cancelled"
    appointment.cancel_reason = reason
    appointment.cancelled_by = current_user["role"]
    appointment.fine_applied = fine
    db.session.commit()
    
    return jsonify({
        "message": "Appointment cancelled", 
        "fine_applied": fine, 
        "warning": "Less than 7 days notice. Fine applied." if fine else "Free cancellation"
    })

@app.route("/recommend_test", methods=["POST"])
@jwt_required()
def recommend_test():
    current_user = json.loads(get_jwt_identity())
    if current_user["role"] != "doctor":
        return jsonify({"message": "Only doctors can recommend tests"}), 403

    data = request.json
    appt_id = data.get("appointment_id")
    tests = sanitize(data.get("tests"))

    appt = Appointment.query.get(appt_id)
    if appt:
        appt.recommended_tests = tests
        db.session.commit()
        return jsonify({"message": "Test recorded"})
    return jsonify({"message": "Appointment not found"}), 404


# -------------------- ROUTES (VIEWS / MISC) --------------------

@app.route("/doctors", methods=["GET"])
def list_doctors():
    doctors = Doctor.query.all()
    payload = []
    for d in doctors:
        payload.append({
            "id": d.id,
            "name": d.name,
            "specialty": d.specialty,
            "workload_today": d.workload_today(),
            "max_daily_slots": d.max_daily_slots,
            "is_available": d.is_available,
        })
    return jsonify(payload)

@app.route("/doctor_availability", methods=["POST"])
@jwt_required()
def doctor_availability():
    current_user = json.loads(get_jwt_identity())
    if current_user["role"] != "doctor":
        return jsonify({"message": "Unauthorized"}), 403
        
    data = request.json
    # fallback to current doctor id if not passed
    doctor_id = data.get("doctor_id")
    if not doctor_id:
        # map current user -> doctor profile
        doc_profile = Doctor.query.filter_by(user_id=current_user["id"]).first()
        doctor_id = doc_profile.id if doc_profile else None
    if not doctor_id:
        return jsonify({"message": "Doctor profile not found"}), 404
    try:
        the_date = datetime.fromisoformat(data["date"]).date()
        # use time.fromisoformat because payload is a time string, not full datetime
        start_t = time.fromisoformat(data["start_time"])
        end_t = time.fromisoformat(data["end_time"])
        slot_minutes = int(data.get("slot_minutes", 30))
    except Exception as e:
        return jsonify({"message": f"Bad payload: {e}"}), 400

    # clear existing for same day to avoid overlaps
    DoctorAvailability.query.filter_by(doctor_id=doctor_id, date=the_date).delete()

    entry = DoctorAvailability(
        doctor_id=doctor_id,
        date=the_date,
        start_time=start_t,
        end_time=end_t,
        slot_minutes=slot_minutes
    )
    db.session.add(entry)
    db.session.commit()
    return jsonify({"message": "Availability saved"})

@app.route("/doctor_slots", methods=["GET"])
def doctor_slots():
    doctor_id = request.args.get("doctor_id", type=int)
    date_str = request.args.get("date")
    if not doctor_id:
        return jsonify({"message": "doctor_id required"}), 400
    try:
        the_date = datetime.fromisoformat(date_str).date() if date_str else datetime.now().date()
    except Exception:
        the_date = datetime.now().date()

    # if no window rows exist for that day, assume default 9-17
    windows = DoctorAvailability.query.filter_by(doctor_id=doctor_id, date=the_date).all()
    if not windows:
        windows = [type("W", (), {
            "date": the_date,
            "start_time": (datetime.min + timedelta(hours=9)).time(),
            "end_time": (datetime.min + timedelta(hours=17)).time(),
            "slot_minutes": 30
        })]

    # collect booked slots
    booked = set(
        a.slot_time
        for a in Appointment.query.filter_by(doctor_id=doctor_id, status="scheduled").all()
        if a.slot_time.date() == the_date
    )

    slots = []
    for w in windows:
        start_dt = datetime.combine(w.date, w.start_time)
        end_dt = datetime.combine(w.date, w.end_time)
        step = timedelta(minutes=w.slot_minutes)
        current = start_dt
        while current < end_dt:
            if current not in booked:
                slots.append(current.isoformat())
            current += step

    return jsonify({"slots": slots})

@app.route("/patient_appointments", methods=["GET"])
@jwt_required()
def patient_appointments():
    current_user = json.loads(get_jwt_identity())
    if current_user["role"] != "patient":
        return jsonify([]), 403
    patient = Patient.query.filter_by(user_id=current_user["id"]).first()
    if not patient: return jsonify([])
    
    appts = Appointment.query.filter_by(patient_id=patient.id).order_by(Appointment.slot_time.desc()).all()
    result = []
    for a in appts:
        d = Doctor.query.get(a.doctor_id)
        result.append({
            "id": a.id,
            "doctor_name": d.name,
            "specialty": d.specialty,
            "slot": a.slot_time.isoformat(),
            "status": a.status,
            "fine": a.fine_applied,
            "tests": a.recommended_tests or "None"
        })
    return jsonify(result)

@app.route("/doctor_patients", methods=["GET"])
@jwt_required()
def doctor_patients():
    doctor_id = request.args.get("doctor_id", type=int)
    today = datetime.now().date()
    items = Appointment.query.filter(
        Appointment.doctor_id == doctor_id,
        Appointment.slot_time >= datetime.combine(today, datetime.min.time()),
        Appointment.status == "scheduled",
    ).all()
    result = []
    for a in items:
        patient = Patient.query.get(a.patient_id)
        result.append({
            "id": a.id, # appointment id
            "patient_code": patient.patient_code if patient else "",
            "name": patient.name if patient else "",
            "priority": patient.priority if patient else "",
            "department": patient.department if patient else "",
            "symptom": patient.symptom if patient else "",
            "report_summary": patient.report_summary if patient else "",
            "slot_time": a.slot_time.isoformat(),
            "status": a.status,
            "tests": a.recommended_tests or ""
        })
    return jsonify(result)

# Hot reload triggered
if __name__ == "__main__":
    app.run(debug=False, port=5000)
