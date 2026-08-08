import os
from pathlib import Path
import streamlit as st
import pandas as pd
import numpy as np
import xgboost as xgb
import lightgbm as lgb
import joblib
import time
import warnings
warnings.filterwarnings('ignore')

# Optional: TensorFlow for LSTM model
try:
    import tensorflow as tf
except:
    pass

# =============================================================================
# CONFIG
# =============================================================================
st.set_page_config(
    page_title="ED Triage AI System",
    page_icon="",
    layout="wide"
)

day_map = {
    "Monday":0,"Tuesday":1,"Wednesday":2,"Thursday":3,
    "Friday":4,"Saturday":5,"Sunday":6
}

month_map = {
    "January":1,"February":2,"March":3,"April":4,
    "May":5,"June":6,"July":7,"August":8,
    "September":9,"October":10,"November":11,"December":12
}


# HELPER: BUILD FEATURE ROW FROM PATIENT DICT

def build_feature_row(patient, features):
    """
    Build a feature dict from a patient dict, compatible with MC-MED features.
    Used for both prediction and quantile interval calculation.
    """
    transport_map = {"WALK IN": 3, "AMBULANCE": 0, "HELICOPTER": 1, "OTHER": 2}
    gender_map    = {"M": 1, "F": 0}

    arrival_hour = patient.get("arrival_hour", 14)
    day_of_week  = patient.get("day_of_week",  1)
    is_peak      = 1 if 8 <= arrival_hour <= 20 else 0
    is_weekend   = 1 if day_of_week >= 5 else 0
    hourly_count = 3

    def get_shift(hour):
        if 6 <= hour < 14:    return 0
        elif 14 <= hour < 22: return 1
        else:                 return 2

    all_features = {
        "temperature"              : patient.get("temperature", 98.6),
        "heartrate"                : patient.get("heartrate",   80),
        "resprate"                 : patient.get("resprate",    18),
        "o2sat"                    : patient.get("o2sat",       98),
        "sbp"                      : patient.get("sbp",         120),
        "dbp"                      : patient.get("dbp",         80),
        "pain"                     : patient.get("pain",        5),
        "acuity"                   : patient.get("acuity",      3),
        "gender"                   : gender_map.get(
                                       patient.get("gender","M"), 1),
        "race"                     : 4,
        "arrival_transport"        : transport_map.get(
                                       patient.get("arrival_transport",
                                                   "WALK IN"), 3),
        "chiefcomplaint"           : 200,
        "icd_title"                : 300,
        "arrival_hour"             : arrival_hour,
        "arrival_day"              : day_of_week,
        "arrival_month"            : patient.get("arrival_month", 6),
        "Is_Peak_Hour"             : is_peak,
        "Is_Weekend"               : is_weekend,
        "Hourly_Patient_Count"     : hourly_count,
        "Daily_Patient_Volume"     : 72,
        "Hourly_Critical_Count"    : 1,
        "High_Urgency_Ratio"       : 0.2 if patient.get("acuity",3) <= 2
                                     else 0.1,
        "Rolling_3Hour_Load"       : hourly_count * 3,
        "Occupancy_Pressure_Index" : hourly_count * 0.15,
        "Estimated_ED_Occupancy"   : hourly_count * 4,
        "Load_Category"            : 1,
        "age"                      : patient.get("age", 40),
        "hour_of_day"              : arrival_hour,
        "day_of_week"              : day_of_week,
        "month"                    : patient.get("arrival_month", 6),
        "is_weekend"               : is_weekend,
        "is_peak_hour"             : is_peak,
        "shift"                    : get_shift(arrival_hour),
        "ed_load"                  : hourly_count,
    }

    row = {f: all_features.get(f, 0) for f in features}
    return row


# LOAD MODELS
HERE = Path(__file__).resolve().parent

