"""Run fair chronological XGBRanker factor-set experiments."""

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
    DATA_FILE, DEVELOPMENT_END, DEVELOPMENT_START, FACTOR_OUTPUT_DIR, FINAL_TEST_END,
    FINAL_TEST_START, RANDOM_STATE, TARGET_COLUMN, VALIDATION_END, VALIDATION_START,
    XGB_OUTPUT_DIR, XGB_RANKER_PARAM_CANDIDATES,
)
from .data import add_exact_week_targets, load_weekly_panel
from .factor_sets import load_factor_sets, save_forward_selected
from .forward_selection import forward_select
from .metrics import aggregate_metrics, metrics_by_date, yearly_metrics
from .rolling import rolling_oos
from .xgb_ranker import fit_ranker, predict_ranker


def tune(df, features, candidates, objective):
    train = df.loc[df["date"].between(DEVELOPMENT_START, DEVELOPMENT_END)
                   & (df["target_observation_date"] < pd.Timestamp(VALIDATION_START))]
    valid = df.loc[df["date"].between(VALIDATION_START, VALIDATION_END)]
    rows = []
    for index, params in enumerate(candidates):
        model = fit_ranker(train, features, params, objective)
        pred = predict_ranker(model, valid, features)
        metrics = aggregate_metrics(metrics_by_date(pred), "validation_")
        rows.append({"candidate_id": index, "hyperparameters": json.dumps(params, sort_keys=True), **metrics})
    result = pd.DataFrame(rows).sort_values(
        ["validation_mean_rank_ic", "validation_icir", "validation_ndcg5", "validation_top5_bottom5_spread"],
        ascending=False, kind="stable")
    return json.loads(result.iloc[0]["hyperparameters"]), result


def _git_hash():
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return None


def _decorate_date_metrics(predictions):
    pieces = []
    for keys, group in predictions.groupby(["factor_set_name", "sample_mode"], sort=True):
        metrics = metrics_by_date(group)
        metrics["factor_set_name"], metrics["sample_mode"] = keys
        model_map = group.drop_duplicates("date").set_index("date")["model_id"]
        metrics["model_id"] = metrics["date"].map(model_map)
        pieces.append(metrics)
    return pd.concat(pieces, ignore_index=True) if pieces else pd.DataFrame()


