"""Attachment-sourced paradigm specification for Goal 2.8.

Feature code reads task structure from here instead of hardcoding event codes,
block counts, durations, or segment boundaries. See AGENTS.md,
Paradigm-Conformance Rules.
"""

from .spec import (
    EegTaskSpec,
    FnirsTaskSpec,
    ParadigmSpec,
    load_paradigm_spec,
)

__all__ = [
    "EegTaskSpec",
    "FnirsTaskSpec",
    "ParadigmSpec",
    "load_paradigm_spec",
]
