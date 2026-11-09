from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import numpy as np


ROOT = Path(__file__).resolve().parent
TABLE_DIR = ROOT / "data" / "tables"
REFERENCE_CSV = ROOT / "data" / "source" / "district_present_risk_baselines.csv"
TABLE_COLUMNS = {
    "District Maxima": [
        "DIST_ID",
        "District",
        "State",
        "Risk_Max_Normalized",
        "Risk_Max_Raw",
        "Hazard_at_Normalized_Max",
        "Exposure_at_Normalized_Max",
        "Exposure_Scenario",
        "Time_Period",
        "Configuration",
    ],
    "District Risk Change": [
        "DIST_ID",
        "District",
        "State",
        "Comparison",
        "Exposure_Scenario",
        "Risk_Change_Percent",
        "Baseline_Risk_Max_Raw",
        "Comparison_Risk_Max_Raw",
        "Comparison_Configuration",
        "IMD_Region",
    ],
    "IMD Regional Summary": [
        "Comparison",
        "Exposure_Scenario",
        "IMD_Region",
        "Mean_Risk_Change_Percent",
        "Median_Risk_Change_Percent",
        "Valid_District_Count",
    ],
    "District Master": ["DIST_ID", "District", "State"],
}
COMPARISONS = (
    ("Epoch 2 vs Epoch 1", "epoch1_population", "epoch2_population", "Population", None, None, None, False, None),
    ("Epoch 2 vs Epoch 1", "epoch1_human_system", "epoch2_human_system", "Human system", None, None, None, True, (-150.0, 150.0)),
    ("Near future vs Present", "population_reference", "near_future_population", "Population", "population_reference", 0.005, 1e-6, False, None),
    ("Near future vs Present", "human_system_reference", "near_future_human_system", "Human system", "human_system_reference", 0.01, None, False, None),
    ("Far future vs Present", "population_reference", "far_future_population", "Population", "population_reference", 0.005, 1e-6, False, None),
    ("Far future vs Present", "human_system_reference", "far_future_human_system", "Human system", "human_system_reference", 0.01, None, False, None),
    ("Far future vs Present", "population_2100_reference", "far_future_population_2100", "Future population (2100)", "population_2100_reference", 0.005, 1e-6, False, None),
)


def read_parquet(path: Path) -> pd.DataFrame:
    if not path.is_file():
        raise FileNotFoundError(f"Required dashboard table is missing: {path}")
    return pd.read_parquet(path)


def apply_research_maxima_semantics(
    maxima: pd.DataFrame, references: pd.DataFrame
) -> pd.DataFrame:
    maxima = maxima.copy()
    references_by_scenario = {
        key: frame.set_index("DIST_ID")
        for key, frame in references.groupby("Configuration")
    }

    for configuration in ("epoch1_human_system", "epoch2_human_system"):
        rows = maxima["Configuration"].eq(configuration)
        raw = pd.to_numeric(maxima.loc[rows, "Risk_Max_Raw"], errors="coerce").fillna(0.0)
        low, high = float(raw.min()), float(raw.max())
        maxima.loc[rows, "Risk_Max_Raw"] = raw
        maxima.loc[rows, "Risk_Max_Normalized"] = (
            0.0 if high == low else (raw - low) / (high - low)
        )

    for configuration in ("historical_population", "historical_human_system"):
        rows = maxima["Configuration"].eq(configuration)
        for column in ("Risk_Max_Raw", "Risk_Max_Normalized"):
            maxima.loc[rows, column] = (
                pd.to_numeric(maxima.loc[rows, column], errors="coerce")
                .fillna(0.0)
            )

    future_masks = {
        "near_future_population": "population_reference",
        "far_future_population": "population_reference",
        "near_future_human_system": "human_system_reference",
        "far_future_human_system": "human_system_reference",
        "far_future_population_2100": "population_2100_reference",
    }
    for configuration, reference_key in future_masks.items():
        if reference_key not in references_by_scenario:
            raise ValueError(f"Missing present-risk reference: {reference_key}")
        rows = maxima["Configuration"].eq(configuration)
        eligible = (
            references_by_scenario[reference_key]["District_Mask_Eligible"]
            .reindex(maxima.loc[rows, "DIST_ID"])
            .fillna(False)
            .to_numpy(dtype=bool)
        )
        for column in ("Risk_Max_Raw", "Risk_Max_Normalized"):
            values = pd.to_numeric(maxima.loc[rows, column], errors="coerce")
            maxima.loc[rows, column] = values.where(eligible).to_numpy()
    return maxima


