import os
import urllib.parse

import requests
import streamlit as st
import streamlit.components.v1 as components

API = os.getenv("AUTH_API_URL", st.secrets.get("AUTH_API_URL", "http://127.0.0.1:5000"))

MODULES = [
    {
        "name": "ER Triage",
        "icon": "🚑",
        "desc": "Emergency prediction & routing",
        "url": "http://localhost:9001",
        "instructions": [
            'cd "d:\\Capsone_all_branches\\Capstone\\Capstone\\ER_NON_ER_PREDICTION_module1\\triage_v3"',
            'python backend.py',
            'cd "d:\\Capsone_all_branches\\Capstone\\Capstone\\ER_NON_ER_PREDICTION_module1\\triage_v3\\triage_v3"',
            'streamlit run app.py --server.port 9001',
        ],
    },
    {
        "name": "Wait Time",
        "icon": "⏱️",
        "desc": "Queue & wait forecasting",
        "url": "http://localhost:9002",
        "instructions": [
            'cd "d:\\Capsone_all_branches\\Capstone\\Capstone-wait-time-prediction\\wait-time-prediction"',
            'streamlit run 1_app.py --server.port 9002',
        ],
    },
    {
        "name": "Adaptive",
        "icon": "🧭",
        "desc": "Adaptive question flow",
        "url": "http://localhost:9003",
        "instructions": [
            'cd "d:\\Capsone_all_branches\\Capstone\\Capstone-adaptive-question-flow\\Adapative_Question_flow"',
            'python backend.py',
            'streamlit run app.py --server.port 9003',
        ],
    },
    {
        "name": "Cost Predictor",
        "icon": "💰",
        "desc": "Healthcare cost forecast",
        "url": "http://localhost:9004",
        "instructions": [
            'cd "d:\\Capsone_all_branches\\Cost_predictor\\backend"',
            'python -m uvicorn main:app --reload --port 8002',
            'cd "d:\\Capsone_all_branches\\Cost_predictor\\frontend"',
            'python -m streamlit run home.py --server.port 9004',
        ],
    },
    {
        "name": "Outbreak Prediction",
        "icon": "🦠",
        "desc": "Outbreak & spread analytics",
        "url": "http://localhost:9005",
        "instructions": [
            'cd "d:\\Capsone_all_branches\\outbreak_prediction\\backend"',
            'python -m uvicorn main:app --reload --port 8001',
            'cd "d:\\Capsone_all_branches\\outbreak_prediction\\frontend"',
            'python -m streamlit run app.py --server.port 9005',
        ],
    },
]

st.set_page_config(
    page_title="Smart Hospital Portal",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed",
)

MODULE_COLORS = {
    "ER Triage": "#f97316",
    "Wait Time": "#f59e0b",
    "Adaptive": "#14b8a6",
    "Cost Predictor": "#6366f1",
    "Outbreak Prediction": "#e11d48",
}

