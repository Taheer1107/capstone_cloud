Outbreak Prediction

Paths:
- Frontend: outbreak_prediction/frontend/app.py
- Backend: outbreak_prediction/backend/main.py (FastAPI)

Run backend (example):
```powershell
cd "outbreak_prediction/backend"
pip install fastapi uvicorn pandas scikit-learn
python -m uvicorn main:app --reload --port 8001
```

Run frontend (example):
```powershell
cd "outbreak_prediction/frontend"
pip install -r ../backend/requirements.txt
python -m streamlit run app.py --server.port 9005
```

Models:
- `outbreak_prediction/models/*.pkl` — ensure these are present.
