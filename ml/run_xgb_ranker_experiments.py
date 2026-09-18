"""Freeze a warmup-selected XGBRanker, then run genuine rolling OOS."""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost

from factor_analysis.build_weekly_factor_analysis import run_factor_analysis
from .config import (
    DAILY_DATA_FILE, DATA_FILE, FACTOR_OUTPUT_DIR, RANDOM_STATE, ROLLING_START,
    TARGET_COLUMN, WARMUP_END, WARMUP_START, XGB_OUTPUT_DIR,
)
from .data import add_exact_week_targets, load_weekly_panel
from .factor_sets import load_factor_sets
from .metrics import aggregate_metrics, metrics_by_date, yearly_metrics
from .optimize_ranker import (best_per_factor_set, frozen_config,
                              native_results_for_common_winners, warmup_ranker_search)
from .rolling import rolling_oos


def _git_hash():
    try: return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception: return None


def run(args):
    args.output_dir.mkdir(parents=True, exist_ok=True); args.factor_output_dir.mkdir(parents=True, exist_ok=True)
    print("[1/8] Build common-date weekly X and full-next-week Y", flush=True)
    data = add_exact_week_targets(load_weekly_panel(args.input, args.daily))
    factor_file = args.factor_output_dir / "ml_factor_sets.json"
    if args.rebuild_factors or not factor_file.exists():
        print("[2/8] Warmup-only factor analysis", flush=True)
        run_factor_analysis(args.input, args.factor_output_dir)
        data = add_exact_week_targets(load_weekly_panel(args.input, args.daily))
    else: print("[2/8] Reuse warmup factor-set export", flush=True)
    factor_sets = load_factor_sets(factor_file, data.columns)
    print("[3/8] Joint chronological search entirely inside first-three-year warmup", flush=True)
    search = warmup_ranker_search(data, factor_sets, "common_sample")
    search.to_csv(args.output_dir / "warmup_ranker_search.csv", index=False)
    search.to_csv(args.output_dir / "xgb_ranker_hyperparameter_results.csv", index=False)  # compatibility alias
    comparison = pd.concat([best_per_factor_set(search),
                            native_results_for_common_winners(data, factor_sets, search)], ignore_index=True)
    comparison["selected_final_config"] = False
    best = search.iloc[0]
    comparison.loc[(comparison.factor_set_name == best.factor_set_name)
                   & (comparison.sample_mode == "common_sample"), "selected_final_config"] = True
    comparison.to_csv(args.factor_output_dir / "warmup_factor_set_comparison.csv", index=False)
    comparison.to_csv(args.output_dir / "xgb_ranker_factor_set_comparison.csv", index=False)
    config = frozen_config(best)
    config.update({"random_state": RANDOM_STATE, "python_version": platform.python_version(),
                   "xgboost_version": xgboost.__version__, "pandas_version": pd.__version__,
                   "numpy_version": np.__version__, "git_commit": _git_hash()})
    (args.output_dir / "frozen_ranker_config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    print(f"[4/8] Frozen: {config['factor_set_name']}, {config['objective']}, bins={config['n_relevance_bins']}", flush=True)
    print("[5/8] Monthly full-window refits and weekly OOS predictions", flush=True)
    predictions, models = rolling_oos(data, config["feature_list"], config["factor_set_name"],
                                      config["hyperparameters"], config["objective"], config["n_relevance_bins"])
    required_prediction = ["decision_date", "market_week_id", "ticker", "model_id", "refit_date",
        "factor_set_name", "ranking_score", "predicted_rank", "actual_return", "actual_rank",
        "relevance_label", "target_week_id", "target_week_first_date", "target_week_last_date",
        "target_observation_date"]
    predictions[required_prediction].to_csv(args.output_dir / "xgb_ranker_oos_predictions.csv", index=False)
    models.to_csv(args.output_dir / "xgb_ranker_model_metrics.csv", index=False)
    print("[6/8] Per-date and yearly metrics", flush=True)
    by_date = metrics_by_date(predictions)
    model_map = predictions.drop_duplicates("date").set_index("date")["model_id"]
    by_date["model_id"] = by_date["date"].map(model_map)
    by_date.to_csv(args.output_dir / "xgb_ranker_metrics_by_date.csv", index=False)
    yearly = yearly_metrics(by_date); yearly.to_csv(args.output_dir / "xgb_ranker_metrics_by_year.csv", index=False)
    print("[7/8] Overall OOS summary", flush=True)
    overall = aggregate_metrics(by_date)
    overall["number_of_weeks"] = overall.pop("number_of_dates")
    overall["number_of_monthly_models"] = len(models)
    pd.DataFrame([overall]).to_csv(args.output_dir / "xgb_ranker_oos_summary.csv", index=False)
    pd.DataFrame([overall]).to_csv(args.output_dir / "xgb_ranker_summary.csv", index=False)
    audit = {"warmup_weeks": int(data.loc[data.date.between(WARMUP_START, WARMUP_END), "date"].nunique()),
             "oos_start": str(predictions.date.min().date()), "oos_end": str(predictions.date.max().date()),
             "monthly_models": len(models), "predictions": len(predictions),
             "post_warmup_selection": False}
    (args.output_dir / "xgb_ranker_config.json").write_text(json.dumps({**config, **audit}, indent=2), encoding="utf-8")
    print("[8/8] Complete", json.dumps(audit), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DATA_FILE)
    parser.add_argument("--daily", type=Path, default=DAILY_DATA_FILE)
    parser.add_argument("--factor-output-dir", type=Path, default=FACTOR_OUTPUT_DIR)
    parser.add_argument("--output-dir", type=Path, default=XGB_OUTPUT_DIR)
    parser.add_argument("--rebuild-factors", action="store_true")
    args = parser.parse_args(); run(args)


if __name__ == "__main__": main()
