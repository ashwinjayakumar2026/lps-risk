
import pandas as pd
import json

# Load GeoJSON directly
with open("districts_light.geojson") as f:
    geojson = json.load(f)

df = pd.read_csv("final_app_data.csv")

import folium
from streamlit_folium import st_folium

import streamlit as st

# UI controls
risk_type = st.selectbox("Risk Type", ["Population", "System"])
time = st.selectbox("Time", ["present", "near", "far"])
agg = st.selectbox("Aggregation", ["mean", "p90", "max"])

prefix = "pop" if risk_type == "Population" else "sys"
col = f"{prefix}_{agg}_{time}"
# Fill NaN
df[col] = df[col].fillna(0)

m = folium.Map(location=[22, 80], zoom_start=4, tiles="cartodbpositron")

folium.Choropleth(
    geo_data=geojson,
    data=df,
    columns=["DIST_ID", col],
    key_on="feature.properties.DIST_ID",
    fill_color="YlOrRd",
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name=col
).add_to(m)

st_folium(m, width=700, height=500)
