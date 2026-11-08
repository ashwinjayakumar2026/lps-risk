import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


# ------------------------------------------------------------
# INDIAN MONSOON LPS RISK EXPLORER
#
# Required files:
#   app.py
#   requirements.txt
#   LPS_Risk_Explorer_Results_20261108T183932Z.xlsx
#   application_district_metrics.csv
#   districts_full.geojson
#
# Vulnerability source:
#   application_district_metrics.csv -> vul
#
# PCA vulnerability is NOT used.
# ------------------------------------------------------------

st.set_page_config(
    page_title="Indian Monsoon LPS Risk Explorer",
    layout="wide",
)

st.title("Indian Monsoon LPS Risk Explorer")
st.caption("District-level LPS risk maxima, risk change and vulnerability")

ROOT = Path(__file__).resolve().parent

XLSX = ROOT / "LPS_Risk_Explorer_Results_20261108T183932Z.xlsx"
METRICS = ROOT / "application_district_metrics.csv"
GEOJSON = ROOT / "districts_full.geojson"


# ============================================================
# LOAD DATA
# ============================================================

@st.cache_data(show_spinner="Loading district data...")
def load_inputs():

    maxima = pd.read_excel(
        XLSX,
        sheet_name="District Maxima"
    )

    changes = pd.read_excel(
        XLSX,
        sheet_name="District Risk Change"
    )

    master = pd.read_excel(
        XLSX,
        sheet_name="District Master"
    )

    # Original district vulnerability values
    metrics = pd.read_csv(
        METRICS,
        usecols=["DIST_ID", "vul"]
    )

    metrics["DIST_ID"] = pd.to_numeric(
        metrics["DIST_ID"],
        errors="coerce"
    ).astype("Int64")

    metrics = metrics.dropna(
        subset=["DIST_ID"]
    )

    if metrics["DIST_ID"].duplicated().any():
        raise ValueError(
            "Duplicate DIST_ID values in application_district_metrics.csv"
        )

    # Standardize district IDs
    master["DIST_ID"] = pd.to_numeric(
        master["DIST_ID"],
        errors="coerce"
    ).astype("Int64")

    maxima["DIST_ID"] = pd.to_numeric(
        maxima["DIST_ID"],
        errors="coerce"
    ).astype("Int64")

    changes["DIST_ID"] = pd.to_numeric(
        changes["DIST_ID"],
        errors="coerce"
    ).astype("Int64")

    # Merge original vulnerability
    master = master.merge(
        metrics[["DIST_ID", "vul"]],
        on="DIST_ID",
        how="left",
        validate="one_to_one"
    )

    # Load district boundaries
    with open(GEOJSON, "r", encoding="utf-8") as f:
        geojson = json.load(f)

    # Ensure GeoJSON IDs are numeric
    for feature in geojson.get("features", []):

        props = feature.get("properties", {})

        if props.get("DIST_ID") is not None:

            try:
                props["DIST_ID"] = int(
                    props["DIST_ID"]
                )

            except (TypeError, ValueError):
                pass

    # Attach original vulnerability to other datasets
    maxima = maxima.merge(
        master[["DIST_ID", "vul"]],
        on="DIST_ID",
        how="left",
        validate="many_to_one"
    )

    changes = changes.merge(
        master[["DIST_ID", "vul"]],
        on="DIST_ID",
        how="left",
        validate="many_to_one"
    )

    return maxima, changes, master, geojson


# ============================================================
# CHECK FILES AND LOAD
# ============================================================

required_files = [
    XLSX,
    METRICS,
    GEOJSON
]

missing = [
    p.name for p in required_files
    if not p.exists()
]

if missing:

    st.error(
        "Missing required files: "
        + ", ".join(missing)
    )

    st.stop()


try:

    maxima, changes, master, geojson = load_inputs()

except Exception as exc:

    st.error(
        f"Data loading failed: {exc}"
    )

    st.stop()


# ============================================================
# SIDEBAR CONTROLS
# ============================================================

st.sidebar.header("Map Controls")

layer = st.sidebar.radio(
    "Explore",
    [
        "Risk maxima",
        "Risk change",
        "Vulnerability"
    ]
)


# ============================================================
# RISK MAXIMA
# ============================================================

