from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from chongqing_binary.config import ReadOnlyInputGuard, load_config
from chongqing_binary.goal2_6.config import load_goal_config as load_goal2_6_config
from chongqing_binary.goal2_7.config import load_goal_config as load_goal2_7_config
from chongqing_binary.paths import RAW_DATA_ENV
from chongqing_binary.readiness import load_readiness_config, raw_data_dir


class ConfigTests(unittest.TestCase):
    def test_load_default_config(self) -> None:
        config = load_config("configs/default.yaml")
        self.assertEqual(config.label_column, "primary_label_nonhealthy")
        self.assertTrue(config.paths["subject_manifest"].exists())
        self.assertGreaterEqual(len(config.readonly_inputs), 2)

    def test_smoke_config_extends_default(self) -> None:
        config = load_config("configs/smoke.yaml")
        self.assertEqual(config.smoke_limit, 32)
        self.assertIn("has_EEG", config.smoke_feature_columns)
        self.assertTrue(config.paths["raw_data_dir"].exists())

    def test_readonly_guard_blocks_input_writes(self) -> None:
        config = load_config("configs/default.yaml")
        guard = ReadOnlyInputGuard(config.readonly_inputs)
        with self.assertRaises(PermissionError):
            guard.assert_write_allowed(config.paths["raw_data_dir"] / "should_not_write.txt")
        with self.assertRaises(PermissionError):
            guard.assert_write_allowed(config.paths["report_input_dir"] / "should_not_write.txt")

    def test_output_paths_are_allowed(self) -> None:
        config = load_config("configs/default.yaml")
        path = config.output_path("artifacts_dir", "unit_test", "placeholder.json")
        self.assertTrue(str(path).endswith("artifacts/unit_test/placeholder.json"))

    def test_raw_data_environment_override_reaches_all_config_loaders(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            override = Path(tmpdir).resolve()
            with patch.dict(os.environ, {RAW_DATA_ENV: str(override)}):
                project = load_config("configs/default.yaml")
                readiness = load_readiness_config("configs/readiness/default.yaml")
                goal2_6 = load_goal2_6_config("configs/goal2_6/models.yaml")
                goal2_7 = load_goal2_7_config("configs/goal2_7/models.yaml")

            self.assertEqual(project.paths["raw_data_dir"], override)
            self.assertIn(override, project.readonly_inputs)
            self.assertEqual(raw_data_dir(readiness), override)
            self.assertIn(str(override), {str(path) for path in readiness["readonly_inputs"]})
            self.assertEqual(Path(goal2_6["paths"]["raw_data_dir"]), override)
            self.assertIn(str(override), {str(path) for path in goal2_6["readonly_inputs"]})
            self.assertEqual(Path(goal2_7["paths"]["raw_data_dir"]), override)
            self.assertIn(str(override), {str(path) for path in goal2_7["readonly_inputs"]})

            guard = ReadOnlyInputGuard(project.readonly_inputs)
            with self.assertRaises(PermissionError):
                guard.assert_write_allowed(override / "should_not_write.txt")

    def test_raw_data_environment_override_must_be_absolute(self) -> None:
        with patch.dict(os.environ, {RAW_DATA_ENV: "relative/data"}):
            with self.assertRaisesRegex(ValueError, RAW_DATA_ENV):
                load_config("configs/default.yaml")


if __name__ == "__main__":
    unittest.main()
