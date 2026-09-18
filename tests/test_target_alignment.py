import numpy as np
import pandas as pd

from ml.config import TARGET_COLUMN
from ml.data import add_exact_week_targets


def panel():
    return pd.DataFrame({
        "date": pd.to_datetime(["2020-01-03", "2020-01-10", "2020-01-17", "2020-01-03", "2020-01-17"]),
        "ticker": ["A", "A", "A", "B", "B"], "open": [9, 10, 20, 4, 8],
        "close": [10, 11, 18, 5, 10], "adj_close": [4.5, 5.5, 9, 10, 20],
    })


def test_exact_next_week_adjusted_open_and_target():
    out = add_exact_week_targets(panel())
    row = out[(out.ticker == "A") & (out.week_id == 0)].iloc[0]
    expected_open = 10 * 5.5 / 11
    assert np.isclose(row[TARGET_COLUMN], np.log(5.5 / expected_open))
    assert not np.isclose(row[TARGET_COLUMN], np.log(5.5 / 4.5))
    assert row.target_observation_date == pd.Timestamp("2020-01-10")


def test_missing_exact_week_does_not_jump_or_cross_tickers():
    out = add_exact_week_targets(panel())
    b0 = out[(out.ticker == "B") & (out.week_id == 0)].iloc[0]
    assert np.isnan(b0[TARGET_COLUMN])
    assert pd.isna(b0.target_observation_date)


def test_final_week_target_missing_and_valid_targets_finite():
    out = add_exact_week_targets(panel())
    assert out.loc[out.week_id == 2, TARGET_COLUMN].isna().all()
    assert np.isfinite(out[TARGET_COLUMN].dropna()).all()


def test_adjusted_open_formula():
    out = add_exact_week_targets(panel())
    np.testing.assert_allclose(out.adj_open_calc, out.open * out.adj_close / out.close)
