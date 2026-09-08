"""Goal 2.8 reports.

The decision rests on one question per modality: does the objective signal add
anything over demographics, with a paired bootstrap interval that excludes zero,
under both CV protocols. Everything else is context.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from .config import ensure_output, load_goal_config, project_path

# Only an increment over demographics can establish independent signal. Beating
# a background or QC baseline shows the modality carries more than the room or
# the recording conditions, which is a shortcut control, not evidence that the
# signal adds anything a questionnaire does not already supply.
DEMOGRAPHIC_INCREMENTS = [
    ("signal", "demographics"),
    ("signal_demographics", "demographics"),
    ("signal_qc_demographics", "qc_demographics"),
    ("signal_qc_demographics", "demographics"),
    ("face", "demographics"),
    ("face_demographics", "demographics"),
]

# Supportive but not decisive.
SHORTCUT_CONTROLS = [
    ("face", "background"),
    ("face_demographics", "background_demographics"),
]

REQUIRED_INCREMENTS = DEMOGRAPHIC_INCREMENTS + SHORTCUT_CONTROLS


def _markdown(frame: pd.DataFrame, limit: int = 60) -> str:
    if frame.empty:
        return "_No rows._"
    data = frame.head(limit).copy()
    for col in data.columns:
        if pd.api.types.is_float_dtype(data[col]):
            data[col] = data[col].map(lambda v: "" if pd.isna(v) else f"{v:.4f}")
    data = data.fillna("").astype(str)
    lines = ["| " + " | ".join(data.columns) + " |",
             "| " + " | ".join(["---"] * len(data.columns)) + " |"]
    for _, row in data.iterrows():
        lines.append("| " + " | ".join(str(row[c]).replace("|", "/") for c in data.columns) + " |")
    if len(frame) > limit:
        lines.append(f"\nShowing {limit} of {len(frame)} rows.")
    return "\n".join(lines)


def _load(config: dict[str, Any], key: str) -> pd.DataFrame:
    path = project_path(config["outputs"][key])
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def required_increment_table(paired: pd.DataFrame) -> pd.DataFrame:
    if paired.empty:
        return pd.DataFrame()
    wanted = {f"{a}_vs_{b}" for a, b in REQUIRED_INCREMENTS}
    frame = paired.copy()
    if "comparison" not in frame.columns:
        frame["comparison"] = frame["feature_set_a"].astype(str) + "_vs_" + frame["feature_set_b"].astype(str)
    frame = frame[frame["comparison"].isin(wanted)].copy()
    if frame.empty:
        return frame
    lo = next((c for c in frame.columns if c.startswith("auroc") and c.endswith("ci_low")), None)
    hi = next((c for c in frame.columns if c.startswith("auroc") and c.endswith("ci_high")), None)
    diff = next((c for c in frame.columns if c.startswith("auroc") and "diff" in c and "ci" not in c), None)
    if lo and hi:
        frame["significant_positive"] = (frame[lo] > 0).astype(int)
        frame["significant_negative"] = (frame[hi] < 0).astype(int)
    keep = [c for c in ["cv_protocol", "cohort_name", "modality", "device", "task", "model",
                        "comparison", diff, lo, hi, "significant_positive", "significant_negative"]
            if c and c in frame.columns]
    return frame[keep].sort_values([c for c in ["cv_protocol", "modality", "cohort_name"] if c in keep])


def modality_decision(required: pd.DataFrame) -> pd.DataFrame:
    """Decide each modality.

    `INDEPENDENT_SIGNAL_SUPPORTED` requires a positive increment **over
    demographics** under both CV protocols. Wins over background or QC are
    counted and reported separately, because they cannot establish that the
    modality adds anything beyond what demographics already predict.
    """
    if required.empty or "significant_positive" not in required.columns:
        return pd.DataFrame()
    demo_names = {f"{a}_vs_{b}" for a, b in DEMOGRAPHIC_INCREMENTS}
    rows = []
    for modality, group in required.groupby("modality"):
        demo = group[group["comparison"].isin(demo_names)]
        shortcut = group[~group["comparison"].isin(demo_names)]
        per_protocol = {
            protocol: int(sub["significant_positive"].sum())
            for protocol, sub in demo.groupby("cv_protocol")
        }
        both = all(per_protocol.get(p, 0) > 0 for p in ("standard_cv", "group_cv"))
        rows.append({
            "modality": modality,
            "demographic_increment_rows": int(len(demo)),
            "positive_over_demographics_standard_cv": per_protocol.get("standard_cv", 0),
            "positive_over_demographics_group_cv": per_protocol.get("group_cv", 0),
            "negative_over_demographics": int(demo["significant_negative"].sum())
            if "significant_negative" in demo else 0,
            "positive_over_shortcut_controls": int(shortcut["significant_positive"].sum()),
            "decision": "INDEPENDENT_SIGNAL_SUPPORTED" if both else "NO_INDEPENDENT_SIGNAL",
        })
    return pd.DataFrame(rows)


def best_rows(pooled: pd.DataFrame) -> pd.DataFrame:
    if pooled.empty:
        return pooled
    frame = pooled.copy()
    if "threshold_type" in frame.columns:
        frame = frame[frame["threshold_type"].astype(str) == "inner_cv"]
    keep = ["cv_protocol", "modality", "cohort_name", "device", "task", "feature_set", "model",
            "n_subjects", "auroc", "auprc"]
    keep = [c for c in keep if c in frame.columns]
    idx = frame.groupby([c for c in ["cv_protocol", "cohort_name", "feature_set"] if c in frame.columns])["auroc"].idxmax()
    return frame.loc[idx, keep].sort_values(["cv_protocol", "modality", "cohort_name", "feature_set"])


def build_reports(config_path: str | Path = "configs/goal2_8/models.yaml") -> dict[str, Any]:
    config = load_goal_config(config_path)
    pooled = _load(config, "all_pooled_metrics")
    paired = _load(config, "paired_comparisons")

    required = required_increment_table(paired)
    decision = modality_decision(required)
    best = best_rows(pooled)

    reports_dir = Path(ensure_output("reports/.keep", config)).parent
    results_dir = Path(ensure_output(config["outputs"]["all_pooled_metrics"], config)).parent
    required.to_csv(results_dir / "required_increments.csv", index=False)
    decision.to_csv(results_dir / "modality_decision.csv", index=False)

    positive = required[required.get("significant_positive", 0) == 1] if not required.isna().all().all() else pd.DataFrame()
    lines = [
        "# Goal 2.8 Results",
        "",
        "Goal 2.8 rebuilt every feature layer from the paradigm specification and reran the",
        "Goal 2.7 protocol unchanged: the same fixed folds, the same inner-CV selection, the",
        "same model families, the same 1000-resample bootstrap. Only the features are new.",
        "",
        "Bikom is excluded from the primary matrix. Its cohort is disjoint from Yiruid's",
        "(one shared subject), so device cannot be separated from acquisition site, and its",
        "features carry no univariate label signal.",
        "",
        "## Modality Decision",
        "",
        _markdown(decision),
        "",
        "A modality is only credited with independent signal when an increment **over",
        "demographics** has a paired bootstrap AUROC interval excluding zero under **both** CV",
        "protocols. Beating a background or QC baseline is reported separately: it shows the",
        "modality carries more than the room or the recording conditions, not that it adds",
        "anything a questionnaire does not already supply.",
        "",
        "## Required Increments",
        "",
        f"Positive and significant: **{int(required.get('significant_positive', pd.Series(dtype=int)).sum())}** of {len(required)} rows.",
        f"Negative and significant: **{int(required.get('significant_negative', pd.Series(dtype=int)).sum())}**.",
        "",
        _markdown(positive if not positive.empty else required, limit=40),
        "",
        "## Best Row Per Feature Set",
        "",
        _markdown(best, limit=80),
    ]
    report_path = reports_dir / "goal2_8_results.md"
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    manifest = {
        "pooled_rows": int(len(pooled)),
        "paired_rows": int(len(paired)),
        "required_rows": int(len(required)),
        "positive_required": int(required.get("significant_positive", pd.Series(dtype=int)).sum()),
        "decision": decision.to_dict(orient="records"),
        "report": str(report_path),
    }
    (results_dir / "report_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest
