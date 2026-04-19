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
st.title("India Monsoon LPS Risk Dashboard")

col1, col2, col3, col4 = st.columns(4)

with col1:
    risk_type = st.selectbox("Risk Type", ["Population", "System"])

with col2:
    time = st.selectbox("Time", ["present", "near", "far"])

with col3:
    agg = st.selectbox("Aggregation", ["mean", "p90", "max"])

with col4:
    view = st.selectbox("View", ["Absolute", "Normalized"])

# -----------------------------
# COLUMN SELECTION
# -----------------------------
prefix = "pop" if risk_type == "Population" else "sys"
col = f"{prefix}_{agg}_{time}"

# -----------------------------
# NORMALIZATION (ONLY FOR VIEW)
# -----------------------------
if view == "Normalized":
    df[f"{col}_norm"] = (
        df[col] - df[col].min()
    ) / (df[col].max() - df[col].min())

    plot_col = f"{col}_norm"
else:
    plot_col = col

import numpy as np

bins = [0,0.01,0.02,0.03,0.04,0.05,0.06,0.07,0.08,0.09,0.10]
labels = [
    "0–0.01","0.01–0.02","0.02–0.03","0.03–0.04","0.04–0.05",
    "0.05–0.06","0.06–0.07","0.07–0.08","0.08–0.09","0.09–0.10"
]

df["class"] = pd.cut(df[plot_col], bins=bins, labels=labels, include_lowest=True)

# Handle NaN
df["class"] = df["class"].astype(object)
df.loc[df[plot_col].isna(), "class"] = "No Data"

# 🔥 FORCE ORDER
category_order = ["No Data"] + labels
df["class"] = pd.Categorical(df["class"], categories=category_order, ordered=True)

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
    color_discrete_sequence=["#ffffff"] + px.colors.sequential.YlOrRd,
    hover_name="district"
)

fig.update_geos(fitbounds="locations", visible=False)

st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# DISTRICT INSIGHTS
# -----------------------------
st.subheader("District Insights")

district = st.selectbox("Select District", sorted(df["district"].dropna().unique()))

row = df[df["district"] == district]

if not row.empty:
    row = row.iloc[0]

    # -------- Risk Table --------
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

    # -------- Change Table --------
    change_df = pd.DataFrame({
        "Scenario": ["Near Change", "Far Change"],
        "Change (%)": [
            row.get(f"{prefix}_change_mean_near"),
            row.get(f"{prefix}_change_mean_far")
        ]
    })

    st.write("### Change (%)")
    st.dataframe(change_df, use_container_width=True)

else:
    st.warning("No data available")
