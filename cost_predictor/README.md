Cost Predictor

Paths:
- Frontend: Cost_predictor/frontend/home.py
- Backend: Cost_predictor/backend/main.py (FastAPI)

Run backend (example):
```powershell
cd "Cost_predictor/backend"
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8002
```

Run frontend (example):
```powershell
cd "Cost_predictor/frontend"
pip install -r ../backend/requirements.txt
python -m streamlit run home.py --server.port 9004
```

Notes:
- The backend already has `requirements.txt` at `Cost_predictor/backend/requirements.txt` — prefer that for backend dependencies.
- The frontend requires `streamlit` and may require additional ML libs if you import them in pages; install `pip install -r ../backend/requirements.txt` to cover both.

Models and artifacts:
- `Cost_predictor/models/*.pkl`
- `Cost_predictor/backend/models/*.pkl`
- `Cost_predictor/backend/artifacts/*.pkl`
