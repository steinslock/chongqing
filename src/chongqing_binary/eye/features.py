"""Subject-level eye-tracking features for Goal 2.10.

Three rules shape everything here.

The free-viewing paradigm shows one face at a time, so its valence effect is a
contrast **between trials**, not the competitive attentional bias most of the
literature reports. Contrast features are named `contrast_` for that reason and
absolute per-valence features are kept beside them, because difference scores
are the part of this literature whose reliability collapses.

Gaze is drift-corrected before any region feature; without it the
eye-versus-mouth contrast reverses on two of the three devices and becomes a
site shortcut.

Velocity-derived features are gated on the device. At 60 Hz a saccade spans one
or two samples, so a peak velocity from it is noise with a number attached.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import pandas as pd

from .aoi import REGION_ORDER, StimulusAoi
from .drift import NO_DRIFT, DriftEstimate
from .events import EventSeries, bcea, detect_from_config, first_fixation
from .spec import VALENCES, EyeParadigmSpec

# Measures aggregated per valence and window in free viewing.
TRIAL_MEASURES = (
    "eyes_share",
    "mouth_share",
    "face_other_share",
    "off_face_share",
    "n_fixations",
    "mean_fixation_ms",
    "scanpath",
    "bcea",
    "pupil_delta",
)

# The subset that also enters a between-valence contrast. Region shares that are
# complements of each other would produce redundant contrasts, so only one of
# `off_face_share` / `face_other_share` is carried.
CONTRAST_MEASURES = (
    "eyes_share",
    "mouth_share",
    "off_face_share",
    "n_fixations",
    "mean_fixation_ms",
    "scanpath",
    "pupil_delta",
)

CONTRASTS = (("sad", "neutral"), ("happy", "neutral"), ("sad", "happy"))


def _finite(values: Iterable[float]) -> np.ndarray:
    array = np.array(list(values), dtype=float)
    return array[np.isfinite(array)]


def _mean(values: Iterable[float]) -> float:
    array = _finite(values)
    return float(array.mean()) if array.size else float("nan")


def _sd(values: Iterable[float]) -> float:
    array = _finite(values)
    return float(array.std(ddof=1)) if array.size > 1 else float("nan")


def _median(values: Iterable[float]) -> float:
    array = _finite(values)
    return float(np.median(array)) if array.size else float("nan")


def _iqr(values: Iterable[float]) -> float:
    array = _finite(values)
    return float(np.percentile(array, 75) - np.percentile(array, 25)) if array.size > 1 else float("nan")


# --------------------------------------------------------------------------
# Free viewing
# --------------------------------------------------------------------------


def free_viewing_trials(
    trace,
    segments: Sequence[tuple[str, float, float]],
    aois: Mapping[str, StimulusAoi],
    spec: EyeParadigmSpec,
    drift: DriftEstimate = NO_DRIFT,
) -> pd.DataFrame:
    """One row per face trial per analysis window."""

    task = spec.task("free_viewing")
    windows = task.raw["analysis_windows"]
    detector = task.raw["events"]
    pupil_cfg = task.raw["pupil"]
    prefix = str(task.raw["drift_correction"]["fixation_media_prefix"])

    ordered = sorted(segments, key=lambda item: item[1])
    baseline_for: dict[int, tuple[float, float]] = {}
    last_cross: tuple[float, float] | None = None
    face_positions: list[tuple[int, str, float, float]] = []
    for index, (media, start_ms, end_ms) in enumerate(ordered):
        if str(media).startswith(prefix):
            last_cross = (start_ms, end_ms)
        elif media in aois:
            face_positions.append((index, media, start_ms, end_ms))
            if last_cross is not None:
                baseline_for[index] = last_cross

    rows: list[dict[str, Any]] = []
    for index, media, start_ms, end_ms in face_positions:
        aoi = aois[media]
        baseline = _pupil_baseline(trace, baseline_for.get(index), pupil_cfg)
        for window_name, (offset_start, offset_end) in (
            ("early", windows["early_ms"]),
            ("late", windows["late_ms"]),
        ):
            piece = trace.window(start_ms + float(offset_start), min(start_ms + float(offset_end), end_ms))
            x, y = drift.apply(piece.x, piece.y)
            shares = aoi.shares(x, y)
            events = detect_from_config(piece.time_ms, x, y, detector)
            pupil = _pupil_mean(piece)
            row: dict[str, Any] = {
                "trial": aoi.order,
                "media": media,
                "valence": aoi.valence,
                "stimulus_sex": aoi.sex,
                "window": window_name,
                "n_samples": int(piece.time_ms.size),
                "valid_fraction": events.valid_fraction,
                "n_fixations": float(events.count),
                "mean_fixation_ms": _mean(events.durations_ms),
                "scanpath": events.scanpath_length(),
                "bcea": bcea(x, y),
                "pupil_delta": pupil - baseline if np.isfinite(baseline) else float("nan"),
            }
            row.update({f"{name}_share": shares[name] for name in REGION_ORDER})
            if window_name == "early":
                first = first_fixation(events)
                row["first_fixation_ms"] = (first.start_ms - (start_ms + float(offset_start))) if first else float("nan")
                row["first_fixation_on_eyes"] = (
                    float(bool(aoi.eyes.contains(np.array([first.x]), np.array([first.y]))[0])) if first else float("nan")
                )
            rows.append(row)
    return pd.DataFrame(rows)


def _pupil_baseline(trace, cross: tuple[float, float] | None, config: Mapping[str, Any]) -> float:
    """Pupil over the tail of the fixation cross that precedes a trial."""

    if cross is None:
        return float("nan")
    start_ms, end_ms = cross
    piece = trace.window(max(start_ms, end_ms - float(config["baseline_ms"])), end_ms)
    return _pupil_mean(piece)


def _pupil_mean(piece) -> float:
    pupil = getattr(piece, "pupil", None)
    if pupil is None:
        return float("nan")
    finite = np.isfinite(pupil)
    return float(np.median(pupil[finite])) if finite.any() else float("nan")


def free_viewing_subject_features(trials: pd.DataFrame, prefix: str = "signal_") -> dict[str, float]:
    """Aggregate one subject's free-viewing trials into features."""

    out: dict[str, float] = {}
    if trials.empty:
        return out

    per_valence: dict[tuple[str, str, str], float] = {}
    for window in ("early", "late"):
        window_rows = trials[trials["window"] == window]
        for valence in VALENCES:
            subset = window_rows[window_rows["valence"] == valence]
            for measure in TRIAL_MEASURES:
                value = _mean(subset[measure]) if measure in subset else float("nan")
                per_valence[(window, valence, measure)] = value
                out[f"{prefix}{window}_{valence}_{measure}"] = value
            # Within-valence stability across the 12 trials.
            for measure in ("eyes_share", "pupil_delta"):
                out[f"{prefix}{window}_{valence}_{measure}_sd"] = _sd(subset[measure]) if measure in subset else float("nan")

        for high, low in CONTRASTS:
            for measure in CONTRAST_MEASURES:
                left = per_valence[(window, high, measure)]
                right = per_valence[(window, low, measure)]
                out[f"{prefix}contrast_{window}_{high}_minus_{low}_{measure}"] = left - right

    early = trials[trials["window"] == "early"]
    for valence in VALENCES:
        subset = early[early["valence"] == valence]
        out[f"{prefix}first_fixation_ms_{valence}"] = _mean(subset.get("first_fixation_ms", pd.Series(dtype=float)))
        out[f"{prefix}first_fixation_on_eyes_{valence}"] = _mean(
            subset.get("first_fixation_on_eyes", pd.Series(dtype=float))
        )
    for high, low in CONTRASTS[:2]:
        for measure in ("first_fixation_ms", "first_fixation_on_eyes"):
            out[f"{prefix}contrast_{high}_minus_{low}_{measure}"] = (
                out[f"{prefix}{measure}_{high}"] - out[f"{prefix}{measure}_{low}"]
            )

    # Trial index and valence are confounded by the fixed presentation order, so
    # a linear trend over trials is reported beside every valence effect.
    late = trials[trials["window"] == "late"]
    for measure in ("eyes_share", "n_fixations", "pupil_delta"):
        out[f"{prefix}trend_{measure}"] = _slope(late["trial"], late[measure]) if measure in late else float("nan")
    return out


