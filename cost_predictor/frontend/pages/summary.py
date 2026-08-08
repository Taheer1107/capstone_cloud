import streamlit as st
from pathlib import Path
import plotly.express as px
import pandas as pd
import html
import re
from utils.insurance_advisor import calculate_adequacy
import sys
from pathlib import Path


BACKEND_PATH = (
    Path(__file__)
    .resolve()
    .parents[2]
    /
    "backend"
)

sys.path.append(
    str(BACKEND_PATH)
)
from agents.financial_advisor import FinancialAdvisorAgent

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="Final Summary",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================
# LOAD CSS
# =====================================================
def load_css():
    css_path = Path(__file__).resolve().parents[1] / "style.css"
    if css_path.exists():
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(
                f"<style>{f.read()}</style>",
                unsafe_allow_html=True
            )

load_css()

# =====================================================
# SESSION
# =====================================================
base_cost = float(st.session_state.get("base_cost", 0))

# Has the user estimated a treatment yet?
estimation_ready = (
    st.session_state.get("ready", False)
    and base_cost > 0
)

def money(x):

    x = int(round(x))

    s = str(x)

    if len(s) <= 3:
        return f"₹{s}"

    last3 = s[-3:]
    rest = s[:-3]

    parts = []

    while len(rest) > 2:
        parts.insert(0, rest[-2:])
        rest = rest[:-2]

    if rest:
        parts.insert(0, rest)

    return "₹" + ",".join(parts + [last3])

def clean_display_text(text):

    emoji_pattern = re.compile(
        "["
        "\U0001F300-\U0001FAFF"
        "\U00002700-\U000027BF"
        "\U00002600-\U000026FF"
        "\u200D"
        "\uFE0F"
        "]+",
        flags=re.UNICODE
    )

    return emoji_pattern.sub("", text)

def render_report_card_markdown(text):

    lines = clean_display_text(text).splitlines()
    html_parts = []
    list_type = None

    def close_list():
        nonlocal list_type
        if list_type:
            html_parts.append(f"</{list_type}>")
            list_type = None

    def inline_format(value):
        escaped = html.escape(value.strip())
        return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)

    for line in lines:
        stripped = line.strip()

        if not stripped:
            close_list()
            continue

        if stripped.startswith("### "):
            close_list()
            html_parts.append(f"<h3>{inline_format(stripped[4:])}</h3>")
            continue

        if stripped.startswith("## "):
            close_list()
            html_parts.append(f"<h2>{inline_format(stripped[3:])}</h2>")
            continue

        if stripped.startswith("- ") or stripped.startswith("* "):
            if list_type != "ul":
                close_list()
                html_parts.append("<ul>")
                list_type = "ul"
            html_parts.append(f"<li>{inline_format(stripped[2:])}</li>")
            continue

        numbered = re.match(r"^\d+\.\s+(.*)$", stripped)
        if numbered:
            if list_type != "ol":
                close_list()
                html_parts.append("<ol>")
                list_type = "ol"
            html_parts.append(f"<li>{inline_format(numbered.group(1))}</li>")
            continue

        close_list()
        html_parts.append(f"<p>{inline_format(stripped)}</p>")

    close_list()

    return "\n".join(html_parts)

coverage = st.session_state.get("coverage", None)

if coverage is None:
    st.error("Coverage has not been calculated.")
    st.stop()

gross_bill = coverage["gross_bill"]

waterfall = coverage["waterfall"]

patient_pay = coverage["patient_pays"]

