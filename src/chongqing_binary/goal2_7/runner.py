"""Fixed-CV and group-aware Goal 2.7 model runner."""

from __future__ import annotations

import hashlib
import inspect
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.decomposition import PCA
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    f1_score,
    precision_recall_fscore_support,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .config import ensure_output, load_goal_config, project_path
from .io import add_clean_demographics, cv_subjects

METRIC_NAMES = [
    "auroc",
    "auprc",
    "balanced_accuracy",
    "macro_f1",
    "sensitivity",
    "specificity",
    "accuracy",
    "brier_score",
    "ece",
    "positive_prediction_rate",
]


@dataclass
class GoalDataset:
    cohort_name: str
    modality: str
    device: str
    task: str
    feature_set: str
    frame: pd.DataFrame
    numeric_columns: list[str]
    categorical_columns: list[str]
    model_family: str
    cv_protocol: str = "standard_cv"

    @property
    def feature_columns(self) -> list[str]:
        return self.numeric_columns + self.categorical_columns


def run_goal2_7(
    modalities: list[str] | None = None,
    config_path: str | Path = "configs/goal2_7/models.yaml",
    include_supplemental: bool = True,
) -> dict[str, Any]:
    config = _combined_config(config_path)
    requested = set(modalities or ["eeg", "fnirs", "face", "core3", "shortcut"])
    base_datasets = build_native_datasets(config, requested)
    if "core3" in requested:
        base_datasets.extend(build_core3_datasets(config))
    if "shortcut" in requested:
        base_datasets.extend(build_shortcut_datasets(config))
    standard_datasets = _datasets_for_protocol(base_datasets, config, "standard_cv")
    group_datasets = _datasets_for_protocol(base_datasets, config, "group_cv")
    standard_results = run_datasets(standard_datasets, config, include_supplemental=False)
    write_outputs(standard_results, standard_datasets, config)
    group_results = run_datasets(group_datasets, config, include_supplemental=False)
    results = _merge_protocol_results(standard_results, group_results)
    write_outputs(results, standard_datasets + group_datasets, config)
    if include_supplemental:
        write_supplemental_outputs(config)
        results["bootstrap"] = pd.read_csv(project_path(config["outputs"]["bootstrap_ci"]))
        results["paired"] = pd.read_csv(project_path(config["outputs"]["paired_comparisons"]))
    return {
        "datasets": len(standard_datasets) + len(group_datasets),
        "pooled_metrics": len(results["pooled_metrics"]),
        "predictions": len(results["predictions"]),
        "outputs": config["outputs"],
    }


def write_supplemental_outputs(config_path: str | Path | dict[str, Any] = "configs/goal2_7/models.yaml") -> dict[str, Any]:
    config = _combined_config(config_path) if not isinstance(config_path, dict) else config_path
    outputs = config["outputs"]
    prediction_frames = []
    for key in ["all_oof_predictions_standard_cv", "all_oof_predictions_group_cv"]:
        path = project_path(outputs[key])
        if not path.exists():
            archive_path = Path(f"{path}.gz")
            if archive_path.exists():
                path = archive_path
        if path.exists() and path.stat().st_size > 0:
            prediction_frames.append(pd.read_csv(path, dtype={"L_id": str}, low_memory=False))
    predictions = pd.concat(prediction_frames, ignore_index=True) if prediction_frames else pd.DataFrame()
    bootstrap = _bootstrap_table(predictions, config)
    paired = _paired_comparisons(predictions, config)
    bootstrap.to_csv(ensure_output(outputs["bootstrap_ci"], config), index=False)
    paired.to_csv(ensure_output(outputs["paired_comparisons"], config), index=False)
    return {
        "prediction_rows": int(len(predictions)),
        "bootstrap_rows": int(len(bootstrap)),
        "paired_rows": int(len(paired)),
        "outputs": {
            "bootstrap_ci": outputs["bootstrap_ci"],
            "paired_comparisons": outputs["paired_comparisons"],
        },
    }


run_goal2_6 = run_goal2_7


def build_native_datasets(config: dict[str, Any], requested: set[str]) -> list[GoalDataset]:
    out: list[GoalDataset] = []
    if "eeg" in requested:
        out.extend(_eeg_datasets(config))
    if "fnirs" in requested:
        out.extend(_fnirs_datasets(config))
    if "face" in requested:
        out.extend(_face_datasets(config))
    return out


def _datasets_for_protocol(datasets: list[GoalDataset], config: dict[str, Any], cv_protocol: str) -> list[GoalDataset]:
    spec = config["protocol"]["cv_protocols"][cv_protocol]
    split = pd.read_csv(project_path(spec["split_file"]), dtype={"L_id": str})
    split = split[split["split_group"].astype(str) == "cv"].copy()
    fold_col = spec["fold_column"]
    split[fold_col] = pd.to_numeric(split[fold_col], errors="coerce")
    split = split[split[fold_col].notna()].copy()
    split = split[["L_id", fold_col]]
    out: list[GoalDataset] = []
    for dataset in datasets:
        frame = dataset.frame.drop(columns=["cv_fold"], errors="ignore").merge(split, on="L_id", how="inner")
        if frame.empty:
            continue
        frame["cv_fold"] = frame[fold_col].astype(int)
        if fold_col != "cv_fold":
            frame = frame.drop(columns=[fold_col])
        out.append(
            GoalDataset(
                cohort_name=dataset.cohort_name,
                modality=dataset.modality,
                device=dataset.device,
                task=dataset.task,
                feature_set=dataset.feature_set,
                frame=frame,
                numeric_columns=dataset.numeric_columns,
                categorical_columns=dataset.categorical_columns,
                model_family=dataset.model_family,
                cv_protocol=cv_protocol,
            )
        )
    return out


def _merge_protocol_results(*results: dict[str, Any]) -> dict[str, Any]:
    keys = ["predictions", "fold_metrics", "pooled_metrics", "bootstrap", "paired", "hyperparameters", "pca"]
    merged: dict[str, Any] = {}
    for key in keys:
        frames = [result.get(key, pd.DataFrame()) for result in results]
        frames = [frame for frame in frames if isinstance(frame, pd.DataFrame) and not frame.empty]
        merged[key] = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    return merged


def _eeg_datasets(config: dict[str, Any]) -> list[GoalDataset]:
    out: list[GoalDataset] = []
    for task, spec in config.get("eeg", {}).get("tasks", {}).items():
        if not project_path(spec["signal_features"]).exists() or not project_path(spec["qc_features"]).exists():
            continue
        signal = pd.read_csv(project_path(spec["signal_features"]), dtype={"L_id": str}, low_memory=False)
        qc = pd.read_csv(project_path(spec["qc_features"]), dtype={"L_id": str}, low_memory=False)
        cohort = _combine_signal_qc(signal, qc, config, "eeg", "", task)
        if cohort.empty:
            continue
        out.extend(_standard_feature_sets(cohort, "eeg", "", task, f"eeg_{task}_native", config, model_family="tabular"))
    control = config.get("eeg", {}).get("v1_rest_control", {})
    path = control.get("path")
    if path and project_path(path).exists():
        split = add_clean_demographics(cv_subjects(config), config)
        raw = pd.read_csv(project_path(path), dtype={"L_id": str})
        features = [col for col in raw.columns if col.startswith(("bp_", "region_", "asym_", "spectral_entropy", "hjorth_"))]
        frame = split.merge(raw[["L_id", *features]], on="L_id", how="inner")
        frame["modality"] = "eeg"
        frame["device"] = ""
        frame["task"] = "rest_v1_control"
        out.append(_dataset(frame, "eeg", "", "rest_v1_control", "signal", control.get("output_name", "eeg_rest_v1_features_fixed_split"), features, [], "tabular"))
        out.append(_dataset(frame, "eeg", "", "rest_v1_control", "demographics", control.get("output_name", "eeg_rest_v1_features_fixed_split"), _demo_numeric(config), _demo_categorical(config), "tabular"))
    return out


def _fnirs_datasets(config: dict[str, Any]) -> list[GoalDataset]:
    out: list[GoalDataset] = []
    out_dir = config.get("fnirs", {}).get("outputs", {}).get("dir", "artifacts/goal2_6/fnirs")
    for device in config.get("fnirs", {}).get("devices", {}):
        for task in config.get("fnirs", {}).get("tasks", []):
            stem = f"{device}_{task}"
            signal_path = project_path(f"{out_dir}/{stem}_signal_features.csv")
            qc_path = project_path(f"{out_dir}/{stem}_qc_features.csv")
            if not signal_path.exists() or not qc_path.exists():
                continue
            signal = pd.read_csv(signal_path, dtype={"L_id": str})
            qc = pd.read_csv(qc_path, dtype={"L_id": str})
            cohort = _combine_signal_qc(signal, qc, config, "fnirs", device, task)
            if cohort.empty:
                continue
            out.extend(_standard_feature_sets(cohort, "fnirs", device, task, f"fnirs_{stem}_native", config, model_family="tabular"))
    return out


