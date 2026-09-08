"""Subject-level EEG features from the Goal 2.8 ERP archive.

The headline quantity is the condition difference wave, which Goal 2.7 could not
compute because its cache held only one Oddball condition.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ..paradigm import load_paradigm_spec
from ..paradigm.spec import EegTaskSpec, ParadigmSpec
from .config import cv_subjects, ensure_output, load_goal_config, project_path


def _window_features(prefix: str, wave: np.ndarray, times: np.ndarray,
                     windows: dict[str, list[float]]) -> dict[str, float]:
    """Mean, peak, trough and peak latency inside each named time window."""
    out: dict[str, float] = {}
    for name, (lo, hi) in windows.items():
        mask = (times >= float(lo)) & (times <= float(hi))
        if not np.any(mask):
            continue
        segment = wave[mask]
        segment_times = times[mask]
        out[f"{prefix}_{name}_mean"] = float(np.nanmean(segment))
        out[f"{prefix}_{name}_peak"] = float(np.nanmax(segment))
        out[f"{prefix}_{name}_trough"] = float(np.nanmin(segment))
        out[f"{prefix}_{name}_peak_latency"] = float(segment_times[int(np.nanargmax(segment))])
        out[f"{prefix}_{name}_area"] = float(np.trapezoid(segment, segment_times))
    return out


def extract_eeg_features(task: str = "oddball",
                         config_path: str | Path = "configs/goal2_8/eeg.yaml",
                         spec: ParadigmSpec | None = None) -> dict[str, Any]:
    config = load_goal_config(config_path)
    spec = spec or load_paradigm_spec(config["paths"]["paradigm_spec"])
    task_spec: EegTaskSpec = spec.eeg(task)
    eeg_cfg = config["eeg"]
    out_dir = Path(ensure_output(f"{eeg_cfg['outputs_dir']}/.keep", config)).parent

    archive = np.load(out_dir / f"{task}_erp.npz", allow_pickle=False)
    index = pd.read_csv(out_dir / f"{task}_erp_index.csv", dtype={"L_id": str})

    l_ids = [str(x) for x in archive["l_ids"]]
    channels = [str(c) for c in archive["channels"]]
    times = np.asarray(archive["times"], dtype=float)
    codes = task_spec.codes_for_contrast()
    erps = {code: np.asarray(archive[f"erp_{code}"], dtype=float) for code in codes}

    erp_channels = [c for c in task_spec.raw.get("erp_channels", []) if c in channels]
    windows = {k: list(v) for k, v in (task_spec.raw.get("erp_windows") or {}).items()}
    contrast = task_spec.primary_contrast
    ch_index = {c: channels.index(c) for c in channels}

    frontal = [c for c in ("Fz", "F3", "F4") if c in channels]
    parietal = [c for c in ("Pz", "P3", "P4") if c in channels]

    rows: list[dict[str, Any]] = []
    for position, l_id in enumerate(l_ids):
        row: dict[str, Any] = {
            "L_id": l_id,
            "modality": "eeg",
            "task": task,
            "feature_version": "goal2_8_eeg_condition_erp_v1",
            "preprocessing_version": eeg_cfg["preprocessing_version"],
            "event_validity_status": "confirmed_from_paradigm_spec",
        }
        per_condition: dict[str, np.ndarray] = {}
        for code in codes:
            condition = task_spec.condition_of(code) or f"code_{code}"
            data = erps[code][position]
            per_condition[code] = data
            for channel in erp_channels:
                row.update(_window_features(
                    f"signal_erp_{condition}_{channel}", data[ch_index[channel]], times, windows))
            mean_wave = np.nanmean(data, axis=0)
            row.update(_window_features(f"signal_erp_{condition}_global", mean_wave, times, windows))
            row[f"signal_erp_{condition}_global_ptp"] = float(np.nanmax(mean_wave) - np.nanmin(mean_wave))

        # The difference wave: the quantity Goal 2.7 could not compute.
        if contrast and contrast["minuend"] in per_condition and contrast["subtrahend"] in per_condition:
            name = contrast["name"]
            diff = per_condition[contrast["minuend"]] - per_condition[contrast["subtrahend"]]
            for channel in erp_channels:
                row.update(_window_features(f"signal_{name}_{channel}", diff[ch_index[channel]], times, windows))
            mean_diff = np.nanmean(diff, axis=0)
            row.update(_window_features(f"signal_{name}_global", mean_diff, times, windows))
            row[f"signal_{name}_global_ptp"] = float(np.nanmax(mean_diff) - np.nanmin(mean_diff))
            if frontal and parietal:
                key = "p300" if "p300" in windows else next(iter(windows), "")
                if key:
                    lo, hi = windows[key]
                    mask = (times >= lo) & (times <= hi)
                    front = float(np.nanmean(diff[[ch_index[c] for c in frontal]][:, mask]))
                    back = float(np.nanmean(diff[[ch_index[c] for c in parietal]][:, mask]))
                    row[f"signal_{name}_frontal_{key}"] = front
                    row[f"signal_{name}_parietal_{key}"] = back
                    row[f"signal_{name}_parietal_minus_frontal_{key}"] = back - front
        rows.append(row)

    signal = pd.DataFrame(rows)

    qc_cols = ["L_id", "status", "reason", "duration_sec", "candidate_trials",
               "rejected_trials", "rejected_rate"] + [f"n_trials_code_{c}" for c in codes]
    qc = index[[c for c in qc_cols if c in index.columns]].copy()
    qc = qc.rename(columns={
        "status": "qc_feature_status", "reason": "qc_failure_reason",
        "duration_sec": "qc_recording_duration_sec", "candidate_trials": "qc_candidate_trials",
        "rejected_trials": "qc_rejected_trials", "rejected_rate": "qc_rejected_rate",
        **{f"n_trials_code_{c}": f"qc_n_trials_{task_spec.condition_of(c) or c}" for c in codes},
    })
    qc["modality"] = "eeg"
    qc["task"] = task
    qc["preprocessing_version"] = eeg_cfg["preprocessing_version"]

    split = cv_subjects(config)
    keep = [c for c in ["L_id", "A_id", "primary_label_nonhealthy", "split_group", "split_role",
                        "is_locked_test", "cv_fold", "sex", "age", "grade", "grade_group",
                        "fnirs_device"] if c in split.columns]
    signal_out = split[keep].merge(signal, on="L_id", how="inner").sort_values("L_id").reset_index(drop=True)
    qc_out = split[keep].merge(qc, on="L_id", how="inner").sort_values("L_id").reset_index(drop=True)
    for frame, label in ((signal_out, "signal"), (qc_out, "qc")):
        if pd.to_numeric(frame.get("is_locked_test", 0), errors="coerce").fillna(0).astype(int).any():
            raise ValueError(f"Goal 2.8 EEG {label} features include pilot-holdout subjects.")

    signal_path = out_dir / f"{task}_signal_features.csv"
    qc_path = out_dir / f"{task}_qc_features.csv"
    signal_out.to_csv(signal_path, index=False)
    qc_out.to_csv(qc_path, index=False)

    manifest = {
        "task": task,
        "feature_version": "goal2_8_eeg_condition_erp_v1",
        "conditions": {c: task_spec.condition_of(c) for c in codes},
        "primary_contrast": contrast,
        "erp_channels": erp_channels,
        "erp_windows": windows,
        "subjects_signal": int(len(signal_out)),
        "subjects_qc": int(len(qc_out)),
        "signal_feature_columns": int(sum(1 for c in signal_out.columns if c.startswith("signal_"))),
        "signal_features": str(signal_path),
        "qc_features": str(qc_path),
    }
    (out_dir / f"{task}_feature_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest
