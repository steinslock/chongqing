"""Goal 2.9 model matrix over the behavioural features.

The protocol is unchanged from Goal 2.7 and Goal 2.8: the same fixed Standard
and Group-aware folds, three-fold inner CV for hyperparameters and thresholds,
the same three model families and grids, the same 1000-resample subject
bootstrap and paired increment tests, and the same pilot-holdout exclusion. Only
the features are new, so only dataset construction lives here.

Feature sets keep the `signal` / `qc` / `demographics` vocabulary, which makes
the existing paired-comparison pairs and the Goal 2.8 decision rule apply
without modification.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from ..goal2_7.runner import (
    GoalDataset,
    _bootstrap_table,
    _combine_signal_qc,
    _datasets_for_protocol,
    _feature_counts,
    _merge_protocol_results,
    _native_summary,
    _paired_comparisons,
    _pooled_metrics,
    _standard_feature_sets,
    _standard_vs_group,
    _threshold_diagnostics,
    run_datasets,
)
from ..goal2_8.runner import _run_parallel
from .config import ensure_output, load_goal_config, project_path


def _read(path: Path) -> pd.DataFrame | None:
    return pd.read_csv(path, dtype={"L_id": str}) if path.exists() else None


def _unit_frames(config: dict[str, Any], device: str, task: str
                 ) -> tuple[pd.DataFrame, pd.DataFrame] | None:
    behaviour_dir = project_path(config["paths"]["behaviour_dir"])
    signal = _read(behaviour_dir / f"{device}_{task}_signal_features.csv")
    qc = _read(behaviour_dir / f"{device}_{task}_qc_features.csv")
    if signal is None or qc is None:
        return None
    return signal, qc


def build_task_datasets(config: dict[str, Any]) -> list[GoalDataset]:
    """One cohort per device/task, with the standard feature-set battery."""
    out: list[GoalDataset] = []
    for device, task in _units(config):
        frames = _unit_frames(config, device, task)
        if frames is None:
            continue
        signal, qc = frames
        cohort = _combine_signal_qc(signal, qc, config, "behaviour", device, task)
        if cohort.empty:
            continue
        out.extend(_standard_feature_sets(cohort, "behaviour", device, task,
                                          f"behaviour_{device}_{task}_native", config, "tabular"))
    return out


def build_combined_datasets(config: dict[str, Any]) -> list[GoalDataset]:
    """One cohort per device holding every behavioural task that device ran.

    A subject's working memory, attention and reward measures are separate
    facets of the same behaviour, and the tasks were run in one session. Joining
    them costs the subjects who are missing a task, which is why the per-task
    cohorts stay in the matrix alongside.
    """
    out: list[GoalDataset] = []
    for device, tasks in _combined_units(config).items():
        signal_parts: list[pd.DataFrame] = []
        qc_parts: list[pd.DataFrame] = []
        for task in tasks:
            frames = _unit_frames(config, device, task)
            if frames is None:
                continue
            signal, qc = frames
            signal_cols = [c for c in signal.columns if c.startswith("signal_")]
            qc_cols = [c for c in qc.columns if c.startswith("qc_")]
            signal_parts.append(signal[["L_id", *signal_cols]].rename(
                columns={c: f"signal_{task}_{c[len('signal_'):]}" for c in signal_cols}))
            qc_parts.append(qc[["L_id", *qc_cols]].rename(
                columns={c: f"qc_{task}_{c[len('qc_'):]}" for c in qc_cols}))
        if len(signal_parts) < 2:
            continue
        signal_all = signal_parts[0]
        for part in signal_parts[1:]:
            signal_all = signal_all.merge(part, on="L_id", how="inner")
        qc_all = qc_parts[0]
        for part in qc_parts[1:]:
            qc_all = qc_all.merge(part, on="L_id", how="inner")
        signal_all["feature_version"] = "goal2_9_behaviour_combined_v1"
        cohort = _combine_signal_qc(signal_all, qc_all, config, "behaviour", device, "combined")
        if cohort.empty:
            continue
        out.extend(_standard_feature_sets(cohort, "behaviour", device, "combined",
                                          f"behaviour_{device}_combined_native", config, "tabular"))
    return out


def _units(config: dict[str, Any]) -> list[tuple[str, str]]:
    return [(str(u["device"]), str(u["task"])) for u in config["goal2_9"]["units"]]


def _combined_units(config: dict[str, Any]) -> dict[str, list[str]]:
    return {str(k): [str(t) for t in v]
            for k, v in (config["goal2_9"].get("combined_units") or {}).items()}


def build_datasets(config: dict[str, Any]) -> list[GoalDataset]:
    datasets = build_task_datasets(config)
    if config["goal2_9"].get("include_combined", True):
        datasets.extend(build_combined_datasets(config))
    return datasets


def write_outputs(results: dict[str, Any], datasets: list[GoalDataset], config: dict[str, Any]) -> None:
    outputs = config["outputs"]
    predictions = results["predictions"]
    for protocol, key in (("standard_cv", "all_oof_predictions_standard_cv"),
                          ("group_cv", "all_oof_predictions_group_cv")):
        predictions[predictions.get("cv_protocol", "") == protocol].to_csv(
            ensure_output(outputs[key], config), index=False)
    for key, name in (("fold_metrics", "all_fold_metrics"), ("pooled_metrics", "all_pooled_metrics"),
                      ("bootstrap", "bootstrap_ci"), ("paired", "paired_comparisons"),
                      ("hyperparameters", "selected_hyperparameters"), ("pca", "pca_diagnostics")):
        value = results.get(key)
        if isinstance(value, pd.DataFrame):
            value.to_csv(ensure_output(outputs[name], config), index=False)
    _feature_counts(datasets).to_csv(ensure_output(outputs["feature_counts"], config), index=False)
    _native_summary(results["pooled_metrics"]).to_csv(
        ensure_output(outputs["native_cohort_summary"], config), index=False)
    _standard_vs_group(results["pooled_metrics"]).to_csv(
        ensure_output(outputs["standard_vs_group_cv"], config), index=False)
    _threshold_diagnostics(results["predictions"], results["fold_metrics"]).to_csv(
        ensure_output(outputs["threshold_diagnostics"], config), index=False)

    manifest = {
        "stage": config["run"]["stage"],
        "n_datasets": len(datasets),
        "n_prediction_rows": int(len(results["predictions"])),
        "n_pooled_rows": int(len(results["pooled_metrics"])),
        "units": [f"{d}_{t}" for d, t in _units(config)],
        "combined_units": _combined_units(config),
        "cv_protocols": list(config["protocol"].get("cv_protocols", {})),
        "outputs": {k: str(project_path(v)) for k, v in outputs.items()},
    }
    ensure_output(outputs["manifest"], config).write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")


def run_goal2_9(config_path: str | Path = "configs/goal2_9/models.yaml",
                include_supplemental: bool = True,
                n_workers: int | None = None) -> dict[str, Any]:
    config = load_goal_config(config_path)
    base = build_datasets(config)
    standard = _datasets_for_protocol(base, config, "standard_cv")
    group = _datasets_for_protocol(base, config, "group_cv")
    workers = int(n_workers if n_workers is not None else config.get("run", {}).get("dataset_workers", 12))
    results = _merge_protocol_results(
        _run_parallel(standard, config, workers),
        _run_parallel(group, config, workers),
    )
    results["pooled_metrics"] = _pooled_metrics(results["predictions"], config)
    if include_supplemental:
        results["bootstrap"] = _bootstrap_table(results["predictions"], config)
        results["paired"] = _paired_comparisons(results["predictions"], config)
    write_outputs(results, standard + group, config)
    return {
        "datasets": len(standard) + len(group),
        "pooled_metrics": int(len(results["pooled_metrics"])),
        "predictions": int(len(results["predictions"])),
        "paired_rows": int(len(results.get("paired", pd.DataFrame()))),
    }


__all__ = ["build_datasets", "build_combined_datasets", "build_task_datasets", "run_goal2_9",
           "run_datasets"]
