"""Data audit and cohort construction for the Chongqing manifest."""

from __future__ import annotations

import os
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from .data import SubjectRecord


LABEL_COLUMNS = [
    "primary_label_nonhealthy",
    "sensitivity_label_clear_diagnosis",
    "sensitivity_label_mdd_highrisk",
]

MODALITY_COLUMNS = [
    "has_EEG",
    "has_fNIRS",
    "has_face",
    "has_eye_direct",
    "has_eye_name_mapped",
]

COHORT_COLUMNS = [
    "coverage_maximized",
    "matched_eeg_fnirs_face",
    "missing_modality",
]

CORE_MODALITY_COLUMNS_WITH_MAPPED_EYE = [
    "has_EEG",
    "has_fNIRS",
    "has_face",
    "has_eye_name_mapped",
]


@dataclass(frozen=True)
class AuditSummary:
    n_subjects: int
    duplicate_a_ids: dict[str, int]
    duplicate_l_ids: dict[str, int]
    label_counts: dict[str, dict[str, int]]
    modality_counts: dict[str, dict[str, int]]
    demographics: dict[str, object]
    fnirs_device_counts: dict[str, int]
    duplicate_file_summary: dict[str, object]


def verify_unique_ids(records: Sequence[SubjectRecord]) -> tuple[dict[str, int], dict[str, int]]:
    a_counts = Counter(record.a_id for record in records)
    l_counts = Counter(record.l_id for record in records)
    duplicate_a = {key: count for key, count in a_counts.items() if count > 1}
    duplicate_l = {key: count for key, count in l_counts.items() if count > 1}
    return duplicate_a, duplicate_l


def count_values(records: Iterable[SubjectRecord], column: str) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for record in records:
        value = record.value(column).strip()
        counts[value if value else "[missing]"] += 1
    return dict(counts)


def label_count_summary(records: Sequence[SubjectRecord]) -> dict[str, dict[str, int]]:
    return {column: count_values(records, column) for column in LABEL_COLUMNS}


def modality_count_summary(records: Sequence[SubjectRecord]) -> dict[str, dict[str, int]]:
    summary: dict[str, dict[str, int]] = {}
    for column in MODALITY_COLUMNS:
        counts = count_values(records, column)
        summary[column] = {"1": counts.get("1", 0), "0": counts.get("0", 0), "[missing]": counts.get("[missing]", 0)}
    return summary


def is_labeled(record: SubjectRecord, label_column: str = "primary_label_nonhealthy") -> bool:
    return record.label(label_column) in {"0", "1"}


def normalize_missing(value: str) -> str:
    value = value.strip()
    if value in {"", "#N/A", "NA", "N/A", "nan", "None"}:
        return "[missing]"
    return value


def parse_age(value: str) -> int | None:
    value = normalize_missing(value)
    if value == "[missing]":
        return None
    try:
        return int(float(value))
    except ValueError:
        return None


def age_bin(age_value: str) -> str:
    age = parse_age(age_value)
    if age is None:
        return "age_missing"
    if age < 9 or age > 20:
        return "age_abnormal"
    if age <= 11:
        return "age_09_11"
    if age <= 14:
        return "age_12_14"
    if age <= 17:
        return "age_15_17"
    return "age_18_20"


def grade_group(grade: str) -> str:
    grade = normalize_missing(grade)
    if grade == "[missing]":
        return "grade_missing"
    if grade in {"四年级", "五年级", "六年级"}:
        return "primary"
    if grade in {"七年级", "八年级", "九年级"}:
        return "middle"
    if grade in {"十年级", "十一年级", "十二年级"}:
        return "high"
    return "grade_other"


def modality_pattern(record: SubjectRecord) -> str:
    bits = [
        "E" if record.value("has_EEG") == "1" else "e",
        "N" if record.value("has_fNIRS") == "1" else "n",
        "F" if record.value("has_face") == "1" else "f",
        "Y" if record.value("has_eye_name_mapped") == "1" else "y",
    ]
    return "".join(bits)