if layer == "Risk maxima":

    config_labels = {

        "Historical (1979–2022) | Population":
            "historical_population",

        "Historical (1979–2022) | Human system":
            "historical_human_system",

        "Epoch 1 (1979–2000) | Population":
            "epoch1_population",

        "Epoch 1 (1979–2000) | Human system":
            "epoch1_human_system",

        "Epoch 2 (2001–2022) | Population":
            "epoch2_population",

        "Epoch 2 (2001–2022) | Human system":
            "epoch2_human_system",

        "Near future (2020–2049) | Population":
            "near_future_population",

        "Near future (2020–2049) | Human system":
            "near_future_human_system",

        "Far future (2079–2099) | Population":
            "far_future_population",

        "Far future (2079–2099) | Human system":
            "far_future_human_system",

        "Far future | Future population (2100)":
            "far_future_population_2100"
    }

    chosen_label = st.sidebar.selectbox(
        "Period and exposure scenario",
        list(config_labels)
    )

    chosen_config = config_labels[
        chosen_label
    ]

    variable_labels = {

        "Normalized risk maximum":
            "Risk_Max_Normalized",

        "Raw risk maximum":
            "Risk_Max_Raw",

        "Hazard at normalized-risk maximum":
            "Hazard_at_Normalized_Max",

        "Exposure at normalized-risk maximum":
            "Exposure_at_Normalized_Max",

        "District vulnerability (original vul)":
            "vul"
    }

    variable_label = st.sidebar.selectbox(
        "Variable",
        list(variable_labels)
    )

    value_col = variable_labels[
        variable_label
    ]

    plot_df = maxima[
        maxima["Configuration"] == chosen_config
    ].copy()

    if value_col == "vul":

        plot_df = master.copy()

    else:

        plot_df = plot_df.merge(
            master[
                ["DIST_ID", "District", "State"]
            ],
            on="DIST_ID",
            how="left",
            suffixes=("", "_master")
        )

        if "District_master" in plot_df.columns:

            plot_df["District"] = (
                plot_df["District"].fillna(
                    plot_df["District_master"]
                )
            )

        if "State_master" in plot_df.columns:

            plot_df["State"] = (
                plot_df["State"].fillna(
                    plot_df["State_master"]
                )
            )

    legend = variable_label


# ============================================================
# RISK CHANGE
# ============================================================

elif layer == "Risk change":

    comparison_options = sorted(
        changes["Comparison"].dropna().unique()
    )

    chosen_comparison = st.sidebar.selectbox(
        "Comparison",
        comparison_options
    )

    scenario_options = sorted(
        changes.loc[
            changes["Comparison"] == chosen_comparison,
            "Exposure_Scenario"
        ].dropna().unique()
    )

    chosen_scenario = st.sidebar.selectbox(
        "Exposure scenario",
        scenario_options
    )

    plot_df = changes[
        (changes["Comparison"] == chosen_comparison)
        &
        (changes["Exposure_Scenario"] == chosen_scenario)
    ].copy()

    value_col = "Risk_Change_Percent"

    legend = "Risk change (%)"


# ============================================================
# VULNERABILITY
# ============================================================

else:

    plot_df = master.copy()

    value_col = "vul"

    legend = "District vulnerability (original vul)"


# ============================================================
# STATE FILTER
# ============================================================

state_options = (
    ["All India"]
    +
    sorted(master["State"].dropna().unique())
)

chosen_state = st.sidebar.selectbox(
    "State",
    state_options
)

if chosen_state != "All India":

    plot_df = plot_df[
        plot_df["State"] == chosen_state
    ].copy()


plot_df = plot_df.drop_duplicates(
    "DIST_ID"
).copy()

plot_df[value_col] = pd.to_numeric(
    plot_df[value_col],
    errors="coerce"
)


# ============================================================
# SUMMARY METRICS
# ============================================================

valid = plot_df[value_col].notna()

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "Districts displayed",
    f"{len(plot_df):,}"
)

c2.metric(
    "Valid values",
    f"{int(valid.sum()):,}"
)

c3.metric(
    "Missing values",
    f"{int((~valid).sum()):,}"
)

c4.metric(
    "Mean",
    "—" if not valid.any()
    else f"{plot_df.loc[valid, value_col].mean():.4f}"
)


# ============================================================
# INDIA DISTRICT MAP
# ============================================================

