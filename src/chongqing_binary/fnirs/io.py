"""Lightweight fNIRS file readers."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class FnirsProbe:
    readable: bool
    format: str
    variables: dict[str, str]
    row_count: int | None = None
    column_count: int | None = None
    error: str = ""


def probe_yiruid_nirs(path: str | Path) -> FnirsProbe:
    path = Path(path)
    if not path.exists():
        return FnirsProbe(False, "nirs", {}, error="file_missing")
    try:
        from scipy.io import whosmat  # type: ignore

        variables = {name: "x".join(str(dim) for dim in shape) for name, shape, _ in whosmat(path)}
        return FnirsProbe(True, "nirs", variables)
    except Exception as exc:
        return FnirsProbe(False, "nirs", {}, error=type(exc).__name__ + ":" + str(exc)[:160])


def probe_csv(path: str | Path) -> FnirsProbe:
    path = Path(path)
    if not path.exists():
        return FnirsProbe(False, "csv", {}, error="file_missing")
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.reader(handle)
            header = next(reader, [])
            rows = 0
            for rows, _ in enumerate(reader, start=1):
                if rows >= 50:
                    break
        return FnirsProbe(True, "csv", {"header_columns": str(len(header))}, row_count=rows, column_count=len(header))
    except UnicodeDecodeError:
        try:
            with path.open("r", encoding="gb18030", newline="") as handle:
                reader = csv.reader(handle)
                header = next(reader, [])
            return FnirsProbe(True, "csv", {"header_columns": str(len(header))}, column_count=len(header))
        except Exception as exc:
            return FnirsProbe(False, "csv", {}, error=type(exc).__name__ + ":" + str(exc)[:160])
    except Exception as exc:
        return FnirsProbe(False, "csv", {}, error=type(exc).__name__ + ":" + str(exc)[:160])


def infer_yiruid_semantics(variables: dict[str, str]) -> dict[str, Any]:
    has_d = "d" in variables
    return {
        "raw_intensity_exists": int(has_d),
        "optical_density_computable": int(has_d),
        "hbo_hbr_exists_or_computable": int(has_d),
        "event_marker_exists": int("s" in variables or "Mark_infor" in variables),
        "channel_count": _shape_second_dim(variables.get("d", "")),
        "source_count": "",
        "detector_count": "",
        "wavelengths": "unknown_from_header_probe",
    }


def _shape_second_dim(shape: str) -> int | str:
    parts = [part for part in shape.split("x") if part]
    if len(parts) >= 2:
        try:
            return int(parts[1])
        except ValueError:
            return ""
    return ""
