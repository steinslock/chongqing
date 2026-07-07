"""Fixed-split baseline training and evaluation utilities."""

from __future__ import annotations

import copy
import hashlib
import json
import math
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import joblib
import numpy as np
import pandas as pd
import yaml
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .config import PROJECT_ROOT, ProjectConfig, ReadOnlyInputGuard, load_config
from .leakage import validate_feature_columns
from .splits import sha256_file

try:
    from lightgbm import LGBMClassifier
except Exception:  # noqa: BLE001
    LGBMClassifier = None


METRIC_NAMES = [
    "auroc",
    "auprc",
    "balanced_accuracy",
    "macro_f1",
    "sensitivity",
    "specificity",
    "ppv",
    "npv",
    "brier_score",
    "ece",
    "mce",
]


@dataclass(frozen=True)
class BaselineDataset:
    name: str
    feature_family: str
    description: str
    frame: pd.DataFrame
    feature_columns: list[str]
    numeric_columns: list[str]
    categorical_columns: list[str]
    feature_count_reported: int


def load_baseline_settings(path: str | Path) -> dict[str, Any]:
    """Load a baseline YAML file with optional same-directory inheritance."""

    config_path = resolve_project_path(path)
    data = _read_yaml(config_path)
    parent = data.pop("extends", None)
    if parent:
        parent_path = Path(parent)
        if not parent_path.is_absolute():
            parent_path = config_path.parent / parent_path
        base = load_baseline_settings(parent_path)
        data = _deep_merge(base, data)
    data["_config_path"] = str(config_path)
    return data


def run_baseline_experiment(config_path: str | Path) -> dict[str, Any]:
    """Run all configured baselines on `subject_splits_v1` without tuning on test."""

    settings = load_baseline_settings(config_path)
    project_config = load_config(settings.get("project_config", "configs/default.yaml"))
    guard = ReadOnlyInputGuard(project_config.readonly_inputs)

    seed = int(settings.get("run", {}).get("seed", project_config.seed))
    threshold = float(settings.get("run", {}).get("threshold", 0.5))
    n_bootstrap = int(settings.get("run", {}).get("n_bootstrap", 1000))
    calibration_bins = int(settings.get("run", {}).get("calibration_bins", 10))
    smoke_limit = settings.get("run", {}).get("smoke_limit_per_dataset")
    smoke_limit = int(smoke_limit) if smoke_limit is not None else None
    save_checkpoints = bool(settings.get("run", {}).get("save_checkpoints", True))

    split_path = resolve_project_path(settings["paths"]["split_file"])
    split_df = load_split_frame(split_path, project_config.label_column)

    outputs = settings["outputs"]
    results_path = checked_output_path(outputs["results_csv"], guard)
    predictions_path = checked_output_path(outputs["predictions_csv"], guard)
    fold_metrics_path = checked_output_path(outputs["fold_metrics_csv"], guard)
    availability_path = checked_output_path(outputs["feature_availability_json"], guard)
    run_manifest_path = checked_output_path(outputs["run_manifest_json"], guard)
    report_path = checked_output_path(outputs["report_md"], guard)
    checkpoints_dir = checked_output_path(Path(outputs["checkpoints_dir"]) / ".placeholder", guard).parent

    datasets, availability = build_datasets(split_df, settings, project_config, smoke_limit=smoke_limit)
    all_results: list[dict[str, Any]] = []
    all_predictions: list[pd.DataFrame] = []
    all_fold_metrics: list[dict[str, Any]] = []
    checkpoint_rows: list[dict[str, str]] = []

    for dataset in datasets:
        model_keys = model_keys_for_dataset(dataset, settings)
        for model_key in model_keys:
            model_name = f"{dataset.name}_{model_key}"
            fitted = evaluate_model_on_fixed_split(
                dataset=dataset,
                model_key=model_key,
                model_name=model_name,
                label_column=project_config.label_column,
                seed=seed,
                threshold=threshold,
                n_bootstrap=n_bootstrap,
                calibration_bins=calibration_bins,
                checkpoint_dir=checkpoints_dir,
                save_checkpoint=save_checkpoints,
            )
            all_results.extend(fitted["results"])
            all_predictions.append(fitted["predictions"])
            all_fold_metrics.extend(fitted["fold_metrics"])
            if fitted["checkpoint"]:
                checkpoint_rows.append(fitted["checkpoint"])

    results_df = pd.DataFrame(all_results)
    predictions_df = pd.concat(all_predictions, ignore_index=True) if all_predictions else pd.DataFrame()
    fold_metrics_df = pd.DataFrame(all_fold_metrics)

    results_path.parent.mkdir(parents=True, exist_ok=True)
    predictions_path.parent.mkdir(parents=True, exist_ok=True)
    fold_metrics_path.parent.mkdir(parents=True, exist_ok=True)
    availability_path.parent.mkdir(parents=True, exist_ok=True)
    run_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    results_df.to_csv(results_path, index=False)
    predictions_df.to_csv(predictions_path, index=False)
    fold_metrics_df.to_csv(fold_metrics_path, index=False)
    availability_path.write_text(json.dumps(availability, indent=2, ensure_ascii=False), encoding="utf-8")

    manifest = {
        "config": str(resolve_project_path(config_path)),
        "project_config": str(project_config.path),
        "split_file": str(split_path),
        "split_sha256": sha256_file(split_path),
        "seed": seed,
        "threshold": threshold,
        "n_bootstrap": n_bootstrap,
        "calibration_bins": calibration_bins,
        "smoke_limit_per_dataset": smoke_limit,
        "results_csv": str(results_path),
        "predictions_csv": str(predictions_path),
        "fold_metrics_csv": str(fold_metrics_path),
        "feature_availability_json": str(availability_path),
        "report_md": str(report_path),
        "checkpoints_dir": str(checkpoints_dir),
        "checkpoints": checkpoint_rows,
    }
    run_manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    write_baseline_report(
        path=report_path,
        results=results_df,
        availability=availability,
        manifest=manifest,
        project_config=project_config,
    )

    return manifest


