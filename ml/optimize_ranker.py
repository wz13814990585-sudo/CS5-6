"""Warmup-only chronological search; no post-warmup row is inspected here."""

from __future__ import annotations

import json
import numpy as np
import pandas as pd

from .config import (
    OBJECTIVE_CANDIDATES, RELEVANCE_BIN_CANDIDATES, TARGET_COLUMN,
    WARMUP_CV_FOLDS, WARMUP_END, WARMUP_START, XGB_RANKER_PARAM_CANDIDATES,
)
from .metrics import aggregate_metrics, metrics_by_date
from .validation import chronological_folds
from .xgb_ranker import fit_ranker, predict_ranker


def common_sample_panel(warmup: pd.DataFrame, factor_sets: dict[str, list[str]]) -> pd.DataFrame:
    mask = warmup[TARGET_COLUMN].notna()
    for features in factor_sets.values():
        mask &= warmup[features].notna().any(axis=1)
    return warmup.loc[mask].copy()


def _cv_predictions(data, features, params, objective, bins):
    pieces = []
    folds = chronological_folds(data["date"], n_folds=WARMUP_CV_FOLDS, min_train_weeks=52)
    for fold_id, (train_dates, valid_dates) in enumerate(folds, 1):
        valid_start = valid_dates.min()
        train = data.loc[data["date"].isin(train_dates) & (data["target_observation_date"] < valid_start)]
        valid = data.loc[data["date"].isin(valid_dates)]
        model = fit_ranker(train, features, params, objective, bins)
        pred = predict_ranker(model, valid, features, bins)
        pred["fold_id"] = fold_id
        pieces.append(pred)
    return pd.concat(pieces, ignore_index=True)


def warmup_ranker_search(data, factor_sets, sample_mode="common_sample") -> pd.DataFrame:
    warmup = data.loc[data["date"].between(WARMUP_START, WARMUP_END)].copy()
    panel = common_sample_panel(warmup, factor_sets) if sample_mode == "common_sample" else warmup
    rows, total, count = [], len(factor_sets) * len(OBJECTIVE_CANDIDATES) * len(RELEVANCE_BIN_CANDIDATES) * len(XGB_RANKER_PARAM_CANDIDATES), 0
    for name, features in factor_sets.items():
        for objective in OBJECTIVE_CANDIDATES:
            for bins in RELEVANCE_BIN_CANDIDATES:
                for param_id, params in enumerate(XGB_RANKER_PARAM_CANDIDATES):
                    count += 1
                    if count == 1 or count % 20 == 0:
                        print(f"  warmup search {count}/{total}: {name}, {objective}, bins={bins}", flush=True)
                    predictions = _cv_predictions(panel, features, params, objective, bins)
                    metrics = aggregate_metrics(metrics_by_date(predictions), "cv_")
                    rows.append({"factor_set_name": name, "number_of_features": len(features),
                                 "feature_list": json.dumps(features), "sample_mode": sample_mode,
                                 "objective": objective, "n_relevance_bins": bins, "param_id": param_id,
                                 "hyperparameters": json.dumps(params, sort_keys=True), **metrics})
    return pd.DataFrame(rows).sort_values(
        ["cv_mean_rank_ic", "cv_icir", "cv_ndcg5", "cv_top5_bottom5_spread"],
        ascending=False, kind="stable").reset_index(drop=True)


def best_per_factor_set(search: pd.DataFrame) -> pd.DataFrame:
    ordered = search.sort_values(
        ["cv_mean_rank_ic", "cv_icir", "cv_ndcg5", "cv_top5_bottom5_spread"],
        ascending=False, kind="stable")
    return ordered.drop_duplicates(["factor_set_name", "sample_mode"]).reset_index(drop=True)


def native_results_for_common_winners(data, factor_sets, common_search):
    """Secondary native-coverage evaluation without changing common-sample selection."""
    warmup = data.loc[data["date"].between(WARMUP_START, WARMUP_END)].copy()
    rows = []
    for _, winner in best_per_factor_set(common_search).iterrows():
        features = factor_sets[winner.factor_set_name]
        predictions = _cv_predictions(warmup, features, json.loads(winner.hyperparameters),
                                      winner.objective, int(winner.n_relevance_bins))
        rows.append({"factor_set_name": winner.factor_set_name, "number_of_features": len(features),
                     "feature_list": json.dumps(features), "sample_mode": "native_coverage",
                     "objective": winner.objective, "n_relevance_bins": int(winner.n_relevance_bins),
                     "param_id": int(winner.param_id), "hyperparameters": winner.hyperparameters,
                     **aggregate_metrics(metrics_by_date(predictions), "cv_")})
    return pd.DataFrame(rows)


def frozen_config(best: pd.Series) -> dict:
    return {"warmup_start": WARMUP_START, "warmup_end": WARMUP_END,
            "factor_set_name": best.factor_set_name, "feature_list": json.loads(best.feature_list),
            "objective": best.objective, "n_relevance_bins": int(best.n_relevance_bins),
            "hyperparameters": json.loads(best.hyperparameters),
            "selection_metric": "warmup chronological CV mean weekly Rank IC",
            "warmup_cv_metrics": {key.removeprefix("cv_"): (None if pd.isna(value) else float(value))
                                  for key, value in best.items() if key.startswith("cv_")},
            "post_warmup_data_used_for_selection": False}
