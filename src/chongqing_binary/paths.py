"""Runtime path overrides shared by Chongqing configuration loaders."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any


RAW_DATA_ENV = "CHONGQING_RAW_DATA_DIR"
DEFAULT_RAW_DATA_DIR = Path("/data4/qiangminc/datasets_qiangmin/chongqing")


def raw_data_override() -> Path | None:
    """Return the absolute raw-data override, when one is configured."""

    value = os.environ.get(RAW_DATA_ENV, "").strip()
    if not value:
        return None
    path = Path(value).expanduser()
    if not path.is_absolute():
        raise ValueError(f"{RAW_DATA_ENV} must be an absolute path: {value}")
    return path.resolve()


def apply_raw_data_override(config: dict[str, Any]) -> dict[str, Any]:
    """Apply the raw-data override and keep that input read-only."""

    override = raw_data_override()
    if override is None:
        return config

    paths = config.setdefault("paths", {})
    configured_raw = paths.get("raw_data_dir")
    paths["raw_data_dir"] = str(override)

    readonly = list(config.get("readonly_inputs", []))
    replacement = str(override)
    replaced = False
    for index, value in enumerate(readonly):
        if configured_raw is not None and str(value) == str(configured_raw):
            readonly[index] = replacement
            replaced = True
    if not replaced and replacement not in {str(value) for value in readonly}:
        readonly.append(replacement)
    config["readonly_inputs"] = readonly
    return config
