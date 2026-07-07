"""Video frame sampling for Face smoke tests."""

from __future__ import annotations

from pathlib import Path


def sample_frames(path: str | Path, n_frames: int) -> list[object]:
    try:
        import cv2  # type: ignore

        cap = cv2.VideoCapture(str(path))
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        if not cap.isOpened() or total <= 0:
            return []
        indices = [int((i + 0.5) * total / n_frames) for i in range(n_frames)]
        frames = []
        for idx in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ok, frame = cap.read()
            if ok:
                frames.append(frame)
        cap.release()
        return frames
    except Exception:
        return []