def modality_count_mapped_eye(record: SubjectRecord) -> int:
    return sum(1 for column in CORE_MODALITY_COLUMNS_WITH_MAPPED_EYE if record.value(column) == "1")


def build_cohort_flags(record: SubjectRecord, label_column: str = "primary_label_nonhealthy") -> dict[str, int]:
    labeled = is_labeled(record, label_column)
    any_modality = any(record.value(column) == "1" for column in CORE_MODALITY_COLUMNS_WITH_MAPPED_EYE)
    all_core_with_eye = all(record.value(column) == "1" for column in CORE_MODALITY_COLUMNS_WITH_MAPPED_EYE)
    eeg_fnirs_face = all(record.value(column) == "1" for column in ["has_EEG", "has_fNIRS", "has_face"])
    coverage_maximized = int(labeled and any_modality)
    return {
        "coverage_maximized": coverage_maximized,
        "matched_eeg_fnirs_face": int(labeled and eeg_fnirs_face),
        "missing_modality": int(bool(coverage_maximized) and not all_core_with_eye),
    }


def build_subject_row(record: SubjectRecord, fnirs_device: str) -> dict[str, str]:
    flags = build_cohort_flags(record)
    row = {
        "A_id": record.a_id,
        "L_id": record.l_id,
        "diag3": record.value("diag3"),
        "primary_label_nonhealthy": record.value("primary_label_nonhealthy"),
        "sensitivity_label_clear_diagnosis": record.value("sensitivity_label_clear_diagnosis"),
        "sensitivity_label_mdd_highrisk": record.value("sensitivity_label_mdd_highrisk"),
        "sex": normalize_missing(record.value("sex")),
        "age": normalize_missing(record.value("age")),
        "age_bin": age_bin(record.value("age")),
        "grade": normalize_missing(record.value("grade")),
        "grade_group": grade_group(record.value("grade")),
        "has_EEG": record.value("has_EEG"),
        "has_fNIRS": record.value("has_fNIRS"),
        "has_face": record.value("has_face"),
        "has_eye_direct": record.value("has_eye_direct"),
        "has_eye_name_mapped": record.value("has_eye_name_mapped"),
        "modality_count_direct": record.value("modality_count_direct"),
        "modality_count_with_eye_name_map": record.value("modality_count_with_eye_name_map"),
        "modality_pattern": modality_pattern(record),
        "fnirs_device": fnirs_device,
    }
    row.update({key: str(value) for key, value in flags.items()})
    return row


def demographic_summary(records: Sequence[SubjectRecord]) -> dict[str, object]:
    age_values = [parse_age(record.value("age")) for record in records]
    abnormal_ages = [
        {"A_id": record.a_id, "L_id": record.l_id, "age": record.value("age")}
        for record, age in zip(records, age_values)
        if age is None or age < 9 or age > 20
    ]
    missing_demographics = {
        "sex": sum(1 for record in records if normalize_missing(record.value("sex")) == "[missing]"),
        "age": sum(1 for record in records if parse_age(record.value("age")) is None),
        "grade": sum(1 for record in records if normalize_missing(record.value("grade")) == "[missing]"),
    }
    return {
        "sex_counts": count_values(records, "sex"),
        "age_counts": count_values(records, "age"),
        "age_bin_counts": dict(Counter(age_bin(record.value("age")) for record in records)),
        "grade_counts": count_values(records, "grade"),
        "grade_group_counts": dict(Counter(grade_group(record.value("grade")) for record in records)),
        "abnormal_age_rows": abnormal_ages,
        "missing_demographics": missing_demographics,
    }