def load_split_frame(path: Path, label_column: str) -> pd.DataFrame:
    split_df = pd.read_csv(path, dtype={"A_id": str, "L_id": str, "cv_fold": str})
    required = {"A_id", "L_id", "is_locked_test", "cv_fold", label_column}
    missing = required.difference(split_df.columns)
    if missing:
        raise ValueError(f"Split file missing required columns: {sorted(missing)}")
    if split_df["A_id"].duplicated().any() or split_df["L_id"].duplicated().any():
        raise ValueError("Split file must be one row per subject by A_id and L_id.")
    split_df = split_df.copy()
    split_df[label_column] = pd.to_numeric(split_df[label_column], errors="raise").astype(int)
    split_df["is_locked_test"] = pd.to_numeric(split_df["is_locked_test"], errors="raise").astype(int)
    return split_df.sort_values("L_id").reset_index(drop=True)


def build_datasets(
    split_df: pd.DataFrame,
    settings: dict[str, Any],
    project_config: ProjectConfig,
    smoke_limit: int | None = None,
) -> tuple[list[BaselineDataset], list[dict[str, Any]]]:
    datasets: list[BaselineDataset] = []
    availability: list[dict[str, Any]] = []

    no_info_frame = split_df.copy()
    if smoke_limit is not None:
        no_info_frame = balanced_smoke_subset(no_info_frame, project_config.label_column, smoke_limit)
    no_info_frame["constant_zero"] = 0.0
    datasets.append(
        BaselineDataset(
            name="no_information",
            feature_family="none",
            description="No subject-level predictors; only training label distribution is used.",
            frame=no_info_frame,
            feature_columns=["constant_zero"],
            numeric_columns=["constant_zero"],
            categorical_columns=[],
            feature_count_reported=0,
        )
    )
    availability.append(
        {
            "dataset": "no_information",
            "enabled": True,
            "status": "available",
            "subjects": int(len(no_info_frame)),
            "feature_count": 0,
            "description": "No feature table required.",
        }
    )

    dataset_specs = settings.get("datasets", {})
    demo_spec = dataset_specs.get("demographics", {})
    if demo_spec.get("enabled", True):
        demo = build_demographics_dataset(split_df, demo_spec, project_config, smoke_limit=smoke_limit)
        datasets.append(demo)
        availability.append(
            {
                "dataset": demo.name,
                "enabled": True,
                "status": "available",
                "subjects": int(len(demo.frame)),
                "feature_count": demo.feature_count_reported,
                "description": demo.description,
                "numeric_columns": demo.numeric_columns,
                "categorical_columns": demo.categorical_columns,
            }
        )

    for name, spec in dataset_specs.items():
        if name in {"demographics"}:
            continue
        if not spec.get("enabled", False):
            availability.append(
                {
                    "dataset": name,
                    "enabled": False,
                    "status": "skipped",
                    "subjects": 0,
                    "feature_count": 0,
                    "description": spec.get("description", ""),
                    "reason": spec.get("skip_reason", "Dataset disabled in config."),
                }
            )
            continue
        dataset, row = build_tabular_numeric_dataset(name, split_df, spec, project_config, smoke_limit=smoke_limit)
        if dataset is not None:
            datasets.append(dataset)
        availability.append(row)

    return datasets, availability


