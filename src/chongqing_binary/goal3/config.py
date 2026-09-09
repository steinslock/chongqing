"""Configuration helpers for Goal 3.

Re-exports the Goal 2.7 loaders, exactly as Goal 2.8 and Goal 2.9 do, so every
stage of this project resolves paths, splits and demographics the same way.
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
