import json
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

from map_rendering import create_map as create_optimized_map


# ============================================================
# CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Indian Monsoon LPS Risk Explorer",
    layout="wide"
)

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
TABLE_DIR = DATA_DIR / "tables"
MAP_DIR = DATA_DIR / "maps"
METRICS = DATA_DIR / "source" / "application_district_metrics.csv"
DISTRICTS = MAP_DIR / "districts.geojson"
INDIA_OUTLINE = MAP_DIR / "india_outline.geojson"
MAP_STYLE = MAP_DIR / "Map_Style.json"


# ============================================================
# LOAD DATA
# ============================================================

@st.cache_resource(show_spinner="Loading LPS risk data...")
def load_data():

    maxima = pd.read_parquet(TABLE_DIR / "district_maxima.parquet")
    changes = pd.read_parquet(TABLE_DIR / "district_risk_change.parquet")
    imd = pd.read_parquet(TABLE_DIR / "imd_regional_summary.parquet")
    master = pd.read_parquet(TABLE_DIR / "district_master.parquet")

    metrics = pd.read_csv(
        METRICS,
        usecols=["DIST_ID", "vul"]
    )

    # Original vulnerability values
    metrics["DIST_ID"] = pd.to_numeric(
        metrics["DIST_ID"], errors="coerce"
    ).astype("Int64")

    master["DIST_ID"] = pd.to_numeric(
        master["DIST_ID"], errors="coerce"
    ).astype("Int64")

    maxima["DIST_ID"] = pd.to_numeric(
        maxima["DIST_ID"], errors="coerce"
    ).astype("Int64")

    changes["DIST_ID"] = pd.to_numeric(
        changes["DIST_ID"], errors="coerce"
    ).astype("Int64")

    if metrics["DIST_ID"].duplicated().any():
        raise ValueError("Duplicate DIST_ID in vulnerability data.")

    # Merge original district vulnerability
    master = master.merge(
        metrics,
        on="DIST_ID",
        how="left",
        validate="one_to_one"
    )

    # Add vulnerability to maxima
    maxima = maxima.merge(
        master[["DIST_ID", "vul"]],
        on="DIST_ID",
        how="left",
        validate="many_to_one"
    )

    # GeoJSON
    with open(DISTRICTS, encoding="utf-8") as f:
        districts = json.load(f)

    with open(INDIA_OUTLINE, encoding="utf-8") as f:
        outline = json.load(f)

    with open(MAP_STYLE, encoding="utf-8") as f:
        style = json.load(f)

    return maxima, changes, imd, master, districts, outline, style


# Check required files
required = [
    METRICS,
    DISTRICTS,
    INDIA_OUTLINE,
    MAP_STYLE,
    TABLE_DIR / "district_maxima.parquet",
    TABLE_DIR / "district_risk_change.parquet",
    TABLE_DIR / "imd_regional_summary.parquet",
    TABLE_DIR / "district_master.parquet",
]

missing = [f.name for f in required if not f.exists()]

if missing:
    st.error("Missing files: " + ", ".join(missing))
    st.stop()


try:
    (
        maxima,
        changes,
        imd,
        master,
        districts,
        outline,
        style
    ) = load_data()

except Exception as e:
    st.error(f"Data loading error: {e}")
    st.stop()


# ============================================================
# MAP STYLE
# ============================================================

DISTRICT_WIDTH = style.get("district_width", 0.4)
DISTRICT_ALPHA = style.get("district_alpha", 0.9)
COUNTRY_WIDTH = style.get("country_width", 1.2)

# Interactive figure height
MAP_HEIGHT = 650


# ============================================================
# USER CONTROLS
# ============================================================

st.title("Indian Monsoon LPS Risk Explorer")

st.caption(
    "Spatial assessment of historical and future "
    "LPS-induced district risk across India"
)

col1, col2, col3 = st.columns([1, 1.5, 1.5])

with col1:

    metric_label = st.selectbox(
        "Risk indicator",
        [
            "Risk Maximum",
            "Risk Change (%)"
        ]
    )

