"""Orchestration for Goal 2.10 eye-tracking feature extraction.

The readiness audit already settled discovery, `A_id` resolution, deduplication
and QC, so this layer consumes `artifacts/goal2_10/readiness/recordings.csv`
rather than repeating any of it. Both stages therefore see the same take of
every recording.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

from ..goal2_7.config import ensure_output, load_goal_config, project_path
from ..goal2_7.io import cv_subjects
from . import aoi as eye_aoi
from . import drift as eye_drift
from . import features as eye_features
from . import qixin as qixin_io
from . import stimuli as eye_stimuli
from . import tobii as tobii_io
from . import trace as eye_trace
from .spec import EyeParadigmSpec, load_eye_spec

BASE_COLUMNS = [
    "L_id",
    "A_id",
    "primary_label_nonhealthy",
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

QC_PASSTHROUGH = [
    "valid_sample_fraction",
    "sampling_rate_hz",
    "clock_scale",
    "duration_agreement",
    "n_gaps",
    "longest_gap_ms",
    "gap_time_ms",
    "n_media_segments",
    "timeline_complete",
    "n_takes",
    "pupil_mean_mm",
    "pupil_sd_mm",
    "drift_dx",
    "drift_dy",
    "drift_dx_iqr",
    "drift_dy_iqr",
    "drift_n_crosses",
    "drift_applied",
    "average_calibration_accuracy_deg",
    "average_validation_accuracy_deg",
    "eyes_not_found_fraction",
]


def load_recordings(config: Mapping[str, Any], device: str, task: str) -> pd.DataFrame:
    """The audited, deduplicated recordings for one unit."""

    path = project_path(config["eye"]["recordings_table"])
    frame = pd.read_csv(path, low_memory=False)
    selected = frame[(frame["device"] == device) & (frame["task"] == task)].copy()
    return selected


def open_trace(spec: EyeParadigmSpec, row: Mapping[str, Any]):
    """Read one recording into a gaze trace plus its presentation timeline."""

    device = str(row["device"])
    if spec.device(device).kind == "qixin":
        duration = float(row.get("vendor_duration") or 0) or None
        trace = eye_trace.qixin_trace(str(row["path"]), duration)
        index = _asdata_index(spec, device)
        record = index.get(spec.task(str(row["task"])).qixin_dir, str(row["record_name"]))
        segments = (
            [(item.media, float(item.start_ms), float(item.end_ms)) for item in record.timeline] if record else []
        )
    else:
        recording = tobii_io.read_tobii_recording(str(row["path"]))
        trace = eye_trace.tobii_trace(recording, spec.screen)
        segments = [(item.media, item.start_ms, item.end_ms) for item in recording.stimulus_segments()]
    return trace, segments


_ASDATA_CACHE: dict[str, Any] = {}


def _asdata_index(spec: EyeParadigmSpec, device: str):
    if device not in _ASDATA_CACHE:
        from ..readiness import raw_data_dir

        _ASDATA_CACHE[device] = qixin_io.load_asdata(raw_data_dir() / spec.device(device).asdata)
    return _ASDATA_CACHE[device]


def _load_stimulus_products(config: Mapping[str, Any], spec: EyeParadigmSpec):
    from ..readiness import raw_data_dir

    stimulus_dir = raw_data_dir() / spec.device("qixin_120").root / spec.task("free_viewing").qixin_dir
    aois = {item.media: item for item in eye_aoi.build_stimulus_aois(spec, stimulus_dir, project_path("."))}
    cache = project_path(config["paths"]["stimuli_dir"])
    tracks = {}
    for name in ("prosaccade_formal", "antisaccade_formal", "pursuit"):
        payload = np.load(cache / f"target_{name}.npz")
        tracks[name] = eye_stimuli.TargetTrack(
            media=str(payload["media"]), fps=float(payload["fps"]), x=payload["x"], y=payload["y"]
        )
    return aois, tracks


def process_recording(
    row: Mapping[str, Any],
    spec: EyeParadigmSpec,
    aois: Mapping[str, Any],
    tracks: Mapping[str, Any],
) -> dict[str, Any]:
    """Trial table and subject features for one recording."""

    device = str(row["device"])
    task = str(row["task"])
    out: dict[str, Any] = {"A_id": row["a_id"], "device": device, "task": task, "status": "ok", "reason": ""}
    try:
        trace, segments = open_trace(spec, row)
    except Exception as error:  # noqa: BLE001 - a broken file is recorded, not fatal
        return {**out, "status": "read_failed", "reason": f"{type(error).__name__}: {error}"}

    velocity_permitted = spec.device(device).velocity_features_permitted
    try:
        if task == "free_viewing":
            drift = eye_drift.estimate_drift(trace, segments, spec.task(task).raw["drift_correction"])
            trials = eye_features.free_viewing_trials(trace, segments, aois, spec, drift)
            if trials.empty:
                return {**out, "status": "no_trials", "reason": "no face trial matched the timeline"}
            out["trials"] = trials.assign(A_id=row["a_id"]).to_dict("records")
            out["features"] = eye_features.free_viewing_subject_features(trials)
            out.update(drift.as_qc())
        elif task == "saccade":
            out["features"] = _saccade_features(trace, segments, spec, tracks, velocity_permitted)
        else:
            out["features"] = _pursuit_features(trace, segments, spec, tracks, velocity_permitted)
        if not out.get("features"):
            return {**out, "status": "no_features", "reason": "task blocks absent from the timeline"}
    except Exception as error:  # noqa: BLE001
        return {**out, "status": "feature_failed", "reason": f"{type(error).__name__}: {error}"}
    return out


def _saccade_features(trace, segments, spec: EyeParadigmSpec, tracks, velocity_permitted: bool) -> dict[str, float]:
    named = {media: (start, end) for media, start, end in segments}
    config = spec.task("saccade").raw["scoring"]
    out: dict[str, float] = {}
    scored: dict[str, list] = {}
    for media, track_name, anti, prefix in (
        ("前扫视-正式", "prosaccade_formal", False, "signal_pro_"),
        ("反扫视-正式", "antisaccade_formal", True, "signal_anti_"),
    ):
        if media not in named:
            continue
        start, end = named[media]
        results = eye_features.saccade_trials_scored(
            trace, tracks[track_name], start, end, anti, config
        )
        scored[prefix] = results
        out.update(eye_features.saccade_block_features(results, prefix, velocity_permitted))
    if "signal_pro_" in scored and "signal_anti_" in scored:
        # The inhibition cost is a within-subject contrast, so it cancels each
        # subject's baseline speed the way the valence contrast cancels identity.
        for measure in ("latency_median_ms", "direction_error_rate", "gain_median"):
            left = out.get(f"signal_anti_{measure}")
            right = out.get(f"signal_pro_{measure}")
            if left is not None and right is not None:
                out[f"signal_contrast_anti_minus_pro_{measure}"] = left - right
    return out


def _pursuit_features(trace, segments, spec: EyeParadigmSpec, tracks, velocity_permitted: bool) -> dict[str, float]:
    named = {media: (start, end) for media, start, end in segments}
    task = spec.task("smooth_pursuit")
    media = str(task.raw["blocks"][1]["media"])
    if media not in named:
        return {}
    start, end = named[media]
    return eye_features.pursuit_features(
        trace,
        tracks["pursuit"],
        start,
        end,
        task.raw["scoring"],
        velocity_permitted,
        blocks_spec=task.raw["pursuit_blocks"],
    )


def extract_unit(
    device: str,
    task: str,
    config_path: str | Path = "configs/goal2_10/features.yaml",
    limit: int | None = None,
    n_jobs: int | None = None,
    spec: EyeParadigmSpec | None = None,
) -> dict[str, Any]:
    """Build the signal and QC feature tables for one `device x task` unit."""

    from joblib import Parallel, delayed

    config = load_goal_config(config_path)
    spec = spec or load_eye_spec(config["paths"]["eye_spec"])
    out_dir = Path(ensure_output(f"{config['eye']['outputs_dir']}/.keep", config)).parent
    stem = f"{device}_{task}"

    recordings = load_recordings(config, device, task)
    split = cv_subjects(config)
    cv_ids = set(split["A_id"].astype(str))
    recordings = recordings[recordings["a_id"].astype(str).isin(cv_ids)].copy()

    threshold = float(config["eye"]["min_valid_sample_fraction"])
    valid = pd.to_numeric(recordings.get("valid_sample_fraction"), errors="coerce")
    excluded_quality = int((valid < threshold).sum())
    recordings = recordings[~(valid < threshold)].copy()
    if limit:
        recordings = recordings.head(limit)

    aois, tracks = _load_stimulus_products(config, spec)
    rows = recordings.to_dict("records")
    jobs = int(n_jobs if n_jobs is not None else config.get("run", {}).get("n_jobs", 1))
    if jobs == 1:
        results = [process_recording(row, spec, aois, tracks) for row in rows]
    else:
        results = Parallel(n_jobs=jobs, backend="loky", verbose=0)(
            delayed(process_recording)(row, spec, aois, tracks) for row in rows
        )

    signal_rows = [{"A_id": item["A_id"], **item["features"]} for item in results if item["status"] == "ok"]
    qc_rows = _qc_rows(results, recordings)
    signal = pd.DataFrame(signal_rows)
    qc = pd.DataFrame(qc_rows)

    keep = [column for column in BASE_COLUMNS if column in split.columns]
    signal_out = _merge(split[keep], signal)
    qc_out = _merge(split[keep], qc)
    for frame, label in ((signal_out, "signal"), (qc_out, "qc")):
        if pd.to_numeric(frame.get("is_locked_test", 0), errors="coerce").fillna(0).astype(int).any():
            raise ValueError(f"Goal 2.10 eye {label} features for {stem} include pilot-holdout subjects.")

    signal_path = out_dir / f"{stem}_signal_features.csv"
    qc_path = out_dir / f"{stem}_qc_features.csv"
    signal_out.to_csv(signal_path, index=False)
    qc_out.to_csv(qc_path, index=False)

    reliability_path = ""
    if task == "free_viewing":
        reliability = _free_viewing_reliability(results, config)
        if not reliability.empty:
            reliability_path = str(out_dir / f"{stem}_split_half_reliability.csv")
            reliability.to_csv(reliability_path, index=False)

    manifest = {
        "device": device,
        "task": task,
        "feature_version": config["eye"]["feature_version"],
        "status": "extracted",
        "subject_key": config["eye"]["subject_key"],
        "velocity_features_permitted": spec.device(device).velocity_features_permitted,
        "sampling_rate_hz": spec.device(device).sampling_rate_hz,
        "recordings_in_cv": int(len(rows) + excluded_quality),
        "excluded_low_valid_fraction": excluded_quality,
        "subjects_signal": int(len(signal_out)),
        "subjects_qc": int(len(qc_out)),
        "signal_feature_columns": int(sum(1 for column in signal_out.columns if column.startswith("signal_"))),
        "failure_reasons": _reason_counts(results),
        "signal_features": str(signal_path),
        "qc_features": str(qc_path),
        "split_half_reliability": reliability_path,
    }
    (out_dir / f"{stem}_feature_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return manifest


def _merge(base: pd.DataFrame, frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return base.head(0).copy()
    return base.merge(frame, on="A_id", how="inner").sort_values("A_id").reset_index(drop=True)


def _qc_rows(results: Sequence[Mapping[str, Any]], recordings: pd.DataFrame) -> list[dict[str, Any]]:
    audited = {str(row["a_id"]): row for row in recordings.to_dict("records")}
    rows: list[dict[str, Any]] = []
    for item in results:
        source = audited.get(str(item["A_id"]), {})
        row: dict[str, Any] = {
            "A_id": item["A_id"],
            "qc_feature_status": item["status"],
            "qc_failure_reason": item["reason"],
        }
        for column in QC_PASSTHROUGH:
            value = item.get(column, source.get(column))
            if value is not None and value == value:
                row[f"qc_{column}"] = value
        rows.append(row)
    return rows


def _reason_counts(results: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in results:
        if item["status"] != "ok":
            counts[item["status"]] = counts.get(item["status"], 0) + 1
    return counts


def _free_viewing_reliability(results: Sequence[Mapping[str, Any]], config: Mapping[str, Any]) -> pd.DataFrame:
    """Odd-even split-half reliability of every free-viewing feature."""

    odd_rows: list[dict[str, Any]] = []
    even_rows: list[dict[str, Any]] = []
    for item in results:
        if item["status"] != "ok" or "trials" not in item:
            continue
        trials = pd.DataFrame(item["trials"])
        for parity, sink in ((1, odd_rows), (0, even_rows)):
            half = trials[trials["trial"] % 2 == parity]
            if half.empty:
                continue
            sink.append({"A_id": item["A_id"], **eye_features.free_viewing_subject_features(half)})
    if not odd_rows or not even_rows:
        return pd.DataFrame()
    odd = pd.DataFrame(odd_rows).set_index("A_id").sort_index()
    even = pd.DataFrame(even_rows).set_index("A_id").sort_index()
    shared = odd.index.intersection(even.index)
    columns = [column for column in odd.columns if column.startswith("signal_")]
    return eye_features.split_half_reliability(
        odd.loc[shared],
        even.loc[shared],
        columns,
        min_subjects=int(config["eye"]["reliability"]["min_subjects"]),
    )
