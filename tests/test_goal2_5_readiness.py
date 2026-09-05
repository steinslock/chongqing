from __future__ import annotations

import csv
import glob
import hashlib
import json
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from chongqing_binary.cohorts import CORE3, build_cohort_rows
from chongqing_binary.config import ReadOnlyInputGuard, load_config
from chongqing_binary.eeg.features import qc_and_signal_disjoint
from chongqing_binary.fnirs.devices import direct_raw_merge_allowed
from chongqing_binary.leakage import LeakageError, validate_feature_columns


def read_csv(path: str) -> list[dict[str, str]]:
    with (PROJECT_ROOT / path).open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def read_json(path: str) -> dict:
    return json.loads((PROJECT_ROOT / path).read_text(encoding="utf-8"))


class Goal25ReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.split = read_csv("artifacts/splits/subject_splits_v1.csv")
        cls.split_by_lid = {row["L_id"]: row for row in cls.split}
        cls.task_tables = (
            sorted(glob.glob(str(PROJECT_ROOT / "artifacts/eeg/task_availability_*.csv")))
            + sorted(glob.glob(str(PROJECT_ROOT / "artifacts/fnirs/task_availability_*.csv")))
            + sorted(glob.glob(str(PROJECT_ROOT / "artifacts/face/video_availability_*.csv")))
        )

    def test_raw_input_write_guard_blocks_raw_dataset(self) -> None:
        config = load_config("configs/default.yaml")
        guard = ReadOnlyInputGuard(config.readonly_inputs)
        with self.assertRaises(PermissionError):
            guard.assert_write_allowed(config.paths["raw_data_dir"] / "should_not_write.txt")

    def test_core3_definition_excludes_eye(self) -> None:
        self.assertEqual(CORE3, ("eeg", "fnirs", "face"))
        rows = read_csv("artifacts/cohorts_v2/core3_complete_flag.csv")
        for row in rows[:200]:
            expected = row["has_EEG"] == row["has_fNIRS"] == row["has_face"] == "1"
            self.assertTrue(expected)

    def test_eye_columns_do_not_change_core3_complete(self) -> None:
        rows = read_csv("artifacts/cohorts_v2/core3_any.csv")
        for row in rows:
            expected = int(row["has_EEG"] == "1" and row["has_fNIRS"] == "1" and row["has_face"] == "1")
            self.assertEqual(int(row["core3_complete_flag"]), expected)

    def test_old_cohort_files_remain_separate(self) -> None:
        old_rows = read_csv("artifacts/cohorts/matched_eeg_fnirs_face.csv")
        new_rows = read_csv("artifacts/cohorts_v2/core3_complete_flag.csv")
        self.assertEqual(len(old_rows), 2376)
        self.assertEqual(len(new_rows), 2376)
        self.assertNotIn("core3_complete_qc", old_rows[0])
        self.assertIn("core3_complete_qc", new_rows[0])

    def test_subject_splits_v1_hash_unchanged(self) -> None:
        digest = hashlib.sha256((PROJECT_ROOT / "artifacts/splits/subject_splits_v1.csv").read_bytes()).hexdigest()
        expected = (PROJECT_ROOT / "artifacts/splits/subject_splits_v1.sha256").read_text(encoding="utf-8").split()[0]
        self.assertEqual(digest, expected)

    def test_task_level_l_id_unique(self) -> None:
        for table in self.task_tables:
            rows = read_csv(str(Path(table).relative_to(PROJECT_ROOT)))
            lids = [row["L_id"] for row in rows]
            self.assertEqual(len(lids), len(set(lids)), table)

    def test_task_tables_inherit_global_split(self) -> None:
        split_lids = set(self.split_by_lid)
        for table in self.task_tables:
            rows = read_csv(str(Path(table).relative_to(PROJECT_ROOT)))
            self.assertEqual({row["L_id"] for row in rows}, split_lids, table)
            for row in rows[:50]:
                split = self.split_by_lid[row["L_id"]]
                self.assertEqual(row["split_group"], split["split_group"])
                self.assertEqual(row["cv_fold"], split["cv_fold"])

    def test_pilot_holdout_not_in_smoke(self) -> None:
        for path in ["artifacts/eeg/smoke/smoke_metrics.json", "artifacts/fnirs/smoke/smoke_metrics.json", "artifacts/face/smoke/smoke_metrics.json"]:
            data = read_json(path)
            self.assertFalse(data["pilot_holdout_used"])
            checks = data.get("checks") or data.get("sample_subjects") or []
            for row in checks:
                self.assertEqual(row.get("split_group"), "cv")

    def test_face_two_videos_fold_consistent(self) -> None:
        intro = {row["L_id"]: row for row in read_csv("artifacts/face/video_availability_self_intro.csv")}
        task = {row["L_id"]: row for row in read_csv("artifacts/face/video_availability_task.csv")}
        for lid in self.split_by_lid:
            self.assertEqual(intro[lid]["cv_fold"], task[lid]["cv_fold"])

    def test_eeg_tasks_fold_consistent(self) -> None:
        tables = [read_csv(f"artifacts/eeg/task_availability_{task}.csv") for task in ("rest", "oddball", "1back")]
        by_lid = [{row["L_id"]: row for row in rows} for rows in tables]
        for lid in self.split_by_lid:
            folds = {mapping[lid]["cv_fold"] for mapping in by_lid}
            self.assertEqual(len(folds), 1)

    def test_fnirs_tasks_fold_consistent(self) -> None:
        tables = [read_csv(str(Path(path).relative_to(PROJECT_ROOT))) for path in sorted(glob.glob(str(PROJECT_ROOT / "artifacts/fnirs/task_availability_*.csv")))]
        by_lid = [{row["L_id"]: row for row in rows} for rows in tables]
        for lid in list(self.split_by_lid)[:200]:
            folds = {mapping[lid]["cv_fold"] for mapping in by_lid}
            self.assertEqual(len(folds), 1)

    def test_clinical_fields_blocked_from_features(self) -> None:
        config = load_config("configs/default.yaml")
        with self.assertRaises(LeakageError):
            validate_feature_columns(
                ["diag3", "CDRS_score", "HAMA_total", "feature_ok"],
                exact=config.forbidden_feature_exact,
                patterns=config.forbidden_feature_patterns,
            )

    def test_eeg_qc_and_signal_features_disjoint(self) -> None:
        with (PROJECT_ROOT / "experiments/v1/eeg/artifacts/features/eeg_rest_features.csv").open(newline="", encoding="utf-8") as handle:
            columns = next(csv.reader(handle))
        self.assertTrue(qc_and_signal_disjoint(columns))

    def test_face_clips_do_not_have_independent_folds(self) -> None:
        for path in ["artifacts/face/video_availability_self_intro.csv", "artifacts/face/video_availability_task.csv"]:
            rows = read_csv(path)
            self.assertNotIn("clip_fold", rows[0])
            self.assertNotIn("frame_fold", rows[0])

    def test_fnirs_devices_not_directly_mergeable(self) -> None:
        self.assertFalse(direct_raw_merge_allowed())
        report = (PROJECT_ROOT / "reports/fnirs_device_alignment_audit.md").read_text(encoding="utf-8")
        self.assertIn("Direct same raw channel model: **No**", report)

    def test_smoke_configs_use_cv_pool(self) -> None:
        for path in ["configs/readiness/eeg_smoke.yaml", "configs/readiness/fnirs_smoke.yaml", "configs/readiness/face_smoke.yaml"]:
            text = (PROJECT_ROOT / path).read_text(encoding="utf-8")
            self.assertIn("split_group: cv", text)

    def test_failed_files_have_failure_reason(self) -> None:
        for table in self.task_tables:
            rows = read_csv(str(Path(table).relative_to(PROJECT_ROOT)))
            for row in rows:
                missing_or_failed = any(
                    row.get(col) == "0"
                    for col in ["data_bdf_exists", "raw_file_exists", "file_exists", "data_bdf_readable", "file_readable"]
                    if col in row
                )
                if missing_or_failed:
                    self.assertTrue(row.get("failure_reason"), table)
                    break

    def test_protocol_no_current_goal0_and_pilot_exposed(self) -> None:
        text = "\n".join((PROJECT_ROOT / path).read_text(encoding="utf-8") for path in ["AGENTS.md", "PROJECT_SPEC.md", "EXPERIMENT_PROTOCOL.md"])
        self.assertIn("Goal 2.5", text)
        self.assertIn("baseline-exposed pilot holdout", text)
        self.assertNotIn("Goal0: project initialization only", text)

    def test_cohort_build_deterministic_same_seed(self) -> None:
        rows1, stats1 = build_cohort_rows()
        rows2, stats2 = build_cohort_rows()
        self.assertEqual(stats1, stats2)
        self.assertEqual([row["L_id"] for row in rows1[:200]], [row["L_id"] for row in rows2[:200]])

    def test_subject_level_outputs_keep_l_id(self) -> None:
        for path in [
            "artifacts/baselines/baseline_predictions.csv",
            "experiments/v1/eeg/artifacts/features/eeg_rest_features.csv",
            "artifacts/cohorts_v2/core3_complete_qc.csv",
        ]:
            with (PROJECT_ROOT / path).open(newline="", encoding="utf-8") as handle:
                header = next(csv.reader(handle))
            self.assertIn("L_id", header)

    def test_modality_outputs_merge_unambiguously_with_split(self) -> None:
        split_lids = set(self.split_by_lid)
        for table in self.task_tables:
            rows = read_csv(str(Path(table).relative_to(PROJECT_ROOT)))
            self.assertTrue({row["L_id"] for row in rows}.issubset(split_lids))
            self.assertEqual(len(rows), len(split_lids))


if __name__ == "__main__":
    unittest.main()