@st.cache_resource
def load_models():
    # EXISTING XGBOOST MODELS

    mimic_model = xgb.XGBRegressor()
    mimic_model.load_model(HERE / "xgboost_model.json")

    mcmed_model = xgb.XGBRegressor()
    mcmed_model.load_model(HERE / "xgboost_mcmed_model.json")

    # Extract feature columns
    mimic_csv = HERE / "mimic_preprocessed.csv"
    mcmed_csv = HERE / "mcmed_preprocessed.csv"

    if mimic_csv.exists():
        mimic_features = [c for c in pd.read_csv(mimic_csv, nrows=1).columns if c != "wait_time_min"]
    else:
        mimic_features = [
            "temperature", "heartrate", "resprate", "o2sat", "sbp", "dbp", "pain",
            "acuity", "gender", "arrival_transport", "arrival_hour", "arrival_day",
            "arrival_month", "Is_Peak_Hour", "Is_Weekend", "Hourly_Patient_Count",
            "Daily_Patient_Volume", "Hourly_Critical_Count", "High_Urgency_Ratio",
            "Rolling_3Hour_Load", "Occupancy_Pressure_Index", "Estimated_ED_Occupancy",
            "Load_Category", "age", "hour_of_day", "day_of_week", "month", "is_weekend",
            "is_peak_hour", "shift", "ed_load",
        ]

    if mcmed_csv.exists():
        mcmed_features = [c for c in pd.read_csv(mcmed_csv, nrows=1).columns if c != "wait_time"]
    else:
        mcmed_features = mimic_features

    
    acuity_models = {}
    for acuity in [3, 4, 5]:
        model = xgb.XGBRegressor()
        filename = f"xgb_acuity_{acuity}.json"
        try:
            model.load_model(filename)
            acuity_models[acuity] = model
        except:
            acuity_models[acuity] = None

  
    quantile_models = {}
    for alpha in [0.10, 0.50, 0.90]:
        filename = f"lgbm_q{int(alpha*100)}.pkl"
        try:
            quantile_models[alpha] = joblib.load(filename)
        except:
            quantile_models[alpha] = None

     
    lstm_model = None
    scaler_X   = None
    scaler_y   = None
    try:
        lstm_model = tf.keras.models.load_model("lstm_model.h5")
        scaler_X   = joblib.load("scaler_X_lstm.pkl")
        scaler_y   = joblib.load("scaler_y_lstm.pkl")
    except:
        pass

     
    model_metadata = {
        "xgb_mimic" : {"r2": 0.2369},
        "xgb_mcmed" : {"r2": 0.7439},
        "lstm"      : {"r2": None}
    }

    return {
        "xgb_mimic"      : mimic_model,
        "xgb_mcmed"      : mcmed_model,
        "acuity_models"  : acuity_models,
        "quantile_models": quantile_models,
        "lstm_model"     : lstm_model,
        "scaler_X"       : scaler_X,
        "scaler_y"       : scaler_y,
        "mimic_features" : mimic_features,
        "mcmed_features" : mcmed_features,
        "model_metadata" : model_metadata,
    }


# Load all models once at startup
models_dict      = load_models()
mimic_model      = models_dict["xgb_mimic"]
mcmed_model      = models_dict["xgb_mcmed"]
acuity_models    = models_dict["acuity_models"]
quantile_models  = models_dict["quantile_models"]
lstm_model       = models_dict["lstm_model"]
scaler_X         = models_dict["scaler_X"]
scaler_y         = models_dict["scaler_y"]
mimic_features   = models_dict["mimic_features"]
mcmed_features   = models_dict["mcmed_features"]
model_metadata   = models_dict["model_metadata"]


 
# AGENTIC TOOLS
 