def build_risk_changes(
    maxima: pd.DataFrame,
    references: pd.DataFrame,
    district_master: pd.DataFrame,
    regions: pd.DataFrame,
) -> pd.DataFrame:
    maxima_by_configuration = {
        key: frame.set_index("DIST_ID")
        for key, frame in maxima.groupby("Configuration")
    }
    references_by_configuration = {
        key: frame.set_index("DIST_ID")
        for key, frame in references.groupby("Configuration")
    }
    master = district_master.set_index("DIST_ID")
    region_by_id = regions.set_index("DIST_ID")["IMD_Region"]
    output = []

    for (
        comparison_name,
        baseline_key,
        comparison_key,
        exposure_scenario,
        reference_key,
        threshold,
        epsilon,
        zero_fill_missing,
        clip,
    ) in COMPARISONS:
        comparison = maxima_by_configuration[comparison_key].reindex(master.index)
        if reference_key is None:
            baseline = maxima_by_configuration[baseline_key].reindex(master.index)
            baseline_values = pd.to_numeric(
                baseline["Risk_Max_Raw"], errors="coerce"
            )
        else:
            reference = references_by_configuration[reference_key].reindex(master.index)
            baseline_values = pd.to_numeric(
                reference["Reference_Risk_Max_Raw"], errors="coerce"
            )
            eligible = (
                reference["District_Mask_Eligible"].fillna(False).astype(bool)
            )
            baseline_values = baseline_values.where(eligible)

        comparison_values = pd.to_numeric(
            comparison["Risk_Max_Raw"], errors="coerce"
        )
        if zero_fill_missing:
            baseline_values = baseline_values.fillna(0.0)
            comparison_values = comparison_values.fillna(0.0)
        if reference_key is not None and threshold is not None:
            reference_values = pd.to_numeric(
                reference["Reference_Risk_Max_Raw"], errors="coerce"
            )
            eligible &= reference_values >= threshold
            baseline_values = baseline_values.where(eligible)
            comparison_values = comparison_values.where(eligible)

        denominator = (
            np.maximum(baseline_values, epsilon)
            if epsilon is not None
            else baseline_values
        )
        with np.errstate(divide="ignore", invalid="ignore"):
            change = ((comparison_values - baseline_values) / denominator) * 100.0
        change = change.replace([np.inf, -np.inf], np.nan)
        if clip is not None:
            change = change.clip(lower=clip[0], upper=clip[1])

        frame = pd.DataFrame(
            {
                "DIST_ID": master.index,
                "District": master["District"].values,
                "State": master["State"].values,
                "Comparison": comparison_name,
                "Exposure_Scenario": exposure_scenario,
                "Risk_Change_Percent": change.to_numpy(dtype=float),
                "Baseline_Risk_Max_Raw": baseline_values.to_numpy(dtype=float),
                "Comparison_Risk_Max_Raw": comparison_values.to_numpy(dtype=float),
                "Comparison_Configuration": comparison_key,
                "IMD_Region": region_by_id.reindex(master.index).to_numpy(),
            }
        )
        output.append(frame)

    return pd.concat(output, ignore_index=True).loc[:, TABLE_COLUMNS["District Risk Change"]]


def build_regional_summary(changes: pd.DataFrame) -> pd.DataFrame:
    summary = (
        changes.groupby(
            ["Comparison", "Exposure_Scenario", "IMD_Region"],
            dropna=False,
            sort=True,
        )["Risk_Change_Percent"]
        .agg(
            Mean_Risk_Change_Percent="mean",
            Median_Risk_Change_Percent="median",
            Valid_District_Count="count",
        )
        .reset_index()
    )
    return summary.loc[:, TABLE_COLUMNS["IMD Regional Summary"]]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build the dashboard Parquet tables from a pipeline workbook."
    )
    parser.add_argument(
        "--workbook",
        type=Path,
        help="Optional pipeline workbook to refresh maxima and district master.",
    )
    args = parser.parse_args()

    if not REFERENCE_CSV.is_file():
        raise FileNotFoundError(f"Original present-risk reference is missing: {REFERENCE_CSV}")
    references = pd.read_csv(REFERENCE_CSV)
    if args.workbook:
        if not args.workbook.is_file():
            raise FileNotFoundError(f"Pipeline workbook not found: {args.workbook}")
        with pd.ExcelFile(args.workbook) as workbook:
            maxima = pd.read_excel(workbook, sheet_name="District Maxima")
            district_master = pd.read_excel(workbook, sheet_name="District Master")
    else:
        maxima = read_parquet(TABLE_DIR / "district_maxima.parquet")
        district_master = read_parquet(TABLE_DIR / "district_master.parquet")
    prior_changes = read_parquet(TABLE_DIR / "district_risk_change.parquet")
    region_columns = prior_changes[["DIST_ID", "IMD_Region"]].drop_duplicates()
    if region_columns["DIST_ID"].duplicated().any():
        raise ValueError("Existing district table contains conflicting IMD assignments")
    missing_columns = set(TABLE_COLUMNS["District Maxima"]) - set(maxima.columns)
    if missing_columns:
        raise ValueError(f"District maxima missing columns: {sorted(missing_columns)}")
    maxima = apply_research_maxima_semantics(maxima, references)
    changes = build_risk_changes(maxima, references, district_master, region_columns)
    regional_summary = build_regional_summary(changes)

    generated = {
        "district_maxima": maxima.loc[:, TABLE_COLUMNS["District Maxima"]],
        "district_risk_change": changes,
        "imd_regional_summary": regional_summary,
        "district_master": district_master.loc[:, TABLE_COLUMNS["District Master"]],
    }
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    for name, frame in generated.items():
        frame.to_parquet(
            TABLE_DIR / f"{name}.parquet",
            index=False,
            engine="pyarrow",
            compression="zstd",
        )
    print(f"Research-aligned dashboard tables written to {TABLE_DIR}")


if __name__ == "__main__":
    main()
