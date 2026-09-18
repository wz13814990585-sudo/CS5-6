"""Development-only model-based forward factor selection."""

from __future__ import annotations

import pandas as pd

from .config import MAX_FORWARD_FACTORS, MIN_RANK_IC_IMPROVEMENT, TARGET_COLUMN
from .metrics import aggregate_metrics, metrics_by_date
from .validation import chronological_folds
from .xgb_ranker import fit_ranker, predict_ranker


def _cross_validated_metrics(df, features, params, objective):
    outputs = []
    for train_dates, valid_dates in chronological_folds(df["date"], n_folds=3, min_train_weeks=78):
        train = df[df["date"].isin(train_dates) & (df["target_observation_date"] < valid_dates.min())]
        valid = df[df["date"].isin(valid_dates)]
        model = fit_ranker(train, features, params, objective)
        outputs.append(predict_ranker(model, valid, features))
    if not outputs:
        return aggregate_metrics(pd.DataFrame())
    return aggregate_metrics(metrics_by_date(pd.concat(outputs, ignore_index=True)))


def forward_select(development, candidates, params, objective="rank:ndcg", max_factors=MAX_FORWARD_FACTORS):
    selected, rows, previous = [], [], float("-inf")
    for step in range(1, min(max_factors, len(candidates)) + 1):
        trials = []
        for candidate in candidates:
            if candidate in selected: continue
            metrics = _cross_validated_metrics(development.dropna(subset=[TARGET_COLUMN]), selected + [candidate], params, objective)
            trials.append((candidate, metrics))
        if not trials: break
        trials.sort(key=lambda item: (-item[1]["mean_rank_ic"] if pd.notna(item[1]["mean_rank_ic"]) else float("inf"), item[0]))
        best, best_metrics = trials[0]
        improvement = best_metrics["mean_rank_ic"] - previous if previous != float("-inf") else best_metrics["mean_rank_ic"]
        accept = step == 1 or improvement >= MIN_RANK_IC_IMPROVEMENT
        for candidate, metrics in trials:
            rows.append({"step": step, "current_factor_set": ";".join(selected), "candidate_factor": candidate,
                         "candidate_mean_rank_ic": metrics["mean_rank_ic"], "candidate_icir": metrics["icir"],
                         "candidate_ndcg5": metrics["ndcg5"], "candidate_top5_bottom5_spread": metrics["top5_bottom5_spread"],
                         "delta_rank_ic": metrics["mean_rank_ic"] - previous if previous != float("-inf") else metrics["mean_rank_ic"],
                         "delta_icir": metrics["icir"], "selected": accept and candidate == best,
                         "reason": "best robust development-fold improvement" if accept and candidate == best else "not selected"})
        if not accept: break
        selected.append(best); previous = best_metrics["mean_rank_ic"]
    return selected, pd.DataFrame(rows)
