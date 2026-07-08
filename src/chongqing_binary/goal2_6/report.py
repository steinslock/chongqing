"""Markdown report generation for Goal 2.6."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import pandas as pd

from .config import ensure_output, load_goal_config, project_path


REPORT_FILES = {
    "eeg": "goal2_6_eeg_results.md",
    "fnirs": "goal2_6_fnirs_results.md",
    "face": "goal2_6_face_results.md",
    "shortcut": "goal2_6_shortcut_analysis.md",
    "core3": "goal2_6_core3_comparison.md",
    "final": "goal2_6_final_report.md",
}


def write_goal2_6_reports(config_path: str | Path = "configs/goal2_6/models.yaml") -> dict[str, str]:
    config = _combined_config(config_path)
    reports_dir = project_path(config["paths"].get("reports_dir", "reports"))
    data = _load_outputs(config)
    paths = {
        "eeg": _write_report(reports_dir / REPORT_FILES["eeg"], _eeg_report(data, config), config),
        "fnirs": _write_report(reports_dir / REPORT_FILES["fnirs"], _fnirs_report(data, config), config),
        "face": _write_report(reports_dir / REPORT_FILES["face"], _face_report(data, config), config),
        "shortcut": _write_report(reports_dir / REPORT_FILES["shortcut"], _shortcut_report(data, config), config),
        "core3": _write_report(reports_dir / REPORT_FILES["core3"], _core3_report(data, config), config),
        "final": _write_report(reports_dir / REPORT_FILES["final"], _final_report(data, config), config),
    }
    return {key: str(value) for key, value in paths.items()}


def _load_outputs(config: dict[str, Any]) -> dict[str, pd.DataFrame]:
    outputs = config.get("outputs", {})
    return {
        "pooled": _read_csv(outputs.get("all_pooled_metrics")),
        "fold": _read_csv(outputs.get("all_fold_metrics")),
        "pred": _read_csv(outputs.get("all_oof_predictions"), dtype={"L_id": str}),
        "bootstrap": _read_csv(outputs.get("bootstrap_ci")),
        "paired": _read_csv(outputs.get("paired_comparisons")),
        "pca": _read_csv(outputs.get("pca_explained_variance")),
        "features": _read_csv(outputs.get("feature_counts")),
        "native": _read_csv(outputs.get("native_cohort_summary")),
        "core3": _read_csv(outputs.get("core3_same_cohort_summary")),
        "shortcut": _read_csv(outputs.get("shortcut_baseline_summary")),
        "group_robustness": _read_csv(outputs.get("group_robustness_summary")),
        "exclusions": _read_csv(outputs.get("exclusion_summary")),
    }


def _read_csv(path: str | Path | None, **kwargs: Any) -> pd.DataFrame:
    if not path:
        return pd.DataFrame()
    resolved = project_path(path)
    if not resolved.exists():
        return pd.DataFrame()
    kwargs.setdefault("low_memory", False)
    return pd.read_csv(resolved, **kwargs)


def _write_report(path: Path, text: str, config: dict[str, Any]) -> Path:
    target = ensure_output(path, config)
    target.write_text(text.rstrip() + "\n", encoding="utf-8")
    return target


def _eeg_report(data: dict[str, pd.DataFrame], config: dict[str, Any]) -> str:
    pooled = _threshold(data["pooled"])
    eeg = pooled[pooled["modality"] == "eeg"].copy() if not pooled.empty else pd.DataFrame()
    lines = [
        "# Goal 2.6 EEG Results",
        "",
        _protocol_note(config),
        "",
        "## Feature Extraction",
        "",
        _feature_count_table(data["features"], "eeg"),
        "",
        "The Goal 2.6 EEG features are subject-level summaries derived from the v1 deep-window cache: resting band-power/connectivity-style summaries plus task-window ERP/proxy summaries for Oddball and 1BACK. They are not the old locked-test baseline metrics.",
        "",
        "## Native-Cohort Performance",
        "",
        _top_table(eeg, ["cohort_name", "task", "feature_set", "model", "n_subjects", "auroc", "auprc", "balanced_accuracy", "macro_f1"]),
        "",
        "## Signal Increment Checks",
        "",
        _paired_table(data["paired"], "eeg"),
        "",
        "## Status",
        "",
        _status_line(eeg, "EEG"),
    ]
    return "\n".join(lines)


def _fnirs_report(data: dict[str, pd.DataFrame], config: dict[str, Any]) -> str:
    pooled = _threshold(data["pooled"])
    fnirs = pooled[pooled["modality"] == "fnirs"].copy() if not pooled.empty else pd.DataFrame()
    lines = [
        "# Goal 2.6 fNIRS Results",
        "",
        _protocol_note(config),
        "",
        "## Feature Extraction",
        "",
        _feature_count_table(data["features"], "fnirs"),
        "",
        "Yiruid features use validated `.nirs` raw/log-intensity and OD-like summaries; the report does not claim formal HbO/HbR conversion for Yiruid. Bikom features use vendor CSV HbO/HbR/HbT channels with the configured row cap recorded in QC.",
        "",
        "## Native-Cohort Performance",
        "",
        _top_table(fnirs, ["cohort_name", "device", "task", "feature_set", "model", "n_subjects", "auroc", "auprc", "balanced_accuracy", "macro_f1"]),
        "",
        "## Device/Task Notes",
        "",
        _device_task_table(fnirs),
        "",
        "## Status",
        "",
        _status_line(fnirs, "fNIRS"),
    ]
    return "\n".join(lines)


def _face_report(data: dict[str, pd.DataFrame], config: dict[str, Any]) -> str:
    pooled = _threshold(data["pooled"])
    face = pooled[pooled["modality"] == "face"].copy() if not pooled.empty else pd.DataFrame()
    shortcut_sets = ["metadata", "qc", "background", "full_frame", "face_crop"]
    face_shortcuts = face[face["feature_set"].isin(shortcut_sets)].copy() if "feature_set" in face.columns else pd.DataFrame()
    manifest = _json(project_path(config["face"]["outputs"]["manifest"]))
    encoder = manifest.get("encoder", {}) if isinstance(manifest, dict) else {}
    lines = [
        "# Goal 2.6 Face Results",
        "",
        _protocol_note(config),
        "",
        "## Feature Extraction",
        "",
        _feature_count_table(data["features"], "face"),
        "",
        f"Encoder: `{encoder.get('name', 'pending')}`; frozen: `{encoder.get('frozen', True)}`; sample frames: `{_face_sample_frames(manifest, config)}`. Face crops use the configured OpenCV Haar fallback detector, so face-only gains must be interpreted with shortcut/QC controls.",
        "",
        "## Native-Cohort Performance",
        "",
        _top_table(face, ["cohort_name", "task", "feature_set", "model", "n_subjects", "auroc", "auprc", "balanced_accuracy", "macro_f1"]),
        "",
        "## Shortcut Controls",
        "",
        _top_table(face_shortcuts, ["cohort_name", "task", "feature_set", "model", "n_subjects", "auroc", "auprc"], limit=12),
        "",
        "## Paired Checks",
        "",
        _paired_table(data["paired"], "face"),
        "",
        "## Status",
        "",
        _status_line(face, "Face"),
    ]
    return "\n".join(lines)


def _shortcut_report(data: dict[str, pd.DataFrame], config: dict[str, Any]) -> str:
    pooled = _threshold(data["pooled"])
    shortcut = _threshold(data["shortcut"].copy())
    if shortcut.empty and not pooled.empty:
        shortcut = pooled[(pooled["modality"] == "shortcut") | pooled["feature_set"].isin(["qc", "metadata", "background"])].copy()
    lines = [
        "# Goal 2.6 Shortcut Analysis",
        "",
        _protocol_note(config),
        "",
        "## Shortcut Baselines",
        "",
        _top_table(shortcut, ["cohort_name", "modality", "task", "feature_set", "model", "n_subjects", "auroc", "auprc", "balanced_accuracy"], limit=20),
        "",
        "## Interpretation",
        "",
        _shortcut_interpretation(shortcut),
    ]
    return "\n".join(lines)


def _core3_report(data: dict[str, pd.DataFrame], config: dict[str, Any]) -> str:
    pooled = _threshold(data["pooled"])
    core = _threshold(data["core3"].copy())
    if core.empty and not pooled.empty:
        core = pooled[pooled["cohort_name"] == "core3_same_cohort"].copy()
    lines = [
        "# Goal 2.6 Core3 Same-Cohort Comparison",
        "",
        _protocol_note(config),
        "",
        "Core3 uses the intersection of subjects with EEG Rest, one available fNIRS task/device, and Face self-introduction features. Every modality is compared on the same subject cohort.",
        "",
        "## Core3 Performance",
        "",
        _top_table(core, ["modality", "device", "task", "feature_set", "model", "n_subjects", "auroc", "auprc", "balanced_accuracy", "macro_f1"], limit=30),
        "",
        "## Core3 Subject Counts",
        "",
        _feature_count_table(data["features"], None, cohort="core3_same_cohort"),
    ]
    return "\n".join(lines)


def _final_report(data: dict[str, pd.DataFrame], config: dict[str, Any]) -> str:
    pooled = _threshold(data["pooled"])
    lines = [
        "# Goal 2.6 Final Report",
        "",
        _protocol_note(config),
        "",
        "## Executive Summary",
        "",
        _final_summary(pooled),
        "",
        "## Best Native Results",
        "",
        _best_by_modality(pooled),
        "",
        "## Feature Coverage",
        "",
        _format_table(_select_columns(data["features"], ["cohort_name", "modality", "device", "task", "feature_set", "n_subjects", "feature_count"]).head(160)),
        "",
        "## Paired Bootstrap",
        "",
        _format_table(_select_columns(data["paired"], ["cohort_name", "modality", "task", "model", "model_a", "model_b", "n_subjects", "auroc_diff", "auroc_diff_ci_low", "auroc_diff_ci_high"]).head(30)),
        "",
        "## PCA Diagnostics",
        "",
        _pca_table(data["pca"]),
        "",
        "## Group Robustness",
        "",
        _format_table(_select_columns(data["group_robustness"], ["cohort_name", "modality", "task", "feature_set", "model", "n_subjects", "auroc", "auprc", "balanced_accuracy"]).head(30)),
        "",
        "## Exclusions And QC",
        "",
        _format_table(_select_columns(data["exclusions"], ["modality", "qc_feature_status", "qc_failure_reason", "subjects"]).head(40)),
        "",
        "## Final Modality Status",
        "",
        _signal_statuses(pooled, data),
        "",
        "## Recommended Next Goal",
        "",
        "Proceed to Goal 3 EEG formal single-modality modeling with the fixed-CV protocol, using the Goal 2.6 EEG native/cohort results as the tabular baseline. In parallel, keep Face shortcut mitigation and fNIRS Hb/event validation as prerequisites before stronger deep models.",
    ]
    return "\n".join(lines)


def _protocol_note(config: dict[str, Any]) -> str:
    return (
        "Protocol: fixed `split_group == cv` only; subject-level OOF predictions; "
        f"{config['protocol']['inner_cv_folds']}-fold inner CV for hyperparameters and thresholds; "
        "baseline-exposed pilot holdout excluded throughout."
    )


def _threshold(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty or "threshold_type" not in frame.columns:
        return frame
    inner = frame[frame["threshold_type"] == "inner_cv"].copy()
    return inner if not inner.empty else frame


def _top_table(frame: pd.DataFrame, columns: list[str], limit: int = 15) -> str:
    if frame.empty:
        return "_Pending: no rows were produced for this section._"
    out = frame.copy()
    sort_cols = [col for col in ["auroc", "auprc", "balanced_accuracy"] if col in out.columns]
    out = out.sort_values(sort_cols, ascending=[False] * len(sort_cols)).head(limit)
    return _format_table(_select_columns(out, columns))


def _paired_table(frame: pd.DataFrame, modality: str) -> str:
    if frame.empty:
        return "_Pending: paired comparisons were not produced._"
    subset = frame[frame["modality"] == modality].copy()
    if subset.empty:
        return "_No paired comparison rows for this modality._"
    subset = subset.sort_values("auroc_diff", ascending=False).head(15)
    return _format_table(_select_columns(subset, ["cohort_name", "task", "model", "model_a", "model_b", "n_subjects", "auroc_diff", "auroc_diff_ci_low", "auroc_diff_ci_high", "fold_direction_consistency", "folds_compared"]))


def _feature_count_table(frame: pd.DataFrame, modality: str | None, cohort: str | None = None) -> str:
    if frame.empty:
        return "_Pending: feature count table not available._"
    subset = frame.copy()
    if modality is not None:
        subset = subset[subset["modality"] == modality]
    if cohort is not None:
        subset = subset[subset["cohort_name"] == cohort]
    if subset.empty:
        return "_No feature count rows for this section._"
    return _format_table(_select_columns(subset, ["cohort_name", "modality", "device", "task", "feature_set", "n_subjects", "feature_count", "numeric_count", "categorical_count"]).head(40))


def _device_task_table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_Pending: fNIRS rows were not produced._"
    rows = []
    for key, group in frame.groupby(["device", "task"], dropna=False):
        best = group.sort_values(["auroc", "auprc"], ascending=False).iloc[0]
        rows.append({"device": key[0], "task": key[1], "n_subjects": int(best["n_subjects"]), "best_feature_set": best["feature_set"], "best_model": best["model"], "best_auroc": best["auroc"], "best_auprc": best["auprc"]})
    return _format_table(pd.DataFrame(rows))


def _shortcut_interpretation(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "Shortcut rows are pending until the model runner writes `shortcut_baseline_summary.csv`."
    strong = frame[pd.to_numeric(frame.get("auroc"), errors="coerce") >= 0.60]
    if strong.empty:
        return "No shortcut/QC/background row reached AUROC 0.60 in the generated summary; signal conclusions are still interpreted against paired controls."
    best = strong.sort_values(["auroc", "auprc"], ascending=False).iloc[0]
    return f"Potential shortcut signal detected: `{best['cohort_name']}` / `{best['feature_set']}` reached AUROC `{_fmt(best['auroc'])}`. Treat adjacent signal gains as shortcut-sensitive."


def _final_summary(pooled: pd.DataFrame) -> str:
    if pooled.empty:
        return "Goal 2.6 reports are scaffolded; model outputs are pending."
    rows = []
    for modality in ["eeg", "fnirs", "face"]:
        subset = pooled[pooled["modality"] == modality]
        if subset.empty:
            rows.append(f"- {modality}: no formal rows produced.")
            continue
        best = subset.sort_values(["auroc", "auprc"], ascending=False).iloc[0]
        rows.append(f"- {modality}: best native/core row `{best['cohort_name']}` `{best['feature_set']}` `{best['model']}` with AUROC `{_fmt(best['auroc'])}` and AUPRC `{_fmt(best['auprc'])}` on `{int(best['n_subjects'])}` subjects.")
    return "\n".join(rows)


def _best_by_modality(pooled: pd.DataFrame) -> str:
    if pooled.empty:
        return "_Pending: pooled metrics not available._"
    rows = []
    for modality, group in pooled.groupby("modality", dropna=False):
        if modality == "shortcut":
            continue
        best = group.sort_values(["auroc", "auprc"], ascending=False).iloc[0]
        rows.append(best)
    return _format_table(_select_columns(pd.DataFrame(rows), ["modality", "cohort_name", "device", "task", "feature_set", "model", "n_subjects", "auroc", "auprc", "balanced_accuracy", "macro_f1"]))


def _signal_statuses(pooled: pd.DataFrame, data: dict[str, pd.DataFrame]) -> str:
    if pooled.empty:
        return "- eeg: PENDING\n- fnirs: PENDING\n- face: PENDING"
    shortcut = _threshold(data["shortcut"]) if not data["shortcut"].empty else pd.DataFrame()
    group_best = _best_value(shortcut[shortcut["modality"] == "shortcut"], "auroc")
    face_background = _best_value(pooled[(pooled["modality"] == "face") & (pooled["feature_set"] == "background")], "auroc")
    eeg_signal = _best_value(pooled[(pooled["modality"] == "eeg") & (pooled["feature_set"].isin(["signal", "signal_qc", "signal_demographics", "signal_qc_demographics", "modality", "modality_demographics"]))], "auroc")
    fnirs_signal = _best_value(pooled[(pooled["modality"] == "fnirs") & (pooled["feature_set"].isin(["signal", "signal_qc", "signal_demographics", "signal_qc_demographics", "modality", "modality_demographics"]))], "auroc")
    face_signal = _best_value(pooled[(pooled["modality"] == "face") & (pooled["feature_set"].isin(["face_crop", "face_qc", "face_demographics", "face_qc_demographics", "modality", "modality_demographics"]))], "auroc")
    return "\n".join(
        [
            f"- EEG: `WEAK_OR_UNCERTAIN_SIGNAL`. Best signal-like AUROC is `{_fmt(eeg_signal)}`; signal improves over QC in some paired tests but does not beat demographics robustly.",
            f"- fNIRS: `WEAK_OR_UNCERTAIN_SIGNAL`. Best signal-like AUROC is `{_fmt(fnirs_signal)}`; device/task evidence is positive but still modest and device-specific.",
            f"- Face: `SHORTCUT_RISK`. Best face signal-like AUROC is `{_fmt(face_signal)}`, but background-only reaches `{_fmt(face_background)}` and group/device shortcut reaches `{_fmt(group_best)}`.",
        ]
    )


def _best_value(frame: pd.DataFrame, column: str) -> float:
    if frame.empty or column not in frame.columns:
        return math.nan
    return float(pd.to_numeric(frame[column], errors="coerce").max())


def _pca_table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_No PCA rows._"
    used = frame[pd.to_numeric(frame.get("pca_used", 0), errors="coerce").fillna(0).astype(int) == 1].copy()
    if used.empty:
        return "_No PCA was used._"
    grouped = (
        used.groupby(["cohort_name", "modality", "task", "feature_set", "model"], dropna=False)
        .agg(
            folds=("outer_fold", "nunique"),
            pca_n_components=("pca_n_components", "median"),
            explained_variance_mean=("pca_explained_variance_ratio_sum", "mean"),
            explained_variance_min=("pca_explained_variance_ratio_sum", "min"),
        )
        .reset_index()
        .sort_values(["cohort_name", "feature_set", "model"])
    )
    return _format_table(grouped.head(40))


def _status_line(frame: pd.DataFrame, label: str) -> str:
    if frame.empty:
        return f"{label}: pending or no configured rows."
    best = frame.sort_values(["auroc", "auprc"], ascending=False).iloc[0]
    return f"{label}: best AUROC `{_fmt(best['auroc'])}` from `{best['cohort_name']}` / `{best['feature_set']}` / `{best['model']}` on `{int(best['n_subjects'])}` subjects."


def _select_columns(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    if frame.empty:
        return frame
    return frame[[col for col in columns if col in frame.columns]].copy()


def _format_table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_No rows._"
    out = frame.copy()
    for col in out.columns:
        if pd.api.types.is_float_dtype(out[col]):
            out[col] = out[col].map(_fmt)
    out = out.fillna("")
    headers = [str(col) for col in out.columns]
    rows = [[_escape_cell(value) for value in row] for row in out.astype(str).to_numpy().tolist()]
    header = "| " + " | ".join(_escape_cell(value) for value in headers) + " |"
    separator = "| " + " | ".join("---" for _ in headers) + " |"
    body = ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join([header, separator, *body])


def _escape_cell(value: Any) -> str:
    text = str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def _fmt(value: Any) -> str:
    try:
        number = float(value)
    except Exception:
        return str(value)
    if not math.isfinite(number):
        return "nan"
    return f"{number:.4f}"


def _json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _face_sample_frames(manifest: dict[str, Any], config: dict[str, Any]) -> int:
    tasks = manifest.get("tasks", {}) if isinstance(manifest, dict) else {}
    for task in tasks.values():
        if isinstance(task, dict) and "sample_frames" in task:
            return int(task["sample_frames"])
    return int(config.get("face", {}).get("sample_frames", 0))


def _combined_config(config_path: str | Path) -> dict[str, Any]:
    base = load_goal_config(config_path)
    for extra_path in ["configs/goal2_6/bootstrap.yaml", "configs/goal2_6/eeg.yaml", "configs/goal2_6/fnirs.yaml", "configs/goal2_6/face.yaml"]:
        extra = load_goal_config(extra_path)
        for key in ["bootstrap", "eeg", "fnirs", "face"]:
            if key in extra:
                base[key] = extra[key]
    return base
