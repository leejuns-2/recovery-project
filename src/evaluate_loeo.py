"""Leave-one-event-out regression and ranking evaluation."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from .build_features import RANKING_LABEL, TARGET_COLUMN
from .ranking_metrics import event_ranking_metrics, summarize_event_metrics


DEFAULT_XGBOOST_PARAMS = {
    "n_estimators": 300,
    "max_depth": 4,
    "learning_rate": 0.03,
    "subsample": 0.9,
    "colsample_bytree": 0.9,
    "objective": "reg:squarederror",
    "random_state": 42,
    "n_jobs": -1,
}


def make_regressor(params: dict[str, object] | None = None):
    try:
        from xgboost import XGBRegressor
    except ImportError as exc:
        raise RuntimeError("Install requirements-submission.txt to run XGBoost LOEO") from exc
    merged = {**DEFAULT_XGBOOST_PARAMS, **(params or {})}
    return XGBRegressor(**merged)


def run_loeo(
    frame: pd.DataFrame,
    feature_columns: list[str],
    *,
    params: dict[str, object] | None = None,
) -> pd.DataFrame:
    predictions = []
    for event_id in sorted(frame["event_id"].unique()):
        train = frame[frame["event_id"] != event_id]
        held_out = frame[frame["event_id"] == event_id].copy()
        model = make_regressor(params)
        model.fit(train[feature_columns], train[TARGET_COLUMN])
        prediction = np.clip(model.predict(held_out[feature_columns]), 0.0, 1.0)
        held_out["predicted_min_recovery_d1_d3"] = prediction
        held_out["risk_score"] = 1.0 - prediction
        predictions.append(held_out)
    return pd.concat(predictions, ignore_index=True)


def write_loeo_outputs(predictions: pd.DataFrame, output_dir: str | Path) -> None:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    predictions.to_csv(output / "loeo_predictions.csv", index=False)

    y_true = predictions[TARGET_COLUMN]
    y_pred = predictions["predicted_min_recovery_d1_d3"]
    mse = mean_squared_error(y_true, y_pred)
    regression = {
        "n_rows": int(len(predictions)),
        "n_events": int(predictions["event_id"].nunique()),
        "MSE": float(mse),
        "RMSE": float(np.sqrt(mse)),
        "MAE": float(mean_absolute_error(y_true, y_pred)),
        "R2": float(r2_score(y_true, y_pred)),
    }
    (output / "loeo_regression_metrics.json").write_text(
        json.dumps(regression, indent=2) + "\n", encoding="utf-8"
    )

    evaluations = {
        "top_20_percent": event_ranking_metrics(predictions, top_fraction=0.20),
        "fixed_k_20": event_ranking_metrics(predictions, k=20),
    }
    summaries = {}
    for name, table in evaluations.items():
        table.to_csv(output / f"ranking_{name}_by_event.csv", index=False)
        summaries[name] = summarize_event_metrics(table)
    (output / "ranking_summary.json").write_text(
        json.dumps(summaries, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
