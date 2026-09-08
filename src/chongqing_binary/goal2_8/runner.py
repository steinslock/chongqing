"""Goal 2.8 model matrix.

Reuses the Goal 2.7 modelling machinery unchanged: outer CV over the fixed
folds, three-fold inner CV for hyperparameters and thresholds, train-fold PCA
for visual embeddings, subject bootstrap CIs and paired increment tests. Only
the dataset construction is new, because the features are new.

Feature sets are named with the Goal 2.7 vocabulary (`signal`, `face`,
`background`, ...) so the existing paired-comparison pairs apply without
modification.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
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
from .config import ensure_output, load_goal_config, project_path


def _read(path: Path) -> pd.DataFrame | None:
    return pd.read_csv(path, dtype={"L_id": str}) if path.exists() else None


def build_eeg_datasets(config: dict[str, Any]) -> list[GoalDataset]:
    out: list[GoalDataset] = []
    eeg_dir = project_path(config["paths"]["eeg_dir"])
    for task in config["goal2_8"]["eeg_tasks"]:
        signal = _read(eeg_dir / f"{task}_signal_features.csv")
        qc = _read(eeg_dir / f"{task}_qc_features.csv")
        if signal is None or qc is None:
            continue
        cohort = _combine_signal_qc(signal, qc, config, "eeg", "", task)
        if cohort.empty:
            continue
        out.extend(_standard_feature_sets(cohort, "eeg", "", task, f"eeg_{task}_native",
                                          config, "tabular"))
    return out


def build_fnirs_datasets(config: dict[str, Any]) -> list[GoalDataset]:
    out: list[GoalDataset] = []
    fnirs_dir = project_path(config["paths"]["fnirs_dir"])
    for device in config["goal2_8"]["fnirs_devices"]:
        for task in config["goal2_8"]["fnirs_tasks"]:
            signal = _read(fnirs_dir / f"{device}_{task}_signal_features.csv")
            qc = _read(fnirs_dir / f"{device}_{task}_qc_features.csv")
            if signal is None or qc is None:
                continue
            cohort = _combine_signal_qc(signal, qc, config, "fnirs", device, task)
            if cohort.empty:
                continue
            out.extend(_standard_feature_sets(cohort, "fnirs", device, task,
                                              f"fnirs_{device}_{task}_native", config, "tabular"))
    return out


def _face_frame(config: dict[str, Any], blocks: dict[str, str]) -> tuple[pd.DataFrame, dict[str, list[str]]]:
    """Materialise selected embedding blocks from the archive into one frame.

    `blocks` maps an output prefix (face / background / full) to an archive key.
    """
    face_dir = project_path(config["paths"]["face_dir"])
    archive = np.load(face_dir / "face_segment_embeddings.npz", allow_pickle=False)
    frame = pd.DataFrame({"L_id": [str(x) for x in archive["l_ids"]]})
    columns: dict[str, list[str]] = {}
    for prefix, key in blocks.items():
        if key not in archive.files:
            continue
        values = np.asarray(archive[key], dtype=float)
        names = [f"signal_{prefix}_{i:03d}" for i in range(values.shape[1])]
        frame = pd.concat([frame, pd.DataFrame(values, columns=names)], axis=1)
        columns[prefix] = names
    return frame, columns


def build_face_datasets(config: dict[str, Any]) -> list[GoalDataset]:
    face_dir = project_path(config["paths"]["face_dir"])
    if not (face_dir / "face_segment_embeddings.npz").exists():
        return []
    qc = _read(face_dir / "face_qc_features.csv")
    if qc is None:
        return []

    demo_num, demo_cat = _demo_numeric(config), _demo_categorical(config)
    cohort_specs = {
        # The within-subject contrast: identity, appearance and background cancel.
        "face_valence_contrast": {
            "face": "contrast_negative_minus_positive",
            "background": "contrast_negative_minus_positive_background",
            "full": "contrast_negative_minus_neutral",
        },
        # Raw per-segment embeddings, kept as the shortcut-exposed comparison.
        "face_segment_raw": {
            "face": "face_negative",
            "background": "background_negative",
            "full": "full_negative",
        },
    }

    out: list[GoalDataset] = []
    for cohort_name in config["goal2_8"]["face_cohorts"]:
        blocks = cohort_specs[cohort_name]
        embeddings, columns = _face_frame(config, blocks)
        cohort = _combine_signal_qc(embeddings.assign(feature_version="goal2_8_face_segment_valence_v1"),
                                    qc, config, "face", "", "task")
        if cohort.empty:
            continue
        qc_cols = _numeric_prefixed(cohort, "qc_")
        face_cols = [c for c in columns.get("face", []) if c in cohort.columns]
        bg_cols = [c for c in columns.get("background", []) if c in cohort.columns]
        full_cols = [c for c in columns.get("full", []) if c in cohort.columns]

        def add(feature_set: str, numeric: list[str], categorical: list[str], family: str = "face_embedding") -> None:
            out.append(_dataset(cohort, "face", "", "task", feature_set, cohort_name,
                                numeric, categorical, family))

        add("no_information", [], [], "no_information")
        add("demographics", demo_num, demo_cat, "tabular")
        add("qc", qc_cols, [], "tabular")
        add("qc_demographics", qc_cols + demo_num, demo_cat, "tabular")
        add("face", face_cols, [])
        add("background", bg_cols, [])
        add("full_frame", full_cols, [])
        add("face_demographics", face_cols + demo_num, demo_cat)
        add("background_demographics", bg_cols + demo_num, demo_cat)
        add("face_qc", face_cols + qc_cols, [])
        add("face_qc_demographics", face_cols + qc_cols + demo_num, demo_cat)
    return out


def build_datasets(config: dict[str, Any], modalities: set[str]) -> list[GoalDataset]:
    datasets: list[GoalDataset] = []
    if "eeg" in modalities:
        datasets.extend(build_eeg_datasets(config))
    if "fnirs" in modalities:
        datasets.extend(build_fnirs_datasets(config))
    if "face" in modalities:
        datasets.extend(build_face_datasets(config))
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
        "fnirs_devices": config["goal2_8"]["fnirs_devices"],
        "cv_protocols": list(config["protocol"].get("cv_protocols", {})),
        "outputs": {k: str(project_path(v)) for k, v in outputs.items()},
    }
    ensure_output(outputs["manifest"], config).write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")


def _run_parallel(datasets: list[GoalDataset], config: dict[str, Any],
                  n_workers: int) -> dict[str, Any]:
    """Fit datasets concurrently.

    Each fit is capped to a few threads, so on a many-core host the throughput
    comes from running many datasets at once rather than from one wide fit.
    Bootstrap and paired tests are deliberately left out here and computed once
    on the merged predictions, because paired tests must see every feature set
    of a cohort together.
    """
    if n_workers <= 1 or len(datasets) <= 1:
        return run_datasets(datasets, config, include_supplemental=False)

    from joblib import Parallel, delayed

    chunks = [datasets[i::n_workers] for i in range(n_workers)]
    chunks = [chunk for chunk in chunks if chunk]
    parts = Parallel(n_jobs=len(chunks), backend="loky", verbose=5)(
        delayed(run_datasets)(chunk, config, False) for chunk in chunks
    )
    return _merge_protocol_results(*parts)


def run_goal2_8(modalities: list[str] | None = None,
                config_path: str | Path = "configs/goal2_8/models.yaml",
                include_supplemental: bool = True,
                n_workers: int | None = None) -> dict[str, Any]:
    config = load_goal_config(config_path)
    requested = set(modalities or ["eeg", "fnirs", "face"])
    base = build_datasets(config, requested)
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
