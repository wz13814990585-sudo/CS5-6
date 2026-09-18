import pandas as pd

from ml.relevance import add_relevance_by_date
from ml.xgb_ranker import group_sizes, prepare_rank_data


def data():
    return pd.DataFrame({"date": pd.to_datetime(["2020-01-03"]*3 + ["2020-01-10"]*2),
                         "ticker": ["C", "A", "B", "B", "A"], "f": [1, 2, 3, 4, 5],
                         "target_next_week_oc_return": [3, 1, 2, 10, -1]})


def test_each_date_is_one_sorted_group_and_sizes_sum():
    work = prepare_rank_data(data(), ["f"])
    assert group_sizes(work) == [3, 2]
    assert sum(group_sizes(work)) == len(work)
    assert work[["date", "ticker"]].equals(work[["date", "ticker"]].sort_values(["date", "ticker"]).reset_index(drop=True))


def test_relevance_is_date_local():
    out = add_relevance_by_date(data(), "target_next_week_oc_return", 10)
    assert out.groupby("date").relevance_label.min().eq(0).all()
    assert out.groupby("date").relevance_label.max().le(9).all()
