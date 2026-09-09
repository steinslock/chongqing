"""Label-free validity checks for the eye-tracking modality.

Each check has an answer that physiology or the paradigm fixes in advance, so a
failure means the parse is wrong, not that the data carry no signal. Goal 2.7
declared EEG and fNIRS unusable on the strength of parses that no check like
this was ever run against.

Nothing here reads `primary_label_nonhealthy` or any other label.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

import numpy as np

from .spec import EyeParadigmSpec
from .drift import NO_DRIFT, DriftEstimate
from .stimuli import FaceStimulusBox, TargetTrack, saccade_trials
from .trace import GazeTrace, qixin_trace, tobii_trace

__all__ = [
    "GazeTrace",
    "free_viewing_aoi_shares",
    "free_viewing_on_face",
    "qixin_trace",
    "saccade_direction_agreement",
    "summarize",
    "target_following",
    "tobii_trace",
]

# Gaze inside the first 150 ms of a step still belongs to the previous target;
# saccade latency to a suddenly appearing target is about 200 ms.
SACCADE_ONSET_SKIP_MS = 150.0

# A trial window shorter than this cannot support a direction judgement.
MIN_TRIAL_WINDOW_MS = 300.0


def _correlation(a: np.ndarray, b: np.ndarray) -> float:
    mask = np.isfinite(a) & np.isfinite(b)
    if mask.sum() < 10:
        return float("nan")
    x = a[mask]
    y = b[mask]
    if np.std(x) < 1e-9 or np.std(y) < 1e-9:
        return float("nan")
    return float(np.corrcoef(x, y)[0, 1])


def free_viewing_on_face(
    trace: GazeTrace,
    segments: Sequence[tuple[str, float, float]],
    boxes: Mapping[str, FaceStimulusBox],
    drift: DriftEstimate = NO_DRIFT,
) -> dict[str, Any]:
    """Share of valid gaze falling inside the stimulus face box.

    The box covers a small part of the screen, so a correct parse puts dwell far
    above the box's area share. A result near the area share means the stimulus
    timing or the gaze coordinate frame is wrong.

    This check alone is not sufficient: the face box is symmetric about screen
    centre, so a vertical gaze offset passes it. Only `free_viewing_aoi_shares`
    exposes that.
    """

    inside = 0
    total = 0
    areas: list[float] = []
    per_trial: list[float] = []
    for media, start_ms, end_ms in segments:
        box = boxes.get(media)
        if box is None:
            continue
        piece = trace.window(start_ms, end_ms)
        finite = np.isfinite(piece.x) & np.isfinite(piece.y)
        if not finite.any():
            continue
        x, y = drift.apply(piece.x[finite], piece.y[finite])
        hit = box.contains(x, y)
        inside += int(hit.sum())
        total += int(finite.sum())
        areas.append(box.area_fraction)
        per_trial.append(float(hit.mean()))
    if total == 0:
        return {"on_face_fraction": float("nan"), "chance_fraction": float("nan"), "n_trials": 0}
    return {
        "on_face_fraction": inside / total,
        "chance_fraction": float(np.mean(areas)),
        "on_face_over_chance": (inside / total) / float(np.mean(areas)),
        "n_trials": len(per_trial),
        "on_face_trial_sd": float(np.std(per_trial)),
    }


def free_viewing_aoi_shares(
    trace: GazeTrace,
    segments: Sequence[tuple[str, float, float]],
    aois: Mapping[str, Any],
    drift: DriftEstimate = NO_DRIFT,
) -> dict[str, Any]:
    """Share of gaze in each stimulus region, pooled over the face trials.

    Face viewing puts far more gaze on the eye region than on the mouth region
    in every population studied, so eyes above mouth is a parse check, not a
    finding. The regions are disjoint and exhaustive, so the four shares sum
    to one.
    """

    totals = {name: 0 for name in ("eyes", "mouth", "face_other", "off_face")}
    usable = 0
    trials = 0
    for media, start_ms, end_ms in segments:
        aoi = aois.get(media)
        if aoi is None:
            continue
        piece = trace.window(start_ms, end_ms)
        finite = np.isfinite(piece.x) & np.isfinite(piece.y)
        if not finite.any():
            continue
        x, y = drift.apply(piece.x, piece.y)
        assigned = aoi.assign(x, y)
        for name in totals:
            totals[name] += int(assigned[name].sum())
        usable += int(finite.sum())
        trials += 1
    if usable == 0:
        return {f"aoi_{name}_share": float("nan") for name in totals} | {"aoi_n_trials": 0}
    out: dict[str, Any] = {f"aoi_{name}_share": totals[name] / usable for name in totals}
    out["aoi_n_trials"] = trials
    out["aoi_eyes_minus_mouth"] = out["aoi_eyes_share"] - out["aoi_mouth_share"]
    return out


def target_following(trace: GazeTrace, track: TargetTrack, start_ms: float, end_ms: float) -> dict[str, Any]:
    """Correlation between gaze and the video target over one block."""

    piece = trace.window(start_ms, end_ms)
    if piece.time_ms.size == 0:
        return {"corr_x": float("nan"), "corr_y": float("nan"), "n_valid": 0}
    relative = piece.time_ms - start_ms
    target_x, target_y = track.at_time_ms(relative)
    return {
        "corr_x": _correlation(piece.x, target_x),
        "corr_y": _correlation(piece.y, target_y),
        "n_valid": piece.n_valid,
    }


def saccade_direction_agreement(
    trace: GazeTrace,
    track: TargetTrack,
    start_ms: float,
    end_ms: float,
    antisaccade: bool,
) -> dict[str, Any]:
    """Whether gaze went towards the target (pro) or away from it (anti).

    Scored per trial as the sign of the mean horizontal gaze offset from screen
    centre, against the sign of the target offset.
    """

    correct = 0
    scored = 0
    offsets: list[float] = []
    for trial in saccade_trials(track):
        onset = start_ms + trial["onset_ms"] + SACCADE_ONSET_SKIP_MS
        # The recorded block runs a few tens of milliseconds short of the
        # video, so the final trial must be clamped rather than dropped.
        offset = min(start_ms + trial["offset_ms"], end_ms)
        if offset - onset < MIN_TRIAL_WINDOW_MS:
            continue
        piece = trace.window(onset, offset)
        finite = np.isfinite(piece.x)
        if finite.sum() < 5:
            continue
        gaze_offset = float(np.nanmean(piece.x[finite])) - 0.5
        expected = -trial["direction"] if antisaccade else trial["direction"]
        scored += 1
        offsets.append(gaze_offset * expected)
        correct += int(np.sign(gaze_offset) == expected)
    if scored == 0:
        return {"n_trials_scored": 0, "direction_correct_rate": float("nan"), "mean_signed_offset": float("nan")}
    return {
        "n_trials_scored": scored,
        "direction_correct_rate": correct / scored,
        "mean_signed_offset": float(np.mean(offsets)),
    }


def summarize(values: Sequence[float]) -> dict[str, float]:
    """Median and quartiles of a check across recordings, ignoring NaN."""

    array = np.array([value for value in values if value == value], dtype=float)
    if array.size == 0:
        return {"n": 0, "median": float("nan"), "q1": float("nan"), "q3": float("nan")}
    return {
        "n": int(array.size),
        "median": float(np.median(array)),
        "q1": float(np.percentile(array, 25)),
        "q3": float(np.percentile(array, 75)),
    }
