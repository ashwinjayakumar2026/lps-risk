import streamlit as st
import pandas as pd
import geopandas as gpd


# -----------------------------
# LOAD DATA
# -----------------------------
df = pd.read_csv("final_app_data.csv")
gdf = gpd.read_file("districts_final.geojson")

# -----------------------------
# MERGE USING DIST_ID (IMPORTANT)
# -----------------------------
gdf = gdf.merge(df, on="DIST_ID", how="left")

# -----------------------------
# STREAMLIT UI
# -----------------------------
st.title("India Monsoon LPS Risk Dashboard")

# Controls
risk_type = st.selectbox("Risk Type", ["Population", "System"])
time = st.selectbox("Time", ["present", "near", "far"])
agg = st.selectbox("Aggregation", ["mean", "p90", "max"])

prefix = "pop" if risk_type == "Population" else "sys"
col = f"{prefix}_{agg}_{time}"

import folium
from streamlit_folium import st_folium

# Create map
m = folium.Map(location=[22, 80], zoom_start=4)

# Add GeoJSON
folium.Choropleth(
    geo_data=gdf,
    data=gdf,
    columns=["DIST_ID", col],
    key_on="feature.properties.DIST_ID",
    fill_color="YlOrRd",
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name=col
).add_to(m)

st_data = st_folium(m, width=700, height=500)
# -----------------------------
# DISTRICT INSIGHTS
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
        "Present": row.get(f"{prefix}_mean_present"),
        "Near Future": row.get(f"{prefix}_mean_near"),
        "Far Future": row.get(f"{prefix}_mean_far")
    })

    st.write("### Change (%)")
    st.write({
        "Near Change": row.get(f"{prefix}_change_mean_near"),
        "Far Change": row.get(f"{prefix}_change_mean_far")
    })
else:
    st.warning("No data available for this district")
