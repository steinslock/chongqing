#!/usr/bin/env python3
"""Generate Goal 2.7 EEG, fNIRS, and Face audit artifacts."""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.io import loadmat

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from chongqing_binary.goal2_7.config import ensure_output, load_goal_config, project_path
from chongqing_binary.goal2_7.fnirs import _collect_bikom, _collect_yiruid, _data_header_skiprows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/goal2_7/models.yaml")
    args = parser.parse_args()
    config = _combined_config(args.config)
    outputs = {
        "eeg": audit_eeg(config),
        "fnirs": audit_fnirs(config),
        "face": audit_face(config),
    }
    print(json.dumps(outputs, ensure_ascii=False, indent=2))


def _combined_config(path: str | Path) -> dict[str, Any]:
    base = load_goal_config(path)
    for extra_path in ["configs/goal2_7/bootstrap.yaml", "configs/goal2_7/eeg.yaml", "configs/goal2_7/fnirs.yaml", "configs/goal2_7/face.yaml"]:
        extra = load_goal_config(extra_path)
        for key in ["bootstrap", "eeg", "fnirs", "face"]:
            if key in extra:
                base[key] = extra[key]
    return base


def audit_eeg(config: dict[str, Any]) -> dict[str, str]:
    inventory_rows: list[dict[str, Any]] = []
    example_rows: list[dict[str, Any]] = []
    for task, spec in config.get("eeg", {}).get("tasks", {}).items():
        meta = pd.read_csv(project_path(spec["metadata_csv"]), dtype={"L_id": str})
        event = meta["event_code"] if "event_code" in meta.columns else pd.Series([""], index=meta.index)
        counts = event.value_counts(dropna=False)
        for code, count in counts.items():
            inventory_rows.append(
                {
                    "task": task,
                    "event_code": "" if pd.isna(code) else str(code),
                    "window_count": int(count),
                    "subject_count": int(meta.loc[event.fillna("").astype(str) == ("" if pd.isna(code) else str(code)), "L_id"].nunique()),
                    "semantic_status": _eeg_semantic_status(task),
                    "epoch_tmin_sec": spec.get("epoch_tmin", ""),
                    "epoch_tmax_sec": spec.get("epoch_tmax", ""),
                    "baseline_interval": "not_confirmed",
                }
            )
        for l_id, group in meta.groupby("L_id", sort=True):
            codes = ["" if pd.isna(x) else str(x) for x in group.get("event_code", pd.Series([], dtype=object)).head(30).tolist()]
            starts = pd.to_numeric(group.get("start_sec"), errors="coerce").head(5).round(3).tolist()
            stops = pd.to_numeric(group.get("stop_sec"), errors="coerce").head(5).round(3).tolist()
            example_rows.append({"task": task, "L_id": l_id, "event_sequence_first_30": " ".join(codes), "start_sec_first_5": starts, "stop_sec_first_5": stops})
            if len([r for r in example_rows if r["task"] == task]) >= 10:
                break
    inventory = pd.DataFrame(inventory_rows)
    examples = pd.DataFrame(example_rows)
    inv_path = ensure_output("artifacts/goal2_7/eeg/event_code_inventory.csv", config)
    ex_path = ensure_output("artifacts/goal2_7/eeg/event_sequence_examples.csv", config)
    inventory.to_csv(inv_path, index=False)
    examples.to_csv(ex_path, index=False)
    report_path = ensure_output("reports/goal2_7_eeg_event_audit.md", config)
    report_path.write_text(_eeg_report(inventory), encoding="utf-8")
    return {"inventory": str(inv_path), "examples": str(ex_path), "report": str(report_path)}


def _eeg_semantic_status(task: str) -> str:
    if task == "rest":
        return "event_free_rest"
    if task == "oddball":
        return "blocked_target_nontarget_not_confirmed_cache_code22_only"
    if task == "1back":
        return "blocked_condition_semantics_not_confirmed"
    return "unknown"


def _eeg_report(inventory: pd.DataFrame) -> str:
    lines = [
        "# Goal 2.7 EEG Event Audit",
        "",
        "The audit uses v1 cached-window metadata and the v1 cache script. Code numbers are not interpreted as task semantics unless a project-local mapping is available.",
        "",
        "## Event Inventory",
        "",
        _markdown_table(inventory),
        "",
        "## Interpretation",
        "",
        "- Rest is event-free and usable as whole-recording/window-generic signal.",
        "- Oddball cache contains only code `22` windows with approximately -0.2 to 0.8 s epochs; target/non-target semantics are not proven, so formal Oddball ERP is blocked and the cache is used only as `oddball_target_only_proxy`.",
        "- 1BACK cache contains codes `18` and `19` with approximately -0.2 to 1.8 s epochs; code semantics are not proven, so condition-difference features are blocked and only generic signal features are used.",
        "- Baseline intervals were not confirmed from project-local documentation.",
    ]
    return "\n".join(lines) + "\n"


