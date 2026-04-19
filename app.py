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
gdf["district"] = gdf["district_clean"].str.strip().str.lower()
df["district"] = df["district"].str.strip().str.lower()

# -----------------------------
# MERGE
# -----------------------------
gdf = gdf.merge(df, on="district", how="left")

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
# HANDLE NaN (IMPORTANT)
# -----------------------------
gdf[col] = gdf[col].fillna(0)

# -----------------------------
# GEOJSON (MORE STABLE)
# -----------------------------
geojson = json.loads(gdf.to_json())

gdf = gdf.reset_index(drop=True)
gdf["id"] = gdf.index.astype(str)

for i, feature in enumerate(geojson["features"]):
    feature["id"] = str(i)

# -----------------------------
# MAP
# -----------------------------
fig = px.choropleth(
    gdf,
    geojson=geojson,
    locations="id",
    color=col,
    hover_name="district",
    color_continuous_scale="YlOrRd"
)

fig.update_geos(fitbounds="locations", visible=False)

st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# DISTRICT INSIGHTS
# -----------------------------
st.subheader("District Insights")

district_list = sorted(df["district"].dropna().unique())
district = st.selectbox("Select District", district_list)

row = df[df["district"] == district]

if not row.empty:
    row = row.iloc[0]

    st.write("### Risk Values")
    st.write({
        "Present": row.get(f"{prefix}_mean_present"),
        "Near Future": row.get(f"{prefix}_mean_near"),
        "Far Future": row.get(f"{prefix}_mean_far")
    })
else:
    st.warning("No data available for this district")
