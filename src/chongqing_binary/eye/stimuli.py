"""Stimulus-side products: face AOI boxes and video target trajectories.

Nothing here depends on any subject, so these products are computed once and
cached. The saccade and pursuit target positions exist nowhere in the recorded
data and can only be recovered by decoding the stimulus videos; the two 七鑫易维
projects hold byte-identical copies and Tobii presented the same files, so one
decode serves all three devices.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Sequence

import cv2
import numpy as np

from .spec import EyeParadigmSpec

# A stimulus pixel counts as foreground above this 8-bit level. The face images
# sit on a true black background (mean level 3.2/255), so the threshold only has
# to clear sensor noise and JPEG ringing.
FOREGROUND_LEVEL = 12

# The saccade and pursuit targets are the only bright object on a dark field.
TARGET_LEVEL = 40
TARGET_MIN_AREA_PX = 20

# Frames where the target dims below threshold leave a hole in the decoded
# track. Holes shorter than this are filled by linear interpolation; longer
# ones stay missing, because interpolating across them would invent motion.
TARGET_MAX_INTERPOLATED_FRAMES = 12

# The decoded centroid wobbles by a fraction of a pixel between frames, so a
# step detector on raw differences fires on noise. A real saccade step in these
# videos is 0.14 or 0.282 of screen width and holds for 60 frames.
MIN_STEP_AMPLITUDE = 0.02
MIN_STEP_HOLD_FRAMES = 5


@dataclass(frozen=True)
class FaceStimulusBox:
    """Normalised bounding box of the face region of one stimulus image."""

    media: str
    valence: str
    sex: str
    order: int
    x0: float
    y0: float
    x1: float
    y1: float
    image_width: int
    image_height: int

    @property
    def area_fraction(self) -> float:
        return (self.x1 - self.x0) * (self.y1 - self.y0)

    def contains(self, x: np.ndarray, y: np.ndarray) -> np.ndarray:
        return (x >= self.x0) & (x <= self.x1) & (y >= self.y0) & (y <= self.y1)


@dataclass(frozen=True)
class TargetTrack:
    """Per-frame normalised target position decoded from a stimulus video."""

    media: str
    fps: float
    x: np.ndarray
    y: np.ndarray
    interpolated_frames: int = 0

    @property
    def n_frames(self) -> int:
        return int(self.x.size)

    @property
    def duration_ms(self) -> float:
        return 1000.0 * self.n_frames / self.fps

    def at_time_ms(self, time_ms: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Target position sampled at arbitrary times within the video."""
        frames = np.clip((time_ms * self.fps / 1000.0).astype(int), 0, self.n_frames - 1)
        return self.x[frames], self.y[frames]

    def levels(self, min_step: float = MIN_STEP_AMPLITUDE, min_hold: int = MIN_STEP_HOLD_FRAMES) -> np.ndarray:
        """The target's held horizontal positions, with sub-pixel wobble removed.

        A new level is accepted only when it differs from the current one by at
        least `min_step` and holds for `min_hold` frames, so centroid noise
        cannot manufacture a step.
        """

        held = np.full(self.x.shape, np.nan)
        current = float("nan")
        for position in range(self.n_frames):
            value = float(self.x[position])
            if not np.isfinite(value):
                held[position] = current
                continue
            if not np.isfinite(current) or abs(value - current) >= min_step:
                window = self.x[position : position + min_hold]
                stable = np.isfinite(window).all() and float(np.nanmax(window) - np.nanmin(window)) < min_step
                if stable or not np.isfinite(current):
                    current = float(np.nanmedian(window)) if window.size else value
            held[position] = current
        return held

    def steps(self, min_step: float = MIN_STEP_AMPLITUDE) -> list[dict[str, Any]]:
        """Frames where the target jumps, with direction and amplitude."""

        held = self.levels(min_step=min_step)
        changed = np.flatnonzero(np.abs(np.diff(held)) >= min_step) + 1
        out: list[dict[str, Any]] = []
        for frame in changed:
            before = float(held[frame - 1])
            after = float(held[frame])
            out.append(
                {
                    "frame": int(frame),
                    "time_ms": 1000.0 * float(frame) / self.fps,
                    "from_x": before,
                    "to_x": after,
                    "direction": int(np.sign(after - before)),
                    "amplitude": float(abs(after - before)),
                    "is_outward": bool(abs(after - 0.5) > abs(before - 0.5)),
                }
            )
        return out


