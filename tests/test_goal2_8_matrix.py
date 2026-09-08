"""Goal 2.8 model matrix and reporting tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from chongqing_binary.goal2_8.config import load_goal_config
from chongqing_binary.goal2_8.report import (
    DEMOGRAPHIC_INCREMENTS,
    REQUIRED_INCREMENTS,
    SHORTCUT_CONTROLS,
    modality_decision,
    required_increment_table,
)


class ConfigInheritanceTests(unittest.TestCase):
    """Goal 2.8 must inherit Goal 2.7's grids so results stay comparable."""

    def setUp(self) -> None:
        self.g8 = load_goal_config("configs/goal2_8/models.yaml")
        self.g7 = load_goal_config("configs/goal2_7/models.yaml")

    def test_model_families_match_goal2_7(self) -> None:
        self.assertEqual(self.g8["models"]["tabular"], self.g7["models"]["tabular"])

    def test_hyperparameter_grids_match_goal2_7(self) -> None:
        self.assertEqual(self.g8["hyperparameters"], self.g7["hyperparameters"])

    def test_bootstrap_settings_match_goal2_7(self) -> None:
        g7 = load_goal_config("configs/goal2_7/bootstrap.yaml")["bootstrap"]
        for key in ("n_resamples", "paired_n_resamples", "ci", "seed", "paired_seed"):
            self.assertEqual(self.g8["bootstrap"][key], g7[key], key)

    def test_splits_are_the_fixed_ones(self) -> None:
        protocols = self.g8["protocol"]["cv_protocols"]
        self.assertTrue(protocols["standard_cv"]["split_file"].endswith("subject_splits_v1.csv"))
        self.assertEqual(protocols["standard_cv"]["fold_column"], "cv_fold")
        self.assertEqual(protocols["group_cv"]["fold_column"], "robustness_fold")

    def test_bikom_excluded_from_primary_matrix(self) -> None:
        self.assertEqual(self.g8["goal2_8"]["fnirs_devices"], ["yiruid"])

    def test_thread_caps_only_affect_speed(self) -> None:
        self.assertGreaterEqual(int(self.g8["run"]["model_n_jobs"]), 1)
        self.assertGreaterEqual(int(self.g8["run"]["dataset_workers"]), 1)

    def test_outputs_are_scoped_to_goal2_8(self) -> None:
        """Goal 2.7 results must not be overwritten."""
        for value in self.g8["outputs"].values():
            self.assertNotIn("goal2_7", str(value))


class DecisionRuleTests(unittest.TestCase):
    """The decision rule is fixed before results exist."""

    def _paired(self, rows: list[dict]) -> pd.DataFrame:
        return pd.DataFrame(rows)

    def test_required_comparisons_cover_demographics_and_background(self) -> None:
        rights = {right for _, right in REQUIRED_INCREMENTS}
        self.assertIn("demographics", rights)
        self.assertIn("background", rights)
        self.assertIn("qc_demographics", rights)

    def test_positive_only_when_interval_excludes_zero(self) -> None:
        paired = self._paired([
            {"cv_protocol": "standard_cv", "cohort_name": "c", "modality": "eeg", "device": "",
             "task": "t", "model": "m", "feature_set_a": "signal", "feature_set_b": "demographics",
             "auroc_diff": 0.05, "auroc_diff_ci_low": 0.01, "auroc_diff_ci_high": 0.09},
            {"cv_protocol": "standard_cv", "cohort_name": "c", "modality": "eeg", "device": "",
             "task": "t", "model": "m", "feature_set_a": "signal_demographics",
             "feature_set_b": "demographics",
             "auroc_diff": 0.02, "auroc_diff_ci_low": -0.01, "auroc_diff_ci_high": 0.05},
        ])
        table = required_increment_table(paired)
        self.assertEqual(list(table["significant_positive"]), [1, 0])

    def test_beating_background_alone_is_not_independent_signal(self) -> None:
        """Winning against background is a shortcut control, not an increment."""
        base = {"cohort_name": "c", "device": "", "task": "t", "model": "m",
                "feature_set_a": "face", "feature_set_b": "background",
                "auroc_diff": 0.05, "auroc_diff_ci_low": 0.02, "auroc_diff_ci_high": 0.09}
        table = required_increment_table(self._paired([
            {**base, "cv_protocol": "standard_cv", "modality": "face"},
            {**base, "cv_protocol": "group_cv", "modality": "face"},
        ]))
        decision = modality_decision(table)
        self.assertEqual(decision.iloc[0]["decision"], "NO_INDEPENDENT_SIGNAL")
        self.assertEqual(int(decision.iloc[0]["positive_over_shortcut_controls"]), 2)
        self.assertEqual(int(decision.iloc[0]["positive_over_demographics_standard_cv"]), 0)

    def test_demographic_and_shortcut_comparisons_are_disjoint(self) -> None:
        self.assertFalse(set(DEMOGRAPHIC_INCREMENTS) & set(SHORTCUT_CONTROLS))
        self.assertEqual(set(REQUIRED_INCREMENTS),
                         set(DEMOGRAPHIC_INCREMENTS) | set(SHORTCUT_CONTROLS))
        for _, right in DEMOGRAPHIC_INCREMENTS:
            self.assertIn("demographics", right)

    def test_modality_needs_both_protocols(self) -> None:
        base = {"cohort_name": "c", "device": "", "task": "t", "model": "m",
                "feature_set_b": "demographics", "feature_set_a": "signal",
                "auroc_diff": 0.05, "auroc_diff_ci_high": 0.09}
        one = required_increment_table(self._paired([
            {**base, "cv_protocol": "standard_cv", "modality": "eeg", "auroc_diff_ci_low": 0.01},
            {**base, "cv_protocol": "group_cv", "modality": "eeg", "auroc_diff_ci_low": -0.02},
        ]))
        self.assertEqual(modality_decision(one).iloc[0]["decision"], "NO_INDEPENDENT_SIGNAL")

        both = required_increment_table(self._paired([
            {**base, "cv_protocol": "standard_cv", "modality": "eeg", "auroc_diff_ci_low": 0.01},
            {**base, "cv_protocol": "group_cv", "modality": "eeg", "auroc_diff_ci_low": 0.01},
        ]))
        self.assertEqual(modality_decision(both).iloc[0]["decision"], "INDEPENDENT_SIGNAL_SUPPORTED")

    def test_empty_input_is_handled(self) -> None:
        self.assertTrue(required_increment_table(pd.DataFrame()).empty)
        self.assertTrue(modality_decision(pd.DataFrame()).empty)


if __name__ == "__main__":
    unittest.main()