def _face_datasets(config: dict[str, Any]) -> list[GoalDataset]:
    out: list[GoalDataset] = []
    for task, spec in config.get("face", {}).get("tasks", {}).items():
        if not project_path(spec["signal_features"]).exists() or not project_path(spec["qc_features"]).exists():
            continue
        signal = pd.read_csv(project_path(spec["signal_features"]), dtype={"L_id": str}, low_memory=False)
        qc = pd.read_csv(project_path(spec["qc_features"]), dtype={"L_id": str}, low_memory=False)
        cohort = _combine_signal_qc(signal, qc, config, "face", "", task)
        if cohort.empty:
            continue
        demo_num = _demo_numeric(config)
        demo_cat = _demo_categorical(config)
        qc_cols = _numeric_prefixed(cohort, "qc_")
        metadata_cols = [col for col in qc_cols if col in {"qc_resolution_width", "qc_resolution_height", "qc_fps", "qc_duration_sec", "qc_aspect_ratio"}]
        metadata_cat = [col for col in ["qc_codec"] if col in cohort.columns]
        face_cols = _numeric_prefixed(cohort, "signal_face_")
        full_cols = _numeric_prefixed(cohort, "signal_full_")
        background_cols = _numeric_prefixed_excluding(cohort, "signal_background_", ["signal_background_blur_"])
        background_blur_cols = _numeric_prefixed(cohort, "signal_background_blur_")
        cohort_name = f"face_{task}_native"
        face_ok = cohort[cohort.get("qc_face_feature_blocked", 0).fillna(0).astype(int) == 0].copy() if "qc_face_feature_blocked" in cohort.columns else cohort
        out.append(_dataset(cohort, "face", "", task, "no_information", cohort_name, [], [], "no_information"))
        out.append(_dataset(cohort, "face", "", task, "demographics", cohort_name, demo_num, demo_cat, "face_embedding"))
        out.append(_dataset(cohort, "face", "", task, "qc", cohort_name, qc_cols, metadata_cat, "face_embedding"))
        out.append(_dataset(cohort, "face", "", task, "qc_demographics", cohort_name, qc_cols + demo_num, metadata_cat + demo_cat, "face_embedding"))
        out.append(_dataset(cohort, "face", "", task, "metadata", cohort_name, metadata_cols, metadata_cat, "face_embedding"))
        out.append(_dataset(cohort, "face", "", task, "full_frame", cohort_name, full_cols, [], "face_embedding"))
        out.append(_dataset(face_ok, "face", "", task, "face", cohort_name, face_cols, [], "face_embedding"))
        out.append(_dataset(face_ok, "face", "", task, "background", cohort_name, background_cols, [], "face_embedding"))
        out.append(_dataset(face_ok, "face", "", task, "background_blur", cohort_name, background_blur_cols, [], "face_embedding"))
        out.append(_dataset(face_ok, "face", "", task, "face_qc", cohort_name, face_cols + qc_cols, metadata_cat, "face_embedding"))
        out.append(_dataset(face_ok, "face", "", task, "face_demographics", cohort_name, face_cols + demo_num, demo_cat, "face_embedding"))
        out.append(_dataset(face_ok, "face", "", task, "background_demographics", cohort_name, background_cols + demo_num, demo_cat, "face_embedding"))
        out.append(_dataset(face_ok, "face", "", task, "face_qc_demographics", cohort_name, face_cols + qc_cols + demo_num, metadata_cat + demo_cat, "face_embedding"))
        out.append(_dataset(face_ok, "face", "", task, "background_qc_demographics", cohort_name, background_cols + qc_cols + demo_num, metadata_cat + demo_cat, "face_embedding"))
        out.extend(_demographic_decomposition_datasets(cohort, "face", "", task, cohort_name, config, "face_embedding"))
    out.extend(_face_two_video_datasets(config))
    return out


def _face_two_video_datasets(config: dict[str, Any]) -> list[GoalDataset]:
    tasks = config.get("face", {}).get("tasks", {})
    if "self_intro" not in tasks or "task" not in tasks:
        return []
    required = []
    for task_name in ["self_intro", "task"]:
        spec = tasks[task_name]
        if not project_path(spec["signal_features"]).exists() or not project_path(spec["qc_features"]).exists():
            return []
        signal = pd.read_csv(project_path(spec["signal_features"]), dtype={"L_id": str}, low_memory=False)
        qc = pd.read_csv(project_path(spec["qc_features"]), dtype={"L_id": str}, low_memory=False)
        required.append((task_name, signal, qc))
    split = add_clean_demographics(cv_subjects(config), config)
    frame = split.copy()
    for task_name, signal, qc in required:
        frame = frame.merge(_prefix_face_task_frame(signal, task_name, "signal_"), on="L_id", how="inner")
        frame = frame.merge(_prefix_face_task_frame(qc, task_name, "qc_"), on="L_id", how="inner")
    if frame.empty:
        return []
    frame["modality"] = "face"
    frame["device"] = ""
    frame["task"] = "two_video"
    demo_num = _demo_numeric(config)
    demo_cat = _demo_categorical(config)
    qc_cols = _numeric_any_prefix(frame, ["qc_self_intro_", "qc_task_"])
    metadata_cols = [
        col
        for col in qc_cols
        if any(
            col.endswith(suffix)
            for suffix in ["resolution_width", "resolution_height", "fps", "duration_sec", "aspect_ratio"]
        )
    ]
    metadata_cat = [col for col in ["qc_self_intro_codec", "qc_task_codec"] if col in frame.columns]
    face_cols = _numeric_any_prefix(frame, ["signal_face_self_intro_", "signal_face_task_"])
    full_cols = _numeric_any_prefix(frame, ["signal_full_self_intro_", "signal_full_task_"])
    background_cols = _numeric_any_prefix_excluding(frame, ["signal_background_self_intro_", "signal_background_task_"], ["signal_background_blur_"])
    background_blur_cols = _numeric_any_prefix(frame, ["signal_background_blur_self_intro_", "signal_background_blur_task_"])
    cohort_name = "face_two_video_native"
    return [
        _dataset(frame, "face", "", "two_video", "no_information", cohort_name, [], [], "no_information"),
        _dataset(frame, "face", "", "two_video", "demographics", cohort_name, demo_num, demo_cat, "face_embedding"),
        _dataset(frame, "face", "", "two_video", "qc", cohort_name, qc_cols, metadata_cat, "face_embedding"),
        _dataset(frame, "face", "", "two_video", "metadata", cohort_name, metadata_cols, metadata_cat, "face_embedding"),
        _dataset(frame, "face", "", "two_video", "full_frame", cohort_name, full_cols, [], "face_embedding"),
        _dataset(frame, "face", "", "two_video", "face", cohort_name, face_cols, [], "face_embedding"),
        _dataset(frame, "face", "", "two_video", "background", cohort_name, background_cols, [], "face_embedding"),
        _dataset(frame, "face", "", "two_video", "background_blur", cohort_name, background_blur_cols, [], "face_embedding"),
        _dataset(frame, "face", "", "two_video", "face_qc", cohort_name, face_cols + qc_cols, metadata_cat, "face_embedding"),
        _dataset(frame, "face", "", "two_video", "face_demographics", cohort_name, face_cols + demo_num, demo_cat, "face_embedding"),
        _dataset(frame, "face", "", "two_video", "background_demographics", cohort_name, background_cols + demo_num, demo_cat, "face_embedding"),
        _dataset(frame, "face", "", "two_video", "qc_demographics", cohort_name, qc_cols + demo_num, metadata_cat + demo_cat, "face_embedding"),
        _dataset(frame, "face", "", "two_video", "face_qc_demographics", cohort_name, face_cols + qc_cols + demo_num, metadata_cat + demo_cat, "face_embedding"),
        _dataset(frame, "face", "", "two_video", "background_qc_demographics", cohort_name, background_cols + qc_cols + demo_num, metadata_cat + demo_cat, "face_embedding"),
    ]


def _prefix_face_task_frame(frame: pd.DataFrame, task_name: str, prefix: str) -> pd.DataFrame:
    rename = {}
    for col in frame.columns:
        if not col.startswith(prefix):
            continue
        if prefix == "signal_":
            for variant in ["signal_face_", "signal_full_", "signal_background_blur_", "signal_background_"]:
                if col.startswith(variant):
                    rename[col] = variant + task_name + "_" + col[len(variant) :]
                    break
        else:
            rename[col] = f"qc_{task_name}_{col[len(prefix):]}"
    return frame[["L_id", *rename]].rename(columns=rename)


def _standard_feature_sets(
    cohort: pd.DataFrame,
    modality: str,
    device: str,
    task: str,
    cohort_name: str,
    config: dict[str, Any],
    model_family: str,
) -> list[GoalDataset]:
    demo_num = _demo_numeric(config)
    demo_cat = _demo_categorical(config)
    signal_cols = _numeric_prefixed(cohort, "signal_")
    qc_cols = _numeric_prefixed(cohort, "qc_")
    datasets = [
        _dataset(cohort, modality, device, task, "no_information", cohort_name, [], [], "no_information"),
        _dataset(cohort, modality, device, task, "demographics", cohort_name, demo_num, demo_cat, model_family),
        _dataset(cohort, modality, device, task, "qc", cohort_name, qc_cols, [], model_family),
        _dataset(cohort, modality, device, task, "qc_demographics", cohort_name, qc_cols + demo_num, demo_cat, model_family),
        _dataset(cohort, modality, device, task, "signal", cohort_name, signal_cols, [], model_family),
        _dataset(cohort, modality, device, task, "signal_qc", cohort_name, signal_cols + qc_cols, [], model_family),
        _dataset(cohort, modality, device, task, "signal_demographics", cohort_name, signal_cols + demo_num, demo_cat, model_family),
        _dataset(cohort, modality, device, task, "signal_qc_demographics", cohort_name, signal_cols + qc_cols + demo_num, demo_cat, model_family),
    ]
    datasets.extend(_demographic_decomposition_datasets(cohort, modality, device, task, cohort_name, config, model_family))
    return datasets


def _demographic_decomposition_datasets(
    cohort: pd.DataFrame,
    modality: str,
    device: str,
    task: str,
    cohort_name: str,
    config: dict[str, Any],
    model_family: str,
) -> list[GoalDataset]:
    out: list[GoalDataset] = []
    for name, spec in config.get("demographics", {}).get("decomposition_sets", {}).items():
        numeric = list(spec.get("numeric", []))
        categorical = list(spec.get("categorical", []))
        out.append(_dataset(cohort, modality, device, task, name, cohort_name, numeric, categorical, model_family))
    return out


def build_core3_datasets(config: dict[str, Any]) -> list[GoalDataset]:
    core = pd.read_csv(project_path(config["paths"]["core3_qc_file"]), dtype={"L_id": str})
    core = core[core["split_group"].astype(str) == "cv"].copy()
    core_lids = set(core["L_id"])
    candidates: list[tuple[str, str, str, str, str]] = []
    eeg_rest = config.get("eeg", {}).get("tasks", {}).get("rest", {})
    if eeg_rest:
        candidates.append(("eeg", "", "rest", eeg_rest["signal_features"], eeg_rest["qc_features"]))
    fnirs_dir = config.get("fnirs", {}).get("outputs", {}).get("dir", "artifacts/goal2_7/fnirs")
    for device, task in [("yiruid", "vft"), ("bikom", "vft"), ("yiruid", "rest"), ("bikom", "rest")]:
        signal_path = project_path(f"{fnirs_dir}/{device}_{task}_signal_features.csv")
        qc_path = project_path(f"{fnirs_dir}/{device}_{task}_qc_features.csv")
        if signal_path.exists() and qc_path.exists():
            candidates.append(("fnirs", device, task, str(signal_path), str(qc_path)))
            break
    face_spec = config.get("face", {}).get("tasks", {}).get("self_intro", {})
    if face_spec:
        candidates.append(("face", "", "self_intro", face_spec["signal_features"], face_spec["qc_features"]))
    loaded: list[tuple[str, str, str, pd.DataFrame]] = []
    for modality, device, task, signal_path, qc_path in candidates:
        if not project_path(signal_path).exists() or not project_path(qc_path).exists():
            continue
        signal = pd.read_csv(project_path(signal_path), dtype={"L_id": str}, low_memory=False)
        qc = pd.read_csv(project_path(qc_path), dtype={"L_id": str}, low_memory=False)
        cohort = _combine_signal_qc(signal, qc, config, modality, device, task)
        cohort = cohort[cohort["L_id"].isin(core_lids)].copy()
        loaded.append((modality, device, task, cohort))
    if len(loaded) < 3:
        return []
    common_lids = set(loaded[0][3]["L_id"])
    for _, _, _, cohort in loaded[1:]:
        common_lids &= set(cohort["L_id"])
    out: list[GoalDataset] = []
    for modality, device, task, cohort in loaded:
        subset = cohort[cohort["L_id"].isin(common_lids)].copy()
        if subset.empty:
            continue
        demo_num = _demo_numeric(config)
        demo_cat = _demo_categorical(config)
        if modality == "face":
            signal_cols = _numeric_prefixed(subset, "signal_face_")
            feature_name = "modality"
        else:
            signal_cols = _numeric_prefixed(subset, "signal_")
            feature_name = "modality"
        qc_cols = _numeric_prefixed(subset, "qc_")
        cohort_name = "core3_rest_yiruidvft_selfintro_intersection"
        out.append(_dataset(subset, modality, device, task, "demographics", cohort_name, demo_num, demo_cat, "face_embedding" if modality == "face" else "tabular"))
        out.append(_dataset(subset, modality, device, task, feature_name, cohort_name, signal_cols, [], "face_embedding" if modality == "face" else "tabular"))
        out.append(_dataset(subset, modality, device, task, f"{feature_name}_demographics", cohort_name, signal_cols + demo_num, demo_cat, "face_embedding" if modality == "face" else "tabular"))
        out.append(_dataset(subset, modality, device, task, "qc_demographics", cohort_name, qc_cols + demo_num, demo_cat, "face_embedding" if modality == "face" else "tabular"))
        out.append(_dataset(subset, modality, device, task, f"{feature_name}_qc_demographics", cohort_name, signal_cols + qc_cols + demo_num, demo_cat, "face_embedding" if modality == "face" else "tabular"))
        out.extend(_demographic_decomposition_datasets(subset, modality, device, task, cohort_name, config, "face_embedding" if modality == "face" else "tabular"))
    return out


def build_shortcut_datasets(config: dict[str, Any]) -> list[GoalDataset]:
    groups_path = project_path(config["paths"]["groups_file"])
    if not groups_path.exists():
        return []
    split = add_clean_demographics(cv_subjects(config), config)
    groups = pd.read_csv(groups_path, dtype={"L_id": str})
    frame = split.merge(groups[["L_id", "group_code", "group_family", "group_prefix2", "group_prefix3"]], on="L_id", how="left")
    frame["modality"] = "shortcut"
    frame["device"] = ""
    frame["task"] = "a_prefix_group"
    cols = [col for col in ["group_code", "group_family", "group_prefix2", "group_prefix3", "fnirs_device"] if col in frame.columns]
    return [_dataset(frame, "shortcut", "", "a_prefix_group", "group_device", "shortcut_a_prefix_group_cv", [], cols, "tabular")]


def run_datasets(
    datasets: list[GoalDataset],
    config: dict[str, Any],
    include_supplemental: bool = True,
) -> dict[str, list[dict[str, Any]] | pd.DataFrame]:
    prediction_rows: list[dict[str, Any]] = []
    fold_metric_rows: list[dict[str, Any]] = []
    hyper_rows: list[dict[str, Any]] = []
    pca_rows: list[dict[str, Any]] = []
    seed = int(config.get("run", {}).get("seed", 20260707))
    label_col = config.get("run", {}).get("label_column", "primary_label_nonhealthy")
    total_jobs = sum(len(_models_for_dataset(dataset, config)) for dataset in datasets)
    job_index = 0
    for dataset_index, dataset in enumerate(datasets, start=1):
        if not dataset.feature_columns and dataset.model_family != "no_information":
            continue
        models = _models_for_dataset(dataset, config)
        for model_name in models:
            job_index += 1
            print(
                f"[goal2_7] {job_index}/{total_jobs} protocol={dataset.cv_protocol} dataset={dataset_index}/{len(datasets)} "
                f"cohort={dataset.cohort_name} modality={dataset.modality} task={dataset.task} "
                f"feature_set={dataset.feature_set} model={model_name} n={dataset.frame['L_id'].nunique()} p={len(dataset.feature_columns)}",
                flush=True,
            )
            fold_predictions: list[pd.DataFrame] = []
            for fold in sorted(dataset.frame["cv_fold"].dropna().astype(int).unique()):
                train = dataset.frame[dataset.frame["cv_fold"].astype(int) != fold].copy()
                val = dataset.frame[dataset.frame["cv_fold"].astype(int) == fold].copy()
                if train.empty or val.empty:
                    continue
                y_train = train[label_col].astype(int).to_numpy()
                y_val = val[label_col].astype(int).to_numpy()
                if dataset.model_family == "no_information":
                    model = DummyClassifier(strategy="prior")
                    model.fit(np.zeros((len(train), 1)), y_train)
                    prob = model.predict_proba(np.zeros((len(val), 1)))[:, 1]
                    threshold = 0.5
                    params: dict[str, Any] = {"strategy": "prior"}
                    inner_score = math.nan
                else:
                    params, threshold, inner_score = _select_hyperparameters(dataset, model_name, train, config, seed + fold)
                    model = _build_pipeline(dataset, model_name, config, seed + 1000 + fold)
                    model.set_params(**params)
                    _fit_model(model, model_name, train[dataset.feature_columns], y_train)
                    pca_rows.append(
                        {
                            **_context(dataset, model_name, seed),
                            "outer_fold": fold,
                            **_pca_summary(model),
                        }
                    )
                    prob = _predict_proba(model, val[dataset.feature_columns])
                predicted_label = (np.asarray(prob, dtype=float) >= float(threshold)).astype(int)
                pred = pd.DataFrame(
                    {
                        "L_id": val["L_id"].astype(str).to_numpy(),
                        "label": y_val,
                        "modality": dataset.modality,
                        "device": dataset.device,
                        "task": dataset.task,
                        "feature_set": dataset.feature_set,
                        "model": model_name,
                        "cv_protocol": dataset.cv_protocol,
                        "seed": seed,
                        "outer_fold": fold,
                        "probability": prob,
                        "threshold": threshold,
                        "fold_specific_threshold": threshold,
                        "selected_threshold_per_subject": threshold,
                        "selected_threshold_per_fold": threshold,
                        "threshold_source": "inner_cv_outer_train_only",
                        "predicted_label": predicted_label,
                        "cohort_name": dataset.cohort_name,
                        "event_validity_status": _row_values(val, "event_validity_status", "unknown"),
                        "feature_version": _row_values(val, "feature_version", ""),
                        "preprocessing_version": _row_values(val, "preprocessing_version", ""),
                    }
                )
                fold_predictions.append(pred)
                for threshold_type, thr in [("fixed_0_5", 0.5), ("inner_cv", threshold)]:
                    fold_metric_rows.append(
                        {
                            **_context(dataset, model_name, seed),
                            "threshold_type": threshold_type,
                            "outer_fold": fold,
                            "threshold": thr,
                            "n_subjects": len(val),
                            "n_positive": int(np.sum(y_val)),
                            "n_negative": int(len(y_val) - np.sum(y_val)),
                            **compute_metrics(y_val, prob, thr, int(config["protocol"]["calibration_bins"])),
                        }
                    )
                hyper_rows.append(
                    {
                        **_context(dataset, model_name, seed),
                        "outer_fold": fold,
                        "selected_params": json.dumps(params, sort_keys=True),
                        "selected_threshold": threshold,
                        "inner_cv_auroc": inner_score,
                        "n_train_subjects": len(train),
                        "n_validation_subjects": len(val),
                    }
                )
            if fold_predictions:
                prediction_rows.extend(pd.concat(fold_predictions, ignore_index=True).to_dict(orient="records"))
    predictions = pd.DataFrame(prediction_rows)
    pooled = _pooled_metrics(predictions, config)
    bootstrap = _bootstrap_table(predictions, config) if include_supplemental else pd.DataFrame()
    paired = _paired_comparisons(predictions, config) if include_supplemental else pd.DataFrame()
    return {
        "predictions": predictions,
        "fold_metrics": pd.DataFrame(fold_metric_rows),
        "pooled_metrics": pooled,
        "bootstrap": bootstrap,
        "paired": paired,
        "hyperparameters": pd.DataFrame(hyper_rows),
        "pca": pd.DataFrame(pca_rows),
    }


