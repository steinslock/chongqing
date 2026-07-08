"""EEG Goal 2.6 features derived from cached preprocessed windows."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .config import ensure_output, load_goal_config, project_path
from .io import cv_subjects
from .stats import (
    basic_time_features,
    channel_time_features,
    connectivity_features,
    hjorth_features,
    spectral_features,
)


def extract_eeg_features(config_path: str | Path = "configs/goal2_6/eeg.yaml") -> dict[str, Any]:
    config = load_goal_config(config_path)
    split = cv_subjects(config)
    label_col = config.get("run", {}).get("label_column", "primary_label_nonhealthy")
    cv_lids = set(split["L_id"].astype(str))
    channels = list(config["eeg"]["channels"])
    manifest: dict[str, Any] = {
        "config": str(project_path(config_path)),
        "preprocessing_version": config["eeg"]["preprocessing_version"],
        "feature_version": config["eeg"]["feature_version"],
        "tasks": {},
    }

    for task, spec in config["eeg"]["tasks"].items():
        meta = pd.read_csv(project_path(spec["metadata_csv"]), dtype={"L_id": str})
        meta["x_index"] = np.arange(len(meta), dtype=int)
        qa = pd.read_csv(project_path(spec["qa_csv"]), dtype={"L_id": str})
        meta = meta[meta["L_id"].isin(cv_lids)].copy()
        qa = qa[qa["L_id"].isin(cv_lids)].copy()
        x = np.load(project_path(spec["window_npy"]), mmap_mode="r")
        if len(meta) != x.shape[0]:
            # Old cache metadata includes locked-test rows. Keep row indices before filtering.
            full_meta = pd.read_csv(project_path(spec["metadata_csv"]), dtype={"L_id": str})
            full_meta["x_index"] = np.arange(len(full_meta), dtype=int)
            meta = full_meta[full_meta["L_id"].isin(cv_lids)].copy()
        signal_rows: list[dict[str, Any]] = []
        qc_rows: list[dict[str, Any]] = []
        grouped = meta.groupby("L_id", sort=True).indices
        qa_by_id = qa.set_index("L_id").to_dict(orient="index") if not qa.empty else {}
        min_windows = int(spec.get("min_valid_windows", 1))
        for l_id, idx in grouped.items():
            meta_group = meta.iloc[np.asarray(idx, dtype=int)].copy()
            idx_array = meta_group["x_index"].to_numpy(dtype=int)
            if idx_array.size < min_windows:
                qc_rows.append(_blocked_qc_row(l_id, task, spec, "too_few_valid_windows", idx_array.size))
                continue
            windows = np.asarray(x[idx_array], dtype=np.float32)
            if windows.ndim != 3 or windows.shape[1] != len(channels):
                qc_rows.append(_blocked_qc_row(l_id, task, spec, "unexpected_window_shape", idx_array.size))
                continue
            feature_windows, feature_meta = _feature_window_subset(windows, meta_group, int(spec.get("max_feature_windows", 0)))
            signal = _eeg_signal_row(l_id, task, feature_windows, feature_meta, channels, float(spec["sfreq"]), config, spec)
            qc = _eeg_qc_row(l_id, task, windows, qa_by_id.get(l_id, {}), float(spec["sfreq"]), config, spec)
            signal["signal_feature_window_count"] = int(feature_windows.shape[0])
            signal_rows.append(signal)
            qc_rows.append(qc)
        signal_df = _attach_split(pd.DataFrame(signal_rows), split, label_col)
        qc_df = _attach_split(pd.DataFrame(qc_rows), split, label_col)
        signal_path = ensure_output(spec["signal_features"], config)
        qc_path = ensure_output(spec["qc_features"], config)
        signal_df.to_csv(signal_path, index=False)
        qc_df.to_csv(qc_path, index=False)
        manifest["tasks"][task] = {
            "signal_features": str(signal_path),
            "qc_features": str(qc_path),
            "subjects_signal": int(len(signal_df)),
            "subjects_qc": int(len(qc_df)),
            "source_window_npy": str(project_path(spec["window_npy"])),
            "source_metadata_csv": str(project_path(spec["metadata_csv"])),
            "source_qa_csv": str(project_path(spec["qa_csv"])),
            "task_status": spec.get("task_status", ""),
        }

    out_path = ensure_output("artifacts/goal2_6/eeg/feature_manifest.json", config)
    out_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest


def _eeg_signal_row(
    l_id: str,
    task: str,
    windows: np.ndarray,
    meta: pd.DataFrame,
    channels: list[str],
    sfreq: float,
    config: dict[str, Any],
    spec: dict[str, Any],
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "L_id": l_id,
        "task": task,
        "feature_version": config["eeg"]["feature_version"],
        "preprocessing_version": config["eeg"]["preprocessing_version"],
        "task_status": spec.get("task_status", ""),
    }
    prefix = "signal"
    row.update(basic_time_features(f"{prefix}_time", windows))
    row.update(channel_time_features(prefix, windows, channels, max_channels=0))
    row.update(hjorth_features(prefix, windows))
    row.update(spectral_features(prefix, windows, sfreq=sfreq, channel_names=channels))
    row.update(connectivity_features(prefix, windows))
    row.update(_erp_features(task, windows, meta, channels, sfreq))
    row["signal_feature_hash"] = _feature_hash(row)
    return row


def _feature_window_subset(windows: np.ndarray, meta: pd.DataFrame, max_windows: int) -> tuple[np.ndarray, pd.DataFrame]:
    if max_windows <= 0 or windows.shape[0] <= max_windows:
        return windows, meta
    indices = np.linspace(0, windows.shape[0] - 1, max_windows, dtype=int)
    return windows[indices], meta.iloc[indices].copy()


def _erp_features(task: str, windows: np.ndarray, meta: pd.DataFrame, channels: list[str], sfreq: float) -> dict[str, float]:
    if task == "rest":
        return {}
    out: dict[str, float] = {}
    time = np.arange(windows.shape[2], dtype=float) / sfreq
    if task in {"oddball"}:
        windows_by_condition = {"target": windows}
    else:
        codes = meta["event_code"].astype(str).to_numpy()
        windows_by_condition = {f"code_{code}": windows[codes == str(code)] for code in sorted(set(codes))}
    for name, subset in windows_by_condition.items():
        if subset.size == 0:
            continue
        erp = np.nanmean(subset, axis=0)
        global_erp = np.nanmean(erp, axis=0)
        for win_name, lo, hi in [("p200", 0.18, 0.28), ("p300", 0.28, 0.55), ("late", 0.55, min(0.8, time[-1]))]:
            mask = (time >= lo) & (time <= hi)
            if not np.any(mask):
                continue
            segment = global_erp[mask]
            out[f"signal_erp_{name}_{win_name}_mean"] = float(np.nanmean(segment))
            out[f"signal_erp_{name}_{win_name}_peak"] = float(np.nanmax(segment))
            out[f"signal_erp_{name}_{win_name}_trough"] = float(np.nanmin(segment))
            out[f"signal_erp_{name}_{win_name}_peak_latency"] = float(time[mask][int(np.nanargmax(segment))])
        out[f"signal_erp_{name}_trial_variability"] = float(np.nanmean(np.nanstd(subset, axis=0)))
        out[f"signal_erp_{name}_global_peak_to_peak"] = float(np.nanmax(global_erp) - np.nanmin(global_erp))
    if task == "1back" and {"signal_erp_code_18_p300_mean", "signal_erp_code_19_p300_mean"}.issubset(out):
        out["signal_erp_19_minus_18_p300_mean"] = out["signal_erp_code_19_p300_mean"] - out["signal_erp_code_18_p300_mean"]
    return out


def _eeg_qc_row(
    l_id: str,
    task: str,
    windows: np.ndarray,
    qa: dict[str, Any],
    sfreq: float,
    config: dict[str, Any],
    spec: dict[str, Any],
) -> dict[str, Any]:
    candidate = int(float(qa.get("windows", windows.shape[0]) or windows.shape[0])) + int(float(qa.get("rejected_windows", 0) or 0))
    rejected = int(float(qa.get("rejected_windows", 0) or 0))
    ptp = np.ptp(windows, axis=2)
    var = np.var(windows, axis=(0, 2))
    diff = np.diff(windows, axis=2)
    high_freq = np.nanstd(diff, axis=(0, 2)) / (np.nanstd(windows, axis=(0, 2)) + 1e-12)
    row = {
        "L_id": l_id,
        "task": task,
        "feature_version": config["eeg"]["feature_version"],
        "preprocessing_version": config["eeg"]["preprocessing_version"],
        "task_status": spec.get("task_status", ""),
        "qc_valid_window_count": int(windows.shape[0]),
        "qc_rejected_window_count": rejected,
        "qc_rejected_window_rate": float(rejected / candidate) if candidate else math.nan,
        "qc_effective_duration_sec": float(windows.shape[0] * windows.shape[2] / sfreq),
        "qc_channel_count": int(windows.shape[1]),
        "qc_flat_channel_count": int(np.sum(np.nanmean(ptp, axis=0) < 1e-6)),
        "qc_flat_channel_rate": float(np.mean(np.nanmean(ptp, axis=0) < 1e-6)),
        "qc_extreme_amplitude_rate": float(np.mean(np.abs(windows) > 8.0)),
        "qc_excessive_variance_channel_count": int(np.sum(var > np.nanmedian(var) * 10.0)) if np.isfinite(var).any() else 0,
        "qc_excessive_variance_channel_rate": float(np.mean(var > np.nanmedian(var) * 10.0)) if np.isfinite(var).any() else 0.0,
        "qc_bad_channel_count": int(np.sum((np.nanmean(ptp, axis=0) < 1e-6) | (var > np.nanmedian(var) * 10.0))) if np.isfinite(var).any() else 0,
        "qc_bad_channel_rate": float(np.mean((np.nanmean(ptp, axis=0) < 1e-6) | (var > np.nanmedian(var) * 10.0))) if np.isfinite(var).any() else 0.0,
        "qc_line_noise_proxy": float(np.nanmean(high_freq)),
        "qc_signal_variance_mean": float(np.nanmean(var)),
        "qc_signal_variance_std": float(np.nanstd(var)),
        "qc_sampling_rate": sfreq,
        "qc_feature_status": "ok",
        "qc_failure_reason": "",
    }
    return row


def _blocked_qc_row(l_id: str, task: str, spec: dict[str, Any], reason: str, windows: int) -> dict[str, Any]:
    return {
        "L_id": l_id,
        "task": task,
        "feature_version": "",
        "preprocessing_version": "",
        "task_status": spec.get("task_status", ""),
        "qc_valid_window_count": int(windows),
        "qc_feature_status": "blocked",
        "qc_failure_reason": reason,
    }


def _attach_split(frame: pd.DataFrame, split: pd.DataFrame, label_col: str) -> pd.DataFrame:
    if frame.empty:
        return frame
    keep = [
        "L_id",
        "A_id",
        label_col,
        "split_group",
        "split_role",
        "is_locked_test",
        "cv_fold",
        "sex",
        "age",
        "grade",
        "grade_group",
        "fnirs_device",
    ]
    keep = [col for col in keep if col in split.columns]
    merged = split[keep].merge(frame, on="L_id", how="inner")
    if "is_locked_test" in merged.columns and pd.to_numeric(merged["is_locked_test"], errors="coerce").fillna(0).astype(int).any():
        raise ValueError("Goal 2.6 EEG features unexpectedly include pilot-holdout subjects.")
    return merged.sort_values("L_id").reset_index(drop=True)


def _feature_hash(row: dict[str, Any]) -> str:
    payload = json.dumps({k: v for k, v in row.items() if k.startswith("signal_")}, sort_keys=True, default=str)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:12]