st.markdown(
    """
    <style>
    /* ============ GLOBAL THEME — calm clinical teal/navy ============ */
    html, body, [data-testid="stAppViewContainer"] {
        background: radial-gradient(circle at 12% 8%, rgba(20,184,166,0.10), transparent 30%),
                    radial-gradient(circle at 88% 92%, rgba(13,148,136,0.08), transparent 32%),
                    linear-gradient(160deg, #f3f8f9 0%, #e7f1f3 45%, #eef6f6 100%);
        color: #1e3a8a;
    }
    .css-1d391kg, .css-1v3fvcr, .css-1y4p8pa {
        background: transparent !important;
    }
    h1, h2, h3, h4, p, label, span, div { color: #1e3a8a; }

    /* ============ SIDEBAR / MODULE SELECTION ============ */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0b2530 0%, #0f3b3f 100%) !important;
        border-right: 1px solid rgba(255,255,255,0.06);
    }
    [data-testid="stSidebar"] * { color: #e6f4f1; }
    .sidebar-title {
        font-size: 1.02rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: #5eead4;
        margin: 0.25rem 0 1.1rem;
        padding-bottom: 0.6rem;
        border-bottom: 1px solid rgba(255,255,255,0.1);
    }
    [data-testid="stSidebar"] .stRadio > div[role="radiogroup"] {
        gap: 0.65rem;
    }
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > div {
        margin-bottom: 0 !important;
    }
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] label {
        position: relative;
        display: flex;
        align-items: center;
        gap: 0.7rem;
        background: rgba(255,255,255,0.05);
        border-radius: 14px;
        padding: 0.9rem 1rem 0.9rem 1.1rem;
        font-size: 1rem;
        font-weight: 500;
        color: #dff5f1;
        border: 1px solid rgba(255,255,255,0.08);
        border-left: 3px solid transparent;
        transition: all 0.18s ease;
        cursor: pointer;
    }
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] label:hover {
        background: rgba(45,212,191,0.12);
        border-left-color: rgba(45,212,191,0.55);
        transform: translateX(2px);
    }
    [data-testid="stSidebar"] .stRadio input:checked + div {
        background: linear-gradient(135deg, rgba(20,184,166,0.28), rgba(13,148,136,0.28));
        color: #f0fdfa;
        border-left: 3px solid #2dd4bf;
        box-shadow: inset 0 0 0 1px rgba(45,212,191,0.3);
    }
    .sidebar-user-card {
        margin-top: 1.3rem;
        padding: 0.85rem 1rem;
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 14px;
        font-size: 0.9rem;
    }
    .sidebar-user-card .u-name {
        font-weight: 700;
        color: #f0fdfa;
    }
    .sidebar-user-card .u-role {
        display: inline-block;
        margin-top: 0.3rem;
        font-size: 0.72rem;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        color: #5eead4;
        background: rgba(45,212,191,0.14);
        padding: 0.15rem 0.55rem;
        border-radius: 999px;
    }
    [data-testid="stSidebar"] .stButton>button {
        width: 100%;
        margin-top: 0.9rem;
        background: rgba(248,113,113,0.14) !important;
        color: #fecaca !important;
        border: 1px solid rgba(248,113,113,0.35) !important;
        border-radius: 999px !important;
        font-weight: 600;
        box-shadow: none !important;
    }
    [data-testid="stSidebar"] .stButton>button:hover {
        background: rgba(248,113,113,0.24) !important;
    }

    /* ============ LOGIN PAGE ============ */
    /* Streamlit container(key="login_card") renders with class st-key-login_card */
    .st-key-login_card {
        max-width: 920px;
        margin: 1.5rem auto 0;
        background: linear-gradient(115deg, #0f9b6c 0%, #16a34a 34%, #ffffff 36%, #ffffff 100%);
        border-radius: 24px;
        padding: 2.6rem 2.8rem;
        box-shadow: 0 25px 70px rgba(15, 59, 63, 0.28);
        border: 1px solid rgba(15,23,42,0.05);
    }
    .login-green-inner {
        padding: 1.4rem 1.2rem 1.4rem 0.2rem;
        color: white;
    }
    .login-green-inner .g-title {
        font-size: 2.5rem;
        font-weight: 800;
        margin-bottom: 0.7rem;
        line-height: 1.1;
    }
    .login-green-inner .g-sub {
        font-size: 1rem;
        opacity: 0.96;
        line-height: 1.6;
        margin-bottom: 1.6rem;
        max-width: 260px;
    }
    .login-green-inner .g-badge {
        display: inline-block;
        border: 1.5px solid rgba(255,255,255,0.85);
        border-radius: 999px;
        padding: 0.5rem 1.3rem;
        font-weight: 600;
        font-size: 0.9rem;
    }
    .login-form-area .form-heading {
        font-size: 1.9rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 0.3rem;
    }
    .login-form-area .form-note {
        color: #64748b;
        font-size: 0.9rem;
        margin-bottom: 1.3rem;
    }
    .st-key-login_card .stTextInput>label {
        color: #1e293b !important;
        font-weight: 600;
        font-size: 0.88rem;
    }
    .st-key-login_card .stTextInput>div>div>input {
        border-radius: 12px;
        border: 1px solid rgba(15,23,42,0.15);
        background: #f8fafc;
        padding: 0.75rem 0.9rem;
        color: #0f172a;
    }
    .st-key-login_card .stFormSubmitButton>button {
        width: 100%;
        background: #16a34a !important;
        color: white !important;
        border: none !important;
        border-radius: 999px !important;
        padding: 0.75rem 1.4rem !important;
        font-weight: 700 !important;
        box-shadow: 0 8px 20px rgba(22,163,74,0.28) !important;
        margin-top: 0.3rem;
    }
    .st-key-login_card .stFormSubmitButton>button:hover {
        background: #15803d !important;
    }
    .register-toggle .stButton>button {
        background: transparent !important;
        border: none !important;
        color: #0d9488 !important;
        font-size: 0.88rem !important;
        font-weight: 600;
        text-decoration: underline;
        box-shadow: none !important;
        padding-left: 0 !important;
    }
    .st-key-register_card {
        max-width: 480px;
        margin: 1.5rem auto 0;
        background: #ffffff;
        border: 1px solid rgba(15,23,42,0.08);
        border-radius: 20px;
        padding: 1.8rem 2rem;
        box-shadow: 0 15px 40px rgba(15,23,42,0.08);
    }
    .register-heading {
        font-size: 1.35rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 0.15rem;
    }
    .register-note {
        color: #64748b;
        font-size: 0.88rem;
        margin-bottom: 1.1rem;
    }
    .st-key-register_card .stFormSubmitButton>button {
        width: 100%;
        background: #0d9488 !important;
        color: white !important;
        border: none !important;
        border-radius: 999px !important;
        font-weight: 700 !important;
        box-shadow: 0 8px 20px rgba(13,148,136,0.25) !important;
    }
    .st-key-register_card .stFormSubmitButton>button:hover {
        background: #0f766e !important;
    }

    /* ============ HEADER / GENERAL CONTENT ============ */
    .top-header {
        position: sticky;
        top: 0;
        z-index: 999;
        background: linear-gradient(120deg, #0b2530 0%, #0f3b3f 100%);
        backdrop-filter: blur(16px);
        border-bottom: 1px solid rgba(255,255,255,0.08);
        padding: 1rem 2rem;
        margin-bottom: 1.5rem;
        border-radius: 0 0 18px 18px;
    }
    .top-header h1 {
        margin: 0;
        font-size: 2.3rem;
        color: #f0fdfa;
        font-weight: 800;
        letter-spacing: -0.03rem;
    }
    .top-header p {
        margin: 0.35rem 0 0;
        color: rgba(224,242,241,0.82);
        font-size: 1rem;
    }
    .content-card {
        background: #ffffff;
        border-radius: 24px;
        padding: 1.5rem;
        border: 1px solid rgba(15,23,42,0.06);
        box-shadow: 0 10px 30px rgba(15,23,42,0.05);
    }
    .stButton>button {
        background: linear-gradient(135deg, #14b8a6, #0d9488) !important;
        color: #fff !important;
        border: none !important;
        font-weight: 600;
        padding: 0.9rem 1.6rem !important;
        border-radius: 999px !important;
        box-shadow: 0 8px 20px rgba(13,148,136,0.22) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "token" not in st.session_state:
    st.session_state["token"] = None
if "role" not in st.session_state:
    st.session_state["role"] = None
if "name" not in st.session_state:
    st.session_state["name"] = None
if "profile_id" not in st.session_state:
    st.session_state["profile_id"] = None
if "show_register" not in st.session_state:
    st.session_state["show_register"] = False

st.markdown(
    "<div class='top-header'><h1>Smart Hospital Portal</h1></div>",
    unsafe_allow_html=True,
)

# ============ Authentication UI (only when not logged in) ============
if not st.session_state.get("token"):
    page_cols = st.columns([1, 4, 1])
    with page_cols[1]:
        with st.container(key="login_card"):
            green_col, form_col = st.columns([0.85, 1.15], gap="large")

            with green_col:
                st.markdown(
                    """
                    <div class="login-green-inner">
                        <div class="g-title">Welcome!</div>
                        <div class="g-sub">Sign in to reach ER triage, wait-time, cost and outbreak tools from one hospital hub.</div>
                       a
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with form_col:
                st.markdown('<div class="login-form-area">', unsafe_allow_html=True)
                st.markdown('<div class="form-heading">Login</div>', unsafe_allow_html=True)
                st.markdown('<div class="form-note">Enter your email and password to continue.</div>', unsafe_allow_html=True)
                with st.form("login_form"):
                    email = st.text_input("Username/Email address", key="login_email")
                    password = st.text_input("Password", type="password", key="login_password")
                    login_sub = st.form_submit_button("Sign In")
                    if login_sub:
                        if not email or not password:
                            st.warning("Enter both email and password.")
                        else:
                            try:
                                response = requests.post(f"{API}/login", json={"email": email, "password": password}, timeout=10)
                                if response.ok:
                                    data = response.json()
                                    st.session_state["token"] = data.get("token")
                                    st.session_state["role"] = data.get("role")
                                    st.session_state["profile_id"] = data.get("profile_id")
                                    st.session_state["name"] = data.get("name")
                                    st.success("Login successful.")
                                    st.rerun()
                                else:
                                    st.error(response.json().get("message", "Login failed."))
                            except Exception as exc:
                                st.error(f"Authentication backend unavailable: {exc}")
                st.markdown('<div class="register-toggle">', unsafe_allow_html=True)
                if st.button("New here? Create an account", key="toggle_register"):
                    st.session_state["show_register"] = not st.session_state["show_register"]
                st.markdown('</div></div>', unsafe_allow_html=True)

        # Registration, revealed on demand so the primary login view stays clean
        if st.session_state["show_register"]:
            with st.container(key="register_card"):
                st.markdown('<div class="register-heading">Register</div>', unsafe_allow_html=True)
                st.markdown('<div class="register-note">Create a new account for hospital staff or patients.</div>', unsafe_allow_html=True)
                with st.form("register_form"):
                    r_role = st.selectbox("Role", ["patient", "doctor", "nurse", "admin"], index=0)
                    r_name = st.text_input("Name", key="r_name")
                    r_email = st.text_input("Email", key="r_email")
                    r_password = st.text_input("Password", type="password", key="r_password")
                    r_extra = st.text_input("Department / Specialty", key="r_extra")
                    reg_sub = st.form_submit_button("Register")
                    if reg_sub:
                        if not r_email or not r_password or not r_name:
                            st.warning("Provide name, email and password.")
                        else:
                            try:
                                endpoint = f"{API}/register/{r_role}"
                                payload = {"email": r_email, "password": r_password, "name": r_name}
                                if r_role in ("doctor", "nurse"):
                                    payload.update({"department": r_extra, "specialty": r_extra})
                                resp = requests.post(endpoint, json=payload, timeout=10)
                                if resp.ok:
                                    st.success("Registered successfully. Log in with your new account.")
                                else:
                                    st.error(resp.json().get("message", "Registration failed."))
                            except Exception as e:
                                st.error(f"Registration backend unavailable: {e}")
    st.stop()

st.markdown("---")

# ============ Auto-run sequence: after login, open ER then proceed automatically ============
if st.session_state.get("token"):
    module_names = [module["name"] for module in MODULES]
    if "selected_module" not in st.session_state:
        st.session_state["selected_module"] = module_names[0]

    st.sidebar.markdown("<div class='sidebar-title'>Module Selection</div>", unsafe_allow_html=True)

    icon_map = {m["name"]: m["icon"] for m in MODULES}
    selected_name = st.sidebar.radio(
        "",
        module_names,
        index=module_names.index(st.session_state["selected_module"]),
        key="sidebar_module",
        format_func=lambda n: f"{icon_map[n]}   {n}",
        label_visibility="collapsed",
    )
    st.session_state["selected_module"] = selected_name
    selected_module = next(module for module in MODULES if module["name"] == selected_name)

    if selected_module["name"] == "Adaptive":
        query = urllib.parse.urlencode(
            {
                "token": st.session_state["token"],
                "role": st.session_state["role"],
                "name": st.session_state["name"],
                "profile_id": st.session_state["profile_id"],
            }
        )
        module_url = f"{selected_module['url']}?{query}"
    else:
        module_url = selected_module["url"]

    st.sidebar.markdown(
        f"""
        <div class="sidebar-user-card">
            <div class="u-name">{st.session_state['name']}</div>
            <span class="u-role">{st.session_state['role']}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.sidebar.button("Logout", key="logout_button"):
        st.session_state["token"] = None
        st.session_state["role"] = None
        st.session_state["profile_id"] = None
        st.session_state["name"] = None
        st.session_state.pop("selected_module", None)
        st.rerun()

    st.title(f"Welcome, {st.session_state['name']}")
    st.write("Default flow begins with ER triage after login. Use the sidebar to switch to Wait Time or Adaptive.")
else:
    st.title("Smart Hospital Portal")
    st.write("Please login or register to continue.")
    st.stop()

try:
    components.iframe(module_url, height=950)
except Exception as exc:
    st.error("Unable to embed the selected module. Make sure it is running at the displayed URL.")
    st.exception(exc)