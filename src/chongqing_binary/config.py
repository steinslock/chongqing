"""Configuration loading and path safety for the Chongqing project."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "configs" / "default.yaml"


def _deep_merge(base: dict[str, Any], override: Mapping[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, Mapping) and isinstance(merged.get(key), Mapping):
            merged[key] = _deep_merge(dict(merged[key]), value)
        else:
            merged[key] = value
    return merged


def _read_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore

        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
    except ModuleNotFoundError:
        from .readiness import read_yaml

        data = read_yaml(path)
    if not isinstance(data, dict):
        raise ValueError(f"Config must be a mapping: {path}")
    return data


def _resolve_path(path_value: str | Path, root: Path = PROJECT_ROOT) -> Path:
    path = Path(path_value)
    if not path.is_absolute():
        path = root / path
    return path.resolve()


@dataclass(frozen=True)
class ProjectConfig:
    """Resolved project configuration."""

    path: Path
    data: dict[str, Any]
    project_root: Path = PROJECT_ROOT

    @property
    def seed(self) -> int:
        return int(self.data.get("project", {}).get("seed", 20260707))

    @property
    def label_column(self) -> str:
        return str(self.data.get("labels", {}).get("primary", "primary_label_nonhealthy"))

    @property
    def negative_label(self) -> str:
        return str(self.data.get("labels", {}).get("negative", "0"))

    @property
    def positive_label(self) -> str:
        return str(self.data.get("labels", {}).get("positive", "1"))

    @property
    def paths(self) -> dict[str, Path]:
        raw_paths = self.data.get("paths", {})
        return {key: _resolve_path(value, self.project_root) for key, value in raw_paths.items()}

    @property
    def readonly_inputs(self) -> tuple[Path, ...]:
        values = self.data.get("readonly_inputs", [])
        return tuple(_resolve_path(value, self.project_root) for value in values)

    @property
    def smoke_feature_columns(self) -> list[str]:
        return list(self.data.get("features", {}).get("allowed_smoke_columns", []))

    @property
    def forbidden_feature_exact(self) -> list[str]:
        return list(self.data.get("safety", {}).get("forbidden_feature_exact", []))

    @property
    def forbidden_feature_patterns(self) -> list[str]:
        return list(self.data.get("safety", {}).get("forbidden_feature_patterns", []))

    @property
    def smoke_limit(self) -> int:
        return int(self.data.get("smoke", {}).get("limit_subjects", 32))

    @property
    def smoke_test_fraction(self) -> float:
        return float(self.data.get("smoke", {}).get("test_fraction", 0.25))

    def output_path(self, key: str, *parts: str) -> Path:
        """Resolve and create a path under a configured output directory."""

        output_root = self.paths[key]
        target = output_root.joinpath(*parts)
        guard = ReadOnlyInputGuard(self.readonly_inputs)
        guard.assert_write_allowed(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        return target


class ReadOnlyInputGuard:
    """Guard writes away from raw data and read-only report inputs."""

    def __init__(self, readonly_roots: tuple[Path, ...] | list[Path]) -> None:
        self.readonly_roots = tuple(root.resolve() for root in readonly_roots)

    def assert_write_allowed(self, path: str | Path) -> None:
        target = Path(path).resolve()
        for root in self.readonly_roots:
            if target == root or target.is_relative_to(root):
                raise PermissionError(f"Refusing to write under read-only input: {target}")


def load_config(path: str | Path | None = None) -> ProjectConfig:
    """Load a YAML config and resolve optional `extends` from `configs/`."""

    config_path = _resolve_path(path or DEFAULT_CONFIG_PATH)
    data = _read_yaml(config_path)
    parent = data.pop("extends", None)
    if parent:
        parent_path = _resolve_path(parent, config_path.parent)
        base = _read_yaml(parent_path)
        data = _deep_merge(base, data)
    return ProjectConfig(path=config_path, data=data)
