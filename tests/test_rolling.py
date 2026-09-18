import pandas as pd

from ml.rolling import eligible_full_window, refit_dates
from ml.validation import chronological_folds


def test_monthly_refit_and_weekly_predictions_between_refits():
    dates = pd.date_range("2024-01-05", periods=12, freq="W-FRI")
    refits = refit_dates(dates)
    assert len(refits) == 3
    assert len(dates) > len(refits)
    assert [d.month for d in refits] == [1, 2, 3]


def test_chronological_folds_keep_dates_whole_and_future_only():
    dates = pd.date_range("2018-01-05", periods=120, freq="W-FRI").repeat(3)
    folds = chronological_folds(dates, n_folds=2, min_train_weeks=52)
    for train, valid in folds:
        assert train.max() < valid.min()
        assert not set(train).intersection(valid)


def test_final_monthly_history_uses_full_eligible_three_year_window():
    dates = pd.date_range("2016-01-08", "2019-01-04", freq="W-FRI")
    df = pd.DataFrame({"date": dates, "target_observation_date": dates + pd.Timedelta(days=7),
                       "target_next_week_oc_return": 0.01})
    history = eligible_full_window(df, pd.Timestamp("2019-01-04"))
    assert history.date.min() >= pd.Timestamp("2016-01-04")
    assert history.date.max() == pd.Timestamp("2018-12-21")
    assert history.date.nunique() > 130  # recent 13 weeks were not removed
