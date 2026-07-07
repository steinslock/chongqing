"""Face/video QC helpers."""

from __future__ import annotations

from .io import VideoMeta


def minimum_qc_pass(meta: VideoMeta, min_duration_sec: float) -> tuple[bool, str]:
    reasons: list[str] = []
    if not meta.readable:
        reasons.append(meta.error or "video_not_readable")
    if meta.readable and (meta.duration_sec or 0) < min_duration_sec:
        reasons.append("duration_below_expected")
    if meta.readable and (meta.frame_count or 0) <= 0:
        reasons.append("no_frames")
    if meta.readable and (meta.fps or 0) <= 0:
        reasons.append("invalid_fps")
    return (not reasons, ";".join(reasons))
