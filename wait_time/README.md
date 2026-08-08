# Wait Time Prediction Module


## Overview

This module predicts  wait times using machine learning models trained on two real-world datasets, and integrates predictions into an agentic AI pipeline with built-in safety validation.

## Datasets

| Dataset | Source | Records | Target Variable |
|---------|--------|---------|------------------|
| MIMIC-IV-ED | PhysioNet | 310,712 | Total ED stay (outtime - intime) |
| MC-MED | PhysioNet, Stanford | 109,268 | Triage-to-room wait (Roomed_time - Arrival_time) |

## Models Used

| Model | Dataset | R² | MAE | Purpose |
|-------|---------|-----|-----|---------|
| XGBoost | MC-MED | 0.7439 | 48.50 min | Primary prediction (Current Hospital) |
| XGBoost | MIMIC | 0.2369 | 80.06 min | Comparison prediction (Other Hospital) |
| LightGBM (q10/q50/q90) | MC-MED | - | - | Confidence interval (Best/Predicted/Worst) |
| XGBoost (acuity-specific) | MC-MED | varies | varies | Per-ESI-level prediction |

## Agentic AI Pipeline

The system uses 4 sequential tools:

1. **Tool 1 — Urgency Classifier**: Rule-based clinical scoring using vitals (heart rate, O2 sat, BP, resp rate, pain)
2. **Tool 2a — Current Hospital Wait**: Predicts wait time using MC-MED model
3. **Tool 2b — Other Hospital Wait**: Predicts wait time using MIMIC model
4. **Tool 3 — Hospital Recommender**: Compares wait times and recommends the faster option, with a hard safety override for CRITICAL patients
5. **Tool 4 — Self-Reflection Validator**: Flags unsafe or unreliable predictions before they reach the clinician

## Safety Validation (Tool 4)

The system automatically flags predictions when:
- Predicted wait exceeds 180 minutes (likely overestimation)
- Patient acuity is 1 or 2 (critical patients should never be routed by wait time)
- Model R² is below 0.4 (low confidence prediction)

## Files

| File | Description |
|------|--------------|
| `1_app.py` | Streamlit UI with agentic pipeline |
| `xgboost_mcmed_model.json` | XGBoost model trained on MC-MED |
| `xgboost_model.json` | XGBoost model trained on MIMIC-IV-ED |
| `lgbm_q10.pkl` | LightGBM quantile model — best case (10th percentile) |
| `lgbm_q50.pkl` | LightGBM quantile model — predicted (50th percentile) |
| `lgbm_q90.pkl` | LightGBM quantile model — worst case (90th percentile) |
| `xgb_acuity_3.json` | XGBoost trained only on ESI level 3 patients |
| `xgb_acuity_4.json` | XGBoost trained only on ESI level 4 patients |
| `xgb_acuity_5.json` | XGBoost trained only on ESI level 5 patients |

## Running the App

```bash
pip install streamlit pandas numpy xgboost lightgbm joblib
streamlit run 1_app.py
```

## Key Findings

- MC-MED's wait time definition (triage-to-room) produces significantly better predictions than MIMIC's total, confirming that 
 **target variable quality matters more than dataset size**.
- Acuity-stratified models underperformed the global model due to data scarcity in lower-volume acuity groups (especially ESI-5 with only 670 records).
- LightGBM, CatBoost, and XGBoost converge to nearly identical performance on MC-MED, indicating the dataset — not the algorithm — is the primary driver of accuracy.