with col2:

    if metric_label == "Risk Maximum":

        time_options = {
            "Epoch 1 (1979–2000)": "Epoch 1 (1979-2000)",
            "Epoch 2 (2001–2022)": "Epoch 2 (2001-2022)",
            "Historical (1979–2022)": "Historical (1979-2022)",
            "Near Future (2020–2049)": "Near future (2020-2049)",
            "Far Future (2079–2099)": "Far future (2079-2099)"
        }

    else:

        time_options = {
            "Epoch 2 vs Epoch 1":
                "Epoch 2 vs Epoch 1",

            "Near Future vs Historical":
                "Near future vs Historical (1979-2022)",

            "Far Future vs Historical":
                "Far future vs Historical (1979-2022)"
        }

    selected_time = st.selectbox(
        "Time Period",
        list(time_options.keys())
    )

    time_value = time_options[selected_time]


with col3:

    if metric_label == "Risk Maximum":

        scenario_options = [
            "Population",
            "Human system",
            "Future population (2100)"
        ]

    else:

        scenario_options = [
            "Population",
            "Human system",
            "Future population (2100) vs historical population"
        ]

    scenario = st.selectbox(
        "Exposure Scenario",
        scenario_options
    )


# ============================================================
# CONFIGURATION MAPPING
# ============================================================

def get_configuration(time_period, scenario):

    mapping = {

        ("Epoch 1 (1979-2000)", "Population"):
            "epoch1_population",

        ("Epoch 1 (1979-2000)", "Human system"):
            "epoch1_human_system",

        ("Epoch 2 (2001-2022)", "Population"):
            "epoch2_population",

        ("Epoch 2 (2001-2022)", "Human system"):
            "epoch2_human_system",

        ("Historical (1979-2022)", "Population"):
            "historical_population",

        ("Historical (1979-2022)", "Human system"):
            "historical_human_system",

        ("Near future (2020-2049)", "Population"):
            "near_future_population",

        ("Near future (2020-2049)", "Human system"):
            "near_future_human_system",

        ("Far future (2079-2099)", "Population"):
            "far_future_population",

        ("Far future (2079-2099)", "Human system"):
            "far_future_human_system",

        ("Far future (2079-2099)", "Future population (2100)"):
            "far_future_population_2100"
    }

    return mapping.get((time_period, scenario))


def get_change_comparison(time_period):

    mapping = {

        "Epoch 2 (2001-2022)":
            "Epoch 2 vs Epoch 1",

        "Near future (2020-2049)":
            "Near future vs Historical (1979-2022)",

        "Far future (2079-2099)":
            "Far future vs Historical (1979-2022)"
    }

    return mapping.get(time_period)


def get_change_scenario(scenario):

    if scenario == "Future population (2100)":
        return "Future population (2100) vs historical population"

    return scenario


# ============================================================
# DISCRETE CLASSIFICATION
# ============================================================

# Risk maximum: normalized risk (0–1)
RISK_BINS = [
    0, 0.05, 0.10, 0.20, 0.30,
    0.40, 0.50, 0.60, 0.70,
    0.80, 0.90, 1.000001
]

RISK_LABELS = [
    "0–0.05",
    "0.05–0.10",
    "0.10–0.20",
    "0.20–0.30",
    "0.30–0.40",
    "0.40–0.50",
    "0.50–0.60",
    "0.60–0.70",
    "0.70–0.80",
    "0.80–0.90",
    "0.90–1.00"
]

RISK_COLORS = [
    "#fff5eb",
    "#fee6ce",
    "#fdd0a2",
    "#fdae6b",
    "#fd8d3c",
    "#f16913",
    "#d94801",
    "#a63603",
    "#7f2704",
    "#4d1600",
    "#2d0b00"
]


# Risk change: negative blue, positive red
CHANGE_BINS = [
    -np.inf,
    -50,
    -25,
    -10,
    0,
    10,
    25,
    50,
    100,
    200,
    400,
    np.inf
]

CHANGE_LABELS = [
    "< -50%",
    "-50 to -25%",
    "-25 to -10%",
    "-10 to 0%",
    "0 to 10%",
    "10 to 25%",
    "25 to 50%",
    "50 to 100%",
    "100 to 200%",
    "200 to 400%",
    "> 400%"
]

