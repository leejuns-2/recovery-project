import unittest

import pandas as pd

from src.build_features import validate_feature_columns
from src.ranking_metrics import event_ranking_metrics


class RankingMetricTests(unittest.TestCase):
    def setUp(self) -> None:
        self.frame = pd.DataFrame(
            {
                "event_id": [1] * 10,
                "adm_cd": [str(i) for i in range(10)],
                "risk_score": list(range(10, 0, -1)),
                "delayed": [1, 1, 0, 0, 0, 0, 0, 0, 0, 0],
                "min_recovery_rate_d1_d3": [0.5, 0.6] + [0.95] * 8,
                "feature_a": list(range(10)),
            }
        )

    def test_top_20_percent_and_fixed_k_are_distinct(self) -> None:
        percent = event_ranking_metrics(self.frame, top_fraction=0.20).iloc[0]
        fixed = event_ranking_metrics(self.frame, k=3).iloc[0]
        self.assertEqual(percent["selected_n"], 2)
        self.assertEqual(fixed["selected_n"], 3)
        self.assertEqual(percent["recall"], 1.0)

    def test_target_derived_feature_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            validate_feature_columns(self.frame, ["feature_a", "risk_score"])


if __name__ == "__main__":
    unittest.main()
