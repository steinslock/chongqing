"""Video metadata and frame IO."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import subprocess


@dataclass(frozen=True)
class VideoMeta:
    readable: bool
    codec: str = ""
    container: str = "mp4"
    duration_sec: float | None = None
    width: int | None = None
    height: int | None = None
    fps: float | None = None
    frame_count: int | None = None
    error: str = ""


def probe_video(path: str | Path) -> VideoMeta:
    path = Path(path)
    if not path.exists():
        return VideoMeta(False, error="file_missing")
    meta = _probe_video_ffprobe(path)
    if meta is not None:
        return meta
    try:
        import cv2  # type: ignore

        cap = cv2.VideoCapture(str(path))
        if not cap.isOpened():
            return VideoMeta(False, error="video_capture_not_opened")
        fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        fourcc = int(cap.get(cv2.CAP_PROP_FOURCC) or 0)
        codec = "".join(chr((fourcc >> 8 * i) & 0xFF) for i in range(4)).strip("\x00")
        cap.release()
        duration = frame_count / fps if fps > 0 else None
        if frame_count <= 0 or fps <= 0 or width <= 0 or height <= 0:
            return VideoMeta(False, codec=codec, duration_sec=duration, width=width, height=height, fps=fps, frame_count=frame_count, error="invalid_video_metadata")
        return VideoMeta(True, codec=codec, duration_sec=duration, width=width, height=height, fps=fps, frame_count=frame_count)
    except Exception as exc:
        return VideoMeta(False, error=type(exc).__name__ + ":" + str(exc)[:160])


def _probe_video_ffprobe(path: Path) -> VideoMeta | None:
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=codec_name,width,height,r_frame_rate,nb_frames,duration",
                "-of",
                "json",
                str(path),
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=3,
        )
        if result.returncode != 0:
            return VideoMeta(False, error="ffprobe_error:" + result.stderr.strip()[:120])
        data = json.loads(result.stdout or "{}")
        streams = data.get("streams") or []
        if not streams:
            return VideoMeta(False, error="ffprobe_no_video_stream")
        stream = streams[0]
        fps = _parse_rate(stream.get("r_frame_rate", ""))
        duration = _float_or_none(stream.get("duration"))
        frames = _int_or_none(stream.get("nb_frames"))
        if frames is None and duration and fps:
            frames = int(round(duration * fps))
        return VideoMeta(
            True,
            codec=str(stream.get("codec_name", "")),
            duration_sec=duration,
            width=_int_or_none(stream.get("width")),
            height=_int_or_none(stream.get("height")),
            fps=fps,
            frame_count=frames,
        )
    except subprocess.TimeoutExpired:
        return VideoMeta(False, error="ffprobe_timeout")
    except FileNotFoundError:
        return None
    except Exception:
        return None


def _parse_rate(value: str) -> float | None:
    try:
        if "/" in value:
            num, den = value.split("/", 1)
            den_f = float(den)
            return float(num) / den_f if den_f else None
        return float(value)
    except Exception:
        return None


def _float_or_none(value: object) -> float | None:
    try:
        return float(value)  # type: ignore[arg-type]
    except Exception:
        return None


def _int_or_none(value: object) -> int | None:
    try:
        return int(float(value))  # type: ignore[arg-type]
    except Exception:
        return None
