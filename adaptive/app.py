import base64
import os
from datetime import datetime, timedelta

import requests
import streamlit as st
import streamlit.components.v1 as components

# Prebuilt local body picker component (returns selected body part string)
OVERLAY_VERSION = "overlay-20260629-1"
body_picker_component = components.declare_component(
    "body_picker",
    path=os.path.join(os.path.dirname(__file__), "body_component")
)

st.set_page_config(layout="wide", page_title="Smart Hospital System", initial_sidebar_state="expanded")

# --- UI STYLING (Premium Modern) ---
st.markdown("""
<style>
    /* Global modern font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Sleek gradient background for main content area */
    .stApp > header {
        background-color: transparent;
    }
    
    /* Modern card containers */
    div[data-testid="stForm"] {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
    }
    
    /* Gradient headers */
    h1 {
        background: -webkit-linear-gradient(45deg, #4ade80, #3b82f6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700 !important;
    }
    
    /* Buttons */
    div.stButton > button {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        border: none;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        color: white;
        border: none;
    }
    
    /* Expander styling */
    div[data-testid="stExpander"] {
        border-radius: 8px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        background: rgba(255, 255, 255, 0.02);
    }
</style>
""", unsafe_allow_html=True)

API = "http://127.0.0.1:5000"

# --- STATE MGMT ---
if "token" not in st.session_state:
    st.session_state["token"] = None
if "role" not in st.session_state:
    st.session_state["role"] = None
if "profile_id" not in st.session_state:
    st.session_state["profile_id"] = None
if "name" not in st.session_state:
    st.session_state["name"] = None

query_params = st.query_params
if query_params.get("token"):
    st.session_state["token"] = query_params.get("token")[0]
    st.session_state["role"] = query_params.get("role", [st.session_state["role"]])[0]
    st.session_state["profile_id"] = query_params.get("profile_id", [st.session_state["profile_id"]])[0]
    st.session_state["name"] = query_params.get("name", [st.session_state["name"]])[0]


def get_headers():
    if st.session_state["token"]:
        return {"Authorization": f"Bearer {st.session_state['token']}"}
    return {}

def logout():
    st.session_state["token"] = None
    st.session_state["role"] = None
    st.session_state["profile_id"] = None
    st.session_state["name"] = None
    st.rerun()

# --- HELPERS ---

def fetch_doctors():
    try:
        res = requests.get(f"{API}/doctors")
        if res.ok: return res.json()
    except Exception: pass
    return []

def api_error_message(res, fallback="Request failed."):
    try:
        return res.json().get("message") or res.json().get("error") or fallback
    except Exception:
        text = (res.text or "").strip()
        if text.startswith("<!doctype") or text.startswith("<html"):
            return fallback
        return text[:300] or fallback

if not st.session_state["token"]:
    st.title("Authentication Required")
    st.error("This module is only accessible after logging in through the main Smart Hospital Portal.")
    st.write("Open the launcher app on localhost:9000 and use the login form there. This page no longer supports its own login or registration UI.")
    st.stop()


# --- LOGGED IN UI ---
st.sidebar.title(f"Role: {st.session_state['role'].capitalize()}")
st.sidebar.write(f"User: {st.session_state['name']}")
if st.sidebar.button("Logout"):
    logout()

