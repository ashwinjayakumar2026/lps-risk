import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px

# Load data
df = pd.read_csv("final_app_data.csv")
gdf = gpd.read_file("districts.geojson")

# Merge
gdf = gdf.merge(df, on="DIST_ID")

st.title("India Climate Risk Dashboard")

# Controls
risk_type = st.selectbox("Risk Type", ["Population", "System"])
time = st.selectbox("Time", ["present", "near", "far"])
agg = st.selectbox("Aggregation", ["mean", "p90", "max"])

# Column selection
prefix = "pop" if risk_type == "Population" else "sys"
col = f"{prefix}_{agg}_{time}"

# Map
fig = px.choropleth(
    gdf,
    geojson=gdf.geometry,
    locations=gdf.index,
    color=col,
    hover_name="district",
)

fig.update_geos(fitbounds="locations", visible=False)
st.plotly_chart(fig)

# District insights
district = st.selectbox("Select District", df["district"].dropna().unique())

row = df[df["district"] == district].iloc[0]

st.write("### Risk Values")
st.write(row[[f"{prefix}_mean_present",
              f"{prefix}_mean_near",
              f"{prefix}_mean_far"]])