"""Configuration helpers for Goal 2.7."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def project_path(path: str | Path) -> Path:
    value = Path(path)
    if not value.is_absolute():
        value = PROJECT_ROOT / value
    return value.resolve()


def load_goal_config(path: str | Path) -> dict[str, Any]:
    cfg_path = project_path(path)
    data = _read_yaml(cfg_path)
    parent = data.pop("extends", None)
    if parent:
        parent_path = Path(parent)
        if not parent_path.is_absolute():
            parent_path = cfg_path.parent / parent_path
        base = load_goal_config(parent_path)
        data = _deep_merge(base, data)
    project_config = data.get("project_config")
    if project_config and "_project_config_loaded" not in data:
        project_data = _read_yaml(project_path(project_config))
        data = _deep_merge(project_data, data)
        data["_project_config_loaded"] = True
    data["_config_path"] = str(cfg_path)
    return data


def ensure_output(path: str | Path, config: dict[str, Any]) -> Path:
    target = project_path(path)
    readonly = [project_path(p) for p in config.get("readonly_inputs", [])]
    for root in readonly:
        if target == root or target.is_relative_to(root):
            raise PermissionError(f"Refusing to write under read-only input: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


def _read_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be a mapping: {path}")
    return data


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged
