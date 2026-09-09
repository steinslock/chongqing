"""Tests for the Goal 2.10 model matrix and its decision rule."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from chongqing_binary.goal2_10 import report as eye_report
from chongqing_binary.goal2_10 import runner as eye_runner
from chongqing_binary.goal2_10.config import load_goal_config
from chongqing_binary.goal2_7.runner import DEFAULT_PAIRED_COMPARISONS, _paired_comparisons
from chongqing_binary.goal2_9.report import COMPARATOR_CHANCE_AUROC, credit_increments


class ConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = load_goal_config("configs/goal2_10/models.yaml")

    def test_nine_units_plus_three_combined(self) -> None:
        self.assertEqual(len(self.config["goal2_10"]["units"]), 9)
        self.assertEqual(sorted(self.config["goal2_10"]["combined_units"]), ["qixin_120", "qixin_500", "tobii"])

    def test_outputs_never_point_at_an_earlier_goal(self) -> None:
        # Goal 2.8 inherited six output keys still pointing at Goal 2.7 and a
        # test now guards that; the same guard belongs here.
        for key, value in self.config["outputs"].items():
            self.assertNotIn("goal2_7", str(value), key)
            self.assertNotIn("goal2_8", str(value), key)
            self.assertNotIn("goal2_9", str(value), key)

    def test_split_files_are_the_shared_fixed_ones(self) -> None:
        self.assertEqual(self.config["paths"]["split_file"], "artifacts/splits/subject_splits_v1.csv")
        self.assertEqual(
            self.config["paths"]["group_split_file"], "artifacts/splits/subject_splits_group_robustness_v1.csv"
        )

    def test_paired_pairs_cover_the_absolute_and_contrast_blocks(self) -> None:
        pairs = {(str(a), str(b)) for a, b in self.config["protocol"]["paired_comparison_pairs"]}
        self.assertIn(("signal_absolute_demographics", "demographics"), pairs)
        self.assertIn(("signal_contrast_demographics", "demographics"), pairs)

    def test_bootstrap_matches_the_earlier_goals(self) -> None:
        # Comparability with Goal 2.7, 2.8 and 2.9 depends on this.
        self.assertEqual(self.config["bootstrap"]["n_resamples"], 1000)


class PairedComparisonTests(unittest.TestCase):
    def _predictions(self, feature_sets: tuple[str, ...]) -> pd.DataFrame:
        # The comparison needs at least 10 shared subjects.
        import numpy as np

        rng = np.random.default_rng(0)
        n = 40
        labels = np.tile([0, 1], n // 2)
        parts = []
        for offset, feature_set in enumerate(feature_sets):
            parts.append(
                pd.DataFrame(
                    {
                        "cv_protocol": "standard_cv",
                        "cohort_name": "c",
                        "modality": "eye",
                        "device": "tobii",
                        "task": "free_viewing",
                        "model": "logistic_regression",
                        "seed": 0,
                        "feature_set": feature_set,
                        "L_id": [f"L{i}" for i in range(n)],
                        "label": labels,
                        "probability": np.clip(0.5 + (0.2 - 0.05 * offset) * (labels - 0.5) * 2 + rng.normal(0, 0.1, n), 0, 1),
                        "outer_fold": np.arange(n) % 5,
                    }
                )
            )
        return pd.concat(parts, ignore_index=True)

    def test_configured_pairs_override_the_default(self) -> None:
        config = {"protocol": {"paired_comparison_pairs": [["signal_absolute", "demographics"]]}}
        predictions = self._predictions(("signal_absolute", "demographics", "signal"))
        result = _paired_comparisons(predictions, config)
        self.assertFalse(result.empty)
        # Only the configured pair, not the default battery.
        self.assertEqual(set(result["comparison"]), {"signal_absolute_vs_demographics"})

    def test_default_list_is_unchanged_for_the_earlier_goals(self) -> None:
        self.assertIn(("signal_demographics", "demographics"), DEFAULT_PAIRED_COMPARISONS)
        self.assertEqual(len(DEFAULT_PAIRED_COMPARISONS), 20)


class DecisionRuleTests(unittest.TestCase):
    def _required(self, comparator_auroc: float) -> pd.DataFrame:
        required = pd.DataFrame(
            {
                "cv_protocol": ["standard_cv"],
                "cohort_name": ["eye_tobii_free_viewing_native"],
                "modality": ["eye"],
                "device": ["tobii"],
                "task": ["free_viewing"],
                "model": ["random_forest"],
                "comparison": ["signal_absolute_demographics_vs_demographics"],
                "significant_positive": [1],
                "significant_negative": [0],
            }
        )
        pooled = pd.DataFrame(
            {
                "cv_protocol": ["standard_cv"],
                "cohort_name": ["eye_tobii_free_viewing_native"],
                "model": ["random_forest"],
                "feature_set": ["demographics"],
                "auroc": [comparator_auroc],
                "threshold_type": ["inner_cv"],
            }
        )
        return credit_increments(required, pooled)

    def test_a_win_over_a_below_chance_baseline_is_not_credited(self) -> None:
        # This is the hole Goal 2.9 found in a live result.
        credited = self._required(0.47)
        self.assertEqual(int(credited.loc[0, "significant_positive"]), 1)
        self.assertEqual(int(credited.loc[0, "significant_positive_credited"]), 0)

    def test_a_win_over_a_working_baseline_is_credited(self) -> None:
        credited = self._required(0.65)
        self.assertEqual(int(credited.loc[0, "significant_positive_credited"]), 1)

    def test_chance_threshold_is_one_half(self) -> None:
        self.assertEqual(COMPARATOR_CHANCE_AUROC, 0.5)


class RequiredIncrementTests(unittest.TestCase):
    def test_the_contrast_block_is_a_demographic_increment(self) -> None:
        comparisons = {f"{a}_vs_{b}" for a, b in eye_report.EYE_DEMOGRAPHIC_INCREMENTS}
        self.assertIn("signal_contrast_demographics_vs_demographics", comparisons)
        self.assertIn("signal_absolute_demographics_vs_demographics", comparisons)

    def test_permutation_threshold_covers_every_eye_cohort(self) -> None:
        # The largest eye cohort holds 336 subjects, so the requirement applies
        # to all of them and none can be reported on the interval alone.
        self.assertEqual(eye_report.PERMUTATION_REQUIRED_BELOW_N, 500)

    def test_table_keeps_only_the_declared_comparisons(self) -> None:
        paired = pd.DataFrame(
            {
                "cv_protocol": ["standard_cv"] * 3,
                "cohort_name": ["c"] * 3,
                "modality": ["eye"] * 3,
                "device": ["tobii"] * 3,
                "task": ["free_viewing"] * 3,
                "model": ["m"] * 3,
                "feature_set_a": ["signal_contrast_demographics", "signal", "qc"],
                "feature_set_b": ["demographics", "demographics", "demographics"],
                "auroc_diff": [0.01, 0.02, 0.03],
                "auroc_diff_ci_low": [0.001, -0.01, 0.001],
                "auroc_diff_ci_high": [0.02, 0.05, 0.06],
            }
        )
        table = eye_report.eye_required_increment_table(paired)
        self.assertEqual(len(table), 2)
        self.assertNotIn("qc_vs_demographics", set(table["comparison"]))


class CombinedNamingTests(unittest.TestCase):
    def test_contrast_marker_survives_the_task_prefix(self) -> None:
        # The combined cohort must still be able to split absolute from
        # contrast features after every column is prefixed with its task.
        renamed = eye_runner._rename("signal_contrast_late_sad_minus_neutral_eyes_share", "signal_", "free_viewing")
        self.assertTrue(renamed.startswith(eye_runner.CONTRAST_MARKER))
        plain = eye_runner._rename("signal_late_sad_eyes_share", "signal_", "free_viewing")
        self.assertFalse(plain.startswith(eye_runner.CONTRAST_MARKER))
        self.assertEqual(plain, "signal_free_viewing_late_sad_eyes_share")


if __name__ == "__main__":
    unittest.main()
