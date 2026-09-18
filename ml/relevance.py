"""Date-local ordinal relevance labels for learning to rank."""

from __future__ import annotations

import numpy as np
import pandas as pd


def relevance_labels(values: pd.Series, n_bins: int = 10) -> pd.Series:
    """Deterministically map one cross-section to 0..n_bins-1."""
    result = pd.Series(pd.NA, index=values.index, dtype="Int64")
    valid = values.dropna()
    if valid.empty:
        return result
    # method='first' makes ties deterministic in the already stable row order.
    ranks = valid.rank(method="first").to_numpy() - 1
    labels = np.minimum((ranks * n_bins // len(valid)).astype(int), n_bins - 1)
    result.loc[valid.index] = labels
    return result


def add_relevance_by_date(df: pd.DataFrame, target: str, n_bins: int = 10) -> pd.DataFrame:
    out = df.copy()
    out["relevance_label"] = out.groupby("date", sort=False)[target].transform(
        lambda s: relevance_labels(s, n_bins)
    )
    return out
