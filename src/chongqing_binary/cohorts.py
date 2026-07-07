"""Goal 2.5 cohort reconciliation for EEG/fNIRS/Face."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from .readiness import count_true, ensure_output_path, read_csv, resolve_project_path, split_rows, text_table, write_csv


CORE3 = ("eeg", "fnirs", "face")


def load_if_exists(path: str | Path) -> list[dict[str, str]]:
    resolved = resolve_project_path(path)
    return read_csv(resolved) if resolved.exists() else []


def summarize_by_l_id(rows: list[dict[str, str]], key_prefix: str, file_col: str, qc_col: str, task_col: str) -> dict[str, dict[str, Any]]:
    summary: dict[str, dict[str, Any]] = {}
    for row in rows:
        l_id = row["L_id"]
        target = summary.setdefault(
            l_id,
            {
                f"{key_prefix}_file_available": 0,
                f"{key_prefix}_qc_pass": 0,
                f"{key_prefix}_tasks_file": [],
                f"{key_prefix}_tasks_qc": [],
            },
        )
        task = row.get(task_col, "")
        if row.get(file_col) == "1":
            target[f"{key_prefix}_file_available"] = 1
            if task:
                target[f"{key_prefix}_tasks_file"].append(task)
        if row.get(qc_col) == "1":
            target[f"{key_prefix}_qc_pass"] = 1
            if task:
                target[f"{key_prefix}_tasks_qc"].append(task)
    for target in summary.values():
        for field in [f"{key_prefix}_tasks_file", f"{key_prefix}_tasks_qc"]:
            target[field] = "|".join(sorted(set(target[field])))
    return summary


def availability_maps() -> dict[str, dict[str, dict[str, Any]]]:
    eeg_rows = []
    for task in ("rest", "oddball", "1back"):
        eeg_rows.extend(load_if_exists(f"artifacts/eeg/task_availability_{task}.csv"))
    fnirs_rows = []
    for device in ("yiruid", "bikom"):
        for task in ("rest", "oddball", "vft", "1back", "doors"):
            for row in load_if_exists(f"artifacts/fnirs/task_availability_{device}_{task}.csv"):
                row = dict(row)
                row["device_task"] = f"{row.get('device','')}:{row.get('task','')}"
                fnirs_rows.append(row)
    face_rows = []
    for name in ("self_intro", "task"):
        face_rows.extend(load_if_exists(f"artifacts/face/video_availability_{name}.csv"))
    return {
        "eeg": summarize_by_l_id(eeg_rows, "eeg", "data_bdf_readable", "qc_pass", "task"),
        "fnirs": summarize_by_l_id(fnirs_rows, "fnirs", "file_readable", "qc_pass", "device_task"),
        "face": summarize_by_l_id(face_rows, "face", "file_readable", "qc_pass", "video_task"),
    }


def build_cohort_rows(config: Mapping[str, Any] | None = None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    maps = availability_maps()
    rows: list[dict[str, Any]] = []
    for row in split_rows(config):
        out = dict(row)
        for prefix in CORE3:
            data = maps[prefix].get(row["L_id"], {})
            out[f"{prefix}_file_available"] = int(data.get(f"{prefix}_file_available", 0))
            out[f"{prefix}_qc_pass"] = int(data.get(f"{prefix}_qc_pass", 0))
            out[f"{prefix}_tasks_file"] = data.get(f"{prefix}_tasks_file", "")
            out[f"{prefix}_tasks_qc"] = data.get(f"{prefix}_tasks_qc", "")
        out["core3_any_flag"] = int(any(out.get(flag) == "1" for flag in ["has_EEG", "has_fNIRS", "has_face"]))
        out["core3_any_file"] = int(any(int(out[f"{prefix}_file_available"]) for prefix in CORE3))
        out["core3_complete_flag"] = int(all(out.get(flag) == "1" for flag in ["has_EEG", "has_fNIRS", "has_face"]))
        out["core3_complete_file"] = int(all(int(out[f"{prefix}_file_available"]) for prefix in CORE3))
        out["core3_complete_qc"] = int(all(int(out[f"{prefix}_qc_pass"]) for prefix in CORE3))
        out["core3_incomplete"] = int(out["core3_any_flag"] and not out["core3_complete_qc"])
        out["four_modality_complete_direct_flag"] = int(out["core3_complete_flag"] and out.get("has_eye_direct") == "1")
        out["four_modality_complete_name_mapped_flag"] = int(
            out["core3_complete_flag"] and out.get("has_eye_name_mapped") == "1"
        )
        rows.append(out)
    stats = cohort_counts(rows)
    return rows, stats


def cohort_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "primary_label_valid": sum(1 for row in rows if row.get("primary_label_nonhealthy") in {"0", "1"}),
        "at_least_one_core3_flag": count_true(rows, "core3_any_flag"),
        "eeg_flag": sum(1 for row in rows if row.get("has_EEG") == "1"),
        "eeg_file": count_true(rows, "eeg_file_available"),
        "eeg_qc": count_true(rows, "eeg_qc_pass"),
        "fnirs_flag": sum(1 for row in rows if row.get("has_fNIRS") == "1"),
        "fnirs_file": count_true(rows, "fnirs_file_available"),
        "fnirs_qc": count_true(rows, "fnirs_qc_pass"),
        "face_flag": sum(1 for row in rows if row.get("has_face") == "1"),
        "face_file": count_true(rows, "face_file_available"),
        "face_qc": count_true(rows, "face_qc_pass"),
        "core3_flag_complete": count_true(rows, "core3_complete_flag"),
        "core3_file_complete": count_true(rows, "core3_complete_file"),
        "core3_qc_complete": count_true(rows, "core3_complete_qc"),
        "four_modality_complete_direct_flag": count_true(rows, "four_modality_complete_direct_flag"),
        "four_modality_complete_name_mapped_flag": count_true(rows, "four_modality_complete_name_mapped_flag"),
    }


def write_cohort_outputs(config: Mapping[str, Any] | None = None) -> dict[str, Any]:
    rows, stats = build_cohort_rows(config)
    write_csv("artifacts/cohorts_v2/core3_any.csv", [row for row in rows if row["core3_any_flag"]])
    write_csv("artifacts/cohorts_v2/core3_complete_flag.csv", [row for row in rows if row["core3_complete_flag"]])
    write_csv("artifacts/cohorts_v2/core3_complete_file.csv", [row for row in rows if row["core3_complete_file"]])
    write_csv("artifacts/cohorts_v2/core3_complete_qc.csv", [row for row in rows if row["core3_complete_qc"]])
    write_csv("artifacts/cohorts_v2/core3_incomplete.csv", [row for row in rows if row["core3_incomplete"]])
    write_csv("artifacts/cohorts_v2/eye_extension_direct.csv", [row for row in rows if row.get("has_eye_direct") == "1"])
    write_csv(
        "artifacts/cohorts_v2/eye_extension_name_mapped.csv",
        [row for row in rows if row.get("has_eye_name_mapped") == "1"],
    )
    report = cohort_report(stats)
    ensure_output_path("reports/cohort_reconciliation.md").write_text(report, encoding="utf-8")
    return {"rows": rows, "stats": stats}


def cohort_report(stats: Mapping[str, int]) -> str:
    lines = [
        "# Goal 2.5 Cohort Reconciliation",
        "",
        "This report recomputes EEG/fNIRS/Face cohorts from `subject_splits_v1.csv` plus task-level file/QC availability tables. Eye tracking is extension-only and is not part of any `core3` definition.",
        "",
        "## Count Summary",
        "",
        text_table(stats),
        "",
        "## 2189 vs 2376",
        "",
        "The existing Goal 1 `matched_eeg_fnirs_face.csv` count of 2376 is a manifest/split flag count for labeled subjects with EEG, fNIRS, and Face flags. A previously documented 2189 count is not reproduced by the current canonical manifest alone and is treated as an older or stricter denominator likely affected by manifest version, label filtering, actual file matching, task requirements, or QC rules.",
        "",
        "For model development after Goal 2.5, use the file-verified and QC-verified `artifacts/cohorts_v2/` cohorts rather than either historical number by itself.",
        "",
        "## Definitions",
        "",
        "- `core3_complete_flag`: manifest/split flags for EEG, fNIRS, and Face are all 1.",
        "- `core3_complete_file`: at least one readable task/video file is available for each of EEG, fNIRS, and Face.",
        "- `core3_complete_qc`: the minimum metadata-level QC pass is true for each of EEG, fNIRS, and Face.",
        "- `core3_incomplete`: at least one core3 flag is present, but QC-complete core3 is not satisfied.",
        "- Eye tracking is written only to `eye_extension_*` tables.",
    ]
    return "\n".join(lines) + "\n"
