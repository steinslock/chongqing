"""Build fNIRS device/task readiness tables."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from ..readiness import (
    base_subject_fields,
    extract_l_ids,
    path_hash,
    raw_data_dir,
    split_rows,
    write_csv,
)
from .io import infer_yiruid_semantics, probe_csv, probe_yiruid_nirs
from .qc import minimum_qc_pass, placeholder_qc_metrics


def collect_yiruid(task_root: Path) -> dict[str, list[Path]]:
    found: dict[str, list[Path]] = {}
    if not task_root.exists():
        return found
    for path in sorted(task_root.rglob("*.nirs")):
        ids = extract_l_ids(str(path))
        if ids:
            found.setdefault(ids[0], []).append(path)
    return found


def collect_bikom(task_root: Path) -> dict[str, dict[str, list[Path]]]:
    found: dict[str, dict[str, list[Path]]] = {}
    if not task_root.exists():
        return found
    for path in sorted(task_root.rglob("*.csv")):
        ids = extract_l_ids(str(path))
        if not ids:
            continue
        l_id = ids[0]
        low = path.name.lower()
        if "hba_oxy" in low:
            role = "HbO"
        elif "hba_deoxy" in low:
            role = "HbR"
        elif "hba_total" in low:
            role = "HbT"
        elif "_mes_" in low or low.endswith("_mes.csv"):
            role = "Mes"
        else:
            role = "other"
        found.setdefault(l_id, {}).setdefault(role, []).append(path)
    return found


def build_yiruid_rows(config: Mapping[str, Any], task: str) -> list[dict[str, Any]]:
    task_root = raw_data_dir(config) / config["fnirs"]["devices"]["yiruid"]["dirs"][task]
    files = collect_yiruid(task_root)
    rows: list[dict[str, Any]] = []
    for split_row in split_rows(config):
        l_id = split_row["L_id"]
        row = base_subject_fields(split_row)
        row.update({"device": "yiruid", "task": task})
        paths = files.get(l_id, [])
        path = paths[0] if paths else None
        probe = probe_yiruid_nirs(path) if path else None
        semantics = infer_yiruid_semantics(probe.variables if probe else {})
        readable = bool(probe and probe.readable)
        channel_count = semantics.get("channel_count", "")
        qc_pass, reason = minimum_qc_pass(bool(path), readable, channel_count)
        row.update(
            {
                "raw_file_exists": int(bool(path)),
                "file_format": "nirs",
                "file_readable": int(readable),
                "file_count": len(paths),
                "source_file_hash": path_hash(path) if path else "",
                "wavelengths": semantics["wavelengths"],
                "source_count": semantics["source_count"],
                "detector_count": semantics["detector_count"],
                "channel_count": channel_count,
                "sampling_rate": "",
                "duration_sec": "",
                "raw_intensity_exists": semantics["raw_intensity_exists"],
                "optical_density_computable": semantics["optical_density_computable"],
                "hbo_hbr_exists_or_computable": semantics["hbo_hbr_exists_or_computable"],
                "event_marker_exists": semantics["event_marker_exists"],
                "event_code_counts": "",
                "recognized_task_segments": "",
                "preprocessing_success": "",
                "qc_pass": int(qc_pass),
                "failure_reason": reason or (probe.error if probe and probe.error else ""),
                "format_variables": "|".join(f"{k}:{v}" for k, v in sorted((probe.variables if probe else {}).items())),
            }
        )
        row.update(placeholder_qc_metrics())
        rows.append(row)
    return rows


def build_bikom_rows(config: Mapping[str, Any], task: str) -> list[dict[str, Any]]:
    task_root = raw_data_dir(config) / config["fnirs"]["devices"]["bikom"]["dirs"][task]
    files = collect_bikom(task_root)
    rows: list[dict[str, Any]] = []
    for split_row in split_rows(config):
        l_id = split_row["L_id"]
        row = base_subject_fields(split_row)
        row.update({"device": "bikom", "task": task})
        roles = files.get(l_id, {})
        hbo = roles.get("HbO", [])
        hbr = roles.get("HbR", [])
        mes = roles.get("Mes", [])
        probe = probe_csv(hbo[0]) if hbo else None
        file_exists = bool(hbo or hbr or mes)
        readable = bool(probe and probe.readable)
        channel_count = probe.column_count if probe and probe.column_count is not None else ""
        qc_pass, reason = minimum_qc_pass(file_exists, readable, channel_count)
        row.update(
            {
                "raw_file_exists": int(file_exists),
                "file_format": "csv_hba",
                "file_readable": int(readable),
                "file_count": sum(len(v) for v in roles.values()),
                "source_file_hash": path_hash(hbo[0]) if hbo else "",
                "wavelengths": "not_in_csv_probe",
                "source_count": "",
                "detector_count": "",
                "channel_count": channel_count,
                "sampling_rate": "",
                "duration_sec": "",
                "raw_intensity_exists": 0,
                "optical_density_computable": 0,
                "hbo_hbr_exists_or_computable": int(bool(hbo and hbr)),
                "event_marker_exists": int(bool(mes)),
                "event_code_counts": "",
                "recognized_task_segments": "",
                "preprocessing_success": "",
                "qc_pass": int(qc_pass),
                "failure_reason": reason or (probe.error if probe and probe.error else ""),
                "format_variables": f"HbO:{len(hbo)}|HbR:{len(hbr)}|HbT:{len(roles.get('HbT', []))}|Mes:{len(mes)}",
            }
        )
        row.update(placeholder_qc_metrics())
        rows.append(row)
    return rows


def write_task_availability(config: Mapping[str, Any]) -> dict[str, list[dict[str, Any]]]:
    outputs: dict[str, list[dict[str, Any]]] = {}
    for device in ("yiruid", "bikom"):
        for task in ("rest", "oddball", "vft", "1back", "doors"):
            rows = build_yiruid_rows(config, task) if device == "yiruid" else build_bikom_rows(config, task)
            path = f"artifacts/fnirs/task_availability_{device}_{task}.csv"
            write_csv(path, rows)
            outputs[f"{device}_{task}"] = rows
    return outputs
