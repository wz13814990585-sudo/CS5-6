import unittest
from types import SimpleNamespace
import numpy as np
import pandas as pd
import prediction_helpers as runner

class PredictionTests(unittest.TestCase):
    def test_training_window_and_label_boundary(self):
        frame = pd.DataFrame({"week_index": range(8), "label_end_week": range(1, 9)})
        part = runner.training_window(frame, SimpleNamespace(training_window_weeks=3), 6)
        self.assertEqual(part.week_index.tolist(), [3, 4, 5])
        self.assertEqual(part.label_end_week.max(), 6)
        frame.loc[5, "label_end_week"] = 7
        with self.assertRaises(ValueError):
            runner.training_window(frame, SimpleNamespace(training_window_weeks=3), 6)


    def test_test_target_does_not_affect_scores(self):
        class Model:
            def predict(self, matrix):
                return matrix[:, 0] * 3
        frame = pd.DataFrame({"week_index": [156] * 3, "date": [pd.Timestamp("2020-01-03")] * 3,
                              "ticker": list("ABC"), "target": [.1, .2, -.2],
                              "actual_rank": [2, 1, 3], "target_verification_status": ["test"] * 3,
                              "csrank__feature": [.3, .8, .5]})
        spec = SimpleNamespace(ranked_features=("csrank__feature",))
        before = runner.score_block(Model(), spec, frame)
        frame["target"] = [100, -100, 0]
        frame["actual_rank"] = [1, 3, 2]
        after = runner.score_block(Model(), spec, frame)
        pd.testing.assert_frame_equal(before[["raw_ranking_score", "percentile_score", "predicted_rank"]],
                                      after[["raw_ranking_score", "percentile_score", "predicted_rank"]])