def _slope(index: pd.Series, values: pd.Series) -> float:
    x = np.asarray(index, dtype=float)
    y = np.asarray(values, dtype=float)
    mask = np.isfinite(x) & np.isfinite(y)
    if mask.sum() < 3:
        return float("nan")
    return float(np.polyfit(x[mask], y[mask], 1)[0])


# --------------------------------------------------------------------------
# Saccade
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class SaccadeTrialResult:
    trial: int
    amplitude: float
    direction: int
    latency_ms: float
    responded: bool
    correct: bool
    corrected: bool
    correction_ms: float
    gain: float
    peak_velocity: float


def saccade_trials_scored(
    trace,
    track,
    block_start_ms: float,
    block_end_ms: float,
    antisaccade: bool,
    config: Mapping[str, Any],
    drift: DriftEstimate = NO_DRIFT,
) -> list[SaccadeTrialResult]:
    """Score each trial of one formal block against the decoded target."""

    from .stimuli import saccade_trials

    threshold = float(config["response_offset_screen_fraction"])
    min_latency = float(config["min_latency_ms"])
    max_latency = float(config["max_latency_ms"])

    results: list[SaccadeTrialResult] = []
    for trial in saccade_trials(track):
        onset = block_start_ms + trial["onset_ms"]
        window_end = min(block_start_ms + trial["offset_ms"], block_end_ms)
        if window_end - onset < min_latency:
            continue
        piece = trace.window(onset, window_end)
        x, _ = drift.apply(piece.x, piece.y)
        times = piece.time_ms - onset
        offset = x - 0.5
        expected = -trial["direction"] if antisaccade else trial["direction"]

        moved = np.flatnonzero(np.isfinite(offset) & (np.abs(offset) >= threshold) & (times >= min_latency))
        if moved.size == 0 or times[moved[0]] > max_latency:
            results.append(
                SaccadeTrialResult(
                    trial=int(trial["trial"]), amplitude=float(trial["amplitude"]), direction=int(trial["direction"]),
                    latency_ms=float("nan"), responded=False, correct=False, corrected=False,
                    correction_ms=float("nan"), gain=float("nan"), peak_velocity=float("nan"),
                )
            )
            continue

        first = int(moved[0])
        latency = float(times[first])
        went = int(np.sign(offset[first]))
        correct = went == expected
        corrected = False
        correction_ms = float("nan")
        if not correct:
            later = np.flatnonzero(
                np.isfinite(offset) & (np.abs(offset) >= threshold) & (np.sign(offset) == expected) & (times > latency)
            )
            if later.size:
                corrected = True
                correction_ms = float(times[int(later[0])] - latency)

        target_offset = abs(trial["target_x"] - 0.5)
        sustained = np.isfinite(offset) & (times >= latency)
        gain = float(np.nanmedian(np.abs(offset[sustained])) / target_offset) if sustained.any() and target_offset else float("nan")
        results.append(
            SaccadeTrialResult(
                trial=int(trial["trial"]), amplitude=float(trial["amplitude"]), direction=int(trial["direction"]),
                latency_ms=latency, responded=True, correct=correct, corrected=corrected,
                correction_ms=correction_ms, gain=gain,
                peak_velocity=_peak_velocity(times, x, latency),
            )
        )
    return results


