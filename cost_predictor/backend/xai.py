import pickle
import shap
import pandas as pd


# ==========================================
# LOAD MODEL
# ==========================================

with open("models/catboost_v3.pkl", "rb") as f:
    model = pickle.load(f)

with open("models/feature_columns_v3.pkl", "rb") as f:
    feature_columns = pickle.load(f)


# ==========================================
# CREATE SHAP EXPLAINER
# ==========================================

explainer = shap.TreeExplainer(model)


# ==========================================
# PREPARE INPUT
# ==========================================

def prepare_input(
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

    return df


# ==========================================
# GROUP SHAP VALUES
# ==========================================

def explain_prediction(
    procedure,
    specialty,
    hospital_type,
    city_tier,
    age
):

    X = prepare_input(
        procedure,
        specialty,
        hospital_type,
        city_tier,
        age
    )

    shap_values = explainer.shap_values(X)

    shap_df = pd.DataFrame({
        "feature": feature_columns,
        "impact": shap_values[0]
    })

    grouped = {
        "Procedure": 0,
        "Specialty": 0,
        "Hospital Type": 0,
        "City Tier": 0,
        "Age": 0,
        "Other": 0
    }

    for _, row in shap_df.iterrows():

        feature = row["feature"]
        impact = float(row["impact"])

        if feature.startswith("procedure_"):
            grouped["Procedure"] += impact

        elif feature.startswith("specialty_"):
            grouped["Specialty"] += impact

        elif feature.startswith("hospital_type_"):
            grouped["Hospital Type"] += impact

        elif feature.startswith("city_tier_"):
            grouped["City Tier"] += impact

        elif feature == "patient_age":
            grouped["Age"] += impact

        else:
            grouped["Other"] += impact

    return grouped