#!/usr/bin/env python3
"""Build subject-level audit cohorts and fixed splits from subject_manifest.csv."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from chongqing_binary.audit import (
    COHORT_COLUMNS,
    build_audit_summary,
    build_subject_row,
)
from chongqing_binary.config import load_config
from chongqing_binary.data import load_subject_manifest
from chongqing_binary.reports import (
    write_data_audit_report,
    write_leakage_audit_report,
    write_split_report,
)
from chongqing_binary.splits import build_subject_splits, write_csv, write_sha256


COHORT_FIELDNAMES = [
    "A_id",
    "L_id",
    "diag3",
    "primary_label_nonhealthy",
    "sensitivity_label_clear_diagnosis",
    "sensitivity_label_mdd_highrisk",
    "sex",
    "age",
    "age_bin",
    "grade",
    "grade_group",
    "has_EEG",
    "has_fNIRS",
    "has_face",
    "has_eye_direct",
    "has_eye_name_mapped",
    "modality_count_direct",
    "modality_count_with_eye_name_map",
    "modality_pattern",
    "fnirs_device",
    *COHORT_COLUMNS,
]

SPLIT_FIELDNAMES = [
    "A_id",
    "L_id",
    "split_group",
    "is_locked_test",
    "cv_fold",
    "split_role",
    *COHORT_FIELDNAMES[2:],
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/default.yaml", help="YAML config path.")
    parser.add_argument("--test-fraction", type=float, default=0.20)
    parser.add_argument("--folds", type=int, default=5)
    args = parser.parse_args()

    config = load_config(args.config)
    records = load_subject_manifest(config=config)
    summary, device_by_l_id = build_audit_summary(records, config.paths["raw_data_dir"])

    rows = [build_subject_row(record, device_by_l_id[record.l_id]) for record in records]
    cohort_rows = {cohort: [row for row in rows if row[cohort] == "1"] for cohort in COHORT_COLUMNS}

    cohort_dir = config.output_path("artifacts_dir", "cohorts", ".placeholder").parent
    for cohort, subset in cohort_rows.items():
        write_csv(cohort_dir / f"{cohort}.csv", subset, COHORT_FIELDNAMES)

    split_rows = build_subject_splits(
        rows,
        seed=config.seed,
        test_fraction=args.test_fraction,
        n_folds=args.folds,
    )
    split_path = config.output_path("artifacts_dir", "splits", "subject_splits_v1.csv")
    write_csv(split_path, split_rows, SPLIT_FIELDNAMES)
    sha_path = config.output_path("artifacts_dir", "splits", "subject_splits_v1.sha256")
    digest = write_sha256(sha_path, split_path)

    write_data_audit_report(
        config.output_path("reports_dir", "data_audit.md"),
        summary,
        cohort_rows,
    )
    write_split_report(
        config.output_path("reports_dir", "split_report.md"),
        split_rows,
        cohort_rows,
        digest,
    )
    write_leakage_audit_report(
        config.output_path("reports_dir", "leakage_audit.md"),
        split_rows,
        config.forbidden_feature_exact,
        config.forbidden_feature_patterns,
    )

    print(f"Wrote {split_path}")
    print(f"Wrote {sha_path}")
    print(f"Wrote {cohort_dir}/*.csv")
    print("Wrote reports/data_audit.md, reports/split_report.md, reports/leakage_audit.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