def _peak_velocity(times: np.ndarray, x: np.ndarray, latency_ms: float) -> float:
    """Peak horizontal speed around the primary saccade, screen widths per second."""

    window = np.isfinite(x) & (times >= latency_ms - 100.0) & (times <= latency_ms + 100.0)
    if window.sum() < 3:
        return float("nan")
    t = times[window] / 1000.0
    values = x[window]
    velocity = np.diff(values) / np.diff(t)
    velocity = velocity[np.isfinite(velocity)]
    return float(np.max(np.abs(velocity))) if velocity.size else float("nan")


def saccade_block_features(results: Sequence[SaccadeTrialResult], prefix: str, velocity_permitted: bool) -> dict[str, float]:
    out: dict[str, float] = {}
    if not results:
        return out
    responded = [item for item in results if item.responded]
    out[f"{prefix}n_trials"] = float(len(results))
    out[f"{prefix}response_rate"] = float(len(responded)) / len(results)
    correct = [item for item in responded if item.correct]
    errors = [item for item in responded if not item.correct]
    out[f"{prefix}direction_error_rate"] = (float(len(errors)) / len(responded)) if responded else float("nan")
    out[f"{prefix}latency_median_ms"] = _median(item.latency_ms for item in correct)
    out[f"{prefix}latency_iqr_ms"] = _iqr(item.latency_ms for item in correct)
    out[f"{prefix}gain_median"] = _median(item.gain for item in correct)
    out[f"{prefix}corrected_error_rate"] = (
        float(sum(1 for item in errors if item.corrected)) / len(errors) if errors else float("nan")
    )
    out[f"{prefix}correction_latency_ms"] = _median(item.correction_ms for item in errors if item.corrected)
    for label, amplitudes in (("small", lambda value: value < 0.2), ("large", lambda value: value >= 0.2)):
        subset = [item for item in responded if amplitudes(item.amplitude)]
        out[f"{prefix}{label}_latency_median_ms"] = _median(item.latency_ms for item in subset if item.correct)
        out[f"{prefix}{label}_direction_error_rate"] = (
            float(sum(1 for item in subset if not item.correct)) / len(subset) if subset else float("nan")
        )
    if velocity_permitted:
        out[f"{prefix}peak_velocity_median"] = _median(item.peak_velocity for item in correct)
    return out


