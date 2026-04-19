import folium
from streamlit_folium import st_folium

# Convert to GeoJSON dict
geojson = gdf.to_json()

# Handle NaN (important for visualization)
gdf[col] = gdf[col].fillna(0)

# Create map
m = folium.Map(location=[22, 80], zoom_start=4, tiles="cartodbpositron")

# Choropleth
folium.Choropleth(
    geo_data=geojson,
    data=gdf,
    columns=["DIST_ID", col],
    key_on="feature.properties.DIST_ID",
    fill_color="YlOrRd",
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name=col
).add_to(m)

# 🔥 ADD TOOLTIP (IMPORTANT)
folium.GeoJson(
    geojson,
    tooltip=folium.GeoJsonTooltip(
        fields=["district_clean"],
        aliases=["District:"],
        localize=True
    )
).add_to(m)

# Render
st_folium(m, width=700, height=500)