def build_demographics_dataset(
    split_df: pd.DataFrame,
    spec: dict[str, Any],
    project_config: ProjectConfig,
    smoke_limit: int | None = None,
) -> BaselineDataset:
    frame = split_df.copy()
    age_min = float(spec.get("age_min", 9))
    age_max = float(spec.get("age_max", 20))
    age = pd.to_numeric(frame.get("age"), errors="coerce")
    frame["age_clean"] = age.where(age.between(age_min, age_max))
    frame["sex_clean"] = clean_category(frame.get("sex"))
    frame["grade_clean"] = clean_category(frame.get("grade"))
    frame["grade_group_clean"] = clean_category(frame.get("grade_group"))

    numeric_columns = [col for col in spec.get("numeric_columns", []) if col in frame.columns]
    categorical_columns = [col for col in spec.get("categorical_columns", []) if col in frame.columns]
    optional_columns = [col for col in spec.get("optional_columns", []) if col in frame.columns]
    for column in optional_columns:
        values = pd.to_numeric(frame[column], errors="coerce")
        if values.notna().any():
            clean_column = f"{column}_clean"
            frame[clean_column] = values
            numeric_columns.append(clean_column)

    feature_columns = numeric_columns + categorical_columns
    validate_feature_columns(
        feature_columns,
        exact=project_config.forbidden_feature_exact,
        patterns=project_config.forbidden_feature_patterns,
    )
    if not feature_columns:
        raise ValueError("No demographics feature columns available.")
    if smoke_limit is not None:
        frame = balanced_smoke_subset(frame, project_config.label_column, smoke_limit)
    return BaselineDataset(
        name="demographics",
        feature_family="demographics",
        description=spec.get("description", "Cleaned demographics."),
        frame=frame.sort_values("L_id").reset_index(drop=True),
        feature_columns=feature_columns,
        numeric_columns=numeric_columns,
        categorical_columns=categorical_columns,
        feature_count_reported=len(feature_columns),
    )


def build_tabular_numeric_dataset(
    name: str,
    split_df: pd.DataFrame,
    spec: dict[str, Any],
    project_config: ProjectConfig,
    smoke_limit: int | None = None,
) -> tuple[BaselineDataset | None, dict[str, Any]]:
    raw_path = spec.get("path")
    if not raw_path:
        return None, {
            "dataset": name,
            "enabled": True,
            "status": "skipped",
            "subjects": 0,
            "feature_count": 0,
            "description": spec.get("description", ""),
            "reason": spec.get("skip_reason", "No feature path configured."),
        }
    path = resolve_project_path(raw_path)
    if not path.exists():
        return None, {
            "dataset": name,
            "enabled": True,
            "status": "skipped",
            "subjects": 0,
            "feature_count": 0,
            "description": spec.get("description", ""),
            "path": str(path),
            "reason": "Feature path does not exist.",
        }

    id_column = spec.get("id_column", "L_id")
    features = pd.read_csv(path, dtype={id_column: str})
    if id_column not in features.columns:
        raise ValueError(f"{name} feature table is missing id column {id_column!r}.")
    if features[id_column].duplicated().any():
        dupes = features.loc[features[id_column].duplicated(), id_column].head(10).tolist()
        raise ValueError(f"{name} feature table has duplicate subject ids: {dupes}")
    if id_column != "L_id":
        features = features.rename(columns={id_column: "L_id"})

    feature_prefixes = tuple(spec.get("feature_prefixes", []))
    metadata = set(spec.get("metadata_columns", [])) | {"A_id", "L_id"}
    feature_columns = [
        column
        for column in features.columns
        if column not in metadata and any(column.startswith(prefix) for prefix in feature_prefixes)
    ]
    validate_feature_columns(
        feature_columns,
        exact=project_config.forbidden_feature_exact,
        patterns=project_config.forbidden_feature_patterns,
    )
    if not feature_columns:
        raise ValueError(f"No configured feature columns found for {name}.")

    keep_columns = ["L_id", *feature_columns]
    merged = split_df.merge(features[keep_columns], on="L_id", how="inner")
    for column in feature_columns:
        merged[column] = pd.to_numeric(merged[column], errors="coerce")
    if smoke_limit is not None:
        merged = balanced_smoke_subset(merged, project_config.label_column, smoke_limit)

    return BaselineDataset(
        name=name,
        feature_family="tabular_numeric",
        description=spec.get("description", f"{name} tabular numeric features."),
        frame=merged.sort_values("L_id").reset_index(drop=True),
        feature_columns=feature_columns,
        numeric_columns=feature_columns,
        categorical_columns=[],
        feature_count_reported=len(feature_columns),
    ), {
        "dataset": name,
        "enabled": True,
        "status": "available",
        "subjects": int(len(merged)),
        "feature_count": len(feature_columns),
        "description": spec.get("description", ""),
        "path": str(path),
        "source_rows": int(len(features)),
    }


def model_keys_for_dataset(dataset: BaselineDataset, settings: dict[str, Any]) -> list[str]:
    models = settings.get("models", {})
    if dataset.name == "no_information":
        return list(models.get("no_information", ["majority", "stratified_random"]))
    if dataset.feature_family == "demographics":
        return list(models.get("demographics", ["logistic_regression", "hist_gradient_boosting"]))
    return list(models.get("tabular_numeric", ["logistic_regression", "random_forest", "hist_gradient_boosting"]))


