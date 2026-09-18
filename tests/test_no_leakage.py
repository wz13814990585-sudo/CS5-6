import pandas as pd
import pytest

from ml.config import DEVELOPMENT_END, FINAL_TEST_START, TARGET_COLUMN
from ml.data import observable_training_rows, validate_feature_columns
from ml.validation import assert_disjoint_dates


@pytest.mark.parametrize("bad", ["date", "decision_date", "ticker", TARGET_COLUMN, "open", "adj_close", "macro_vix_level", "future_open", "fwd_x"])
def test_forbidden_features_rejected(bad):
    with pytest.raises(ValueError):
        validate_feature_columns([bad], [bad])


def test_duplicate_and_missing_features_rejected():
    with pytest.raises(ValueError): validate_feature_columns(["f", "f"], ["f"])
    with pytest.raises(ValueError): validate_feature_columns(["missing"], ["f"])


def test_target_must_be_observable_before_training():
    df = pd.DataFrame({"date": pd.to_datetime(["2020-01-03", "2020-01-10"]),
                       "target_observation_date": pd.to_datetime(["2020-01-10", "2020-01-17"])})
    got = observable_training_rows(df, "2020-01-10")
    assert got.empty
    inclusive = observable_training_rows(df, "2020-01-10", inclusive=True)
    assert inclusive.date.tolist() == [pd.Timestamp("2020-01-03")]


def test_periods_are_ordered_and_dates_never_split():
    assert pd.Timestamp(DEVELOPMENT_END) < pd.Timestamp(FINAL_TEST_START)
    train = pd.DataFrame({"date": pd.to_datetime(["2020-01-03"])})
    valid = pd.DataFrame({"date": pd.to_datetime(["2020-01-10"])})
    assert_disjoint_dates(train, valid)
    with pytest.raises(ValueError): assert_disjoint_dates(train, train)
