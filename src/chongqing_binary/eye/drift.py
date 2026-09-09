"""Per-recording gaze drift correction from the paradigm's own fixation cross.

All three trackers report gaze below the true fixation point by a
device-dependent amount. The eye and mouth bands on a face stimulus are each
about a tenth of screen height, so an offset of a few hundredths reverses the
eye-versus-mouth contrast. Because device is collinear with acquisition site in
this dataset, an uncorrected offset would enter a model as a site shortcut.

The free-viewing paradigm shows a 1 s cross at screen centre before every
trial, which gives a per-recording offset that uses no label and no trial-level
variance.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import numpy as np

SCREEN_CENTRE = (0.5, 0.5)


@dataclass(frozen=True)
class DriftEstimate:
    """A recording's gaze offset, and how well determined it is."""

    dx: float
    dy: float
    n_crosses: int
    dx_iqr: float
    dy_iqr: float
    usable: bool

    def apply(self, x: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        if not self.usable:
            return x, y
        return x - self.dx, y - self.dy

    def as_qc(self) -> dict[str, Any]:
        return {
            "drift_dx": self.dx,
            "drift_dy": self.dy,
            "drift_n_crosses": self.n_crosses,
            "drift_dx_iqr": self.dx_iqr,
            "drift_dy_iqr": self.dy_iqr,
            "drift_applied": int(self.usable),
        }


NO_DRIFT = DriftEstimate(0.0, 0.0, 0, float("nan"), float("nan"), False)


def estimate_drift(
    trace,
    segments: Sequence[tuple[str, float, float]],
    config: Mapping[str, Any],
) -> DriftEstimate:
    """Median gaze over a recording's fixation crosses, minus screen centre."""

    prefix = str(config["fixation_media_prefix"])
    skip_ms = float(config["skip_ms"])
    min_samples = int(config["min_samples_per_cross"])
    min_crosses = int(config["min_crosses"])

    xs: list[float] = []
    ys: list[float] = []
    for media, start_ms, end_ms in segments:
        if not str(media).startswith(prefix):
            continue
        # The eye is still arriving during the first samples of a cross.
        piece = trace.window(start_ms + skip_ms, end_ms)
        finite = np.isfinite(piece.x) & np.isfinite(piece.y)
        if int(finite.sum()) < min_samples:
            continue
        xs.append(float(np.nanmedian(piece.x[finite])))
        ys.append(float(np.nanmedian(piece.y[finite])))

    if len(xs) < min_crosses:
        return DriftEstimate(0.0, 0.0, len(xs), float("nan"), float("nan"), False)

    x_array = np.array(xs)
    y_array = np.array(ys)
    return DriftEstimate(
        dx=float(np.median(x_array) - SCREEN_CENTRE[0]),
        dy=float(np.median(y_array) - SCREEN_CENTRE[1]),
        n_crosses=len(xs),
        dx_iqr=float(np.percentile(x_array, 75) - np.percentile(x_array, 25)),
        dy_iqr=float(np.percentile(y_array, 75) - np.percentile(y_array, 25)),
        usable=True,
    )
