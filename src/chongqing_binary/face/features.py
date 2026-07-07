"""Frozen lightweight visual features used by Face smoke tests."""

from __future__ import annotations

from typing import Any


def simple_frozen_embedding(frame: Any) -> list[float]:
    """A deterministic non-trained frame descriptor for smoke shape checks."""

    try:
        import cv2  # type: ignore
        import numpy as np  # type: ignore

        resized = cv2.resize(frame, (64, 64))
        arr = resized.astype("float32") / 255.0
        means = arr.mean(axis=(0, 1)).tolist()
        stds = arr.std(axis=(0, 1)).tolist()
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        hist = cv2.calcHist([gray], [0], None, [8], [0, 256]).flatten()
        hist = (hist / max(float(hist.sum()), 1.0)).tolist()
        return [float(x) for x in means + stds + hist]
    except Exception:
        return []


def temporal_forward_shape(embeddings: list[list[float]]) -> tuple[int, int]:
    if not embeddings:
        return (0, 0)
    return (len(embeddings), len(embeddings[0]))
