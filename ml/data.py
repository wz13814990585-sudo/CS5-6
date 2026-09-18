"""Common weekly snapshots and exact full-next-week targets built from daily data."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import DAILY_DATA_FILE, FORBIDDEN_FEATURE_COLUMNS, TARGET_COLUMN, TARGET_OBSERVATION_DATE


def load_daily_prices(path=DAILY_DATA_FILE) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.normalize()
    df["ticker"] = df["ticker"].astype("string")
    numeric = ["open", "high", "low", "close", "adj_close", "volume"]
    df[numeric] = df[numeric].apply(pd.to_numeric, errors="coerce")
    df = df.dropna(subset=["date", "ticker", "open", "close", "adj_close"])
    if df.duplicated(["date", "ticker"]).any():
        raise ValueError("Daily date+ticker must be unique")
    return df.sort_values(["ticker", "date"], kind="stable").reset_index(drop=True)


def build_market_week_calendar(daily: pd.DataFrame) -> pd.DataFrame:
    """Shared market calendar with one actual final session per complete W-FRI week."""
    dates = pd.DataFrame({"session_date": pd.DatetimeIndex(sorted(daily["date"].unique()))})
    dates["market_week"] = dates["session_date"].dt.to_period("W-FRI")
    calendar = dates.groupby("market_week", as_index=False).agg(
        week_first_market_date=("session_date", "min"), decision_date=("session_date", "max"),
        market_sessions=("session_date", "size"),
    ).sort_values("market_week").reset_index(drop=True)
    # A download ending Mon-Wed cannot establish that week's actual final market session.
    if len(calendar):
        last = calendar.iloc[-1]
        if last.decision_date < last.market_week.end_time.normalize() and last.decision_date.weekday() <= 2:
            calendar = calendar.iloc[:-1].copy()
    calendar["market_week_id"] = np.arange(len(calendar), dtype=int)
    return calendar


def exclude_incomplete_terminal_week(df: pd.DataFrame) -> pd.DataFrame:
    """Compatibility helper used by focused tests and external callers."""
    if df.empty:
        return df.copy()
    latest = pd.Timestamp(df["date"].max()).normalize()
    period = latest.to_period("W-FRI")
    if latest < period.end_time.normalize() and latest.weekday() <= 2:
        return df.loc[df["date"].dt.to_period("W-FRI") != period].copy().reset_index(drop=True)
    return df.copy()


def build_weekly_return_table(daily: pd.DataFrame, calendar: pd.DataFrame | None = None) -> pd.DataFrame:
    """Per-ticker full-week first adjusted open to last adjusted close."""
    calendar = build_market_week_calendar(daily) if calendar is None else calendar
    work = daily.copy()
    work["market_week"] = work["date"].dt.to_period("W-FRI")
    work = work.merge(calendar[["market_week", "market_week_id"]], on="market_week", how="inner", validate="many_to_one")
    work["adjusted_open"] = work["open"] * work["adj_close"] / work["close"]
    work = work.sort_values(["ticker", "market_week_id", "date"], kind="stable")
    first = work.groupby(["ticker", "market_week_id"], as_index=False).first()
    last = work.groupby(["ticker", "market_week_id"], as_index=False).last()
    result = first[["ticker", "market_week_id", "date", "open", "adjusted_open"]].rename(columns={
        "date": "week_first_date", "open": "week_first_open", "adjusted_open": "week_adj_open"})
    result = result.merge(
        last[["ticker", "market_week_id", "date", "close", "adj_close"]].rename(columns={
            "date": "week_last_date", "close": "week_last_close", "adj_close": "week_adj_close"}),
        on=["ticker", "market_week_id"], validate="one_to_one")
    valid = (result.week_adj_open > 0) & (result.week_adj_close > 0)
    result["weekly_oc_return"] = np.where(valid, np.log(result.week_adj_close / result.week_adj_open), np.nan)
    return result


def _read_weekly_factors(path) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.normalize()
    df["ticker"] = df["ticker"].astype("string")
    for column in df.columns.difference(["date", "ticker"]):
        df[column] = pd.to_numeric(df[column], errors="coerce")
    if df.duplicated(["date", "ticker"]).any():
        raise ValueError("Weekly date+ticker must be unique")
    return df


def load_weekly_panel(path, daily_path=DAILY_DATA_FILE) -> pd.DataFrame:
    """Keep factor rows only on each week's shared market decision date."""
    factors, daily = _read_weekly_factors(path), load_daily_prices(daily_path)
    calendar = build_market_week_calendar(daily)
    panel = factors.merge(calendar[["decision_date", "market_week_id"]], left_on="date", right_on="decision_date",
                          how="inner", validate="many_to_one")
    panel["date"] = panel["decision_date"]  # canonical internal grouping alias
    return panel.sort_values(["ticker", "date"], kind="stable").reset_index(drop=True)


