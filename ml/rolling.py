"""Frozen-config monthly refits on the full eligible rolling three-year window."""

from __future__ import annotations

import json
import pandas as pd
from dateutil.relativedelta import relativedelta

from .config import DATA_END, ROLLING_START, TARGET_COLUMN, TRAIN_YEARS
from .data import observable_training_rows
from .metrics import aggregate_metrics, metrics_by_date
from .xgb_ranker import fit_ranker, predict_ranker


def refit_dates(prediction_dates) -> list[pd.Timestamp]:
    dates = pd.DatetimeIndex(sorted(pd.to_datetime(pd.Series(prediction_dates).unique())))
    result, last_period = [], None
    for date in dates:
        if date.to_period("M") != last_period:
            result.append(date); last_period = date.to_period("M")
    return result


def eligible_full_window(df, refit):
    """Return the full eligible 3-year history used by the final monthly fit."""
    refit = pd.Timestamp(refit)
    history = observable_training_rows(df, refit, refit - relativedelta(years=TRAIN_YEARS), inclusive=False)
    return history.loc[history[TARGET_COLUMN].notna()].copy()


def rolling_oos(df, features, factor_set_name, params, objective="rank:ndcg", n_bins=10):
    oos_panel = df.loc[df["date"].between(ROLLING_START, DATA_END)].copy()
    dates = pd.DatetimeIndex(sorted(oos_panel["date"].unique()))
    starts = refit_dates(dates)
    predictions, model_rows = [], []
    for index, refit in enumerate(starts):
        next_refit = starts[index + 1] if index + 1 < len(starts) else dates.max() + pd.Timedelta(days=1)
        history = eligible_full_window(df, refit)
        if history["date"].nunique() < 52:
            continue
        # Final OOS model uses every eligible observation; no validation holdout remains removed.
        model = fit_ranker(history, features, params, objective, n_bins)
        train_pred = predict_ranker(model, history, features, n_bins)
        period = oos_panel.loc[(oos_panel["date"] >= refit) & (oos_panel["date"] < next_refit)
                               & oos_panel[TARGET_COLUMN].notna()].copy()
        if period.empty:
            continue
        oos = predict_ranker(model, period, features, n_bins)
        model_id = f"xgbranker_{refit:%Y%m%d}"
        oos["model_id"], oos["factor_set_name"], oos["refit_date"] = model_id, factor_set_name, refit
        predictions.append(oos)
        train_metrics = aggregate_metrics(metrics_by_date(train_pred), "train_")
        oos_metrics = aggregate_metrics(metrics_by_date(oos), "oos_")
        row = {"model_id": model_id, "model_type": "XGBRanker", "refit_date": refit,
               "factor_set_name": factor_set_name, "number_of_features": len(features),
               "feature_list": json.dumps(features), "objective": objective,
               "n_relevance_bins": n_bins, "hyperparameters": json.dumps(params, sort_keys=True),
               "train_start": history["date"].min(), "train_end": history["date"].max(),
               "number_of_train_dates": history["date"].nunique(), "number_of_train_rows": len(history),
               **train_metrics, **oos_metrics}
        row["number_of_oos_dates"] = row["oos_number_of_dates"]
        row["prediction_score_std"] = row["oos_prediction_score_std"]
        row["train_oos_rank_ic_gap"] = row["train_mean_rank_ic"] - row["oos_mean_rank_ic"]
        model_rows.append(row)
    return (pd.concat(predictions, ignore_index=True) if predictions else pd.DataFrame(), pd.DataFrame(model_rows))
