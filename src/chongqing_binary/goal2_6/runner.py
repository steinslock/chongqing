"""Fixed-CV Goal 2.6 model runner."""

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

    @property
    def feature_columns(self) -> list[str]:
        return self.numeric_columns + self.categorical_columns


def run_goal2_6(
    modalities: list[str] | None = None,
    config_path: str | Path = "configs/goal2_6/models.yaml",
) -> dict[str, Any]:
    config = _combined_config(config_path)
    requested = set(modalities or ["eeg", "fnirs", "face", "core3", "shortcut"])
    datasets = build_native_datasets(config, requested)
    if "core3" in requested:
        datasets.extend(build_core3_datasets(config))
    if "shortcut" in requested:
        datasets.extend(build_shortcut_datasets(config))
    results = run_datasets(datasets, config)
    write_outputs(results, datasets, config)
    return {
        "datasets": len(datasets),
        "pooled_metrics": len(results["pooled_metrics"]),
        "predictions": len(results["predictions"]),
        "outputs": config["outputs"],
    }


def build_native_datasets(config: dict[str, Any], requested: set[str]) -> list[GoalDataset]:
    out: list[GoalDataset] = []
    if "eeg" in requested:
        out.extend(_eeg_datasets(config))
    if "fnirs" in requested:
        out.extend(_fnirs_datasets(config))
    if "face" in requested:
        out.extend(_face_datasets(config))
    return out


def _eeg_datasets(config: dict[str, Any]) -> list[GoalDataset]:
    out: list[GoalDataset] = []
    for task, spec in config.get("eeg", {}).get("tasks", {}).items():
        if not project_path(spec["signal_features"]).exists() or not project_path(spec["qc_features"]).exists():
            continue
        signal = pd.read_csv(project_path(spec["signal_features"]), dtype={"L_id": str})
        qc = pd.read_csv(project_path(spec["qc_features"]), dtype={"L_id": str})
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
        signal = pd.read_csv(project_path(spec["signal_features"]), dtype={"L_id": str})
        qc = pd.read_csv(project_path(spec["qc_features"]), dtype={"L_id": str})
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
        background_cols = _numeric_prefixed(cohort, "signal_background_")
        cohort_name = f"face_{task}_native"
        out.append(_dataset(cohort, "face", "", task, "no_information", cohort_name, [], [], "no_information"))
        out.append(_dataset(cohort, "face", "", task, "demographics", cohort_name, demo_num, demo_cat, "face_embedding"))
        out.append(_dataset(cohort, "face", "", task, "qc", cohort_name, qc_cols, metadata_cat, "face_embedding"))
        out.append(_dataset(cohort, "face", "", task, "metadata", cohort_name, metadata_cols, metadata_cat, "face_embedding"))
        out.append(_dataset(cohort, "face", "", task, "full_frame", cohort_name, full_cols, [], "face_embedding"))
        out.append(_dataset(cohort, "face", "", task, "face_crop", cohort_name, face_cols, [], "face_embedding"))
        out.append(_dataset(cohort, "face", "", task, "background", cohort_name, background_cols, [], "face_embedding"))
        out.append(_dataset(cohort, "face", "", task, "face_qc", cohort_name, face_cols + qc_cols, metadata_cat, "face_embedding"))
        out.append(_dataset(cohort, "face", "", task, "face_demographics", cohort_name, face_cols + demo_num, demo_cat, "face_embedding"))
        out.append(_dataset(cohort, "face", "", task, "face_qc_demographics", cohort_name, face_cols + qc_cols + demo_num, metadata_cat + demo_cat, "face_embedding"))
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
    background_cols = _numeric_any_prefix(frame, ["signal_background_self_intro_", "signal_background_task_"])
    cohort_name = "face_two_video_native"
    return [
        _dataset(frame, "face", "", "two_video", "no_information", cohort_name, [], [], "no_information"),
        _dataset(frame, "face", "", "two_video", "demographics", cohort_name, demo_num, demo_cat, "face_embedding"),
        _dataset(frame, "face", "", "two_video", "qc", cohort_name, qc_cols, metadata_cat, "face_embedding"),
        _dataset(frame, "face", "", "two_video", "metadata", cohort_name, metadata_cols, metadata_cat, "face_embedding"),
        _dataset(frame, "face", "", "two_video", "full_frame", cohort_name, full_cols, [], "face_embedding"),
        _dataset(frame, "face", "", "two_video", "face_crop", cohort_name, face_cols, [], "face_embedding"),
        _dataset(frame, "face", "", "two_video", "background", cohort_name, background_cols, [], "face_embedding"),
        _dataset(frame, "face", "", "two_video", "face_qc", cohort_name, face_cols + qc_cols, metadata_cat, "face_embedding"),
        _dataset(frame, "face", "", "two_video", "face_demographics", cohort_name, face_cols + demo_num, demo_cat, "face_embedding"),
        _dataset(frame, "face", "", "two_video", "face_qc_demographics", cohort_name, face_cols + qc_cols + demo_num, metadata_cat + demo_cat, "face_embedding"),
    ]