def audit_fnirs(config: dict[str, Any]) -> dict[str, str]:
    raw_root = project_path(config["paths"]["raw_data_dir"])
    inventory_rows: list[dict[str, Any]] = []
    timing_rows: list[dict[str, Any]] = []
    example_rows: list[dict[str, Any]] = []
    for device, device_cfg in config.get("fnirs", {}).get("devices", {}).items():
        for task in ["vft", "1back", "rest"]:
            task_dir = raw_root / device_cfg["dirs"][task]
            if device == "yiruid":
                rows = _audit_yiruid_task(task_dir, device, task)
            else:
                rows = _audit_bikom_task(task_dir, device, task)
            if not rows:
                continue
            marker_counts = Counter(row["marker_count"] for row in rows)
            inventory_rows.extend(
                {
                    "device": device,
                    "task": task,
                    "marker_count": marker_count,
                    "subjects": subjects,
                    "segment_status": _fnirs_segment_status(task, marker_count),
                }
                for marker_count, subjects in sorted(marker_counts.items())
            )
            durations = [row["duration_sec"] for row in rows if math.isfinite(row["duration_sec"])]
            raw_rows = [row["raw_rows"] for row in rows if row["raw_rows"] >= 0]
            timing_rows.append(
                {
                    "device": device,
                    "task": task,
                    "subjects": len(rows),
                    "raw_rows_min": min(raw_rows) if raw_rows else math.nan,
                    "raw_rows_median": float(np.median(raw_rows)) if raw_rows else math.nan,
                    "raw_rows_max": max(raw_rows) if raw_rows else math.nan,
                    "duration_min_sec": min(durations) if durations else math.nan,
                    "duration_median_sec": float(np.median(durations)) if durations else math.nan,
                    "duration_max_sec": max(durations) if durations else math.nan,
                    "rows_gt_2000": sum(row["raw_rows"] > 2000 for row in rows),
                    "markers_after_2000": sum(row.get("markers_after_2000", 0) for row in rows),
                    "formal_task_response_status": "blocked_without_confirmed_timing" if task != "rest" else "whole_recording",
                }
            )
            example_rows.extend(rows[:10])
    inventory = pd.DataFrame(inventory_rows)
    timing = pd.DataFrame(timing_rows)
    examples = pd.DataFrame(example_rows)
    inv_path = ensure_output("artifacts/goal2_7/fnirs/marker_inventory.csv", config)
    timing_path = ensure_output("artifacts/goal2_7/fnirs/task_timing_summary.csv", config)
    ex_path = ensure_output("artifacts/goal2_7/fnirs/marker_sequence_examples.csv", config)
    inventory.to_csv(inv_path, index=False)
    timing.to_csv(timing_path, index=False)
    examples.to_csv(ex_path, index=False)
    report_path = ensure_output("reports/goal2_7_fnirs_event_audit.md", config)
    report_path.write_text(_fnirs_report(inventory, timing), encoding="utf-8")
    return {"inventory": str(inv_path), "timing": str(timing_path), "examples": str(ex_path), "report": str(report_path)}


def _audit_yiruid_task(task_dir: Path, device: str, task: str) -> list[dict[str, Any]]:
    rows = []
    for l_id, path in _collect_yiruid(task_dir).items():
        try:
            mat = loadmat(path, squeeze_me=True, struct_as_record=False, variable_names=["d", "t", "s", "Mark_infor"])
            data = np.asarray(mat.get("d", []))
            t = np.asarray(mat.get("t", [])).reshape(-1)
            s = np.asarray(mat.get("s", [])).reshape(-1)
            marker_idx = np.flatnonzero(s != 0).astype(int).tolist() if s.size else []
            duration = float(np.nanmax(t) - np.nanmin(t)) if t.size else math.nan
            rows.append(
                {
                    "device": device,
                    "task": task,
                    "L_id": l_id,
                    "raw_rows": int(data.shape[0]) if data.ndim else -1,
                    "duration_sec": duration,
                    "marker_count": len(marker_idx),
                    "marker_values": " ".join(sorted(set(str(x) for x in s.tolist() if str(x) not in {"0", "0.0", "nan"}))) if s.size else "",
                    "marker_indices_first_20": " ".join(map(str, marker_idx[:20])),
                    "markers_after_2000": sum(idx >= 2000 for idx in marker_idx),
                    "source_file": str(path),
                }
            )
        except Exception as exc:  # noqa: BLE001
            rows.append({"device": device, "task": task, "L_id": l_id, "raw_rows": -1, "duration_sec": math.nan, "marker_count": -1, "marker_values": "", "marker_indices_first_20": "", "markers_after_2000": 0, "source_file": str(path), "error": type(exc).__name__})
    return rows


