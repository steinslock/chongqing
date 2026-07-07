"""EEG preprocessing placeholders used by Goal 2.5 smoke tests."""

from __future__ import annotations


def planned_preprocessing_steps() -> list[str]:
    return [
        "read BDF",
        "clean channel names",
        "pick required EEG channels",
        "average reference",
        "notch 50Hz",
        "band-pass 0.5-45Hz",
        "resample for deep windows",
        "reject high-amplitude and flat windows",
    ]
