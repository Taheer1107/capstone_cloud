import os

from dotenv import load_dotenv, find_dotenv
from google import genai

# Load environment variables
load_dotenv(find_dotenv())

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError("GEMINI_API_KEY not found in .env")

# Create Gemini client
client = genai.Client(api_key=api_key)


def generate_financial_explanation(
    risk,
    catastrophic,
    recommendations,
    provider,
    city_tier,
):
    prompt = f"""
You are an experienced healthcare financial advisor helping Indian patients understand their hospital expenses.

IMPORTANT:
- Do NOT change any calculated values.
- Do NOT invent numbers.
- Explain only using the supplied information.
- Keep the tone supportive and professional.
- Maximum 170 words.

Financial Assessment

Risk Level:
{risk["risk_level"]}

Patient Liability:
{risk["liability_percentage"]:.1f}%

Patient Pays:
₹{risk["patient_pay"]:,.0f}

Insurance Provider:
{provider if provider else "None"}

City Tier:
{city_tier}

Catastrophic Healthcare Expense:
{catastrophic["is_catastrophic"]}

Estimated Household Income Used:
₹{catastrophic["reference_income"]:,.0f}

Recommendations:
"""

    for rec in recommendations:
        prompt += f"""

Title:
{rec["title"]}

Reason:
{rec["reason"]}

Suggested Action:
{rec["action"]}
"""

    prompt += """

Generate a personalized financial summary for the patient in Markdown format.

IMPORTANT:
- Return ONLY the Markdown report.
- Do not include introductions such as "Here is your report."
- Do not use code blocks.
- Use the exact section headings given below.
- Keep the report between 150 and 220 words.
- Never invent facts, numbers, insurance benefits, treatments, or recommendations.
- Never contradict the calculated values provided.
- Do not repeat the same information across different sections.
- Use warm, professional, reassuring language that is easy for patients to understand.
- Write naturally, as an experienced healthcare financial advisor would speak to a patient.

Use the following structure exactly.

## 🟢 Overall Financial Assessment

Write 2–3 short paragraphs explaining the patient's financial situation.

Include:
- Financial risk level (Low, Medium, High)
- Whether the current insurance coverage is adequate
- The estimated patient payment in simple language
- Whether the patient is protected from major financial burden
- If catastrophic healthcare expenditure is FALSE, simply state that the assessment does not indicate catastrophic healthcare expenditure.
- If TRUE, explain it briefly using the assessment benchmark.

Do not mention assumed household income unless catastrophic healthcare expenditure is TRUE.
---

## 💰 Insurance Coverage

Use bullet points.

Include:
- Insurance provider
- Total treatment cost
- Amount covered by insurance
- Estimated patient payment
- Whether the current insurance protection appears adequate

---

## 📍 Cost Insights

Briefly explain the factors that influenced the treatment cost using only the provided information.

Examples include:
- City Tier
- Hospital Type
- Insurance Coverage

Do not invent additional reasons.

---

## 💡 Recommended Actions

Convert the provided recommendations into 3–5 short bullet points.

Do not copy the recommendation text word-for-word.

Keep each point short, practical, and patient-friendly.

---

## ❤️ Final Advice

Write one thoughtful closing paragraph (3–5 sentences).

The paragraph should:
- Naturally summarize the patient's financial outcome.
- Mention how their insurance affected the final cost.
- If relevant, briefly mention the effect of the city tier on treatment costs.
- Encourage maintaining or improving insurance coverage based on the patient's current situation.
- Offer one practical suggestion for future healthcare planning.
- End with a warm, reassuring sentence that leaves the patient feeling confident and financially prepared.

The tone should be supportive, professional, personalized, and conversational—not robotic.

The report should complement the structured financial information shown elsewhere in the application instead of repeating it.
"""

    try:
        response = client.models.generate_content(
            model="gemini-flash-latest",
            contents=prompt,
        )

        return response.text

    except Exception as e:
        return f"⚠️ AI explanation could not be generated.\n\n{str(e)}"