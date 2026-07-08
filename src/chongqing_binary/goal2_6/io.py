"""Shared data loading helpers for Goal 2.6."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from .config import project_path


def load_split(config: dict[str, Any]) -> pd.DataFrame:
    label_col = config.get("run", {}).get("label_column", "primary_label_nonhealthy")
    path = project_path(config["paths"]["split_file"])
    df = pd.read_csv(path, dtype={"A_id": str, "L_id": str, "cv_fold": "Int64"})
    df[label_col] = pd.to_numeric(df[label_col], errors="coerce")
    df = df[df[label_col].isin([0, 1])].copy()
    df[label_col] = df[label_col].astype(int)
    df["split_group"] = df["split_group"].astype(str)
    return df


def cv_subjects(config: dict[str, Any]) -> pd.DataFrame:
    split_group = str(config.get("run", {}).get("split_group", "cv"))
    df = load_split(config)
    return df[df["split_group"] == split_group].copy().reset_index(drop=True)


def add_clean_demographics(frame: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
    out = frame.copy()
    demo = config.get("demographics", {})
    age_min = float(demo.get("age_min", 9))
    age_max = float(demo.get("age_max", 20))
    age = pd.to_numeric(out.get("age"), errors="coerce")
    out["age_clean"] = age.where(age.between(age_min, age_max))
    for src, dst in [("sex", "sex_clean"), ("grade", "grade_clean"), ("grade_group", "grade_group_clean")]:
        values = out.get(src)
        if values is None:
            out[dst] = pd.NA
        else:
            out[dst] = values.astype("string").str.strip().replace({"": pd.NA, "nan": pd.NA, "None": pd.NA})
    return out


def split_metadata_columns() -> list[str]:
    return [
        "A_id",
        "L_id",
        "primary_label_nonhealthy",
        "split_group",
        "split_role",
        "is_locked_test",
        "cv_fold",
        "sex",
        "age",
        "grade",
        "grade_group",
        "fnirs_device",
    ]


def merge_cv_metadata(features: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
    split = cv_subjects(config)
    keep = [col for col in split_metadata_columns() if col in split.columns]
    merged = split[keep].merge(features, on="L_id", how="inner", suffixes=("", "_feature"))
    return merged.sort_values("L_id").reset_index(drop=True)


def read_csv_flexible(path: str | Path, **kwargs: Any) -> pd.DataFrame:
    resolved = project_path(path)
    try:
        return pd.read_csv(resolved, encoding="utf-8-sig", **kwargs)
    except UnicodeDecodeError:
        return pd.read_csv(resolved, encoding="gb18030", **kwargs)

