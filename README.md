# Climate Risk Dashboard for India (LPS-Based)

## Overview
This project presents an interactive climate risk dashboard for India, developed using Low Pressure System (LPS)-driven rainfall hazard, exposure, and vulnerability data.

The dashboard allows users to explore district-level climate risk across:
- Present (historical baseline)
- Near future
- Far future

## Methodology

Risk is computed using:

Risk = Hazard × Exposure × Vulnerability

### Components

- **Hazard**: LPS-induced rainfall extremes (ETCCDI indices)
- **Exposure**:
  - Population exposure
  - Human system exposure (built-up and crop intensity)
- **Vulnerability**: District-level socio-economic vulnerability index

### Aggregation

Grid-level risk (0.25° resolution) is aggregated to district level using:
- Mean (overall risk)
- 90th percentile (high-risk zones)
- Maximum (extreme hotspots)

### Change Analysis

Percentage change is computed relative to the present baseline, with masking applied to low baseline values to avoid inflated changes.

## Features

- Interactive district-level risk map
- Multiple time scenarios
- Population vs human system risk comparison
- Aggregation toggle (Mean, P90, Max)

## Tech Stack

- Python
- Streamlit
- GeoPandas
- Xarray
- Plotly

## Data

- IMD-based LPS rainfall data (1979–2022)
- HighResMIP climate model projections
- Population and built-up datasets
- District-level vulnerability index

## How to Run

```bash
pip install -r requirements.txt
streamlit run app.py
