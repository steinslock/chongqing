"""Markdown report rendering for data audit and splits."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Mapping, Sequence

from .audit import AuditSummary, COHORT_COLUMNS, LABEL_COLUMNS, MODALITY_COLUMNS
from .splits import distribution


def write_data_audit_report(path: Path, summary: AuditSummary, cohort_rows: Mapping[str, Sequence[dict[str, str]]]) -> None:
    lines: list[str] = [
        "# Chongqing Subject-Level Data Audit",
        "",
        "## Technical Summary",
        "",
        f"- Manifest subjects: `{summary.n_subjects}`.",
        f"- Duplicate `A_id` count: `{len(summary.duplicate_a_ids)}`.",
        f"- Duplicate `L_id` count: `{len(summary.duplicate_l_ids)}`.",
        "- Audit scope: subject manifest, modality coverage flags, demographic fields, fNIRS device inferred from raw path metadata, and metadata-level duplicate file checks.",
        "",
        "## Label Counts",
        "",
    ]
    for column in LABEL_COLUMNS:
        lines.extend(_count_table(column, summary.label_counts[column]))

    lines.extend(["## Modality Coverage", ""])
    for column in MODALITY_COLUMNS:
        lines.extend(_count_table(column, summary.modality_counts[column]))

    lines.extend(["## Cohort Sizes", "", "| Cohort | Subjects |", "|---|---:|"])
    for cohort, rows in cohort_rows.items():
        lines.append(f"| `{cohort}` | {len(rows)} |")

    lines.extend(["", "## Demographics", ""])
    demographics = summary.demographics
    lines.extend(_count_table("sex", demographics["sex_counts"]))  # type: ignore[index]
    lines.extend(_count_table("age_bin", demographics["age_bin_counts"]))  # type: ignore[index]
    lines.extend(_count_table("grade_group", demographics["grade_group_counts"]))  # type: ignore[index]
    missing = demographics["missing_demographics"]  # type: ignore[index]
    lines.extend(["### Missing Demographics", "", "| Field | Missing rows |", "|---|---:|"])
    for key, value in missing.items():
        lines.append(f"| `{key}` | {value} |")
    abnormal = demographics["abnormal_age_rows"]  # type: ignore[index]
    lines.extend(["", "### Abnormal Age Rows", ""])
    lines.append(f"- Rows with missing, non-numeric, `<9`, or `>20` age: `{len(abnormal)}`.")
    if abnormal:
        lines.extend(["", "| A_id | L_id | age |", "|---|---|---:|"])
        for row in abnormal[:30]:
            lines.append(f"| `{row['A_id']}` | `{row['L_id']}` | `{row['age']}` |")
        if len(abnormal) > 30:
            lines.append(f"| ... | ... | {len(abnormal) - 30} more |")

    lines.extend(["", "## fNIRS Device Coverage", ""])
    lines.extend(_count_table("fnirs_device", summary.fnirs_device_counts))

    lines.extend(["## Duplicate File Checks", ""])
    lines.append("These are metadata-level checks; large raw files were not content-hashed.")
    lines.append("")
    lines.append("### EEG Role Files")
    lines.append("")
    lines.append("| Task | Subject dirs | Duplicate data role | Duplicate evt role | Missing data role | Missing evt role |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for task, task_summary in summary.duplicate_file_summary["eeg"].items():  # type: ignore[index]
        lines.append(
            f"| `{task}` | {task_summary['subject_dirs']} | {task_summary['duplicate_data_role_count']} | "
            f"{task_summary['duplicate_evt_role_count']} | {task_summary['missing_data_role_count']} | {task_summary['missing_evt_role_count']} |"
        )

    lines.append("")
    lines.append("### Face MP4 Files")
    lines.append("")
    lines.append("| Task | L_ids | Duplicate L_id count |")
    lines.append("|---|---:|---:|")
    for task, task_summary in summary.duplicate_file_summary["face"].items():  # type: ignore[index]
        lines.append(f"| `{task}` | {task_summary['mp4_l_ids']} | {task_summary['duplicate_l_id_count']} |")

    lines.append("")
    lines.append("### fNIRS Subject Directories")
    lines.append("")
    lines.append("| Source task | Subject dirs with L_id | Duplicate L_id dir count | `.nirs` L_ids | Duplicate `.nirs` L_id count |")
    lines.append("|---|---:|---:|---:|---:|")
    for task, task_summary in summary.duplicate_file_summary["fnirs"].items():  # type: ignore[index]
        lines.append(
            f"| `{task}` | {task_summary['subject_dirs_with_l_id']} | {task_summary['duplicate_l_id_dir_count']} | "
            f"{task_summary['nirs_files_with_l_id']} | {task_summary['duplicate_nirs_file_l_id_count']} |"
        )

    lines.append("")
    lines.append("### Eye-Tracking Files")
    lines.append("")
    lines.append("Eye-tracking raw paths mostly do not contain stable `L_id`; this is a filename-level duplicate check.")
    lines.append("")
    lines.append("| Source | Files | Unique stems | Duplicate stem count | L_ids in paths |")
    lines.append("|---|---:|---:|---:|---:|")
    for source, source_summary in summary.duplicate_file_summary["eye"].items():  # type: ignore[index]
        lines.append(
            f"| `{source}` | {source_summary['files']} | {source_summary['stems']} | "
            f"{source_summary['duplicate_stem_count']} | {source_summary['l_ids_in_paths']} |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- `A_id` and `L_id` uniqueness should remain a hard gate before any model run.",
            "- `primary_label_nonhealthy` is the default split label; sensitivity labels are counted here but not used for split assignment.",
            "- fNIRS device balance is approximate because device is inferred from raw path metadata and some manifest fNIRS rows have unknown device source.",
            "- Eye-tracking direct and name-mapped coverage are kept separate. The split uses name-mapped eye coverage for the four-modality missingness pattern.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def write_split_report(path: Path, split_rows: Sequence[dict[str, str]], cohort_rows: Mapping[str, Sequence[dict[str, str]]], sha256: str) -> None:
    locked = [row for row in split_rows if row["is_locked_test"] == "1"]
    cv = [row for row in split_rows if row["is_locked_test"] == "0"]
    lines = [
        "# Subject Split Report",
        "",
        "## Technical Summary",
        "",
        f"- Split file: `artifacts/splits/subject_splits_v1.csv`.",
        f"- SHA256: `{sha256}`.",
        f"- Eligible coverage-maximized subjects: `{len(split_rows)}`.",
        f"- Locked test subjects: `{len(locked)}` ({len(locked) / len(split_rows):.1%}).",
        f"- Cross-validation pool subjects: `{len(cv)}` ({len(cv) / len(split_rows):.1%}).",
        "- Locked test set is for final evaluation only and must not be used for model selection.",
        "- Each non-test subject is assigned exactly one validation fold; for fold `k`, train on non-test subjects where `cv_fold != k` and validate on `cv_fold == k`.",
        "",
        "## Cohort Membership",
        "",
        "| Cohort | Subjects |",
        "|---|---:|",
    ]
    for cohort, rows in cohort_rows.items():
        lines.append(f"| `{cohort}` | {len(rows)} |")

    lines.extend(["", "## Split Sizes", "", "| Split | Subjects |", "|---|---:|"])
    lines.append(f"| locked_test | {len(locked)} |")
    lines.append(f"| cv_pool | {len(cv)} |")
    for fold in range(5):
        count = sum(1 for row in cv if row["cv_fold"] == str(fold))
        lines.append(f"| cv_fold_{fold}_validation | {count} |")

    for column in [
        "primary_label_nonhealthy",
        "sex",
        "age_bin",
        "grade_group",
        "modality_pattern",
        "fnirs_device",
    ]:
        lines.extend(["", f"## Distribution: `{column}`", ""])
        lines.extend(_split_distribution_table(split_rows, column))

    lines.extend(
        [
            "",
            "## Balancing Notes",
            "",
            "- Split assignment used deterministic stratification labels that prioritize primary label, sex, age bin, grade group, modality pattern, and fNIRS device.",
            "- Rare fine-grained strata were collapsed to coarser labels so that the 20% test split and 5-fold CV remain feasible.",
            "- The split is deterministic for seed `20260707` and should be treated as fixed for downstream experiments.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def write_leakage_audit_report(path: Path, split_rows: Sequence[dict[str, str]], forbidden_exact: Sequence[str], forbidden_patterns: Sequence[str]) -> None:
    split_columns = list(split_rows[0].keys()) if split_rows else []
    label_columns_present = [column for column in split_columns if column in LABEL_COLUMNS or column == "diag3"]
    lines = [
        "# Leakage Audit",
        "",
        "## Technical Summary",
        "",
        "- No model training was run in this stage.",
        "- Cohort and split artifacts retain labels and diagnosis fields only for auditing, stratification, and future evaluation joins.",
        "- Feature inputs for the Goal0 smoke path remain limited to non-clinical modality availability fields.",
        "- Automated tests cover forbidden clinical/diagnosis feature detection and split ID non-overlap.",
        "",
        "## Forbidden Feature Policy",
        "",
        "Exact forbidden fields:",
        "",
    ]
    lines.extend([f"- `{value}`" for value in forbidden_exact])
    lines.extend(["", "Forbidden patterns:", ""])
    lines.extend([f"- `{value}`" for value in forbidden_patterns])

    lines.extend(
        [
            "",
            "## Split Artifact Label Columns",
            "",
            "The split file intentionally includes the following label/diagnosis columns for auditability, not as model features:",
            "",
        ]
    )
    lines.extend([f"- `{column}`" for column in label_columns_present])
    lines.extend(
        [
            "",
            "## Required Downstream Use",
            "",
            "- Before feature matrices are accepted, run `validate_feature_columns` from `src/chongqing_binary/leakage.py`.",
            "- Do not include CDRS, CES-DC, HAMA, SCARED, suicide/self-harm, diagnosis, label, manual review, or clinical scale total columns in model inputs.",
            "- Do not use the locked test set for feature selection, hyperparameter tuning, threshold selection, early stopping, model family choice, or any other model-selection decision.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def _count_table(name: str, counts: Mapping[str, int]) -> list[str]:
    lines = [f"### `{name}`", "", "| Value | Count |", "|---|---:|"]
    for key, value in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"| `{key}` | {value} |")
    lines.append("")
    return lines


def _split_distribution_table(rows: Sequence[dict[str, str]], column: str) -> list[str]:
    groups = {
        "all": list(rows),
        "locked_test": [row for row in rows if row["is_locked_test"] == "1"],
        "cv_pool": [row for row in rows if row["is_locked_test"] == "0"],
    }
    for fold in range(5):
        groups[f"cv_fold_{fold}"] = [row for row in rows if row.get("cv_fold") == str(fold)]
    values = sorted({row.get(column, "[missing]") or "[missing]" for row in rows})
    lines = ["| Value | " + " | ".join(groups.keys()) + " |"]
    lines.append("|---|" + "|".join(["---:"] * len(groups)) + "|")
    distributions = {name: Counter(row.get(column, "[missing]") or "[missing]" for row in group) for name, group in groups.items()}
    for value in values:
        counts = [distributions[name].get(value, 0) for name in groups]
        lines.append(f"| `{value}` | " + " | ".join(str(count) for count in counts) + " |")
    return lines
