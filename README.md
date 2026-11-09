# LPS Risk Explorer — Optimized Dashboard Package

This package runs the existing Indian Monsoon LPS Risk Explorer interface
against self-contained, preprocessed copies of the source data. The original
GitHub project is not needed to run the dashboard.

## Run

From PowerShell:

```powershell
cd D:\IISER\Project\App\LPS_Risk_Explorer\Dashboard_package
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

The ready-to-run Parquet tables and map files are included under `data`. To
rebuild them after replacing the source workbook or map files in `data\source`,
run:

```powershell
python prepare_data.py
python validate_science.py
```

District vulnerability is read only from
`data\source\application_district_metrics.csv`, using its `DIST_ID` and `vul`
columns. The workbook's `Vulnerability_PCA` fields are not used by the app.

## Package contents

- `app.py` — Streamlit dashboard, retaining the existing layout, controls,
  tables, labels, scenarios and outputs.
- `map_rendering.py` — fast choropleth rendering using one copy of each
  district geometry per figure and one combined outline trace.
- `prepare_data.py` — creates the Parquet tables and render-ready GeoJSON from
  the included source copies. Geometry coordinates and district IDs are
  preserved; no simplification is applied.
- `validate_science.py` — exact source-to-package checks for displayed data,
  vulnerability provenance, district IDs, regional values and geometries.
- `benchmark.py` — comparable data-loading and map-rendering benchmarks for
  the original and optimized approaches.
- `data\source` — copies of the workbook, app metrics CSV, district and outline
  GeoJSON, and map style used to produce this package.
- `data\tables` — app-specific Parquet projections of the workbook sheets.
- `data\maps` — compact GeoJSON files and map style used by the app.

## Reports

- `performance_benchmark_report.md` — measured before/after timings and
  browser interaction results.
- `scientific_validation_report.md` — value, ID, missingness and geometry
  validation results.

To re-run the local benchmark:

```powershell
python benchmark.py --mode baseline --repeat 3
python benchmark.py --mode optimized --repeat 3
```

Benchmark commands write JSON measurements to `benchmarks`. Baseline mode
reads the bundled copies of the unoptimized workbook and GeoJSON and reproduces
the original Excel/Plotly workflow; optimized mode measures the packaged data
and renderer.

## Portable Windows desktop package

The Windows one-folder build and supervisor instructions are in
`README_DESKTOP.txt`. On a Windows build machine with Python 3.13 and the
dashboard dependencies installed, run
`powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\build_desktop.ps1`
from this directory.
The script installs PyInstaller if needed, builds
`dist\LPS_Risk_Explorer\LPS_Risk_Explorer.exe`, and creates
`LPS_Risk_Explorer_Desktop.zip`. The ZIP contains the complete application
folder; keep its files together after extraction.

Desktop packaging results and test limitations are recorded in
`desktop_build_test_report.md`.
