"""Load and validate an event-district modeling table without altering raw data."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


ID_COLUMNS = ["event_id", "adm_cd"]
TARGET_COLUMN = "min_recovery_rate_d1_d3"
RANKING_LABEL = "delayed"
FORBIDDEN_FEATURES = {
    TARGET_COLUMN,
    RANKING_LABEL,
    "recovery_days",
    "recovery_days_actual",
    "delayed_actual",
    "risk_score",
    "predicted_min_recovery_d1_d3",
}


def read_modeling_table(path: str | Path) -> pd.DataFrame:
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(f"Modeling table not found: {source}")
    if source.suffix.lower() == ".parquet":
        frame = pd.read_parquet(source)
    elif source.suffix.lower() == ".csv":
        frame = pd.read_csv(source)
    else:
        raise ValueError("Input must be a .csv or .parquet file")

    required = set(ID_COLUMNS + [TARGET_COLUMN, RANKING_LABEL])
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"Modeling table is missing required columns: {missing}")
    if frame.duplicated(ID_COLUMNS).any():
        raise ValueError("Each event_id × adm_cd pair must be unique")
    if frame[TARGET_COLUMN].isna().any() or frame[RANKING_LABEL].isna().any():
        raise ValueError("Target and delayed label must not contain missing values")

    frame = frame.copy()
    frame["adm_cd"] = frame["adm_cd"].astype("string")
    return frame.sort_values(ID_COLUMNS).reset_index(drop=True)


def validate_feature_columns(frame: pd.DataFrame, feature_columns: list[str]) -> list[str]:
    if not feature_columns:
        raise ValueError("Pass the original experiment feature names with --features")
    missing = sorted(set(feature_columns) - set(frame.columns))
    if missing:
        raise ValueError(f"Requested feature columns are missing: {missing}")
    forbidden = sorted(set(feature_columns) & FORBIDDEN_FEATURES)
    if forbidden:
        raise ValueError(f"Post-outcome or target-derived features are forbidden: {forbidden}")
    non_numeric = [column for column in feature_columns if not pd.api.types.is_numeric_dtype(frame[column])]
    if non_numeric:
        raise ValueError(f"This reconstructed XGBoost path expects numeric features: {non_numeric}")
    return feature_columns
