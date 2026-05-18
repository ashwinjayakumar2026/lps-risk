import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go

# -----------------------------
# LOAD DATA
# -----------------------------
with open("districts_full.geojson") as f:
    geojson = json.load(f)

with open("india_outline.geojson") as f:
    india_outline = json.load(f)

df = pd.read_csv("final_app_data.csv")

# -----------------------------
# UI
# -----------------------------
st.title("Indian Monsoon LPS Risk Dashboard")

col1, col2, col3 = st.columns(3)

with col1:
    risk_type = st.selectbox(
        "Risk Type",
        ["Population", "Human-System"]
    )

with col2:
    time_label = st.selectbox(
        "Time",
        ["Present", "Near Future", "Far Future"]
    )

with col3:
    agg = st.selectbox(
        "Aggregation",
        ["mean", "p90", "max"]
    )

# -----------------------------
# TIME MAP
# -----------------------------
time_map = {
    "Present": "present",
    "Near Future": "near",
    "Far Future": "far"
}

time = time_map[time_label]

# -----------------------------
# COLUMN SELECTION
# -----------------------------
prefix = "pop" if risk_type == "Population" else "sys"

col = f"{prefix}_{agg}_{time}"

# -----------------------------
# SAFETY CHECK
# -----------------------------
if col not in df.columns:
    st.error(f"{col} not found in dataset")
    st.stop()

# -----------------------------
# CLASSIFICATION
# -----------------------------
bins = [
    0, 0.01, 0.02, 0.03, 0.04, 0.05,
    0.06, 0.07, 0.08, 0.09, 0.10, 1
]

labels = [
    "0–0.01",
    "0.01–0.02",
    "0.02–0.03",
    "0.03–0.04",
    "0.04–0.05",
    "0.05–0.06",
    "0.06–0.07",
    "0.07–0.08",
    "0.08–0.09",
    "0.09–0.10",
    ">0.10"
]

df["class"] = pd.cut(
    df[col],
    bins=bins,
    labels=labels,
    include_lowest=True
)

# KEEP ALL DISTRICTS
df["class"] = df["class"].astype(object)

# NO DATA LABEL
df.loc[df[col].isna(), "class"] = "No Data"

# CATEGORY ORDER
category_order = ["No Data"] + labels

df["class"] = pd.Categorical(
    df["class"],
    categories=category_order,
    ordered=True
)

# -----------------------------
# COLOR SCALE
# -----------------------------
colors = [
    "#d3d3d3",  # No Data
    "#ffffff",
    "#fee5d9",
    "#fcbba1",
    "#fc9272",
    "#fb6a4a",
    "#ef3b2c",
    "#e31a1c",
    "#cb181d",
    "#a50f15",
    "#800026",
    "#67000d"
]

# -----------------------------
# CREATE DISCRETE COLOR MAP
# -----------------------------
color_map = dict(zip(category_order, colors))

# -----------------------------
# MAIN DISTRICT MAP
# -----------------------------
fig = px.choropleth(
    df,
    geojson=geojson,
    locations="DIST_ID",
    featureidkey="properties.DIST_ID",
    color="class",
    category_orders={"class": category_order},
    color_discrete_map=color_map,
    hover_name="district"
)

# -----------------------------
# DISTRICT BOUNDARY STYLING
# -----------------------------
fig.update_traces(
    marker_line_color="#4a4a4a",
    marker_line_width=0.7
)

# -----------------------------
# ADD INDIA OUTLINE
# -----------------------------
for feature in india_outline["features"]:

    geometry = feature["geometry"]

    if geometry["type"] == "Polygon":

        coords = geometry["coordinates"][0]

        lon = [c[0] for c in coords]
        lat = [c[1] for c in coords]

        fig.add_trace(
            go.Scattergeo(
                lon=lon,
                lat=lat,
                mode="lines",
                line=dict(
                    color="black",
                    width=2
                ),
                hoverinfo="skip",
                showlegend=False
            )
        )

    elif geometry["type"] == "MultiPolygon":

        for polygon in geometry["coordinates"]:

            coords = polygon[0]

            lon = [c[0] for c in coords]
            lat = [c[1] for c in coords]

            fig.add_trace(
                go.Scattergeo(
                    lon=lon,
                    lat=lat,
                    mode="lines",
                    line=dict(
                        color="black",
                        width=2
                    ),
                    hoverinfo="skip",
                    showlegend=False
                )
            )

# -----------------------------
# MAP LAYOUT
# -----------------------------
fig.update_geos(
    visible=False,
    lataxis_range=[6, 38],
    lonaxis_range=[67, 98],
    projection_type="mercator"
)

fig.update_layout(
    margin=dict(l=0, r=0, t=0, b=0),
    height=700
)

# -----------------------------
# DISPLAY MAP
# -----------------------------
st.plotly_chart(
    fig,
    use_container_width=True
)

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

    # -----------------------------
    # RISK VALUES
    # -----------------------------
    risk_df = pd.DataFrame({
        "Time": [
            "Present",
            "Near Future",
            "Far Future"
        ],
        "Risk": [
            row.get(f"{prefix}_mean_present"),
            row.get(f"{prefix}_mean_near"),
            row.get(f"{prefix}_mean_far")
        ]
    })

    st.write("### Risk Values")

    st.dataframe(
        risk_df,
        use_container_width=True
    )

    # -----------------------------
    # CHANGE VALUES
    # -----------------------------
    change_df = pd.DataFrame({
        "Scenario": [
            "Near Change",
            "Far Change"
        ],
        "Change (%)": [
            row.get(f"{prefix}_change_mean_near"),
            row.get(f"{prefix}_change_mean_far")
        ]
    })

    change_df["Change (%)"] = (
        change_df["Change (%)"]
        .fillna("Low baseline")
    )

    st.write("### Change (%)")

    st.dataframe(
        change_df,
        use_container_width=True
    )

    # -----------------------------
    # H / E / V COMPONENTS
    # -----------------------------
    st.write("### Components & Contribution")

    if risk_type == "Population":
        exposure_val = row.get("exp_pop")
    else:
        exposure_val = row.get("exp_sys")

    haz = row.get(f"haz_{time}")
    exp = exposure_val
    vul = row.get("vul")

    hev_df = pd.DataFrame({
        "Component": [
            "Hazard",
            "Exposure",
            "Vulnerability"
        ],
        "Value": [
            haz,
            exp,
            vul
        ]
    })

    # -----------------------------
    # CONTRIBUTION
    # -----------------------------
    if (
        pd.notna(haz)
        and pd.notna(exp)
        and pd.notna(vul)
    ):

        total = haz + exp + vul

        if total != 0:

            hev_df["Contribution (%)"] = [
                haz / total * 100,
                exp / total * 100,
                vul / total * 100
            ]

        else:

            hev_df["Contribution (%)"] = 0

    else:

        hev_df["Contribution (%)"] = None

    hev_df["Value"] = hev_df["Value"].round(4)

    hev_df["Contribution (%)"] = (
        hev_df["Contribution (%)"]
        .round(2)
    )

    st.dataframe(
        hev_df,
        use_container_width=True
    )

else:

    st.warning("No data available")
