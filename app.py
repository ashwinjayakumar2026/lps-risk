import streamlit as st
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

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

# -----------------------------
# MAP (MATPLOTLIB)
# -----------------------------
st.subheader("Risk Map")

fig, ax = plt.subplots(figsize=(10, 12))

gdf.plot(
    column=col,
    cmap="viridis",
    linewidth=0.3,
    edgecolor="black",
    ax=ax,
    legend=True,
    missing_kwds={
        "color": "lightgrey",
        "label": "No data"
    }
)

ax.set_title(f"{risk_type} Risk ({agg} - {time})", fontsize=14)
ax.axis("off")

st.pyplot(fig)

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
