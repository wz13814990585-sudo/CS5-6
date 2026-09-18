"""Date-first ranking metrics. No pooled/global Rank IC is reported."""

from __future__ import annotations

import math
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import ndcg_score


DATE_METRIC_COLUMNS = [
    "date", "rank_ic", "ndcg5", "ndcg10", "ndcg20", "top5_return", "top10_return",
    "bottom5_return", "bottom10_return", "top5_bottom5_spread", "top10_bottom10_spread",
    "top5_hit_rate", "number_of_stocks", "prediction_score_std",
]


def metrics_for_date(group: pd.DataFrame) -> dict:
    g = group.dropna(subset=["ranking_score", "actual_return"]).sort_values(
        ["ranking_score", "ticker"], ascending=[False, True], kind="stable"
    )
    n = len(g)
    base = {key: np.nan for key in DATE_METRIC_COLUMNS}
    base.update({"date": group["date"].iloc[0], "number_of_stocks": n})
    if n == 0:
        return base
    base["prediction_score_std"] = g["ranking_score"].std(ddof=0)
    if n >= 2 and g["ranking_score"].nunique() > 1 and g["actual_return"].nunique() > 1:
        base["rank_ic"] = float(spearmanr(g["ranking_score"], g["actual_return"]).statistic)
    relevance = g["relevance_label"].astype(float).to_numpy()[None, :]
    scores = g["ranking_score"].to_numpy()[None, :]
    for k in (5, 10, 20):
        base[f"ndcg{k}"] = float(ndcg_score(relevance, scores, k=min(k, n))) if n >= 2 else np.nan
    for k in (5, 10):
        if n >= 2 * k:
            top = g.head(k)["actual_return"]
            bottom = g.tail(k)["actual_return"]
            base[f"top{k}_return"] = top.mean()
            base[f"bottom{k}_return"] = bottom.mean()
            base[f"top{k}_bottom{k}_spread"] = top.mean() - bottom.mean()
            if k == 5:
                base["top5_hit_rate"] = (top > 0).mean()
    return base


def metrics_by_date(predictions: pd.DataFrame) -> pd.DataFrame:
    if predictions.empty:
        return pd.DataFrame(columns=DATE_METRIC_COLUMNS)
    return pd.DataFrame([metrics_for_date(g) for _, g in predictions.groupby("date", sort=True)])


def aggregate_metrics(by_date: pd.DataFrame, prefix: str = "") -> dict:
    ic = by_date["rank_ic"].dropna() if "rank_ic" in by_date else pd.Series(dtype=float)
    mean_ic = ic.mean() if len(ic) else np.nan
    std_ic = ic.std(ddof=1) if len(ic) > 1 else np.nan
    values = {
        "mean_rank_ic": mean_ic, "median_rank_ic": ic.median() if len(ic) else np.nan,
        "rank_ic_std": std_ic, "positive_ic_ratio": (ic > 0).mean() if len(ic) else np.nan,
        "negative_ic_ratio": (ic < 0).mean() if len(ic) else np.nan,
        "icir": mean_ic / std_ic if np.isfinite(std_ic) and std_ic else np.nan,
        "annualized_icir": mean_ic / std_ic * math.sqrt(52) if np.isfinite(std_ic) and std_ic else np.nan,
        "ndcg5": by_date["ndcg5"].mean() if len(by_date) else np.nan,
        "ndcg10": by_date["ndcg10"].mean() if len(by_date) else np.nan,
        "ndcg20": by_date["ndcg20"].mean() if len(by_date) else np.nan,
        "top5_return": by_date["top5_return"].mean() if len(by_date) else np.nan,
        "top10_return": by_date["top10_return"].mean() if len(by_date) else np.nan,
        "top5_bottom5_spread": by_date["top5_bottom5_spread"].mean() if len(by_date) else np.nan,
        "top10_bottom10_spread": by_date["top10_bottom10_spread"].mean() if len(by_date) else np.nan,
        "number_of_dates": len(ic),
    }
    return {f"{prefix}{key}": value for key, value in values.items()}


def yearly_metrics(by_date: pd.DataFrame) -> pd.DataFrame:
    if by_date.empty:
        return pd.DataFrame()
    work = by_date.copy()
    work["year"] = pd.to_datetime(work["date"]).dt.year
    rows = []
    for year, group in work.groupby("year"):
        row = {"year": year, **aggregate_metrics(group)}
        rows.append(row)
    result = pd.DataFrame(rows)
    return result.rename(columns={"ndcg5": "mean_ndcg5", "ndcg10": "mean_ndcg10",
                                  "ndcg20": "mean_ndcg20", "top5_return": "mean_top5_return",
                                  "top10_return": "mean_top10_return",
                                  "top5_bottom5_spread": "mean_top5_bottom5_spread",
                                  "top10_bottom10_spread": "mean_top10_bottom10_spread"})
