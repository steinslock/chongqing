"""fNIRS feature families."""

from __future__ import annotations


SIGNAL_FEATURE_PREFIXES = ("hbo_", "hbr_", "hbt_", "region_", "task_")
QC_FEATURE_PREFIXES = ("qc_", "bad_channel_", "motion_")


def feature_family(column: str) -> str:
    if column.startswith(QC_FEATURE_PREFIXES):
        return "qc"
    if column.startswith(SIGNAL_FEATURE_PREFIXES):
        return "signal"
    return "metadata"
