"""Fixation and saccade detection, one algorithm for all three devices.

Each vendor ships its own classifier: Tobii labels every sample with I-VT,
七鑫易维 writes an I-DT event table. Using both would make a feature of the same
name mean two different things, so this module applies a single dispersion-based
I-DT to the drift-corrected gaze of every device, and the vendor's own counts are
kept only as a QC cross-check.

I-DT rather than I-VT on purpose: a velocity threshold behaves differently at
60 Hz and 500 Hz, while a dispersion threshold does not.

The dispersion threshold is in normalised screen units. The paradigm document
gives the saccade targets at 6 and 12 degrees, which fixes the viewing geometry
(configs/goal2_10/eye_paradigm_spec.yaml, `viewing_geometry`), and the default
0.025 measures 1.078 deg horizontally. It measures 0.607 deg vertically, since
the same number is applied to a y axis normalised by screen height: the vertical
criterion is the stricter one. See known_defects/axis_anisotropy.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import numpy as np


@dataclass(frozen=True)
class Fixation:
    """One dispersion-defined fixation within a trial."""

    start_ms: float
    end_ms: float
    x: float
    y: float
    n_samples: int

    @property
    def duration_ms(self) -> float:
        return self.end_ms - self.start_ms


@dataclass(frozen=True)
class EventSeries:
    """Fixations and the inter-fixation transitions between them."""

    fixations: tuple[Fixation, ...]
    valid_fraction: float

    @property
    def count(self) -> int:
        return len(self.fixations)

    @property
    def durations_ms(self) -> np.ndarray:
        return np.array([fixation.duration_ms for fixation in self.fixations], dtype=float)

    def scanpath_length(self) -> float:
        """Summed distance between consecutive fixations, in screen widths."""
        if self.count < 2:
            return 0.0
        xs = np.array([fixation.x for fixation in self.fixations])
        ys = np.array([fixation.y for fixation in self.fixations])
        return float(np.sum(np.hypot(np.diff(xs), np.diff(ys))))

    def saccade_amplitudes(self) -> np.ndarray:
        if self.count < 2:
            return np.array([], dtype=float)
        xs = np.array([fixation.x for fixation in self.fixations])
        ys = np.array([fixation.y for fixation in self.fixations])
        return np.hypot(np.diff(xs), np.diff(ys))


def detect_fixations(
    time_ms: np.ndarray,
    x: np.ndarray,
    y: np.ndarray,
    dispersion: float,
    min_duration_ms: float,
    max_gap_ms: float,
) -> EventSeries:
    """I-DT over one trial's gaze.

    A candidate window grows while its bounding box stays within `dispersion`;
    when it no longer does, the window so far becomes a fixation if it lasted
    at least `min_duration_ms`. Samples with no gaze end the current window when
    the hole is longer than `max_gap_ms`, so a blink does not merge the
    fixations on either side of it.
    """

    finite = np.isfinite(x) & np.isfinite(y)
    valid_fraction = float(finite.mean()) if finite.size else 0.0
    if finite.sum() < 2:
        return EventSeries(fixations=(), valid_fraction=valid_fraction)

    fixations: list[Fixation] = []
    start = None
    x_min = x_max = y_min = y_max = 0.0
    last_valid_time = None

    def close(end_index: int) -> None:
        nonlocal start
        if start is None:
            return
        window = slice(start, end_index)
        window_finite = finite[window]
        if window_finite.sum() >= 2:
            # End the fixation at its last sample with gaze, not at whatever
            # sample happened to break the window; otherwise a blink inflates
            # the duration of the fixation before it.
            last = start + int(np.flatnonzero(window_finite)[-1])
            duration = float(time_ms[last] - time_ms[start])
            if duration >= min_duration_ms:
                fixations.append(
                    Fixation(
                        start_ms=float(time_ms[start]),
                        end_ms=float(time_ms[last]),
                        x=float(np.nanmean(x[window][window_finite])),
                        y=float(np.nanmean(y[window][window_finite])),
                        n_samples=int(window_finite.sum()),
                    )
                )
        start = None

    for index in range(time_ms.size):
        if not finite[index]:
            if last_valid_time is not None and time_ms[index] - last_valid_time > max_gap_ms:
                close(index)
                last_valid_time = None
            continue
        if start is None:
            start = index
            x_min = x_max = float(x[index])
            y_min = y_max = float(y[index])
            last_valid_time = float(time_ms[index])
            continue
        new_x_min = min(x_min, float(x[index]))
        new_x_max = max(x_max, float(x[index]))
        new_y_min = min(y_min, float(y[index]))
        new_y_max = max(y_max, float(y[index]))
        if (new_x_max - new_x_min) > dispersion or (new_y_max - new_y_min) > dispersion:
            close(index)
            start = index
            x_min = x_max = float(x[index])
            y_min = y_max = float(y[index])
        else:
            x_min, x_max, y_min, y_max = new_x_min, new_x_max, new_y_min, new_y_max
        last_valid_time = float(time_ms[index])
    close(time_ms.size)
    return EventSeries(fixations=tuple(fixations), valid_fraction=valid_fraction)


def detect_from_config(time_ms: np.ndarray, x: np.ndarray, y: np.ndarray, config: Mapping[str, Any]) -> EventSeries:
    return detect_fixations(
        time_ms,
        x,
        y,
        dispersion=float(config["dispersion_screen_fraction"]),
        min_duration_ms=float(config["min_fixation_ms"]),
        max_gap_ms=float(config["max_gap_ms"]),
    )


def first_fixation(events: EventSeries, after_ms: float = 0.0) -> Fixation | None:
    for fixation in events.fixations:
        if fixation.start_ms >= after_ms:
            return fixation
    return None


def bcea(x: np.ndarray, y: np.ndarray, probability: float = 0.68) -> float:
    """Bivariate contour ellipse area, the standard gaze dispersion measure.

    Returned in screen widths times screen heights, not deg^2 and not a square:
    x is normalised by width and y by height. `viewing_geometry` in the
    specification gives the conversion. See known_defects/axis_anisotropy.
    """

    finite = np.isfinite(x) & np.isfinite(y)
    if finite.sum() < 3:
        return float("nan")
    xs = x[finite]
    ys = y[finite]
    sx = float(np.std(xs, ddof=1))
    sy = float(np.std(ys, ddof=1))
    if sx <= 0 or sy <= 0:
        return 0.0
    rho = float(np.corrcoef(xs, ys)[0, 1])
    rho = 0.0 if rho != rho else rho
    k = -np.log(1.0 - probability)
    return float(2.0 * k * np.pi * sx * sy * np.sqrt(max(0.0, 1.0 - rho**2)))