def evaluate_model_on_fixed_split(
    dataset: BaselineDataset,
    model_key: str,
    model_name: str,
    label_column: str,
    seed: int,
    threshold: float,
    n_bootstrap: int,
    calibration_bins: int,
    checkpoint_dir: Path,
    save_checkpoint: bool,
) -> dict[str, Any]:
    frame = dataset.frame.sort_values("L_id").reset_index(drop=True)
    cv_frame = frame[frame["is_locked_test"] == 0].copy()
    test_frame = frame[frame["is_locked_test"] == 1].copy()
    if cv_frame.empty or test_frame.empty:
        raise ValueError(f"{dataset.name} must contain both CV and locked-test subjects.")

    predictions: list[pd.DataFrame] = []
    fold_metrics: list[dict[str, Any]] = []
    for fold in sorted(cv_frame["cv_fold"].dropna().unique(), key=lambda value: int(float(value))):
        val_mask = cv_frame["cv_fold"].astype(str) == str(fold)
        train_frame = cv_frame[~val_mask].copy()
        val_frame = cv_frame[val_mask].copy()
        assert_disjoint_subjects(train_frame, val_frame, context=f"{model_name} fold {fold}")

        model = build_model(dataset, model_key, seed + int(float(fold)) + 1)
        x_train, y_train = xy(train_frame, dataset.feature_columns, label_column)
        x_val, y_val = xy(val_frame, dataset.feature_columns, label_column)
        model.fit(x_train, y_train)
        score = predict_positive_probability(model, x_val)
        pred = prediction_frame(dataset.name, model_name, "cv_oof", fold, val_frame, y_val, score, threshold)
        predictions.append(pred)
        fold_metric = metrics_with_context(
            y_val,
            score,
            threshold=threshold,
            calibration_bins=calibration_bins,
            context={
                "dataset": dataset.name,
                "feature_family": dataset.feature_family,
                "model": model_name,
                "evaluation_stage": "cv_fold",
                "fold": str(fold),
                "n_subjects": len(val_frame),
                "n_train_subjects": len(train_frame),
                "feature_count": dataset.feature_count_reported,
            },
        )
        fold_metrics.append(fold_metric)

    cv_predictions = pd.concat(predictions, ignore_index=True)
    cv_summary = summarize_predictions(
        dataset=dataset,
        model_name=model_name,
        evaluation_stage="cv_oof",
        y_true=cv_predictions["y_true"].to_numpy(dtype=int),
        y_score=cv_predictions["y_score"].to_numpy(dtype=float),
        threshold=threshold,
        n_train_subjects=np.nan,
        n_bootstrap=n_bootstrap,
        calibration_bins=calibration_bins,
        seed=stable_seed(seed, dataset.name, model_name, "cv_oof"),
    )

    final_model = build_model(dataset, model_key, seed + 9001)
    assert_disjoint_subjects(cv_frame, test_frame, context=f"{model_name} locked_test")
    x_train, y_train = xy(cv_frame, dataset.feature_columns, label_column)
    x_test, y_test = xy(test_frame, dataset.feature_columns, label_column)
    final_model.fit(x_train, y_train)
    test_score = predict_positive_probability(final_model, x_test)
    test_predictions = prediction_frame(dataset.name, model_name, "locked_test", "", test_frame, y_test, test_score, threshold)
    test_summary = summarize_predictions(
        dataset=dataset,
        model_name=model_name,
        evaluation_stage="locked_test",
        y_true=y_test,
        y_score=test_score,
        threshold=threshold,
        n_train_subjects=len(cv_frame),
        n_bootstrap=n_bootstrap,
        calibration_bins=calibration_bins,
        seed=stable_seed(seed, dataset.name, model_name, "locked_test"),
    )
    predictions.append(test_predictions)

    checkpoint_row: dict[str, str] | None = None
    if save_checkpoint:
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        checkpoint_path = checkpoint_dir / f"{dataset.name}__{model_name}.joblib"
        checkpoint_payload = {
            "model": final_model,
            "dataset": dataset.name,
            "model_name": model_name,
            "model_key": model_key,
            "feature_columns": dataset.feature_columns,
            "numeric_columns": dataset.numeric_columns,
            "categorical_columns": dataset.categorical_columns,
            "threshold": threshold,
            "trained_on": "cv_pool_only",
        }
        joblib.dump(checkpoint_payload, checkpoint_path)
        checkpoint_row = {
            "dataset": dataset.name,
            "model": model_name,
            "path": str(checkpoint_path),
            "sha256": sha256_file(checkpoint_path),
        }

    return {
        "results": [cv_summary, test_summary],
        "predictions": pd.concat(predictions, ignore_index=True),
        "fold_metrics": fold_metrics,
        "checkpoint": checkpoint_row,
    }


