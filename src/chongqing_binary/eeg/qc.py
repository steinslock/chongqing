"""EEG QC helpers."""

from __future__ import annotations

from .io import BdfHeader


def required_channel_complete(channel_names: tuple[str, ...], required: list[str]) -> bool:
    available = {name.strip().replace(" ", "").lower() for name in channel_names}
    return all(ch.lower() in available for ch in required)


def minimum_qc_pass(
    data_header: BdfHeader,
    event_header: BdfHeader,
    required_channels: list[str],
    min_duration_sec: float,
) -> tuple[bool, str]:
    reasons: list[str] = []
    if data_header.status != "ok":
        reasons.append("data_bdf_not_readable")
    if event_header.status not in {"ok", "missing"}:
        reasons.append("event_bdf_not_readable")
    if data_header.status == "ok":
        if data_header.n_channels <= 0:
            reasons.append("no_channels")
        if not required_channel_complete(data_header.channel_names, required_channels):
            reasons.append("required_channels_incomplete")
        if (data_header.duration_sec or 0) < min_duration_sec:
            reasons.append("duration_below_minimum")
        if not data_header.sfreq or data_header.sfreq <= 0:
            reasons.append("invalid_sampling_rate")
    return (not reasons, ";".join(reasons))