def face_stimulus_boxes(spec: EyeParadigmSpec, stimulus_dir: Path) -> list[FaceStimulusBox]:
    """Bounding box of the visible face in each free-viewing stimulus."""

    boxes: list[FaceStimulusBox] = []
    for stimulus in spec.free_viewing_sequence:
        path = stimulus_dir / f"{stimulus.media}.png"
        image = cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), cv2.IMREAD_GRAYSCALE)
        if image is None:
            raise FileNotFoundError(f"Unreadable stimulus image: {path}")
        height, width = image.shape
        ys, xs = np.where(image >= FOREGROUND_LEVEL)
        if xs.size == 0:
            raise ValueError(f"Stimulus image has no foreground above {FOREGROUND_LEVEL}: {path}")
        boxes.append(
            FaceStimulusBox(
                media=stimulus.media,
                valence=stimulus.valence,
                sex=stimulus.sex,
                order=stimulus.order,
                x0=float(xs.min()) / width,
                y0=float(ys.min()) / height,
                x1=float(xs.max() + 1) / width,
                y1=float(ys.max() + 1) / height,
                image_width=int(width),
                image_height=int(height),
            )
        )
    return boxes


def decode_target_track(video_path: Path) -> TargetTrack:
    """Per-frame target centroid of one stimulus video, in normalised coords."""

    capture = cv2.VideoCapture(str(video_path))
    try:
        fps = float(capture.get(cv2.CAP_PROP_FPS))
        width = float(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = float(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        xs: list[float] = []
        ys: list[float] = []
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            grey = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            mask = (grey >= TARGET_LEVEL).astype(np.uint8)
            count, _, stats, centroids = cv2.connectedComponentsWithStats(mask, 8)
            best_area = 0
            best = (float("nan"), float("nan"))
            for label in range(1, count):
                area = int(stats[label, cv2.CC_STAT_AREA])
                if area >= TARGET_MIN_AREA_PX and area > best_area:
                    best_area = area
                    best = (float(centroids[label][0]) / width, float(centroids[label][1]) / height)
            xs.append(best[0])
            ys.append(best[1])
    finally:
        capture.release()
    x = np.array(xs)
    y = np.array(ys)
    filled = _fill_short_gaps(x) + _fill_short_gaps(y)
    track = TargetTrack(media=video_path.stem, fps=fps, x=x, y=y)
    object.__setattr__(track, "interpolated_frames", filled // 2)
    return track


def _fill_short_gaps(values: np.ndarray, max_run: int = TARGET_MAX_INTERPOLATED_FRAMES) -> int:
    """Linearly fill missing runs no longer than `max_run`. Returns frames filled."""

    missing = ~np.isfinite(values)
    if not missing.any():
        return 0
    indices = np.arange(values.size)
    filled = 0
    start = None
    for position in range(values.size + 1):
        inside = position < values.size and missing[position]
        if inside and start is None:
            start = position
        elif not inside and start is not None:
            run = position - start
            if run <= max_run and start > 0 and position < values.size:
                values[start:position] = np.interp(
                    indices[start:position], [start - 1, position], [values[start - 1], values[position]]
                )
                filled += run
            start = None
    return filled


def build_stimulus_products(
    spec: EyeParadigmSpec, raw_root: Path, output_dir: Path, project_root: Path | None = None
) -> dict[str, Any]:
    """Compute and cache every stimulus-side product. Idempotent."""

    from .aoi import build_stimulus_aois, check_aoi_geometry, serialise

    output_dir.mkdir(parents=True, exist_ok=True)
    reference = raw_root / spec.device("qixin_120").root
    stimulus_dir = reference / spec.task("free_viewing").qixin_dir

    boxes = face_stimulus_boxes(spec, stimulus_dir)
    (output_dir / "free_viewing_face_boxes.json").write_text(
        json.dumps([asdict(box) for box in boxes], ensure_ascii=False, indent=2), encoding="utf-8"
    )

    aois = build_stimulus_aois(spec, stimulus_dir, project_root or Path.cwd())
    (output_dir / "free_viewing_aois.json").write_text(
        json.dumps(serialise(aois), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    aoi_check = check_aoi_geometry(aois, spec.task("free_viewing").raw["aoi"])

    tracks: dict[str, Any] = {}
    videos = {
        "prosaccade_formal": reference / spec.task("saccade").qixin_dir / "前扫视-正式.mp4",
        "antisaccade_formal": reference / spec.task("saccade").qixin_dir / "反扫视-正式.mp4",
        "prosaccade_practice": reference / spec.task("saccade").qixin_dir / "前扫视-练习.mp4",
        "antisaccade_practice": reference / spec.task("saccade").qixin_dir / "反扫视-练习.mp4",
        "pursuit": reference / spec.task("smooth_pursuit").qixin_dir / "平滑追随.mp4",
    }
    for name, path in videos.items():
        cache = output_dir / f"target_{name}.npz"
        if cache.exists():
            payload = np.load(cache)
            track = TargetTrack(
                media=str(payload["media"]),
                fps=float(payload["fps"]),
                x=payload["x"],
                y=payload["y"],
                interpolated_frames=int(payload["interpolated_frames"]) if "interpolated_frames" in payload else 0,
            )
        else:
            track = decode_target_track(path)
            np.savez_compressed(
                cache,
                media=track.media,
                fps=track.fps,
                x=track.x,
                y=track.y,
                interpolated_frames=getattr(track, "interpolated_frames", 0),
            )
        tracks[name] = track

    summary = {
        "aoi_geometry": aoi_check,
        "face_boxes": {
            "n": len(boxes),
            "area_fraction_median": float(np.median([box.area_fraction for box in boxes])),
            "x_range": [min(box.x0 for box in boxes), max(box.x1 for box in boxes)],
            "y_range": [min(box.y0 for box in boxes), max(box.y1 for box in boxes)],
        },
        "targets": {
            name: {
                "n_frames": track.n_frames,
                "fps": track.fps,
                "duration_ms": track.duration_ms,
                "unique_x": sorted({round(float(value), 3) for value in track.x if np.isfinite(value)}),
                "unique_y": sorted({round(float(value), 3) for value in track.y if np.isfinite(value)}),
                "n_steps": len(track.steps()),
                "n_saccade_trials": len(saccade_trials(track)) if name != "pursuit" else 0,
                "missing_frames": int(np.isnan(track.x).sum()),
                "interpolated_frames": int(getattr(track, "interpolated_frames", 0)),
            }
            for name, track in tracks.items()
        },
    }
    (output_dir / "stimulus_products.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return {"boxes": boxes, "aois": aois, "tracks": tracks, "summary": summary}


def pursuit_blocks(track: TargetTrack, min_block_ms: float = 5000.0) -> list[dict[str, Any]]:
    """Blocks of the pursuit video, from the runs where the target is present.

    The target is absent between blocks, so the missing runs in the decoded
    track are the block boundaries. Deriving them here rather than reading them
    from the specification keeps the specification a conformance check.
    """

    present = np.isfinite(track.x)
    blocks: list[dict[str, Any]] = []
    start: int | None = None
    for position in range(present.size + 1):
        inside = position < present.size and bool(present[position])
        if inside and start is None:
            start = position
        elif not inside and start is not None:
            duration_ms = 1000.0 * (position - start) / track.fps
            if duration_ms >= min_block_ms:
                blocks.append(
                    {
                        "block": len(blocks),
                        "start_ms": 1000.0 * start / track.fps,
                        "end_ms": 1000.0 * position / track.fps,
                        "duration_ms": duration_ms,
                    }
                )
            start = None
    return blocks


def saccade_trials(track: TargetTrack) -> list[dict[str, Any]]:
    """Outward target steps, one per saccade trial, with the return time."""

    steps = track.steps()
    trials: list[dict[str, Any]] = []
    for position, step in enumerate(steps):
        if not step["is_outward"]:
            continue
        next_return = next((later["time_ms"] for later in steps[position + 1 :] if not later["is_outward"]), track.duration_ms)
        trials.append(
            {
                "trial": len(trials),
                "onset_ms": step["time_ms"],
                "offset_ms": next_return,
                "target_x": step["to_x"],
                "direction": step["direction"],
                "amplitude": step["amplitude"],
            }
        )
    return trials