def build_model(dataset: BaselineDataset, model_key: str, seed: int) -> Any:
    if model_key == "majority":
        return DummyClassifier(strategy="prior")
    if model_key == "stratified_random":
        return DummyClassifier(strategy="stratified", random_state=seed)
    if dataset.feature_family == "demographics":
        return build_demographics_model(dataset, model_key, seed)
    if dataset.feature_family == "tabular_numeric":
        return build_numeric_model(model_key, seed)
    raise ValueError(f"Unsupported model {model_key!r} for dataset {dataset.name!r}.")


def build_demographics_model(dataset: BaselineDataset, model_key: str, seed: int) -> Pipeline:
    dense = model_key in {"hist_gradient_boosting", "lightgbm"}
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "num",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="median", keep_empty_features=True)),
                        ("scaler", StandardScaler()),
                    ]
                ),
                dataset.numeric_columns,
            ),
            (
                "cat",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=not dense)),
                    ]
                ),
                dataset.categorical_columns,
            ),
        ],
        sparse_threshold=0.0 if dense else 0.3,
    )
    if model_key == "logistic_regression":
        classifier = LogisticRegression(class_weight="balanced", max_iter=2000, random_state=seed)
    elif model_key == "hist_gradient_boosting":
        classifier = HistGradientBoostingClassifier(
            max_iter=80,
            learning_rate=0.05,
            l2_regularization=0.01,
            class_weight="balanced",
            random_state=seed,
        )
    elif model_key == "lightgbm":
        if LGBMClassifier is None:
            raise RuntimeError("LightGBM is configured but not installed.")
        classifier = LGBMClassifier(
            objective="binary",
            n_estimators=250,
            learning_rate=0.03,
            num_leaves=31,
            subsample=0.8,
            colsample_bytree=0.8,
            class_weight="balanced",
            random_state=seed,
            verbosity=-1,
            n_jobs=-1,
        )
    else:
        raise ValueError(f"Unsupported demographics model: {model_key}")
    return Pipeline([("preprocess", preprocessor), ("model", classifier)])


def build_numeric_model(model_key: str, seed: int) -> Pipeline:
    if model_key == "logistic_regression":
        return Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median", keep_empty_features=True)),
                ("scaler", StandardScaler()),
                (
                    "model",
                    LogisticRegression(
                        class_weight="balanced",
                        max_iter=3000,
                        random_state=seed,
                    ),
                ),
            ]
        )
    if model_key == "random_forest":
        return Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median", keep_empty_features=True)),
                (
                    "model",
                    RandomForestClassifier(
                        n_estimators=300,
                        min_samples_leaf=5,
                        class_weight="balanced_subsample",
                        n_jobs=-1,
                        random_state=seed,
                    ),
                ),
            ]
        )
    if model_key == "hist_gradient_boosting":
        return Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median", keep_empty_features=True)),
                (
                    "model",
                    HistGradientBoostingClassifier(
                        max_iter=80,
                        learning_rate=0.05,
                        l2_regularization=0.01,
                        class_weight="balanced",
                        random_state=seed,
                    ),
                ),
            ]
        )
    if model_key == "lightgbm":
        if LGBMClassifier is None:
            raise RuntimeError("LightGBM is configured but not installed.")
        return Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median", keep_empty_features=True)),
                (
                    "model",
                    LGBMClassifier(
                        objective="binary",
                        n_estimators=300,
                        learning_rate=0.03,
                        num_leaves=31,
                        subsample=0.8,
                        colsample_bytree=0.8,
                        class_weight="balanced",
                        random_state=seed,
                        verbosity=-1,
                        n_jobs=-1,
                    ),
                ),
            ]
        )
    raise ValueError(f"Unsupported numeric model: {model_key}")


def xy(frame: pd.DataFrame, feature_columns: list[str], label_column: str) -> tuple[pd.DataFrame, np.ndarray]:
    return frame.loc[:, feature_columns], frame[label_column].to_numpy(dtype=int)


def predict_positive_probability(model: Any, x: pd.DataFrame) -> np.ndarray:
    if hasattr(model, "predict_proba"):
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="X does not have valid feature names.*")
            probability = model.predict_proba(x)
        return np.asarray(probability, dtype=float)[:, 1]
    decision = np.asarray(model.decision_function(x), dtype=float)
    return 1.0 / (1.0 + np.exp(-decision))


