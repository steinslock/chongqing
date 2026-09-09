"""One device-independent gaze trace, on the presentation clock.

Both the readiness checks and the feature layer work on this, so the
device-specific reading happens once here: the 七鑫易维 sample clock is mapped
onto the presentation clock, Tobii pixels are normalised by screen size, and
pupil diameter is carried in millimetres from whichever columns the device
supplies.
"""

from __future__ import annotations

import numpy as np

from . import qixin as qixin_io
from . import tobii as tobii_io


class GazeTrace:
    """Normalised gaze and pupil over one recording."""

    def __init__(
        self,
        time_ms: np.ndarray,
        x: np.ndarray,
        y: np.ndarray,
        valid: np.ndarray,
        pupil: np.ndarray | None = None,
    ) -> None:
        self.time_ms = time_ms
        self.x = np.where(valid, x, np.nan)
        self.y = np.where(valid, y, np.nan)
        self.valid = valid
        self.pupil = np.where(valid, pupil, np.nan) if pupil is not None else np.full(time_ms.shape, np.nan)

    def window(self, start_ms: float, end_ms: float) -> "GazeTrace":
        mask = (self.time_ms >= start_ms) & (self.time_ms <= end_ms)
        return GazeTrace(self.time_ms[mask], self.x[mask], self.y[mask], self.valid[mask], self.pupil[mask])

    @property
    def n_valid(self) -> int:
        return int(np.isfinite(self.x).sum())


def _mean_pupil(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    """Mean of whichever eyes reported a diameter, without warning on neither."""

    stacked = np.vstack([left, right])
    finite = np.isfinite(stacked)
    count = finite.sum(axis=0)
    total = np.where(finite, stacked, 0.0).sum(axis=0)
    return np.where(count > 0, total / np.maximum(count, 1), np.nan)


def qixin_trace(recording_dir: str, record_duration_ms: float | None = None) -> GazeTrace:
    """Gaze for one 七鑫易维 recording, on the presentation clock.

    `record_duration_ms` must be the project file's duration for this
    recording. Omitting it leaves the sample clock unscaled, which misaligns
    the F500 device by 300-400 ms.
    """

    samples = qixin_io.read_basic_samples(recording_dir)
    valid = qixin_io.valid_gaze_mask(samples)
    pupil = _mean_pupil(
        samples["leftPupilDiameterMM"].to_numpy(dtype=float),
        samples["rightPupilDiameterMM"].to_numpy(dtype=float),
    )
    return GazeTrace(
        qixin_io.aligned_time_ms(samples, record_duration_ms),
        samples["recomGazePoint.x"].to_numpy(dtype=float),
        samples["recomGazePoint.y"].to_numpy(dtype=float),
        valid,
        pupil,
    )


def tobii_trace(recording: tobii_io.TobiiRecording, screen: tuple[int, int]) -> GazeTrace:
    width, height = screen
    return GazeTrace(
        recording.time_ms,
        recording.gaze_x / float(width),
        recording.gaze_y / float(height),
        recording.valid_mask(),
        _mean_pupil(recording.pupil_left, recording.pupil_right),
    )
