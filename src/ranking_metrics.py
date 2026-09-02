"""Ranking metrics with explicit percentage and fixed-capacity definitions."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd


def _selected_count(n_rows: int, *, top_fraction: float | None, k: int | None) -> int:
    if (top_fraction is None) == (k is None):
        raise ValueError("Specify exactly one of top_fraction or k")
    if top_fraction is not None:
        if not 0 < top_fraction <= 1:
            raise ValueError("top_fraction must be in (0, 1]")
        return max(1, math.ceil(n_rows * top_fraction))
    if k is None or k <= 0:
        raise ValueError("k must be positive")
    return min(k, n_rows)


def event_ranking_metrics(
    frame: pd.DataFrame,
    *,
    score_column: str = "risk_score",
    label_column: str = "delayed",
    event_column: str = "event_id",
    top_fraction: float | None = None,
    k: int | None = None,
) -> pd.DataFrame:
    """Return one precision/recall/lift row per event."""
    rows: list[dict[str, object]] = []
    for event_id, event in frame.groupby(event_column, sort=True):
        selected_n = _selected_count(len(event), top_fraction=top_fraction, k=k)
        selected = event.nlargest(selected_n, score_column)
        positives = int(event[label_column].sum())
        prevalence = float(event[label_column].mean())
        precision = float(selected[label_column].mean())
        recall = float(selected[label_column].sum() / positives) if positives else np.nan
        lift = float(precision / prevalence) if prevalence else np.nan
        rows.append(
            {
                event_column: event_id,
                "definition": (
                    f"top_{top_fraction:.0%}" if top_fraction is not None else f"fixed_k_{k}"
                ),
                "n_districts": int(len(event)),
                "selected_n": int(selected_n),
                "n_delayed": positives,
                "prevalence": prevalence,
                "precision": precision,
                "recall": recall,
                "lift": lift,
            }
        )
    return pd.DataFrame(rows)


def summarize_event_metrics(event_metrics: pd.DataFrame) -> dict[str, float | int]:
    """Summarize event variability without inventing confidence intervals."""
    return {
        "n_events": int(len(event_metrics)),
        "n_events_with_delayed": int(event_metrics["n_delayed"].gt(0).sum()),
        "mean_precision": float(event_metrics["precision"].mean()),
        "median_precision": float(event_metrics["precision"].median()),
        "mean_recall": float(event_metrics["recall"].mean(skipna=True)),
        "median_recall": float(event_metrics["recall"].median(skipna=True)),
        "mean_lift": float(event_metrics["lift"].mean(skipna=True)),
        "median_lift": float(event_metrics["lift"].median(skipna=True)),
    }