def prediction_frame(
    dataset_name: str,
    model_name: str,
    stage: str,
    fold: str | int,
    frame: pd.DataFrame,
    y_true: np.ndarray,
    y_score: np.ndarray,
    threshold: float,
) -> pd.DataFrame:
    output = pd.DataFrame(
        {
            "dataset": dataset_name,
            "model": model_name,
            "evaluation_stage": stage,
            "fold": str(fold),
            "A_id": frame["A_id"].to_numpy(),
            "L_id": frame["L_id"].to_numpy(),
            "y_true": y_true.astype(int),
            "y_score": y_score.astype(float),
        }
    )
    output["threshold"] = threshold
    output["y_pred"] = (output["y_score"] >= threshold).astype(int)
    return output


def summarize_predictions(
    dataset: BaselineDataset,
    model_name: str,
    evaluation_stage: str,
    y_true: np.ndarray,
    y_score: np.ndarray,
    threshold: float,
    n_train_subjects: float | int,
    n_bootstrap: int,
    calibration_bins: int,
    seed: int,
) -> dict[str, Any]:
    context = {
        "dataset": dataset.name,
        "feature_family": dataset.feature_family,
        "model": model_name,
        "evaluation_stage": evaluation_stage,
        "fold": "",
        "n_subjects": int(len(y_true)),
        "n_train_subjects": n_train_subjects,
        "n_positive": int(np.sum(y_true)),
        "n_negative": int(len(y_true) - np.sum(y_true)),
        "positive_rate": float(np.mean(y_true)),
        "feature_count": dataset.feature_count_reported,
        "threshold": threshold,
    }
    point = compute_metrics(y_true, y_score, threshold=threshold, calibration_bins=calibration_bins)
    row = {**context, **point}
    ci = bootstrap_confidence_intervals(
        y_true,
        y_score,
        threshold=threshold,
        n_bootstrap=n_bootstrap,
        calibration_bins=calibration_bins,
        seed=seed,
    )
    for metric in METRIC_NAMES:
        low, high = ci.get(metric, (math.nan, math.nan))
        row[f"{metric}_ci_low"] = low
        row[f"{metric}_ci_high"] = high
    row["n_bootstrap"] = n_bootstrap
    return row


def metrics_with_context(
    y_true: np.ndarray,
    y_score: np.ndarray,
    threshold: float,
    calibration_bins: int,
    context: dict[str, Any],
) -> dict[str, Any]:
    point = compute_metrics(y_true, y_score, threshold=threshold, calibration_bins=calibration_bins)
    return {**context, "threshold": threshold, **point}


def compute_metrics(
    y_true: Iterable[int] | np.ndarray,
    y_score: Iterable[float] | np.ndarray,
    threshold: float = 0.5,
    calibration_bins: int = 10,
) -> dict[str, float]:
    truth = np.asarray(list(y_true), dtype=int)
    score = np.asarray(list(y_score), dtype=float)
    pred = (score >= threshold).astype(int)
    tp = int(np.sum((truth == 1) & (pred == 1)))
    tn = int(np.sum((truth == 0) & (pred == 0)))
    fp = int(np.sum((truth == 0) & (pred == 1)))
    fn = int(np.sum((truth == 1) & (pred == 0)))

    sensitivity = safe_div(tp, tp + fn)
    specificity = safe_div(tn, tn + fp)
    ppv = safe_div(tp, tp + fp)
    npv = safe_div(tn, tn + fn)
    f1_pos = safe_div(2 * tp, 2 * tp + fp + fn)
    f1_neg = safe_div(2 * tn, 2 * tn + fp + fn)
    auroc = safe_metric(lambda: roc_auc_score(truth, score))
    auprc = safe_metric(lambda: average_precision_score(truth, score))
    brier = float(np.mean((score - truth) ** 2))
    ece, mce = calibration_errors(truth, score, n_bins=calibration_bins)
    return {
        "auroc": auroc,
        "auprc": auprc,
        "balanced_accuracy": float((sensitivity + specificity) / 2.0),
        "macro_f1": float((f1_pos + f1_neg) / 2.0),
        "sensitivity": sensitivity,
        "specificity": specificity,
        "ppv": ppv,
        "npv": npv,
        "brier_score": brier,
        "ece": ece,
        "mce": mce,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "tp": tp,
    }


def bootstrap_confidence_intervals(
    y_true: np.ndarray,
    y_score: np.ndarray,
    threshold: float,
    n_bootstrap: int,
    calibration_bins: int,
    seed: int,
) -> dict[str, tuple[float, float]]:
    rng = np.random.default_rng(seed)
    y_true = np.asarray(y_true, dtype=int)
    y_score = np.asarray(y_score, dtype=float)
    metric_values = {metric: [] for metric in METRIC_NAMES}
    n = len(y_true)
    if n_bootstrap <= 0:
        return {metric: (math.nan, math.nan) for metric in METRIC_NAMES}
    for _ in range(n_bootstrap):
        index = rng.integers(0, n, size=n)
        metrics = compute_metrics(y_true[index], y_score[index], threshold=threshold, calibration_bins=calibration_bins)
        for metric in METRIC_NAMES:
            value = metrics[metric]
            if not math.isnan(value):
                metric_values[metric].append(value)
    intervals: dict[str, tuple[float, float]] = {}
    for metric, values in metric_values.items():
        if not values:
            intervals[metric] = (math.nan, math.nan)
            continue
        low, high = np.percentile(np.asarray(values, dtype=float), [2.5, 97.5])
        intervals[metric] = (float(low), float(high))
    return intervals


