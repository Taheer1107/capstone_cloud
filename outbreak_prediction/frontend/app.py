import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import requests
import streamlit as st


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "processed_dataset.csv"
if not DATA_FILE.exists():
    DATA_FILE = BASE_DIR / "models" / "training_snapshot.csv"
GEOJSON_FILE = BASE_DIR / "frontend" / "india_states.geojson"
API_BASE_URL = "http://127.0.0.1:8001"

# -------------------- PAGE CONFIG --------------------
st.set_page_config(
    page_title="Outbreak Surveillance - India",
    layout="wide",
)

st.title("Outbreak Surveillance Dashboard - India")
st.caption("Weekly disease surveillance based on reported cases")


# -------------------- LOAD DATA --------------------
@st.cache_data(ttl=1)
def load_data():
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Dataset not found: {DATA_FILE}")

    data = pd.read_csv(DATA_FILE)
    data["state"] = data["state"].astype(str).str.strip()
    data["disease"] = data["disease"].astype(str).str.strip()
    data["cases"] = pd.to_numeric(data["cases"], errors="coerce").fillna(0)
    data["deaths"] = pd.to_numeric(data["deaths"], errors="coerce").fillna(0)
    if "week" not in data.columns and {"year", "week_num"}.issubset(data.columns):
        data["week"] = (
            data["year"].astype(int).astype(str)
            + "-W"
            + data["week_num"].astype(int).astype(str).str.zfill(2)
        )
    return data


