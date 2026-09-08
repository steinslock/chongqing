"""fNIRS features for Goal 2.8, driven by the paradigm specification.

Goal 2.7 blocked every task-response feature because timing looked unconfirmed,
and its `_segments()` took the task window as "first marker to last marker",
which degenerates to a single sample for VFT and swallows all ten rest periods
for Oddball. Here the block windows come from the specification plus the
recorded markers, and Yiruid intensity is converted to real HbO/HbR.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ..paradigm import load_paradigm_spec
from ..paradigm.spec import FnirsTaskSpec, ParadigmSpec
from .config import cv_subjects, ensure_output, load_goal_config, project_path
from .fnirs_io import modified_beer_lambert, optical_density, read_bikom_csv, read_yiruid_nirs
from .fnirs_regions import region_groups

L_ID_RE = re.compile(r"(?<![A-Za-z0-9])L\d+(?![A-Za-z0-9])", re.IGNORECASE)


def _extract_l_id(text: str) -> str:
    match = L_ID_RE.search(text)
    return match.group(0).upper() if match else ""


def collect_yiruid(task_dir: Path) -> dict[str, Path]:
    out: dict[str, Path] = {}
    if task_dir.exists():
        for path in sorted(task_dir.rglob("*.nirs")):
            l_id = _extract_l_id(path.name) or _extract_l_id(str(path))
            if l_id and l_id not in out:
                out[l_id] = path
    return out


def collect_bikom(task_dir: Path) -> dict[str, dict[str, Path]]:
    out: dict[str, dict[str, Path]] = {}
    if not task_dir.exists():
        return out
    for path in sorted(task_dir.rglob("*.csv")):
        l_id = _extract_l_id(path.name) or _extract_l_id(str(path))
        if not l_id:
            continue
        lower = path.name.lower()
        role = ("HbO" if "hba_oxy" in lower else
                "HbR" if "hba_deoxy" in lower else
                "HbT" if "hba_total" in lower else None)
        if role:
            out.setdefault(l_id, {}).setdefault(role, path)
    return out


def _bikom_block_windows(marks: list[dict[str, Any]], ts: FnirsTaskSpec) -> list[dict[str, float]]:
    """Block windows straight from the labelled marks: A0/A1 and B0/B1 pairs."""
    baseline_sec = float(ts.raw.get("baseline_sec", 30))
    opens = [m for m in marks if m["label"] in ("A0", "B0")]
    closes = [m for m in marks if m["label"] in ("A1", "B1")]
    windows: list[dict[str, float]] = []
    for index, open_mark in enumerate(opens):
        close = next((c for c in closes if c["onset_sec"] > open_mark["onset_sec"]), None)
        if close is None:
            continue
        start = float(open_mark["onset_sec"])
        end = float(close["onset_sec"])
        windows.append({
            "block": float(index),
            "baseline_start": max(0.0, start - baseline_sec), "baseline_end": start,
            "task_start": start, "task_end": end,
            "recovery_start": end, "recovery_end": min(end + baseline_sec, float(ts.duration_sec)),
        })
    return windows


def _nan_safe(fn, values: np.ndarray, **kwargs) -> Any:
    """Reduce with a nan-aware function, returning NaN for all-NaN input.

    Some recordings carry channels that are NaN throughout; numpy raises on an
    all-NaN slice rather than returning NaN.
    """
    array = np.asarray(values, dtype=float)
    if array.size == 0 or not np.any(np.isfinite(array)):
        axis = kwargs.get("axis")
        if axis is None:
            return float("nan")
        shape = list(array.shape)
        if 0 <= axis < len(shape):
            shape.pop(axis)
        return np.full(shape or (1,), np.nan)
    with np.errstate(invalid="ignore"):
        import warnings as _w
        with _w.catch_warnings():
            _w.simplefilter("ignore")
            return fn(array, **kwargs)


def _slice(values: np.ndarray, time: np.ndarray, start: float, end: float) -> np.ndarray:
    mask = (time >= start) & (time < end)
    return values[mask] if np.any(mask) else np.empty((0, values.shape[1]))


def _block_features(prefix: str, values: np.ndarray, time: np.ndarray,
                    windows: list[dict[str, float]], groups: dict[str, list[int]]) -> dict[str, float]:
    """Per-block task-minus-baseline change, averaged over blocks and regions."""
    out: dict[str, float] = {}
    if not windows or values.size == 0:
        return out
    deltas: list[np.ndarray] = []
    peaks: list[np.ndarray] = []
    latencies: list[float] = []
    aucs: list[float] = []
    recoveries: list[float] = []
    for window in windows:
        baseline = _slice(values, time, window["baseline_start"], window["baseline_end"])
        task = _slice(values, time, window["task_start"], window["task_end"])
        if baseline.size == 0 or task.size == 0:
            continue
        if not np.any(np.isfinite(baseline)) or not np.any(np.isfinite(task)):
            continue
        base_mean = _nan_safe(np.nanmean, baseline, axis=0)
        corrected = task - base_mean
        deltas.append(_nan_safe(np.nanmean, corrected, axis=0))
        peaks.append(_nan_safe(np.nanmax, corrected, axis=0))
        grand = _nan_safe(np.nanmean, corrected, axis=1)
        if np.size(grand) and np.any(np.isfinite(grand)):
            latencies.append(float(np.nanargmax(grand)) / max(1, np.size(grand))
                             * (window["task_end"] - window["task_start"]))
            aucs.append(float(np.trapezoid(grand)))
        recovery = _slice(values, time, window["recovery_start"], window["recovery_end"])
        if recovery.size and np.any(np.isfinite(recovery)):
            recoveries.append(float(_nan_safe(np.nanmean, recovery - base_mean)))

    if not deltas:
        return out
    delta = np.vstack(deltas)                       # (n_blocks, n_channels)
    mean_delta = np.nanmean(delta, axis=0)          # (n_channels,)
    out[f"{prefix}_block_delta_mean"] = float(_nan_safe(np.nanmean, mean_delta))
    out[f"{prefix}_block_delta_std"] = float(_nan_safe(np.nanstd, mean_delta))
    out[f"{prefix}_block_peak_mean"] = float(_nan_safe(np.nanmean, np.vstack(peaks)))
    out[f"{prefix}_n_blocks_used"] = float(delta.shape[0])
    if latencies:
        out[f"{prefix}_time_to_peak_mean_sec"] = float(np.nanmean(latencies))
    if aucs:
        out[f"{prefix}_block_auc_mean"] = float(np.nanmean(aucs))
    if recoveries:
        out[f"{prefix}_recovery_mean"] = float(np.nanmean(recoveries))
    if delta.shape[0] > 1:
        block_means = _nan_safe(np.nanmean, delta, axis=1)
        out[f"{prefix}_block_consistency_std"] = float(np.nanstd(block_means))
        out[f"{prefix}_block_first_minus_last"] = float(block_means[0] - block_means[-1])

    for region, channels in groups.items():
        idx = [c - 1 for c in channels if 0 <= c - 1 < mean_delta.size]
        if idx:
            out[f"{prefix}_block_delta_{region}"] = float(_nan_safe(np.nanmean, mean_delta[idx]))
    left = [c - 1 for r, ch in groups.items() if r.endswith("_left") for c in ch]
    right = [c - 1 for r, ch in groups.items() if r.endswith("_right") for c in ch]
    left = [i for i in left if i < mean_delta.size]
    right = [i for i in right if i < mean_delta.size]
    if left and right:
        out[f"{prefix}_block_delta_lateralisation"] = float(
            _nan_safe(np.nanmean, mean_delta[right]) - _nan_safe(np.nanmean, mean_delta[left]))
    return out


def _whole_recording_features(prefix: str, values: np.ndarray, groups: dict[str, list[int]]) -> dict[str, float]:
    out: dict[str, float] = {}
    if values.size == 0:
        return out
    out[f"{prefix}_mean"] = float(_nan_safe(np.nanmean, values))
    out[f"{prefix}_std"] = float(_nan_safe(np.nanstd, values))
    channel_std = _nan_safe(np.nanstd, values, axis=0)
    out[f"{prefix}_channel_std_mean"] = float(_nan_safe(np.nanmean, channel_std))
    finite = np.where(np.isfinite(values), values, 0.0)
    slopes = np.polyfit(np.linspace(0, 1, finite.shape[0]), finite, 1)[0]
    out[f"{prefix}_slope_mean"] = float(_nan_safe(np.nanmean, slopes))
    out[f"{prefix}_slope_std"] = float(_nan_safe(np.nanstd, slopes))
    with np.errstate(invalid="ignore"):
        corr = np.corrcoef(np.where(np.isfinite(values), values, 0.0).T)
    upper = corr[np.triu_indices_from(corr, k=1)]
    out[f"{prefix}_connectivity_mean"] = float(_nan_safe(np.nanmean, upper))
    out[f"{prefix}_connectivity_std"] = float(_nan_safe(np.nanstd, upper))
    for region, channels in groups.items():
        idx = [c - 1 for c in channels if 0 <= c - 1 < values.shape[1]]
        if idx:
            out[f"{prefix}_mean_{region}"] = float(_nan_safe(np.nanmean, values[:, idx]))
    return out


def _process_yiruid(l_id: str, path: Path, ts: FnirsTaskSpec, age: float,
                    spec: ParadigmSpec) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    qc: dict[str, Any] = {"L_id": l_id, "modality": "fnirs", "device": "yiruid", "task": ts.task,
                          "qc_feature_status": "blocked", "qc_failure_reason": ""}
    try:
        rec = read_yiruid_nirs(path)
    except Exception as exc:  # noqa: BLE001
        qc["qc_failure_reason"] = f"read_error:{type(exc).__name__}"
        return None, qc

    distances = rec.source_detector_distances_mm()
    od = optical_density(rec.raw_intensity)
    try:
        hbo, hbr = modified_beer_lambert(od, rec.measurement_list, rec.wavelengths_nm, distances, age)
    except Exception as exc:  # noqa: BLE001
        qc["qc_failure_reason"] = f"mbll_error:{type(exc).__name__}"
        return None, qc

    time = rec.time
    groups = region_groups("yiruid")
    long_sep = spec.data["fnirs"]["yiruid"]["geometry"].get("long_separation_channels", [])

    signal: dict[str, Any] = {
        "L_id": l_id, "modality": "fnirs", "device": "yiruid", "task": ts.task,
        "feature_version": "goal2_8_fnirs_mbll_block_v1",
        "event_validity_status": "confirmed_from_paradigm_spec",
        "signal_hb_units": "micromolar",
    }
    signal.update(_whole_recording_features("signal_hbo", hbo, groups))
    signal.update(_whole_recording_features("signal_hbr", hbr, groups))

    onsets = rec.marker_onsets_sec
    windows = ts.block_windows(onsets) if not ts.event_free else []
    if windows:
        signal.update(_block_features("signal_hbo", hbo, time, windows, groups))
        signal.update(_block_features("signal_hbr", hbr, time, windows, groups))

    corr = [np.corrcoef(hbo[:, i], hbr[:, i])[0, 1] for i in range(min(hbo.shape[1], hbr.shape[1]))]
    signal["signal_hbo_hbr_corr_mean"] = float(np.nanmean(corr))

    expected = ts.expected_marker_count
    qc.update({
        "qc_feature_status": "ok", "qc_failure_reason": "",
        "qc_duration_sec": rec.duration_sec, "qc_sampling_rate": rec.sfreq_hz,
        "qc_channel_count": rec.n_channels,
        "qc_marker_count": len(onsets),
        "qc_marker_count_expected": expected if expected is not None else np.nan,
        "qc_marker_conformant": int(expected is None or len(onsets) == expected),
        "qc_blocks_used": len(windows),
        "qc_timing_confidence": ts.timing_confidence,
        "qc_long_separation_channels": len(long_sep),
        "qc_wavelengths_nm": "/".join(str(int(w)) for w in rec.wavelengths_nm),
        "qc_region_mapping_status": "mni_projected_yrd53",
        "qc_missing_value_rate": float(np.mean(~np.isfinite(hbo))),
        "qc_flat_channel_rate": float(np.mean(np.nanstd(hbo, axis=0) < 1e-9)),
        "qc_motion_proxy": float(np.nanmean(np.nanstd(np.diff(hbo, axis=0), axis=0))),
    })
    return signal, qc


def _process_bikom(l_id: str, roles: dict[str, Path], ts: FnirsTaskSpec,
                   spec: ParadigmSpec) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    qc: dict[str, Any] = {"L_id": l_id, "modality": "fnirs", "device": "bikom", "task": ts.task,
                          "qc_feature_status": "blocked", "qc_failure_reason": ""}
    if "HbO" not in roles or "HbR" not in roles:
        qc["qc_failure_reason"] = "missing_hbo_or_hbr_csv"
        return None, qc
    try:
        hbo_rec = read_bikom_csv(roles["HbO"])
        hbr_rec = read_bikom_csv(roles["HbR"])
    except Exception as exc:  # noqa: BLE001
        qc["qc_failure_reason"] = f"read_error:{type(exc).__name__}"
        return None, qc

    hbo, hbr = hbo_rec["values"], hbr_rec["values"]
    time = np.arange(hbo.shape[0]) * hbo_rec["sampling_period_sec"]
    groups = region_groups("bikom")

    signal: dict[str, Any] = {
        "L_id": l_id, "modality": "fnirs", "device": "bikom", "task": ts.task,
        "feature_version": "goal2_8_fnirs_mbll_block_v1",
        "event_validity_status": "confirmed_from_paradigm_spec",
        "signal_hb_units": "vendor_units",
    }
    signal.update(_whole_recording_features("signal_hbo", hbo, groups))
    signal.update(_whole_recording_features("signal_hbr", hbr, groups))

    marks = hbo_rec["marks"]
    windows = [] if ts.event_free else _bikom_block_windows(marks, ts)
    if windows:
        signal.update(_block_features("signal_hbo", hbo, time, windows, groups))
        signal.update(_block_features("signal_hbr", hbr, time, windows, groups))

    qc.update({
        "qc_feature_status": "ok", "qc_failure_reason": "",
        "qc_duration_sec": hbo_rec["duration_sec"], "qc_sampling_rate": hbo_rec["sfreq_hz"],
        "qc_channel_count": len(hbo_rec["channel_names"]),
        "qc_marker_count": len(marks),
        "qc_mark_labels": "|".join(hbo_rec["mark_labels"]),
        "qc_blocks_used": len(windows),
        "qc_timing_confidence": ts.timing_confidence,
        "qc_sensitivity_only": int(ts.sensitivity_only),
        "qc_region_mapping_status": "provider_network_partition",
        "qc_missing_value_rate": float(np.mean(~np.isfinite(hbo))),
        "qc_flat_channel_rate": float(np.mean(np.nanstd(hbo, axis=0) < 1e-12)),
        "qc_motion_proxy": float(np.nanmean(np.nanstd(np.diff(hbo, axis=0), axis=0))),
    })
    return signal, qc


def extract_fnirs_features(device: str, task: str,
                           config_path: str | Path = "configs/goal2_8/fnirs.yaml",
                           limit: int | None = None, n_jobs: int | None = None,
                           spec: ParadigmSpec | None = None) -> dict[str, Any]:
    from joblib import Parallel, delayed

    config = load_goal_config(config_path)
    spec = spec or load_paradigm_spec(config["paths"]["paradigm_spec"])
    ts = spec.fnirs(device, task)
    raw_root = project_path(config["paths"]["raw_data_dir"])
    task_dir = raw_root / ts.raw_dir

    split = cv_subjects(config)
    # Age drives the DPF. The column carries sentinels such as "[missing]" and a
    # few out-of-range values, so coerce and clip to the configured range.
    demo = config.get("demographics", {}) or {}
    age_min = float(demo.get("age_min", 9))
    age_max = float(demo.get("age_max", 20))
    default_age = float(config["fnirs"].get("default_age_years", 13.0))
    age_values = pd.to_numeric(split.get("age"), errors="coerce")
    age_values = age_values.where(age_values.between(age_min, age_max))
    ages = {str(l): (float(a) if pd.notna(a) else default_age)
            for l, a in zip(split["L_id"], age_values)}

    if device == "yiruid":
        found = collect_yiruid(task_dir)
        targets = [(l, found[l]) for l in map(str, split["L_id"]) if l in found]
        if limit:
            targets = targets[:limit]
        work = [(l, p, ts, ages.get(l, 13.0), spec) for l, p in targets]
        fn = _process_yiruid
    else:
        found = collect_bikom(task_dir)
        targets = [(l, found[l]) for l in map(str, split["L_id"]) if l in found]
        if limit:
            targets = targets[:limit]
        work = [(l, p, ts, spec) for l, p in targets]
        fn = _process_bikom

    jobs = int(n_jobs if n_jobs is not None else config.get("run", {}).get("n_jobs", 1))
    if jobs == 1:
        results = [fn(*item) for item in work]
    else:
        results = Parallel(n_jobs=jobs, backend="loky", verbose=5)(delayed(fn)(*item) for item in work)

    signal = pd.DataFrame([s for s, _ in results if s])
    qc = pd.DataFrame([q for _, q in results])

    keep = [c for c in ["L_id", "A_id", "primary_label_nonhealthy", "split_group", "split_role",
                        "is_locked_test", "cv_fold", "sex", "age", "grade", "grade_group",
                        "fnirs_device"] if c in split.columns]
    signal_out = split[keep].merge(signal, on="L_id", how="inner").sort_values("L_id").reset_index(drop=True)
    qc_out = split[keep].merge(qc, on="L_id", how="inner").sort_values("L_id").reset_index(drop=True)
    for frame, label in ((signal_out, "signal"), (qc_out, "qc")):
        if pd.to_numeric(frame.get("is_locked_test", 0), errors="coerce").fillna(0).astype(int).any():
            raise ValueError(f"Goal 2.8 fNIRS {label} features include pilot-holdout subjects.")

    out_dir = Path(ensure_output(f"{config['fnirs']['outputs_dir']}/.keep", config)).parent
    stem = f"{device}_{task}"
    signal_path = out_dir / f"{stem}_signal_features.csv"
    qc_path = out_dir / f"{stem}_qc_features.csv"
    signal_out.to_csv(signal_path, index=False)
    qc_out.to_csv(qc_path, index=False)

    manifest = {
        "device": device, "task": task,
        "feature_version": "goal2_8_fnirs_mbll_block_v1",
        "timing_confidence": ts.timing_confidence,
        "sensitivity_only": ts.sensitivity_only,
        "subjects_attempted": len(work),
        "subjects_signal": int(len(signal_out)), "subjects_qc": int(len(qc_out)),
        "signal_feature_columns": int(sum(1 for c in signal_out.columns if c.startswith("signal_"))),
        "block_reasons": qc.loc[qc["qc_feature_status"] != "ok", "qc_failure_reason"].value_counts().to_dict() if len(qc) else {},
        "signal_features": str(signal_path), "qc_features": str(qc_path),
    }
    (out_dir / f"{stem}_feature_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest
