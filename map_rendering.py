from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import plotly.graph_objects as go


RISK_BINS = [
    0, 0.05, 0.10, 0.20, 0.30,
    0.40, 0.50, 0.60, 0.70,
    0.80, 0.90, 1.000001,
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
    "0.90–1.00",
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
    "#2d0b00",
]
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
    np.inf,
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
    "> 400%",
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
    "#67000d",
]
NO_DATA_COLOR = "#d9d9d9"
MAP_HEIGHT = 650


def classify_map_data(
    dataframe: pd.DataFrame, column: str, map_type: str
) -> tuple[pd.DataFrame, list[str], dict[str, str]]:
    result = dataframe.copy()
    if map_type == "risk":
        labels, colors = RISK_LABELS, RISK_COLORS
        result["Map_Class"] = pd.cut(
            result[column],
            bins=RISK_BINS,
            labels=RISK_LABELS,
            include_lowest=True,
        ).astype(object)
    else:
        labels, colors = CHANGE_LABELS, CHANGE_COLORS
        result["Map_Class"] = pd.cut(
            result[column],
            bins=CHANGE_BINS,
            labels=CHANGE_LABELS,
            include_lowest=True,
            right=True,
        ).astype(object)
    result.loc[result[column].isna(), "Map_Class"] = "No Data"
    order = ["No Data"] + labels
    color_map = {"No Data": NO_DATA_COLOR, **dict(zip(labels, colors))}
    result["Map_Class"] = pd.Categorical(
        result["Map_Class"], categories=order, ordered=True
    )
    return result, order, color_map


def _outline_coordinates(
    outline: dict[str, Any],
) -> tuple[list[float | None], list[float | None]]:
    longitudes: list[float | None] = []
    latitudes: list[float | None] = []
    for feature in outline["features"]:
        geometry = feature["geometry"]
        if geometry["type"] == "Polygon":
            polygons = [geometry["coordinates"]]
        elif geometry["type"] == "MultiPolygon":
            polygons = geometry["coordinates"]
        else:
            continue
        for polygon in polygons:
            ring = polygon[0]
            longitudes.extend(point[0] for point in ring)
            latitudes.extend(point[1] for point in ring)
            longitudes.append(None)
            latitudes.append(None)
    return longitudes, latitudes


def create_map(
    dataframe: pd.DataFrame,
    column: str,
    map_type: str,
    districts: dict[str, Any],
    outline: dict[str, Any],
    style: dict[str, Any],
) -> tuple[go.Figure, pd.DataFrame]:
    map_data, category_order, color_map = classify_map_data(
        dataframe, column, map_type
    )
    populated_categories = [
        category
        for category in category_order
        if map_data["Map_Class"].eq(category).any()
    ]
    feature_key = style.get("join_key", "DIST_ID")
    feature_by_id = {
        int(feature["properties"][feature_key]): feature
        for feature in districts["features"]
    }
    district_ids = pd.to_numeric(map_data["DIST_ID"], errors="raise").astype(int)
    missing_ids = set(district_ids) - set(feature_by_id)
    if missing_ids:
        raise ValueError(
            f"District map geometry is missing IDs: {sorted(missing_ids)[:10]}"
        )
    values = pd.to_numeric(map_data[column], errors="coerce").to_numpy()
    figure = go.Figure()
    for category in populated_categories:
        selected = map_data["Map_Class"].eq(category).to_numpy()
        locations = district_ids.to_numpy()[selected]
        category_features = [
            feature_by_id[int(district_id)] for district_id in locations
        ]
        customdata = np.empty((int(selected.sum()), 3), dtype=object)
        customdata[:, 0] = map_data.loc[selected, "District"].fillna("").astype(str)
        customdata[:, 1] = map_data.loc[selected, "State"].fillna("").astype(str)
        customdata[:, 2] = values[selected]
        figure.add_trace(
            go.Choropleth(
                geojson={"type": "FeatureCollection", "features": category_features},
                locations=locations,
                z=np.zeros(len(locations), dtype=np.float64),
                zmin=0,
                zmax=1,
                colorscale=[[0, color_map[category]], [1, color_map[category]]],
                showscale=False,
                showlegend=True,
                name=category,
                featureidkey=f"properties.{feature_key}",
                customdata=customdata,
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>"
                    "State=%{customdata[1]}<br>"
                    f"{column}=%{{customdata[2]:.3f}}<extra></extra>"
                ),
                marker={
                    "line": {
                        "color": "#555555",
                        "width": style.get("district_width", 0.4),
                    },
                    "opacity": style.get("district_alpha", 0.9),
                },
            )
        )

    longitude, latitude = _outline_coordinates(outline)
    figure.add_trace(
        go.Scattergeo(
            lon=longitude,
            lat=latitude,
            mode="lines",
            line=dict(
                color="#222222",
                width=style.get("country_width", 1.2),
            ),
            hoverinfo="skip",
            showlegend=False,
        )
    )

    figure.update_geos(
        visible=False,
        lataxis_range=[6, 38],
        lonaxis_range=[67, 98],
        projection_type="mercator",
    )
    figure.update_layout(
        height=MAP_HEIGHT,
        margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(
            title="",
            orientation="h",
            yanchor="bottom",
            y=-0.15,
            xanchor="center",
            x=0.5,
        ),
        showlegend=True,
    )
    return figure, map_data
