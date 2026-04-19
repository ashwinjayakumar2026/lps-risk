
import pandas as pd
import json

# Load GeoJSON directly
with open("districts_light.geojson") as f:
    geojson = json.load(f)

df = pd.read_csv("final_app_data.csv")

import folium
from streamlit_folium import st_folium

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