def write_outputs(results: dict[str, Any], datasets: list[GoalDataset], config: dict[str, Any]) -> None:
    outputs = config["outputs"]
    predictions = results["predictions"]
    predictions[predictions.get("cv_protocol", "") == "standard_cv"].to_csv(ensure_output(outputs["all_oof_predictions_standard_cv"], config), index=False)
    predictions[predictions.get("cv_protocol", "") == "group_cv"].to_csv(ensure_output(outputs["all_oof_predictions_group_cv"], config), index=False)
    results["fold_metrics"].to_csv(ensure_output(outputs["all_fold_metrics"], config), index=False)
    results["pooled_metrics"].to_csv(ensure_output(outputs["all_pooled_metrics"], config), index=False)
    results["bootstrap"].to_csv(ensure_output(outputs["bootstrap_ci"], config), index=False)
    results["paired"].to_csv(ensure_output(outputs["paired_comparisons"], config), index=False)
    results["hyperparameters"].to_csv(ensure_output(outputs["selected_hyperparameters"], config), index=False)
    results["pca"].to_csv(ensure_output(outputs["pca_diagnostics"], config), index=False)
    _feature_counts(datasets).to_csv(ensure_output(outputs["feature_counts"], config), index=False)
    _native_summary(results["pooled_metrics"]).to_csv(ensure_output(outputs["native_cohort_summary"], config), index=False)
    _core3_summary(results["pooled_metrics"]).to_csv(ensure_output(outputs["core3_intersection_summary"], config), index=False)
    _shortcut_summary(results["pooled_metrics"]).to_csv(ensure_output(outputs["shortcut_baseline_summary"], config), index=False)
    _demographics_decomposition(results["pooled_metrics"], config).to_csv(ensure_output(outputs["demographics_decomposition"], config), index=False)
    _standard_vs_group(results["pooled_metrics"]).to_csv(ensure_output(outputs["standard_vs_group_cv"], config), index=False)
    _threshold_diagnostics(results["predictions"], results["fold_metrics"]).to_csv(ensure_output(outputs["threshold_diagnostics"], config), index=False)
    _face_strict_control_summary(config).to_csv(ensure_output(outputs["face_strict_control_summary"], config), index=False)
    _event_validity_summary(config, "eeg").to_csv(ensure_output(outputs["eeg_event_validity_summary"], config), index=False)
    _event_validity_summary(config, "fnirs").to_csv(ensure_output(outputs["fnirs_event_validity_summary"], config), index=False)
    _exclusion_summary(config).to_csv(ensure_output(outputs["exclusion_summary"], config), index=False)
    manifest = {
        "config": config.get("_config_path", ""),
        "n_datasets": len(datasets),
        "n_prediction_rows": int(len(results["predictions"])),
        "n_pooled_rows": int(len(results["pooled_metrics"])),
        "lightgbm_fallback": config.get("fallbacks", {}),
        "cv_protocols": list(config["protocol"].get("cv_protocols", {})),
        "outputs": {key: str(project_path(value)) for key, value in outputs.items()},
    }
    ensure_output(outputs["manifest"], config).write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")


def _select_hyperparameters(
    dataset: GoalDataset,
    model_name: str,
    train: pd.DataFrame,
    config: dict[str, Any],
    seed: int,
) -> tuple[dict[str, Any], float, float]:
    label_col = config.get("run", {}).get("label_column", "primary_label_nonhealthy")
    y = train[label_col].astype(int).to_numpy()
    candidates = _hyperparameter_candidates(dataset, model_name, train, config)
    best_params: dict[str, Any] = candidates[0] if candidates else {}
    best_score = -math.inf
    best_prob = np.full(len(train), np.nan, dtype=float)
    splits = StratifiedKFold(n_splits=int(config["protocol"]["inner_cv_folds"]), shuffle=True, random_state=seed)
    for params in candidates:
        oof = np.full(len(train), np.nan, dtype=float)
        for inner_train_idx, inner_val_idx in splits.split(train, y):
            inner_train = train.iloc[inner_train_idx]
            inner_val = train.iloc[inner_val_idx]
            model = _build_pipeline(dataset, model_name, config, seed)
            model.set_params(**params)
            _fit_model(model, model_name, inner_train[dataset.feature_columns], y[inner_train_idx])
            oof[inner_val_idx] = _predict_proba(model, inner_val[dataset.feature_columns])
        score = _safe_metric(lambda: roc_auc_score(y, oof))
        if math.isnan(score):
            score = _safe_metric(lambda: average_precision_score(y, oof))
        if score > best_score:
            best_score = score
            best_params = params
            best_prob = oof
    threshold = _select_threshold(y, best_prob, config["protocol"]["threshold_grid"])
    return best_params, threshold, best_score


def _hyperparameter_candidates(dataset: GoalDataset, model_name: str, train: pd.DataFrame, config: dict[str, Any]) -> list[dict[str, Any]]:
    base = list(config.get("hyperparameters", {}).get(model_name, [{}]))[:20]
    visual_columns = _visual_columns(dataset)
    if not visual_columns:
        return base
    inner_folds = int(config["protocol"].get("inner_cv_folds", 3))
    min_inner_train = max(2, int(math.floor(len(train) * (inner_folds - 1) / inner_folds)))
    max_legal = max(2, min(len(visual_columns), min_inner_train))
    dims = []
    for dim in config["protocol"].get("face_pca_components", [32, 64, 128]):
        legal = min(int(dim), max_legal)
        if legal >= 2 and legal not in dims:
            dims.append(legal)
    if not dims:
        dims = [max_legal]
    out: list[dict[str, Any]] = []
    for params in base:
        for dim in dims:
            candidate = dict(params)
            candidate["preprocess__visual__pca__n_components"] = int(dim)
            out.append(candidate)
    return out[:20]


def _build_pipeline(dataset: GoalDataset, model_name: str, config: dict[str, Any], seed: int) -> Pipeline:
    transformers = []
    visual_columns = _visual_columns(dataset)
    visual_set = set(visual_columns)
    nonvisual_numeric = [col for col in dataset.numeric_columns if col not in visual_set]
    if visual_columns:
        n_components = min(
            int(config["protocol"].get("max_pca_components", 128)),
            max(2, len(dataset.frame) - 1),
            len(visual_columns),
        )
        transformers.append(
            (
                "visual",
                Pipeline(
                    [
                        ("imputer", _simple_imputer("median")),
                        ("scaler", StandardScaler()),
                        ("pca", PCA(n_components=n_components, svd_solver="randomized", random_state=seed)),
                    ]
                ),
                visual_columns,
            )
        )
    if nonvisual_numeric:
        transformers.append(
            (
                "num",
                Pipeline(
                    [
                        ("imputer", _simple_imputer("median")),
                        ("scaler", StandardScaler()),
                    ]
                ),
                nonvisual_numeric,
            )
        )
    if dataset.categorical_columns:
        transformers.append(
            (
                "cat",
                Pipeline(
                    [
                        ("imputer", _simple_imputer("most_frequent")),
                        ("onehot", _one_hot_encoder()),
                    ]
                ),
                dataset.categorical_columns,
            )
        )
    preprocess = ColumnTransformer(transformers=transformers, sparse_threshold=0.0)
    steps: list[tuple[str, Any]] = [("preprocess", preprocess)]
    if model_name == "logistic_regression":
        classifier = LogisticRegression(class_weight="balanced", max_iter=2000, random_state=seed)
    elif model_name == "random_forest":
        classifier = RandomForestClassifier(
            n_estimators=120,
            min_samples_leaf=5,
            class_weight="balanced_subsample",
            n_jobs=-1,
            random_state=seed,
        )
    elif model_name == "hist_gradient_boosting":
        classifier = HistGradientBoostingClassifier(
            max_iter=80,
            learning_rate=0.05,
            max_leaf_nodes=15,
            l2_regularization=0.01,
            random_state=seed,
        )
    else:
        raise ValueError(f"Unsupported model: {model_name}")
    steps.append(("model", classifier))
    return Pipeline(steps)


