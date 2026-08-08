import json

with open("backend.py", "r", encoding="utf-8") as f:
    code = f.read()

# Fix AI_summarize
if "gemini_model and text" not in code:
    find_summary = "def AI_summarize(text: str) -> str:\n"
    replace_summary = find_summary + """
    if gemini_model and text:
        try:
            r = gemini_model.generate_content("Summarize this medical report for a doctor plainly:\\n\\n" + text[:2000])
            if r.text: return r.text.strip()
        except Exception as e:
            print("Gemini summarization fallback triggers.")
"""
    code = code.replace(find_summary, replace_summary)
    
# Fix ai_allocate_doctor
if "gemini_model and available_doctors" not in code:
    find_alloc = "def ai_allocate_doctor("
    replace_alloc = find_alloc
    # We will inject code right inside ai_allocate_doctor
    
    # We look for:
    #     department = mapping.get(patient_details.get("body_part"), "General Physician")
    
    target_block = """    department = mapping.get(patient_details.get("body_part"), "General Physician")
    if any(x in symptom_lower for x in ["fever", "weakness", "cold", "cough"]):
        department = "General Physician"
    if "rash" in symptom_lower or "skin" in symptom_lower:
        department = "Dermatologist"
"""
    
    inject_block = target_block + """
    if gemini_model and available_doctors:
        docs_json = json.dumps([{"id": d["id"], "specialty": d["specialty"], "name": d["name"]} for d in available_doctors])
        p = f'''You are a medical triage AI. Assign the most suitable doctor ID based on symptoms: '{patient_details.get('symptom')}' (Body part: {patient_details.get('body_part')}). 
        Priority: {patient_details.get('priority')}. 
        Available Doctors: {docs_json}.
        Respond ONLY with valid JSON exactly in this format: {{"doctor_id": <int>, "confidence": 0.95, "priority": "<High or Normal>", "department_reason": "<Specialty name>"}}'''
        try:
            resp = gemini_model.generate_content(p)
            out = resp.text.strip().replace('```json', '').replace('```', '').strip()
            parsed = json.loads(out)
            # Find the best_doc mathematically matching the ID
            found = next((d for d in available_doctors if d['id'] == parsed.get('doctor_id')), None)
            if found:
                confidence = parsed.get('confidence', 0.9)
                department = parsed.get('department_reason', department)
                available_doctors = [found] # Force filter to skip fallback logic
        except Exception as e:
            print(f"Gemini allocation failed: {e}")
"""
    code = code.replace(target_block, inject_block)

with open("backend.py", "w", encoding="utf-8") as f:
    f.write(code)

print("Done")