def _audit_bikom_task(task_dir: Path, device: str, task: str) -> list[dict[str, Any]]:
    rows = []
    for l_id, roles in _collect_bikom(task_dir).items():
        path = (roles.get("HbO") or [None])[0]
        if path is None:
            continue
        try:
            skip = _data_header_skiprows(path)
            df = pd.read_csv(path, skiprows=skip, encoding="utf-8-sig", usecols=lambda col: str(col) in {"Time", "Mark"})
        except UnicodeDecodeError:
            df = pd.read_csv(path, skiprows=skip, encoding="gb18030", usecols=lambda col: str(col) in {"Time", "Mark"})
        if "Time" in df.columns:
            t = pd.to_numeric(df["Time"], errors="coerce").dropna()
            duration = float(t.iloc[-1] - t.iloc[0]) if len(t) else math.nan
        else:
            duration = math.nan
        if "Mark" in df.columns:
            mark = df["Mark"].astype(str).str.strip()
            marker = ~mark.isin(["", "0", "nan", "None"])
            indices = np.flatnonzero(marker.to_numpy()).astype(int).tolist()
            values = " ".join(sorted(set(mark[marker].astype(str).tolist())))
        else:
            indices = []
            values = ""
        rows.append(
            {
                "device": device,
                "task": task,
                "L_id": l_id,
                "raw_rows": int(len(df)),
                "duration_sec": duration,
                "marker_count": len(indices),
                "marker_values": values,
                "marker_indices_first_20": " ".join(map(str, indices[:20])),
                "markers_after_2000": sum(idx >= 2000 for idx in indices),
                "source_file": str(path),
            }
        )
    return rows


def _fnirs_segment_status(task: str, marker_count: int) -> str:
    if task == "rest":
        return "event_free_whole_recording"
    if marker_count > 0:
        return "markers_present_but_timing_semantics_unconfirmed"
    return "segment_blocked_no_markers"


def _fnirs_report(inventory: pd.DataFrame, timing: pd.DataFrame) -> str:
    lines = [
        "# Goal 2.7 fNIRS Event and Timing Audit",
        "",
        "The audit inspects Yiruid `.nirs` marker arrays and Bikom CSV `Mark` columns. Formal task-response features require marker-confirmed or protocol-confirmed timing; the old 20/60/20 fallback is not used.",
        "",
        "## Marker Inventory",
        "",
        _markdown_table(inventory) if not inventory.empty else "No marker inventory rows.",
        "",
        "## Timing Summary",
        "",
        _markdown_table(timing) if not timing.empty else "No timing rows.",
        "",
        "## Interpretation",
        "",
        "- Rest is modeled as whole-recording.",
        "- VFT and 1BACK task-response features are blocked unless a later protocol document confirms segment timing.",
        "- Bikom is audited with full-file rows; the Goal 2.6 fixed 2000-row cap is not used.",
        "- Yiruid features are named raw/log-intensity or OD-like; no HbO/HbR claim is made.",
    ]
    return "\n".join(lines) + "\n"


def audit_face(config: dict[str, Any]) -> dict[str, str]:
    report_path = ensure_output("reports/goal2_7_face_detection_audit.md", config)
    rows = []
    for task, spec in config.get("face", {}).get("tasks", {}).items():
        path = project_path(spec["qc_features"])
        if not path.exists():
            rows.append({"task": task, "status": "pending_strict_face_extraction"})
            continue
        df = pd.read_csv(path, dtype={"L_id": str})
        rows.append(
            {
                "task": task,
                "status": "available",
                "videos": len(df),
                "blocked": int(pd.to_numeric(df.get("qc_face_feature_blocked", 1), errors="coerce").fillna(1).sum()),
                "mean_detection_rate": float(pd.to_numeric(df.get("qc_face_detection_rate"), errors="coerce").mean()),
                "fallback_count": int(pd.to_numeric(df.get("qc_detector_fallback_used", 0), errors="coerce").fillna(0).sum()),
                "multi_face_rate": float(pd.to_numeric(df.get("qc_multi_face_rate"), errors="coerce").mean()),
            }
        )
    summary = pd.DataFrame(rows)
    contact_dir = project_path(config["face"]["outputs"]["contact_sheet_dir"])
    contact_count = len(list(contact_dir.glob("*.jpg"))) if contact_dir.exists() else 0
    lines = [
        "# Goal 2.7 Face Detection Audit",
        "",
        f"Contact sheet directory: `{contact_dir}`",
        f"Contact sheets found: `{contact_count}`",
        "",
        _markdown_table(summary) if not summary.empty else "Strict Face extraction has not run.",
        "",
        "Background masks remove the expanded face bounding box but may still preserve body, room, camera, and acquisition-context information; this remains a shortcut limitation.",
    ]
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"report": str(report_path)}


def _markdown_table(frame: pd.DataFrame, limit: int = 80) -> str:
    if frame.empty:
        return ""
    data = frame.head(limit).fillna("").astype(str)
    cols = list(data.columns)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in data.iterrows():
        lines.append("| " + " | ".join(str(row[col]).replace("|", "/") for col in cols) + " |")
    if len(frame) > limit:
        lines.append(f"\nShowing first {limit} of {len(frame)} rows.")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
