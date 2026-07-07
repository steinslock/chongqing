"""Subject-level data interface for the Chongqing manifest."""

from __future__ import annotations

import csv
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from .config import ProjectConfig


REQUIRED_MANIFEST_COLUMNS = {
    "A_id",
    "L_id",
    "diag3",
    "primary_label_nonhealthy",
    "sensitivity_label_clear_diagnosis",
    "sensitivity_label_mdd_highrisk",
    "sex",
    "age",
    "grade",
    "has_EEG",
    "has_fNIRS",
    "has_face",
    "has_eye_direct",
    "has_eye_name_mapped",
}


@dataclass(frozen=True)
class SubjectRecord:
    """One anonymized subject row from `subject_manifest.csv`."""

    fields: Mapping[str, str]

    @property
    def a_id(self) -> str:
        return self.fields["A_id"]

    @property
    def l_id(self) -> str:
        return self.fields["L_id"]

    def value(self, column: str, default: str = "") -> str:
        return self.fields.get(column, default)

    def label(self, column: str) -> str:
        return self.value(column).strip()

    def has_modality(self, column: str) -> bool:
        return self.value(column) == "1"

    def numeric_feature(self, column: str) -> float:
        value = self.value(column, "0").strip()
        if value in {"", "#N/A", "NA", "nan"}:
            return 0.0
        return float(value)


def load_subject_manifest(path: str | Path | None = None, config: ProjectConfig | None = None) -> list[SubjectRecord]:
    """Load the canonical subject manifest without requiring pandas."""

    manifest_path = Path(path) if path is not None else config.paths["subject_manifest"] if config else None
    if manifest_path is None:
        raise ValueError("Either path or config must be provided.")
    with manifest_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"Manifest has no header: {manifest_path}")
        missing = REQUIRED_MANIFEST_COLUMNS.difference(reader.fieldnames)
        if missing:
            raise ValueError(f"Manifest missing required columns: {sorted(missing)}")
        return [SubjectRecord(dict(row)) for row in reader]


def labeled_subjects(records: Iterable[SubjectRecord], label_column: str) -> list[SubjectRecord]:
    """Keep subjects with binary labels only."""

    return [record for record in records if record.label(label_column) in {"0", "1"}]


def class_counts(records: Iterable[SubjectRecord], label_column: str) -> dict[str, int]:
    counts = {"0": 0, "1": 0}
    for record in records:
        label = record.label(label_column)
        if label in counts:
            counts[label] += 1
    return counts


def balanced_smoke_sample(
    records: Sequence[SubjectRecord],
    label_column: str,
    limit: int,
) -> list[SubjectRecord]:
    """Return a small deterministic class-balanced sample for wiring tests."""

    labeled = labeled_subjects(records, label_column)
    negatives = [record for record in labeled if record.label(label_column) == "0"]
    positives = [record for record in labeled if record.label(label_column) == "1"]
    if not negatives or not positives:
        raise ValueError("Smoke sample requires both classes.")

    per_class = max(1, limit // 2)
    sample = negatives[:per_class] + positives[:per_class]
    return sorted(sample[:limit], key=lambda record: _stable_hash(record.l_id))


def deterministic_stratified_split(
    records: Sequence[SubjectRecord],
    label_column: str,
    test_fraction: float,
) -> tuple[list[SubjectRecord], list[SubjectRecord]]:
    """Create a tiny deterministic subject-level split for smoke tests."""

    train: list[SubjectRecord] = []
    test: list[SubjectRecord] = []
    for label in ("0", "1"):
        group = [record for record in records if record.label(label_column) == label]
        group = sorted(group, key=lambda record: _stable_hash(record.l_id))
        n_test = max(1, round(len(group) * test_fraction))
        test.extend(group[:n_test])
        train.extend(group[n_test:])
    return train, test


def feature_matrix(records: Sequence[SubjectRecord], feature_columns: Sequence[str]) -> list[list[float]]:
    return [[record.numeric_feature(column) for column in feature_columns] for record in records]


def label_vector(records: Sequence[SubjectRecord], label_column: str) -> list[int]:
    return [int(record.label(label_column)) for record in records]


def _stable_hash(value: str) -> int:
    return int(hashlib.sha1(value.encode("utf-8")).hexdigest(), 16)