def calibration_errors(y_true: np.ndarray, y_score: np.ndarray, n_bins: int) -> tuple[float, float]:
    y_true = np.asarray(y_true, dtype=int)
    y_score = np.asarray(y_score, dtype=float)
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    mce = 0.0
    for left, right in zip(bins[:-1], bins[1:], strict=False):
        if right == 1.0:
            mask = (y_score >= left) & (y_score <= right)
        else:
            mask = (y_score >= left) & (y_score < right)
        if not np.any(mask):
            continue
        gap = abs(float(np.mean(y_score[mask])) - float(np.mean(y_true[mask])))
        ece += (int(np.sum(mask)) / len(y_true)) * gap
        mce = max(mce, gap)
    return float(ece), float(mce)


def write_baseline_report(
    path: Path,
    results: pd.DataFrame,
    availability: list[dict[str, Any]],
    manifest: dict[str, Any],
    project_config: ProjectConfig,
) -> None:
    locked = results[results["evaluation_stage"] == "locked_test"].copy()
    cv = results[results["evaluation_stage"] == "cv_oof"].copy()
    metric_columns = ["auroc", "auprc", "balanced_accuracy", "macro_f1", "sensitivity", "specificity", "ppv", "npv", "brier_score", "ece"]
    summary_cols = ["dataset", "model", "n_subjects", "n_positive", "feature_count", *metric_columns]

    def format_table(df: pd.DataFrame, cols: list[str]) -> str:
        if df.empty:
            return "No rows available."
        table = df.loc[:, cols].copy()
        return table.to_markdown(index=False, floatfmt=".4f")

    best_locked = locked.sort_values(["auroc", "auprc"], ascending=False).head(1)
    if best_locked.empty:
        main_result = "No locked-test baseline results were generated."
    else:
        row = best_locked.iloc[0]
        main_result = (
            f"Best locked-test AUROC is `{row['auroc']:.4f}` from `{row['model']}` "
            f"on `{row['dataset']}`; this is a fixed-split baseline, not a tuned final model."
        )

    skipped = [row for row in availability if row.get("status") == "skipped"]
    available = [row for row in availability if row.get("status") == "available"]

    with path.open("w", encoding="utf-8") as handle:
        handle.write("# Chongqing Binary Diagnosis Baseline Report\n\n")
        handle.write("## Technical Summary\n\n")
        handle.write(f"- {main_result}\n")
        handle.write(
            "- Evaluation uses `subject_splits_v1`: five out-of-fold CV validation folds from the CV pool plus one locked-test evaluation trained only on the CV pool.\n"
        )
        handle.write(
            "- All thresholded metrics use the fixed threshold `0.5`; the locked test set is not used for feature selection, hyperparameter tuning, threshold tuning, or early stopping.\n"
        )
        handle.write(
            "- Demographics models use cleaned age, sex, grade, and grade group only. Diagnosis, CDRS, CES-DC, HAMA, SCARED, self-harm, suicide, and other clinical scale fields are blocked by the leakage guard.\n\n"
        )

        handle.write("## Locked-Test Results Are Baseline-Level Only\n\n")
        handle.write(
            "The table below is the final-evaluation view for the fixed locked test split. Full confidence intervals and every requested metric are in `results/baseline_results.csv`.\n\n"
        )
        handle.write(format_table(locked.sort_values(["dataset", "model"]), summary_cols))
        handle.write("\n\n")

        handle.write("## CV Out-of-Fold Results Track Internal Stability\n\n")
        handle.write(
            "CV rows are generated by fitting preprocessing and models inside each training fold, then predicting only that fold's held-out validation subjects.\n\n"
        )
        handle.write(format_table(cv.sort_values(["dataset", "model"]), summary_cols))
        handle.write("\n\n")

        handle.write("## Scope, Data, And Metric Definitions\n\n")
        handle.write(f"- Primary label: `{project_config.label_column}` with `1` as non-healthy and `0` as healthy.\n")
        handle.write(f"- Split file: `{manifest['split_file']}`; SHA256 `{manifest['split_sha256']}`.\n")
        handle.write("- Reported unit: subject-level prediction, one row per subject per model and evaluation stage.\n")
        handle.write(
            "- Metrics: AUROC, AUPRC, Balanced Accuracy, Macro-F1, Sensitivity, Specificity, PPV, NPV, Brier Score, 10-bin Expected Calibration Error, and 10-bin Maximum Calibration Error.\n"
        )
        handle.write("- PPV, NPV, F1, sensitivity, and specificity use `zero_division=0` when a denominator is empty.\n")
        handle.write(f"- Uncertainty: `{manifest['n_bootstrap']}` bootstrap resamples over subject-level predictions for each model and evaluation stage.\n\n")

        handle.write("## Available Feature Families\n\n")
        for row in available:
            handle.write(
                f"- `{row['dataset']}`: available, subjects `{row['subjects']}`, features `{row['feature_count']}`. {row.get('description', '')}\n"
            )
        for row in skipped:
            handle.write(
                f"- `{row['dataset']}`: skipped. {row.get('reason', 'No reliable feature table available.')}\n"
            )
        handle.write("\n")

        handle.write("## Methodology And Leakage Controls\n\n")
        handle.write(
            "- Majority and stratified-random baselines use no subject predictors; a dummy zero column is passed only to satisfy the estimator API and is counted as zero features.\n"
        )
        handle.write(
            "- Demographics-only Logistic Regression and the configured boosting classifier use pipeline-fitted imputers/encoders inside each fold or final CV-pool fit.\n"
        )
        handle.write(
            "- EEG Rest Logistic Regression, Random Forest, and the configured boosting classifier use the existing v1 Rest EEG feature table with configured non-clinical prefixes only.\n"
        )
        handle.write(
            "- The fNIRS and Face interfaces are represented in config, but no fNIRS/Face results are reported because no reliable subject-level traditional feature table is currently configured.\n\n"
        )
        handle.write("- This run used CPU estimators only. LightGBM was run with its default CPU backend; no CUDA or GPU training was enabled.\n\n")

        handle.write("## Limitations, Robustness, And Next Steps\n\n")
        handle.write(
            "- These are conservative baseline runs with fixed hyperparameters; they establish reproducible references rather than optimized clinical models.\n"
        )
        handle.write(
            "- EEG results cover only the existing Rest traditional feature table. Oddball/1BACK or future fNIRS/Face feature tables should be added through `configs/baselines/default.yaml` and rerun under the same split protocol.\n"
        )
        handle.write(
            "- Before any deep or multimodal model comparison, keep the locked test untouched and compare candidate development using CV-pool evidence first.\n\n"
        )

        handle.write("## Reproducibility Artifacts\n\n")
        handle.write(f"- Results: `{manifest['results_csv']}`\n")
        handle.write(f"- Predictions: `{manifest['predictions_csv']}`\n")
        handle.write(f"- Fold metrics: `{manifest['fold_metrics_csv']}`\n")
        handle.write(f"- Feature availability: `{manifest['feature_availability_json']}`\n")
        handle.write(f"- Checkpoints: `{manifest['checkpoints_dir']}`\n")


