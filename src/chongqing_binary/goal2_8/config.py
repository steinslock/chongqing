"""Configuration helpers for Goal 2.8.

Re-exports the Goal 2.7 loaders so both goals share one implementation. Do not
clone them; the duplicated Goal 2.6/2.7 modules were the debt this goal repays.
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
