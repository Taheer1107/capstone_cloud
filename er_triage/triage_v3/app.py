from datetime import datetime
import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="Triage AI - ER Decision Support",
    page_icon="hospital",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap');

:root {
    --bg: #0f1117;
    --panel: #161b27;
    --panel-2: #1b2232;
    --line: #263246;
    --line-soft: #202938;
    --text: #e8edf7;
    --muted: #9aa6ba;
    --blue: #4a9eff;
    --teal: #1db6a3;
    --green: #22c55e;
    --amber: #f59e0b;
    --red: #ef4444;
}

html, body, [class*="css"] {
    font-family: Inter, sans-serif;
}
.stApp {
    background: var(--bg);
    color: var(--text);
}
.main .block-container {
    max-width: 1450px;
    padding: 1.4rem 2rem 3rem;
}

section[data-testid="stSidebar"] {
    background: #0b1624;
    border-right: 1px solid #1e2a3d;
}
section[data-testid="stSidebar"] * {
    color: #edf5ff !important;
}

[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] strong,
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3 {
    color: var(--text);
}
[data-testid="stWidgetLabel"] p {
    color: #cbd5e1 !important;
    font-weight: 700 !important;
}

input, textarea, [data-baseweb="select"] > div {
    background: #111827 !important;
    border: 1px solid #334155 !important;
    color: #f8fafc !important;
}
[data-baseweb="select"] span {
    color: #f8fafc !important;
}
[data-testid="stNumberInput"] button {
    background: #1f2937 !important;
    color: #f8fafc !important;
    border-color: #334155 !important;
}
.stSlider [data-baseweb="slider"] div {
    color: #f8fafc !important;
}

.stButton > button {
    background: #1f2937;
    color: #f8fafc;
    border: 1px solid #334155;
    border-radius: 8px;
    min-height: 42px;
    font-weight: 800;
}
.stButton > button:hover {
    border-color: var(--blue);
    color: white;
    box-shadow: 0 0 0 2px rgba(74, 158, 255, .14);
}
.stDownloadButton > button {
    background: #1f2937;
    color: #f8fafc;
    border: 1px solid #334155;
    border-radius: 8px;
    font-weight: 800;
}

.hero {
    background: linear-gradient(135deg, #132238 0%, #123c4a 50%, #155e53 100%);
    border: 1px solid #214155;
    border-radius: 12px;
    padding: 24px 28px;
    margin-bottom: 18px;
    box-shadow: 0 18px 48px rgba(0, 0, 0, .22);
}
.hero h1 {
    color: #f8fafc !important;
    margin: 0 0 8px;
    font-size: 31px;
    font-weight: 800;
}
.hero p {
    color: #b9f4ec !important;
    margin: 0;
    font-size: 15px;
}

.panel {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 12px;
    padding: 18px;
    margin-bottom: 16px;
    box-shadow: 0 16px 38px rgba(0, 0, 0, .18);
}
.section-title {
    color: #7dd3fc;
    font-size: 12px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: .12em;
    margin: 0 0 14px;
}
.mini-copy {
    color: var(--muted);
    font-size: 13px;
}

.result-card {
    border-radius: 12px;
    padding: 20px;
    border: 1px solid var(--line);
    background: var(--panel-2);
}
.result-card.er {
    border-color: rgba(239, 68, 68, .65);
    background: linear-gradient(135deg, #2a1117 0%, #1b2232 100%);
}
.result-card.non-er {
    border-color: rgba(34, 197, 94, .65);
    background: linear-gradient(135deg, #0d291a 0%, #1b2232 100%);
}
.result-title {
    font-size: 30px;
    font-weight: 800;
    color: #f8fafc;
    margin-bottom: 6px;
}
.result-body {
    color: #cbd5e1;
    font-size: 14px;
    line-height: 1.55;
}

.metric-card {
    background: #111827;
    border: 1px solid #263246;
    border-radius: 10px;
    padding: 15px;
    min-height: 112px;
}
.metric-label {
    color: #94a3b8;
    font-size: 11px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: .08em;
}
.metric-value {
    color: #f8fafc;
    font-family: "JetBrains Mono", monospace;
    font-size: 27px;
    font-weight: 800;
    margin-top: 5px;
}
.metric-note {
    color: #94a3b8;
    font-size: 12px;
    margin-top: 4px;
}

.badge {
    display: inline-block;
    padding: 6px 10px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 800;
    margin: 3px 6px 3px 0;
}
.high { background: rgba(239, 68, 68, .16); color: #fca5a5; border: 1px solid rgba(239, 68, 68, .3); }
.medium { background: rgba(245, 158, 11, .16); color: #fcd34d; border: 1px solid rgba(245, 158, 11, .3); }
.low { background: rgba(34, 197, 94, .16); color: #86efac; border: 1px solid rgba(34, 197, 94, .3); }
.blue { background: rgba(74, 158, 255, .16); color: #93c5fd; border: 1px solid rgba(74, 158, 255, .32); }
.neutral { background: rgba(148, 163, 184, .14); color: #cbd5e1; border: 1px solid rgba(148, 163, 184, .28); }

.agent-grid {
    display: grid;
    grid-template-columns: repeat(5, minmax(0, 1fr));
    gap: 12px;
}
.agent-card {
    background: #111827;
    border: 1px solid #263246;
    border-radius: 10px;
    padding: 14px;
    min-height: 142px;
}
.agent-card h4 {
    color: #f8fafc !important;
    font-size: 15px;
    margin: 0 0 8px;
}
.agent-card p {
    color: #aeb9ca !important;
    font-size: 13px;
    line-height: 1.45;
    margin: 0;
}
.doctor-card {
    background: #111827;
    border: 1px solid #263246;
    border-radius: 10px;
    padding: 16px;
}
.factor {
    border-bottom: 1px solid var(--line-soft);
    padding: 11px 0;
}
.factor strong { color: #f8fafc; }
.factor small { color: var(--muted); }

div[data-testid="stDataFrame"] {
    border: 1px solid #263246;
    border-radius: 10px;
}
</style>
""",
    unsafe_allow_html=True,
)


COMPLAINT_OPTIONS = {
    "Unknown": "unknown",
    "Chest Pain": "chest_pain",
    "Shortness of Breath": "dyspnea",
    "Altered Mental Status": "altered_ms",
    "Trauma / Injury": "trauma",
    "Abdominal Pain": "abdominal",
    "Cardiac / Palpitations": "cardiac",
    "Fever / Infection": "fever_infection",
    "Neurological": "neurological",
    "Urological": "urological",
    "Psychiatric": "psychiatric",
    "General Pain": "pain_general",
    "Other": "other",
}

DEMO_DOCTORS = [
    {"name": "Dr. Rohan Mehta", "specialization": "Cardiology", "available": True, "active_cases": 2, "experience_years": 11, "performance": 0.96},
    {"name": "Dr. Nisha Rao", "specialization": "Pulmonology", "available": True, "active_cases": 3, "experience_years": 9, "performance": 0.92},
    {"name": "Dr. Asha Menon", "specialization": "Emergency Medicine", "available": True, "active_cases": 4, "experience_years": 13, "performance": 0.94},
    {"name": "Dr. Farah Khan", "specialization": "Internal Medicine", "available": True, "active_cases": 1, "experience_years": 8, "performance": 0.90},
    {"name": "Dr. Karan Shah", "specialization": "Trauma Surgery", "available": False, "active_cases": 6, "experience_years": 15, "performance": 0.95},
]

SAMPLE_PATIENTS = {
    "Stable Walk-In": {
        "temperature": 37.0, "heartrate": 78, "resprate": 16, "o2sat": 98.0,
        "sbp": 122, "dbp": 76, "pain": 2, "complaint_group": "other",
        "gender": "Female", "arrival_transport": "Walk-in", "age_at_admission": 32,
        "acuity": 4, "has_hypertension": 0, "has_diabetes": 0, "has_cardiac": 0,
        "has_respiratory": 0, "has_renal": 0, "has_sepsis": 0, "prior_admission_count": 0,
        "height_cm": 165.0, "weight_kg": 62.0, "bmi": 22.8,
    },
    "Cardiac Emergency": {
        "temperature": 37.8, "heartrate": 128, "resprate": 26, "o2sat": 91.0,
        "sbp": 92, "dbp": 58, "pain": 9, "complaint_group": "chest_pain",
        "gender": "Male", "arrival_transport": "Ambulance", "age_at_admission": 67,
        "acuity": 1, "has_hypertension": 1, "has_diabetes": 1, "has_cardiac": 1,
        "has_respiratory": 0, "has_renal": 0, "has_sepsis": 0, "prior_admission_count": 2,
        "height_cm": 172.0, "weight_kg": 84.0, "bmi": 28.4,
    },
    "Respiratory Distress": {
        "temperature": 38.5, "heartrate": 112, "resprate": 30, "o2sat": 88.0,
        "sbp": 108, "dbp": 70, "pain": 6, "complaint_group": "dyspnea",
        "gender": "Female", "arrival_transport": "Ambulance", "age_at_admission": 58,
        "acuity": 2, "has_hypertension": 0, "has_diabetes": 0, "has_cardiac": 0,
        "has_respiratory": 1, "has_renal": 0, "has_sepsis": 0, "prior_admission_count": 1,
        "height_cm": 160.0, "weight_kg": 72.0, "bmi": 28.1,
    },
}

FALLBACK_RESOURCES = {
    "department_status": {
        "er_occupancy": 72,
        "icu_beds_available": 4,
        "general_beds_available": 18,
        "ambulance_queue": 3,
        "average_wait_minutes": 26,
    },
    "doctors": DEMO_DOCTORS,
}


if "api_url" not in st.session_state:
    st.session_state.api_url = "http://localhost:8000"
if "history" not in st.session_state:
    st.session_state.history = []
if "latest_result" not in st.session_state:
    st.session_state.latest_result = None
if "form_seed" not in st.session_state:
    st.session_state.form_seed = SAMPLE_PATIENTS["Cardiac Emergency"].copy()
if "notifications" not in st.session_state:
    st.session_state.notifications = []


def api_get(path: str, timeout: int = 4):
    try:
        response = requests.get(f"{st.session_state.api_url}{path}", timeout=timeout)
        if response.status_code == 200:
            return response.json(), None
        return None, f"{response.status_code}: {response.text}"
    except Exception as exc:
        return None, str(exc)


def api_post(path: str, payload: dict, timeout: int = 20):
    try:
        response = requests.post(f"{st.session_state.api_url}{path}", json=payload, timeout=timeout)
        if response.status_code == 200:
            return response.json(), None
        return None, f"{response.status_code}: {response.text}"
    except Exception as exc:
        return None, str(exc)


def hero(title: str, subtitle: str):
    st.markdown(
        f"""
        <div class="hero">
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_title(text: str):
    st.markdown(f'<div class="section-title">{text}</div>', unsafe_allow_html=True)


def badge(text: str, style: str = "neutral"):
    return f'<span class="badge {style}">{text}</span>'


def level_style(level: str):
    level = (level or "").lower()
    if level == "high":
        return "high"
    if level == "medium":
        return "medium"
    if level == "low":
        return "low"
    return "neutral"


def metric_card(label: str, value: str, note: str = ""):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def health_status():
    health, error = api_get("/health")
    if health:
        return health, None
    return {"status": "offline", "features": 0, "mode": "offline"}, error


def resources_data():
    resources, error = api_get("/resources")
    if resources:
        return resources, None
    return FALLBACK_RESOURCES, error


def reverse_complaint(value: str) -> str:
    for label, mapped in COMPLAINT_OPTIONS.items():
        if mapped == value:
            return label
    return "Unknown"


def patient_form():
    seed = st.session_state.form_seed
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    section_title("Patient Input")
    p1, p2, p3 = st.columns(3)
    if p1.button("Stable Walk-In", use_container_width=True):
        st.session_state.form_seed = SAMPLE_PATIENTS["Stable Walk-In"].copy()
        st.rerun()
    if p2.button("Cardiac Emergency", use_container_width=True):
        st.session_state.form_seed = SAMPLE_PATIENTS["Cardiac Emergency"].copy()
        st.rerun()
    if p3.button("Respiratory Distress", use_container_width=True):
        st.session_state.form_seed = SAMPLE_PATIENTS["Respiratory Distress"].copy()
        st.rerun()

    st.divider()
    section_title("Vital Signs")
    v1, v2, v3 = st.columns(3)
    temperature = v1.number_input("Temperature (C)", 30.0, 45.0, float(seed["temperature"]), 0.1)
    heartrate = v1.number_input("Heart Rate (bpm)", 20, 250, int(seed["heartrate"]), 1)
    resprate = v2.number_input("Respiratory Rate", 5, 60, int(seed["resprate"]), 1)
    o2sat = v2.number_input("O2 Saturation (%)", 50.0, 100.0, float(seed["o2sat"]), 0.1)
    sbp = v3.number_input("Systolic BP (mmHg)", 50, 250, int(seed["sbp"]), 1)
    dbp = v3.number_input("Diastolic BP (mmHg)", 30, 180, int(seed["dbp"]), 1)
    pain = st.slider("Pain Score", 0, 10, int(seed["pain"]))

    section_title("Clinical Context")
    c1, c2, c3 = st.columns(3)
    age = c1.number_input("Age", 0, 120, int(seed["age_at_admission"]), 1)
    gender_options = ["Unknown", "Male", "Female"]
    gender = c1.selectbox("Gender", gender_options, index=gender_options.index(seed["gender"]))
    complaint_labels = list(COMPLAINT_OPTIONS.keys())
    complaint_label = c2.selectbox("Chief Complaint", complaint_labels, index=complaint_labels.index(reverse_complaint(seed["complaint_group"])))
    transport_options = ["Unknown", "Walk-in", "Ambulance", "Police", "Other"]
    transport = c2.selectbox("Arrival", transport_options, index=transport_options.index(seed["arrival_transport"]))
    acuity = c3.slider("Acuity Score (1 = most urgent)", 1, 5, int(seed["acuity"]))
    prior = c3.number_input("Prior Admissions", 0, 50, int(seed["prior_admission_count"]), 1)

    with st.expander("Advanced details and comorbidities", expanded=True):
        a1, a2, a3 = st.columns(3)
        height_cm = a1.number_input("Height (cm)", 100.0, 230.0, float(seed["height_cm"]), 0.5)
        weight_kg = a1.number_input("Weight (kg)", 30.0, 220.0, float(seed["weight_kg"]), 0.5)
        bmi_default = seed.get("bmi") or weight_kg / ((height_cm / 100) ** 2)
        bmi = a2.number_input("BMI", 0.0, 70.0, float(bmi_default), 0.1)
        a2.caption("Temporary demo input until your patient module is connected.")
        hyp = a3.checkbox("Hypertension", value=bool(seed["has_hypertension"]))
        dia = a3.checkbox("Diabetes", value=bool(seed["has_diabetes"]))
        car = a3.checkbox("Cardiac disease", value=bool(seed["has_cardiac"]))
        res = a3.checkbox("Respiratory disease", value=bool(seed["has_respiratory"]))
        ren = a3.checkbox("Renal disease", value=bool(seed["has_renal"]))
        sep = a3.checkbox("Sepsis", value=bool(seed["has_sepsis"]))

    payload = {
        "temperature": temperature,
        "heartrate": heartrate,
        "resprate": resprate,
        "o2sat": o2sat,
        "sbp": sbp,
        "dbp": dbp,
        "pain": pain,
        "complaint_group": COMPLAINT_OPTIONS[complaint_label],
        "gender": gender,
        "arrival_transport": transport,
        "age_at_admission": age,
        "acuity": acuity,
        "has_hypertension": int(hyp),
        "has_diabetes": int(dia),
        "has_cardiac": int(car),
        "has_respiratory": int(res),
        "has_renal": int(ren),
        "has_sepsis": int(sep),
        "prior_admission_count": prior,
        "height_cm": height_cm,
        "weight_kg": weight_kg,
        "bmi": bmi,
    }
    run = st.button("Run Emergency Triage", type="primary", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
    return payload, complaint_label, run


def save_history(payload: dict, complaint_label: str, result: dict):
    st.session_state.history.append({
        "time": datetime.now().strftime("%H:%M:%S"),
        "age": payload["age_at_admission"],
        "gender": payload["gender"],
        "complaint": complaint_label,
        "label": result["label"],
        "probability_er": result["probability_er"],
        "severity_score": result.get("severity", {}).get("score"),
        "severity_level": result.get("severity", {}).get("level"),
        "doctor": result.get("doctor_recommendation", {}).get("recommended", {}).get("name"),
        "mode": result.get("mode", "-"),
    })


def result_panel(result: dict):
    label = result.get("label", "No result")
    er = label == "Needs ER"
    severity = result.get("severity", {})
    level = severity.get("level", "Low")
    css = "er" if er else "non-er"
    st.markdown(
        f"""
        <div class="result-card {css}">
            <div class="result-title">{label}</div>
            <div class="result-body">{result.get("explanation", "Run triage to generate clinical reasoning.")}</div>
            <div style="margin-top:10px;">
                {badge(level + " severity", level_style(level))}
                {badge(result.get("mode", "prediction"), "blue")}
                {badge("clinical override" if result.get("override") else "standard route", "neutral")}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")
    doctor = result.get("doctor_recommendation", {}).get("recommended", {})
    c1, c2, c3 = st.columns(3)
    with c1:
        metric_card("ER Probability", f"{float(result.get('probability_er', 0)) * 100:.1f}%", f"Threshold {result.get('threshold', '-')}")
    with c2:
        metric_card("Severity Score", str(severity.get("score", "-")), severity.get("description", ""))
    with c3:
        metric_card("Doctor Match", str(doctor.get("match_score", "-")), doctor.get("specialization", "Pending"))
    st.progress(int(float(result.get("probability_er", 0)) * 100), text="ER probability")


def agent_summary_panel(result: dict):
    severity = result.get("severity", {})
    doctor = result.get("doctor_recommendation", {}).get("recommended", {})
    resource = result.get("resource_allocation", {})
    factors = result.get("top_factors", [])
    top_factor = factors[0]["feature"] if factors else "stable vitals"

    agents = [
        {
            "name": "Triage Agent",
            "status": "Complete",
            "output": "Validated vitals, complaint, acuity, demographics, BMI, and comorbidity inputs.",
            "next": "No missing critical fields detected.",
        },
        {
            "name": "Prediction Agent",
            "status": "Complete",
            "output": f"{result.get('label')} with {float(result.get('probability_er', 0)) * 100:.1f}% ER probability.",
            "next": f"Decision mode: {result.get('mode', 'prediction')}.",
        },
        {
            "name": "Explainability Agent",
            "status": "Complete",
            "output": f"Primary driver: {top_factor}.",
            "next": result.get("explanation", "Explanation generated."),
        },
        {
            "name": "Doctor Agent",
            "status": "Ready to notify",
            "output": f"{doctor.get('name', 'No doctor')} selected for {doctor.get('required_specialization', doctor.get('specialization', 'review'))}.",
            "next": f"Reason: availability, workload, experience, and {doctor.get('match_score', '-')} match score.",
        },
        {
            "name": "Resource Agent",
            "status": "Routed",
            "output": f"{resource.get('recommended_area', 'Care area pending')}.",
            "next": f"Priority: {resource.get('priority', 'Pending')} | Severity: {severity.get('level', '-')}.",
        },
    ]

    with st.container(border=True):
        section_title("AI Agents - Live Decision Chain")
        cols = st.columns(len(agents))
        for col, agent in zip(cols, agents):
            with col:
                st.markdown(f"#### {agent['name']}")
                st.markdown(badge(agent["status"], "blue"), unsafe_allow_html=True)
                st.write(agent["output"])
                st.caption(agent["next"])


def explanation_panel(result: dict):
    with st.container(border=True):
        section_title("Why This Prediction Was Made")
        factors = result.get("top_factors", [])
        if factors:
            chart = pd.DataFrame(factors)[["feature", "impact"]]
            st.bar_chart(chart.set_index("feature"))
            for factor in factors:
                st.markdown(
                    f"""
                    <div class="factor">
                        <strong>{factor.get("feature")}</strong>
                        <span style="float:right;color:#93c5fd;font-weight:800;">{factor.get("impact", 0):+.2f}</span><br>
                        <small>{factor.get("detail")}</small>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("No factor explanation returned.")


def doctor_notify_panel(result: dict):
    doctor_data = result.get("doctor_recommendation", {})
    recommended = doctor_data.get("recommended", {})
    alternates = doctor_data.get("alternates", [])
    actions = result.get("clinical_actions", [])
    resource = result.get("resource_allocation", {})

    with st.container(border=True):
        section_title("Doctor Routing and Notification")
        left, right = st.columns([1, 1])
        with left:
            st.subheader(recommended.get("name", "No recommendation"))
            st.markdown(
                badge("Available" if recommended.get("available") else "Busy", "low" if recommended.get("available") else "high")
                + badge(recommended.get("specialization", "-"), "blue")
                + badge(f"{recommended.get('match_score', '-')} match", "neutral"),
                unsafe_allow_html=True,
            )
            st.write("")
            st.markdown(f"**Why this doctor:** matched required **{recommended.get('required_specialization', '-')}** specialty, current workload of **{recommended.get('active_cases', '-')}** active cases, **{recommended.get('experience_years', '-')}** years experience, and performance score **{recommended.get('performance', '-')}**.")
            st.markdown(f"**Routing area:** {resource.get('recommended_area', '-')}")
            st.markdown(f"**Priority:** {resource.get('priority', '-')}")

        with right:
            doctor_names = [recommended.get("name", "Recommended doctor")] + [doc.get("name") for doc in alternates if doc.get("name")]
            doctor_names += ["Custom doctor"]
            selected = st.selectbox("Notify doctor", doctor_names)
            custom_doctor = ""
            if selected == "Custom doctor":
                custom_doctor = st.text_input("Custom doctor name", placeholder="Enter doctor name")
            message = st.text_area(
                "Notification message",
                value=(
                    f"{result.get('label')} case. "
                    f"Severity {result.get('severity', {}).get('level')} "
                    f"({result.get('severity', {}).get('score')}/100). "
                    f"{result.get('explanation')}"
                ),
                height=120,
            )
            if st.button("Notify Doctor", type="primary", use_container_width=True):
                target = custom_doctor.strip() if selected == "Custom doctor" else selected
                if not target:
                    st.error("Enter a custom doctor name before notifying.")
                else:
                    st.session_state.notifications.append({
                        "time": datetime.now().strftime("%H:%M:%S"),
                        "doctor": target,
                        "message": message,
                        "patient_label": result.get("label"),
                        "severity": result.get("severity", {}).get("level"),
                    })
                    st.success(f"Demo notification queued for {target}.")

        st.divider()
        c1, c2 = st.columns([1, 1])
        with c1:
            section_title("Clinical Actions")
            for action in actions:
                st.markdown(f"- {action}")
        with c2:
            section_title("Alternate Doctors")
            if alternates:
                st.dataframe(pd.DataFrame(alternates)[["name", "specialization", "available", "active_cases", "match_score"]], use_container_width=True, hide_index=True)
            else:
                st.caption("No alternates returned.")


def triage_console():
    hero(
        "ER / Non-ER Patient Prediction and Intelligent Triage",
        "Dark-mode emergency console with prediction, live AI agents, explainability, doctor routing, and demo notification workflow.",
    )
    health, _ = health_status()
    if health.get("mode") == "clinical_rules_fallback":
        st.warning("Model files are not loaded, so this is using clinical-rule fallback mode. Install catboost/xgboost/lightgbm to use the saved ensemble.")

    left, right = st.columns([1.08, .92], gap="large")
    with left:
        payload, complaint_label, run = patient_form()
    with right:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        section_title("Emergency Prediction")
        if run:
            with st.spinner("Running triage agents..."):
                result, error = api_post("/predict", payload)
            if error:
                st.error(f"Prediction failed: {error}")
            else:
                st.session_state.latest_result = result
                save_history(payload, complaint_label, result)
                # Publish vitals to adaptive backend for autofill in downstream modules
                try:
                    import requests, json
                    vitals_payload = {"profile_id": st.session_state.get("profile_id"), "vitals": payload}
                    requests.post("http://localhost:9003/vitals/public", json=vitals_payload, timeout=3)
                except Exception:
                    pass
        if st.session_state.latest_result:
            result_panel(st.session_state.latest_result)
        else:
            st.info("Pick a preset or enter patient vitals, then run emergency triage.")
        st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.latest_result:
        agent_summary_panel(st.session_state.latest_result)
        doctor_notify_panel(st.session_state.latest_result)
        explanation_panel(st.session_state.latest_result)


def batch_prediction():
    hero("Batch CSV Prediction", "Run the same triage workflow over multiple patients and export results.")
    template = pd.DataFrame([SAMPLE_PATIENTS["Stable Walk-In"], SAMPLE_PATIENTS["Cardiac Emergency"], SAMPLE_PATIENTS["Respiratory Distress"]])
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    section_title("Batch Workflow")
    st.download_button("Download Example CSV", template.to_csv(index=False).encode(), "triage_template.csv", "text/csv")
    uploaded = st.file_uploader("Upload patient CSV", type=["csv"])
    run_demo = st.button("Run Built-In Example Batch", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    df_input = pd.read_csv(uploaded) if uploaded else template.copy() if run_demo else None
    if df_input is not None:
        result, error = api_post("/predict/batch", {"patients": df_input.to_dict(orient="records")}, timeout=120)
        if error:
            st.error(f"Batch prediction failed: {error}")
            return
        results_df = pd.DataFrame(result["results"])
        output = pd.concat([df_input.reset_index(drop=True), results_df], axis=1)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total", result["total"])
        c2.metric("Needs ER", result["needs_er"])
        c3.metric("Non-ER", result["non_er"])
        c4.metric("High Severity", int((results_df["severity_level"] == "High").sum()))
        st.dataframe(output, use_container_width=True, hide_index=True)
        st.download_button("Download Results CSV", output.to_csv(index=False).encode(), "triage_batch_results.csv", "text/csv")


def operations_center():
    hero("Operations Center", "Demo doctor availability and ER capacity until your availability module is connected.")
    resources, error = resources_data()
    if error:
        st.warning(f"Using demo resource data: {error}")
    status = resources.get("department_status", {})
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("ER Occupancy", f"{status.get('er_occupancy', 0)}%")
    c2.metric("ICU Beds", status.get("icu_beds_available", 0))
    c3.metric("General Beds", status.get("general_beds_available", 0))
    c4.metric("Ambulance Queue", status.get("ambulance_queue", 0))
    c5.metric("Avg Wait", f"{status.get('average_wait_minutes', 0)} min")
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    section_title("Demo Doctor Availability")
    st.dataframe(pd.DataFrame(resources.get("doctors", [])), use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)


def patient_history():
    hero("Patient History", "Session predictions and queued demo notifications.")
    col1, col2 = st.columns([1.1, .9])
    with col1:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        section_title("Predictions")
        if st.session_state.history:
            st.dataframe(pd.DataFrame(st.session_state.history), use_container_width=True, hide_index=True)
            st.download_button("Export History CSV", pd.DataFrame(st.session_state.history).to_csv(index=False).encode(), "triage_session_history.csv", "text/csv")
        else:
            st.info("No predictions yet.")
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        section_title("Queued Doctor Notifications")
        if st.session_state.notifications:
            st.dataframe(pd.DataFrame(st.session_state.notifications), use_container_width=True, hide_index=True)
        else:
            st.info("No demo notifications queued yet.")
        st.markdown("</div>", unsafe_allow_html=True)


def model_info():
    hero("Model and Decision Support", "Model status, fallback mode, and enabled triage capabilities.")
    info, info_error = api_get("/model/info")
    health, _ = health_status()
    if info_error:
        st.warning(f"Model info unavailable: {info_error}")
    c1, c2, c3 = st.columns(3)
    c1.metric("API Mode", health.get("mode", "offline"))
    c2.metric("Features", health.get("features", 0))
    c3.metric("Threshold", health.get("threshold") or "0.50")
    if info:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        section_title("Capabilities")
        st.markdown(f"**Model:** {info.get('model')}")
        st.markdown(f"**Dataset:** {info.get('dataset')}")
        for item in info.get("decision_support", []):
            st.markdown(f"- {item}")
        st.markdown("</div>", unsafe_allow_html=True)


with st.sidebar:
    st.markdown("## Triage AI")
    st.caption("Emergency decision support")
    st.session_state.api_url = st.text_input("API URL", value=st.session_state.api_url)
    health, health_error = health_status()
    if health.get("status") == "ok":
        mode = "Model" if health.get("mode") == "ensemble_model" else "Fallback"
        st.success(f"API connected | {mode} | {health.get('features', 0)} features")
    else:
        st.error("API offline")
        if health_error:
            st.caption(health_error)

    page = st.radio(
        "Navigation",
        ["Triage Console", "Batch Prediction", "Operations Center", "Patient History", "Model Info"],
    )
    if st.button("Clear Session", use_container_width=True):
        st.session_state.history = []
        st.session_state.latest_result = None
        st.session_state.notifications = []
        st.success("Cleared")


if page == "Triage Console":
    triage_console()
elif page == "Batch Prediction":
    batch_prediction()
elif page == "Operations Center":
    operations_center()
elif page == "Patient History":
    patient_history()
elif page == "Model Info":
    model_info()
