from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from chongqing_binary.config import ReadOnlyInputGuard, load_config


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


if __name__ == "__main__":
    unittest.main()

