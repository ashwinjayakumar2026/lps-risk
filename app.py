import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
import json

# -----------------------------
# LOAD DATA
# -----------------------------
df = pd.read_csv("final_app_data.csv")
gdf = gpd.read_file("districts_light.geojson")

# -----------------------------
# CLEAN NAMES
# -----------------------------
df["district"] = df["district"].str.lower().str.strip()
gdf["district"] = gdf["district_clean"].str.lower().str.strip()

# -----------------------------
# MERGE
# -----------------------------
gdf = gdf.merge(df, on="district", how="left")

# -----------------------------
# FIX GEOMETRY (IMPORTANT)
# -----------------------------
gdf = gdf.explode(index_parts=False)
gdf = gdf.reset_index(drop=True)

# -----------------------------
# CREATE GEOJSON WITH IDS
# -----------------------------
geojson = json.loads(gdf.to_json())

for i, feature in enumerate(geojson["features"]):
    feature["id"] = str(i)

gdf["id"] = gdf.index.astype(str)

# -----------------------------
# STREAMLIT UI
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
    hover_name="district",
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

    st.write("### Risk Values")
    st.write({
        "Present": row[f"{prefix}_mean_present"],
        "Near Future": row[f"{prefix}_mean_near"],
        "Far Future": row[f"{prefix}_mean_far"]
    })

    st.write("### Change (%)")
    st.write({
        "Near Change": row.get(f"{prefix}_change_mean_near", None),
        "Far Change": row.get(f"{prefix}_change_mean_far", None)
    })
else:
    st.warning("No data available for this district")
