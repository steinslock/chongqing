"""Loader for the Goal 2.8 paradigm specification.

The specification records how each experiment was actually run, with a `source`
on every value naming the dataset attachment it came from. Feature code must
take task structure from here rather than hardcoding it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SPEC_PATH = "configs/goal2_8/paradigm_spec.yaml"


def project_path(path: str | Path) -> Path:
    value = Path(path).expanduser()
    if not value.is_absolute():
        value = PROJECT_ROOT / value
    return value


@dataclass(frozen=True)
class EegTaskSpec:
    """Structure of one EEG task."""

    task: str
    raw_dir: str
    event_free: bool
    event_codes: dict[str, dict[str, Any]]
    epoch: dict[str, Any]
    raw: dict[str, Any] = field(repr=False, default_factory=dict)

    @property
    def codes(self) -> list[str]:
        """Every event code this task emits, as strings."""
        return sorted(self.event_codes)

    def codes_for_contrast(self) -> list[str]:
        """Codes usable as experimental conditions."""
        return sorted(
            code
            for code, meta in self.event_codes.items()
            if meta.get("use_in_condition_contrast", meta.get("usable", True))
            and meta.get("usable", True)
            and meta.get("lag_trials") is None
        )

    def condition_of(self, code: str | int) -> str:
        meta = self.event_codes.get(str(code))
        return "" if meta is None else str(meta.get("condition", ""))

    def expected_total(self, code: str | int) -> int | None:
        totals = self.raw.get("expected_total_per_subject") or {}
        value = totals.get(str(code))
        return None if value is None else int(value)

    @property
    def primary_contrast(self) -> dict[str, Any] | None:
        return self.raw.get("primary_contrast")

    @property
    def epoch_window(self) -> tuple[float, float]:
        return float(self.epoch["tmin"]), float(self.epoch["tmax"])

    @property
    def baseline(self) -> tuple[float, float] | None:
        base = self.epoch.get("baseline")
        if not base:
            return None
        return float(base[0]), float(base[1])


@dataclass(frozen=True)
class FnirsTaskSpec:
    """Structure of one fNIRS task on one device."""

    device: str
    task: str
    raw_dir: str
    duration_sec: float
    event_free: bool
    raw: dict[str, Any] = field(repr=False, default_factory=dict)
    device_raw: dict[str, Any] = field(repr=False, default_factory=dict)

    @property
    def sfreq_hz(self) -> float:
        return float(self.device_raw["sfreq_hz"])

    @property
    def wavelengths_nm(self) -> list[float]:
        return [float(x) for x in self.device_raw["wavelengths_nm"]]

    @property
    def n_channels(self) -> int:
        return int(self.device_raw["n_channels"])

    @property
    def expected_marker_count(self) -> int | None:
        if "markers" in self.raw:
            return int(self.raw["markers"])
        if "marker_sequence" in self.raw:
            return len(self.raw["marker_sequence"])
        if "marker_pairs" in self.raw:
            return int(self.raw["marker_pairs"]) * 2 + 2  # ST + pairs + ED
        return None

    @property
    def expected_marker_onsets_sec(self) -> list[float] | None:
        if self.raw.get("marker_onsets_sec"):
            return [float(x) for x in self.raw["marker_onsets_sec"]]
        first = self.raw.get("first_marker_sec")
        interval = self.raw.get("marker_interval_sec")
        blocks = self.raw.get("task_blocks")
        if first is None or interval is None or blocks is None:
            return None
        return [float(first) + float(interval) * i for i in range(int(blocks))]

    @property
    def marker_labels(self) -> dict[str, str]:
        return dict(self.device_raw.get("marker_semantics", {}) or {})

    @property
    def timing_confidence(self) -> str:
        return str(self.raw.get("timing_confidence", "high"))

    @property
    def sensitivity_only(self) -> bool:
        return bool(self.raw.get("sensitivity_only", False))

    def block_windows(self, onsets_sec: list[float]) -> list[dict[str, float]]:
        """Baseline/task/recovery windows for each block, from observed onsets.

        Uses the observed marker onsets plus the specified block duration and
        baseline length. Returns an empty list for event-free tasks or when the
        specification does not define a block duration.
        """
        if self.event_free:
            return []
        block_sec = self.raw.get("block_duration_sec")
        if block_sec is None or not onsets_sec:
            return []
        block_sec = float(block_sec)
        baseline_sec = float(self.raw.get("baseline_sec", 30))
        intro_sec = float(self.raw.get("intro_sec", 0.0))
        onsets = sorted(float(x) for x in onsets_sec)
        total_blocks = int(self.raw.get("task_blocks", len(onsets)) or len(onsets))
        # Some tasks emit one marker per block (1BACK, Oddball, Doors); VFT emits
        # a single marker and then runs its blocks back to back from that onset.
        blocks_per_onset = max(1, total_blocks // max(1, len(onsets)))
        windows: list[dict[str, float]] = []
        index = 0
        for onset in onsets:
            for step in range(blocks_per_onset):
                task_start = onset + intro_sec + step * block_sec
                task_end = task_start + block_sec
                windows.append(
                    {
                        "block": float(index),
                        "baseline_start": max(0.0, onset - baseline_sec) if step == 0 else task_start - block_sec,
                        "baseline_end": onset if step == 0 else task_start,
                        "task_start": task_start,
                        "task_end": min(task_end, float(self.duration_sec)),
                        "recovery_start": task_end,
                        "recovery_end": min(task_end + baseline_sec, float(self.duration_sec)),
                    }
                )
                index += 1
        return windows


@dataclass(frozen=True)
class ParadigmSpec:
    """The whole specification."""

    data: dict[str, Any]
    path: Path

    @property
    def version(self) -> str:
        return str(self.data.get("spec_version", ""))

    @property
    def sources(self) -> dict[str, str]:
        return dict(self.data.get("sources", {}) or {})

    @property
    def known_gaps(self) -> dict[str, Any]:
        return dict(self.data.get("known_gaps", {}) or {})

    @property
    def antipatterns(self) -> dict[str, Any]:
        return dict(self.data.get("antipatterns", {}) or {})

    # -- EEG ---------------------------------------------------------------
    @property
    def eeg_common(self) -> dict[str, Any]:
        return dict(self.data["eeg"].get("common", {}) or {})

    def eeg_tasks(self) -> list[str]:
        return [key for key in self.data["eeg"] if key != "common"]

    def eeg(self, task: str) -> EegTaskSpec:
        raw = self.data["eeg"][task]
        return EegTaskSpec(
            task=task,
            raw_dir=str(raw.get("dir", "")),
            event_free=bool(raw.get("event_free", False)),
            event_codes={str(k): dict(v) for k, v in (raw.get("event_codes") or {}).items()},
            epoch=dict(raw.get("epoch", {}) or {}),
            raw=raw,
        )

    # -- fNIRS -------------------------------------------------------------
    def fnirs_devices(self) -> list[str]:
        return list(self.data["fnirs"])

    def fnirs_tasks(self, device: str) -> list[str]:
        return list(self.data["fnirs"][device]["tasks"])

    def fnirs(self, device: str, task: str) -> FnirsTaskSpec:
        device_raw = self.data["fnirs"][device]
        raw = device_raw["tasks"][task]
        return FnirsTaskSpec(
            device=device,
            task=task,
            raw_dir=str(raw.get("dir", "")),
            duration_sec=float(raw.get("duration_sec", 0.0)),
            event_free=bool(raw.get("event_free", False)),
            raw=raw,
            device_raw=device_raw,
        )

    # -- Face --------------------------------------------------------------
    @property
    def face(self) -> dict[str, Any]:
        return dict(self.data.get("face", {}) or {})

    def face_movies(self) -> dict[str, dict[str, Any]]:
        return dict(self.face.get("task", {}).get("movies", {}) or {})


def load_paradigm_spec(path: str | Path = DEFAULT_SPEC_PATH) -> ParadigmSpec:
    spec_path = project_path(path)
    with spec_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Paradigm spec root must be a mapping: {spec_path}")
    for required in ("spec_version", "sources", "eeg", "fnirs", "face"):
        if required not in data:
            raise ValueError(f"Paradigm spec missing required section '{required}': {spec_path}")
    return ParadigmSpec(data=data, path=spec_path)
