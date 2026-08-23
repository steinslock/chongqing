from __future__ import annotations

import gzip
import hashlib
import json
import inspect
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from chongqing_binary.goal2_7.fnirs import _segments
from chongqing_binary.goal2_7.runner import (
    GoalDataset,
    _build_pipeline,
    _combined_config,
    _datasets_for_protocol,
    _paired_comparisons,
    _standard_feature_sets,
    compute_metrics,
)


class Goal27ProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = _combined_config("configs/goal2_7/models.yaml")
        cls.results_dir = PROJECT_ROOT / "results/goal2_7"
        cls.artifacts_dir = PROJECT_ROOT / "artifacts/goal2_7"
        cls.pooled = pd.read_csv(cls.results_dir / "all_pooled_metrics.csv")
        cls.paired = pd.read_csv(cls.results_dir / "paired_increment_comparisons.csv")
        cls.bootstrap = pd.read_csv(cls.results_dir / "bootstrap_confidence_intervals.csv")
        cls.threshold = pd.read_csv(cls.results_dir / "threshold_diagnostics.csv")
        cls.pca = pd.read_csv(cls.results_dir / "pca_diagnostics.csv")
        cls.face_control = pd.read_csv(cls.results_dir / "face_strict_control_summary.csv")

    def test_protocol_outputs_are_declared(self) -> None:
        outputs = self.config["outputs"]
        required = [
            "all_oof_predictions_standard_cv",
            "all_oof_predictions_group_cv",
            "paired_comparisons",
            "demographics_decomposition",
            "standard_vs_group_cv",
            "threshold_diagnostics",
            "pca_diagnostics",
        ]
        for key in required:
            self.assertIn(key, outputs)

    def test_result_files_exist_and_are_nonempty(self) -> None:
        required = [
            "all_oof_predictions_standard_cv.csv",
            "all_oof_predictions_group_cv.csv",
            "all_pooled_metrics.csv",
            "all_fold_metrics.csv",
            "bootstrap_confidence_intervals.csv",
            "paired_increment_comparisons.csv",
            "demographics_decomposition.csv",
            "standard_vs_group_cv.csv",
            "face_strict_control_summary.csv",
            "eeg_event_validity_summary.csv",
            "fnirs_event_validity_summary.csv",
            "core3_intersection_summary.csv",
            "threshold_diagnostics.csv",
            "selected_hyperparameters.csv",
            "pca_diagnostics.csv",
            "exclusion_summary.csv",
        ]
        for name in required:
            path = self.results_dir / name
            self.assertTrue(path.exists(), name)
            self.assertGreater(path.stat().st_size, 1, name)

    def test_oof_required_columns_are_present(self) -> None:
        required = {
            "L_id",
            "label",
            "modality",
            "device",
            "task",
            "feature_set",
            "model",
            "cv_protocol",
            "outer_fold",
            "probability",
            "fold_specific_threshold",
            "predicted_label",
            "cohort_name",
            "event_validity_status",
            "feature_version",
            "preprocessing_version",
            "selected_threshold_per_subject",
            "selected_threshold_per_fold",
            "threshold_source",
        }
        for name in ["all_oof_predictions_standard_cv.csv", "all_oof_predictions_group_cv.csv"]:
            cols = set(pd.read_csv(self.results_dir / name, nrows=0).columns)
            self.assertTrue(required.issubset(cols), name)

    def test_oof_protocol_labels_match_output_files(self) -> None:
        for name, expected in [
            ("all_oof_predictions_standard_cv.csv", "standard_cv"),
            ("all_oof_predictions_group_cv.csv", "group_cv"),
        ]:
            values = set(pd.read_csv(self.results_dir / name, usecols=["cv_protocol"])["cv_protocol"].unique())
            self.assertEqual(values, {expected})

    def test_oof_probabilities_and_thresholds_are_bounded(self) -> None:
        for name in ["all_oof_predictions_standard_cv.csv", "all_oof_predictions_group_cv.csv"]:
            frame = pd.read_csv(self.results_dir / name, usecols=["probability", "fold_specific_threshold", "predicted_label"])
            self.assertTrue(frame["probability"].between(0, 1).all(), name)
            self.assertTrue(frame["fold_specific_threshold"].between(0, 1).all(), name)
            self.assertTrue(set(frame["predicted_label"].unique()).issubset({0, 1}), name)

    def test_oof_has_one_prediction_per_subject_group(self) -> None:
        columns = ["L_id", "modality", "device", "task", "cohort_name", "feature_set", "model", "seed", "outer_fold"]
        for name in ["all_oof_predictions_standard_cv.csv", "all_oof_predictions_group_cv.csv"]:
            frame = pd.read_csv(self.results_dir / name, usecols=columns, dtype={"L_id": str}, low_memory=False)
            duplicates = frame.duplicated(columns).sum()
            self.assertEqual(int(duplicates), 0, name)

    def test_oof_subjects_are_cv_pool_only(self) -> None:
        split = pd.read_csv(PROJECT_ROOT / "artifacts/splits/subject_splits_v1.csv", dtype={"L_id": str})
        cv_ids = set(split.loc[split["split_group"] == "cv", "L_id"])
        for name in ["all_oof_predictions_standard_cv.csv", "all_oof_predictions_group_cv.csv"]:
            ids = set(pd.read_csv(self.results_dir / name, usecols=["L_id"], dtype={"L_id": str})["L_id"])
            self.assertTrue(ids.issubset(cv_ids), name)

    def test_standard_and_group_cv_are_fixed_split_columns(self) -> None:
        protocols = self.config["protocol"]["cv_protocols"]
        self.assertEqual(protocols["standard_cv"]["fold_column"], "cv_fold")
        self.assertEqual(protocols["group_cv"]["fold_column"], "robustness_fold")

    def test_pooled_metrics_contain_both_protocols(self) -> None:
        protocols = set(self.pooled["cv_protocol"].unique())
        self.assertEqual(protocols, {"standard_cv", "group_cv"})

    def test_pooled_metrics_include_all_required_metrics(self) -> None:
        required = {
            "auroc",
            "auprc",
            "balanced_accuracy",
            "macro_f1",
            "sensitivity",
            "specificity",
            "accuracy",
            "brier_score",
            "ece",
        }
        self.assertTrue(required.issubset(set(self.pooled.columns)))
        self.assertEqual(set(self.pooled["threshold_type"].unique()), {"fixed_0_5", "inner_cv"})

    def test_main_demographics_excludes_grade_group(self) -> None:
        self.assertEqual(self.config["demographics"]["main_numeric_columns"], ["age_clean"])
        self.assertEqual(self.config["demographics"]["main_categorical_columns"], ["sex_clean", "grade_clean"])
        self.assertIn("grade_group_only", self.config["demographics"]["decomposition_sets"])

    def test_demographics_decomposition_sets_all_present(self) -> None:
        demo = pd.read_csv(self.results_dir / "demographics_decomposition.csv")
        expected = {
            "age_only",
            "sex_only",
            "grade_only",
            "grade_group_only",
            "age_sex",
            "age_grade",
            "sex_grade",
            "age_sex_grade",
            "age_sex_grade_group",
            "group_proxy_only",
            "fnirs_device_only",
            "demographics_group",
            "demographics_group_device",
            "demographics",
        }
        self.assertTrue(expected.issubset(set(demo["feature_set"])))

    def test_grade_and_grade_group_are_separate_feature_sets(self) -> None:
        sets = self.config["demographics"]["decomposition_sets"]
        self.assertIn("grade_only", sets)
        self.assertIn("grade_group_only", sets)
        self.assertNotIn("grade_group_clean", self.config["demographics"]["main_categorical_columns"])

    def test_hgb_grid_has_multiple_reasonable_candidates(self) -> None:
        grid = self.config["hyperparameters"]["hist_gradient_boosting"]
        self.assertGreaterEqual(len(grid), 3)
        self.assertLessEqual(len(grid), 12)
        self.assertTrue(all(row["model__max_iter"] >= 50 for row in grid))

    def test_bikom_fixed_2000_cap_removed(self) -> None:
        self.assertEqual(int(self.config["fnirs"]["bikom_max_rows"]), 0)
        self.assertEqual(self.config["fnirs"]["task_segment_rule"], "marker_confirmed_or_protocol_confirmed_only")

    def test_fnirs_segments_no_20_60_20_fallback(self) -> None:
        data = np.ones((100, 2), dtype=float)
        baseline, active, recovery = _segments(data, np.zeros(100, dtype=int))
        self.assertEqual(baseline.size, 0)
        self.assertEqual(active.size, 0)
        self.assertEqual(recovery.size, 0)
        self.assertNotIn("0.2", inspect.getsource(_segments))

    def test_eeg_condition_features_blocked(self) -> None:
        oneback = pd.read_csv(PROJECT_ROOT / "artifacts/goal2_7/eeg/1back_generic_signal_features.csv", nrows=2)
        oddball = pd.read_csv(PROJECT_ROOT / "artifacts/goal2_7/eeg/oddball_target_only_proxy_signal_features.csv", nrows=2)
        self.assertFalse(any("minus" in col for col in oneback.columns))
        self.assertFalse(any("signal_erp_code_" in col for col in oneback.columns))
        self.assertTrue(any("oddball_target_only_proxy" in col for col in oddball.columns))
        self.assertIn("blocked_condition_semantics_unconfirmed_generic_signal_only", set(oneback["event_validity_status"]))

    def test_eeg_event_validity_summary_marks_blocked_tasks(self) -> None:
        validity = pd.read_csv(self.results_dir / "eeg_event_validity_summary.csv")
        statuses = set(validity["event_validity_status"])
        self.assertIn("blocked_target_nontarget_semantics_unconfirmed_target_only_proxy", statuses)
        self.assertIn("blocked_condition_semantics_unconfirmed_generic_signal_only", statuses)

    def test_fnirs_event_validity_summary_marks_blocked_timing(self) -> None:
        validity = pd.read_csv(self.results_dir / "fnirs_event_validity_summary.csv")
        statuses = set(validity["event_validity_status"])
        self.assertIn("bikom_vft_no_markers_task_response_blocked", statuses)
        self.assertIn("yiruid_vft_markers_present_timing_semantics_unconfirmed", statuses)

    def test_fnirs_timing_audit_records_bikom_full_read(self) -> None:
        timing = pd.read_csv(PROJECT_ROOT / "artifacts/goal2_7/fnirs/task_timing_summary.csv")
        bikom_rest = timing[(timing["device"] == "bikom") & (timing["task"] == "rest")].iloc[0]
        self.assertGreater(int(bikom_rest["rows_gt_2000"]), 0)
        self.assertGreater(int(bikom_rest["markers_after_2000"]), 0)

    def test_yiruid_features_do_not_claim_hbo_hbr(self) -> None:
        for rel in [
            "artifacts/goal2_7/fnirs/yiruid_rest_signal_features.csv",
            "artifacts/goal2_7/fnirs/yiruid_vft_signal_features.csv",
        ]:
            cols = pd.read_csv(PROJECT_ROOT / rel, nrows=0).columns
            lowered = [col.lower() for col in cols]
            self.assertFalse(any("hbo" in col or "hbr" in col for col in lowered), rel)

    def test_fnirs_no_formal_task_delta_without_confirmed_timing(self) -> None:
        for rel in [
            "artifacts/goal2_7/fnirs/yiruid_vft_signal_features.csv",
            "artifacts/goal2_7/fnirs/bikom_vft_signal_features.csv",
        ]:
            cols = pd.read_csv(PROJECT_ROOT / rel, nrows=0).columns
            self.assertFalse(any("task_minus_baseline" in col or "active_minus" in col for col in cols), rel)

    def test_generated_goal27_features_exclude_pilot_holdout(self) -> None:
        for rel in [
            "artifacts/goal2_7/eeg/rest_signal_features.csv",
            "artifacts/goal2_7/fnirs/bikom_rest_qc_features.csv",
        ]:
            frame = pd.read_csv(PROJECT_ROOT / rel)
            self.assertFalse(pd.to_numeric(frame["is_locked_test"], errors="coerce").fillna(0).astype(int).any(), rel)

    def test_clinical_and_diagnosis_fields_not_in_oof(self) -> None:
        forbidden = {"diagnosis", "clinical", "scale", "symptom"}
        for name in ["all_oof_predictions_standard_cv.csv", "all_oof_predictions_group_cv.csv"]:
            cols = [col.lower() for col in pd.read_csv(self.results_dir / name, nrows=0).columns]
            self.assertFalse(any(any(token in col for token in forbidden) for col in cols), name)

    def test_standard_feature_sets_include_qc_demographics(self) -> None:
        frame = pd.DataFrame(
            {
                "L_id": ["L1", "L2"],
                "primary_label_nonhealthy": [0, 1],
                "cv_fold": [0, 1],
                "age_clean": [10.0, 11.0],
                "sex_clean": ["F", "M"],
                "grade_clean": ["5", "6"],
                "signal_a": [0.1, 0.2],
                "qc_a": [1.0, 2.0],
            }
        )
        names = {d.feature_set for d in _standard_feature_sets(frame, "eeg", "", "rest", "toy", self.config, "tabular")}
        self.assertIn("qc_demographics", names)
        self.assertIn("signal_qc_demographics", names)

    def test_signal_only_and_qc_demographics_are_separated(self) -> None:
        frame = pd.DataFrame(
            {
                "L_id": ["L1", "L2", "L3", "L4"],
                "primary_label_nonhealthy": [0, 1, 0, 1],
                "cv_fold": [0, 1, 2, 3],
                "age_clean": [10.0, 11.0, 12.0, 13.0],
                "sex_clean": ["F", "M", "F", "M"],
                "grade_clean": ["5", "6", "5", "6"],
                "signal_a": [0.1, 0.2, 0.3, 0.4],
                "qc_a": [1.0, 2.0, 3.0, 4.0],
            }
        )
        datasets = {d.feature_set: d for d in _standard_feature_sets(frame, "eeg", "", "rest", "toy", self.config, "tabular")}
        self.assertEqual(datasets["signal"].numeric_columns, ["signal_a"])
        self.assertNotIn("signal_a", datasets["qc_demographics"].numeric_columns)
        self.assertIn("qc_a", datasets["qc_demographics"].numeric_columns)

    def test_face_pca_branch_separates_visual_from_nonvisual(self) -> None:
        frame = pd.DataFrame(
            {
                "L_id": [f"L{i}" for i in range(12)],
                "primary_label_nonhealthy": [0, 1] * 6,
                "cv_fold": [0, 1, 2, 3, 4, 0, 1, 2, 3, 4, 0, 1],
                "signal_face_mean_000": np.linspace(0, 1, 12),
                "signal_face_mean_001": np.linspace(1, 0, 12),
                "qc_blur_score_mean": np.linspace(2, 3, 12),
                "age_clean": np.linspace(10, 12, 12),
                "sex_clean": ["F", "M"] * 6,
            }
        )
        ds = GoalDataset("toy_face", "face", "", "self_intro", "face_qc_demographics", frame, ["signal_face_mean_000", "signal_face_mean_001", "qc_blur_score_mean", "age_clean"], ["sex_clean"], "face_embedding")
        pipe = _build_pipeline(ds, "logistic_regression", self.config, 1)
        transformers = {name: cols for name, _, cols in pipe.named_steps["preprocess"].transformers}
        self.assertEqual(transformers["visual"], ["signal_face_mean_000", "signal_face_mean_001"])
        self.assertIn("qc_blur_score_mean", transformers["num"])
        self.assertIn("age_clean", transformers["num"])
        self.assertIn("sex_clean", transformers["cat"])

    def test_pca_diagnostics_record_visual_and_nonvisual_counts(self) -> None:
        face = self.pca[(self.pca["modality"] == "face") & (self.pca["pca_used"] == 1)]
        self.assertFalse(face.empty)
        self.assertTrue((face["visual_branch_feature_count"] > 0).all())
        mixed = face[face["feature_set"].astype(str).str.contains("demographics|qc", regex=True)]
        self.assertTrue((mixed["nonvisual_branch_feature_count"] > 0).any())

    def test_face_encoder_manifest_is_frozen_visual_only(self) -> None:
        manifest = json.loads((PROJECT_ROOT / "artifacts/goal2_7/face/encoder_manifest.json").read_text())
        self.assertTrue(manifest["encoder"]["frozen"])
        self.assertEqual(manifest["encoder"]["name"], "torchvision_resnet18")
        self.assertIn("cuda", manifest["encoder"]["device"])

    def test_face_strict_qc_records_blocked_and_no_audio(self) -> None:
        self.assertGreater(int(self.face_control["blocked_videos"].sum()), 0)
        self.assertEqual(int(self.face_control["audio_used_sum"].sum()), 0)

    def test_face_contact_sheets_at_least_200(self) -> None:
        sheet_dir = PROJECT_ROOT / "artifacts/goal2_7/face/contact_sheets"
        sheets = list(sheet_dir.glob("*.jpg")) + list(sheet_dir.glob("*.png"))
        self.assertGreaterEqual(len(sheets), 200)

    def test_face_background_and_blur_features_exist(self) -> None:
        cols = pd.read_csv(PROJECT_ROOT / "artifacts/goal2_7/face/task_signal_features.csv", nrows=0).columns
        self.assertTrue(any(col.startswith("signal_background_mean_") for col in cols))
        self.assertTrue(any(col.startswith("signal_background_blur_mean_") for col in cols))

    def test_face_fallback_detector_is_recorded(self) -> None:
        qc = pd.read_csv(PROJECT_ROOT / "artifacts/goal2_7/face/self_intro_qc_features.csv", usecols=["qc_detector_fallback_used"])
        self.assertGreater(int(pd.to_numeric(qc["qc_detector_fallback_used"], errors="coerce").fillna(0).sum()), 0)

    def test_fold_specific_threshold_metrics_accept_row_thresholds(self) -> None:
        metrics = compute_metrics([0, 0, 1, 1], [0.2, 0.55, 0.45, 0.8], [0.5, 0.6, 0.4, 0.7])
        self.assertAlmostEqual(metrics["balanced_accuracy"], 1.0)

    def test_threshold_diagnostics_use_inner_cv_source(self) -> None:
        self.assertEqual(set(self.threshold["threshold_source"]), {"inner_cv_outer_train_only"})
        self.assertTrue(self.threshold["selected_threshold_per_fold"].between(0, 1).all())

    def test_inner_threshold_predictions_are_row_specific_in_oof(self) -> None:
        sample = pd.read_csv(
            self.results_dir / "all_oof_predictions_standard_cv.csv",
            usecols=["selected_threshold_per_subject", "selected_threshold_per_fold", "threshold_source"],
            nrows=50000,
        )
        self.assertTrue((sample["selected_threshold_per_subject"] == sample["selected_threshold_per_fold"]).all())
        self.assertEqual(set(sample["threshold_source"]), {"inner_cv_outer_train_only"})

    def test_paired_comparisons_include_required_increment(self) -> None:
        rows = []
        for feature_set, offset in [("signal_demographics", 0.1), ("demographics", 0.0), ("signal_qc_demographics", 0.1), ("qc_demographics", 0.0)]:
            for i in range(40):
                label = i % 2
                rows.append(
                    {
                        "L_id": f"L{i}",
                        "label": label,
                        "modality": "eeg",
                        "device": "",
                        "task": "rest",
                        "feature_set": feature_set,
                        "model": "logistic_regression",
                        "cv_protocol": "standard_cv",
                        "seed": 1,
                        "outer_fold": i % 5,
                        "probability": 0.2 + 0.5 * label + offset,
                        "fold_specific_threshold": 0.5,
                        "cohort_name": "toy",
                    }
                )
        cfg = dict(self.config)
        cfg["bootstrap"] = dict(self.config["bootstrap"], paired_n_resamples=20)
        paired = _paired_comparisons(pd.DataFrame(rows), cfg)
        comparisons = set(paired["comparison"])
        self.assertIn("signal_demographics_vs_demographics", comparisons)
        self.assertIn("signal_qc_demographics_vs_qc_demographics", comparisons)

    def test_paired_output_contains_all_required_comparison_families(self) -> None:
        required = {
            "signal_vs_demographics",
            "signal_demographics_vs_demographics",
            "signal_qc_vs_qc",
            "signal_qc_demographics_vs_qc_demographics",
            "signal_qc_demographics_vs_demographics",
            "signal_demographics_vs_signal",
            "signal_qc_demographics_vs_signal_qc",
            "face_vs_demographics",
            "face_demographics_vs_demographics",
            "face_qc_vs_qc",
            "face_qc_demographics_vs_qc_demographics",
            "face_qc_demographics_vs_demographics",
            "face_vs_background",
            "face_vs_full_frame",
            "face_vs_metadata",
            "face_vs_qc",
            "face_demographics_vs_background_demographics",
        }
        self.assertTrue(required.issubset(set(self.paired["comparison"])))

    def test_paired_bootstrap_is_1000_and_has_protocol_consistency(self) -> None:
        self.assertEqual(set(self.paired["n_bootstrap"].unique()), {1000})
        self.assertIn("protocol_consistent_direction", self.paired.columns)

    def test_bootstrap_ci_is_1000_and_has_all_metrics(self) -> None:
        self.assertEqual(set(self.bootstrap["n_bootstrap"].unique()), {1000})
        expected = {
            "auroc",
            "auprc",
            "balanced_accuracy",
            "macro_f1",
            "sensitivity",
            "specificity",
            "accuracy",
            "brier_score",
            "ece",
            "positive_prediction_rate",
        }
        self.assertEqual(set(self.bootstrap["metric"].unique()), expected)

    def test_paired_subject_counts_are_positive_and_same_fold_based(self) -> None:
        self.assertTrue((self.paired["n_subjects"] >= 10).all())
        self.assertTrue((self.paired["folds_compared"] <= 5).all())
        self.assertTrue((self.paired["folds_compared"] > 0).all())

    def test_protocol_clone_uses_group_fold_without_pilot(self) -> None:
        frame = pd.read_csv(PROJECT_ROOT / "artifacts/goal2_7/eeg/rest_signal_features.csv")
        ds = GoalDataset("toy", "eeg", "", "rest", "signal", frame, [c for c in frame.columns if c.startswith("signal_")][:2], [], "tabular")
        group = _datasets_for_protocol([ds], self.config, "group_cv")[0].frame
        self.assertIn("cv_fold", group.columns)
        self.assertFalse(pd.to_numeric(group["is_locked_test"], errors="coerce").fillna(0).astype(int).any())
        self.assertEqual(set(group["cv_fold"].dropna().astype(int).unique()), {0, 1, 2, 3, 4})

    def test_core3_name_and_subject_count_are_explicit(self) -> None:
        core = pd.read_csv(self.results_dir / "core3_intersection_summary.csv")
        self.assertEqual(set(core["cohort_name"]), {"core3_rest_yiruidvft_selfintro_intersection"})
        self.assertEqual(set(core["n_subjects"].astype(int)), {661})

    def test_standard_vs_group_summary_has_delta_columns(self) -> None:
        summary = pd.read_csv(self.results_dir / "standard_vs_group_cv.csv")
        for metric in ["auroc", "auprc", "balanced_accuracy", "macro_f1"]:
            self.assertIn(f"{metric}_delta_standard_minus_group", summary.columns)

    def test_reports_were_generated(self) -> None:
        reports = [
            "goal2_7_preimplementation_audit.md",
            "goal2_7_eeg_event_audit.md",
            "goal2_7_fnirs_event_audit.md",
            "goal2_7_face_detection_audit.md",
            "goal2_7_demographics_and_group_analysis.md",
            "goal2_7_eeg_results.md",
            "goal2_7_fnirs_results.md",
            "goal2_7_face_results.md",
            "goal2_7_core3_comparison.md",
            "goal2_7_protocol_comparison.md",
            "goal2_7_final_report.md",
            "goal2_7_release_notes.md",
        ]
        for name in reports:
            path = PROJECT_ROOT / "reports" / name
            self.assertTrue(path.exists(), name)
            self.assertGreater(path.stat().st_size, 100, name)

    def test_release_oof_archives_match_manifest(self) -> None:
        manifest = json.loads((PROJECT_ROOT / "artifacts/goal2_7/release_manifest.json").read_text())
        expected_rows = {
            "results/goal2_7/all_oof_predictions_standard_cv.csv.gz": 1528167,
            "results/goal2_7/all_oof_predictions_group_cv.csv.gz": 1528167,
        }
        for row in manifest["oof_archives"]:
            archive = PROJECT_ROOT / row["archive"]
            digest = hashlib.sha256(archive.read_bytes()).hexdigest()
            self.assertEqual(digest, row["archive_sha256"])
            self.assertEqual(int(row["source_rows"]), expected_rows[row["archive"]])
            with gzip.open(archive, "rt", encoding="utf-8") as handle:
                header = handle.readline()
            self.assertIn("L_id,label,modality", header)

    def test_release_manifest_keeps_sensitive_face_audits_local(self) -> None:
        manifest = json.loads((PROJECT_ROOT / "artifacts/goal2_7/release_manifest.json").read_text())
        files = {row["path"]: row for row in manifest["files"]}
        contact_rows = [row for path, row in files.items() if "/contact_sheets/" in path]
        face_signal_rows = [
            row
            for path, row in files.items()
            if path.startswith("artifacts/goal2_7/face/")
            and "_signal_features" in path
            and path.endswith(".csv")
            and not path.endswith(".part.csv")
        ]
        face_part_rows = [
            row
            for path, row in files.items()
            if path.startswith("artifacts/goal2_7/face/") and path.endswith(".part.csv")
        ]
        self.assertEqual(len(contact_rows), 200)
        self.assertTrue(all(row["disposition"] == "local_sensitive_audit" for row in contact_rows))
        self.assertTrue(all(row["disposition"] == "local_large_regenerable" for row in face_signal_rows))
        self.assertTrue(all(row["disposition"] == "local_intermediate" for row in face_part_rows))


if __name__ == "__main__":
    unittest.main()