# --------------------------------------------------------------------------
# Smooth pursuit
# --------------------------------------------------------------------------


def pursuit_features(
    trace,
    track,
    start_ms: float,
    end_ms: float,
    config: Mapping[str, Any],
    velocity_permitted: bool,
    prefix: str = "signal_",
    drift: DriftEstimate = NO_DRIFT,
    blocks_spec: Mapping[str, Any] | None = None,
) -> dict[str, float]:
    """Pursuit measures per condition, plus the contrasts between conditions.

    The task is six 21 s sinusoidal blocks, three conditions repeated twice,
    not one continuous sweep. Pursuit gain depends strongly on target
    frequency, so pooling the conditions would average a known effect away.
    """

    from .stimuli import pursuit_blocks

    out: dict[str, float] = {}
    blocks = pursuit_blocks(track)
    if not blocks:
        return out

    settling_ms = float(blocks_spec["settling_ms"]) if blocks_spec else 1000.0
    conditions: dict[str, list[int]] = (
        {name: list(entry["blocks"]) for name, entry in blocks_spec["conditions"].items()}
        if blocks_spec
        else {"all": [item["block"] for item in blocks]}
    )

    per_block: dict[int, dict[str, float]] = {}
    for block in blocks:
        measures = _pursuit_block(
            trace, track, start_ms, end_ms, block, settling_ms, config, velocity_permitted, drift
        )
        if measures:
            per_block[int(block["block"])] = measures

    for name, members in conditions.items():
        present = [per_block[index] for index in members if index in per_block]
        if not present:
            continue
        for measure in present[0]:
            out[f"{prefix}pursuit_{name}_{measure}"] = _mean(item.get(measure, float("nan")) for item in present)
        # Two presentations of the same condition give a within-session repeat
        # difference for free, without an odd-even split.
        if len(present) == 2:
            for measure in ("corr_x", "position_gain_x", "rmse"):
                left = present[0].get(measure, float("nan"))
                right = present[1].get(measure, float("nan"))
                out[f"{prefix}pursuit_{name}_{measure}_repeat_diff"] = abs(left - right)

    if "lissajous_fast" in conditions and "lissajous_slow" in conditions:
        # Same amplitude, exactly double the frequency, so this isolates how
        # pursuit degrades with target speed and cancels the subject's baseline.
        for measure in (
            "corr_x",
            "position_gain_x",
            "rmse",
            "catch_up_rate_hz",
            "smooth_fraction",
            "velocity_gain",
        ):
            fast = out.get(f"{prefix}pursuit_lissajous_fast_{measure}")
            slow = out.get(f"{prefix}pursuit_lissajous_slow_{measure}")
            if fast is not None and slow is not None:
                out[f"{prefix}contrast_pursuit_fast_minus_slow_{measure}"] = fast - slow

    valid = [item["valid_fraction"] for item in per_block.values() if "valid_fraction" in item]
    out[f"{prefix}pursuit_valid_fraction"] = _mean(valid)
    out[f"{prefix}pursuit_blocks_used"] = float(len(per_block))
    return out


