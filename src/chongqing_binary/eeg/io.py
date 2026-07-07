"""Lightweight EEG/BDF IO helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class BdfHeader:
    status: str
    n_channels: int = 0
    channel_names: tuple[str, ...] = ()
    sfreq: float | None = None
    n_records: int | None = None
    record_duration_sec: float | None = None
    duration_sec: float | None = None
    error: str = ""


def read_bdf_header(path: str | Path) -> BdfHeader:
    """Parse an EDF/BDF header without reading signal samples."""

    path = Path(path)
    if not path.exists():
        return BdfHeader(status="missing", error="file_missing")
    try:
        with path.open("rb") as handle:
            fixed = handle.read(256)
            if len(fixed) < 256:
                return BdfHeader(status="fail", error="header_too_short")
            n_records = _int_text(fixed[236:244])
            record_duration = _float_text(fixed[244:252])
            n_channels = _int_text(fixed[252:256])
            variable = handle.read(256 * n_channels)
        if len(variable) < 256 * n_channels:
            return BdfHeader(status="fail", error="channel_header_too_short")
        labels = []
        offset = 0
        for _ in range(n_channels):
            labels.append(_decode(variable[offset : offset + 16]))
            offset += 16
        offset = 16 * n_channels
        offset += 80 * n_channels  # transducer
        offset += 8 * n_channels  # physical dimension
        offset += 8 * n_channels  # physical min
        offset += 8 * n_channels  # physical max
        offset += 8 * n_channels  # digital min
        offset += 8 * n_channels  # digital max
        offset += 80 * n_channels  # prefiltering
        samples_per_record = []
        for _ in range(n_channels):
            samples_per_record.append(_int_text(variable[offset : offset + 8]))
            offset += 8
        sfreq = None
        if record_duration and samples_per_record:
            sfreq = samples_per_record[0] / record_duration
        duration = None
        if n_records is not None and record_duration is not None and n_records >= 0:
            duration = n_records * record_duration
        return BdfHeader(
            status="ok",
            n_channels=n_channels,
            channel_names=tuple(labels),
            sfreq=sfreq,
            n_records=n_records,
            record_duration_sec=record_duration,
            duration_sec=duration,
        )
    except Exception as exc:
        return BdfHeader(status="fail", error=type(exc).__name__ + ":" + str(exc)[:160])


def _decode(raw: bytes) -> str:
    return raw.decode("latin-1", errors="ignore").strip().replace(" ", "")


def _int_text(raw: bytes) -> int | None:
    text = _decode(raw)
    if not text:
        return None
    return int(float(text))


def _float_text(raw: bytes) -> float | None:
    text = _decode(raw)
    if not text:
        return None
    return float(text)