def _pca_summary(model: Pipeline) -> dict[str, Any]:
    preprocess = model.named_steps.get("preprocess")
    visual_pipe = None
    if preprocess is not None and hasattr(preprocess, "named_transformers_"):
        visual_pipe = preprocess.named_transformers_.get("visual")
    if visual_pipe is None or not hasattr(visual_pipe, "named_steps") or "pca" not in visual_pipe.named_steps:
        return {
            "pca_used": 0,
            "pca_n_components": 0,
            "pca_explained_variance_ratio_sum": math.nan,
            "visual_branch_feature_count": 0,
            "nonvisual_branch_feature_count": 0,
        }
    pca = visual_pipe.named_steps["pca"]
    ratio = getattr(pca, "explained_variance_ratio_", np.asarray([], dtype=float))
    visual_count = 0
    nonvisual_count = 0
    for name, _, cols in getattr(preprocess, "transformers", []):
        if name == "visual":
            visual_count += len(cols)
        elif name in {"num", "cat"}:
            nonvisual_count += len(cols)
    return {
        "pca_used": 1,
        "pca_n_components": int(getattr(pca, "n_components_", len(ratio))),
        "pca_explained_variance_ratio_sum": float(np.sum(ratio)) if len(ratio) else math.nan,
        "visual_branch_feature_count": visual_count,
        "nonvisual_branch_feature_count": nonvisual_count,
    }


def _group_robustness_table(datasets: list[GoalDataset], config: dict[str, Any]) -> pd.DataFrame:
    path = project_path(config["paths"].get("group_split_file", ""))
    if not path.exists():
        return pd.DataFrame()
    robust = pd.read_csv(path, dtype={"L_id": str})
    robust = robust[robust["split_group"].astype(str) == "cv"][["L_id", "robustness_fold"]].copy()
    robust["robustness_fold"] = pd.to_numeric(robust["robustness_fold"], errors="coerce")
    robust = robust[robust["robustness_fold"].notna()].copy()
    desired = {
        ("eeg_oddball_native", "signal_demographics"),
        ("fnirs_yiruid_vft_native", "signal_qc"),
        ("face_task_native", "face_demographics"),
        ("face_two_video_native", "face_demographics"),
        ("shortcut_a_prefix_group_cv", "group_device"),
    }
    selected: list[GoalDataset] = []
    for dataset in datasets:
        if (dataset.cohort_name, dataset.feature_set) not in desired:
            continue
        frame = dataset.frame.drop(columns=["cv_fold"], errors="ignore").merge(robust, on="L_id", how="inner")
        if frame.empty:
            continue
        frame["cv_fold"] = frame["robustness_fold"].astype(int)
        frame = frame.drop(columns=["robustness_fold"])
        selected.append(
            GoalDataset(
                cohort_name=f"{dataset.cohort_name}_group_robustness",
                modality=dataset.modality,
                device=dataset.device,
                task=dataset.task,
                feature_set=dataset.feature_set,
                frame=frame,
                numeric_columns=dataset.numeric_columns,
                categorical_columns=dataset.categorical_columns,
                model_family=dataset.model_family,
                cv_protocol="group_cv",
            )
        )
    if not selected:
        return pd.DataFrame()
    result = run_datasets(selected, config, include_supplemental=False)["pooled_metrics"]
    if result.empty:
        return result
    result = result[result["threshold_type"] == "inner_cv"].copy()
    result["robustness_split_file"] = str(path)
    result["robustness_fold_column"] = "robustness_fold"
    return result.reset_index(drop=True)


def _simple_imputer(strategy: str) -> SimpleImputer:
    kwargs: dict[str, Any] = {"strategy": strategy}
    if "keep_empty_features" in inspect.signature(SimpleImputer).parameters:
        kwargs["keep_empty_features"] = True
    return SimpleImputer(**kwargs)


def _one_hot_encoder() -> OneHotEncoder:
    if "sparse_output" in inspect.signature(OneHotEncoder).parameters:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    return OneHotEncoder(handle_unknown="ignore", sparse=False)


def _fit_model(model: Pipeline, model_name: str, x: pd.DataFrame, y: np.ndarray) -> None:
    fit_params: dict[str, Any] = {}
    if model_name == "hist_gradient_boosting":
        fit_params["model__sample_weight"] = _balanced_sample_weight(y)
    model.fit(x, y, **fit_params)


def _balanced_sample_weight(y: np.ndarray) -> np.ndarray:
    labels = np.asarray(y, dtype=int)
    weights = np.ones(len(labels), dtype=float)
    counts = np.bincount(labels, minlength=2)
    for cls in range(len(counts)):
        if counts[cls] > 0:
            weights[labels == cls] = len(labels) / (len(counts) * counts[cls])
    return weights


def compute_metrics(y_true: Iterable[int], y_score: Iterable[float], threshold: float | Iterable[float], calibration_bins: int = 10) -> dict[str, float]:
    y = np.asarray(list(y_true), dtype=int)
    score = np.asarray(list(y_score), dtype=float)
    threshold_arr = np.asarray(threshold, dtype=float)
    if threshold_arr.ndim == 0:
        threshold_arr = np.full(len(score), float(threshold_arr), dtype=float)
    pred = (score >= threshold_arr).astype(int)
    precision, recall, _, _ = precision_recall_fscore_support(y, pred, zero_division=0)
    sensitivity = recall[1] if len(recall) > 1 else 0.0
    specificity = recall[0] if len(recall) > 0 else 0.0
    return {
        "auroc": _safe_metric(lambda: roc_auc_score(y, score)),
        "auprc": _safe_metric(lambda: average_precision_score(y, score)),
        "balanced_accuracy": float(balanced_accuracy_score(y, pred)),
        "macro_f1": float(f1_score(y, pred, average="macro", zero_division=0)),
        "sensitivity": float(sensitivity),
        "specificity": float(specificity),
        "accuracy": float(accuracy_score(y, pred)),
        "brier_score": _safe_metric(lambda: brier_score_loss(y, score)),
        "ece": calibration_error(y, score, calibration_bins),
        "positive_prediction_rate": float(np.mean(pred)),
    }


def calibration_error(y_true: np.ndarray, y_score: np.ndarray, bins: int) -> float:
    edges = np.linspace(0.0, 1.0, bins + 1)
    ece = 0.0
    for left, right in zip(edges[:-1], edges[1:]):
        if right == 1.0:
            mask = (y_score >= left) & (y_score <= right)
        else:
            mask = (y_score >= left) & (y_score < right)
        if not np.any(mask):
            continue
        ece += float(np.mean(mask)) * abs(float(np.mean(y_score[mask])) - float(np.mean(y_true[mask])))
    return float(ece)