def add_exact_week_targets(df: pd.DataFrame, daily_prices: pd.DataFrame | None = None) -> pd.DataFrame:
    """Merge week-t X with exact week-(t+1) full-week return; never jump weeks."""
    daily = load_daily_prices() if daily_prices is None else daily_prices.copy()
    calendar = build_market_week_calendar(daily)
    returns = build_weekly_return_table(daily, calendar)
    out = df.copy()
    if "market_week_id" not in out:
        out = out.merge(calendar[["decision_date", "market_week_id"]], left_on="date", right_on="decision_date",
                        how="inner", validate="many_to_one")
    out["week_id"] = out["market_week_id"]
    target = returns.rename(columns={
        "market_week_id": "target_week_id", "week_first_date": "target_week_first_date",
        "week_last_date": "target_week_last_date", "week_first_open": "target_week_first_open",
        "week_last_close": "target_week_last_close", "week_adj_open": "target_week_first_adj_open",
        "week_adj_close": "target_week_last_adj_close", "weekly_oc_return": TARGET_COLUMN,
    })
    out["target_week_id"] = out["market_week_id"] + 1
    out = out.merge(target, on=["ticker", "target_week_id"], how="left", validate="many_to_one")
    out[TARGET_OBSERVATION_DATE] = out["target_week_last_date"]
    # Close-to-close diagnostics use exact week IDs from the same daily table.
    current = returns[["ticker", "market_week_id", "week_adj_close"]]
    out = out.merge(current.rename(columns={"week_adj_close": "_current_week_adj_close"}),
                    on=["ticker", "market_week_id"], how="left", validate="many_to_one")
    for horizon in (1, 4, 12):
        future = current.rename(columns={"market_week_id": "_future_week_id", "week_adj_close": "_future_close"})
        out["_future_week_id"] = out["market_week_id"] + horizon
        out = out.merge(future, left_on=["ticker", "_future_week_id"], right_on=["ticker", "_future_week_id"],
                        how="left", validate="many_to_one")
        out[f"fwd_{horizon}w_close_to_close"] = np.log(out["_future_close"] / out["_current_week_adj_close"])
        out = out.drop(columns=["_future_close"])
    return out.drop(columns=["_current_week_adj_close", "_future_week_id"])


def validate_feature_columns(features: list[str], available) -> None:
    if len(features) != len(set(features)):
        raise ValueError("Feature list contains duplicates")
    missing = set(features).difference(available)
    forbidden = set(features).intersection(FORBIDDEN_FEATURE_COLUMNS)
    future_like = {c for c in features if c.startswith(("next_", "future_", "fwd_", "target_"))}
    if missing or forbidden or future_like:
        raise ValueError(f"Invalid features: missing={sorted(missing)}, forbidden={sorted(forbidden | future_like)}")


def observable_training_rows(df, prediction_date, start_date=None, inclusive=False):
    prediction_date = pd.Timestamp(prediction_date)
    observed = df[TARGET_OBSERVATION_DATE] <= prediction_date if inclusive else df[TARGET_OBSERVATION_DATE] < prediction_date
    mask = df[TARGET_OBSERVATION_DATE].notna() & observed & (df["date"] < prediction_date)
    if start_date is not None:
        mask &= df["date"] >= pd.Timestamp(start_date)
    return df.loc[mask].copy()


def manual_target_samples(df: pd.DataFrame, n: int = 20) -> pd.DataFrame:
    valid = df.loc[df[TARGET_COLUMN].notna()].sort_values(["date", "ticker"])
    picks = valid.iloc[np.linspace(0, len(valid) - 1, min(n, len(valid)), dtype=int)]
    rows = []
    for row in picks.itertuples():
        manual = np.log(row.target_week_last_adj_close / row.target_week_first_adj_open)
        rows.append({"decision_date": row.decision_date, "ticker": row.ticker,
                     "decision_week_id": row.market_week_id, "target_week_id": row.target_week_id,
                     "target_week_first_date": row.target_week_first_date,
                     "target_week_last_date": row.target_week_last_date,
                     "target_week_first_open": row.target_week_first_open,
                     "target_week_last_close": row.target_week_last_close,
                     "target_week_first_adj_open": row.target_week_first_adj_open,
                     "target_week_last_adj_close": row.target_week_last_adj_close,
                     "calculated_target": getattr(row, TARGET_COLUMN), "manual_target": manual})
    return pd.DataFrame(rows)
