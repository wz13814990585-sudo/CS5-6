import numpy as np
import pandas as pd

from ml.config import TARGET_COLUMN
from ml.data import (add_exact_week_targets, build_market_week_calendar,
                     build_weekly_return_table, exclude_incomplete_terminal_week)


def daily_panel():
    rows = []
    # Decision week ends Friday Jan 3.
    rows.append(("2020-01-03", "A", 9, 10, 5))
    rows.append(("2020-01-03", "B", 4, 5, 10))
    # Normal next week: Monday open through Friday close for A only.
    rows += [("2020-01-06", "A", 10, 10.5, 5.25), ("2020-01-10", "A", 11, 12, 6)]
    # B is absent from exact next week and reappears in t+2.
    rows += [("2020-01-13", "B", 8, 9, 18), ("2020-01-17", "B", 9, 10, 20)]
    df = pd.DataFrame(rows, columns=["date", "ticker", "open", "close", "adj_close"])
    df["date"] = pd.to_datetime(df.date); df["high"] = df[["open", "close"]].max(axis=1)
    df["low"] = df[["open", "close"]].min(axis=1); df["volume"] = 100
    return df


def x_panel(daily):
    cal = build_market_week_calendar(daily)
    rows = pd.DataFrame({"date": pd.to_datetime(["2020-01-03", "2020-01-03", "2020-01-10", "2020-01-17"]),
                         "ticker": ["A", "B", "A", "B"], "factor": [1, 2, 3, 4]})
    return rows.merge(cal[["decision_date", "market_week_id"]], left_on="date", right_on="decision_date")


def test_normal_week_uses_monday_adjusted_open_and_friday_adjusted_close():
    daily = daily_panel(); out = add_exact_week_targets(x_panel(daily), daily)
    row = out[(out.ticker == "A") & (out.market_week_id == 0)].iloc[0]
    monday_adj_open = 10 * 5.25 / 10.5
    assert row.target_week_first_date == pd.Timestamp("2020-01-06")
    assert row.target_week_last_date == pd.Timestamp("2020-01-10")
    assert np.isclose(row.target_week_first_adj_open, monday_adj_open)
    assert np.isclose(row[TARGET_COLUMN], np.log(6 / monday_adj_open))
    assert row.target_observation_date == pd.Timestamp("2020-01-10")


def test_missing_exact_week_does_not_jump_or_cross_tickers():
    daily = daily_panel(); out = add_exact_week_targets(x_panel(daily), daily)
    b0 = out[(out.ticker == "B") & (out.market_week_id == 0)].iloc[0]
    assert np.isnan(b0[TARGET_COLUMN]) and pd.isna(b0.target_observation_date)


def test_holiday_tuesday_friday_and_monday_thursday_weeks():
    daily = pd.DataFrame({
        "date": pd.to_datetime(["2020-01-07", "2020-01-10", "2020-01-13", "2020-01-16"]),
        "ticker": ["A"]*4, "open": [10, 11, 20, 21], "close": [10, 12, 20, 22],
        "adj_close": [10, 12, 20, 22], "high": [10, 12, 20, 22], "low": [10, 11, 20, 21], "volume": [1]*4})
    table = build_weekly_return_table(daily)
    first, second = table.iloc[0], table.iloc[1]
    assert first.week_first_date == pd.Timestamp("2020-01-07") and first.week_last_date == pd.Timestamp("2020-01-10")
    assert second.week_first_date == pd.Timestamp("2020-01-13") and second.week_last_date == pd.Timestamp("2020-01-16")
    assert np.isclose(first.weekly_oc_return, np.log(12/10))
    assert np.isclose(second.weekly_oc_return, np.log(22/20))


def test_common_market_decision_date_and_terminal_completeness():
    daily = daily_panel(); calendar = build_market_week_calendar(daily)
    assert calendar.decision_date.is_unique
    raw = pd.DataFrame({"date": pd.to_datetime(["2026-08-28", "2026-08-31"]), "ticker": ["A", "A"]})
    assert exclude_incomplete_terminal_week(raw).date.tolist() == [pd.Timestamp("2026-08-28")]
    thursday = pd.DataFrame({"date": pd.to_datetime(["2026-04-02"]), "ticker": ["A"]})
    assert len(exclude_incomplete_terminal_week(thursday)) == 1


def test_final_complete_week_has_no_next_week_target():
    daily = daily_panel(); out = add_exact_week_targets(x_panel(daily), daily)
    assert out.loc[out.market_week_id == out.market_week_id.max(), TARGET_COLUMN].isna().all()
