import pandas as pd

from ml.rolling import refit_dates
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
