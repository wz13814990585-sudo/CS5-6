import itertools
import unittest

import numpy as np
import pandas as pd

import build_evaluation as evaluation


def sample(score, target=None):
    return pd.DataFrame({"ticker": [f"S{i:02d}" for i in range(len(score))],
                         "prediction_score": score,
                         "actual_next_week_log_return": np.arange(len(score)) if target is None else target})


class EvaluationTests(unittest.TestCase):
    def test_perfect_ranking(self):
        row = evaluation.weekly_metrics(sample(np.arange(10)))
        for metric in ["IC", "Rank_IC", "Kendall_Tau", "Pairwise_Accuracy", "NDCG_at_5", "NDCG_at_10", "NDCG_at_all", "Hit_Rate_at_5", "Hit_Rate_at_10"]:
            self.assertAlmostEqual(row[metric], 1)
        self.assertEqual(row["Rank_MAE"], 0)
        self.assertEqual(row["Rank_RMSE"], 0)

    def test_reversed_ranking(self):
        row = evaluation.weekly_metrics(sample(np.arange(10)[::-1]))
        self.assertAlmostEqual(row["Rank_IC"], -1)
        self.assertEqual(row["Pairwise_Accuracy"], 0)
        self.assertEqual(row["Hit_Rate_at_5"], 0)
        self.assertEqual(row["Rank_MAE"], 5)
        self.assertAlmostEqual(row["Normalized_Rank_MAE"], 5/9)

    def test_score_ties_use_expected_ndcg_and_half_pair_credit(self):
        row = evaluation.weekly_metrics(sample(np.ones(10)))
        self.assertTrue(np.isnan(row["IC"]))
        self.assertTrue(np.isnan(row["Rank_IC"]))
        self.assertEqual(row["Pairwise_Accuracy"], .5)
        for k in ["5", "10", "all"]:
            self.assertAlmostEqual(row[f"NDCG_at_{k}"], row[f"Random_NDCG_at_{k}"])

    def test_target_ties_excluded_from_pairwise(self):
        self.assertAlmostEqual(evaluation.pairwise_accuracy([0, 1, 2], [0, 0, 1]), 1)
        self.assertTrue(np.isnan(evaluation.pairwise_accuracy([0, 1, 2], [1, 1, 1])))

    def test_pairwise_random_expectation(self):
        scores = list(itertools.permutations(range(4)))
        self.assertAlmostEqual(np.mean([evaluation.pairwise_accuracy(s, range(4)) for s in scores]), .5)

    def test_relevance_labels_follow_weekly_quantiles(self):
        np.testing.assert_array_equal(evaluation.labels_from_target(np.arange(10)), [0,0,1,1,2,2,3,3,4,4])

    def test_bootstrap_minimum_and_constant_series(self):
        self.assertTrue(np.isnan(evaluation.bootstrap_rankic_interval([.1]*7)[0]))
        lo, hi = evaluation.bootstrap_rankic_interval([.1]*20)
        self.assertAlmostEqual(lo, .1)
        self.assertAlmostEqual(hi, .1)
        self.assertTrue(np.isnan(evaluation.bootstrap_rankic_interval([.1]*10+[np.nan])[0]))


if __name__ == "__main__":
    unittest.main()
