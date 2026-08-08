Adaptive Question Flow

Path:
- Capstone/Capstone-adaptive-question-flow/Adapative_Question_flow/

Run:
```powershell
cd "Capstone/Capstone-adaptive-question-flow/Adapative_Question_flow"
# start backend (if present)
python backend.py
# start Streamlit app
python -m streamlit run app.py --server.port 9003
```

Notes:
- This module uses an SQLite runtime DB (`hospital_runtime.db`) — ensure the DB files are present in the folder before running.
- If you see query param incompatibilities, the app uses `st.query_params` in newer Streamlit versions.

Requirements:
```powershell
pip install streamlit requests sqlite3 pandas
```
