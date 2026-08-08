import pickle
import pandas as pd
from xai import explain_prediction

# ==========================
# LOAD MODEL
# ==========================

with open("models/catboost_v3.pkl", "rb") as f:
    model = pickle.load(f)

with open("models/feature_columns_v3.pkl", "rb") as f:
    feature_columns = pickle.load(f)

# ==========================
# PREDICT
# ==========================

def predict_cost(
    procedure,
    specialty,
    hospital_type,
    city_tier,
    age
):

    row = {
        "procedure": procedure,
        "specialty": specialty,
        "hospital_type": hospital_type,
        "city_tier": city_tier,
        "patient_age": age,
        "comorbidity": "None"
    }

    df = pd.DataFrame([row])

    df = pd.get_dummies(df)

    df = df.reindex(
        columns=feature_columns,
        fill_value=0
    )

    prediction = max(0, float(model.predict(df)[0]))

    return prediction


# ==========================
# PREDICT WITH EXPLANATION
# ==========================

def predict_with_explanation(
    procedure,
    specialty,
    hospital_type,
    city_tier,
    age
):

    prediction = predict_cost(
        procedure,
        specialty,
        hospital_type,
        city_tier,
        age
    )

    explanation = explain_prediction(
        procedure,
        specialty,
        hospital_type,
        city_tier,
        age
    )

    return {
        "prediction": prediction,
        "explanation": explanation
    }