fig = px.choropleth(

    plot_df,

    geojson=geojson,

    locations="DIST_ID",

    featureidkey="properties.DIST_ID",

    color=value_col,

    color_continuous_scale="YlOrRd",

    hover_name="District",

    hover_data={
        "DIST_ID": True,
        "State": True,
        value_col: ":.5f"
    },

    labels={
        value_col: legend
    }
)


fig.update_traces(

    marker_line_color="#555555",

    marker_line_width=0.45

)


fig.update_geos(

    visible=False,

    lataxis_range=[6, 38],

    lonaxis_range=[67, 98],

    projection_type="mercator"

)


fig.update_layout(

    height=650,

    margin=dict(
        l=0,
        r=0,
        t=10,
        b=0
    ),

    coloraxis_colorbar=dict(
        title=legend
    )

)


st.plotly_chart(
    fig,
    use_container_width=True
)


# ============================================================
# DISTRICT INSIGHTS
# ============================================================

st.subheader("District Insights")

district_names = sorted(
    master["District"].dropna().unique()
)

selected_district = st.selectbox(
    "Select District",
    district_names
)


drow = master.loc[
    master["District"] == selected_district
].iloc[0]


district_id = drow["DIST_ID"]


a, b, c = st.columns(3)


a.metric(
    "District",
    str(drow["District"])
)

b.metric(
    "State",
    str(drow["State"])
)

c.metric(
    "Vulnerability (original vul)",

    "No data"
    if pd.isna(drow["vul"])
    else f"{float(drow['vul']):.5f}"
)


# ============================================================
# DISTRICT RISK MAXIMA DETAILS
# ============================================================

if layer == "Risk maxima":

    selected = maxima[

        (maxima["DIST_ID"] == district_id)

        &

        (maxima["Configuration"] == chosen_config)

    ]

    if not selected.empty:

        r = selected.iloc[0]

        st.markdown(
            "**Risk maximum and components**"
        )

        details = pd.DataFrame({

            "Component / metric": [

                "Normalized risk maximum",

                "Raw risk maximum",

                "Hazard at normalized-risk maximum",

                "Exposure at normalized-risk maximum",

                "District vulnerability (original vul)"

            ],

            "Value": [

                r.get("Risk_Max_Normalized"),

                r.get("Risk_Max_Raw"),

                r.get("Hazard_at_Normalized_Max"),

                r.get("Exposure_at_Normalized_Max"),

                drow["vul"]

            ]

        })

        details["Value"] = pd.to_numeric(
            details["Value"],
            errors="coerce"
        ).round(6)

        st.dataframe(
            details,
            hide_index=True,
            use_container_width=True
        )

        st.caption(
            "District vulnerability is sourced from "
            "application_district_metrics.csv, column 'vul'. "
            "The workbook PCA vulnerability fields are not used."
        )


# ============================================================
# DISTRICT RISK CHANGE DETAILS
# ============================================================

elif layer == "Risk change":

    selected = changes[

        (changes["DIST_ID"] == district_id)

        &

        (changes["Comparison"] == chosen_comparison)

        &

        (changes["Exposure_Scenario"] == chosen_scenario)

    ]

    if not selected.empty:

        r = selected.iloc[0]

        st.markdown(
            "**Risk-change result**"
        )

        st.write({

            "Comparison":
                chosen_comparison,

            "Exposure scenario":
                chosen_scenario,

            "Risk change (%)":

                None
                if pd.isna(r["Risk_Change_Percent"])

                else round(
                    float(r["Risk_Change_Percent"]),
                    3
                ),

            "Baseline eligible":
                r.get("Baseline_Eligible")

        })


# ============================================================
# VULNERABILITY DETAILS
# ============================================================

else:

    st.caption(
        "This map uses the original district-level vulnerability "
        "values from application_district_metrics.csv, column 'vul'."
    )


# ============================================================
# DATA TABLE AND DOWNLOAD
# ============================================================

with st.expander("View District Data"):

    st.dataframe(

        plot_df.sort_values("District"),

        hide_index=True,

        use_container_width=True

    )

    st.download_button(

        "Download displayed data (CSV)",

        plot_df.to_csv(
            index=False
        ).encode("utf-8"),

        file_name="lps_risk_explorer_view.csv",

        mime="text/csv"

    )


# ============================================================
# FOOTER
# ============================================================

st.caption(

    "Sources: LPS_Risk_Explorer_Results_20261108T183932Z.xlsx; "
    "application_district_metrics.csv. "
    "Vulnerability uses the original 'vul' column."

)