def tool_classify_urgency(acuity, heartrate, o2sat, sbp, resprate=18, pain=5):
    reasons = []
    score   = 0

    acuity_scores = {1: 10, 2: 7, 3: 4, 4: 2, 5: 0}
    score += acuity_scores.get(acuity, 0)
    reasons.append(f"ESI Acuity Level {acuity}")

    if heartrate > 130 or heartrate < 40:
        score += 5
        reasons.append(f"Critical heart rate: {heartrate} bpm")
    elif heartrate > 100:
        score += 2
        reasons.append(f"Elevated heart rate: {heartrate} bpm")

    if o2sat < 88:
        score += 6
        reasons.append(f"Critically low O2: {o2sat}%")
    elif o2sat < 92:
        score += 3
        reasons.append(f"Low O2 saturation: {o2sat}%")

    if sbp < 80:
        score += 6
        reasons.append(f"Critically low BP: {sbp} mmHg")
    elif sbp < 90:
        score += 3
        reasons.append(f"Low systolic BP: {sbp} mmHg")
    elif sbp > 180:
        score += 2
        reasons.append(f"High BP: {sbp} mmHg")

    if resprate > 30 or resprate < 8:
        score += 4
        reasons.append(f"Abnormal resp rate: {resprate}/min")

    if pain >= 9:
        score += 2
        reasons.append(f"Severe pain: {pain}/10")

    if score >= 10:
        urgency = "CRITICAL"
        action  = "Immediate resuscitation required. Do NOT delay."
        color   = "RED"
        badge   = "🔴"
    elif score >= 6:
        urgency = "EMERGENCY"
        action  = "Seen within 10 minutes. Continuous monitoring required."
        color   = "ORANGE"
        badge   = "🟠"
    elif score >= 3:
        urgency = "URGENT"
        action  = "Seen within 30 minutes. Monitor vitals every 15 min."
        color   = "YELLOW"
        badge   = "🟡"
    else:
        urgency = "ROUTINE"
        action  = "Can wait in queue. Reassess if condition changes."
        color   = "GREEN"
        badge   = "🟢"

    return {
        "urgency" : urgency,
        "color"   : color,
        "badge"   : badge,
        "score"   : score,
        "action"  : action,
        "reasons" : reasons
    }


