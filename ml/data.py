"""Weekly panel loading, exact-week target construction, and leakage guards."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import FORBIDDEN_FEATURE_COLUMNS, TARGET_COLUMN, TARGET_OBSERVATION_DATE


def load_weekly_panel(path) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.normalize()
    df["ticker"] = df["ticker"].astype("string")
    df = df.dropna(subset=["date", "ticker"]).copy()
    if df.duplicated(["date", "ticker"]).any():
        raise ValueError("date+ticker must be unique")
    for column in df.columns.difference(["date", "ticker"]):
        df[column] = pd.to_numeric(df[column], errors="coerce")
    return df.sort_values(["ticker", "date"], kind="stable").reset_index(drop=True)


def add_exact_week_targets(df: pd.DataFrame) -> pd.DataFrame:
    """Add exact market-week targets; a missing k+1 row never jumps to k+2."""
    required = {"date", "ticker", "open", "close", "adj_close"}
    if missing := required.difference(df.columns):
        raise ValueError(f"Missing target inputs: {sorted(missing)}")
    out = df.copy()
    weeks = pd.DatetimeIndex(sorted(out["date"].dropna().unique()))
    out["week_id"] = pd.Categorical(out["date"], categories=weeks, ordered=True).codes
    close = out["close"].to_numpy(float)
    adj_close = out["adj_close"].to_numpy(float)
    open_ = out["open"].to_numpy(float)
    good = np.isfinite(open_) & np.isfinite(close) & np.isfinite(adj_close) & (open_ > 0) & (close > 0) & (adj_close > 0)
    out["adj_open_calc"] = np.where(good, open_ * adj_close / close, np.nan)
    keyed = out.set_index(["ticker", "week_id"])
    for horizon, name in [(1, "fwd_1w_close_to_close"), (4, "fwd_4w_close_to_close"), (12, "fwd_12w_close_to_close")]:
        keys = pd.MultiIndex.from_arrays([out["ticker"], out["week_id"] + horizon], names=["ticker", "week_id"])
        future = keyed["adj_close"].reindex(keys).to_numpy(float)
        valid = np.isfinite(adj_close) & np.isfinite(future) & (adj_close > 0) & (future > 0)
        out[name] = np.where(valid, np.log(future / adj_close), np.nan)
    next_keys = pd.MultiIndex.from_arrays([out["ticker"], out["week_id"] + 1], names=["ticker", "week_id"])
    next_rows = keyed[["date", "open", "close", "adj_close", "adj_open_calc"]].reindex(next_keys)
    future_adj_close = next_rows["adj_close"].to_numpy(float)
    future_adj_open = next_rows["adj_open_calc"].to_numpy(float)
    valid = np.isfinite(future_adj_close) & np.isfinite(future_adj_open) & (future_adj_close > 0) & (future_adj_open > 0)
    out[TARGET_COLUMN] = np.where(valid, np.log(future_adj_close / future_adj_open), np.nan)
    out[TARGET_OBSERVATION_DATE] = pd.to_datetime(next_rows["date"].to_numpy())
    return out


def validate_feature_columns(features: list[str], available: list[str] | pd.Index) -> None:
    if len(features) != len(set(features)):
        raise ValueError("Feature list contains duplicates")
    missing = set(features).difference(available)
    forbidden = set(features).intersection(FORBIDDEN_FEATURE_COLUMNS)
    future_like = {c for c in features if c.startswith(("next_", "future_", "fwd_", "target_"))}
    if missing or forbidden or future_like:
        raise ValueError(f"Invalid features: missing={sorted(missing)}, forbidden={sorted(forbidden | future_like)}")


def observable_training_rows(df: pd.DataFrame, prediction_date, start_date=None) -> pd.DataFrame:
    prediction_date = pd.Timestamp(prediction_date)
    mask = df[TARGET_OBSERVATION_DATE].notna() & (df[TARGET_OBSERVATION_DATE] <= prediction_date)
    mask &= df["date"] < prediction_date
    if start_date is not None:
        mask &= df["date"] >= pd.Timestamp(start_date)
    return df.loc[mask].copy()


def manual_target_samples(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    valid = df.loc[df[TARGET_COLUMN].notna()].sort_values(["date", "ticker"])
    if valid.empty:
        return pd.DataFrame()
    picks = valid.iloc[np.linspace(0, len(valid) - 1, min(n, len(valid)), dtype=int)]
    keyed = df.set_index(["ticker", "week_id"])
    rows = []
    for row in picks.itertuples():
        nxt = keyed.loc[(row.ticker, row.week_id + 1)]
        adj_open = nxt.open * nxt.adj_close / nxt.close
        manual = np.log(nxt.adj_close / adj_open)
        rows.append({"date": row.date, "ticker": row.ticker, "current_week_id": row.week_id,
                     "next_week_date": nxt.date, "next_week_open": nxt.open, "next_week_close": nxt.close,
                     "next_week_adj_close": nxt.adj_close, "calculated_adj_open": adj_open,
                     "calculated_target": getattr(row, TARGET_COLUMN), "manually_recomputed_target": manual})
    return pd.DataFrame(rows)
