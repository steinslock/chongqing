"""Goal 2.10 model matrix over the eye-tracking features.

The protocol is unchanged from Goal 2.7, 2.8 and 2.9: the same fixed Standard
and Group-aware folds, three-fold inner CV, the same model families and grids,
the same 1000-resample subject bootstrap and paired tests, the same
pilot-holdout exclusion, and the Goal 2.9 rule that a credited increment must
beat a comparator that is itself above chance. Only the features are new.

One thing here is not in the earlier goals. Free viewing carries two kinds of
feature that must not share a block: absolute per-valence measures, whose
odd-even split-half reliability is 0.68 to 0.74, and valence contrasts, of
which none of 46 reaches 0.5 on any device. Mixing 46 unreliable columns into
75 informative ones would depress the result for a reason unrelated to signal,
which this project has already measured as dilution, so they enter as separate
declared feature sets and are tested separately.
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
    _dataset,
    _datasets_for_protocol,
    _demo_categorical,
    _demo_numeric,
    _feature_counts,
    _merge_protocol_results,
    _native_summary,
    _numeric_prefixed,
    _paired_comparisons,
    _pooled_metrics,
    _standard_feature_sets,
    _standard_vs_group,
    _threshold_diagnostics,
    run_datasets,
)
from ..goal2_8.runner import _run_parallel
from .config import ensure_output, load_goal_config, project_path

CONTRAST_MARKER = "signal_contrast_"


def _read(path: Path) -> pd.DataFrame | None:
    return pd.read_csv(path, dtype={"L_id": str}, low_memory=False) if path.exists() else None


def _unit_frames(config: dict[str, Any], device: str, task: str) -> tuple[pd.DataFrame, pd.DataFrame] | None:
    eye_dir = project_path(config["paths"]["eye_dir"])
    signal = _read(eye_dir / f"{device}_{task}_signal_features.csv")
    qc = _read(eye_dir / f"{device}_{task}_qc_features.csv")
    if signal is None or qc is None:
        return None
    return signal, qc


def _contrast_split_datasets(
    cohort: pd.DataFrame,
    device: str,
    task: str,
    cohort_name: str,
    config: dict[str, Any],
) -> list[GoalDataset]:
    """Absolute and contrast blocks as separate feature sets.

    Only meaningful where both kinds exist, which is free viewing and, for the
    within-subject speed and inhibition contrasts, saccade and pursuit.
    """

    signal_cols = _numeric_prefixed(cohort, "signal_")
    contrast = [column for column in signal_cols if column.startswith(CONTRAST_MARKER)]
    absolute = [column for column in signal_cols if not column.startswith(CONTRAST_MARKER)]
    if not contrast or not absolute:
        return []
    demo_num = _demo_numeric(config)
    demo_cat = _demo_categorical(config)
    return [
        _dataset(cohort, "eye", device, task, "signal_absolute", cohort_name, absolute, [], "tabular"),
        _dataset(cohort, "eye", device, task, "signal_contrast", cohort_name, contrast, [], "tabular"),
        _dataset(
            cohort, "eye", device, task, "signal_absolute_demographics", cohort_name,
            absolute + demo_num, demo_cat, "tabular",
        ),
        _dataset(
            cohort, "eye", device, task, "signal_contrast_demographics", cohort_name,
            contrast + demo_num, demo_cat, "tabular",
        ),
    ]


def build_task_datasets(config: dict[str, Any]) -> list[GoalDataset]:
    """One cohort per device/task, with the standard battery plus the split."""

    out: list[GoalDataset] = []
    for device, task in _units(config):
        frames = _unit_frames(config, device, task)
        if frames is None:
            continue
        signal, qc = frames
        cohort = _combine_signal_qc(signal, qc, config, "eye", device, task)
        if cohort.empty:
            continue
        cohort_name = f"eye_{device}_{task}_native"
        out.extend(_standard_feature_sets(cohort, "eye", device, task, cohort_name, config, "tabular"))
        out.extend(_contrast_split_datasets(cohort, device, task, cohort_name, config))
    return out


def build_combined_datasets(config: dict[str, Any]) -> list[GoalDataset]:
    """One cohort per device holding every eye task that device ran.

    Free viewing, saccade and pursuit index different systems recorded in one
    session. Joining them costs the subjects missing a task, which is why the
    per-task cohorts stay in the matrix alongside.
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
            signal_cols = [column for column in signal.columns if column.startswith("signal_")]
            qc_cols = [column for column in qc.columns if column.startswith("qc_")]
            signal_parts.append(
                signal[["L_id", *signal_cols]].rename(
                    columns={column: _rename(column, "signal_", task) for column in signal_cols}
                )
            )
            qc_parts.append(
                qc[["L_id", *qc_cols]].rename(
                    columns={column: f"qc_{task}_{column[len('qc_'):]}" for column in qc_cols}
                )
            )
        if len(signal_parts) < 2:
            continue
        signal_all = signal_parts[0]
        for part in signal_parts[1:]:
            signal_all = signal_all.merge(part, on="L_id", how="inner")
        qc_all = qc_parts[0]
        for part in qc_parts[1:]:
            qc_all = qc_all.merge(part, on="L_id", how="inner")
        signal_all["feature_version"] = config["goal2_10"].get("combined_feature_version", "goal2_10_eye_combined_v1")
        cohort = _combine_signal_qc(signal_all, qc_all, config, "eye", device, "combined")
        if cohort.empty:
            continue
        cohort_name = f"eye_{device}_combined_native"
        out.extend(_standard_feature_sets(cohort, "eye", device, "combined", cohort_name, config, "tabular"))
        out.extend(_contrast_split_datasets(cohort, device, "combined", cohort_name, config))
    return out


