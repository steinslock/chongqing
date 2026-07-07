from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from chongqing_binary.config import load_config
from chongqing_binary.leakage import LeakageError, find_forbidden_feature_columns, validate_feature_columns


class LeakageGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = load_config("configs/smoke.yaml")

    def test_nonclinical_smoke_columns_pass(self) -> None:
        validate_feature_columns(
            self.config.smoke_feature_columns,
            exact=self.config.forbidden_feature_exact,
            patterns=self.config.forbidden_feature_patterns,
        )

    def test_diagnosis_and_label_columns_fail(self) -> None:
        with self.assertRaises(LeakageError):
            validate_feature_columns(
                ["has_EEG", "diag3", "primary_label_nonhealthy"],
                exact=self.config.forbidden_feature_exact,
                patterns=self.config.forbidden_feature_patterns,
            )

    def test_clinical_scale_columns_fail(self) -> None:
        forbidden = [
            "CDRS_score",
            "CES-DC总分：[JH05_30_001323_6376_1]",
            "HAMA总分：[JH05_10_008_453_6385_1]",
            "最近一次自杀尝试日期：[JH05_30_001432_6386_1]",
            "诊断3-他评量表CDRS>=40",
        ]
        findings = find_forbidden_feature_columns(
            forbidden,
            exact=self.config.forbidden_feature_exact,
            patterns=self.config.forbidden_feature_patterns,
        )
        self.assertEqual(len(findings), len(forbidden))
        with self.assertRaises(LeakageError):
            validate_feature_columns(
                forbidden,
                exact=self.config.forbidden_feature_exact,
                patterns=self.config.forbidden_feature_patterns,
            )


if __name__ == "__main__":
    unittest.main()

