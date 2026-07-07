"""Fixed subject-level test and cross-validation split construction."""

from __future__ import annotations

import csv
import hashlib
from collections import Counter
from pathlib import Path
from typing import Iterable, Sequence

from sklearn.model_selection import StratifiedKFold, StratifiedShuffleSplit


STRATIFICATION_HIERARCHY = [
    ["primary_label_nonhealthy", "sex", "age_bin", "grade_group", "modality_pattern", "fnirs_device"],
    ["primary_label_nonhealthy", "sex", "age_bin", "grade_group", "modality_count_with_eye_name_map", "fnirs_device"],
    ["primary_label_nonhealthy", "sex", "age_bin", "grade_group"],
    ["primary_label_nonhealthy", "sex", "age_bin"],
    ["primary_label_nonhealthy"],
]


def build_subject_splits(
    rows: Sequence[dict[str, str]],
    seed: int,
    test_fraction: float = 0.20,
    n_folds: int = 5,
) -> list[dict[str, str]]:
    """Assign one locked test split and one CV validation fold per non-test subject."""

    eligible = [row for row in rows if row["coverage_maximized"] == "1"]
    eligible = sorted(eligible, key=lambda row: stable_hash(row["L_id"]))
    if not eligible:
        raise ValueError("No coverage-maximized subjects available for splitting.")

    test_labels = make_stratification_labels(eligible, min_count=2)
    splitter = StratifiedShuffleSplit(n_splits=1, test_size=test_fraction, random_state=seed)
    train_idx, test_idx = next(splitter.split([[0]] * len(eligible), test_labels))

    assignments: dict[str, dict[str, str]] = {}
    for index in test_idx:
        row = dict(eligible[index])
        row["split_group"] = "locked_test"
        row["is_locked_test"] = "1"
        row["cv_fold"] = ""
        row["split_role"] = "test_only"
        assignments[row["L_id"]] = row

    cv_rows = [eligible[index] for index in train_idx]
    cv_rows = sorted(cv_rows, key=lambda row: stable_hash(row["L_id"]))
    cv_labels = make_stratification_labels(cv_rows, min_count=n_folds)
    fold_splitter = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=seed)
    for fold, (_, val_idx) in enumerate(fold_splitter.split([[0]] * len(cv_rows), cv_labels)):
        for index in val_idx:
            row = dict(cv_rows[index])
            row["split_group"] = "cv"
            row["is_locked_test"] = "0"
            row["cv_fold"] = str(fold)
            row["split_role"] = "cv_validation_fold"
            assignments[row["L_id"]] = row

    split_rows = [assignments[row["L_id"]] for row in eligible]
    return sorted(split_rows, key=lambda row: (row["split_group"] != "locked_test", row.get("cv_fold", ""), row["L_id"]))


def make_stratification_labels(rows: Sequence[dict[str, str]], min_count: int) -> list[str]:
    """Return deterministic labels with rare fine-grained strata collapsed."""

    counts_by_level = [_counts_for_columns(rows, columns) for columns in STRATIFICATION_HIERARCHY]
    labels: list[str] = []
    for row in rows:
        label = None
        for columns, counts in zip(STRATIFICATION_HIERARCHY, counts_by_level):
            key = _key(row, columns)
            if counts[key] >= min_count:
                label = key
                break
        labels.append(label or row["primary_label_nonhealthy"])
    final_counts = Counter(labels)
    rare = {key for key, count in final_counts.items() if count < min_count}
    if rare:
        labels = [row["primary_label_nonhealthy"] if label in rare else label for row, label in zip(rows, labels)]
    return labels


def write_csv(path: Path, rows: Sequence[dict[str, str]], fieldnames: Sequence[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        seen: list[str] = []
        for row in rows:
            for key in row:
                if key not in seen:
                    seen.append(key)
        fieldnames = seen
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_sha256(path: Path, target: Path) -> str:
    digest = sha256_file(target)
    path.write_text(f"{digest}  {target.name}\n", encoding="utf-8")
    return digest


def distribution(rows: Iterable[dict[str, str]], column: str) -> dict[str, int]:
    return dict(Counter(row.get(column, "[missing]") or "[missing]" for row in rows))


def stable_hash(value: str) -> int:
    return int(hashlib.sha1(value.encode("utf-8")).hexdigest(), 16)


def _counts_for_columns(rows: Sequence[dict[str, str]], columns: Sequence[str]) -> Counter[str]:
    return Counter(_key(row, columns) for row in rows)


def _key(row: dict[str, str], columns: Sequence[str]) -> str:
    return "|".join(row.get(column, "[missing]") or "[missing]" for column in columns)

