"""fNIRS preprocessing plan and smoke helpers."""

from __future__ import annotations


def planned_preprocessing_steps() -> list[str]:
    return [
        "read device-specific file",
        "confirm signal semantics",
        "raw intensity to optical density when raw intensity is present",
        "optical density to HbO/HbR when wavelengths/source-detector geometry are known",
        "bad channel detection",
        "motion artifact detection",
        "band-pass filtering",
        "task segment extraction",
        "baseline correction",
    ]