CHANGE_COLORS = [
    "#08306b",
    "#2171b5",
    "#6baed6",
    "#c6dbef",
    "#f7f7f7",
    "#fee0d2",
    "#fc9272",
    "#fb6a4a",
    "#de2d26",
    "#a50f15",
    "#67000d"
]


def classify_risk(df, column):

    result = df.copy()

    result["Map_Class"] = pd.cut(
        result[column],
        bins=RISK_BINS,
        labels=RISK_LABELS,
        include_lowest=True
    )

    result["Map_Class"] = result[
        "Map_Class"
    ].astype(object)

    result.loc[
        result[column].isna(),
        "Map_Class"
    ] = "No Data"

    result["Map_Class"] = pd.Categorical(
        result["Map_Class"],
        categories=["No Data"] + RISK_LABELS,
        ordered=True
    )

    color_map = {
        "No Data": "#d9d9d9"
    }

    color_map.update(
        dict(zip(RISK_LABELS, RISK_COLORS))
    )

    return result, color_map, ["No Data"] + RISK_LABELS


def classify_change(df, column):

    result = df.copy()

    result["Map_Class"] = pd.cut(
        result[column],
        bins=CHANGE_BINS,
        labels=CHANGE_LABELS,
        include_lowest=True,
        right=True
    )

    result["Map_Class"] = result[
        "Map_Class"
    ].astype(object)

    result.loc[
        result[column].isna(),
        "Map_Class"
    ] = "No Data"

    result["Map_Class"] = pd.Categorical(
        result["Map_Class"],
        categories=["No Data"] + CHANGE_LABELS,
        ordered=True
    )

    color_map = {
        "No Data": "#d9d9d9"
    }

    color_map.update(
        dict(zip(CHANGE_LABELS, CHANGE_COLORS))
    )

    return result, color_map, ["No Data"] + CHANGE_LABELS


# ============================================================
# INDIA OUTLINE
# ============================================================

def add_india_outline(fig):

    for feature in outline["features"]:

        geometry = feature["geometry"]

        if geometry["type"] == "Polygon":

            polygons = [
                geometry["coordinates"]
            ]

        elif geometry["type"] == "MultiPolygon":

            polygons = geometry["coordinates"]

        else:
            continue

        for polygon in polygons:

            coords = polygon[0]

            lon = [p[0] for p in coords]
            lat = [p[1] for p in coords]

            fig.add_trace(
                go.Scattergeo(
                    lon=lon,
                    lat=lat,
                    mode="lines",
                    line=dict(
                        color="#222222",
                        width=COUNTRY_WIDTH
                    ),
                    hoverinfo="skip",
                    showlegend=False
                )
            )


# ============================================================
# MAP CREATION
# ============================================================

def create_map_legacy(df, column, map_type="risk"):

    if map_type == "risk":

        map_df, color_map, order = classify_risk(
            df, column
        )

    else:

        map_df, color_map, order = classify_change(
            df, column
        )

    fig = px.choropleth(

        map_df,

        geojson=districts,

        locations="DIST_ID",

        featureidkey=f"properties.{style.get('join_key', 'DIST_ID')}",

        color="Map_Class",

        category_orders={
            "Map_Class": order
        },

        color_discrete_map=color_map,

        hover_name="District",

        hover_data={
            "State": True,
            column: ":.3f",
            "Map_Class": False
        }
    )

    fig.update_traces(

        marker_line_color="#555555",

        marker_line_width=DISTRICT_WIDTH,

        marker_opacity=DISTRICT_ALPHA

    )

    # India outline remains visible on every map
    add_india_outline(fig)

    fig.update_geos(

        visible=False,

        lataxis_range=[6, 38],

        lonaxis_range=[67, 98],

        projection_type="mercator"

    )

    fig.update_layout(

        height=MAP_HEIGHT,

        margin=dict(
            l=0,
            r=0,
            t=10,
            b=0
        ),

        legend=dict(
            title="",
            orientation="h",
            yanchor="bottom",
            y=-0.15,
            xanchor="center",
            x=0.5
        ),

        showlegend=True

    )

    return fig, map_df


# ============================================================
# PREPARE MAIN MAP DATA
# ============================================================