def _pooled_metrics(predictions: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
    rows = []
    if predictions.empty:
        return pd.DataFrame()
    group_cols = ["cv_protocol", "cohort_name", "modality", "device", "task", "feature_set", "model", "seed"]
    for key, group in predictions.groupby(group_cols, dropna=False):
        base = dict(zip(group_cols, key))
        for threshold_type, threshold in [("fixed_0_5", 0.5), ("inner_cv", group["fold_specific_threshold"].to_numpy(dtype=float))]:
            fold_values = []
            for _, fold_group in group.groupby("outer_fold"):
                fold_threshold = 0.5 if threshold_type == "fixed_0_5" else fold_group["fold_specific_threshold"].to_numpy(dtype=float)
                fold_values.append(compute_metrics(fold_group["label"], fold_group["probability"], fold_threshold, config["protocol"]["calibration_bins"]))
            pooled = compute_metrics(group["label"], group["probability"], threshold, config["protocol"]["calibration_bins"])
            row = {
                **base,
                "threshold_type": threshold_type,
                "threshold": 0.5 if threshold_type == "fixed_0_5" else math.nan,
                "n_subjects": int(group["L_id"].nunique()),
                "n_positive": int(group.drop_duplicates("L_id")["label"].sum()),
                "n_negative": int(group["L_id"].nunique() - group.drop_duplicates("L_id")["label"].sum()),
                **pooled,
            }
            for metric in METRIC_NAMES:
                vals = [m[metric] for m in fold_values if metric in m and math.isfinite(m[metric])]
                row[f"{metric}_fold_mean"] = float(np.mean(vals)) if vals else math.nan
                row[f"{metric}_fold_std"] = float(np.std(vals, ddof=1)) if len(vals) > 1 else math.nan
            rows.append(row)
    return pd.DataFrame(rows)


def _bootstrap_table(predictions: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
    n_boot = int(config.get("bootstrap", {}).get("n_resamples", 1000))
    seed = int(config.get("bootstrap", {}).get("seed", 20260707))
    rows = []
    if predictions.empty:
        return pd.DataFrame()
    group_cols = ["cv_protocol", "cohort_name", "modality", "device", "task", "feature_set", "model", "seed"]
    groups = list(predictions.groupby(group_cols, dropna=False))
    print(f"[goal2_7][bootstrap] groups={len(groups)} n_resamples={n_boot}", flush=True)
    for group_index, (key, group) in enumerate(groups, start=1):
        if group_index == 1 or group_index % 25 == 0 or group_index == len(groups):
            print(f"[goal2_7][bootstrap] {group_index}/{len(groups)} {key}", flush=True)
        base = dict(zip(group_cols, key))
        y = group["label"].to_numpy(dtype=int)
        score = group["probability"].to_numpy(dtype=float)
        thresholds = group["fold_specific_threshold"].to_numpy(dtype=float)
        rng = np.random.default_rng(_stable_seed(seed, *map(str, key)))
        weights = _bootstrap_weights(len(group), n_boot, rng)
        score_samples = _weighted_score_metric_samples(y, score, weights, config["protocol"]["calibration_bins"])
        for threshold_type in ["fixed_0_5", "inner_cv"]:
            threshold = 0.5 if threshold_type == "fixed_0_5" else thresholds
            samples = dict(score_samples)
            samples.update(_weighted_threshold_metric_samples(y, score, threshold, weights))
            for metric, values in samples.items():
                low, high = _ci(values)
                rows.append({**base, "threshold_type": threshold_type, "metric": metric, "ci_low": low, "ci_high": high, "n_bootstrap": n_boot})
    return pd.DataFrame(rows)


def _paired_comparisons(predictions: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
    if predictions.empty:
        return pd.DataFrame()
    pairs = [
        ("signal", "demographics"),
        ("signal_demographics", "demographics"),
        ("signal_qc", "qc"),
        ("signal_qc_demographics", "qc_demographics"),
        ("signal_qc_demographics", "demographics"),
        ("signal_demographics", "signal"),
        ("signal_qc_demographics", "signal_qc"),
        ("face", "demographics"),
        ("face_demographics", "demographics"),
        ("face_qc", "qc"),
        ("face_qc_demographics", "qc_demographics"),
        ("face_qc_demographics", "demographics"),
        ("face", "background"),
        ("face", "full_frame"),
        ("face", "metadata"),
        ("face", "qc"),
        ("face_demographics", "background_demographics"),
        ("modality", "demographics"),
        ("modality_demographics", "demographics"),
        ("modality_qc_demographics", "qc_demographics"),
    ]
    n_boot = int(config.get("bootstrap", {}).get("paired_n_resamples", 1000))
    seed = int(config.get("bootstrap", {}).get("paired_seed", 20260708))
    rows = []
    group_cols = ["cv_protocol", "cohort_name", "modality", "device", "task", "model", "seed"]
    groups = list(predictions.groupby(group_cols, dropna=False))
    print(f"[goal2_7][paired] groups={len(groups)} n_resamples={n_boot}", flush=True)
    for group_index, (key, group) in enumerate(groups, start=1):
        if group_index == 1 or group_index % 25 == 0 or group_index == len(groups):
            print(f"[goal2_7][paired] {group_index}/{len(groups)} {key}", flush=True)
        base = dict(zip(group_cols, key))
        for left, right in pairs:
            a = group[group["feature_set"] == left]
            b = group[group["feature_set"] == right]
            if a.empty or b.empty:
                continue
            merged = a[["L_id", "label", "probability", "outer_fold"]].merge(
                b[["L_id", "label", "probability", "outer_fold"]],
                on=["L_id", "outer_fold"],
                suffixes=("_a", "_b"),
            )
            if len(merged) < 10:
                continue
            y = merged["label_a"].to_numpy(dtype=int)
            a_score = merged["probability_a"].to_numpy(dtype=float)
            b_score = merged["probability_b"].to_numpy(dtype=float)
            diffs = _paired_bootstrap(y, a_score, b_score, n_boot, _stable_seed(seed, *map(str, key), left, right))
            fold_dir = []
            for _, fg in merged.groupby("outer_fold"):
                fold_dir.append(_safe_metric(lambda fg=fg: roc_auc_score(fg["label_a"], fg["probability_a"]) - roc_auc_score(fg["label_b"], fg["probability_b"])))
            rows.append(
                {
                    **base,
                    "feature_set_a": left,
                    "feature_set_b": right,
                    "comparison": f"{left}_vs_{right}",
                    "n_subjects": len(merged),
                    "auroc_diff": _safe_metric(lambda: roc_auc_score(y, a_score) - roc_auc_score(y, b_score)),
                    "auroc_diff_ci_low": diffs["auroc"][0],
                    "auroc_diff_ci_high": diffs["auroc"][1],
                    "auprc_diff": _safe_metric(lambda: average_precision_score(y, a_score) - average_precision_score(y, b_score)),
                    "auprc_diff_ci_low": diffs["auprc"][0],
                    "auprc_diff_ci_high": diffs["auprc"][1],
                    "fold_direction_consistency": int(sum(1 for value in fold_dir if value > 0)),
                    "folds_compared": int(len(fold_dir)),
                    "n_bootstrap": n_boot,
                }
            )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    consistency_cols = [col for col in ["cohort_name", "modality", "device", "task", "model", "seed", "comparison"] if col in out.columns]
    statuses = []
    for _, group in out.groupby(consistency_cols, dropna=False):
        signs = group.set_index("cv_protocol")["auroc_diff"].apply(lambda v: 1 if v > 0 else (-1 if v < 0 else 0)).to_dict()
        consistent = int("standard_cv" in signs and "group_cv" in signs and signs["standard_cv"] == signs["group_cv"])
        for idx in group.index:
            statuses.append((idx, consistent))
    status_map = dict(statuses)
    out["protocol_consistent_direction"] = [status_map.get(idx, 0) for idx in out.index]
    return out


def _paired_bootstrap(y: np.ndarray, a_score: np.ndarray, b_score: np.ndarray, n_boot: int, seed: int) -> dict[str, tuple[float, float]]:
    rng = np.random.default_rng(seed)
    weights = _bootstrap_weights(len(y), n_boot, rng)
    values = {
        "auroc": _weighted_auc_samples(y, a_score, weights) - _weighted_auc_samples(y, b_score, weights),
        "auprc": _weighted_average_precision_samples(y, a_score, weights) - _weighted_average_precision_samples(y, b_score, weights),
    }
    return {metric: _ci(vals) for metric, vals in values.items()}


def _bootstrap_weights(n_subjects: int, n_boot: int, rng: np.random.Generator) -> np.ndarray:
    if n_subjects <= 0 or n_boot <= 0:
        return np.zeros((0, 0), dtype=float)
    probabilities = np.full(int(n_subjects), 1.0 / float(n_subjects), dtype=float)
    return rng.multinomial(int(n_subjects), probabilities, size=int(n_boot)).astype(float)


def _weighted_score_metric_samples(y: np.ndarray, score: np.ndarray, weights: np.ndarray, calibration_bins: int) -> dict[str, np.ndarray]:
    y = np.asarray(y, dtype=int)
    score = np.asarray(score, dtype=float)
    total = weights.sum(axis=1)
    residual = score - y
    brier = np.divide(
        (weights * np.square(residual)).sum(axis=1),
        total,
        out=np.full(weights.shape[0], math.nan, dtype=float),
        where=total > 0,
    )
    return {
        "auroc": _weighted_auc_samples(y, score, weights),
        "auprc": _weighted_average_precision_samples(y, score, weights),
        "brier_score": brier,
        "ece": _weighted_ece_samples(y, score, weights, calibration_bins),
    }


def _weighted_threshold_metric_samples(y: np.ndarray, score: np.ndarray, threshold: float | np.ndarray, weights: np.ndarray) -> dict[str, np.ndarray]:
    y = np.asarray(y, dtype=int)
    score = np.asarray(score, dtype=float)
    threshold_arr = np.asarray(threshold, dtype=float)
    if threshold_arr.ndim == 0:
        threshold_arr = np.full(len(score), float(threshold_arr), dtype=float)
    pred = score >= threshold_arr
    positive = y == 1
    negative = ~positive
    tp = weights[:, positive & pred].sum(axis=1)
    fp = weights[:, negative & pred].sum(axis=1)
    tn = weights[:, negative & ~pred].sum(axis=1)
    fn = weights[:, positive & ~pred].sum(axis=1)
    total = tp + fp + tn + fn
    sensitivity = _safe_divide(tp, tp + fn)
    specificity = _safe_divide(tn, tn + fp)
    f1_positive = _safe_divide(2.0 * tp, 2.0 * tp + fp + fn)
    f1_negative = _safe_divide(2.0 * tn, 2.0 * tn + fn + fp)
    return {
        "balanced_accuracy": 0.5 * (sensitivity + specificity),
        "macro_f1": 0.5 * (f1_positive + f1_negative),
        "sensitivity": sensitivity,
        "specificity": specificity,
        "accuracy": _safe_divide(tp + tn, total),
        "positive_prediction_rate": _safe_divide(tp + fp, total),
    }


def _weighted_auc_samples(y: np.ndarray, score: np.ndarray, weights: np.ndarray) -> np.ndarray:
    y = np.asarray(y, dtype=int)
    score = np.asarray(score, dtype=float)
    order = np.argsort(score, kind="mergesort")
    sorted_score = score[order]
    sorted_y = y[order].astype(float)
    sorted_weights = weights[:, order]
    pos_weights = sorted_weights * sorted_y
    neg_weights = sorted_weights * (1.0 - sorted_y)
    pos_total = pos_weights.sum(axis=1)
    neg_total = neg_weights.sum(axis=1)
    cum_neg_before = np.cumsum(neg_weights, axis=1) - neg_weights
    concordant = (pos_weights * cum_neg_before).sum(axis=1)
    tie_edges = np.flatnonzero(np.diff(sorted_score) != 0) + 1
    starts = np.r_[0, tie_edges]
    ends = np.r_[tie_edges, len(sorted_score)]
    for start, end in zip(starts, ends):
        if end - start <= 1:
            continue
        block_pos = pos_weights[:, start:end].sum(axis=1)
        block_neg = neg_weights[:, start:end].sum(axis=1)
        current = (pos_weights[:, start:end] * cum_neg_before[:, start:end]).sum(axis=1)
        exact = block_pos * (cum_neg_before[:, start] + 0.5 * block_neg)
        concordant += exact - current
    denom = pos_total * neg_total
    return np.divide(concordant, denom, out=np.full(weights.shape[0], math.nan, dtype=float), where=denom > 0)


def _weighted_average_precision_samples(y: np.ndarray, score: np.ndarray, weights: np.ndarray) -> np.ndarray:
    y = np.asarray(y, dtype=int)
    score = np.asarray(score, dtype=float)
    order = np.argsort(-score, kind="mergesort")
    sorted_score = score[order]
    sorted_y = y[order].astype(float)
    sorted_weights = weights[:, order]
    pos_weights = sorted_weights * sorted_y
    pos_total = pos_weights.sum(axis=1)
    cumulative_pos = np.cumsum(pos_weights, axis=1)
    cumulative_total = np.cumsum(sorted_weights, axis=1)
    precision = np.divide(cumulative_pos, cumulative_total, out=np.zeros_like(cumulative_pos), where=cumulative_total > 0)
    numerator = (precision * pos_weights).sum(axis=1)
    tie_edges = np.flatnonzero(np.diff(sorted_score) != 0) + 1
    starts = np.r_[0, tie_edges]
    ends = np.r_[tie_edges, len(sorted_score)]
    for start, end in zip(starts, ends):
        if end - start <= 1:
            continue
        block_pos = pos_weights[:, start:end].sum(axis=1)
        current = (precision[:, start:end] * pos_weights[:, start:end]).sum(axis=1)
        block_precision = np.divide(
            cumulative_pos[:, end - 1],
            cumulative_total[:, end - 1],
            out=np.zeros(weights.shape[0], dtype=float),
            where=cumulative_total[:, end - 1] > 0,
        )
        numerator += block_precision * block_pos - current
    return np.divide(numerator, pos_total, out=np.full(weights.shape[0], math.nan, dtype=float), where=pos_total > 0)


def _weighted_ece_samples(y: np.ndarray, score: np.ndarray, weights: np.ndarray, bins: int) -> np.ndarray:
    y = np.asarray(y, dtype=float)
    score = np.asarray(score, dtype=float)
    total = weights.sum(axis=1)
    ece = np.zeros(weights.shape[0], dtype=float)
    edges = np.linspace(0.0, 1.0, int(bins) + 1)
    for left, right in zip(edges[:-1], edges[1:]):
        if right == 1.0:
            mask = (score >= left) & (score <= right)
        else:
            mask = (score >= left) & (score < right)
        if not np.any(mask):
            continue
        bin_weight = weights[:, mask].sum(axis=1)
        avg_conf = _safe_divide((weights[:, mask] * score[mask]).sum(axis=1), bin_weight)
        avg_label = _safe_divide((weights[:, mask] * y[mask]).sum(axis=1), bin_weight)
        ece += np.divide(bin_weight, total, out=np.zeros_like(bin_weight), where=total > 0) * np.abs(avg_conf - avg_label)
    ece[total <= 0] = math.nan
    return ece


def _safe_divide(numerator: np.ndarray, denominator: np.ndarray) -> np.ndarray:
    return np.divide(
        numerator,
        denominator,
        out=np.zeros_like(np.asarray(numerator, dtype=float)),
        where=np.asarray(denominator, dtype=float) > 0,
    )


def _ci(values: Iterable[float]) -> tuple[float, float]:
    arr = np.asarray(list(values), dtype=float)
    arr = arr[np.isfinite(arr)]
    return tuple(np.percentile(arr, [2.5, 97.5])) if len(arr) else (math.nan, math.nan)


def _combine_signal_qc(signal: pd.DataFrame, qc: pd.DataFrame, config: dict[str, Any], modality: str, device: str, task: str) -> pd.DataFrame:
    split = add_clean_demographics(cv_subjects(config), config)
    label_col = config.get("run", {}).get("label_column", "primary_label_nonhealthy")
    signal_meta = [col for col in ["feature_version", "preprocessing_version", "event_validity_status", "face_feature_blocked"] if col in signal.columns]
    qc_meta = [col for col in ["event_validity_status"] if col in qc.columns and col not in signal_meta]
    signal_cols = ["L_id", *signal_meta, *[col for col in signal.columns if col.startswith("signal_")]]
    qc_cols = ["L_id", *[col for col in qc.columns if col.startswith("qc_")]]
    if qc_meta:
        qc_cols.extend(qc_meta)
    merged = split.merge(signal[signal_cols], on="L_id", how="inner").merge(qc[qc_cols], on="L_id", how="inner", suffixes=("", "_qc"))
    if "event_validity_status" not in merged.columns and "event_validity_status_qc" in merged.columns:
        merged["event_validity_status"] = merged["event_validity_status_qc"]
    merged["modality"] = modality
    merged["device"] = device
    merged["task"] = task
    merged[label_col] = merged[label_col].astype(int)
    return merged.sort_values("L_id").reset_index(drop=True)


def _dataset(
    frame: pd.DataFrame,
    modality: str,
    device: str,
    task: str,
    feature_set: str,
    cohort_name: str,
    numeric: list[str],
    categorical: list[str],
    model_family: str,
) -> GoalDataset:
    numeric = [col for col in dict.fromkeys(numeric) if col in frame.columns]
    categorical = [col for col in dict.fromkeys(categorical) if col in frame.columns]
    return GoalDataset(
        cohort_name=cohort_name,
        modality=modality,
        device=device,
        task=task,
        feature_set=feature_set,
        frame=frame.copy(),
        numeric_columns=numeric,
        categorical_columns=categorical,
        model_family=model_family,
    )


def _models_for_dataset(dataset: GoalDataset, config: dict[str, Any]) -> list[str]:
    if dataset.model_family == "no_information":
        return ["no_information_prior"]
    if dataset.model_family == "face_embedding":
        return list(config["models"].get("face_embedding", ["logistic_regression", "hist_gradient_boosting"]))
    return list(config["models"].get("tabular", ["logistic_regression", "random_forest", "hist_gradient_boosting"]))


def _visual_columns(dataset: GoalDataset) -> list[str]:
    if dataset.modality != "face":
        return []
    visual_prefixes = (
        "signal_face_",
        "signal_full_",
        "signal_background_",
    )
    return [col for col in dataset.numeric_columns if col.startswith(visual_prefixes)]


def _numeric_prefixed(frame: pd.DataFrame, prefix: str) -> list[str]:
    cols = []
    for col in frame.columns:
        if col.startswith(prefix) and pd.api.types.is_numeric_dtype(frame[col]):
            cols.append(col)
    return cols


def _numeric_prefixed_excluding(frame: pd.DataFrame, prefix: str, exclude_prefixes: list[str]) -> list[str]:
    return [
        col
        for col in _numeric_prefixed(frame, prefix)
        if not any(col.startswith(exclude) for exclude in exclude_prefixes)
    ]


def _numeric_any_prefix(frame: pd.DataFrame, prefixes: list[str]) -> list[str]:
    return [
        col
        for col in frame.columns
        if any(col.startswith(prefix) for prefix in prefixes) and pd.api.types.is_numeric_dtype(frame[col])
    ]


def _numeric_any_prefix_excluding(frame: pd.DataFrame, prefixes: list[str], exclude_prefixes: list[str]) -> list[str]:
    return [
        col
        for col in _numeric_any_prefix(frame, prefixes)
        if not any(col.startswith(exclude) for exclude in exclude_prefixes)
    ]


def _demo_numeric(config: dict[str, Any]) -> list[str]:
    return list(config["demographics"].get("main_numeric_columns", config["demographics"].get("numeric_columns", [])))


def _demo_categorical(config: dict[str, Any]) -> list[str]:
    return list(config["demographics"].get("main_categorical_columns", config["demographics"].get("categorical_columns", [])))


def _predict_proba(model: Any, x: pd.DataFrame) -> np.ndarray:
    proba = model.predict_proba(x)
    return np.asarray(proba, dtype=float)[:, 1]


def _row_values(frame: pd.DataFrame, column: str, default: str) -> np.ndarray:
    if column not in frame.columns:
        return np.full(len(frame), default, dtype=object)
    return frame[column].fillna(default).astype(str).to_numpy()


def _select_threshold(y: np.ndarray, score: np.ndarray, grid: list[float]) -> float:
    best = 0.5
    best_value = -math.inf
    for threshold in grid:
        pred = (score >= float(threshold)).astype(int)
        value = balanced_accuracy_score(y, pred)
        if value > best_value:
            best_value = value
            best = float(threshold)
    return best


def _context(dataset: GoalDataset, model_name: str, seed: int) -> dict[str, Any]:
    return {
        "cv_protocol": dataset.cv_protocol,
        "cohort_name": dataset.cohort_name,
        "modality": dataset.modality,
        "device": dataset.device,
        "task": dataset.task,
        "feature_set": dataset.feature_set,
        "model": model_name,
        "seed": seed,
        "feature_count": len(dataset.feature_columns),
    }


def _feature_counts(datasets: list[GoalDataset]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "cohort_name": d.cohort_name,
                "modality": d.modality,
                "device": d.device,
                "task": d.task,
                "feature_set": d.feature_set,
                "n_subjects": d.frame["L_id"].nunique(),
                "feature_count": len(d.feature_columns),
                "numeric_count": len(d.numeric_columns),
                "categorical_count": len(d.categorical_columns),
            }
            for d in datasets
        ]
    )


def _native_summary(pooled: pd.DataFrame) -> pd.DataFrame:
    if pooled.empty:
        return pooled
    native = pooled[pooled["cohort_name"].astype(str).str.contains("_native|v1_features", regex=True)].copy()
    if native.empty:
        return native
    return native.sort_values(["cohort_name", "auroc", "auprc"], ascending=[True, False, False]).groupby("cohort_name").head(5)


def _core3_summary(pooled: pd.DataFrame) -> pd.DataFrame:
    return pooled[pooled["cohort_name"] == "core3_rest_yiruidvft_selfintro_intersection"].copy() if not pooled.empty else pooled


def _shortcut_summary(pooled: pd.DataFrame) -> pd.DataFrame:
    if pooled.empty:
        return pooled
    mask = (pooled["modality"] == "shortcut") | pooled["feature_set"].isin(["qc", "metadata", "background"])
    return pooled[mask].copy()


def _demographics_decomposition(pooled: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
    if pooled.empty:
        return pooled
    demo_sets = set(config.get("demographics", {}).get("decomposition_sets", {}))
    demo_sets.add("demographics")
    out = pooled[(pooled["feature_set"].isin(demo_sets)) & (pooled["threshold_type"] == "inner_cv")].copy()
    return out.reset_index(drop=True)


def _standard_vs_group(pooled: pd.DataFrame) -> pd.DataFrame:
    if pooled.empty or "cv_protocol" not in pooled.columns:
        return pd.DataFrame()
    inner = pooled[pooled["threshold_type"] == "inner_cv"].copy()
    keys = ["cohort_name", "modality", "device", "task", "feature_set", "model", "seed"]
    standard = inner[inner["cv_protocol"] == "standard_cv"][keys + ["auroc", "auprc", "balanced_accuracy", "macro_f1"]]
    group = inner[inner["cv_protocol"] == "group_cv"][keys + ["auroc", "auprc", "balanced_accuracy", "macro_f1"]]
    merged = standard.merge(group, on=keys, suffixes=("_standard_cv", "_group_cv"))
    for metric in ["auroc", "auprc", "balanced_accuracy", "macro_f1"]:
        merged[f"{metric}_delta_standard_minus_group"] = merged[f"{metric}_standard_cv"] - merged[f"{metric}_group_cv"]
    return merged


def _threshold_diagnostics(predictions: pd.DataFrame, fold_metrics: pd.DataFrame) -> pd.DataFrame:
    if predictions.empty:
        return pd.DataFrame()
    keys = ["cv_protocol", "cohort_name", "modality", "device", "task", "feature_set", "model", "seed", "outer_fold"]
    rows = predictions.groupby(keys, dropna=False).agg(
        n_subjects=("L_id", "nunique"),
        selected_threshold_per_fold=("fold_specific_threshold", "first"),
        predicted_positive_rate=("predicted_label", "mean"),
    ).reset_index()
    rows["threshold_source"] = "inner_cv_outer_train_only"
    return rows


def _face_strict_control_summary(config: dict[str, Any]) -> pd.DataFrame:
    rows = []
    for task, spec in config.get("face", {}).get("tasks", {}).items():
        path = project_path(spec["qc_features"])
        if not path.exists():
            continue
        df = pd.read_csv(path, dtype={"L_id": str})
        rows.append(
            {
                "task": task,
                "n_videos": int(len(df)),
                "strict_face_valid_videos": int((pd.to_numeric(df.get("qc_face_feature_blocked", 1), errors="coerce").fillna(1) == 0).sum()),
                "blocked_videos": int((pd.to_numeric(df.get("qc_face_feature_blocked", 1), errors="coerce").fillna(1) == 1).sum()),
                "mean_detection_rate": float(pd.to_numeric(df.get("qc_face_detection_rate"), errors="coerce").mean()),
                "mean_effective_face_frames": float(pd.to_numeric(df.get("qc_effective_face_frame_count"), errors="coerce").mean()),
                "fallback_videos": int(pd.to_numeric(df.get("qc_detector_fallback_used", 0), errors="coerce").fillna(0).sum()),
                "multi_face_rate_mean": float(pd.to_numeric(df.get("qc_multi_face_rate"), errors="coerce").mean()),
                "audio_used_sum": int(pd.to_numeric(df.get("qc_audio_used", 0), errors="coerce").fillna(0).sum()),
            }
        )
    return pd.DataFrame(rows)


def _event_validity_summary(config: dict[str, Any], modality: str) -> pd.DataFrame:
    rows = []
    if modality == "eeg":
        for task, spec in config.get("eeg", {}).get("tasks", {}).items():
            path = project_path(spec["qc_features"])
            if not path.exists():
                continue
            df = pd.read_csv(path, dtype={"L_id": str})
            status_col = "event_validity_status" if "event_validity_status" in df.columns else "task_status"
            for status, group in df.groupby(status_col, dropna=False):
                rows.append({"modality": "eeg", "device": "", "task": task, "event_validity_status": status, "subjects": int(group["L_id"].nunique())})
    elif modality == "fnirs":
        out_dir = config.get("fnirs", {}).get("outputs", {}).get("dir", "artifacts/goal2_7/fnirs")
        for device in config.get("fnirs", {}).get("devices", {}):
            for task in config.get("fnirs", {}).get("tasks", []):
                path = project_path(f"{out_dir}/{device}_{task}_qc_features.csv")
                if not path.exists():
                    continue
                df = pd.read_csv(path, dtype={"L_id": str})
                status_col = "event_validity_status" if "event_validity_status" in df.columns else "qc_task_response_status"
                for status, group in df.groupby(status_col, dropna=False):
                    rows.append({"modality": "fnirs", "device": device, "task": task, "event_validity_status": status, "subjects": int(group["L_id"].nunique())})
    return pd.DataFrame(rows)


def _exclusion_summary(config: dict[str, Any]) -> pd.DataFrame:
    rows = []
    paths: list[tuple[str, Path]] = []
    for spec in config.get("eeg", {}).get("tasks", {}).values():
        paths.append(("eeg", project_path(spec["qc_features"])))
    fnirs_dir = config.get("fnirs", {}).get("outputs", {}).get("dir", "artifacts/goal2_7/fnirs")
    for device in config.get("fnirs", {}).get("devices", {}):
        for task in config.get("fnirs", {}).get("tasks", []):
            paths.append(("fnirs", project_path(f"{fnirs_dir}/{device}_{task}_qc_features.csv")))
    for spec in config.get("face", {}).get("tasks", {}).values():
        paths.append(("face", project_path(spec["qc_features"])))
    for modality, path in paths:
        if not path.exists():
            continue
        df = pd.read_csv(path, dtype={"L_id": str})
        status_col = "qc_feature_status"
        reason_col = "qc_failure_reason"
        if status_col not in df.columns:
            continue
        for (status, reason), group in df.groupby([status_col, reason_col], dropna=False):
            rows.append({"modality": modality, "file": str(path), "qc_feature_status": status, "qc_failure_reason": reason, "subjects": len(group)})
    return pd.DataFrame(rows)


def _safe_metric(fn: Any) -> float:
    try:
        value = fn()
    except Exception:
        return math.nan
    return float(value) if value is not None and math.isfinite(float(value)) else math.nan


def _stable_seed(seed: int, *parts: str) -> int:
    payload = "|".join([str(seed), *parts])
    return int(hashlib.sha1(payload.encode("utf-8")).hexdigest()[:8], 16)


def _combined_config(config_path: str | Path) -> dict[str, Any]:
    base = load_goal_config(config_path)
    for extra_path in ["configs/goal2_7/bootstrap.yaml", "configs/goal2_7/eeg.yaml", "configs/goal2_7/fnirs.yaml", "configs/goal2_7/face.yaml"]:
        extra = load_goal_config(extra_path)
        for key in ["bootstrap", "eeg", "fnirs", "face"]:
            if key in extra:
                base[key] = extra[key]
    return base