def tool_predict_wait_time(patient, hospital, model, features):
    row = build_feature_row(patient, features)
    X   = pd.DataFrame([row])

    # Try to detect the model's expected feature names (XGBoost booster or sklearn wrapper).
    expected_features = None
    try:
        booster = model.get_booster()
        if booster is not None and hasattr(booster, "feature_names"):
            expected_features = list(booster.feature_names)
    except Exception:
        expected_features = None

    if expected_features is None and hasattr(model, "feature_names_in_"):
        try:
            expected_features = list(getattr(model, "feature_names_in_"))
        except Exception:
            expected_features = None

    # Fall back to the provided features list
    if not expected_features:
        expected_features = list(features)

    # Normalize and ensure presence; reindex DataFrame to model's expected columns
    expected_features = [str(c).strip() for c in expected_features]
    X = X.reindex(columns=expected_features, fill_value=0)

    wait = float(np.clip(model.predict(X)[0], 0, 480))
    if wait < 5:
        wait = 60.0

    return {
        "hospital"       : hospital,
        "predicted_wait" : round(wait, 1),
        "hours"          : int(wait // 60),
        "minutes"        : int(wait % 60)
    }


def tool_recommend_hospital(current_wait, other_wait, urgency):
    diff = abs(current_wait - other_wait)

    if urgency == "CRITICAL":
        return {
            "recommendation" : "Current Hospital",
            "reason"         : ("CRITICAL patient — go to nearest ED "
                                "immediately. Do not travel."),
            "time_saved"     : 0,
            "override"       : True
        }

    if current_wait <= other_wait:
        return {
            "recommendation" : "Current Hospital",
            "reason"         : (f"Current Hospital has ~{int(diff)} min "
                                f"shorter wait."),
            "time_saved"     : int(diff),
            "override"       : False
        }
    else:
        return {
            "recommendation" : "Other Hospital",
            "reason"         : (f"Other Hospital has ~{int(diff)} min "
                                f"shorter wait."),
            "time_saved"     : int(diff),
            "override"       : False
        }


def tool_validate_prediction(predicted_wait, acuity, recommendation,
                              model_r2=None, used_model="xgb_mcmed"):
    """
    Tool 4: Self-Reflection / Prediction Validation

    Flags:
      1. predicted_wait > 180 min  → unrealistic prediction
      2. acuity <= 2               → unsafe wait-time routing
      3. model R2 < 0.4            → low confidence model
    """
    flags = []
    safe  = True

    # Flag 1: Unrealistic wait time
    if predicted_wait > 180:
        flags.append(
            f"WARNING UNREALISTIC: Predicted wait ({predicted_wait:.0f} min) "
            f"exceeds typical ED maximum (~180 min). "
            f"May indicate model overestimation."
        )
        safe = False

    # Flag 2: Critical/Emergency patient routed by wait time
    if acuity <= 2:
        flags.append(
            f"UNSAFE ROUTING: Critical/Emergency patient (Acuity {acuity}) "
            f"should be prioritized by clinical severity, NOT wait time. "
            f"Override recommendation to current hospital."
        )
        safe = False

    # Flag 3: Low model confidence (R2 < 0.4)
    if model_r2 is not None and model_r2 < 0.4:
        flags.append(
            f"LOW CONFIDENCE: Model R2 = {model_r2:.4f} (threshold: 0.4). "
            f"Predictions may be unreliable. Use clinical judgment."
        )
        safe = False

    if safe:
        recommendation_text = (
            f"SAFE TO PROCEED: Prediction appears valid. "
            f"Recommended: {recommendation}"
        )
        color = "green"
    else:
        recommendation_text = (
            f"CAUTION REQUIRED: Safety flags detected. "
            f"Review flagged concerns before finalising recommendation."
        )
        color = "red"

    return {
        "safe"           : safe,
        "flags"          : flags,
        "recommendation" : recommendation_text,
        "color"          : color,
        "model_used"     : used_model
    }



# HEADER

st.title("AI Wait Time prediction")
st.divider()


# INPUT FORM
st.subheader("👤 Patient Information")

col1, col2 = st.columns(2)

with col1:
    gender = st.selectbox("Gender", ["M", "F"])
    age    = st.number_input("Age", 1, 120, 40)

    acuity = st.selectbox(
        "Triage Level (ESI)",
        [1, 2, 3, 4, 5],
        format_func=lambda x: {
            1: "1 - Critical",
            2: "2 - Emergency",
            3: "3 - Urgent",
            4: "4 - Less Urgent",
            5: "5 - Non-Urgent"
        }[x],
        index=2
    )
    pain = st.slider("Pain Level (0-10)", 0, 10, 5)

with col2:
    arrival_transport = st.selectbox("Arrival Source", [
        "WALK IN", "AMBULANCE", "HELICOPTER", "OTHER"
    ])
    arrival_hour  = st.slider("Arrival Hour (0-23)", 0, 23, 12)
    arrival_month = st.selectbox("Month", list(month_map.keys()))
    day_of_week   = st.selectbox("Day of Week", list(day_map.keys()))

st.divider()
st.subheader("🩺 Vitals")

col3, col4, col5 = st.columns(3)

with col3:
    temperature = st.number_input("Temperature (F)",
                                  95.0, 106.0, 98.6, step=0.1)
    heartrate   = st.number_input("Heart Rate (bpm)", 30, 200, 80)

with col4:
    resprate = st.number_input("Resp Rate", 8, 40, 18)
    o2sat    = st.number_input("O2 Saturation (%)", 70, 100, 98)

with col5:
    sbp = st.number_input("Systolic BP", 60, 220, 120)
    dbp = st.number_input("Diastolic BP", 40, 140, 80)

st.divider()

# =============================================================================
# PREDICT BUTTON
# =============================================================================
if st.button(" Run Agentic Triage AI",
             type="primary", use_container_width=True):

    patient = {
        "age"               : age,
        "gender"            : gender,
        "acuity"            : acuity,
        "heartrate"         : heartrate,
        "o2sat"             : o2sat,
        "sbp"               : sbp,
        "dbp"               : dbp,
        "resprate"          : resprate,
        "temperature"       : temperature,
        "pain"              : pain,
        "arrival_transport" : arrival_transport,
        "arrival_hour"      : arrival_hour,
        "day_of_week"       : day_map[day_of_week],
        "arrival_month"     : month_map[arrival_month]
    }

   # st.divider()
    st.subheader(" Agentic AI — Reasoning Live")

    # ── TOOL 1: URGENCY CLASSIFICATION ────────────────────────
    with st.status("Tool 1 → Classifying Patient Urgency...",
                   expanded=True) as status:
        time.sleep(0.6)
        urgency_result = tool_classify_urgency(
            acuity    = patient["acuity"],
            heartrate = patient["heartrate"],
            o2sat     = patient["o2sat"],
            sbp       = patient["sbp"],
            resprate  = patient["resprate"],
            pain      = patient["pain"]
        )
        st.write(f"Urgency: **{urgency_result['badge']} "
                 f"{urgency_result['urgency']}** "
                 f"(Score: {urgency_result['score']}/20)")
        for r in urgency_result['reasons']:
            st.write(f"   - {r}")
        status.update(
            label="Tool 1 → Urgency Classification Complete",
            state="complete"
        )

    # ── TOOL 2a: CURRENT HOSPITAL (MC-MED) ────────────────────
    with st.status(
        "Tool 2a → Predicting Current Hospital Wait...",
        expanded=True
    ) as status:
        time.sleep(0.6)

        acuity_override = None

        # Select model — acuity-specific only if MC-MED and acuity in [3,4,5]
        selected_model      = mcmed_model
        selected_features   = mcmed_features
        selected_model_name = "xgb_mcmed"
        selected_model_r2   = model_metadata["xgb_mcmed"]["r2"]

        if acuity_override is not None and acuity_override in acuity_models:
            if acuity_models[acuity_override] is not None:
                selected_model      = acuity_models[acuity_override]
                selected_features   = mcmed_features
                selected_model_name = f"xgb_acuity_{acuity_override}"
                # Use global R2 as conservative estimate for acuity models
                selected_model_r2   = model_metadata["xgb_mcmed"]["r2"]
            else:
                st.write(f"   Acuity {acuity_override} model not found — "
                         f"falling back to global model.")

        current_wait = tool_predict_wait_time(
            patient  = patient,
            hospital = "Current Hospital",
            model    = selected_model,
            features = selected_features
        )

        # ── Confidence intervals using quantile models ─────────
        current_wait_q10 = None
        current_wait_q50 = None
        current_wait_q90 = None

        if (quantile_models.get(0.10) is not None and
                quantile_models.get(0.50) is not None and
                quantile_models.get(0.90) is not None):
            # Build feature row correctly from patient dict
            patient_row = build_feature_row(patient, mcmed_features)
            X_patient   = pd.DataFrame([patient_row])
            # Align quantile model inputs to expected mcmed_features
            X_patient = X_patient.reindex(columns=[str(c).strip() for c in mcmed_features], fill_value=0)

            try:
                current_wait_q10 = float(np.clip(
                    quantile_models[0.10].predict(X_patient)[0], 0, 480))
            except Exception:
                current_wait_q10 = None
            try:
                current_wait_q50 = float(np.clip(
                    quantile_models[0.50].predict(X_patient)[0], 0, 480))
            except Exception:
                current_wait_q50 = None
            try:
                current_wait_q90 = float(np.clip(
                    quantile_models[0.90].predict(X_patient)[0], 0, 480))
            except Exception:
                current_wait_q90 = None

        st.write(f"Current Hospital: "
                 f"**{current_wait['hours']}h {current_wait['minutes']}m** "
                 f"(~{int(current_wait['predicted_wait'])} min)")

        if current_wait_q10 is not None:
            q10_h = int(current_wait_q10 // 60)
            q10_m = int(current_wait_q10 % 60)
            q50_h = int(current_wait_q50 // 60)
            q50_m = int(current_wait_q50 % 60)
            q90_h = int(current_wait_q90 // 60)
            q90_m = int(current_wait_q90 % 60)
            st.write(
                f"   Confidence Range: "
                f"Best {q10_h}h{q10_m:02d}m | "
                f"Pred {q50_h}h{q50_m:02d}m | "
                f"Worst {q90_h}h{q90_m:02d}m"
            )

        if acuity_override is not None:
            st.write(f"   Using acuity-specific model "
                     f"(Acuity {acuity_override})")

        status.update(
            label="Tool 2a → Current Hospital Prediction Complete",
            state="complete"
        )

    # ── TOOL 2b: OTHER HOSPITAL (MIMIC) ───────────────────────
    with st.status(
        "Tool 2b → Predicting Other Hospital Wait...",
        expanded=True
    ) as status:
        time.sleep(0.6)
        other_wait = tool_predict_wait_time(
            patient  = patient,
            hospital = "Other Hospital",
            model    = mimic_model,
            features = mimic_features
        )
        st.write(f"Other Hospital: "
                 f"**{other_wait['hours']}h {other_wait['minutes']}m** "
                 f"(~{int(other_wait['predicted_wait'])} min)")
        st.write(f""
                 f"treat as directional estimate only.")
        status.update(
            label="Tool 2b → Other Hospital Prediction Complete",
            state="complete"
        )

    # ── TOOL 3: HOSPITAL RECOMMENDATION ───────────────────────
    with st.status("Tool 3 → Recommending Best Hospital...",
                   expanded=True) as status:
        time.sleep(0.6)
        recommendation = tool_recommend_hospital(
            current_wait = current_wait["predicted_wait"],
            other_wait   = other_wait["predicted_wait"],
            urgency      = urgency_result["urgency"]
        )
        st.write(f"Recommendation: "
                 f"**{recommendation['recommendation']}**")
        st.write(f"   Reason: {recommendation['reason']}")
        status.update(
            label="Tool 3 → Hospital Recommendation Complete",
            state="complete"
        )

    # ── TOOL 4: SELF-REFLECTION VALIDATION (Phase 3) ──────────
    with st.status("Tool 4 → Validating Prediction Safety...",
                   expanded=True) as status:
        time.sleep(0.6)
        validation = tool_validate_prediction(
            predicted_wait = current_wait["predicted_wait"],
            acuity         = patient["acuity"],
            recommendation = recommendation["recommendation"],
            model_r2       = selected_model_r2,
            used_model     = selected_model_name
        )

        if validation["safe"]:
            st.success(f"✅ {validation['recommendation']}")
        else:
            st.warning(f"⚠️ {validation['recommendation']}")

        if validation["flags"]:
            st.markdown("**Safety Flags Detected:**")
            for flag in validation["flags"]:
                if "UNSAFE" in flag:
                    st.error(f"🚨 {flag}")
                elif "LOW CONFIDENCE" in flag:
                    st.warning(f"⚠️ {flag}")
                else:
                    st.warning(f"⚠️ {flag}")

        st.write(f"   Model used: {validation['model_used']} "
                 f"| R2: {selected_model_r2:.4f}")

        status.update(
            label="Tool 4 → Prediction Validation Complete",
            state="complete"
        )

   

    # ==========================================================================
    # FINAL RESULTS
    # ==========================================================================
    st.subheader("📋 Final Triage Report")

    urgency_colors = {
        "CRITICAL"  : "#7f0000",
        "EMERGENCY" : "#7f3300",
        "URGENT"    : "#7f6600",
        "ROUTINE"   : "#1a4d1a"
    }
    bg_color = urgency_colors.get(urgency_result['urgency'], "#1a1f2e")

    st.markdown(
        f"""
        <div style='background-color:{bg_color}; padding:16px;
                    border-radius:12px; margin-bottom:16px;
                    text-align:center;'>
            <h2 style='color:white; margin:0'>
                {urgency_result['badge']} {urgency_result['urgency']}
            </h2>
            <p style='color:#ddd; margin:6px 0 0 0; font-size:1em'>
                {urgency_result['action']}
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    col_a, col_b = st.columns([1, 1])

    # Confidence interval HTML for Current Hospital card
    current_interval_html = ""
    if current_wait_q10 is not None:
        current_interval_html = (
            f"<p style='color:#7cfc00; margin:8px 0 0 0; font-size:1.2em'>"
            f"Best: {int(current_wait_q10)} min &nbsp;|&nbsp; "
            f"Pred: {int(current_wait_q50)} min &nbsp;|&nbsp; "
            f"Worst: {int(current_wait_q90)} min</p>"
        )

    # Tool 4 validation badge for Current Hospital card
    validation_badge = (
        "<p style='color:#00e676; margin:6px 0 0 0; font-size:0.85em'>"
        "✅ Prediction Validated</p>"
        if validation["safe"] else
        "<p style='color:#ffab40; margin:6px 0 0 0; font-size:0.85em'>"
        "⚠️ Safety Flags — See Validation Above</p>"
    )

    with col_a:
        st.markdown(
            f"""
            <div style='background-color:#1a1f2e; padding:24px;
                        border-radius:12px; border:2px solid #70AD47;
                        text-align:center;'>
                <h4 style='color:#70AD47; margin:0'>
                     Current Hospital
                </h4>
                <h1 style='color:white; margin:8px 0; font-size:2.8em'>
                    {current_wait['hours']}h {current_wait['minutes']}m
                </h1>
                <p style='color:#aaa; margin:0'>
                    ~{int(current_wait['predicted_wait'])} min estimated wait
                </p>
                {current_interval_html}
                {validation_badge}
            </div>
            """,
            unsafe_allow_html=True
        )

    with col_b:
        st.markdown(
            f"""
            <div style='background-color:#1a1f2e; padding:24px;
                        border-radius:12px; border:2px solid #4472C4;
                        text-align:center;'>
                <h4 style='color:#4472C4; margin:0'>
                     Other Hospital
                </h4>
                <h1 style='color:white; margin:8px 0; font-size:2.8em'>
                    {other_wait['hours']}h {other_wait['minutes']}m
                </h1>
                <p style='color:#aaa; margin:0'>
                    ~{int(other_wait['predicted_wait'])} min estimated wait
                <p style='color:#888; margin:6px 0 0 0; font-size:0.85em'>
                    &nbsp;
                    &nbsp;
                    &nbsp;
                <p>
                &nbsp;
                &nbsp;
                </p>
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<br>", unsafe_allow_html=True)

    rec_color    = ("#0e3d1f"
                    if recommendation['recommendation'] == "Other Hospital"
                    else "#0e1f3d")
    border_color = ("#4472C4"
                    if recommendation['recommendation'] == "Other Hospital"
                    else "#70AD47")

    st.markdown(
        f"""
        <div style='background-color:{rec_color}; padding:20px;
                    border-radius:12px; border:2px solid {border_color};'>
            <h4 style='color:{border_color}; margin:0 0 10px 0'>
                Agent Recommendation
            </h4>
            <p style='color:white; margin:0 0 6px 0; font-size:1.15em'>
                Go to <b>{recommendation['recommendation']}</b>
            </p>
            <p style='color:#aaa; margin:0; font-size:0.9em'>
                {recommendation['reason']}
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.divider()

    # ==========================================================================
    # CLINICAL INTERPRETATION
    # ==========================================================================
    st.subheader("🩺 Clinical Interpretation")

    if acuity <= 2:
        interp = (f"{urgency_result['badge']} High Priority — "
                  f"Immediate assessment required. "
                  f"Do not delay based on wait time estimates.")
    elif acuity == 3:
        interp = (f"{urgency_result['badge']} Moderate Priority — "
                  f"Monitor vitals closely. "
                  f"Reassess if condition changes.")
    else:
        if recommendation['recommendation'] == "Current Hospital":
            rec_h = current_wait['hours']
            rec_m = current_wait['minutes']
        else:
            rec_h = other_wait['hours']
            rec_m = other_wait['minutes']
        interp = (f"{urgency_result['badge']} Standard Priority — "
                  f"Patient can wait. "
                  f"Recommended hospital wait: {rec_h}h {rec_m}m.")

    st.info(interp)

    st.markdown("**Key Factors Identified by Agent:**")

    peak_label    = ("Peak Hours"
                     if 8 <= arrival_hour <= 20 else "Off-Peak")
    weekend_label = ("Weekend"
                     if day_map[day_of_week] >= 5 else "Weekday")
    pain_label    = ("Severe"    if pain >= 8
                     else "Moderate" if pain >= 4
                     else "Mild")

    st.markdown(f"""
- **Urgency:** {urgency_result['badge']} {urgency_result['urgency']} (Score: {urgency_result['score']}/20)
- **Triage Level:** ESI {acuity}
- **Time of Day:** Hour {arrival_hour} ({peak_label})
- **Day:** {day_of_week} ({weekend_label})
- **Pain Level:** {pain}/10 ({pain_label})
- **Arrival:** {arrival_transport}
- **Model Used:** {selected_model_name} (R2={selected_model_r2:.4f})
- **Prediction Validated:** {"Yes" if validation["safe"] else "No — review flags above"}
""")

    st.divider()
    st.caption(
        "Agentic AI Pipeline (Phase 3): "
        "Tool 1 (Urgency) → "
        "Tool 2a (Current Hospital) → "
        "Tool 2b (Other Hospital) → "
        "Tool 3 (Recommend) → "
        "Tool 4 (Validate) | "
        "Based on historical ED patterns — not live queue data."
    )