@st.cache_data
def load_geojson():
    with open(GEOJSON_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


df = load_data()
india_geojson = load_geojson()

# -------------------- CLEAN --------------------
df["cases"] = df["cases"].astype(int)

# REMOVE BAD STATES
df = df[~df["state"].str.contains(r"/", na=False)]

# -------------------- ADD YEAR COLUMN --------------------
df["year"] = df["week"].str[:4]

# -------------------- SIDEBAR --------------------
st.sidebar.header("Controls")

selected_year = st.sidebar.selectbox(
    "Select Year",
    sorted(df["year"].unique()),
)

df = df[df["year"] == selected_year]

# -------------------- CONTINUE NORMAL FLOW --------------------
df = df.sort_values("week")

all_weeks = sorted(df["week"].unique())
latest_week = all_weeks[-1]

selected_disease = st.sidebar.selectbox(
    "Disease",
    ["All Diseases"] + sorted(df["disease"].unique()),
)

time_window = st.sidebar.radio(
    "Time Window",
    ["Latest Week", "Last 4 Weeks", "Last 8 Weeks", "Last 12 Weeks"],
    index=1,
)

# -------------------- FILTER --------------------
if time_window == "Latest Week":
    weeks_to_use = [latest_week]
elif time_window == "Last 4 Weeks":
    weeks_to_use = all_weeks[-4:]
elif time_window == "Last 8 Weeks":
    weeks_to_use = all_weeks[-8:]
else:
    weeks_to_use = all_weeks[-12:]

filtered_df = df[df["week"].isin(weeks_to_use)]

if selected_disease != "All Diseases":
    filtered_df = filtered_df[filtered_df["disease"] == selected_disease]

# -------------------- MAP --------------------
state_cases = filtered_df.groupby("state", as_index=False)["cases"].sum()

all_states = [f["properties"]["NAME_1"].strip() for f in india_geojson["features"]]

full_map_df = pd.DataFrame({"state": all_states})
full_map_df = full_map_df.merge(state_cases, on="state", how="left")
full_map_df["cases"] = full_map_df["cases"].fillna(0)

st.subheader(f"Outbreak Map ({selected_year})")

fig_map = px.choropleth(
    full_map_df,
    geojson=india_geojson,
    locations="state",
    featureidkey="properties.NAME_1",
    color="cases",
    color_continuous_scale="Reds",
    hover_name="state",
)

fig_map.update_geos(
    scope="asia",
    visible=False,
    center={"lat": 22.5, "lon": 78.9},
    projection_scale=4.5,
)

fig_map.update_layout(height=650, margin={"r": 0, "t": 0, "l": 0, "b": 0})

st.plotly_chart(fig_map, use_container_width=True)

# -------------------- TREND --------------------
st.subheader("Trend Analysis")

trend_df = filtered_df.groupby("week", as_index=False)["cases"].sum()

fig_trend = px.line(
    trend_df,
    x="week",
    y="cases",
    markers=True,
    title="Reported cases over time",
)

st.plotly_chart(fig_trend, use_container_width=True)

# -------------------- TOP STATES --------------------
st.subheader("Most Affected States")

top_states = (
    filtered_df.groupby("state", as_index=False)["cases"]
    .sum()
    .sort_values("cases", ascending=False)
    .head(10)
)

st.table(top_states)

# -------------------- ML PREDICTION --------------------
st.markdown("---")
st.subheader("Outbreak Prediction (ML Model)")

try:
    health_response = requests.get(f"{API_BASE_URL}/health", timeout=5)
    if health_response.ok:
        health_data = health_response.json()
        if health_data.get("api_running") and health_data.get("model_loaded"):
            st.success(
                f"Backend online | {health_data.get('model_type', 'model')} | "
                f"{health_data.get('feature_count', 0)} features"
            )
        else:
            st.warning("Backend responded, but the model is not ready.")
    else:
        st.warning(f"Backend health check failed: HTTP {health_response.status_code}")
except requests.exceptions.ConnectionError:
    st.warning("Backend is offline. Start FastAPI before using prediction.")
except requests.exceptions.Timeout:
    st.warning("Backend health check timed out.")
except ValueError:
    st.warning("Backend health check returned an invalid response.")

input_state = st.selectbox("Select State", sorted(df["state"].unique()))
input_disease = st.selectbox("Select Disease", sorted(df["disease"].unique()))

latest_week_num = int(str(latest_week).split("W")[-1].split("-")[-1])

col1, col2, col3 = st.columns(3)
with col1:
    prediction_year = st.number_input("Year", min_value=1900, value=int(selected_year))
    week_of_year = st.number_input(
        "Week of year",
        min_value=1,
        max_value=53,
        value=latest_week_num,
    )
    current_cases = st.number_input("Current week cases", min_value=0.0, value=10.0)
    current_deaths = st.number_input("Current week deaths", min_value=0.0, value=0.0)

with col2:
    previous_week_cases = st.number_input("Previous week cases", min_value=0.0, value=8.0)
    cases_lag2 = st.number_input("Cases 2 weeks ago", min_value=0.0, value=6.0)
    cases_lag3 = st.number_input("Cases 3 weeks ago", min_value=0.0, value=5.0)
    cases_lag4 = st.number_input("Cases 4 weeks ago", min_value=0.0, value=4.0)

with col3:
    rolling_mean_3 = st.number_input("Rolling mean 3", min_value=0.0, value=6.33)
    rolling_mean_5 = st.number_input("Rolling mean 5", min_value=0.0, value=6.0)
    rolling_std_3 = st.number_input("Rolling std 3", min_value=0.0, value=1.5)

if st.button("Predict Outbreak"):
    payload = {
        "state": input_state,
        "disease": input_disease,
        "year": int(prediction_year),
        "week_of_year": int(week_of_year),
        "cases": float(current_cases),
        "deaths": float(current_deaths),
        "previous_week_cases": float(previous_week_cases),
        "cases_lag2": float(cases_lag2),
        "cases_lag3": float(cases_lag3),
        "cases_lag4": float(cases_lag4),
        "rolling_mean_3": float(rolling_mean_3),
        "rolling_mean_5": float(rolling_mean_5),
        "rolling_std_3": float(rolling_std_3),
    }

    try:
        response = requests.post(
            f"{API_BASE_URL}/predict",
            json=payload,
            timeout=10,
        )
        response.raise_for_status()
        result = response.json()

        required_keys = {
            "outbreak",
            "outbreak_probability",
            "risk_level",
            "model_type",
        }
        if not required_keys.issubset(result):
            st.warning(f"Invalid API response: {result}")
        else:
            outbreak_detected = int(result["outbreak"]) == 1
            probability = float(result["outbreak_probability"]) * 100

            if outbreak_detected:
                st.error("Outbreak detected: Yes")
            else:
                st.success("Outbreak detected: No")

            st.metric("Outbreak probability", f"{probability:.2f}%")
            st.write(f"Risk level: **{result['risk_level']}**")
            st.write(f"Model type: `{result['model_type']}`")

    except requests.exceptions.ConnectionError:
        st.error("Could not connect to the backend. Make sure FastAPI is running on port 8000.")
    except requests.exceptions.Timeout:
        st.error("Prediction request timed out. Please try again.")
    except requests.exceptions.HTTPError as e:
        try:
            st.error(f"API error: {response.json()}")
        except ValueError:
            st.error(f"API error: {e}")
    except ValueError:
        st.error("Backend returned an invalid JSON response.")
    except Exception as e:
        st.error(f"Backend error: {e}")
