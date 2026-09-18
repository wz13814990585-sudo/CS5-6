"""Chronological split helpers that keep complete weekly ranking groups together."""

from __future__ import annotations

import pandas as pd


def date_slice(df: pd.DataFrame, start, end) -> pd.DataFrame:
    return df.loc[df["date"].between(pd.Timestamp(start), pd.Timestamp(end))].copy()


def chronological_folds(dates, n_folds: int = 3, min_train_weeks: int = 52):
    unique = pd.DatetimeIndex(sorted(pd.to_datetime(pd.Series(dates).dropna().unique())))
    if len(unique) <= min_train_weeks + n_folds:
        return []
    remaining = len(unique) - min_train_weeks
    block = max(1, remaining // n_folds)
    folds = []
    for i in range(n_folds):
        valid_start = min_train_weeks + i * block
        valid_end = len(unique) if i == n_folds - 1 else min_train_weeks + (i + 1) * block
        if valid_start < valid_end:
            folds.append((unique[:valid_start], unique[valid_start:valid_end]))
    return folds


def assert_disjoint_dates(train: pd.DataFrame, validation: pd.DataFrame) -> None:
    overlap = set(train["date"]).intersection(validation["date"])
    if overlap:
        raise ValueError(f"Dates split across train/validation: {sorted(overlap)[:3]}")