# =====================================================
# SIDEBAR
# =====================================================
with st.sidebar:

    st.markdown("""
    <div class='brand-box'>
        <div class='brand-main'>HealthCare</div>
        <div class='brand-sub'>Cost Estimator</div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Main", use_container_width=True):
        st.switch_page("pages/user.py")

    if st.button("Insurance", use_container_width=True):
        st.switch_page("pages/insurance.py")

    if st.button("Military", use_container_width=True):
        st.switch_page("pages/military.py")

    if st.button("Govt Employee", use_container_width=True):
        st.switch_page("pages/govt_employee.py")

    if st.button("Summary", use_container_width=True):
        st.rerun()

# =====================================================
# TITLE
# =====================================================
st.markdown("""
<div class='hero-box'>
<div>
<div class='hero-title'>Final Cost Summary</div>
<div class='hero-sub'>Coverage applied based on eligibility and policy rules</div>
</div>
</div>
""", unsafe_allow_html=True)

# =====================================================
# VALIDATION
# =====================================================
if not estimation_ready:

    st.info(
        "Estimate the treatment cost first from the Main page to view the final summary."
    )

    if st.button("Go to Main Page", use_container_width=True):
        st.switch_page("pages/user.py")

    st.stop()
    
# =====================================================
# TOP RESULT CARDS
# =====================================================
a, b, c = st.columns(3)

with a:
    st.markdown(f"""
    <div class='metric-card'>
    <div class='metric-title'>TOTAL BILL</div>
    <div class='metric-value'>{money(gross_bill["total"])}</div>
    </div>
    """, unsafe_allow_html=True)

with b:

    total_covered = sum(
    item["covered"]
    for item in coverage["waterfall"]
)

    st.markdown(f"""
    <div class='metric-card metric-green'>
    <div class='metric-title'>TOTAL COVERED</div>
    <div class='metric-value'>{money(total_covered)}</div>
    </div>
    """, unsafe_allow_html=True)

with c:
    st.markdown(f"""
    <div class='metric-card metric-purple'>
    <div class='metric-title'>YOU PAY</div>
    <div class='metric-value'>{money(patient_pay)}</div>
    </div>
    """, unsafe_allow_html=True)

# =====================================================
# COVERAGE BREAKDOWN
# =====================================================
st.markdown("## Coverage Breakdown")

if len(coverage["waterfall"]) == 0:

    st.info("No healthcare scheme has been applied.")

else:
    for i, scheme in enumerate(coverage["waterfall"], start=1):

        st.markdown(
            f"""
            <div class='coverage-card'>
                <div class='coverage-card-header'>
                    <div>
                        <div class='coverage-card-title'>{scheme['scheme']}</div>
                        <div class='coverage-card-subtitle'>{scheme['type']} Scheme</div>
                    </div>
                </div>
                <div class='coverage-card-covered'>
                    <div class='coverage-amount-label'>Covered</div>
                    <div class='coverage-amount-value'>{money(scheme['covered'])}</div>
                </div>
                <div class='scheme-amount-grid'>
                    <div class='scheme-amount-card green'>
                        <div class='scheme-label'>Amount Paid</div>
                        <div class='scheme-value'>{money(scheme['covered'])}</div>
                    </div>
                    <div class='scheme-amount-card blue'>
                        <div class='scheme-label'>Remaining Bill</div>
                        <div class='scheme-value'>{money(scheme['remaining'])}</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
# =====================================================
# COVERAGE EXPLANATION
# =====================================================



# =====================================================
# INSURANCE ADEQUACY ADVISOR
# =====================================================

sum_insured = st.session_state.get(
    "sum_insured",
    0
)

if sum_insured > 0:

    total_covered = sum(
    item["covered"]
    for item in waterfall
)


calculate_adequacy(
    total_bill=gross_bill["total"],
    sum_insured=sum_insured,
    total_covered=total_covered
)

# =====================================================
# STATUS MESSAGE
# =====================================================

gross_total = gross_bill["total"]

coverage_paid = gross_total - patient_pay

if patient_pay == 0:
    st.success("Fully covered. No patient payment required.")

elif coverage_paid >= gross_total * 0.70:
    st.warning("Mostly covered. Small patient payment remains.")

else:
    st.error("Low coverage. Higher out-of-pocket payment remains.")


# =====================================================
# FINANCIAL ADVISOR AGENT
# =====================================================

# =====================================================
# AI FINANCIAL HEALTH ASSESSMENT
# =====================================================

agent = FinancialAdvisorAgent()


risk = agent.calculate_financial_risk(

    patient_pay=coverage["patient_pays"],

    total_bill=gross_bill["total"]

)


risk_level = risk["risk_level"]


risk_config = {

    "High": {
        "icon": "",
        "title": "High Financial Risk",
        "message":
        "A significant portion of the treatment cost remains your responsibility."
    },

    "Medium": {
        "icon": "",
        "title": "Moderate Financial Risk",
        "message":
        "Your coverage reduces the burden, but additional planning may help."
    },

    "Low": {
        "icon": "",
        "title": "Low Financial Risk",
        "message":
        "Your current healthcare coverage provides good protection."
    }

}
current = risk_config[risk_level]

# ==========================================
# AI RECOMMENDATIONS
# ==========================================


advisor_result = agent.generate_advice(

    predicted_cost=gross_bill["total"],

    explanation=st.session_state.get(
        "explanation",
        {}
    ),

    coverage=coverage,

    insurance_info={

        "provider":
        st.session_state.get(
            "insurance_provider",
            ""
        ),

        "city_tier":
        st.session_state.get(
            "city_tier",
            "Tier-2"
        )

    },

    scheme=st.session_state.get(
        "primary_scheme",
        "Self Pay"
    )

)

recommendations = advisor_result["recommendations"]
from agents.gemini_helper import generate_financial_explanation
llm_explanation = generate_financial_explanation(

    risk=advisor_result["risk"],

    catastrophic=advisor_result["catastrophic"],

    recommendations=advisor_result["recommendations"],

    provider=st.session_state.get(
        "insurance_provider",
        ""
    ),

    city_tier=st.session_state.get(
        "city_tier",
        "Tier-2"
    )

)

overall_intro = f"""
## Coverage Summary

**Risk Level:** {current["title"]}

{current["message"]}

"""

financial_report_html = render_report_card_markdown(
    overall_intro + "\n" + llm_explanation
)
st.markdown("## Financial Assessment")
st.markdown(
    f"""
    <div class='financial-assessment-card financial-report'>
        {financial_report_html}
    </div>
    """,
    unsafe_allow_html=True
)
# =====================================================
# RESET BUTTON
# =====================================================
if st.button("Start New Estimation", use_container_width=True):
    keys_to_clear = [

    # Main estimation
    "ready",
    "base_cost",
    "coverage",
    "explanation",

    # Procedure details
    "procedure",
    "specialty",
    "city_tier",
    "hospital_type",
    "ward_type",
    "age",

    # Insurance
    "primary_scheme",
    "has_topup",
    "insurance_provider",
    "sum_insured",

    # Government
    "govt_scheme",

    # Military
    "military_scheme",

    # Final bill
    "patient_pays"

]

    for key in keys_to_clear:

        st.session_state.pop(key, None)

    st.switch_page("pages/user.py")