def balanced_smoke_subset(frame: pd.DataFrame, label_column: str, limit: int) -> pd.DataFrame:
    chunks = []
    per_class = max(1, limit // 2)
    for label in [0, 1]:
        group = frame[frame[label_column] == label].sort_values("L_id").head(per_class)
        chunks.append(group)
    subset = pd.concat(chunks, ignore_index=True).sort_values("L_id").reset_index(drop=True)
    return subset


def clean_category(values: pd.Series | None) -> pd.Series:
    if values is None:
        return pd.Series(dtype="object")
    cleaned = values.astype("string").str.strip()
    cleaned = cleaned.mask(cleaned.isin(["", "nan", "None", "#N/A", "NA"]))
    return cleaned


def assert_disjoint_subjects(train: pd.DataFrame, test: pd.DataFrame, context: str) -> None:
    train_a = set(train["A_id"].astype(str))
    train_l = set(train["L_id"].astype(str))
    test_a = set(test["A_id"].astype(str))
    test_l = set(test["L_id"].astype(str))
    if train_a.intersection(test_a) or train_l.intersection(test_l):
        raise ValueError(f"Subject leakage detected in {context}.")


def safe_div(num: float, den: float) -> float:
    return float(num / den) if den else 0.0


def safe_metric(fn: Any) -> float:
    try:
        value = fn()
    except Exception:
        return math.nan
    if value is None:
        return math.nan
    return float(value)


def stable_seed(seed: int, *parts: str) -> int:
    payload = "|".join([str(seed), *parts])
    digest = hashlib.sha1(payload.encode("utf-8")).hexdigest()
    return int(digest[:8], 16)


def resolve_project_path(path: str | Path) -> Path:
    value = Path(path)
    if not value.is_absolute():
        value = PROJECT_ROOT / value
    return value.resolve()


def checked_output_path(path: str | Path, guard: ReadOnlyInputGuard) -> Path:
    resolved = resolve_project_path(path)
    guard.assert_write_allowed(resolved)
    return resolved


def _read_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML must contain a mapping: {path}")
    return data


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged
