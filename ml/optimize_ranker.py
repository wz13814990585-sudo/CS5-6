"""Validation-only Ranker optimization followed by one locked OOS evaluation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from .config import (
    DATA_FILE, DEVELOPMENT_END, DEVELOPMENT_START, FACTOR_OUTPUT_DIR,
    TARGET_COLUMN, VALIDATION_END, VALIDATION_START,
)
from .data import add_exact_week_targets, load_weekly_panel
from .factor_sets import load_factor_sets
from .metrics import aggregate_metrics, metrics_by_date, yearly_metrics
from .rolling import rolling_oos
from .xgb_ranker import fit_ranker, predict_ranker


SEARCH_PARAMS = [
    {"max_depth": 1, "learning_rate": .03, "n_estimators": 150, "min_child_weight": 10,
     "subsample": .85, "colsample_bytree": .7, "reg_alpha": 1., "reg_lambda": 10., "gamma": .1},
    {"max_depth": 2, "learning_rate": .02, "n_estimators": 250, "min_child_weight": 20,
     "subsample": .85, "colsample_bytree": .7, "reg_alpha": 1., "reg_lambda": 20., "gamma": .2},
    {"max_depth": 2, "learning_rate": .05, "n_estimators": 200, "min_child_weight": 5,
     "subsample": .85, "colsample_bytree": .85, "reg_alpha": .1, "reg_lambda": 5., "gamma": 0.},
    {"max_depth": 3, "learning_rate": .03, "n_estimators": 400, "min_child_weight": 5,
     "subsample": .85, "colsample_bytree": 1., "reg_alpha": 0., "reg_lambda": 5., "gamma": .1},
]


def validation_search(data, factor_sets):
    train = data.loc[data["date"].between(DEVELOPMENT_START, DEVELOPMENT_END)
                     & (data["target_observation_date"] < pd.Timestamp(VALIDATION_START))]
    validation = data.loc[data["date"].between(VALIDATION_START, VALIDATION_END)]
    rows = []
    total = len(factor_sets) * 2 * 3 * len(SEARCH_PARAMS)
    index = 0
    for name, features in factor_sets.items():
        for objective in ("rank:ndcg", "rank:pairwise"):
            for bins in (5, 10, 20):
                for param_id, params in enumerate(SEARCH_PARAMS):
                    index += 1
                    if index == 1 or index % 20 == 0:
                        print(f"  validation search {index}/{total}: {name}, {objective}, bins={bins}", flush=True)
                    model = fit_ranker(train, features, params, objective, bins)
                    predictions = predict_ranker(model, validation, features, bins)
                    metrics = aggregate_metrics(metrics_by_date(predictions), "validation_")
                    rows.append({"factor_set_name": name, "number_of_features": len(features),
                                 "objective": objective, "n_relevance_bins": bins, "param_id": param_id,
                                 "hyperparameters": json.dumps(params, sort_keys=True), **metrics})
    result = pd.DataFrame(rows).sort_values(
        ["validation_mean_rank_ic", "validation_icir", "validation_ndcg5", "validation_top5_bottom5_spread"],
        ascending=False, kind="stable").reset_index(drop=True)
    return result


def run(input_path: Path, factor_file: Path, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    print("[1/5] Load corrected complete-week panel", flush=True)
    data = add_exact_week_targets(load_weekly_panel(input_path))
    factor_sets = load_factor_sets(factor_file, data.columns)
    # Identical feature lists are evaluated once, while aliases remain traceable.
    unique_sets, aliases = {}, {}
    for name, features in factor_sets.items():
        key = tuple(features)
        if key not in aliases:
            aliases[key] = name; unique_sets[name] = features
    print(f"[2/5] Validation-only search across {len(unique_sets)} unique factor sets", flush=True)
    search = validation_search(data, unique_sets)
    search.to_csv(output_dir / "ranker_optimization_validation_search.csv", index=False)
    best = search.iloc[0]
    features = unique_sets[best.factor_set_name]
    params = json.loads(best.hyperparameters)
    print("[3/5] Freeze best Validation configuration", flush=True)
    print(best[["factor_set_name", "objective", "n_relevance_bins", "validation_mean_rank_ic",
                "validation_icir", "validation_ndcg5", "validation_top5_bottom5_spread"]].to_string(), flush=True)
    config = {"selection_data": "development fit and 2022-2023 validation only",
              "locked_oos_used_for_selection": False, "factor_set_name": best.factor_set_name,
              "features": features, "objective": best.objective,
              "n_relevance_bins": int(best.n_relevance_bins), "hyperparameters": params}
    (output_dir / "ranker_optimized_config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    print("[4/5] Run one locked OOS rolling evaluation", flush=True)
    predictions, models = rolling_oos(data, features, best.factor_set_name, params, best.objective,
                                      int(best.n_relevance_bins))
    predictions["sample_mode"] = "native_coverage"; predictions["common_sample_flag"] = True
    predictions.to_csv(output_dir / "ranker_optimized_oos_predictions.csv", index=False)
    models.to_csv(output_dir / "ranker_optimized_model_metrics.csv", index=False)
    by_date = metrics_by_date(predictions)
    by_date.to_csv(output_dir / "ranker_optimized_metrics_by_date.csv", index=False)
    years = yearly_metrics(by_date); years.to_csv(output_dir / "ranker_optimized_metrics_by_year.csv", index=False)
    summary = pd.DataFrame([{**best.to_dict(), **aggregate_metrics(by_date, "oos_")}])
    summary.to_csv(output_dir / "ranker_optimized_summary.csv", index=False)
    print("[5/5] Optimization complete", flush=True)
    print(summary[["factor_set_name", "objective", "n_relevance_bins", "validation_mean_rank_ic",
                   "oos_mean_rank_ic", "oos_icir", "oos_positive_ic_ratio",
                   "oos_top5_bottom5_spread"]].to_string(index=False), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DATA_FILE)
    parser.add_argument("--factor-file", type=Path, default=FACTOR_OUTPUT_DIR / "ml_factor_sets.json")
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/xgb_ranker_optimized"))
    args = parser.parse_args()
    run(args.input, args.factor_file, args.output_dir)


if __name__ == "__main__":
    main()