def _prefix_face_task_frame(frame: pd.DataFrame, task_name: str, prefix: str) -> pd.DataFrame:
    rename = {}
    for col in frame.columns:
        if not col.startswith(prefix):
            continue
        if prefix == "signal_":
            for variant in ["signal_face_", "signal_full_", "signal_background_"]:
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
    return [
        _dataset(cohort, modality, device, task, "no_information", cohort_name, [], [], "no_information"),
        _dataset(cohort, modality, device, task, "demographics", cohort_name, demo_num, demo_cat, model_family),
        _dataset(cohort, modality, device, task, "qc", cohort_name, qc_cols, [], model_family),
        _dataset(cohort, modality, device, task, "signal", cohort_name, signal_cols, [], model_family),
        _dataset(cohort, modality, device, task, "signal_qc", cohort_name, signal_cols + qc_cols, [], model_family),
        _dataset(cohort, modality, device, task, "signal_demographics", cohort_name, signal_cols + demo_num, demo_cat, model_family),
        _dataset(cohort, modality, device, task, "signal_qc_demographics", cohort_name, signal_cols + qc_cols + demo_num, demo_cat, model_family),
    ]


def build_core3_datasets(config: dict[str, Any]) -> list[GoalDataset]:
    core = pd.read_csv(project_path(config["paths"]["core3_qc_file"]), dtype={"L_id": str})
    core = core[core["split_group"].astype(str) == "cv"].copy()
    core_lids = set(core["L_id"])
    candidates: list[tuple[str, str, str, str, str]] = []
    eeg_rest = config.get("eeg", {}).get("tasks", {}).get("rest", {})
    if eeg_rest:
        candidates.append(("eeg", "", "rest", eeg_rest["signal_features"], eeg_rest["qc_features"]))
    fnirs_dir = config.get("fnirs", {}).get("outputs", {}).get("dir", "artifacts/goal2_6/fnirs")
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
        signal = pd.read_csv(project_path(signal_path), dtype={"L_id": str})
        qc = pd.read_csv(project_path(qc_path), dtype={"L_id": str})
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
        cohort_name = "core3_same_cohort"
        out.append(_dataset(subset, modality, device, task, "demographics", cohort_name, demo_num, demo_cat, "face_embedding" if modality == "face" else "tabular"))
        out.append(_dataset(subset, modality, device, task, feature_name, cohort_name, signal_cols, [], "face_embedding" if modality == "face" else "tabular"))
        out.append(_dataset(subset, modality, device, task, f"{feature_name}_demographics", cohort_name, signal_cols + demo_num, demo_cat, "face_embedding" if modality == "face" else "tabular"))
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
                f"[goal2_6] {job_index}/{total_jobs} dataset={dataset_index}/{len(datasets)} "
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
                pred = pd.DataFrame(
                    {
                        "L_id": val["L_id"].astype(str).to_numpy(),
                        "label": y_val,
                        "modality": dataset.modality,
                        "device": dataset.device,
                        "task": dataset.task,
                        "feature_set": dataset.feature_set,
                        "model": model_name,
                        "seed": seed,
                        "outer_fold": fold,
                        "probability": prob,
                        "threshold": threshold,
                        "cohort_name": dataset.cohort_name,
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
    bootstrap = _bootstrap_table(predictions, config)
    paired = _paired_comparisons(predictions, config)
    group_robustness = _group_robustness_table(datasets, config) if include_supplemental else pd.DataFrame()
    return {
        "predictions": predictions,
        "fold_metrics": pd.DataFrame(fold_metric_rows),
        "pooled_metrics": pooled,
        "bootstrap": bootstrap,
        "paired": paired,
        "hyperparameters": pd.DataFrame(hyper_rows),
        "pca": pd.DataFrame(pca_rows),
        "group_robustness": group_robustness,
    }


def write_outputs(results: dict[str, Any], datasets: list[GoalDataset], config: dict[str, Any]) -> None:
    outputs = config["outputs"]
    results["predictions"].to_csv(ensure_output(outputs["all_oof_predictions"], config), index=False)
    results["fold_metrics"].to_csv(ensure_output(outputs["all_fold_metrics"], config), index=False)
    results["pooled_metrics"].to_csv(ensure_output(outputs["all_pooled_metrics"], config), index=False)
    results["bootstrap"].to_csv(ensure_output(outputs["bootstrap_ci"], config), index=False)
    results["paired"].to_csv(ensure_output(outputs["paired_comparisons"], config), index=False)
    results["hyperparameters"].to_csv(ensure_output(outputs["selected_hyperparameters"], config), index=False)
    results["pca"].to_csv(ensure_output(outputs["pca_explained_variance"], config), index=False)
    results["group_robustness"].to_csv(ensure_output(outputs["group_robustness_summary"], config), index=False)
    _feature_counts(datasets).to_csv(ensure_output(outputs["feature_counts"], config), index=False)
    _native_summary(results["pooled_metrics"]).to_csv(ensure_output(outputs["native_cohort_summary"], config), index=False)
    _core3_summary(results["pooled_metrics"]).to_csv(ensure_output(outputs["core3_same_cohort_summary"], config), index=False)
    _shortcut_summary(results["pooled_metrics"]).to_csv(ensure_output(outputs["shortcut_baseline_summary"], config), index=False)
    _exclusion_summary(config).to_csv(ensure_output(outputs["exclusion_summary"], config), index=False)
    manifest = {
        "config": config.get("_config_path", ""),
        "n_datasets": len(datasets),
        "n_prediction_rows": int(len(results["predictions"])),
        "n_pooled_rows": int(len(results["pooled_metrics"])),
        "lightgbm_fallback": config.get("fallbacks", {}),
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
    candidates = list(config.get("hyperparameters", {}).get(model_name, [{}]))[:20]
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


def _build_pipeline(dataset: GoalDataset, model_name: str, config: dict[str, Any], seed: int) -> Pipeline:
    dense = True
    transformers = []
    if dataset.numeric_columns:
        transformers.append(
            (
                "num",
                Pipeline(
                    [
                        ("imputer", _simple_imputer("median")),
                        ("scaler", StandardScaler()),
                    ]
                ),
                dataset.numeric_columns,
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
    use_pca = dataset.modality == "face" and len(dataset.numeric_columns) > int(config["protocol"]["max_pca_components"])
    if use_pca:
        n_components = min(int(config["protocol"]["max_pca_components"]), max(2, len(dataset.frame) - 1), len(dataset.numeric_columns))
        steps.append(("pca", PCA(n_components=n_components, svd_solver="randomized", random_state=seed)))
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
    if "pca" not in model.named_steps:
        return {"pca_used": 0, "pca_n_components": 0, "pca_explained_variance_ratio_sum": math.nan}
    pca = model.named_steps["pca"]
    ratio = getattr(pca, "explained_variance_ratio_", np.asarray([], dtype=float))
    return {
        "pca_used": 1,
        "pca_n_components": int(getattr(pca, "n_components_", len(ratio))),
        "pca_explained_variance_ratio_sum": float(np.sum(ratio)) if len(ratio) else math.nan,
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


def compute_metrics(y_true: Iterable[int], y_score: Iterable[float], threshold: float, calibration_bins: int = 10) -> dict[str, float]:
    y = np.asarray(list(y_true), dtype=int)
    score = np.asarray(list(y_score), dtype=float)
    pred = (score >= threshold).astype(int)
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
    group_cols = ["cohort_name", "modality", "device", "task", "feature_set", "model", "seed"]
    for key, group in predictions.groupby(group_cols, dropna=False):
        base = dict(zip(group_cols, key))
        for threshold_type, threshold in [("fixed_0_5", 0.5), ("inner_cv", float(group["threshold"].median()))]:
            fold_values = []
            for _, fold_group in group.groupby("outer_fold"):
                fold_values.append(compute_metrics(fold_group["label"], fold_group["probability"], threshold, config["protocol"]["calibration_bins"]))
            pooled = compute_metrics(group["label"], group["probability"], threshold, config["protocol"]["calibration_bins"])
            row = {
                **base,
                "threshold_type": threshold_type,
                "threshold": threshold,
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
    group_cols = ["cohort_name", "modality", "device", "task", "feature_set", "model", "seed"]
    for key, group in predictions.groupby(group_cols, dropna=False):
        base = dict(zip(group_cols, key))
        y = group["label"].to_numpy(dtype=int)
        score = group["probability"].to_numpy(dtype=float)
        threshold = float(group["threshold"].median())
        rng = np.random.default_rng(_stable_seed(seed, *map(str, key)))
        samples = {metric: [] for metric in METRIC_NAMES}
        for _ in range(n_boot):
            idx = rng.integers(0, len(group), size=len(group))
            metrics = compute_metrics(y[idx], score[idx], threshold, config["protocol"]["calibration_bins"])
            for metric, value in metrics.items():
                if metric in samples and math.isfinite(value):
                    samples[metric].append(value)
        for metric, values in samples.items():
            if values:
                low, high = np.percentile(values, [2.5, 97.5])
            else:
                low, high = math.nan, math.nan
            rows.append({**base, "metric": metric, "ci_low": low, "ci_high": high, "n_bootstrap": n_boot})
    return pd.DataFrame(rows)


def _paired_comparisons(predictions: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
    if predictions.empty:
        return pd.DataFrame()
    pairs = [
        ("signal", "demographics"),
        ("signal", "qc"),
        ("signal_qc_demographics", "signal"),
        ("face_crop", "demographics"),
        ("face_crop", "qc"),
        ("face_crop", "metadata"),
        ("face_crop", "background"),
        ("face_crop", "full_frame"),
        ("modality", "demographics"),
        ("modality_demographics", "modality"),
    ]
    n_boot = int(config.get("bootstrap", {}).get("paired_n_resamples", 1000))
    seed = int(config.get("bootstrap", {}).get("paired_seed", 20260708))
    rows = []
    group_cols = ["cohort_name", "modality", "device", "task", "model", "seed"]
    for key, group in predictions.groupby(group_cols, dropna=False):
        base = dict(zip(group_cols, key))
        for left, right in pairs:
            a = group[group["feature_set"] == left]
            b = group[group["feature_set"] == right]
            if a.empty or b.empty:
                continue
            merged = a[["L_id", "label", "probability", "outer_fold"]].merge(
                b[["L_id", "label", "probability", "outer_fold"]],
                on="L_id",
                suffixes=("_a", "_b"),
            )
            if len(merged) < 10:
                continue
            y = merged["label_a"].to_numpy(dtype=int)
            a_score = merged["probability_a"].to_numpy(dtype=float)
            b_score = merged["probability_b"].to_numpy(dtype=float)
            diffs = _paired_bootstrap(y, a_score, b_score, n_boot, _stable_seed(seed, *map(str, key), left, right))
            fold_dir = []
            for _, fg in merged.groupby("outer_fold_a"):
                fold_dir.append(_safe_metric(lambda fg=fg: roc_auc_score(fg["label_a"], fg["probability_a"]) - roc_auc_score(fg["label_b"], fg["probability_b"])))
            rows.append(
                {
                    **base,
                    "model_a": left,
                    "model_b": right,
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
    return pd.DataFrame(rows)


def _paired_bootstrap(y: np.ndarray, a_score: np.ndarray, b_score: np.ndarray, n_boot: int, seed: int) -> dict[str, tuple[float, float]]:
    rng = np.random.default_rng(seed)
    values = {"auroc": [], "auprc": []}
    for _ in range(n_boot):
        idx = rng.integers(0, len(y), size=len(y))
        yy = y[idx]
        aa = a_score[idx]
        bb = b_score[idx]
        auroc = _safe_metric(lambda: roc_auc_score(yy, aa) - roc_auc_score(yy, bb))
        auprc = _safe_metric(lambda: average_precision_score(yy, aa) - average_precision_score(yy, bb))
        if math.isfinite(auroc):
            values["auroc"].append(auroc)
        if math.isfinite(auprc):
            values["auprc"].append(auprc)
    out = {}
    for metric, vals in values.items():
        out[metric] = tuple(np.percentile(vals, [2.5, 97.5])) if vals else (math.nan, math.nan)
    return out


def _combine_signal_qc(signal: pd.DataFrame, qc: pd.DataFrame, config: dict[str, Any], modality: str, device: str, task: str) -> pd.DataFrame:
    split = add_clean_demographics(cv_subjects(config), config)
    label_col = config.get("run", {}).get("label_column", "primary_label_nonhealthy")
    signal_cols = ["L_id", *[col for col in signal.columns if col.startswith("signal_")]]
    qc_cols = ["L_id", *[col for col in qc.columns if col.startswith("qc_")]]
    merged = split.merge(signal[signal_cols], on="L_id", how="inner").merge(qc[qc_cols], on="L_id", how="inner")
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


def _numeric_prefixed(frame: pd.DataFrame, prefix: str) -> list[str]:
    cols = []
    for col in frame.columns:
        if col.startswith(prefix) and pd.api.types.is_numeric_dtype(frame[col]):
            cols.append(col)
    return cols


def _numeric_any_prefix(frame: pd.DataFrame, prefixes: list[str]) -> list[str]:
    return [
        col
        for col in frame.columns
        if any(col.startswith(prefix) for prefix in prefixes) and pd.api.types.is_numeric_dtype(frame[col])
    ]


def _demo_numeric(config: dict[str, Any]) -> list[str]:
    return list(config["demographics"].get("numeric_columns", []))


def _demo_categorical(config: dict[str, Any]) -> list[str]:
    return list(config["demographics"].get("categorical_columns", []))


def _predict_proba(model: Any, x: pd.DataFrame) -> np.ndarray:
    proba = model.predict_proba(x)
    return np.asarray(proba, dtype=float)[:, 1]


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
    return pooled[pooled["cohort_name"] == "core3_same_cohort"].copy() if not pooled.empty else pooled


def _shortcut_summary(pooled: pd.DataFrame) -> pd.DataFrame:
    if pooled.empty:
        return pooled
    mask = (pooled["modality"] == "shortcut") | pooled["feature_set"].isin(["qc", "metadata", "background"])
    return pooled[mask].copy()


def _exclusion_summary(config: dict[str, Any]) -> pd.DataFrame:
    rows = []
    paths: list[tuple[str, Path]] = []
    for spec in config.get("eeg", {}).get("tasks", {}).values():
        paths.append(("eeg", project_path(spec["qc_features"])))
    fnirs_dir = config.get("fnirs", {}).get("outputs", {}).get("dir", "artifacts/goal2_6/fnirs")
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
    for extra_path in ["configs/goal2_6/bootstrap.yaml", "configs/goal2_6/eeg.yaml", "configs/goal2_6/fnirs.yaml", "configs/goal2_6/face.yaml"]:
        extra = load_goal_config(extra_path)
        for key in ["bootstrap", "eeg", "fnirs", "face"]:
            if key in extra:
                base[key] = extra[key]
    return base