def _rename(column: str, prefix: str, task: str) -> str:
    """Prefix a feature with its task, keeping `signal_contrast_` recognisable.

    The combined cohort must still be able to split absolute from contrast
    features, so the contrast marker stays at the front of the name.
    """

    body = column[len(prefix) :]
    if body.startswith("contrast_"):
        return f"{prefix}contrast_{task}_{body[len('contrast_'):]}"
    return f"{prefix}{task}_{body}"


def _units(config: dict[str, Any]) -> list[tuple[str, str]]:
    return [(str(unit["device"]), str(unit["task"])) for unit in config["goal2_10"]["units"]]


def _combined_units(config: dict[str, Any]) -> dict[str, list[str]]:
    return {
        str(key): [str(task) for task in value]
        for key, value in (config["goal2_10"].get("combined_units") or {}).items()
    }


def build_datasets(config: dict[str, Any]) -> list[GoalDataset]:
    datasets = build_task_datasets(config)
    if config["goal2_10"].get("include_combined", True):
        datasets.extend(build_combined_datasets(config))
    return datasets


def write_outputs(results: dict[str, Any], datasets: list[GoalDataset], config: dict[str, Any]) -> None:
    outputs = config["outputs"]
    predictions = results["predictions"]
    for protocol, key in (
        ("standard_cv", "all_oof_predictions_standard_cv"),
        ("group_cv", "all_oof_predictions_group_cv"),
    ):
        predictions[predictions.get("cv_protocol", "") == protocol].to_csv(
            ensure_output(outputs[key], config), index=False
        )
    for key, name in (
        ("fold_metrics", "all_fold_metrics"),
        ("pooled_metrics", "all_pooled_metrics"),
        ("bootstrap", "bootstrap_ci"),
        ("paired", "paired_comparisons"),
        ("hyperparameters", "selected_hyperparameters"),
        ("pca", "pca_diagnostics"),
    ):
        value = results.get(key)
        if isinstance(value, pd.DataFrame):
            value.to_csv(ensure_output(outputs[name], config), index=False)
    _feature_counts(datasets).to_csv(ensure_output(outputs["feature_counts"], config), index=False)
    _native_summary(results["pooled_metrics"]).to_csv(
        ensure_output(outputs["native_cohort_summary"], config), index=False
    )
    _standard_vs_group(results["pooled_metrics"]).to_csv(
        ensure_output(outputs["standard_vs_group_cv"], config), index=False
    )
    _threshold_diagnostics(results["predictions"], results["fold_metrics"]).to_csv(
        ensure_output(outputs["threshold_diagnostics"], config), index=False
    )

    manifest = {
        "stage": config["run"]["stage"],
        "n_datasets": len(datasets),
        "n_prediction_rows": int(len(results["predictions"])),
        "n_pooled_rows": int(len(results["pooled_metrics"])),
        "units": [f"{device}_{task}" for device, task in _units(config)],
        "combined_units": _combined_units(config),
        "cv_protocols": list(config["protocol"].get("cv_protocols", {})),
        "subject_key_note": (
            "Eye cohorts join on A_id; the feature tables carry L_id from the split so the shared "
            "runner, which keys on L_id, is unchanged."
        ),
        "outputs": {key: str(project_path(value)) for key, value in outputs.items()},
    }
    ensure_output(outputs["manifest"], config).write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def run_goal2_10(
    config_path: str | Path = "configs/goal2_10/models.yaml",
    include_supplemental: bool = True,
    n_workers: int | None = None,
) -> dict[str, Any]:
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


__all__ = [
    "build_combined_datasets",
    "build_datasets",
    "build_task_datasets",
    "run_datasets",
    "run_goal2_10",
]
