import pandas as pd

from ml.config import ROLLING_START, WARMUP_END, WARMUP_START
from ml.validation import chronological_folds


def test_warmup_is_first_three_complete_model_years():
    assert pd.Timestamp(WARMUP_START) == pd.Timestamp("2016-01-01")
    assert pd.Timestamp(WARMUP_END) == pd.Timestamp("2018-12-31")
    assert pd.Timestamp(ROLLING_START) == pd.Timestamp("2019-01-01")


def test_warmup_cv_never_reads_post_warmup_dates():
    dates = pd.date_range(WARMUP_START, WARMUP_END, freq="W-FRI")
    for train, valid in chronological_folds(dates, n_folds=3, min_train_weeks=52):
        assert train.max() < valid.min()
        assert valid.max() <= pd.Timestamp(WARMUP_END)
