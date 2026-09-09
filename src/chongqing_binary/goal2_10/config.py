"""Configuration helpers for Goal 2.10.

Re-exports the shared loaders so every goal uses one implementation.
"""

from __future__ import annotations

from ..goal2_7.config import PROJECT_ROOT, ensure_output, load_goal_config, project_path
from ..goal2_7.io import add_clean_demographics, cv_subjects, load_split, merge_cv_metadata

__all__ = [
    "PROJECT_ROOT",
    "add_clean_demographics",
    "cv_subjects",
    "ensure_output",
    "load_goal_config",
    "load_split",
    "merge_cv_metadata",
    "project_path",
]
