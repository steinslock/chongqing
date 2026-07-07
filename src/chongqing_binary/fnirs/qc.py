"""fNIRS QC helpers."""

from __future__ import annotations


def minimum_qc_pass(file_exists: bool, readable: bool, channel_count: int | str) -> tuple[bool, str]:
    reasons: list[str] = []
    if not file_exists:
        reasons.append("raw_file_missing")
    if file_exists and not readable:
        reasons.append("raw_file_not_readable")
    try:
        if int(channel_count) <= 0:
            reasons.append("no_channels")
    except Exception:
        reasons.append("channel_count_unknown")
    return (not reasons, ";".join(reasons))


def placeholder_qc_metrics() -> dict[str, str | int]:
    return {
        "bad_channel_count": "",
        "bad_channel_rate": "",
        "saturated_channel_rate": "",
        "low_signal_channel_rate": "",
        "motion_artifact_metric": "",
    }
