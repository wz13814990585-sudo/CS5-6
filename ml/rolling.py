"""Monthly-refit, weekly-prediction rolling OOS engine."""

from __future__ import annotations

import json
import pandas as pd
from dateutil.relativedelta import relativedelta

from .config import FINAL_TEST_END, FINAL_TEST_START, TARGET_COLUMN, TRAIN_YEARS, VALIDATION_WEEKS
from .data import observable_training_rows
from .metrics import aggregate_metrics, metrics_by_date
from .xgb_ranker import fit_ranker, predict_ranker


def refit_dates(prediction_dates) -> list[pd.Timestamp]:
    dates = pd.DatetimeIndex(sorted(pd.to_datetime(pd.Series(prediction_dates).unique())))
    result, last_period = [], None
    for date in dates:
        period = date.to_period("M")
        if period != last_period:
            result.append(date); last_period = period
    return result


def rolling_oos(df, features, factor_set_name, params, objective="rank:ndcg", n_bins=10):
    test = df.loc[df["date"].between(FINAL_TEST_START, FINAL_TEST_END)].copy()
    dates = pd.DatetimeIndex(sorted(test["date"].unique()))
    starts = refit_dates(dates)
    predictions, model_rows = [], []
    for index, refit in enumerate(starts):
        next_refit = starts[index + 1] if index + 1 < len(starts) else dates.max() + pd.Timedelta(days=1)
        history = observable_training_rows(df, refit, refit - relativedelta(years=TRAIN_YEARS))
        history = history.loc[history[TARGET_COLUMN].notna()].copy()
        history_dates = pd.DatetimeIndex(sorted(history["date"].unique()))
        if len(history_dates) <= VALIDATION_WEEKS + 10:
            continue
        validation_dates = history_dates[-VALIDATION_WEEKS:]
        train = history.loc[history["date"] < validation_dates[0]]
        validation = history.loc[history["date"].isin(validation_dates)]
        model = fit_ranker(train, features, params, objective, n_bins)
        train_pred = predict_ranker(model, train, features, n_bins)
        val_pred = predict_ranker(model, validation, features, n_bins)
        period = test.loc[(test["date"] >= refit) & (test["date"] < next_refit) & test[TARGET_COLUMN].notna()]
        oos = predict_ranker(model, period, features, n_bins)
        model_id = f"{factor_set_name}_{refit:%Y%m%d}"
        oos["model_id"], oos["factor_set_name"], oos["refit_date"] = model_id, factor_set_name, refit
        predictions.append(oos)
        train_metrics = aggregate_metrics(metrics_by_date(train_pred), "train_")
        val_metrics = aggregate_metrics(metrics_by_date(val_pred), "validation_")
        oos_metrics = aggregate_metrics(metrics_by_date(oos), "oos_")
        row = {"model_id": model_id, "model_type": "XGBRanker", "objective": objective,
               "factor_set_name": factor_set_name, "refit_date": refit,
               "n_relevance_bins": n_bins,
               "train_start": train["date"].min(), "train_end": train["date"].max(),
               "validation_start": validation["date"].min(), "validation_end": validation["date"].max(),
               "number_of_train_dates": train["date"].nunique(), "number_of_train_rows": len(train),
               "number_of_validation_dates": validation["date"].nunique(), "number_of_validation_rows": len(validation),
               "number_of_features": len(features), "feature_list": json.dumps(features),
               "hyperparameters": json.dumps(params, sort_keys=True), **train_metrics, **val_metrics, **oos_metrics}
        row["train_validation_rank_ic_gap"] = row["train_mean_rank_ic"] - row["validation_mean_rank_ic"]
        row["train_oos_rank_ic_gap"] = row["train_mean_rank_ic"] - row["oos_mean_rank_ic"]
        # Keep the requested concise field names alongside the explicit rank-IC names.
        row["train_ic_std"] = row["train_rank_ic_std"]
        row["validation_ic_std"] = row["validation_rank_ic_std"]
        row["oos_ic_std"] = row["oos_rank_ic_std"]
        row["train_strong_validation_weak_flag"] = bool(
            row["train_mean_rank_ic"] > 0.10 and abs(row["validation_mean_rank_ic"]) < 0.01
        )
        model_rows.append(row)
    return (pd.concat(predictions, ignore_index=True) if predictions else pd.DataFrame(), pd.DataFrame(model_rows))