def infer_fnirs_devices(raw_data_dir: Path) -> dict[str, str]:
    """Infer fNIRS device coverage per L_id from directory and file names."""

    fnirs_dir = raw_data_dir / "近红外"
    vendor_map = {
        "依瑞德近红外": "yiruid",
        "必可明近红外": "bikom",
    }
    per_l_id: dict[str, set[str]] = defaultdict(set)
    for vendor_dir_name, vendor_code in vendor_map.items():
        vendor_dir = fnirs_dir / vendor_dir_name
        if not vendor_dir.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(vendor_dir):
            path_text = str(dirpath)
            for l_id in _extract_l_ids(path_text):
                per_l_id[l_id].add(vendor_code)
            for name in dirnames:
                for l_id in _extract_l_ids(name):
                    per_l_id[l_id].add(vendor_code)
            for name in filenames:
                for l_id in _extract_l_ids(name):
                    per_l_id[l_id].add(vendor_code)
    result: dict[str, str] = {}
    for l_id, devices in per_l_id.items():
        if devices == {"yiruid"}:
            result[l_id] = "yiruid"
        elif devices == {"bikom"}:
            result[l_id] = "bikom"
        elif devices:
            result[l_id] = "both"
    return result


def attach_fnirs_device(records: Sequence[SubjectRecord], inferred_devices: Mapping[str, str]) -> dict[str, str]:
    device_by_l_id: dict[str, str] = {}
    for record in records:
        if record.value("has_fNIRS") != "1":
            device = "none"
        else:
            device = inferred_devices.get(record.l_id, "unknown")
        device_by_l_id[record.l_id] = device
    return device_by_l_id


def duplicate_file_summary(raw_data_dir: Path) -> dict[str, object]:
    """Metadata-level duplicate checks without hashing large raw files."""

    return {
        "eeg": _eeg_duplicate_summary(raw_data_dir / "脑电"),
        "face": _face_duplicate_summary(raw_data_dir / "面部"),
        "fnirs": _fnirs_duplicate_summary(raw_data_dir / "近红外"),
        "eye": _eye_duplicate_summary(raw_data_dir / "眼动"),
    }


def build_audit_summary(records: Sequence[SubjectRecord], raw_data_dir: Path) -> tuple[AuditSummary, dict[str, str]]:
    duplicate_a, duplicate_l = verify_unique_ids(records)
    inferred_devices = infer_fnirs_devices(raw_data_dir)
    device_by_l_id = attach_fnirs_device(records, inferred_devices)
    summary = AuditSummary(
        n_subjects=len(records),
        duplicate_a_ids=duplicate_a,
        duplicate_l_ids=duplicate_l,
        label_counts=label_count_summary(records),
        modality_counts=modality_count_summary(records),
        demographics=demographic_summary(records),
        fnirs_device_counts=dict(Counter(device_by_l_id.values())),
        duplicate_file_summary=duplicate_file_summary(raw_data_dir),
    )
    return summary, device_by_l_id


def _eeg_duplicate_summary(eeg_dir: Path) -> dict[str, object]:
    tasks = {
        "rest": "1_rest-1334",
        "oddball": "2_Oldball-2358",
        "1back": "4_1BACK-1810",
    }
    result: dict[str, object] = {}
    for task_name, task_dir_name in tasks.items():
        task_dir = eeg_dir / task_dir_name
        duplicate_data_roles: list[str] = []
        duplicate_evt_roles: list[str] = []
        missing_data_roles = 0
        missing_evt_roles = 0
        n_subject_dirs = 0
        if task_dir.exists():
            for subject_dir in task_dir.iterdir():
                if not subject_dir.is_dir():
                    continue
                n_subject_dirs += 1
                bdfs = sorted(subject_dir.glob("*.bdf"))
                data_files = [path for path in bdfs if path.name.lower() == "data.bdf" or path.name.lower().endswith("_data.bdf")]
                evt_files = [path for path in bdfs if path.name.lower() == "evt.bdf" or path.name.lower().endswith("_evt.bdf")]
                if len(data_files) > 1:
                    duplicate_data_roles.append(subject_dir.name)
                if len(evt_files) > 1:
                    duplicate_evt_roles.append(subject_dir.name)
                if not data_files:
                    missing_data_roles += 1
                if not evt_files:
                    missing_evt_roles += 1
        result[task_name] = {
            "subject_dirs": n_subject_dirs,
            "duplicate_data_role_subjects": duplicate_data_roles[:20],
            "duplicate_data_role_count": len(duplicate_data_roles),
            "duplicate_evt_role_subjects": duplicate_evt_roles[:20],
            "duplicate_evt_role_count": len(duplicate_evt_roles),
            "missing_data_role_count": missing_data_roles,
            "missing_evt_role_count": missing_evt_roles,
        }
    return result


