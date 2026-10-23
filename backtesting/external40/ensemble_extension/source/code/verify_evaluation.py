"""Independent checks of saved ranking-only outputs and metric definitions."""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import rankdata

import build_evaluation as builder


def manual_ndcg(gain, score, k):
    order = np.argsort(-score, kind="stable")
    sorted_score, sorted_gain = score[order], gain[order]
    discount = np.zeros(len(score))
    discount[:k] = 1/np.log2(np.arange(k)+2)
    value = 0.0
    i = 0
    while i < len(score):
        j = i+1
        while j < len(score) and sorted_score[j] == sorted_score[i]:
            j += 1
        value += sorted_gain[i:j].mean()*discount[i:j].sum()
        i = j
    ideal = np.dot(np.sort(gain)[::-1], discount)
    return value/ideal if ideal else np.nan


def verify(out):
    manifest = json.loads((out/"run_manifest.json").read_text())
    source = Path(manifest["source_run"])
    if not source.is_absolute():
        source = builder.ROOT / source
    old = builder.read_csv(source/"predictions/stock_rankings.csv", ["date"]).rename(columns={"actual_next_week_log_return": "target"})
    wide = builder.read_csv(out/"predictions/stock_rankings.csv", ["date"])
    long = builder.read_csv(out/"predictions/model_rankings_long.csv", ["date"])
    weekly = builder.read_csv(out/"metrics/weekly_metrics.csv", ["date"])
    assert len(wide) == 13517 and len(long) == 54068 and len(weekly) == 1464
    pd.testing.assert_frame_equal(wide[["date", "ticker"]], old[["date", "ticker"]])
    for col in ["ensemble_ranking_score", "ensemble_predicted_rank"]+[c for c in old if c.startswith("model_")]:
        pd.testing.assert_series_equal(wide[col], old[col], check_names=False)
    np.testing.assert_array_equal(wide.actual_next_week_log_return, old.target)
    assert not long.duplicated(["model", "date", "ticker"]).any()
    max_error = 0.0
    row_checks = 0
    indexed = weekly.set_index(["model", "date"])
    for (model, date), group in long.groupby(["model", "date"], sort=True):
        group = group.sort_values("ticker")
        score, target = group.prediction_score.to_numpy(), group.actual_next_week_log_return.to_numpy()
        n = len(group)
        predicted_rank = rankdata(-score, method="average")
        actual_rank = rankdata(-target, method="average")
        row = indexed.loc[(model, date)]
        np.testing.assert_allclose(group.predicted_rank_average, predicted_rank, rtol=0, atol=0)
        np.testing.assert_allclose(group.actual_rank_average, actual_rank, rtol=0, atol=0)
        checks = {"IC": np.corrcoef(score, target)[0,1], "Rank_IC": np.corrcoef(predicted_rank, actual_rank)[0,1],
                  "Rank_MAE": np.abs(predicted_rank-actual_rank).mean(),
                  "Rank_RMSE": np.sqrt(((predicted_rank-actual_rank)**2).mean())}
        labels = np.minimum(4, np.floor((rankdata(target)-1)*5/n)).astype(int)
        gain = 2.0**labels-1
        for label, k in [("5",5), ("10",10), ("all",n)]:
            checks[f"NDCG_at_{label}"] = manual_ndcg(gain, score, k)
            checks[f"Random_NDCG_at_{label}"] = manual_ndcg(gain, np.zeros(n), k)
        correct, eligible, concordant, discordant, score_only_ties, target_only_ties = 0.0, 0, 0, 0, 0, 0
        for i in range(n):
            for j in range(i+1, n):
                s, t = np.sign(score[i]-score[j]), np.sign(target[i]-target[j])
                if t != 0:
                    eligible += 1
                    correct += 1 if s == t else (.5 if s == 0 else 0)
                if s*t > 0:
                    concordant += 1
                elif s*t < 0:
                    discordant += 1
                elif s == 0 and t != 0:
                    score_only_ties += 1
                elif t == 0 and s != 0:
                    target_only_ties += 1
        checks["Pairwise_Accuracy"] = correct/eligible if eligible else np.nan
        denom = np.sqrt((concordant+discordant+score_only_ties)*(concordant+discordant+target_only_ties))
        checks["Kendall_Tau"] = (concordant-discordant)/denom if denom else np.nan
        for k in [5,10]:
            predicted = np.argsort(-score, kind="stable")[:k]
            actual = np.argsort(-target, kind="stable")[:k]
            checks[f"Hit_Rate_at_{k}"] = len(set(predicted)&set(actual))/k
        for name, value in checks.items():
            np.testing.assert_allclose(row[name], value, rtol=0, atol=1e-12, equal_nan=True)
            if np.isfinite(value):
                max_error = max(max_error, abs(row[name]-value))
        row_checks += 1
    summary_checks = 0
    for filename in ["overall_metrics.csv", "stage_metrics.csv", "annual_metrics.csv", "fold_metrics.csv", "refit_metrics.csv"]:
        frame = builder.read_csv(out/"metrics"/filename, ["start_date", "end_date"])
        for _, row in frame.iterrows():
            part = weekly[weekly.model.eq(row.model)&weekly.date.between(row.start_date,row.end_date)]
            assert len(part) == row.prediction_weeks and part.number_of_stocks.sum() == row.prediction_rows
            for column in checks:
                np.testing.assert_allclose(row[column], part[column].mean(), rtol=0, atol=1e-12, equal_nan=True)
            for name in ["IC", "Rank_IC"]:
                expected = part[name].mean()/part[name].std(ddof=1) if part[name].std(ddof=1)>0 else np.nan
                np.testing.assert_allclose(row[name+"IR"], expected, rtol=0, atol=1e-12, equal_nan=True)
            if len(part) < 8:
                assert np.isnan(row.Rank_IC_CI95_Lower) and np.isnan(row.Rank_IC_CI95_Upper)
            elif np.isfinite(part.Rank_IC).all():
                assert -1 <= row.Rank_IC_CI95_Lower <= row.Rank_IC_CI95_Upper <= 1
            summary_checks += 1
    csvs = list(out.rglob("*.csv"))
    for path in csvs:
        header = builder.read_csv(path).columns
        assert not any(word in column.lower() for column in header for word in builder.FORBIDDEN), path
    assert not any(word in str(p.relative_to(out)).lower() for p in out.rglob("*") for word in ["backtest", "strategy", "positions"])
    snapshot = builder.protected_snapshot()
    assert builder.snapshot_digest(snapshot) == manifest["protected_snapshot_sha256"]
    assert builder.sha256(source/"predictions/stock_rankings.csv") == manifest["source_predictions_sha256"]
    assert builder.sha256(builder.__file__) == manifest["builder_sha256"]
    result = {"status": "passed", "stock_week_rows": len(wide), "model_prediction_rows": len(long),
              "weekly_metric_rows_independently_recalculated": row_checks,
              "summary_rows_reconciled": summary_checks, "maximum_metric_error": max_error,
              "predictions_identical_to_source": True, "ranking_only_csv_schema_scan": "passed",
              "csv_files_checked": len(csvs), "protected_source_files_unchanged": True,
              "confidence_interval_bounds_and_minimum_sample_check": "passed",
              "checked_metric_methods": "manual tie-averaged DCG, explicit stock pairs, correlation of ranks, ranking-set overlap"}
    builder.write_json(out/"verification.json", result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    verify(parser.parse_args().output.resolve())
