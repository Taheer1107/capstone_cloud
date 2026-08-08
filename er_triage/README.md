ER Triage

Path examples:
- Capstone/Capstone/ER_NON_ER_PREDICTION_module1/triage_v3/
- The Streamlit app(s) live under `triage_v3/` (see `triage_v3/app.py` and `triage_v3/backend.py`).

Run (example):
```powershell
cd "Capstone/Capstone/ER_NON_ER_PREDICTION_module1/triage_v3"
# start backend (if required)
python backend.py
# start Streamlit app
python -m streamlit run app.py --server.port 9001
```

Dependencies:
- Mostly Streamlit + common ML libs. If you encounter missing modules, install:

```powershell
pip install streamlit pandas numpy scikit-learn joblib
```

Models/artifacts to keep in place:
- `triage_v3/triage_v3/stacking_final.pkl`
- `triage_v3/triage_v3/features_final.pkl`
- `triage_v3/triage_v3/threshold_final.pkl`