def _pursuit_block(
    trace,
    track,
    start_ms: float,
    end_ms: float,
    block: Mapping[str, Any],
    settling_ms: float,
    config: Mapping[str, Any],
    velocity_permitted: bool,
    drift: DriftEstimate,
) -> dict[str, float]:
    """Tracking measures over one pursuit block, after its stationary opening."""

    block_start = start_ms + float(block["start_ms"]) + settling_ms
    block_end = min(start_ms + float(block["end_ms"]), end_ms)
    if block_end - block_start < 5000.0:
        return {}
    piece = trace.window(block_start, block_end)
    x, y = drift.apply(piece.x, piece.y)
    relative = piece.time_ms - start_ms
    target_x, target_y = track.at_time_ms(relative)
    mask = np.isfinite(x) & np.isfinite(y) & np.isfinite(target_x) & np.isfinite(target_y)
    measures: dict[str, float] = {"valid_fraction": float(mask.mean()) if mask.size else float("nan")}
    if mask.sum() < 100:
        return measures

    gx, gy = x[mask], y[mask]
    tx, ty = target_x[mask], target_y[mask]
    measures["corr_x"] = float(np.corrcoef(gx, tx)[0, 1]) if np.std(tx) > 1e-9 else float("nan")
    measures["corr_y"] = float(np.corrcoef(gy, ty)[0, 1]) if np.std(ty) > 1e-9 else float("nan")
    measures["position_gain_x"] = float(np.polyfit(tx, gx, 1)[0]) if np.std(tx) > 1e-9 else float("nan")
    measures["position_gain_y"] = float(np.polyfit(ty, gy, 1)[0]) if np.std(ty) > 1e-9 else float("nan")
    measures["rmse"] = float(np.sqrt(np.mean((gx - tx) ** 2 + (gy - ty) ** 2)))
    measures["rmse_x"] = float(np.sqrt(np.mean((gx - tx) ** 2)))

    if velocity_permitted:
        gain = _velocity_gain(piece.time_ms[mask], gx, tx, config)
        if gain == gain:
            measures["velocity_gain"] = gain
        measures.update(_catch_up(piece.time_ms[mask], gx, gy, tx, ty, config))
    return measures


def _catch_up(
    time_ms: np.ndarray,
    gaze_x: np.ndarray,
    gaze_y: np.ndarray,
    target_x: np.ndarray,
    target_y: np.ndarray,
    config: Mapping[str, Any],
) -> dict[str, float]:
    """Catch-up saccade rate and the share of time spent genuinely pursuing.

    A saccade during pursuit is a run of samples whose eye speed exceeds the
    target's by a clear margin. Counting inter-fixation transitions instead
    does not work here: during pursuit the eye moves smoothly, so a dispersion
    detector chops that motion at its threshold and its rate tracks eye speed
    rather than saccades.
    """

    from scipy.signal import savgol_filter

    if time_ms.size < 20:
        return {}
    seconds = time_ms / 1000.0
    step = float(np.median(np.diff(seconds)))
    if not np.isfinite(step) or step <= 0:
        return {}
    window = int(round(float(config["velocity_smoothing_ms"]) / 1000.0 / step)) | 1
    if window < 5 or window >= gaze_x.size:
        return {}

    eye_speed = np.hypot(
        savgol_filter(gaze_x, window, 2, deriv=1, delta=step, mode="interp"),
        savgol_filter(gaze_y, window, 2, deriv=1, delta=step, mode="interp"),
    )
    target_speed = np.hypot(
        savgol_filter(target_x, window, 2, deriv=1, delta=step, mode="interp"),
        savgol_filter(target_y, window, 2, deriv=1, delta=step, mode="interp"),
    )
    residual = eye_speed - target_speed
    saccadic = residual > float(config["catch_up_residual_speed"])

    minimum_samples = max(1, int(round(float(config["catch_up_min_duration_ms"]) / 1000.0 / step)))
    starts = np.flatnonzero(np.diff(np.concatenate([[0], saccadic.view(np.int8), [0]])) == 1)
    ends = np.flatnonzero(np.diff(np.concatenate([[0], saccadic.view(np.int8), [0]])) == -1)
    count = int(np.sum((ends - starts) >= minimum_samples))
    duration_s = max(1e-9, float(seconds[-1] - seconds[0]))
    return {
        "catch_up_rate_hz": count / duration_s,
        "smooth_fraction": float(np.mean(~saccadic)),
    }


