from __future__ import annotations

import csv
import hashlib
import sys
import unittest
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))


SPLIT_PATH = PROJECT_ROOT / "artifacts" / "splits" / "subject_splits_v1.csv"
SHA_PATH = PROJECT_ROOT / "artifacts" / "splits" / "subject_splits_v1.sha256"
COHORT_DIR = PROJECT_ROOT / "artifacts" / "cohorts"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class SubjectSplitArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.split_rows = read_csv(SPLIT_PATH)

    def test_required_artifacts_exist(self) -> None:
        self.assertTrue(SPLIT_PATH.exists())
        self.assertTrue(SHA_PATH.exists())
        for name in ["coverage_maximized.csv", "matched_eeg_fnirs_face.csv", "missing_modality.csv"]:
            self.assertTrue((COHORT_DIR / name).exists(), name)
        for name in ["data_audit.md", "split_report.md", "leakage_audit.md"]:
            self.assertTrue((PROJECT_ROOT / "reports" / name).exists(), name)

    def test_split_sha256_matches_file(self) -> None:
        digest = hashlib.sha256(SPLIT_PATH.read_bytes()).hexdigest()
        recorded = SHA_PATH.read_text(encoding="utf-8").split()[0]
        self.assertEqual(recorded, digest)

    def test_split_has_unique_subject_ids(self) -> None:
        a_ids = [row["A_id"] for row in self.split_rows]
        l_ids = [row["L_id"] for row in self.split_rows]
        self.assertEqual(len(a_ids), len(set(a_ids)))
        self.assertEqual(len(l_ids), len(set(l_ids)))

    def test_locked_test_and_cv_pool_do_not_overlap(self) -> None:
        test_rows = [row for row in self.split_rows if row["is_locked_test"] == "1"]
        cv_rows = [row for row in self.split_rows if row["is_locked_test"] == "0"]
        self.assertEqual(len(test_rows), 900)
        self.assertEqual(len(cv_rows), 3597)

        test_a = {row["A_id"] for row in test_rows}
        test_l = {row["L_id"] for row in test_rows}
        cv_a = {row["A_id"] for row in cv_rows}
        cv_l = {row["L_id"] for row in cv_rows}
        self.assertFalse(test_a.intersection(cv_a))
        self.assertFalse(test_l.intersection(cv_l))

    def test_cv_validation_folds_are_subject_disjoint(self) -> None:
        cv_rows = [row for row in self.split_rows if row["is_locked_test"] == "0"]
        fold_counts = Counter(row["cv_fold"] for row in cv_rows)
        self.assertEqual(set(fold_counts), {"0", "1", "2", "3", "4"})
        self.assertEqual(sum(fold_counts.values()), len(cv_rows))

        for fold in range(5):
            val_rows = [row for row in cv_rows if row["cv_fold"] == str(fold)]
            train_rows = [row for row in cv_rows if row["cv_fold"] != str(fold)]
            val_a = {row["A_id"] for row in val_rows}
            val_l = {row["L_id"] for row in val_rows}
            train_a = {row["A_id"] for row in train_rows}
            train_l = {row["L_id"] for row in train_rows}
            self.assertFalse(val_a.intersection(train_a), f"A_id overlap in fold {fold}")
            self.assertFalse(val_l.intersection(train_l), f"L_id overlap in fold {fold}")

    def test_cohort_sizes_and_membership(self) -> None:
        coverage = read_csv(COHORT_DIR / "coverage_maximized.csv")
        matched = read_csv(COHORT_DIR / "matched_eeg_fnirs_face.csv")
        missing = read_csv(COHORT_DIR / "missing_modality.csv")
        self.assertEqual(len(coverage), 4497)
        self.assertEqual(len(matched), 2376)
        self.assertEqual(len(missing), 3837)
        self.assertEqual({row["L_id"] for row in coverage}, {row["L_id"] for row in self.split_rows})
        self.assertTrue({row["L_id"] for row in matched}.issubset({row["L_id"] for row in coverage}))
        self.assertTrue({row["L_id"] for row in missing}.issubset({row["L_id"] for row in coverage}))

    def test_locked_test_warning_is_in_report(self) -> None:
        report = (PROJECT_ROOT / "reports" / "split_report.md").read_text(encoding="utf-8")
        self.assertIn("Locked test set is for final evaluation only", report)
        leakage = (PROJECT_ROOT / "reports" / "leakage_audit.md").read_text(encoding="utf-8")
        self.assertIn("Do not use the locked test set", leakage)


if __name__ == "__main__":
    unittest.main()