selected_comparison = None
selected_change_scenario = None
selected_configuration = None

if metric_label == "Risk Maximum":

    selected_configuration = get_configuration(
        time_value,
        scenario
    )

    if selected_configuration is None:

        st.error("Invalid time period and exposure scenario.")
        st.stop()

    main_df = maxima[
        maxima["Configuration"] == selected_configuration
    ].copy()

    map_column = "Risk_Max_Normalized"

    map_type = "risk"

    legend_title = "Normalized Risk Maximum"

else:

    selected_comparison = time_value

    selected_change_scenario = get_change_scenario(
        scenario
    )

    main_df = changes[

        (changes["Comparison"] == selected_comparison)

        &

        (changes["Exposure_Scenario"] == selected_change_scenario)

    ].copy()

    map_column = "Risk_Change_Percent"

    map_type = "change"

    legend_title = "Risk Change (%)"


# ============================================================
# MAIN RESULT
# ============================================================

st.divider()

st.subheader(
    f"{metric_label} | {selected_time} | {scenario}"
)

main_fig, main_map_df = create_optimized_map(
    main_df,
    map_column,
    map_type,
    districts,
    outline,
    style,
)

st.plotly_chart(
    main_fig,
    use_container_width=True
)


# ============================================================
# DISTRICT SELECTION
# ============================================================

st.subheader("District-level results")

district_names = sorted(
    master["District"].dropna().unique()
)

selected_district = st.selectbox(
    "Select a district",
    district_names
)

district_info = master[
    master["District"] == selected_district
].iloc[0]

district_id = district_info["DIST_ID"]

district_vul = district_info["vul"]


# ============================================================
# GET DISTRICT HAZARD / EXPOSURE / RISK
# ============================================================

if metric_label == "Risk Maximum":

    selected_record = maxima[

        (maxima["DIST_ID"] == district_id)

        &

        (maxima["Configuration"] == selected_configuration)

    ]

    if not selected_record.empty:

        r = selected_record.iloc[0]

        hazard = r["Hazard_at_Normalized_Max"]

        exposure = r["Exposure_at_Normalized_Max"]

        normalized_risk = r["Risk_Max_Normalized"]

        raw_risk = r["Risk_Max_Raw"]

    else:

        hazard = exposure = normalized_risk = raw_risk = np.nan

    change_comparison = get_change_comparison(
        time_value
    )

    change_scenario = get_change_scenario(
        scenario
    )

    if change_comparison:

        selected_change = changes[

            (changes["DIST_ID"] == district_id)

            &

            (changes["Comparison"] == change_comparison)

            &

            (changes["Exposure_Scenario"] == change_scenario)

        ]

        risk_change = (
            selected_change.iloc[0]["Risk_Change_Percent"]
            if not selected_change.empty
            else np.nan
        )

    else:

        risk_change = np.nan

    table = pd.DataFrame({

        "Indicator": [

            "Hazard",

            "Exposure",

            "Vulnerability",

            "Normalized Risk Maximum",

            "Raw Risk Maximum",

            "Risk Change (%)"

        ],

        "Value": [

            hazard,

            exposure,

            district_vul,

            normalized_risk,

            raw_risk,

            risk_change

        ]

    })

else:

    selected_record = changes[

        (changes["DIST_ID"] == district_id)

        &

        (changes["Comparison"] == selected_comparison)

        &

        (changes["Exposure_Scenario"] == selected_change_scenario)

    ]

    if not selected_record.empty:

        r = selected_record.iloc[0]

        risk_change = r["Risk_Change_Percent"]

        baseline_risk = r["Baseline_Risk_Max_Raw"]

        comparison_risk = r["Comparison_Risk_Max_Raw"]

        config = r["Comparison_Configuration"]

        selected_maxima = maxima[

            (maxima["DIST_ID"] == district_id)

            &

            (maxima["Configuration"] == config)

        ]

        if not selected_maxima.empty:

            m = selected_maxima.iloc[0]

            hazard = m["Hazard_at_Normalized_Max"]

            exposure = m["Exposure_at_Normalized_Max"]

            normalized_risk = m["Risk_Max_Normalized"]

        else:

            hazard = exposure = normalized_risk = np.nan

    else:

        risk_change = baseline_risk = comparison_risk = np.nan

        hazard = exposure = normalized_risk = np.nan

    table = pd.DataFrame({

        "Indicator": [

            "Hazard (comparison period)",

            "Exposure (comparison period)",

            "Vulnerability",

            "Baseline Raw Risk Maximum",

            "Comparison Raw Risk Maximum",

            "Comparison Normalized Risk Maximum",

            "Risk Change (%)"

        ],

        "Value": [

            hazard,

            exposure,

            district_vul,

            baseline_risk,

            comparison_risk,

            normalized_risk,

            risk_change

        ]

    })


