from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from chongqing_binary.baselines import (
    build_datasets,
    load_baseline_settings,
    load_split_frame,
    model_keys_for_dataset,
)
from chongqing_binary.config import load_config
from chongqing_binary.leakage import LeakageError, validate_feature_columns


class BaselineConfigTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.project_config = load_config("configs/default.yaml")
        cls.settings = load_baseline_settings("configs/baselines/smoke.yaml")
        cls.split = load_split_frame(PROJECT_ROOT / "artifacts" / "splits" / "subject_splits_v1.csv", cls.project_config.label_column)

    def test_config_declares_required_model_families(self) -> None:
        models = self.settings["models"]
        self.assertIn("majority", models["no_information"])
        self.assertIn("stratified_random", models["no_information"])
        self.assertIn("logistic_regression", models["demographics"])
        self.assertIn("lightgbm", models["demographics"])
        self.assertIn("logistic_regression", models["tabular_numeric"])
        self.assertIn("random_forest", models["tabular_numeric"])
        self.assertIn("lightgbm", models["tabular_numeric"])

    def test_available_dataset_features_pass_leakage_guard(self) -> None:
        datasets, availability = build_datasets(self.split, self.settings, self.project_config, smoke_limit=16)
        self.assertTrue(any(row["dataset"] == "fnirs" and row["status"] == "skipped" for row in availability))
        self.assertTrue(any(row["dataset"] == "face" and row["status"] == "skipped" for row in availability))
        for dataset in datasets:
            validate_feature_columns(
                dataset.feature_columns,
                exact=self.project_config.forbidden_feature_exact,
                patterns=self.project_config.forbidden_feature_patterns,
            )

    def test_clinical_fields_still_fail_in_baseline_context(self) -> None:
        with self.assertRaises(LeakageError):
            validate_feature_columns(
                ["age_clean", "sex_clean", "CDRS_score", "diag3", "suicide_attempt"],
                exact=self.project_config.forbidden_feature_exact,
                patterns=self.project_config.forbidden_feature_patterns,
            )

    def test_dataset_model_mapping_is_explicit(self) -> None:
        datasets, _ = build_datasets(self.split, self.settings, self.project_config, smoke_limit=16)
        mapping = {dataset.name: model_keys_for_dataset(dataset, self.settings) for dataset in datasets}
        self.assertEqual(mapping["no_information"], ["majority", "stratified_random"])
        self.assertEqual(mapping["demographics"], ["logistic_regression", "lightgbm"])
        self.assertEqual(mapping["eeg_rest"], ["logistic_regression", "random_forest", "lightgbm"])


if __name__ == "__main__":
    unittest.main()
