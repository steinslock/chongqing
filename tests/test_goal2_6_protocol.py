from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from chongqing_binary.goal2_6.config import load_goal_config, project_path


class Goal26ProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = load_goal_config("configs/goal2_6/models.yaml")
        for extra in ["bootstrap", "eeg", "fnirs", "face"]:
            extra_cfg = load_goal_config(f"configs/goal2_6/{extra}.yaml")
            if extra in extra_cfg:
                cls.config[extra] = extra_cfg[extra]
        cls.split = pd.read_csv(PROJECT_ROOT / "artifacts/splits/subject_splits_v1.csv", dtype={"L_id": str})
        cls.predictions = pd.read_csv(
            PROJECT_ROOT / "results/goal2_6/all_oof_predictions.csv",
            dtype={"L_id": str},
            low_memory=False,
        )
        cls.features = pd.read_csv(PROJECT_ROOT / "results/goal2_6/feature_counts.csv")
        cls.paired = pd.read_csv(PROJECT_ROOT / "results/goal2_6/paired_model_comparisons.csv")
        cls.pca = pd.read_csv(PROJECT_ROOT / "results/goal2_6/pca_explained_variance.csv")
        cls.robustness = pd.read_csv(PROJECT_ROOT / "results/goal2_6/group_robustness_summary.csv")

    def test_goal2_6_uses_cv_pool_only(self) -> None:
        merged = self.predictions.merge(
            self.split[["L_id", "split_group", "is_locked_test", "cv_fold"]],
            on="L_id",
            how="left",
            suffixes=("", "_split"),
        )
        self.assertEqual(set(merged["split_group"]), {"cv"})
        self.assertEqual(int(merged["is_locked_test"].fillna(0).astype(int).sum()), 0)
        self.assertEqual(set(self.predictions["outer_fold"].astype(int)), {0, 1, 2, 3, 4})
        self.assertTrue((merged["outer_fold"].astype(int) == merged["cv_fold"].astype(int)).all())

    def test_oof_predictions_are_subject_level_unique(self) -> None:
        group_cols = ["cohort_name", "modality", "device", "task", "feature_set", "model", "seed"]
        for key, group in self.predictions.groupby(group_cols, dropna=False):
            self.assertEqual(len(group), group["L_id"].nunique(), key)
            self.assertTrue(set(group["outer_fold"].astype(int)).issubset({0, 1, 2, 3, 4}), key)

    def test_bootstrap_configuration_is_reproducible_and_large_enough(self) -> None:
        self.assertGreaterEqual(int(self.config["bootstrap"]["n_resamples"]), 1000)
        self.assertGreaterEqual(int(self.config["bootstrap"]["paired_n_resamples"]), 1000)
        ci = pd.read_csv(PROJECT_ROOT / "results/goal2_6/bootstrap_confidence_intervals.csv")
        self.assertEqual(set(ci["n_bootstrap"].astype(int)), {int(self.config["bootstrap"]["n_resamples"])})
        self.assertEqual(set(self.paired["n_bootstrap"].astype(int)), {int(self.config["bootstrap"]["paired_n_resamples"])})

    def test_feature_sets_keep_signal_qc_and_demographics_separate(self) -> None:
        demo_rows = self.features[self.features["feature_set"] == "demographics"]
        qc_rows = self.features[self.features["feature_set"] == "qc"]
        signal_rows = self.features[self.features["feature_set"].isin(["signal", "face_crop", "full_frame", "background", "modality"])]
        self.assertTrue((demo_rows["categorical_count"] >= 1).all())
        self.assertTrue((qc_rows["numeric_count"] >= 1).all())
        self.assertTrue((signal_rows["numeric_count"] >= 1).all())
        self.assertFalse((self.features["feature_set"] == "signal").equals(self.features["feature_set"] == "qc"))

    def test_required_goal2_6_scopes_are_present(self) -> None:
        required = {
            "fnirs_yiruid_1back_native": {
                "no_information",
                "demographics",
                "qc",
                "signal",
                "signal_qc",
                "signal_demographics",
                "signal_qc_demographics",
            },
            "fnirs_bikom_1back_native": {
                "no_information",
                "demographics",
                "qc",
                "signal",
                "signal_qc",
                "signal_demographics",
                "signal_qc_demographics",
            },
            "face_two_video_native": {
                "no_information",
                "demographics",
                "qc",
                "metadata",
                "full_frame",
                "face_crop",
                "background",
                "face_qc",
                "face_demographics",
                "face_qc_demographics",
            },
        }
        for cohort_name, expected_sets in required.items():
            observed = set(self.features.loc[self.features["cohort_name"] == cohort_name, "feature_set"])
            self.assertEqual(observed, expected_sets, cohort_name)

    def test_pca_and_group_robustness_outputs_are_written(self) -> None:
        self.assertFalse(self.pca.empty)
        self.assertGreater(int(self.pca["pca_used"].fillna(0).astype(int).sum()), 0)
        self.assertLessEqual(int(self.pca["pca_n_components"].fillna(0).max()), int(self.config["protocol"]["max_pca_components"]))
        self.assertTrue(
            {"face_self_intro_native", "face_task_native", "face_two_video_native", "core3_same_cohort"}.issubset(
                set(self.pca["cohort_name"])
            )
        )
        self.assertFalse(self.robustness.empty)
        expected = {
            "eeg_oddball_native_group_robustness",
            "fnirs_yiruid_vft_native_group_robustness",
            "face_task_native_group_robustness",
            "face_two_video_native_group_robustness",
            "shortcut_a_prefix_group_cv_group_robustness",
        }
        self.assertEqual(set(self.robustness["cohort_name"]), expected)

    def test_face_features_are_frozen_resnet_embeddings_not_color_histograms(self) -> None:
        manifest_path = project_path(self.config["face"]["outputs"]["manifest"])
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["encoder"]["name"], "torchvision_resnet18")
        self.assertTrue(manifest["encoder"]["frozen"])
        for task, spec in self.config["face"]["tasks"].items():
            signal = pd.read_csv(project_path(spec["signal_features"]), nrows=2)
            face_cols = [col for col in signal.columns if col.startswith("signal_face_mean_") or col.startswith("signal_face_std_")]
            self.assertGreaterEqual(len(face_cols), 1024, task)

    def test_paired_comparisons_use_subject_intersections(self) -> None:
        self.assertFalse(self.paired.empty)
        self.assertTrue((self.paired["n_subjects"].astype(int) >= 10).all())
        self.assertTrue({"model_a", "model_b", "auroc_diff_ci_low", "auroc_diff_ci_high"}.issubset(self.paired.columns))

    def test_core3_predictions_share_the_same_subject_set(self) -> None:
        core = self.predictions[self.predictions["cohort_name"] == "core3_same_cohort"]
        self.assertFalse(core.empty)
        sets = []
        group_cols = ["modality", "device", "task", "feature_set", "model", "seed"]
        for _, group in core.groupby(group_cols, dropna=False):
            sets.append(frozenset(group["L_id"].astype(str)))
        self.assertEqual(len(set(sets)), 1)

    def test_reports_exist(self) -> None:
        for name in [
            "goal2_6_eeg_results.md",
            "goal2_6_fnirs_results.md",
            "goal2_6_face_results.md",
            "goal2_6_shortcut_analysis.md",
            "goal2_6_core3_comparison.md",
            "goal2_6_final_report.md",
        ]:
            path = PROJECT_ROOT / "reports" / name
            self.assertTrue(path.exists(), name)
            self.assertIn("Goal 2.6", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
