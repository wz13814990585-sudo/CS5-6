"""Build an independent ranking-only evaluation from saved out-of-sample scores."""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import scipy
from scipy.stats import kendalltau
import sklearn
from sklearn.metrics import ndcg_score

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "outputs/current"
STAGES = {"full_period": ("2019-08-30", "2026-08-28"),
          "development": ("2022-09-02", "2024-08-30"),
          "validation": ("2024-09-06", "2025-08-29"),
          "final_test": ("2025-09-05", "2026-08-21")}
FOLDS = (156, 247, 338, 430, 522)
SEED = 5703
BLOCK_LENGTH = 4
BOOTSTRAPS = 4000
FORBIDDEN = ("annualized_return", "information_ratio", "excess", "drawdown", "portfolio",
             "cash_weight", "target_weight", "transaction_cost", "slippage", "selected_stocks",
             "backtest", "strategy", "net_return", "gross_return", "benchmark_return")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_csv(path, dates=None):
    return pd.read_csv(path, parse_dates=dates, float_precision="round_trip")


def json_safe(obj):
    if isinstance(obj, dict):
        return {str(k): json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [json_safe(x) for x in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (float, np.floating)):
        return float(obj) if np.isfinite(obj) else None
    if isinstance(obj, pd.Timestamp):
        return obj.strftime("%Y-%m-%d")
    return obj


def write_json(path, obj):
    Path(path).write_text(json.dumps(json_safe(obj), indent=2, ensure_ascii=False, allow_nan=False)+"\n", encoding="utf-8")


def write_csv(path, frame):
    for column in frame:
        if any(word in column.lower() for word in FORBIDDEN):
            raise ValueError(f"Out-of-scope output column: {column}")
    frame.to_csv(path, index=False, encoding="utf-8-sig", float_format="%.17g")


def protected_snapshot():
    files = [ROOT / "model_configuration.json"]
    for directory in [ROOT / "inputs", ROOT / "models", ROOT / "code"]:
        files += [p for p in directory.rglob("*") if p.is_file() and "__pycache__" not in p.parts]
    return {str(p.relative_to(ROOT)): sha256(p) for p in sorted(files)}


def snapshot_digest(snapshot):
    return hashlib.sha256(json.dumps(snapshot, sort_keys=True).encode()).hexdigest()


def labels_from_target(target):
    return np.floor((pd.Series(target).rank(method="average")-1)*5/len(target)).clip(0, 4).to_numpy(int)


def pairwise_accuracy(score, target):
    i, j = np.triu_indices(len(target), 1)
    actual = np.sign(np.asarray(target)[i] - np.asarray(target)[j])
    predicted = np.sign(np.asarray(score)[i] - np.asarray(score)[j])
    valid = actual != 0
    if not valid.any():
        return np.nan
    return float(((predicted[valid] == actual[valid]).astype(float) + .5*(predicted[valid] == 0)).mean())


def weekly_metrics(group):
    group = group.sort_values("ticker", kind="stable")
    target, score = group.actual_next_week_log_return, group.prediction_score
    n = len(group)
    if n < 10 or not np.isfinite(group[["actual_next_week_log_return", "prediction_score"]]).all().all():
        raise ValueError("A weekly evaluation requires at least ten finite observations")
    pred_rank = score.rank(method="average", ascending=False).to_numpy()
    actual_rank = target.rank(method="average", ascending=False).to_numpy()
    rank_error = pred_rank - actual_rank
    random_rank_mae = float(np.abs(pred_rank[:, None] - actual_rank[None, :]).mean())
    unique_score = score.nunique() > 1
    unique_target = target.nunique() > 1
    row = {"IC": float(score.corr(target)) if unique_score and unique_target else np.nan,
           "Rank_IC": float(score.corr(target, method="spearman")) if unique_score and unique_target else np.nan,
           "Kendall_Tau": float(kendalltau(score, target, variant="b").statistic) if unique_score and unique_target else np.nan,
           "Pairwise_Accuracy": pairwise_accuracy(score, target), "Random_Pairwise_Accuracy": .5,
           "Rank_MAE": float(np.abs(rank_error).mean()), "Rank_RMSE": float(np.sqrt(np.mean(rank_error**2))),
           "Normalized_Rank_MAE": float(np.abs(rank_error).mean()/(n-1)),
           "Random_Normalized_Rank_MAE": random_rank_mae/(n-1)}
    gains = 2.0**labels_from_target(target) - 1
    discount = 1 / np.log2(np.arange(n) + 2)
    for label, k in [("5", 5), ("10", 10), ("all", n)]:
        ideal = float(np.dot(np.sort(gains)[::-1][:k], discount[:k]))
        row[f"NDCG_at_{label}"] = float(ndcg_score(gains[None, :], score.to_numpy()[None, :], k=k)) if ideal > 0 else np.nan
        row[f"Random_NDCG_at_{label}"] = float(gains.mean()*discount[:k].sum()/ideal) if ideal > 0 else np.nan
    for k in (5, 10):
        predicted = set(group.sort_values(["prediction_score", "ticker"], ascending=[False, True]).head(k).ticker)
        actual = set(group.sort_values(["actual_next_week_log_return", "ticker"], ascending=[False, True]).head(k).ticker)
        row[f"Hit_Rate_at_{k}"] = len(predicted & actual)/k
        row[f"Random_Hit_Rate_at_{k}"] = k/n
    counts = score.value_counts().to_numpy()
    row["Score_Tie_Pair_Ratio"] = float(np.sum(counts*(counts-1))/(n*(n-1)))
    return row


def bootstrap_rankic_interval(values):
    values = np.asarray(values, float)
    # Preserve the weekly sequence: do not bridge missing weeks by dropping them.
    if len(values) < 8 or not np.isfinite(values).all():
        return np.nan, np.nan
    rng = np.random.default_rng(SEED)
    starts = rng.integers(0, len(values), size=(BOOTSTRAPS, int(np.ceil(len(values)/BLOCK_LENGTH))))
    indices = ((starts[..., None]+np.arange(BLOCK_LENGTH)) % len(values)).reshape(BOOTSTRAPS, -1)[:, :len(values)]
    low, high = np.quantile(values[indices].mean(axis=1), [.025, .975])
    return float(low), float(high)


def aggregate(weekly, scope):
    weekly = weekly.sort_values("date")
    numeric = [c for c in weekly if c not in {"model", "date", "week_index", "refit_week", "number_of_stocks"}]
    row = {"model": weekly.model.iloc[0], "scope": scope, "start_date": weekly.date.min(),
           "end_date": weekly.date.max(), "prediction_weeks": len(weekly),
           "prediction_rows": int(weekly.number_of_stocks.sum()),
           "minimum_weekly_stocks": int(weekly.number_of_stocks.min()),
           "maximum_weekly_stocks": int(weekly.number_of_stocks.max()),
           **weekly[numeric].mean().to_dict()}
    for name in ["IC", "Rank_IC"]:
        valid = weekly[name].dropna()
        std = float(valid.std(ddof=1))
        row[f"{name}IR"] = float(valid.mean()/std) if std > 0 else np.nan
        row[f"Positive_{name}_Ratio"] = float((valid > 0).mean()) if len(valid) else np.nan
        row[f"Valid_{name}_Weeks"] = len(valid)
        row[f"Weekly_{name}_Std"] = std
    row["Median_Rank_IC"] = weekly.Rank_IC.median()
    row["Rank_IC_CI95_Lower"], row["Rank_IC_CI95_Upper"] = bootstrap_rankic_interval(weekly.Rank_IC)
    for label in ("5", "10", "all"):
        row[f"NDCG_at_{label}_Above_Random"] = row[f"NDCG_at_{label}"]-row[f"Random_NDCG_at_{label}"]
    for k in (5, 10):
        row[f"Hit_Rate_at_{k}_Above_Random"] = row[f"Hit_Rate_at_{k}"]-row[f"Random_Hit_Rate_at_{k}"]
    return row


def factor_audit(path, final_dates):
    frame = read_csv(path, ["date"])
    features = ["revenue_growth_yoy", "operating_profitability", "cashflow_to_assets", "debt_to_assets", "asset_growth_yoy"]
    rows = []
    for ticker, stock in frame.groupby("ticker"):
        stock = stock.sort_values("date")
        recent = stock[stock.date.between(*final_dates)]
        for feature in features:
            values = stock[feature]
            change = values.ne(values.shift())
            last_change = stock.loc[change, "date"].iloc[-1]
            days = (stock.date.max()-last_change).days
            rows.append({"ticker": ticker, "factor": feature, "observed_rows": len(stock),
                         "missing_values": int(values.isna().sum()), "nonfinite_values": int((~np.isfinite(values)).sum()),
                         "distinct_values_final_test": recent[feature].nunique(),
                         "last_observed_value": values.iloc[-1], "last_observed_change_date": last_change,
                         "last_observation_date": stock.date.max(), "unchanged_days_at_end": days,
                         "review_long_unchanged_value": days > 365})
    return pd.DataFrame(rows)


def build(args):
    source = args.source.resolve()
    before = protected_snapshot()
    old = read_csv(source / "predictions/stock_rankings.csv", ["date"]).rename(columns={"actual_next_week_log_return": "target", "actual_rank_ticker_tiebreak": "actual_rank"})
    if len(old) != 13517 or old.date.nunique() != 366 or old.ticker.nunique() != 40:
        raise ValueError("Unexpected source experiment dimensions")
    if old.duplicated(["date", "ticker"]).any():
        raise ValueError("Duplicate prediction keys")
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    for name in ("predictions", "metrics", "audit"):
        (out/name).mkdir()
    base_columns = ["week_index", "date", "ticker", "stock_name", "target", "actual_rank", "target_verification_status", "refit_week", "prediction_block"]
    columns = base_columns + [c for c in old if c.startswith("model_")] + ["ensemble_model_id", "ensemble_ranking_score", "ensemble_predicted_rank"]
    wide = old[columns].rename(columns={"target": "actual_next_week_log_return", "actual_rank": "actual_rank_ticker_tiebreak"}).copy()
    wide["actual_rank_average"] = wide.groupby("date").actual_next_week_log_return.rank(method="average", ascending=False)
    wide["actual_relevance_0_to_4"] = wide.groupby("date").actual_next_week_log_return.transform(lambda x: labels_from_target(x))
    write_csv(out/"predictions/stock_rankings.csv", wide)
    write_csv(out/"predictions/latest_historical_ranking.csv", wide[wide.date.eq(wide.date.max())].sort_values("ensemble_predicted_rank"))
    frames = []
    for model, prefix in [("Model 1", "model_1"), ("Model 2", "model_2"), ("Model 3", "model_3"), ("Ensemble", "ensemble")]:
        part = wide[["week_index", "date", "ticker", "stock_name", "actual_next_week_log_return", "actual_rank_average", "actual_rank_ticker_tiebreak", "actual_relevance_0_to_4", "refit_week"]].copy()
        part["model"] = model
        part["prediction_score"] = wide[f"{prefix}_percentile"] if model != "Ensemble" else wide.ensemble_ranking_score
        part["predicted_rank_ticker_tiebreak"] = wide[f"{prefix}_predicted_rank"]
        part["predicted_rank_average"] = part.groupby("date").prediction_score.rank(method="average", ascending=False)
        part["absolute_rank_error"] = (part.predicted_rank_average-part.actual_rank_average).abs()
        frames.append(part)
    predictions = pd.concat(frames, ignore_index=True)
    write_csv(out/"predictions/model_rankings_long.csv", predictions)
    weekly_rows = []
    for (model, date), group in predictions.groupby(["model", "date"], sort=True):
        weekly_rows.append({"model": model, "date": date, "week_index": int(group.week_index.iloc[0]),
                            "refit_week": int(group.refit_week.iloc[0]), "number_of_stocks": len(group), **weekly_metrics(group)})
    weekly = pd.DataFrame(weekly_rows)
    write_csv(out/"metrics/weekly_metrics.csv", weekly)
    stage_rows, annual_rows, fold_rows, refit_rows = [], [], [], []
    for model, group in weekly.groupby("model", sort=True):
        for scope, dates in STAGES.items():
            stage_rows.append(aggregate(group[group.date.between(*dates)], scope))
        for year, year_group in group.groupby(group.date.dt.year):
            annual_rows.append({"year": year, **aggregate(year_group, f"year_{year}")})
        for fold, (start, end) in enumerate(zip(FOLDS[:-1], FOLDS[1:]), 1):
            fold_rows.append({"fold": fold, **aggregate(group[group.week_index.between(start, end-1)], f"fold_{fold}")})
        for refit, block in group.groupby("refit_week"):
            refit_rows.append({"refit_week": refit, **aggregate(block, f"refit_{refit:04d}")})
        print(f"Computed ranking metrics: {model}", flush=True)
    stages = pd.DataFrame(stage_rows)
    write_csv(out/"metrics/stage_metrics.csv", stages)
    write_csv(out/"metrics/overall_metrics.csv", stages[stages.scope.eq("full_period")])
    write_csv(out/"metrics/annual_metrics.csv", pd.DataFrame(annual_rows))
    write_csv(out/"metrics/fold_metrics.csv", pd.DataFrame(fold_rows))
    write_csv(out/"metrics/refit_metrics.csv", pd.DataFrame(refit_rows))
    stock_rows = []
    for (model, ticker), g in predictions.groupby(["model", "ticker"]):
        stock_rows.append({"model": model, "ticker": ticker, "stock_name": g.stock_name.iloc[0],
                           "prediction_weeks": len(g), "first_date": g.date.min(), "last_date": g.date.max(),
                           "mean_predicted_rank": g.predicted_rank_average.mean(), "mean_actual_rank": g.actual_rank_average.mean(),
                           "rank_MAE": g.absolute_rank_error.mean(),
                           "predicted_top5_weeks": int((g.predicted_rank_ticker_tiebreak<=5).sum()),
                           "actual_top5_weeks": int((g.actual_rank_ticker_tiebreak<=5).sum()),
                           "matched_top5_weeks": int(((g.predicted_rank_ticker_tiebreak<=5)&(g.actual_rank_ticker_tiebreak<=5)).sum())})
    write_csv(out/"metrics/stock_rank_diagnostics.csv", pd.DataFrame(stock_rows))
    old_refit = read_csv(source/"audit/training_windows.csv")
    keep = ["model_id", "refit_week", "refit_date", "training_start_week", "training_end_week", "training_start_date",
            "training_end_date", "maximum_training_label_end_week", "training_weeks", "training_rows", "training_tickers",
            "test_ticker_overlap", "features", "hyperparameters", "training_label", "start_date", "end_date", "prediction_weeks", "prediction_rows"]
    write_csv(out/"audit/training_windows.csv", old_refit[keep])
    manifest = json.loads((source/"run_manifest.json").read_text())
    for filename in ["data_audit.csv", "training_data_audit.csv", "original_model_reproduction.csv"]:
        write_csv(out/"audit"/filename, read_csv(source/"audit"/filename))
    write_csv(out/"audit/factor_quality.csv", factor_audit(ROOT/"inputs/test40.csv", STAGES["final_test"]))
    config = json.loads((ROOT/"model_configuration.json").read_text())
    keep = ["model_type", "training_label", "evaluation_target", "feature_transform", "formal_prediction_weeks",
            "refit_interval_weeks", "label_observability_rule", "random_seed", "components", "ensemble"]
    write_json(out/"model_configuration.json", {k: config[k] for k in keep})
    max_error = 0.0
    if (source/"metrics/weekly_metrics.csv").exists():
        old_weekly = read_csv(source/"metrics/weekly_metrics.csv", ["date"])
        for model, prefix in [("Model 1", "model_1"), ("Model 2", "model_2"), ("Model 3", "model_3"), ("Ensemble", "ensemble")]:
            actual = weekly[weekly.model.eq(model)].sort_values("date")
            expected = old_weekly[old_weekly.model.eq(model)].sort_values("date")
            for metric in ["IC", "Rank_IC"]:
                np.testing.assert_allclose(actual[metric], expected[metric], rtol=0, atol=1e-12, equal_nan=True)
                max_error = max(max_error, float(np.nanmax(np.abs(actual[metric].to_numpy()-expected[metric].to_numpy()))))
    after = protected_snapshot()
    if before != after:
        raise AssertionError("An existing source file changed")
    report = {"status": "complete", "task": "stock ranking prediction and machine-learning evaluation",
              "created_utc": datetime.now(timezone.utc).isoformat(), "source_run": str(source.relative_to(ROOT)) if source.is_relative_to(ROOT) else str(source),
              "source_predictions_sha256": sha256(source/"predictions/stock_rankings.csv"),
              "source_input_sha256": sha256(ROOT/"inputs/test40.csv"), "builder_sha256": sha256(__file__),
              "prediction_rows": len(wide), "model_prediction_rows": len(predictions), "prediction_weeks": 366,
              "train_tickers": manifest["train_tickers"], "test_tickers": manifest["test_tickers"],
              "models_retrained": False, "hyperparameters_changed": False,
              "protected_file_count": len(before), "protected_snapshot_sha256": snapshot_digest(before),
              "original_files_unchanged": before == after, "max_original_correlation_error": max_error,
              "reporting_stages": STAGES, "stages_used_for_tuning": False,
              "confidence_interval": {"metric": "mean weekly Rank IC", "method": "circular moving-block percentile bootstrap",
                                      "block_weeks": BLOCK_LENGTH, "replicates": BOOTSTRAPS, "seed": SEED,
                                      "minimum_complete_weeks": 8, "coverage": .95},
              "versions": {"python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__,
                           "scipy": scipy.__version__, "scikit_learn": sklearn.__version__},
              "target_verification": "user-confirmed next-week adjusted-close log return; prices unavailable for independent verification",
              "factor_availability": "publication timestamps and long unchanged values require source review"}
    write_json(out/"run_manifest.json", report)
    print(stages[stages.scope.eq("final_test")][["model", "IC", "Rank_IC", "NDCG_at_10", "Hit_Rate_at_5", "Rank_IC_CI95_Lower", "Rank_IC_CI95_Upper"]].to_string(index=False))
    print(f"Completed: {out}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--output", type=Path, required=True)
    build(parser.parse_args())
