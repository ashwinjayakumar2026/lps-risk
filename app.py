import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
import json

# -----------------------------
# LOAD DATA
# -----------------------------
df = pd.read_csv("final_app_data.csv")
gdf = gpd.read_file("districts_final.geojson")

# -----------------------------
# MERGE USING DIST_ID (PERFECT MATCH)
# -----------------------------
gdf = gdf.merge(df, on="DIST_ID", how="left")

# -----------------------------
# GEOJSON WITH IDS
# -----------------------------
geojson = json.loads(gdf.to_json())

gdf["id"] = gdf["DIST_ID"].astype(str)

for feature in geojson["features"]:
    feature["id"] = str(feature["properties"]["DIST_ID"])

# -----------------------------
# UI
# -----------------------------
st.title("India Monsoon LPS Risk Dashboard")

risk_type = st.selectbox("Risk Type", ["Population", "System"])
time = st.selectbox("Time", ["present", "near", "far"])
agg = st.selectbox("Aggregation", ["mean", "p90", "max"])

prefix = "pop" if risk_type == "Population" else "sys"
col = f"{prefix}_{agg}_{time}"

# -----------------------------
# MAP
# -----------------------------
fig = px.choropleth(
    gdf,
    geojson=geojson,
    locations="id",
    color=col,
    hover_name="district_clean"
)

fig.update_geos(fitbounds="locations", visible=False)
st.plotly_chart(fig, width="stretch")

# -----------------------------
# INSIGHTS
# -----------------------------
st.subheader("District Insights")

district = st.selectbox(
    "Select District",
    sorted(gdf["district_clean"].dropna().unique())
)

row = gdf[gdf["district_clean"] == district]

if not row.empty:
    row = row.iloc[0]

    st.write("### Risk Values")
    st.write({
        "Present": row[f"{prefix}_mean_present"],
        "Near Future": row[f"{prefix}_mean_near"],
        "Far Future": row[f"{prefix}_mean_far"]
    })
