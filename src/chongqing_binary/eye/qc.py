"""Recording-level quality control for eye tracking.

QC here records acquisition integrity only: how much of the recording the
tracker actually resolved, how well it was calibrated, and whether the
presentation timeline matches the specification. Task performance belongs to
the signal side, otherwise the `signal_qc vs qc` control tests nothing.
"""

from __future__ import annotations

from typing import Any, Mapping

import numpy as np
import pandas as pd

from . import qixin as qixin_io
from . import tobii as tobii_io
from .spec import EyeParadigmSpec

# A gap is a run of unusable samples at least this long. Chosen above the
# longest ordinary blink so that blinks are counted as blinks, not as tracking
# failures.
GAP_THRESHOLD_MS = 300.0


def _gap_summary(time_ms: np.ndarray, valid: np.ndarray) -> dict[str, float]:
    """Number and length of tracking gaps, in milliseconds."""

    if time_ms.size == 0:
        return {"n_gaps": 0, "longest_gap_ms": 0.0, "gap_time_ms": 0.0}
    invalid = ~valid
    gaps: list[float] = []
    start: int | None = None
    for position in range(invalid.size):
        if invalid[position] and start is None:
            start = position
        elif not invalid[position] and start is not None:
            gaps.append(float(time_ms[position - 1] - time_ms[start]))
            start = None
    if start is not None:
        gaps.append(float(time_ms[-1] - time_ms[start]))
    long_gaps = [gap for gap in gaps if gap >= GAP_THRESHOLD_MS]
    return {
        "n_gaps": len(long_gaps),
        "longest_gap_ms": max(gaps) if gaps else 0.0,
        "gap_time_ms": float(sum(long_gaps)),
    }


def _segment_conformance(
    spec: EyeParadigmSpec,
    device: str,
    task: str,
    observed: int,
    face_durations_ms: list[float] | None = None,
) -> dict[str, Any]:
    expected = spec.task(task).expected_media_segments(device)
    out: dict[str, Any] = {
        "n_media_segments": observed,
        "expected_media_segments": expected if expected is not None else "",
        "timeline_complete": int(expected is not None and observed == expected),
    }
    if face_durations_ms:
        nominal = float(spec.task(task).raw["trial_structure"][1]["duration_ms"])
        out["n_face_trials"] = len(face_durations_ms)
        out["face_duration_median_ms"] = float(np.median(face_durations_ms))
        out["face_duration_error_ms"] = float(np.median(face_durations_ms) - nominal)
    return out


def qixin_qc(
    spec: EyeParadigmSpec,
    row: Mapping[str, Any],
    record: qixin_io.QixinRecord | None,
) -> dict[str, Any]:
    """QC for one 七鑫易维 recording, read from the raw samples."""

    out: dict[str, Any] = {"qc_read_ok": 0}
    try:
        samples = qixin_io.read_basic_samples(row["path"])
    except (FileNotFoundError, ValueError, pd.errors.EmptyDataError) as error:
        out["qc_error"] = f"{type(error).__name__}: {error}"
        return out

    record_duration_ms = float(record.qc.get("duration") or 0) if record is not None else 0.0
    time_ms = qixin_io.aligned_time_ms(samples, record_duration_ms)
    clock_scale = qixin_io.clock_scale(samples, record_duration_ms)
    valid = qixin_io.valid_gaze_mask(samples)
    duration_ms = float(time_ms[-1] - time_ms[0]) if time_ms.size else 0.0
    pupil = np.nanmean(
        np.vstack(
            [
                samples["leftPupilDiameterMM"].to_numpy(dtype=float),
                samples["rightPupilDiameterMM"].to_numpy(dtype=float),
            ]
        ),
        axis=0,
    )
    blinks = (samples["leftBlink"].to_numpy() == 1) | (samples["rightBlink"].to_numpy() == 1)

    out.update(
        {
            "qc_read_ok": 1,
            "n_samples": int(time_ms.size),
            "duration_ms": duration_ms,
            "sampling_rate_hz": float(time_ms.size / (duration_ms / 1000.0)) if duration_ms > 0 else float("nan"),
            "valid_sample_fraction": float(valid.mean()) if valid.size else 0.0,
            "blink_sample_fraction": float(blinks.mean()) if blinks.size else 0.0,
            "pupil_mean_mm": float(np.nanmean(pupil[valid])) if valid.any() else float("nan"),
            "pupil_sd_mm": float(np.nanstd(pupil[valid])) if valid.any() else float("nan"),
            "clock_scale": clock_scale,
        }
    )
    out.update(_gap_summary(time_ms, valid))

    observed = record.n_media_segments if record is not None else 0
    face_durations = None
    if record is not None and row["task"] == "free_viewing":
        face_media = {stimulus.media for stimulus in spec.free_viewing_sequence}
        face_durations = [float(segment.duration_ms) for segment in record.timeline if segment.media in face_media]
    out.update(_segment_conformance(spec, str(row["device"]), str(row["task"]), observed, face_durations))
    if record is not None:
        for key, value in record.qc.items():
            out[f"vendor_{key}"] = value
    return out


def tobii_qc(spec: EyeParadigmSpec, row: Mapping[str, Any]) -> dict[str, Any]:
    """QC for one Tobii recording, read from the export."""

    out: dict[str, Any] = {"qc_read_ok": 0}
    try:
        recording = tobii_io.read_tobii_recording(row["path"])
    except (ValueError, KeyError, OSError) as error:
        out["qc_error"] = f"{type(error).__name__}: {error}"
        return out

    valid = recording.valid_mask()
    pupil = np.nanmean(np.vstack([recording.pupil_left, recording.pupil_right]), axis=0)
    segments = recording.stimulus_segments()

    out.update(
        {
            "qc_read_ok": 1,
            "n_samples": recording.n_samples,
            "duration_ms": recording.duration_ms,
            "sampling_rate_hz": recording.sampling_rate_hz,
            "duration_agreement": recording.duration_agreement,
            "valid_sample_fraction": float(valid.mean()) if valid.size else 0.0,
            "eyes_not_found_fraction": float((recording.movement == tobii_io.MOVEMENT_EYES_NOT_FOUND).mean()),
            "unclassified_fraction": float((recording.movement == tobii_io.MOVEMENT_UNCLASSIFIED).mean()),
            "pupil_mean_mm": float(np.nanmean(pupil[valid])) if valid.any() else float("nan"),
            "pupil_sd_mm": float(np.nanstd(pupil[valid])) if valid.any() else float("nan"),
            "timeline_name": recording.timeline_name,
            "timeline_name_matches": int(recording.timeline_name == spec.task(str(row["task"])).tobii_timeline_name),
        }
    )
    out.update(_gap_summary(recording.time_ms, valid))
    for key in (
        "Average calibration accuracy (degrees)",
        "Average calibration precision SD (degrees)",
        "Average validation accuracy (degrees)",
        "Average validation precision SD (degrees)",
    ):
        out[_metadata_key(key)] = recording.metadata.get(key)

    face_durations = None
    if row["task"] == "free_viewing":
        face_media = {stimulus.media for stimulus in spec.free_viewing_sequence}
        face_durations = [float(segment.duration_ms) for segment in segments if segment.media in face_media]
    out.update(_segment_conformance(spec, str(row["device"]), str(row["task"]), len(segments), face_durations))
    return out


def _metadata_key(name: str) -> str:
    return (
        name.lower()
        .replace(" (degrees)", "_deg")
        .replace(" ", "_")
    )
