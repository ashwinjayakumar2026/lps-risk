import streamlit as st
import pandas as pd
import json
import plotly.express as px

# -----------------------------
# LOAD DATA
# -----------------------------
with open("districts_light.geojson") as f:
    geojson = json.load(f)

df = pd.read_csv("final_app_data.csv")

# -----------------------------
# UI
# -----------------------------
st.title("Indian Monsoon LPS Risk Dashboard")

col1, col2, col3 = st.columns(3)

with col1:
    risk_type = st.selectbox("Risk Type", ["Population", "Human-System"])

with col2:
    time_label = st.selectbox("Time", ["Present", "Near Future", "Far Future"])

time_map = {
    "Present": "present",
    "Near Future": "near",
    "Far Future": "far"
}

time = time_map[time_label]

with col3:
    agg = st.selectbox("Aggregation", ["mean", "p90", "max"])

# -----------------------------
# COLUMN SELECTION
# -----------------------------
prefix = "pop" if risk_type == "Population" else "sys"
col = f"{prefix}_{agg}_{time}"

# Safety check
if col not in df.columns:
    st.error(f"{col} not found in dataset")
    st.stop()

# -----------------------------
# CLASSIFICATION
# -----------------------------
bins = [0,0.01,0.02,0.03,0.04,0.05,0.06,0.07,0.08,0.09,0.10, 1]
labels = [
    "0–0.01","0.01–0.02","0.02–0.03","0.03–0.04","0.04–0.05",
    "0.05–0.06","0.06–0.07","0.07–0.08","0.08–0.09","0.09–0.10", ">0.10"
]

df["class"] = pd.cut(df[col], bins=bins, labels=labels, include_lowest=True)

# 🔥 KEEP ALL DISTRICTS
df["class"] = df["class"].astype(object)

# Assign explicit label for missing
df.loc[df[col].isna(), "class"] = "No Data"

# Force order
category_order = ["No Data"] + labels
df["class"] = pd.Categorical(df["class"], categories=category_order, ordered=True)

# -----------------------------
# COLOR SCALE
# -----------------------------
colors = [
    "#d3d3d3",  # No Data
    "#ffffff",  # 0–0.01
    "#fee5d9",
    "#fcbba1",
    "#fc9272",
    "#fb6a4a",
    "#ef3b2c",
    "#e31a1c",   
    "#cb181d",
    "#a50f15",
    "#800026",
    "#67000d" # slightly dark, but not extreme
]

# -----------------------------
# MAP
# -----------------------------
fig = px.choropleth(
    df,
    geojson=geojson,
    locations="DIST_ID",
    featureidkey="properties.DIST_ID",
    color="class",
    category_orders={"class": category_order},
    color_discrete_sequence=colors,
    hover_name="district"
)

fig.update_geos(fitbounds="locations", visible=False)

st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# DISTRICT INSIGHTS
# -----------------------------
st.subheader("District Insights")

district = st.selectbox(
    "Select District",
    sorted(df["district"].dropna().unique())
)

row = df[df["district"] == district]

if not row.empty:
    row = row.iloc[0]

    # -------- Risk --------
    risk_df = pd.DataFrame({
        "Time": ["Present", "Near Future", "Far Future"],
        "Risk": [
            row.get(f"{prefix}_mean_present"),
            row.get(f"{prefix}_mean_near"),
            row.get(f"{prefix}_mean_far")
        ]
    })

    st.write("### Risk Values")
    st.dataframe(risk_df, use_container_width=True)

    # -------- Change --------
    change_df = pd.DataFrame({
        "Scenario": ["Near Change", "Far Change"],
        "Change (%)": [
            row.get(f"{prefix}_change_mean_near"),
            row.get(f"{prefix}_change_mean_far")
        ]
    })

    change_df["Change (%)"] = change_df["Change (%)"].fillna("Low baseline")

    st.write("### Change (%)")
    st.dataframe(change_df, use_container_width=True)

    # -------- H / E / V --------
    st.write("### Components & Contribution")

    if risk_type == "Population":
        exposure_val = row.get("exp_pop")
    else:
        exposure_val = row.get("exp_sys")

    haz = row.get(f"haz_{time}")
    exp = exposure_val
    vul = row.get("vul")

    hev_df = pd.DataFrame({
        "Component": ["Hazard", "Exposure", "Vulnerability"],
        "Value": [haz, exp, vul]
    })

    # Contribution
    if pd.notna(haz) and pd.notna(exp) and pd.notna(vul):
        total = haz + exp + vul

        if total != 0:
            hev_df["Contribution (%)"] = [
                haz / total * 100,
                exp / total * 100,
                vul / total * 100
            ]
        else:
            hev_df["Contribution (%)"] = 0
    else:
        hev_df["Contribution (%)"] = None

    hev_df["Value"] = hev_df["Value"].round(4)
    hev_df["Contribution (%)"] = hev_df["Contribution (%)"].round(2)

    st.dataframe(hev_df, use_container_width=True)

else:
    st.warning("No data available")
