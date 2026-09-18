"""Thin, deterministic XGBRanker adapter with date query groups."""

from __future__ import annotations

import numpy as np
import pandas as pd
from xgboost import XGBRanker

from .config import N_RELEVANCE_BINS, RANDOM_STATE, TARGET_COLUMN
from .data import validate_feature_columns
from .relevance import add_relevance_by_date


def prepare_rank_data(df: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    validate_feature_columns(features, df.columns)
    work = df.dropna(subset=[TARGET_COLUMN]).sort_values(["date", "ticker"], kind="stable").reset_index(drop=True).copy()
    work = work.loc[work[features].notna().any(axis=1)].copy()
    return add_relevance_by_date(work, TARGET_COLUMN, N_RELEVANCE_BINS)


def group_sizes(df: pd.DataFrame) -> list[int]:
    ordered = df.sort_values(["date", "ticker"], kind="stable")
    return ordered.groupby("date", sort=False).size().astype(int).tolist()


def fit_ranker(df: pd.DataFrame, features: list[str], params: dict, objective: str = "rank:ndcg") -> XGBRanker:
    work = prepare_rank_data(df, features)
    if work["date"].nunique() < 2:
        raise ValueError("At least two complete date groups are required")
    model = XGBRanker(objective=objective, random_state=RANDOM_STATE, tree_method="hist",
                      eval_metric="ndcg", n_jobs=-1, **params)
    model.fit(work[features], work["relevance_label"].astype(int), group=group_sizes(work), verbose=False)
    return model


def predict_ranker(model: XGBRanker, df: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    work = df.loc[df[features].notna().any(axis=1)].sort_values(["date", "ticker"], kind="stable").copy()
    work["ranking_score"] = model.predict(work[features])
    work["predicted_rank"] = work.groupby("date")["ranking_score"].rank(method="first", ascending=False).astype(int)
    work["actual_return"] = work[TARGET_COLUMN]
    if "relevance_label" not in work:
        work = add_relevance_by_date(work, TARGET_COLUMN, N_RELEVANCE_BINS)
    work["actual_rank"] = work.groupby("date")["actual_return"].rank(method="first", ascending=False)
    return work
