"""Build EEG task-level readiness tables."""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping

from ..readiness import (
    base_subject_fields,
    extract_l_ids,
    path_hash,
    raw_data_dir,
    read_csv,
    resolve_project_path,
    split_rows,
    write_csv,
)
from .io import read_bdf_header
from .qc import minimum_qc_pass, required_channel_complete


TASK_ORDER = ["rest", "oddball", "1back"]


def role_file(subject_dir: Path, role: str) -> Path | None:
    bdfs = sorted(subject_dir.glob("*.bdf"))
    if role == "data":
        matches = [p for p in bdfs if p.name.lower().endswith("_data.bdf") or p.name.lower() == "data.bdf"]
    elif role == "evt":
        matches = [p for p in bdfs if p.name.lower().endswith("_evt.bdf") or p.name.lower() == "evt.bdf"]
    else:
        raise ValueError(role)
    return matches[0] if matches else None


def collect_subject_files(task_root: Path) -> dict[str, dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}
    if not task_root.exists():
        return found
    for subject_dir in sorted(path for path in task_root.iterdir() if path.is_dir()):
        ids = extract_l_ids(subject_dir.name)
        if not ids:
            continue
        l_id = ids[0]
        data_file = role_file(subject_dir, "data")
        evt_file = role_file(subject_dir, "evt")
        found[l_id] = {
            "subject_dir": subject_dir.name,
            "data_file": data_file,
            "evt_file": evt_file,
            "bdf_file_count": len(list(subject_dir.glob("*.bdf"))),
        }
    return found


def old_deep_qa(task: str) -> dict[str, dict[str, str]]:
    path = resolve_project_path(f"experiments/v1/eeg/artifacts/deep/windows/qa_{task}.csv")
    if not path.exists():
        return {}
    return {row["L_id"]: row for row in read_csv(path)}


def old_event_counts(task: str) -> dict[str, str]:
    path = resolve_project_path(f"experiments/v1/eeg/artifacts/deep/windows/metadata_{task}.csv")
    if not path.exists():
        return {}
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    for row in read_csv(path):
        code = row.get("event_code", "") or "[window]"
        counts[row["L_id"]][code] += 1
    return {l_id: "|".join(f"{key}:{value}" for key, value in sorted(counter.items())) for l_id, counter in counts.items()}


def old_rest_features() -> set[str]:
    path = resolve_project_path("experiments/v1/eeg/artifacts/features/eeg_rest_features.csv")
    if not path.exists():
        return set()
    return {row["L_id"] for row in read_csv(path)}


def build_task_availability(config: Mapping[str, Any], task: str) -> list[dict[str, Any]]:
    task_cfg = config["eeg"]["tasks"][task]
    task_root = raw_data_dir(config) / task_cfg["raw_dir"]
    files = collect_subject_files(task_root)
    qa = old_deep_qa(task)
    event_counts = old_event_counts(task)
    rest_features = old_rest_features() if task == "rest" else set()
    required_channels = list(config.get("eeg", {}).get("required_channels", []))
    min_duration = float(task_cfg.get("expected_min_duration_seconds", 30))

    rows: list[dict[str, Any]] = []
    for split_row in split_rows(config):
        l_id = split_row["L_id"]
        row = base_subject_fields(split_row)
        row["task"] = task
        info = files.get(l_id, {})
        data_file = info.get("data_file")
        evt_file = info.get("evt_file")
        data_header = read_bdf_header(data_file) if data_file else read_bdf_header("__missing__")
        evt_header = read_bdf_header(evt_file) if evt_file else read_bdf_header("__missing__")
        qc_pass, reason = minimum_qc_pass(data_header, evt_header, required_channels, min_duration)
        deep = qa.get(l_id, {})
        candidate = int(deep.get("windows") or 0) + int(deep.get("rejected_windows") or 0) if deep else 0
        effective = int(deep.get("windows") or 0) if deep else 0
        rejected = int(deep.get("rejected_windows") or 0) if deep else 0
        if deep and deep.get("status") != "ok":
            qc_pass = False
            reason = (reason + ";" if reason else "") + "old_deep_window_cache_failed"
        row.update(
            {
                "data_bdf_exists": int(bool(data_file and Path(data_file).exists())),
                "event_bdf_exists": int(bool(evt_file and Path(evt_file).exists())),
                "data_bdf_readable": int(data_header.status == "ok"),
                "event_bdf_readable": int(evt_header.status == "ok"),
                "data_file_hash": path_hash(data_file) if data_file else "",
                "event_file_hash": path_hash(evt_file) if evt_file else "",
                "n_channels": data_header.n_channels,
                "channel_names": "|".join(data_header.channel_names),
                "required_channels_complete": int(required_channel_complete(data_header.channel_names, required_channels)),
                "sfreq": data_header.sfreq,
                "duration_sec": data_header.duration_sec,
                "event_code_counts": event_counts.get(l_id, ""),
                "preprocessing_success": int(deep.get("status") == "ok") if deep else "",
                "candidate_windows": candidate,
                "effective_windows": effective,
                "rejected_windows": rejected,
                "bad_window_rate": (rejected / candidate) if candidate else "",
                "traditional_feature_exists": int(l_id in rest_features) if task == "rest" else 0,
                "deep_window_cache_exists": int(bool(deep)),
                "qc_pass": int(qc_pass),
                "failure_reason": reason or (deep.get("error", "") if deep else ""),
                "source_subject_dir": info.get("subject_dir", ""),
                "bdf_file_count": info.get("bdf_file_count", 0),
            }
        )
        if not info:
            row["failure_reason"] = "task_file_missing"
        rows.append(row)
    return rows


def write_task_availability(config: Mapping[str, Any]) -> dict[str, list[dict[str, Any]]]:
    outputs: dict[str, list[dict[str, Any]]] = {}
    for task in TASK_ORDER:
        rows = build_task_availability(config, task)
        write_csv(config["eeg"]["tasks"][task]["output_csv"], rows)
        outputs[task] = rows
    return outputs