def _face_duplicate_summary(face_dir: Path) -> dict[str, object]:
    result: dict[str, object] = {}
    for task_dir_name in ["面部1-自我介绍1分钟", "面部2-任务"]:
        task_dir = face_dir / task_dir_name
        counts: Counter[str] = Counter()
        if task_dir.exists():
            for path in task_dir.glob("*.mp4"):
                ids = _extract_l_ids(path.stem)
                if ids:
                    counts[ids[0]] += 1
        duplicates = {l_id: count for l_id, count in counts.items() if count > 1}
        result[task_dir_name] = {
            "mp4_l_ids": len(counts),
            "duplicate_l_id_count": len(duplicates),
            "duplicate_l_id_examples": dict(list(duplicates.items())[:20]),
        }
    return result


def _fnirs_duplicate_summary(fnirs_dir: Path) -> dict[str, object]:
    result: dict[str, object] = {}
    for vendor_dir in sorted(path for path in fnirs_dir.iterdir() if path.is_dir()) if fnirs_dir.exists() else []:
        for task_dir in sorted(path for path in vendor_dir.iterdir() if path.is_dir()):
            dir_l_ids: Counter[str] = Counter()
            nirs_file_l_ids: Counter[str] = Counter()
            for child in task_dir.iterdir():
                if child.is_dir():
                    ids = _extract_l_ids(child.name)
                    if ids:
                        dir_l_ids[ids[0]] += 1
            for path in task_dir.rglob("*.nirs"):
                ids = _extract_l_ids(str(path.relative_to(task_dir)))
                if ids:
                    nirs_file_l_ids[ids[0]] += 1
            duplicate_dirs = {l_id: count for l_id, count in dir_l_ids.items() if count > 1}
            duplicate_nirs_files = {l_id: count for l_id, count in nirs_file_l_ids.items() if count > 1}
            result[f"{vendor_dir.name}/{task_dir.name}"] = {
                "subject_dirs_with_l_id": len(dir_l_ids),
                "duplicate_l_id_dir_count": len(duplicate_dirs),
                "duplicate_l_id_dir_examples": dict(list(duplicate_dirs.items())[:20]),
                "nirs_files_with_l_id": len(nirs_file_l_ids),
                "duplicate_nirs_file_l_id_count": len(duplicate_nirs_files),
                "duplicate_nirs_file_l_id_examples": dict(list(duplicate_nirs_files.items())[:20]),
            }
    return result


def _eye_duplicate_summary(eye_dir: Path) -> dict[str, object]:
    sources = {
        "Tobbi原始数据_xlsx": (eye_dir / "Tobbi原始数据", "*.xlsx"),
        "七鑫易维原始工程_csv": (eye_dir / "七鑫易维原始工程", "*.csv"),
        "Tobbi工程原文件_rec": (eye_dir / "Tobbi工程原文件", "*.rec"),
    }
    result: dict[str, object] = {}
    for source_name, (source_dir, pattern) in sources.items():
        stem_counts: Counter[str] = Counter()
        l_ids: set[str] = set()
        if source_dir.exists():
            for path in source_dir.rglob(pattern):
                stem_counts[path.stem] += 1
                for l_id in _extract_l_ids(str(path.relative_to(source_dir))):
                    l_ids.add(l_id)
        duplicate_stems = {stem: count for stem, count in stem_counts.items() if count > 1}
        result[source_name] = {
            "files": sum(stem_counts.values()),
            "stems": len(stem_counts),
            "duplicate_stem_count": len(duplicate_stems),
            "duplicate_stem_examples": dict(list(duplicate_stems.items())[:20]),
            "l_ids_in_paths": len(l_ids),
        }
    return result


def _extract_l_ids(text: str) -> list[str]:
    return [match.upper() for match in re.findall(r"(?<![A-Za-z0-9])L\d+(?![A-Za-z0-9])", text, flags=re.IGNORECASE)]