# ----------------- PATIENT PORTAL -----------------
if st.session_state["role"] == "patient":
    st.title("👤 Patient Portal")
    
    doctors = fetch_doctors()
    doctor_options = {f"Dr. {d['name']} ({d['specialty']}) - Load: {d['workload_today']}/{d['max_daily_slots']}": d["id"] for d in doctors}
    
    tab_book, tab_appts = st.tabs(["📅 Book Consultation", "📋 My Appointments"])
    
    with tab_book:
        st.subheader("Step 1: Understand Your Symptom")
        colA, colB = st.columns([1.2, 1])
        with colA:
            st.caption("Tap on the body to highlight the area (auto-fills the field).")

            # Use the packaged Streamlit component (body_component/index.html)
            selected_from_model = body_picker_component(
                default=st.session_state.get("selected_body_part"),
                key=f"body_part_component_{OVERLAY_VERSION}"
            )
            if selected_from_model:
                st.session_state["selected_body_part"] = selected_from_model
                # Also push into selectbox state so the dropdown reflects the click
                st.session_state["body_part_dropdown"] = selected_from_model


        with colB:
            body_options = ["Select area", "Head", "Chest", "Abdomen", "Pelvis", "Arms", "Legs", "Skin"]
            selected_value = st.session_state.get("selected_body_part")
            if selected_value not in body_options:
                st.session_state.pop("selected_body_part", None)

            # Ensure widget state is valid; default to Head
            if "body_part_dropdown" not in st.session_state or st.session_state["body_part_dropdown"] not in body_options:
                st.session_state["body_part_dropdown"] = "Head"
            if st.session_state.get("selected_body_part") in body_options:
                st.session_state["body_part_dropdown"] = st.session_state["selected_body_part"]

            body_part = st.selectbox("Primary Body Area", body_options, key="body_part_dropdown")
            if body_part != "Select area":
                st.session_state["selected_body_part"] = body_part
            common_symptom_map = {
                "Head": ["Headache", "Dizziness", "Vision changes", "Fever", "Other"],
                "Chest": ["Chest pain", "Shortness of breath", "Palpitations", "Cough", "Other"],
                "Abdomen": ["Stomach ache", "Nausea", "Vomiting", "Bloating", "Other"],
                "Pelvis": ["Pelvic pain", "Urinary issues", "Menstrual irregularity", "Other"],
                "Arms": ["Joint pain", "Muscle weakness", "Numbness", "Swelling", "Other"],
                "Legs": ["Knee pain", "Swollen ankles", "Calf cramp", "Numbness", "Other"],
                "Skin": ["Rash", "Itching", "Discoloration", "Lump", "Other"],
            }
            if body_part in common_symptom_map:
                symptoms_for_part = common_symptom_map[body_part]
                selected_symptom = st.selectbox("Common Symptoms", symptoms_for_part)
                if selected_symptom == "Other":
                    symptom_desc = st.text_area("Please describe your symptom", placeholder="e.g. sharp pain...")
                else:
                    symptom_desc = selected_symptom
            else:
                symptom_desc = st.text_area("Symptom Description", placeholder="e.g. sharp chest pain when breathing...")
            duration = st.selectbox("Duration", ["Just started", "1-2 days", "A week", "More than a week"])
            severity = st.slider("Severity (1-10)", 1, 10, 5)
            extra_hints = st.multiselect("Associated hints", ["Fever", "Nausea", "Weakness", "Bleeding", "Swelling", "Rash"])
            priority = st.radio("Priority", ["normal", "emergency"], horizontal=True)
            
            symptom_full = f"{symptom_desc} | Duration: {duration} | Severity: {severity}/10 | Extra: {', '.join(extra_hints)}"
            
        st.divider()
        st.subheader("Step 2: Upload Medical Report & Extract Insights (Optional)")
        report_file = st.file_uploader("Upload prior reports (PDF, DOCX, Image)", type=["pdf", "docx", "png", "jpg", "jpeg"])
        if report_file and st.button("Upload & Summarize"):
            files = {"report_file": (report_file.name, report_file, report_file.type)}
            res = requests.post(f"{API}/upload_report", data={"patient_id": st.session_state["profile_id"]}, files=files)
            if res.ok:
                st.success("Uploaded successfully!")
                data = res.json()
                st.info("🧠 AI Extracted Summary:")
                st.write(data.get("summary", ""))
            else:
                st.error("Upload failed.")

        st.divider()
        st.subheader("Step 3: Book Your Slot")
        col1, col2 = st.columns(2)
        with col1:
            preferred_doc = st.selectbox("Doctor Preference", ["Auto-assign"] + list(doctor_options.keys()))
        with col2:
            use_custom_slot = st.checkbox("Pick Specific Slot manually")
            desired_slot = None
            if use_custom_slot:
                # choose doctor explicitly
                slot_doc = st.selectbox("Pick doctor for this slot", list(doctor_options.keys()))
                slot_date = st.date_input("Preferred Date")
                # fetch slots from backend
                selected_doc_id = doctor_options.get(slot_doc)
                if selected_doc_id:
                    try:
                        resp = requests.get(f"{API}/doctor_slots", params={"doctor_id": selected_doc_id, "date": slot_date.isoformat()})
                        if resp.ok:
                            slots = resp.json().get("slots", [])
                        else:
                            slots = []
                    except Exception:
                        slots = []
                    if not slots:
                        st.warning("No free slots for that doctor/day. Try another date/doctor.")
                    else:
                        readable = [datetime.fromisoformat(s).strftime("%I:%M %p, %b %d") for s in slots]
                        chosen = st.selectbox("Available slots", readable)
                        desired_slot = slots[readable.index(chosen)]
                        preferred_doc = slot_doc  # force selection for booking
                
        if st.button("Allocate Consultation", use_container_width=True, type="primary", disabled=len(doctors)==0):
            if len(doctors)==0:
                st.error("No doctors available. Please ask an admin/doctor to register first.")
                st.stop()
            effective_body_part = st.session_state.get("selected_body_part") or body_part
            if effective_body_part == "Select area":
                st.warning("Please pick a body area from the graphic or dropdown.")
                st.stop()
            payload = {
                "patient_id": st.session_state["profile_id"],
                "body_part": effective_body_part,
                "symptom": symptom_full,
                "priority": priority,
                "preferred_doctor_id": doctor_options.get(preferred_doc) if preferred_doc != "Auto-assign" else None,
                "slot_time": desired_slot
            }
            with st.spinner("AI Triage Model Analyzing..."):
                res = requests.post(f"{API}/allocate", json=payload, headers=get_headers())
            if res.ok:
                data = res.json()
                st.success("✅ **AI Allocation Successful!**")
                c1, c2, c3 = st.columns(3)
                c1.metric(label="Assigned Doctor", value=data["doctor_name"], delta=data.get("specialization", data.get("department", "")), delta_color="off")
                c2.metric(label="Scheduled Slot", value=data["slot"])
                c3.metric(label="AI Confidence", value=f"{int(data.get('confidence', 0.95)*100)}%", delta=data.get("priority", "Normal") + " Priority", delta_color="inverse" if data.get("priority")=="High" else "normal")

                st.info(f"📍 **Location:** {data['room']} | **Department:** {data['department']}")

                if data.get("explanation"):
                    with st.expander("🧠 **Explainable AI Allocation Reasoning**", expanded=True):
                        st.markdown(data["explanation"])
                        if data.get("agent_trace"):
                            st.markdown("**Agent workflow**")
                            for step in data["agent_trace"]:
                                st.write(f"- {step}")

                if data.get("recommended_doctors"):
                    with st.expander("Other recommended / available doctors", expanded=False):
                        rows = []
                        for doc in data["recommended_doctors"]:
                            slot = doc.get("next_slot")
                            try:
                                slot = datetime.fromisoformat(slot).strftime("%I:%M %p, %b %d") if slot else "No slot"
                            except Exception:
                                slot = slot or "No slot"
                            rows.append({
                                "Doctor": doc.get("doctor_name"),
                                "Specialty": doc.get("specialty"),
                                "Score": doc.get("score"),
                                "Workload": doc.get("workload"),
                                "Next slot": slot,
                                "Why": "; ".join(doc.get("reasons", [])),
                                "Selected": "Yes" if doc.get("selected") else "No",
                            })
                        st.dataframe(rows, use_container_width=True, hide_index=True)

                if data.get("report_summary"):
                    st.caption("Your report entry and summarization has been forwarded to the doctor.")
            else:
                st.error(api_error_message(res, "Could not book appointment."))
                st.caption(f"Debug info: status={res.status_code}")

    with tab_appts:
        res = requests.get(f"{API}/patient_appointments", headers=get_headers())
        if res.ok:
            appts = res.json()
            if not appts: st.write("No appointments found.")
            for a in appts:
                with st.expander(f"Booking: {a['doctor_name']} ({a['specialty']}) - {a['slot']}"):
                    st.write(f"**Status:** {a['status']}")
                    st.write(f"**Doctor's Tests:** {a['tests']}")
                    if a['fine'] > 0:
                        st.write(f"**Cancellation Fine Paid:** ₹{a['fine']}")
                    
                    if a['status'] == 'scheduled':
                        # Cancellation Logic Validation Showcase
                        st.warning("⚠️ Appointments cancelled less than 7 days ahead incur a ₹500 fine.")
                        c_reason = st.text_input("Reason for cancellation", key=f"r_{a['id']}")
                        if st.button("Cancel Appointment", key=f"btn_{a['id']}"):
                            c_res = requests.post(f"{API}/cancel_appointment", json={"appointment_id": a['id'], "reason": c_reason}, headers=get_headers())
                            if c_res.ok:
                                c_data = c_res.json()
                                st.success(c_data['message'])
                                if c_data.get('fine_applied', 0) > 0: st.error(f"Fine Applied: ₹{c_data['fine_applied']}")
                                st.rerun()
                            else:
                                st.error("Failed to cancel.")
        else:
            st.error("Could not fetch appointments.")


