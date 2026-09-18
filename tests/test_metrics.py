import numpy as np
import pandas as pd

from ml.metrics import aggregate_metrics, metrics_by_date


def predictions():
    rows = []
    for date, sign in [("2020-01-03", 1), ("2020-01-10", -1)]:
        for i in range(10):
            rows.append({"date": pd.Timestamp(date), "ticker": str(i), "ranking_score": i,
                         "actual_return": sign*i, "relevance_label": i if sign == 1 else 9-i})
    return pd.DataFrame(rows)


def test_rank_ic_is_date_first_and_aggregated_mean():
    by_date = metrics_by_date(predictions())
    np.testing.assert_allclose(by_date.rank_ic, [1, -1])
    assert np.isclose(aggregate_metrics(by_date)["mean_rank_ic"], by_date.rank_ic.mean())


def test_ndcg_and_top_k_follow_score_order():
    by_date = metrics_by_date(predictions())
    assert by_date.iloc[0].ndcg5 > by_date.iloc[1].ndcg5
    assert by_date.iloc[0].top5_return == np.mean(range(5, 10))
    assert by_date.iloc[0].top5_bottom5_spread > 0
