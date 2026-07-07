#!/usr/bin/env python3
"""Summarize traditional and deep EEG v1 baselines into one markdown report."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


V1_ROOT = Path("/home/qiangminc/codes/data4_qiangminc/code/chongqing/experiments/v1")
EEG_ROOT = V1_ROOT / "eeg"
TRADITIONAL_METRICS = EEG_ROOT / "artifacts" / "results" / "rest_primary_metrics.csv"
DEEP_RESULTS = EEG_ROOT / "artifacts" / "deep" / "results"
WINDOW_DIR = EEG_ROOT / "artifacts" / "deep" / "windows"
REPORT_DIR = EEG_ROOT / "reports"
REST_REPORT = REPORT_DIR / "eeg_rest_baseline_report.md"
OUT_REPORT = REPORT_DIR / "eeg_deep_baseline_report.md"

METRIC_COLS = [
    "auroc",
    "auprc",
    "balanced_accuracy",
    "sensitivity",
    "specificity",
    "f1",
    "brier",
]


def load_traditional() -> pd.DataFrame:
    if not TRADITIONAL_METRICS.exists():
        return pd.DataFrame()
    df = pd.read_csv(TRADITIONAL_METRICS)
    df = df[df["fold"].astype(str) == "overall_oof"].copy()
    df = df[df["model"] != "demographics_only_logreg"].copy()
    df.insert(0, "task", "rest")
    df.insert(1, "family", "traditional_features")
    df = df.rename(columns={"n": "n_subjects"})
    return df


def load_deep() -> pd.DataFrame:
    rows = []
    for path in sorted(DEEP_RESULTS.glob("*/*/metrics.csv")):
        df = pd.read_csv(path)
        df.insert(1, "family", "deep_windows")
        rows.append(df)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def parse_demographics_baseline() -> pd.DataFrame:
    if not REST_REPORT.exists():
        return pd.DataFrame()
    lines = REST_REPORT.read_text(encoding="utf-8").splitlines()
    row = next((line for line in lines if line.strip().startswith("| demographics_only_logreg ")), "")
    if not row:
        return pd.DataFrame()
    header = next((line for line in lines if line.strip().startswith("| model") and "fold" in line and "auroc" in line), "")
    if not header:
        return pd.DataFrame()
    cols = [part.strip() for part in header.strip().strip("|").split("|")]
    vals = [part.strip() for part in row.strip().strip("|").split("|")]
    if len(cols) != len(vals):
        return pd.DataFrame()
    out = pd.DataFrame([dict(zip(cols, vals, strict=False))])
    out.insert(0, "task", "rest")
    out.insert(1, "family", "demographics_sanity")
    out = out.rename(columns={"n": "n_subjects"})
    for col in ["n_subjects", "threshold", *METRIC_COLS, "tn", "fp", "fn", "tp"]:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    return out


def window_inventory() -> pd.DataFrame:
    rows = []
    for task in ["rest", "oddball", "1back"]:
        meta_path = WINDOW_DIR / f"metadata_{task}.csv"
        if not meta_path.exists():
            rows.append({"task": task, "subjects": 0, "windows": 0, "label_counts": "missing", "event_counts": "missing"})
            continue
        meta = pd.read_csv(meta_path, dtype={"L_id": str})
        label_counts = meta.groupby("L_id")["label"].first().value_counts().sort_index().to_dict()
        event_counts = {}
        if "event_code" in meta:
            events = meta["event_code"].dropna().astype(str)
            events = events[events.str.len() > 0]
            event_counts = events.value_counts().to_dict()
        rows.append(
            {
                "task": task,
                "subjects": int(meta["L_id"].nunique()),
                "windows": int(len(meta)),
                "label_counts": str(label_counts),
                "event_counts": str(event_counts),
            }
        )
    return pd.DataFrame(rows)


def fold_mean_std(deep: pd.DataFrame) -> pd.DataFrame:
    if deep.empty:
        return pd.DataFrame()
    folds = deep[deep["fold"].astype(str) != "overall_oof"].copy()
    if folds.empty:
        return pd.DataFrame()
    summaries = []
    for (task, model), group in folds.groupby(["task", "model"]):
        row = {"task": task, "model": model, "folds": int(group["fold"].nunique())}
        for col in ["auroc", "auprc", "balanced_accuracy", "f1", "brier"]:
            row[f"{col}_mean"] = group[col].mean()
            row[f"{col}_std"] = group[col].std(ddof=1)
        summaries.append(row)
    return pd.DataFrame(summaries)


def comparable_overall(traditional: pd.DataFrame, deep: pd.DataFrame, demographics: pd.DataFrame) -> pd.DataFrame:
    frames = []
    for df in [traditional, deep, demographics]:
        if df.empty:
            continue
        overall = df[df["fold"].astype(str) == "overall_oof"].copy() if "fold" in df else df.copy()
        frames.append(overall)
    if not frames:
        return pd.DataFrame()
    cols = ["family", "task", "model", "n_subjects", *METRIC_COLS, "tn", "fp", "fn", "tp"]
    combined = pd.concat(frames, ignore_index=True)
    for col in cols:
        if col not in combined:
            combined[col] = pd.NA
    return combined[cols].sort_values(["family", "task", "model"]).reset_index(drop=True)


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    traditional = load_traditional()
    deep = load_deep()
    demographics = parse_demographics_baseline()
    overall = comparable_overall(traditional, deep, demographics)
    folds = fold_mean_std(deep)
    inventory = window_inventory()

    with OUT_REPORT.open("w", encoding="utf-8") as f:
        f.write("# EEG Deep Baseline Report\n\n")
        f.write("## Scope\n\n")
        f.write(
            "This report summarizes anonymous cached-window EEG deep baselines for Rest, Oddball, and 1BACK. "
            "Predictions are trained at the window level and evaluated after subject-level aggregation. "
            "Raw BDF files remain in the original dataset directory and are not copied here.\n\n"
        )
        f.write("## Cached Window Inventory\n\n")
        f.write(inventory.to_markdown(index=False))
        f.write("\n\n")
        if not overall.empty:
            f.write("## Overall Out-of-Fold Comparison\n\n")
            f.write(overall.to_markdown(index=False, floatfmt=".4f"))
            f.write("\n\n")
        if not folds.empty:
            f.write("## Deep Fold Mean/Std\n\n")
            f.write(folds.to_markdown(index=False, floatfmt=".4f"))
            f.write("\n\n")
        f.write("## QA Notes\n\n")
        f.write("- All deep outputs use `L_id` only; names and clinical scale columns are not model features.\n")
        f.write("- Every deep model writes `cv_splits.csv`; train/test overlap checks should be performed on `L_id` per fold.\n")
        f.write("- The demographics-only sanity baseline is included when parseable from the traditional Rest report.\n")
        f.write("- If deep EEG performance is not above the demographics-only baseline, this v1 result should be treated as a baseline rather than evidence of diagnostic validity.\n")
    print(OUT_REPORT)


if __name__ == "__main__":
    main()
