"""EEG feature-set definitions for leakage and QC separation tests."""

from __future__ import annotations


QC_FEATURE_PREFIXES = ("qc_",)
SIGNAL_FEATURE_PREFIXES = ("bp_", "region_", "asym_", "spectral_entropy", "hjorth_")


def feature_family(column: str) -> str:
    if column.startswith(QC_FEATURE_PREFIXES):
        return "qc"
    if column.startswith(SIGNAL_FEATURE_PREFIXES):
        return "signal"
    return "metadata"


def qc_and_signal_disjoint(columns: list[str]) -> bool:
    qc = {col for col in columns if feature_family(col) == "qc"}
    signal = {col for col in columns if feature_family(col) == "signal"}
    return qc.isdisjoint(signal)
