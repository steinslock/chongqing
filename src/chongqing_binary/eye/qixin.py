"""Readers for the 七鑫易维 (7invensun) eye-tracking project export.

Stimulus onsets are NOT in the per-subject export: every `*_annotation.csv` is
header-only. They live in the project `.asdata` file, a single JSON document
holding, per experiment and per recording, the start and end time of every
presented medium. That file also carries the vendor's own recording-level
quality numbers.

The sample clock and the presentation clock are not the same clock. On the
F500 device the sample timestamps span about 0.4 percent longer than the
recording duration the project file reports, which accumulates to a 300-400 ms
misalignment by the end of a 136 s block. `aligned_time_ms` maps sample time
onto the presentation clock; without it every trial-locked feature on that
device would be silently wrong.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

# `type` codes in `*_filter.csv`. Confirmed against the per-record
# fixationCount / saccadeCount the vendor stores in the .asdata file.
FILTER_TYPE_FIXATION = 4
FILTER_TYPE_SACCADE = 2

BASIC_COLUMNS = [
    "timestampUs",
    "recomGazePoint.x",
    "recomGazePoint.y",
    "recommend",
    "leftBlink",
    "rightBlink",
    "leftPupilDiameterMM",
    "rightPupilDiameterMM",
]

RECORD_QC_FIELDS = [
    "dataCount",
    "duration",
    "validRatio",
    "gazeRate",
    "settingGazeRate",
    "fps",
    "leftScore",
    "rightScore",
    "fixationCount",
    "saccadeCount",
    "blinkCount",
]


@dataclass(frozen=True)
class MediaSegment:
    """One presented medium inside one recording."""

    media: str
    index: int
    start_ms: int
    end_ms: int

    @property
    def duration_ms(self) -> int:
        return self.end_ms - self.start_ms


@dataclass(frozen=True)
class QixinRecord:
    """One recording as the project file describes it."""

    experiment: str
    record_name: str
    timeline: tuple[MediaSegment, ...]
    qc: dict[str, Any] = field(repr=False, default_factory=dict)

    @property
    def n_media_segments(self) -> int:
        return len(self.timeline)

    @property
    def duration_ms(self) -> float:
        return float(self.qc.get("duration", 0) or 0)

    def segments_named(self, media: str) -> list[MediaSegment]:
        return [segment for segment in self.timeline if segment.media == media]


@dataclass(frozen=True)
class AsdataIndex:
    """Every recording in one 七鑫易维 project, keyed by experiment and name."""

    path: Path
    records: dict[tuple[str, str], QixinRecord]
    experiments: tuple[str, ...]

    def get(self, experiment: str, record_name: str) -> QixinRecord | None:
        return self.records.get((experiment, record_name))


def load_asdata(path: str | Path) -> AsdataIndex:
    """Parse one `.asdata` project file into per-recording timelines."""

    path = Path(path)
    document = json.loads(path.read_text(encoding="utf-8"))
    records: dict[tuple[str, str], QixinRecord] = {}
    experiments: list[str] = []

    for experiment_block in document.get("experimentPoMap", {}).values():
        experiment = str(experiment_block.get("experiment", {}).get("name", ""))
        experiments.append(experiment)
        media_names = {
            int(media_id): str(media.get("media", {}).get("name") or media.get("media", {}).get("path") or "")
            for media_id, media in experiment_block.get("mediaPoMap", {}).items()
        }
        for record_block in experiment_block.get("recordPoMap", {}).values():
            record = record_block.get("record", {})
            record_name = str(record.get("dataName") or record.get("name") or "")
            if not record_name:
                continue
            segments = sorted(
                (
                    MediaSegment(
                        media=media_names.get(int(entry.get("mediaId", -1)), ""),
                        index=int(entry.get("index", 0)),
                        start_ms=int(entry.get("startTime", 0)),
                        end_ms=int(entry.get("endTime", 0)),
                    )
                    for entry in record_block.get("mediaInRecordMap", {}).values()
                ),
                key=lambda segment: segment.start_ms,
            )
            records[(experiment, record_name)] = QixinRecord(
                experiment=experiment,
                record_name=record_name,
                timeline=tuple(segments),
                qc={key: record.get(key) for key in RECORD_QC_FIELDS},
            )
    return AsdataIndex(path=path, records=records, experiments=tuple(sorted(set(experiments))))


def annotate_recordings(
    rows: Sequence[Mapping[str, Any]],
    spec,
    asdata_by_device: Mapping[str, AsdataIndex],
) -> list[dict[str, Any]]:
    """Attach the project file's timeline and quality numbers to discovery rows.

    Runs before deduplication so that a take with a complete timeline is
    preferred over an aborted one.
    """

    out: list[dict[str, Any]] = []
    for row in rows:
        new = dict(row)
        index = asdata_by_device.get(str(row.get("device", "")))
        task_name = str(row.get("task") or "")
        if index is not None and task_name:
            experiment = spec.task(task_name).qixin_dir
            record = index.get(experiment, str(row.get("record_name", "")))
            if record is not None:
                expected = spec.task(task_name).expected_media_segments(str(row["device"]))
                new["n_media_segments"] = record.n_media_segments
                new["record_duration_ms"] = record.duration_ms
                new["timeline_complete"] = int(expected is not None and record.n_media_segments == expected)
                new["asdata_found"] = 1
                for key in RECORD_QC_FIELDS:
                    new[f"vendor_{key}"] = record.qc.get(key)
            else:
                new["asdata_found"] = 0
        out.append(new)
    return out


def aligned_time_ms(samples: pd.DataFrame, record_duration_ms: float | None) -> np.ndarray:
    """Sample times mapped onto the presentation clock the timeline uses.

    The project file's `duration` is the authoritative recording length, since
    the media start and end times are expressed against it. Sample timestamps
    run on the tracker's own clock, which drifts against it by device.
    """

    time_ms = (samples["timestampUs"].to_numpy(dtype=float) - float(samples["timestampUs"].iloc[0])) / 1000.0
    span = float(time_ms[-1] - time_ms[0]) if time_ms.size > 1 else 0.0
    if not record_duration_ms or span <= 0:
        return time_ms
    return time_ms * (float(record_duration_ms) / span)


def clock_scale(samples: pd.DataFrame, record_duration_ms: float | None) -> float:
    """How far the sample clock runs from the presentation clock, as a ratio."""

    time_ms = samples["time_ms"].to_numpy(dtype=float)
    span = float(time_ms[-1] - time_ms[0]) if time_ms.size > 1 else 0.0
    if not record_duration_ms or span <= 0:
        return float("nan")
    return float(record_duration_ms) / span


def read_basic_samples(recording_dir: str | Path) -> pd.DataFrame:
    """Per-sample gaze, pupil and blink for one recording."""

    recording_dir = Path(recording_dir)
    matches = sorted(recording_dir.glob("*_basic.csv"))
    if not matches:
        raise FileNotFoundError(f"No *_basic.csv under {recording_dir}")
    frame = pd.read_csv(matches[0], encoding="utf-8-sig", usecols=lambda name: name in set(BASIC_COLUMNS))
    frame["time_ms"] = (frame["timestampUs"] - frame["timestampUs"].iloc[0]) / 1000.0
    return frame


def read_filter_events(recording_dir: str | Path) -> pd.DataFrame:
    """Vendor-classified fixation and saccade events for one recording."""

    recording_dir = Path(recording_dir)
    matches = sorted(recording_dir.glob("*_filter.csv"))
    if not matches:
        raise FileNotFoundError(f"No *_filter.csv under {recording_dir}")
    frame = pd.read_csv(matches[0], encoding="utf-8-sig")
    frame["is_fixation"] = frame["type"] == FILTER_TYPE_FIXATION
    frame["is_saccade"] = frame["type"] == FILTER_TYPE_SACCADE
    return frame


def valid_gaze_mask(samples: pd.DataFrame) -> np.ndarray:
    """Samples the tracker itself marks usable, with a gaze point on screen."""

    recommended = samples["recommend"].to_numpy() == 1
    x = samples["recomGazePoint.x"].to_numpy(dtype=float)
    y = samples["recomGazePoint.y"].to_numpy(dtype=float)
    on_screen = np.isfinite(x) & np.isfinite(y) & (x >= 0.0) & (x <= 1.0) & (y >= 0.0) & (y <= 1.0)
    blink = (samples["leftBlink"].to_numpy() == 1) & (samples["rightBlink"].to_numpy() == 1)
    return recommended & on_screen & ~blink
