"""Fit the post-event model after the evaluation protocol is fixed."""

from __future__ import annotations

import json
from pathlib import Path

import joblib

from .build_features import TARGET_COLUMN
from .evaluate_loeo import DEFAULT_XGBOOST_PARAMS, make_regressor


def fit_final_model(frame, feature_columns, output_dir, params=None):
    model = make_regressor(params)
    model.fit(frame[feature_columns], frame[TARGET_COLUMN])
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, output / "post_event_recovery_model.joblib")
    metadata = {
        "task": "post-event recovery triage",
        "target": TARGET_COLUMN,
        "features": feature_columns,
        "model": "XGBRegressor",
        "params": {**DEFAULT_XGBOOST_PARAMS, **(params or {})},
        "warning": "This fitted model is not evidence of policy impact or real-time performance.",
    }
    (output / "model_metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return model