# ----------------- DOCTOR PORTAL -----------------
elif st.session_state["role"] == "doctor":
    st.title("🩺 Doctor Portal")
    
    doc_id = st.session_state["profile_id"]
    
    tab_dash, tab_slots = st.tabs(["📊 Dashboard & Patients", "⏰ Availability Manager"])
    
    with tab_dash:
        st.subheader("Your Patients Today")
        res = requests.get(f"{API}/doctor_patients", params={"doctor_id": doc_id}, headers=get_headers())
        if res.ok:
            patients = res.json()
            # quick stats
            total = len(patients)
            emergencies = sum(1 for p in patients if p.get("priority") == "emergency")
            completed = sum(1 for p in patients if p.get("status") == "completed")
            c1, c2, c3 = st.columns(3)
            c1.metric("Scheduled today", total)
            c2.metric("Emergency", emergencies, delta_color="inverse")
            c3.metric("Completed", completed)
            if not patients:
                st.write("No regular appointments booked today.")
            for p in patients:
                with st.expander(f"{p['slot_time']} | Patient: {p['name']} ({p['priority'].upper()})"):
                    st.write(f"**Affected Area:** {p['department']} - {p['symptom']}")
                    st.info(f"**AI Report Summary:** {p['report_summary'] or 'No summary available.'}")
                    # allow quick view of report summary only once confirmed booking
                    if p.get("report_summary"):
                        st.success("Report attached for this visit.")
                    
                    # Test recommendation logic
                    st.write("---")
                    t_rec = st.text_input("Recommend Tests", value=p['tests'], key=f"test_{p['id']}", placeholder="e.g. CBC, X-Ray")
                    colX, colY = st.columns(2)
                    with colX:
                        if st.button("Save Test Recommendation", key=f"s_{p['id']}"):
                            s_res = requests.post(f"{API}/recommend_test", json={"appointment_id": p['id'], "tests": t_rec}, headers=get_headers())
                            if s_res.ok: st.success("Saved.")
                            else: st.error("Failed.")
                    with colY:
                        # Cancellation
                        if st.button("Cancel this appointment", key=f"dc_{p['id']}", help="Cancel on your end."):
                            c_res = requests.post(f"{API}/cancel_appointment", json={"appointment_id": p['id'], "reason": "Doctor unavailable"}, headers=get_headers())
                            if c_res.ok:
                                st.success("Cancelled successfully.")
                                st.rerun()

    with tab_slots:
        st.subheader("Set Free Slots")
        col1, col2 = st.columns(2)
        with col1:
            avail_date = st.date_input("Date")
            start_time = st.time_input("Start time", value=datetime.now().replace(hour=9, minute=0).time())
            end_time = st.time_input("End time", value=datetime.now().replace(hour=17, minute=0).time())
            slot_minutes = st.number_input("Duration per slot (min)", min_value=10, max_value=60, value=30, step=5)
            
            if st.button("Publish Slots", type="primary"):
                payload = {
                    "doctor_id": doc_id, "date": avail_date.isoformat(),
                    "start_time": start_time.isoformat(), "end_time": end_time.isoformat(),
                    "slot_minutes": slot_minutes,
                }
                ares = requests.post(f"{API}/doctor_availability", json=payload, headers=get_headers())
                if ares.ok:
                    st.success("Availability updated!")
                else:
                    try:
                        st.error(ares.json().get("message", "Failed to update."))
                    except Exception:
                        st.error("Failed to update.")

