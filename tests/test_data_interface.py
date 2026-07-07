from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from chongqing_binary.config import load_config
from chongqing_binary.data import (
    balanced_smoke_sample,
    class_counts,
    deterministic_stratified_split,
    feature_matrix,
    labeled_subjects,
    load_subject_manifest,
)


class DataInterfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = load_config("configs/smoke.yaml")
        cls.records = load_subject_manifest(config=cls.config)

    def test_manifest_loads_subject_records(self) -> None:
        self.assertEqual(len(self.records), 4610)
        first = self.records[0]
        self.assertTrue(first.a_id.startswith("A"))
        self.assertTrue(first.l_id.startswith("L"))

    def test_labeled_counts_match_expected_primary_label(self) -> None:
        labeled = labeled_subjects(self.records, self.config.label_column)
        counts = class_counts(labeled, self.config.label_column)
        self.assertEqual(len(labeled), 4498)
        self.assertEqual(counts["0"], 3126)
        self.assertEqual(counts["1"], 1372)

    def test_balanced_smoke_sample_contains_both_classes(self) -> None:
        sample = balanced_smoke_sample(self.records, self.config.label_column, 32)
        counts = class_counts(sample, self.config.label_column)
        self.assertEqual(len(sample), 32)
        self.assertEqual(counts["0"], 16)
        self.assertEqual(counts["1"], 16)

    def test_subject_level_split_and_features(self) -> None:
        sample = balanced_smoke_sample(self.records, self.config.label_column, 32)
        train, test = deterministic_stratified_split(sample, self.config.label_column, 0.25)
        self.assertEqual(len(train) + len(test), 32)
        self.assertFalse({record.l_id for record in train}.intersection(record.l_id for record in test))
        matrix = feature_matrix(test, self.config.smoke_feature_columns)
        self.assertEqual(len(matrix), len(test))
        self.assertEqual(len(matrix[0]), len(self.config.smoke_feature_columns))


if __name__ == "__main__":
    unittest.main()

