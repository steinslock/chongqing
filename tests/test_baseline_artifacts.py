from __future__ import annotations

import csv
import json
import math
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))


RESULTS_PATH = PROJECT_ROOT / "results" / "baseline_results.csv"
PREDICTIONS_PATH = PROJECT_ROOT / "artifacts" / "baselines" / "baseline_predictions.csv"
AVAILABILITY_PATH = PROJECT_ROOT / "artifacts" / "baselines" / "feature_availability.json"
MANIFEST_PATH = PROJECT_ROOT / "artifacts" / "baselines" / "baseline_run_manifest.json"
REPORT_PATH = PROJECT_ROOT / "reports" / "baseline_report.md"
SPLIT_PATH = PROJECT_ROOT / "artifacts" / "splits" / "subject_splits_v1.csv"


REQUIRED_MODELS = {
    "no_information_majority",
    "no_information_stratified_random",
    "demographics_logistic_regression",
    "demographics_lightgbm",
    "eeg_rest_logistic_regression",
    "eeg_rest_random_forest",
    "eeg_rest_lightgbm",
}

REQUIRED_METRICS = [
    "auroc",
    "auprc",
    "balanced_accuracy",
    "macro_f1",
    "sensitivity",
    "specificity",
    "ppv",
    "npv",
    "brier_score",
    "ece",
    "mce",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class BaselineArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result_rows = read_csv(RESULTS_PATH)
        cls.prediction_rows = read_csv(PREDICTIONS_PATH)
        cls.split_rows = read_csv(SPLIT_PATH)
        cls.availability = json.loads(AVAILABILITY_PATH.read_text(encoding="utf-8"))
        cls.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    def test_required_artifacts_exist(self) -> None:
        for path in [RESULTS_PATH, PREDICTIONS_PATH, AVAILABILITY_PATH, MANIFEST_PATH, REPORT_PATH]:
            self.assertTrue(path.exists(), str(path))
        self.assertTrue((PROJECT_ROOT / "configs" / "baselines").is_dir())
        self.assertTrue((PROJECT_ROOT / "checkpoints" / "baselines").is_dir())

    def test_results_cover_required_models_stages_metrics_and_ci(self) -> None:
        self.assertEqual({row["model"] for row in self.result_rows}, REQUIRED_MODELS)
        self.assertEqual({row["evaluation_stage"] for row in self.result_rows}, {"cv_oof", "locked_test"})
        self.assertEqual(len(self.result_rows), len(REQUIRED_MODELS) * 2)
        for row in self.result_rows:
            for metric in REQUIRED_METRICS:
                for suffix in ["", "_ci_low", "_ci_high"]:
                    column = f"{metric}{suffix}"
                    self.assertIn(column, row)
                    self.assertTrue(math.isfinite(float(row[column])), f"{column} missing for {row['model']}")

    def test_fnirs_and_face_are_explicitly_skipped_without_fake_results(self) -> None:
        availability = {row["dataset"]: row for row in self.availability}
        for dataset in ["fnirs", "face"]:
            self.assertEqual(availability[dataset]["status"], "skipped")
            self.assertIn("No reliable", availability[dataset]["reason"])
        self.assertFalse(any(row["dataset"] in {"fnirs", "face"} for row in self.result_rows))

    def test_predictions_respect_locked_test_boundary(self) -> None:
        locked_lids = {row["L_id"] for row in self.split_rows if row["is_locked_test"] == "1"}
        cv_lids = {row["L_id"] for row in self.split_rows if row["is_locked_test"] == "0"}
        cv_prediction_lids = {row["L_id"] for row in self.prediction_rows if row["evaluation_stage"] == "cv_oof"}
        test_prediction_lids = {row["L_id"] for row in self.prediction_rows if row["evaluation_stage"] == "locked_test"}
        self.assertTrue(cv_prediction_lids.issubset(cv_lids))
        self.assertTrue(test_prediction_lids.issubset(locked_lids))
        self.assertFalse(cv_prediction_lids.intersection(locked_lids))

    def test_manifest_checkpoints_exist(self) -> None:
        self.assertEqual(len(self.manifest["checkpoints"]), len(REQUIRED_MODELS))
        for row in self.manifest["checkpoints"]:
            self.assertTrue(Path(row["path"]).exists(), row["path"])
            self.assertEqual(len(row["sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
