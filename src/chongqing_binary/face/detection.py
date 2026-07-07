"""Face detection utilities for smoke tests."""

from __future__ import annotations

from typing import Any


def detect_faces(frame: Any) -> list[tuple[int, int, int, int]]:
    try:
        import cv2  # type: ignore

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        detector = cv2.CascadeClassifier(cascade_path)
        boxes = detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(24, 24))
        return [(int(x), int(y), int(w), int(h)) for x, y, w, h in boxes]
    except Exception:
        return []
