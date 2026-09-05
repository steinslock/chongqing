"""Relocatable paths for the legacy Chongqing v1 EEG entry points."""

from __future__ import annotations

import os
from pathlib import Path


RAW_DATA_ENV = "CHONGQING_RAW_DATA_DIR"
PROJECT_ROOT = Path(__file__).resolve().parents[4]
V1_ROOT = PROJECT_ROOT / "experiments" / "v1"
MANIFEST = PROJECT_ROOT / "inputs" / "derived_reports" / "chongqing_binary_diagnosis_report" / "data" / "subject_manifest.csv"


def _raw_data_root() -> Path:
    value = os.environ.get(RAW_DATA_ENV, "/data4/qiangminc/datasets_qiangmin/chongqing")
    path = Path(value).expanduser()
    if not path.is_absolute():
        raise ValueError(f"{RAW_DATA_ENV} must be an absolute path: {value}")
    return path.resolve()


DATA_ROOT = _raw_data_root()
