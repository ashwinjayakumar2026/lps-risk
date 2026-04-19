import streamlit as st
import pandas as pd
import json
import plotly.express as px

# -----------------------------
# LOAD DATA
# -----------------------------
with open("districts_final.geojson") as f:
    geojson = json.load(f)

df = pd.read_csv("final_app_data.csv")

# -----------------------------
# UI
# -----------------------------
st.title("India Monsoon LPS Risk Dashboard")

col1, col2, col3 = st.columns(3)

with col1:
    risk_type = st.selectbox("Risk Type", ["Population", "Human-System"])

with col2:
    time_label = st.selectbox("Time", ["Present", "Near Future", "Far Future"])

    time_map = {
        "Present": "present",
        "Near Future": "near",
        "Far Future": "far"
    }

time = time_map[time_label]

with col3:
    agg = st.selectbox("Aggregation", ["mean", "p90", "max"])

# -----------------------------
# COLUMN SELECTION
# -----------------------------
prefix = "pop" if risk_type == "Population" else "sys"
col = f"{prefix}_{agg}_{time}"

# -----------------------------
# CLASSIFICATION
# -----------------------------
bins = [0,0.01,0.02,0.03,0.04,0.05,0.06,0.07,0.08,0.09,0.10]
labels = [
    "0–0.01","0.01–0.02","0.02–0.03","0.03–0.04","0.04–0.05",
    "0.05–0.06","0.06–0.07","0.07–0.08","0.08–0.09","0.09–0.10"
]

df["class"] = pd.cut(df[col], bins=bins, labels=labels, include_lowest=True)

# Drop NaN classification (no "No Data" category)
df = df[df["class"].notna()]

# Force order
df["class"] = pd.Categorical(df["class"], categories=labels, ordered=True)

# -----------------------------
# COLOR SCALE (WHITE → RED ONLY)
# -----------------------------
colors = [
    "#ffffff",  # 0–0.01
    "#fee5d9",
    "#fcbba1",
    "#fc9272",
    "#fb6a4a",
    "#ef3b2c",
    "#cb181d",
    "#a50f15",
    "#67000d",
    "#3b0008"
]

# -----------------------------
# MAP
# -----------------------------
fig = px.choropleth(
    df,
    geojson=geojson,
    locations="DIST_ID",
    featureidkey="properties.DIST_ID",
    color="class",
    category_orders={"class": labels},
    color_discrete_sequence=colors,
    hover_name="district"
)

fig.update_geos(fitbounds="locations", visible=False)

st.plotly_chart(fig, use_container_width=True)

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

    # -------- Risk --------
    risk_df = pd.DataFrame({
        "Time": ["Present", "Near Future", "Far Future"],
        "Risk": [
            row.get(f"{prefix}_mean_present"),
            row.get(f"{prefix}_mean_near"),
            row.get(f"{prefix}_mean_far")
        ]
    })

    st.write("### Risk Values")
    st.dataframe(risk_df, use_container_width=True)

    # -------- Change --------
    change_df = pd.DataFrame({
        "Scenario": ["Near Change", "Far Change"],
        "Change (%)": [
            row.get(f"{prefix}_change_mean_near"),
            row.get(f"{prefix}_change_mean_far")
        ]
    })

    # Fill NaN safely for display
    change_df["Change (%)"] = change_df["Change (%)"].fillna("Low baseline")

    st.write("### Change (%)")
    st.dataframe(change_df, use_container_width=True)

    # -------- H / E / V --------
    st.write("### Components")

    if risk_type == "Population":
        exposure_val = row.get("exp_pop")
    else:
        exposure_val = row.get("exp_sys")

    hev_df = pd.DataFrame({
        "Component": ["Hazard", "Exposure", "Vulnerability"],
        "Value": [
            row.get(f"haz_{time}"),
            exposure_val,
            row.get("vul")
        ]
    })

    st.dataframe(hev_df, use_container_width=True)

    # -------- Contribution --------
    try:
        total = sum([v for v in hev_df["Value"] if pd.notna(v)])

        contrib_df = pd.DataFrame({
            "Component": ["Hazard", "Exposure", "Vulnerability"],
            "Contribution (%)": [
                hev_df["Value"][0] / total * 100,
                hev_df["Value"][1] / total * 100,
                hev_df["Value"][2] / total * 100
            ]
        })

        st.write("### Contribution (%)")
        st.dataframe(contrib_df.round(2), use_container_width=True)

    except:
        st.info("Contribution not available")

else:
    st.warning("No data available")