# ============================================================
# DISPLAY DISTRICT TABLE
# ============================================================

st.markdown(
    f"**{selected_district} — {district_info['State']}**"
)

table["Value"] = pd.to_numeric(
    table["Value"],
    errors="coerce"
).round(5)

st.dataframe(
    table,
    hide_index=True,
    use_container_width=True
)

st.caption(
    "Hazard and exposure are extracted at the grid cell of maximum "
    "normalized risk. Vulnerability is the original district-level "
    "'vul' value from application_district_metrics.csv."
)


# ============================================================
# IMD REGIONAL HOMOGENEOUS RISK CHANGE
# ============================================================

st.divider()

st.subheader(
    "IMD Homogeneous Regional Risk Change"
)

# Determine which risk-change comparison to use
# for the regional summary.

if metric_label == "Risk Change (%)":

    imd_comparison = selected_comparison

    imd_scenario = selected_change_scenario

else:

    imd_comparison = get_change_comparison(
        time_value
    )

    imd_scenario = get_change_scenario(
        scenario
    )


if imd_comparison is None:

    st.info(
        "No corresponding risk-change comparison is available "
        "for this baseline period. Select Epoch 2, Near Future "
        "or Far Future to view the associated regional change."
    )

else:

    # Select matching regional averages
    regional = imd[

        (imd["Comparison"] == imd_comparison)

        &

        (imd["Exposure_Scenario"] == imd_scenario)

    ].copy()

    # District-wise IMD region assignments
    district_changes = changes[

        (changes["Comparison"] == imd_comparison)

        &

        (changes["Exposure_Scenario"] == imd_scenario)

    ][

        ["DIST_ID", "District", "State", "IMD_Region"]

    ].copy()

    # Assign each district its IMD region mean
    regional_map = district_changes.merge(

        regional[
            [
                "IMD_Region",
                "Mean_Risk_Change_Percent"
            ]
        ],

        on="IMD_Region",

        how="left"

    )

    # Four homogeneous regional averages
    regional_table = regional[

        [
            "IMD_Region",
            "Mean_Risk_Change_Percent",
            "Median_Risk_Change_Percent",
            "Valid_District_Count"
        ]

    ].copy()

    regional_table = regional_table.rename(

        columns={

            "IMD_Region": "IMD Region",

            "Mean_Risk_Change_Percent":
                "Average Risk Change (%)",

            "Median_Risk_Change_Percent":
                "Median Risk Change (%)",

            "Valid_District_Count":
                "Valid Districts"

        }

    )

    regional_table = regional_table.round(2)

    regional_map = regional_map.rename(

        columns={

            "Mean_Risk_Change_Percent":
                "Average_Risk_Change"

        }

    )

    # Two equally sized columns
    map_col, table_col = st.columns(
        [1, 1]
    )

    with map_col:

        st.markdown("**Regional Average Risk Change Map**")

        regional_fig, _ = create_optimized_map(

            regional_map,

            "Average_Risk_Change",

            "change",
            districts,
            outline,
            style,

        )

        st.plotly_chart(

            regional_fig,

            use_container_width=True

        )

    with table_col:

        st.markdown("**IMD Regional Average Risk Change (%)**")

        st.dataframe(

            regional_table,

            hide_index=True,

            use_container_width=True,

            height=MAP_HEIGHT

        )

        st.caption(
            "Each district is assigned the mean risk change "
            "of its corresponding IMD homogeneous region."
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Indian Monsoon Low Pressure System (LPS) Risk Assessment | "
    "District-level hazard, exposure and vulnerability analysis"
)