def run(args):
    args.output_dir.mkdir(parents=True, exist_ok=True)
    factor_path = args.factor_output_dir / "ml_factor_sets.json"
    if not factor_path.exists():
        run_factor_analysis(args.input, args.factor_output_dir)
    print("[1/8] Loading corrected weekly target and factor sets", flush=True)
    data = add_exact_week_targets(load_weekly_panel(args.input))
    sets = load_factor_sets(factor_path, data.columns)
    requested = list(sets) if args.factor_set == "all" else [args.factor_set]
    if args.quick and args.factor_set == "all":
        requested = [n for n in ["core_5", "extended", "top_10", "all_eligible"] if n in sets]
    candidates = XGB_RANKER_PARAM_CANDIDATES[:1] if args.skip_tuning else XGB_RANKER_PARAM_CANDIDATES[:2 if args.quick else None]
    config = {"target": TARGET_COLUMN, "development": [DEVELOPMENT_START, DEVELOPMENT_END],
              "validation": [VALIDATION_START, VALIDATION_END], "final_test": [FINAL_TEST_START, FINAL_TEST_END],
              "objective": args.objective, "random_state": RANDOM_STATE, "quick": args.quick,
              "versions": {"python": platform.python_version(), "xgboost": xgboost.__version__, "pandas": pd.__version__, "numpy": np.__version__},
              "git_commit": _git_hash()}
    (args.output_dir / "xgb_ranker_config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    print("[2/8] Hyperparameter tuning on chronological validation", flush=True)
    tuning_rows, best_params = [], {}
    for name in requested:
        print(f"  tuning {name} ({len(sets[name])} features)", flush=True)
        params, result = tune(data, sets[name], candidates, args.objective)
        result["factor_set_name"] = name; tuning_rows.append(result); best_params[name] = params
    pd.concat(tuning_rows, ignore_index=True).to_csv(args.output_dir / "xgb_ranker_hyperparameter_results.csv", index=False)
    if args.run_forward_selection:
        print("[3/8] Development-only forward selection", flush=True)
        ordered = sets["all_eligible"][:(8 if args.quick else len(sets["all_eligible"]))]
        development = data.loc[data["date"].between(DEVELOPMENT_START, DEVELOPMENT_END)]
        selected, audit = forward_select(development, ordered, best_params[requested[0]], args.objective,
                                         max_factors=3 if args.quick else 15)
        audit.to_csv(args.output_dir / "xgb_ranker_forward_selection.csv", index=False)
        save_forward_selected(factor_path, selected)
        if "forward_selected" not in requested:
            sets["forward_selected"] = selected
    elif not (args.output_dir / "xgb_ranker_forward_selection.csv").exists():
        pd.DataFrame(columns=["step", "current_factor_set", "candidate_factor", "candidate_mean_rank_ic", "candidate_icir",
                              "candidate_ndcg5", "candidate_top5_bottom5_spread", "delta_rank_ic", "delta_icir", "selected", "reason"]).to_csv(
                                  args.output_dir / "xgb_ranker_forward_selection.csv", index=False)
    print("[4/8] Monthly refits and weekly locked-test predictions", flush=True)
    all_predictions, all_models = [], []
    for name in requested:
        print(f"  rolling {name}", flush=True)
        pred, model_metrics = rolling_oos(data, sets[name], name, best_params[name], args.objective)
        pred["sample_mode"] = "native_coverage"; pred["common_sample_flag"] = False
        all_predictions.append(pred); all_models.append(model_metrics)
    native = pd.concat(all_predictions, ignore_index=True)
    keys_by_set = [set(map(tuple, g[["date", "ticker"]].to_numpy())) for _, g in native.groupby("factor_set_name")]
    common_keys = set.intersection(*keys_by_set) if keys_by_set else set()
    common = native.loc[[tuple(x) in common_keys for x in native[["date", "ticker"]].to_numpy()]].copy()
    common["sample_mode"], common["common_sample_flag"] = "common_sample", True
    predictions = pd.concat([native, common], ignore_index=True)
    keep = ["date", "ticker", "model_id", "factor_set_name", "refit_date", "ranking_score", "predicted_rank",
            "actual_return", "actual_rank", "relevance_label", "sample_mode", "common_sample_flag"]
    predictions[keep].to_csv(args.output_dir / "xgb_ranker_oos_predictions.csv", index=False)
    models = pd.concat(all_models, ignore_index=True)
    models.to_csv(args.output_dir / "xgb_ranker_model_metrics.csv", index=False)
    print("[5/8] Date and year metrics", flush=True)
    date_metrics = _decorate_date_metrics(predictions)
    date_metrics.to_csv(args.output_dir / "xgb_ranker_metrics_by_date.csv", index=False)
    year_parts = []
    for keys, group in date_metrics.groupby(["factor_set_name", "sample_mode"]):
        yearly = yearly_metrics(group); yearly["factor_set_name"], yearly["sample_mode"] = keys; year_parts.append(yearly)
    years = pd.concat(year_parts, ignore_index=True)
    years.to_csv(args.output_dir / "xgb_ranker_metrics_by_year.csv", index=False)
    print("[6/8] Fair factor-set comparison", flush=True)
    comparison = []
    tuning_all = pd.concat(tuning_rows, ignore_index=True)
    for name in requested:
        best_tune = tuning_all.loc[tuning_all["factor_set_name"] == name].sort_values("validation_mean_rank_ic", ascending=False).iloc[0]
        row = {"factor_set_name": name, "number_of_features": len(sets[name]), "feature_list": json.dumps(sets[name])}
        row.update({c: best_tune[c] for c in best_tune.index if c.startswith("validation_")})
        for mode in ["common_sample", "native_coverage"]:
            subset = date_metrics.loc[(date_metrics["factor_set_name"] == name) & (date_metrics["sample_mode"] == mode)]
            agg = aggregate_metrics(subset, "oos_")
            if mode == "common_sample": row.update(agg)
            row[f"{mode}_n"] = len(predictions.loc[(predictions.factor_set_name == name) & (predictions.sample_mode == mode)])
        y = years.loc[(years.factor_set_name == name) & (years.sample_mode == "common_sample")]
        row["yearly_rank_ic_std"] = y["mean_rank_ic"].std(); row["worst_year_rank_ic"] = y["mean_rank_ic"].min(); row["best_year_rank_ic"] = y["mean_rank_ic"].max()
        comparison.append(row)
    comparison = pd.DataFrame(comparison)
    comparison.to_csv(args.output_dir / "xgb_ranker_factor_set_comparison.csv", index=False)
    comparison.to_csv(args.output_dir / "xgb_ranker_summary.csv", index=False)
    print("[7/8] Diagnostics", flush=True)
    diagnostics = {"low_dispersion_dates": int((date_metrics.prediction_score_std < 1e-8).sum()),
                   "models": len(models), "predictions": len(predictions), "common_observations_per_set": len(common_keys)}
    print(json.dumps(diagnostics, indent=2), flush=True)
    print("[8/8] Complete", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DATA_FILE)
    parser.add_argument("--factor-output-dir", type=Path, default=FACTOR_OUTPUT_DIR)
    parser.add_argument("--output-dir", type=Path, default=XGB_OUTPUT_DIR)
    parser.add_argument("--factor-set", default="all")
    parser.add_argument("--objective", choices=["rank:ndcg", "rank:pairwise"], default="rank:ndcg")
    parser.add_argument("--common-sample", action="store_true", help="Retained for CLI compatibility; both modes are always exported.")
    parser.add_argument("--skip-tuning", action="store_true")
    parser.add_argument("--run-forward-selection", action="store_true")
    mode = parser.add_mutually_exclusive_group(); mode.add_argument("--quick", action="store_true"); mode.add_argument("--full", action="store_true")
    args = parser.parse_args(); args.quick = args.quick or not args.full
    run(args)


if __name__ == "__main__":
    main()
