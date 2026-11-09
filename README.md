# Indian Monsoon LPS Risk Explorer

## Overview

The **Indian Monsoon LPS Risk Explorer** is an interactive geospatial dashboard developed to explore district-level climate risk associated with Indian Monsoon Low Pressure Systems (LPS) across India.

The dashboard integrates hazard, exposure and vulnerability information to examine the spatial distribution of risk, compare historical and future scenarios, and investigate changes in district-level risk over time.

## Features

- Interactive district-level risk maps across India.
- Historical and future risk assessment.
- Risk-change comparisons between historical and future periods.
- Population and human-system exposure scenarios.
- Future population scenario using projected 2100 population.
- District-level hazard, exposure, vulnerability and risk results.
- IMD homogeneous regional risk-change maps and summary tables.

## Temporal Framework

The dashboard covers the following assessment periods:

| Period | Years |
|---|---|
| Epoch 1 | 1979–2000 |
| Epoch 2 | 2001–2022 |
| Historical | 1979–2022 |
| Near Future | 2020–2049 |
| Far Future | 2079–2099 |

### Risk Change Comparisons

- Epoch 2 vs Epoch 1
- Near Future vs scenario-specific Present
- Far Future vs scenario-specific Present

Future comparisons use the present-risk baseline and eligibility mask for the
selected exposure scenario. Historical equal-exposure epoch maxima are
zero-filled and normalized by epoch; their changes follow the research
workflow's zero-fill and ±150% clipping rules.

## Risk Assessment Framework

Risk is conceptualised through the integration of three components:

**Risk = Hazard × Exposure × Vulnerability**

### Hazard

LPS-associated rainfall extremes represented using selected ETCCDI-based rainfall indices.

### Exposure

The dashboard includes two principal exposure representations:

- **Population:** Population-based exposure.
- **Human System:** Exposure representing population, built-up areas and cropland.

A future population scenario based on projected 2100 population is also included.

### Vulnerability

District-level socio-economic vulnerability represented using the original district vulnerability values incorporated into the application dataset.

## Risk Indicators

The dashboard provides two principal indicators:

- **Risk Maximum:** District-level maximum risk values, including normalised and raw risk.
- **Risk Change (%):** Percentage change in risk relative to the corresponding baseline period.

The district-level results table presents hazard, exposure, vulnerability and relevant risk indicators for the selected district.

## IMD Homogeneous Regional Analysis

The dashboard additionally provides risk-change summaries across the four IMD homogeneous rainfall regions of India.

The regional analysis includes:

- Spatial representation of regional average risk change.
- Regional mean and median risk-change values.
- Number of valid districts contributing to each regional summary.

## Technology Stack

- Python
- Streamlit
- Pandas
- NumPy
- Plotly
- PyArrow

## Repository Structure

```text
LPS_Risk_Explorer/
│
├── app.py
├── map_rendering.py
├── prepare_data.py
├── requirements.txt
├── README.md
│
└── data/
    ├── source/
    ├── tables/
    └── maps/
```

## Installation and Execution

### 1. Clone the repository

```bash
git clone <YOUR-GITHUB-REPOSITORY-URL>
cd LPS_Risk_Explorer
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the dashboard

```bash
streamlit run app.py
```

The dashboard will open in your default web browser.

### Regenerate the dashboard tables

After rebuilding the corrected pipeline workbook, run:

```bash
python prepare_data.py --workbook "<path-to-LPS_Risk_Explorer_Results.xlsx>"
```

Without `--workbook`, the script rebuilds from the existing district maxima.
It uses `data/source/district_present_risk_baselines.csv`, derived from the
original scenario-specific present-risk arrays, to rebuild district changes
and IMD summaries. It does not rebuild maps or change the vulnerability CSV.

## Data

The application uses prepared district-level risk datasets and supporting geospatial files derived from the underlying research.

The `data/` directory contains the processed tables, district vulnerability data and map geometries required to run the dashboard.

## Research Context

This dashboard accompanies a research assessment of compound climate risk associated with Indian Monsoon Low Pressure Systems. It is intended to support the exploration and interpretation of spatial and temporal patterns in district-level risk across India.

**Note:** Dashboard outputs reflect the datasets, scenarios, assumptions and methodology documented in the associated research.