def _velocity_gain(time_ms: np.ndarray, gaze: np.ndarray, target: np.ndarray, config: Mapping[str, Any]) -> float:
    """Median eye-to-target velocity ratio over the non-saccadic samples.

    A plain sample difference is dominated by tracker noise, and the more so
    the higher the sampling rate: at 500 Hz it returns about 0.21 where the
    physiological range is 0.7 to 1.0. A Savitzky-Golay first derivative over a
    window set from the stimulus dynamics recovers the range. The same filter
    is applied to the target, so first-order attenuation cancels in the ratio.

    This measure stays sampling-rate dependent even so, and the specification
    records the measurements that show it. It is device-specific and must never
    be pooled across devices.
    """

    from scipy.signal import savgol_filter

    if time_ms.size < 20:
        return float("nan")
    seconds = time_ms / 1000.0
    step = float(np.median(np.diff(seconds)))
    if not np.isfinite(step) or step <= 0:
        return float("nan")
    window = int(round(float(config["velocity_smoothing_ms"]) / 1000.0 / step)) | 1
    if window < 5 or window >= gaze.size:
        return float("nan")

    gaze_velocity = savgol_filter(gaze, window, 2, deriv=1, delta=step, mode="interp")
    target_velocity = savgol_filter(target, window, 2, deriv=1, delta=step, mode="interp")
    max_ratio = float(config["velocity_max_ratio"])
    floor = float(config["velocity_min_target_speed"])
    usable = (
        np.isfinite(gaze_velocity)
        & np.isfinite(target_velocity)
        & (np.abs(target_velocity) > floor)
        & (np.abs(gaze_velocity) < max_ratio * np.abs(target_velocity) + 0.05)
    )
    if usable.sum() < 100:
        return float("nan")
    return float(np.median(gaze_velocity[usable] / target_velocity[usable]))


# --------------------------------------------------------------------------
# Split-half reliability
# --------------------------------------------------------------------------


def split_half_reliability(
    odd: pd.DataFrame, even: pd.DataFrame, columns: Sequence[str], min_subjects: int = 20
) -> pd.DataFrame:
    """Spearman-Brown corrected odd-even correlation for each feature.

    Difference scores are the part of this literature whose reliability
    collapses, so every feature carries its own estimate rather than the set
    being assumed adequate.
    """

    rows: list[dict[str, Any]] = []
    for column in columns:
        if column not in odd or column not in even:
            continue
        left = pd.to_numeric(odd[column], errors="coerce").to_numpy(dtype=float)
        right = pd.to_numeric(even[column], errors="coerce").to_numpy(dtype=float)
        mask = np.isfinite(left) & np.isfinite(right)
        if mask.sum() < min_subjects or np.std(left[mask]) < 1e-12 or np.std(right[mask]) < 1e-12:
            rows.append({"feature": column, "n": int(mask.sum()), "r_half": float("nan"), "spearman_brown": float("nan")})
            continue
        r = float(np.corrcoef(left[mask], right[mask])[0, 1])
        corrected = (2.0 * r) / (1.0 + r) if r > -1.0 else float("nan")
        rows.append(
            {
                "feature": column,
                "n": int(mask.sum()),
                "r_half": r,
                "spearman_brown": min(1.0, corrected) if corrected == corrected else float("nan"),
            }
        )
    return pd.DataFrame(rows)
