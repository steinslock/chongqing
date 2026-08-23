"""fNIRS Goal 2.7 device-specific event-audited traditional features."""

from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from scipy.io import loadmat

from .config import ensure_output, load_goal_config, project_path
from .io import cv_subjects
from .stats import autocorr_lag1, basic_time_features, channel_time_features, connectivity_features, spectral_features

L_ID_RE = re.compile(r"(?<![A-Za-z0-9])L\d+(?![A-Za-z0-9])", re.IGNORECASE)


def extract_fnirs_features(config_path: str | Path = "configs/goal2_7/fnirs.yaml") -> dict[str, Any]:
    config = load_goal_config(config_path)
    split = cv_subjects(config)
    cv_lids = set(split["L_id"].astype(str))
    raw_root = project_path(config["paths"]["raw_data_dir"])
    n_jobs = int(config.get("run", {}).get("n_jobs", 1))
    manifest: dict[str, Any] = {
        "config": str(project_path(config_path)),
        "preprocessing_version": config["fnirs"]["preprocessing_version"],
        "feature_version": config["fnirs"]["feature_version"],
        "tasks": {},
    }
    for device, device_cfg in config["fnirs"]["devices"].items():
        for task in config["fnirs"]["tasks"]:
            task_dir = raw_root / device_cfg["dirs"][task]
            out_dir = config["fnirs"]["outputs"]["dir"]
            stem = f"{device}_{task}"
            signal_path = ensure_output(f"{out_dir}/{stem}_signal_features.csv", config)
            qc_path = ensure_output(f"{out_dir}/{stem}_qc_features.csv", config)
            log_path = ensure_output(f"{out_dir}/{stem}_preprocessing_log.json", config)
            excluded_path = ensure_output(f"{out_dir}/{stem}_excluded_subjects.csv", config)
            if signal_path.exists() and qc_path.exists() and log_path.exists():
                signal_df = pd.read_csv(signal_path, dtype={"L_id": str})
                qc_df = pd.read_csv(qc_path, dtype={"L_id": str})
                manifest["tasks"][stem] = {
                    "signal_features": str(signal_path),
                    "qc_features": str(qc_path),
                    "preprocessing_log": str(log_path),
                    "excluded_subjects": str(excluded_path),
                    "subjects_found": int(len(qc_df)),
                    "signal_rows": int(len(signal_df)),
                    "qc_rows": int(len(qc_df)),
                    "representation": device_cfg.get("representation", ""),
                    "task_segment_rule": config["fnirs"].get("task_segment_rule", ""),
                    "raw_channel_merge": "forbidden",
                    "status": "reused_existing",
                }
                continue
            files = _collect_yiruid(task_dir) if device == "yiruid" else _collect_bikom(task_dir)
            subject_items = [(l_id, files[l_id]) for l_id in sorted(files) if l_id in cv_lids]
            if n_jobs == 1:
                results = [_process_subject(device, task, item, config) for item in subject_items]
            else:
                results = Parallel(n_jobs=n_jobs, backend="loky")(
                    delayed(_process_subject)(device, task, item, config) for item in subject_items
                )
            signal_rows = [signal for signal, qc in results if signal]
            qc_rows = [qc for signal, qc in results if qc]
            signal_df = _attach_split(pd.DataFrame(signal_rows), split, config)
            qc_df = _attach_split(pd.DataFrame(qc_rows), split, config)
            signal_df.to_csv(signal_path, index=False)
            qc_df.to_csv(qc_path, index=False)
            excluded = qc_df[qc_df.get("qc_feature_status", "") != "ok"].copy() if not qc_df.empty else pd.DataFrame()
            excluded.to_csv(excluded_path, index=False)
            log = {
                "device": device,
                "task": task,
                "subjects_found": len(subject_items),
                "signal_rows": len(signal_df),
                "qc_rows": len(qc_df),
                "representation": device_cfg.get("representation", ""),
                "task_segment_rule": config["fnirs"].get("task_segment_rule", ""),
                "raw_channel_merge": "forbidden",
            }
            log_path.write_text(json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8")
            manifest["tasks"][stem] = {
                "signal_features": str(signal_path),
                "qc_features": str(qc_path),
                "preprocessing_log": str(log_path),
                "excluded_subjects": str(excluded_path),
                **log,
            }
    manifest_path = ensure_output("artifacts/goal2_7/fnirs/feature_manifest.json", config)
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest


def _process_subject(device: str, task: str, item: tuple[str, Any], config: dict[str, Any]) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    l_id, payload = item
    try:
        if device == "yiruid":
            signal, qc = _process_yiruid(l_id, task, payload, config)
        else:
            signal, qc = _process_bikom(l_id, task, payload, config)
        return signal, qc
    except Exception as exc:  # noqa: BLE001
        return None, _blocked_qc(l_id, device, task, type(exc).__name__ + ":" + str(exc)[:160], config)


def _process_yiruid(l_id: str, task: str, path: Path, config: dict[str, Any]) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    data = loadmat(path, squeeze_me=False, struct_as_record=False)
    raw = np.asarray(data.get("d"), dtype=float)
    t = np.asarray(data.get("t"), dtype=float).reshape(-1)
    ml = np.asarray(data.get("ml"), dtype=float) if "ml" in data else np.empty((0, 0))
    if raw.ndim != 2 or raw.shape[0] < 8:
        return None, _blocked_qc(l_id, "yiruid", task, "missing_or_invalid_d", config)
    raw = raw[:, np.nanstd(raw, axis=0) > 0]
    if raw.size == 0:
        return None, _blocked_qc(l_id, "yiruid", task, "all_channels_constant", config)
    sfreq = _sampling_rate(t)
    baseline = np.nanmedian(raw[: max(5, int(round(sfreq * 5)))], axis=0)
    baseline = np.where(np.isfinite(baseline) & (baseline > 0), baseline, np.nanmedian(raw, axis=0))
    od = -np.log(np.maximum(raw, 1e-6) / np.maximum(baseline, 1e-6))
    marker = _yiruid_marker(data, raw.shape[0])
    channels = [f"ch{idx + 1}" for idx in range(raw.shape[1])]
    signal = _base_signal_row(l_id, "fnirs", "yiruid", task, config)
    signal.update(_fnirs_signal_features("signal_raw", np.log(np.maximum(raw, 1e-6)), sfreq, channels, config))
    signal.update(_fnirs_signal_features("signal_od", od, sfreq, channels, config))
    signal.update(_task_delta_features("signal_od", od, marker, task, config))
    signal["signal_ml_rows"] = int(ml.shape[0]) if ml.ndim == 2 else 0
    signal["signal_task_response_status"] = _task_response_status(task)
    signal["event_validity_status"] = _fnirs_event_validity_status("yiruid", task, int(np.count_nonzero(marker)))
    qc = _fnirs_qc_row(l_id, "yiruid", task, od, t, marker, config)
    qc["qc_raw_channel_count"] = int(raw.shape[1])
    qc["qc_ml_rows"] = int(ml.shape[0]) if ml.ndim == 2 else 0
    qc["qc_wavelength_semantics"] = "ml wavelength indices present; wavelength values not confirmed in nirs header"
    qc["qc_task_response_status"] = _task_response_status(task)
    qc["event_validity_status"] = _fnirs_event_validity_status("yiruid", task, int(np.count_nonzero(marker)))
    return signal, qc


def _process_bikom(l_id: str, task: str, roles: dict[str, list[Path]], config: dict[str, Any]) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    max_rows = int(config["fnirs"].get("bikom_max_rows", 0) or 0)
    hbo = _read_bikom_data(_first(roles.get("HbO", [])), max_rows=max_rows)
    hbr = _read_bikom_data(_first(roles.get("HbR", [])), max_rows=max_rows)
    hbt = _read_bikom_data(_first(roles.get("HbT", [])), max_rows=max_rows) if roles.get("HbT") else None
    if hbo is None or hbr is None:
        return None, _blocked_qc(l_id, "bikom", task, "missing_hbo_or_hbr_csv", config)
    hbo_values, time, marker = hbo
    hbr_values, _, _ = hbr
    hbt_values = hbt[0] if hbt is not None else np.full_like(hbo_values, np.nan)
    sfreq = _sampling_rate(time)
    channels = [f"ch{idx + 1}" for idx in range(hbo_values.shape[1])]
    signal = _base_signal_row(l_id, "fnirs", "bikom", task, config)
    signal.update(_fnirs_signal_features("signal_hbo", hbo_values, sfreq, channels, config))
    signal.update(_fnirs_signal_features("signal_hbr", hbr_values, sfreq, channels, config))
    signal.update(_fnirs_signal_features("signal_hbt", hbt_values, sfreq, channels, config))
    signal.update(_task_delta_features("signal_hbo", hbo_values, marker, task, config))
    signal.update(_task_delta_features("signal_hbr", hbr_values, marker, task, config))
    signal["signal_task_response_status"] = _task_response_status(task)
    signal["event_validity_status"] = _fnirs_event_validity_status("bikom", task, int(np.count_nonzero(marker)))
    if hbo_values.shape == hbr_values.shape:
        corr = [np.corrcoef(hbo_values[:, i], hbr_values[:, i])[0, 1] for i in range(hbo_values.shape[1])]
        signal["signal_hbo_hbr_corr_mean"] = float(np.nanmean(corr))
        signal["signal_hbo_hbr_corr_std"] = float(np.nanstd(corr))
    qc = _fnirs_qc_row(l_id, "bikom", task, hbo_values, time, marker, config)
    qc["qc_hbo_channel_count"] = int(hbo_values.shape[1])
    qc["qc_hbr_channel_count"] = int(hbr_values.shape[1])
    qc["qc_wavelength_semantics"] = "vendor CSV already contains HbO/HbR/HbT outputs"
    qc["qc_bikom_max_rows"] = max_rows
    qc["qc_bikom_raw_rows"] = int(hbo_values.shape[0])
    qc["qc_bikom_used_rows"] = int(hbo_values.shape[0])
    qc["qc_bikom_truncated"] = 0
    qc["qc_bikom_previous_2000_cap_would_truncate"] = int(hbo_values.shape[0] > 2000)
    qc["qc_bikom_markers_after_previous_2000_cap"] = int(np.count_nonzero(marker[2000:])) if marker.size > 2000 else 0
    qc["qc_task_response_status"] = _task_response_status(task)
    qc["event_validity_status"] = _fnirs_event_validity_status("bikom", task, int(np.count_nonzero(marker)))
    return signal, qc


def _fnirs_signal_features(prefix: str, data: np.ndarray, sfreq: float, channels: list[str], config: dict[str, Any]) -> dict[str, float]:
    max_channels = int(config["fnirs"].get("max_channel_features", 0))
    out: dict[str, float] = {}
    out.update(basic_time_features(f"{prefix}_time", data))
    out.update(channel_time_features(prefix, data.T, channels, max_channels=max_channels))
    out.update(spectral_features(prefix, data.T, sfreq=max(sfreq, 1.0), channel_names=None))
    out.update(connectivity_features(prefix, data.T))
    slopes = [np.polyfit(np.linspace(0.0, 1.0, data.shape[0]), data[:, i], 1)[0] for i in range(data.shape[1])]
    out[f"{prefix}_slope_mean"] = float(np.nanmean(slopes))
    out[f"{prefix}_slope_std"] = float(np.nanstd(slopes))
    out[f"{prefix}_autocorr_lag1_mean"] = float(np.nanmean([autocorr_lag1(data[:, i]) for i in range(data.shape[1])]))
    mid = data.shape[1] // 2
    if mid > 0:
        left = np.nanmean(data[:, :mid])
        right = np.nanmean(data[:, mid:])
        out[f"{prefix}_hemisphere_proxy_asymmetry"] = float(right - left)
    return out


def _task_delta_features(prefix: str, data: np.ndarray, marker: np.ndarray, task: str, config: dict[str, Any]) -> dict[str, float]:
    if task == "rest":
        return {}
    if config.get("fnirs", {}).get("task_response_without_confirmed_timing") == "blocked":
        return {}
    baseline, active, recovery = _segments(data, marker)
    out: dict[str, float] = {}
    if baseline.size and active.size:
        base_mean = np.nanmean(baseline, axis=0)
        active_mean = np.nanmean(active, axis=0)
        delta = active_mean - base_mean
        out[f"{prefix}_baseline_mean"] = float(np.nanmean(base_mean))
        out[f"{prefix}_task_mean"] = float(np.nanmean(active_mean))
        out[f"{prefix}_task_minus_baseline_delta_mean"] = float(np.nanmean(delta))
        out[f"{prefix}_task_minus_baseline_delta_std"] = float(np.nanstd(delta))
        out[f"{prefix}_task_auc_mean"] = float(np.nanmean(np.trapz(active, axis=0)))
        peak = np.nanmax(active, axis=0)
        out[f"{prefix}_task_peak_amplitude_mean"] = float(np.nanmean(peak))
        out[f"{prefix}_trial_block_variability"] = float(np.nanmean(np.nanstd(active, axis=0)))
    if active.size and recovery.size:
        out[f"{prefix}_recovery_minus_task_mean"] = float(np.nanmean(recovery) - np.nanmean(active))
    return out


def _segments(data: np.ndarray, marker: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    n = data.shape[0]
    nonzero = np.flatnonzero(marker)
    if nonzero.size:
        first = int(nonzero[0])
        last = int(nonzero[-1])
        baseline = data[: max(first, 1)]
        active = data[first : max(last + 1, first + 1)]
        recovery = data[last + 1 :]
    else:
        baseline = np.empty((0, data.shape[1]))
        active = np.empty((0, data.shape[1]))
        recovery = np.empty((0, data.shape[1]))
    return baseline, active, recovery


def _fnirs_qc_row(l_id: str, device: str, task: str, data: np.ndarray, time: np.ndarray, marker: np.ndarray, config: dict[str, Any]) -> dict[str, Any]:
    invalid = ~np.isfinite(data)
    channel_var = np.nanvar(data, axis=0)
    diff = np.diff(data, axis=0)
    diff_abs = np.abs(diff)
    motion_threshold = np.nanmedian(diff_abs) + 6.0 * np.nanstd(diff_abs)
    if not math.isfinite(motion_threshold) or motion_threshold <= 0:
        motion_threshold = math.inf
    duration = float(np.nanmax(time) - np.nanmin(time)) if time.size and np.isfinite(time).any() else float(data.shape[0])
    sfreq = _sampling_rate(time)
    row = {
        "L_id": l_id,
        "modality": "fnirs",
        "device": device,
        "task": task,
        "feature_version": config["fnirs"]["feature_version"],
        "preprocessing_version": config["fnirs"]["preprocessing_version"],
        "qc_feature_status": "ok",
        "qc_failure_reason": "",
        "qc_channel_count": int(data.shape[1]) if data.ndim == 2 else 0,
        "qc_bad_channel_count": int(np.sum(channel_var < 1e-12)),
        "qc_bad_channel_rate": float(np.mean(channel_var < 1e-12)),
        "qc_near_constant_channel_rate": float(np.mean(channel_var < 1e-10)),
        "qc_extreme_value_rate": float(np.mean(np.abs(data) > np.nanpercentile(np.abs(data), 99.9))) if np.isfinite(data).any() else math.nan,
        "qc_saturated_invalid_value_rate": float(np.mean(invalid)),
        "qc_missing_value_rate": float(np.mean(invalid)),
        "qc_high_frequency_noise_proxy": float(np.nanmean(np.nanstd(diff, axis=0) / (np.nanstd(data, axis=0) + 1e-12))) if diff.size else math.nan,
        "qc_motion_artifact_rate": float(np.mean(diff_abs > motion_threshold)) if diff_abs.size and math.isfinite(motion_threshold) else 0.0,
        "qc_valid_duration_sec": duration,
        "qc_sampling_rate": sfreq,
        "qc_valid_task_segment_count": int(np.count_nonzero(marker)) if marker.size else 0,
        "qc_baseline_available": int(data.shape[0] >= 10),
        "qc_hbo_hbr_variance_proxy_mean": float(np.nanmean(channel_var)),
        "qc_region_mapping_status": "unconfirmed_channel_global_hemisphere_only",
        "qc_task_response_status": _task_response_status(task),
        "event_validity_status": _fnirs_event_validity_status(device, task, int(np.count_nonzero(marker)) if marker.size else 0),
    }
    return row


def _blocked_qc(l_id: str, device: str, task: str, reason: str, config: dict[str, Any]) -> dict[str, Any]:
    return {
        "L_id": l_id,
        "modality": "fnirs",
        "device": device,
        "task": task,
        "feature_version": config.get("fnirs", {}).get("feature_version", ""),
        "preprocessing_version": config.get("fnirs", {}).get("preprocessing_version", ""),
        "qc_feature_status": "blocked",
        "qc_failure_reason": reason,
        "qc_task_response_status": _task_response_status(task),
        "event_validity_status": _fnirs_event_validity_status(device, task, 0),
    }


def _base_signal_row(l_id: str, modality: str, device: str, task: str, config: dict[str, Any]) -> dict[str, Any]:
    return {
        "L_id": l_id,
        "modality": modality,
        "device": device,
        "task": task,
        "feature_version": config["fnirs"]["feature_version"],
        "preprocessing_version": config["fnirs"]["preprocessing_version"],
        "event_validity_status": _fnirs_event_validity_status(device, task, -1),
    }


def _attach_split(frame: pd.DataFrame, split: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
    if frame.empty:
        return frame
    label_col = config.get("run", {}).get("label_column", "primary_label_nonhealthy")
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
    if pd.to_numeric(merged.get("is_locked_test", 0), errors="coerce").fillna(0).astype(int).any():
        raise ValueError("Goal 2.7 fNIRS features unexpectedly include pilot-holdout subjects.")
    return merged.sort_values("L_id").reset_index(drop=True)


def _task_response_status(task: str) -> str:
    if task == "rest":
        return "whole_recording_event_free"
    return "segment_blocked_no_confirmed_timing"


def _fnirs_event_validity_status(device: str, task: str, marker_count: int) -> str:
    if task == "rest":
        return "event_free_rest_whole_recording"
    if marker_count > 0:
        return f"{device}_{task}_markers_present_timing_semantics_unconfirmed"
    if marker_count == 0:
        return f"{device}_{task}_no_markers_task_response_blocked"
    return f"{device}_{task}_whole_recording_only"


def _collect_yiruid(task_dir: Path) -> dict[str, Path]:
    out: dict[str, Path] = {}
    if not task_dir.exists():
        return out
    for path in sorted(task_dir.rglob("*.nirs")):
        l_id = _extract_l_id(str(path))
        if l_id and l_id not in out:
            out[l_id] = path
    return out


def _collect_bikom(task_dir: Path) -> dict[str, dict[str, list[Path]]]:
    out: dict[str, dict[str, list[Path]]] = {}
    if not task_dir.exists():
        return out
    for path in sorted(task_dir.rglob("*.csv")):
        l_id = _extract_l_id(str(path))
        if not l_id:
            continue
        lower = path.name.lower()
        if "hba_oxy" in lower:
            role = "HbO"
        elif "hba_deoxy" in lower:
            role = "HbR"
        elif "hba_total" in lower:
            role = "HbT"
        elif "_mes_" in lower or lower.endswith("_mes.csv"):
            role = "Mes"
        else:
            role = "other"
        out.setdefault(l_id, {}).setdefault(role, []).append(path)
    return out


def _read_bikom_data(path: Path | None, max_rows: int = 0) -> tuple[np.ndarray, np.ndarray, np.ndarray] | None:
    if path is None or not path.exists():
        return None
    skiprows = _data_header_skiprows(path)
    if skiprows is None:
        return None
    try:
        df = pd.read_csv(path, skiprows=skiprows, encoding="utf-8-sig", nrows=max_rows if max_rows > 0 else None)
    except UnicodeDecodeError:
        df = pd.read_csv(path, skiprows=skiprows, encoding="gb18030", nrows=max_rows if max_rows > 0 else None)
    if df.empty:
        return None
    channel_cols = [col for col in df.columns if str(col).startswith("CH")]
    if not channel_cols:
        return None
    values = df[channel_cols].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
    time = pd.to_numeric(df["Time"], errors="coerce").to_numpy(dtype=float) if "Time" in df.columns else np.arange(len(df), dtype=float)
    if "Mark" in df.columns:
        mark = df["Mark"].astype(str).str.strip()
        marker = (~mark.isin(["", "0", "nan", "None"])).astype(int).to_numpy()
    else:
        marker = np.zeros(len(df), dtype=int)
    return values, time, marker


def _data_header_skiprows(path: Path) -> int | None:
    with path.open("r", encoding="utf-8-sig", errors="replace") as handle:
        for idx, line in enumerate(handle):
            if line.strip() == "Data":
                return idx + 1
    return None


def _yiruid_marker(data: dict[str, Any], n: int) -> np.ndarray:
    marker = np.zeros(n, dtype=int)
    s = data.get("s")
    if s is not None:
        arr = np.asarray(s).reshape(-1)
        if arr.size == n:
            marker = (arr != 0).astype(int)
    mark = data.get("Mark_infor")
    try:
        arr = np.asarray(mark).reshape(-1)
        numeric = pd.to_numeric(pd.Series(arr), errors="coerce").dropna().astype(int).to_numpy()
        numeric = numeric[(numeric >= 0) & (numeric < n)]
        marker[numeric] = 1
    except Exception:
        pass
    return marker


def _sampling_rate(time: np.ndarray) -> float:
    arr = np.asarray(time, dtype=float).reshape(-1)
    arr = arr[np.isfinite(arr)]
    if arr.size < 3:
        return 1.0
    diffs = np.diff(arr)
    diffs = diffs[(diffs > 0) & np.isfinite(diffs)]
    if diffs.size == 0:
        return 1.0
    return float(1.0 / np.median(diffs))


def _extract_l_id(text: str) -> str:
    match = L_ID_RE.search(text)
    return match.group(0).upper() if match else ""


def _first(paths: list[Path] | None) -> Path | None:
    return sorted(paths)[0] if paths else None
