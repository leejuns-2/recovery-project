"""One-command entry point for the reconstructed public experiment path."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .build_features import read_modeling_table, validate_feature_columns
from .evaluate_loeo import run_loeo, write_loeo_outputs
from .train import fit_final_model


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="CSV or Parquet event-district table")
    parser.add_argument("--features", nargs="+", required=True, help="Original numeric feature names")
    parser.add_argument("--output-dir", default="outputs/reproducible")
    parser.add_argument("--model-params", help="Optional JSON file of XGBRegressor parameters")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    frame = read_modeling_table(args.input)
    features = validate_feature_columns(frame, args.features)
    params = None
    if args.model_params:
        params = json.loads(Path(args.model_params).read_text(encoding="utf-8"))
    predictions = run_loeo(frame, features, params=params)
    write_loeo_outputs(predictions, args.output_dir)
    fit_final_model(frame, features, args.output_dir, params=params)
    print(f"Wrote reproducible outputs to {Path(args.output_dir).resolve()}")


if __name__ == "__main__":
    main()
