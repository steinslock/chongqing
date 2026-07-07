#!/usr/bin/env python3
"""Train EEG Rest subject-level baseline models for Chongqing v1."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

try:
    from lightgbm import LGBMClassifier
except Exception:  # noqa: BLE001
    LGBMClassifier = None


SEED = 20260703
V1_ROOT = Path("/home/qiangminc/codes/data4_qiangminc/code/chongqing/experiments/v1")
MANIFEST = Path(
    "/home/qiangminc/codes/data4_qiangminc/code/chongqing/"
    "inputs/derived_reports/chongqing_binary_diagnosis_report/data/subject_manifest.csv"
)
FEATURES = V1_ROOT / "eeg" / "artifacts" / "features" / "eeg_rest_features.csv"
RESULTS_DIR = V1_ROOT / "eeg" / "artifacts" / "results"
REPORT_DIR = V1_ROOT / "eeg" / "reports"

FORBIDDEN_PATTERNS = [
    "CDRS",
    "CES",
    "HAMA",
    "自杀",
    "诊断",
    "量表",
    "姓名",
    "name",
    "diag",
    "label",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--label", default="primary_label_nonhealthy")
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--features", type=Path, default=FEATURES)
    parser.add_argument("--out-dir", type=Path, default=RESULTS_DIR)
    parser.add_argument("--report-dir", type=Path, default=REPORT_DIR)
    parser.add_argument("--limit", type=int, default=None, help="Limit subjects after merge for smoke tests.")
    parser.add_argument("--n-splits", type=int, default=5)
    parser.add_argument("--seed", type=int, default=SEED)
    return parser.parse_args()


def load_dataset(args: argparse.Namespace) -> tuple[pd.DataFrame, list[str], list[str]]:
    if not args.manifest.exists():
        raise FileNotFoundError(args.manifest)
    if not args.features.exists():
        raise FileNotFoundError(args.features)
    manifest = pd.read_csv(args.manifest, dtype={"L_id": str, args.label: "string"})
    features = pd.read_csv(args.features, dtype={"L_id": str})
    if features["L_id"].duplicated().any():
        dupes = features.loc[features["L_id"].duplicated(), "L_id"].head(10).tolist()
        raise RuntimeError(f"Duplicate L_id in features: {dupes}")
    merged = manifest.merge(features, on="L_id", how="inner", suffixes=("_manifest", ""))
    merged = merged[merged[args.label].isin(["0", "1", 0, 1])].copy()
    merged[args.label] = merged[args.label].astype(int)
    if merged[args.label].nunique() < 2:
        raise RuntimeError("Need both classes after filtering.")
    if args.limit is not None:
        by_class = {
            cls: group.copy()
            for cls, group in merged.groupby(args.label, sort=True)
        }
        selected_indices = []
        while len(selected_indices) < args.limit:
            changed = False
            for cls in sorted(by_class):
                group = by_class[cls]
                if len(group) > 0:
                    selected_indices.append(group.index[0])
                    by_class[cls] = group.iloc[1:]
                    changed = True
                    if len(selected_indices) >= args.limit:
                        break
            if not changed:
                break
        merged = merged.loc[selected_indices].copy()
        if merged[args.label].nunique() < 2:
            raise RuntimeError("Limit sample contains fewer than two classes; increase --limit.")
    forbidden_cols = [
        col
        for col in merged.columns
        if any(pattern.lower() in col.lower() for pattern in FORBIDDEN_PATTERNS)
    ]
    feature_cols = [
        col
        for col in merged.columns
        if (
            col.startswith("bp_")
            or col.startswith("region_")
            or col.startswith("asym_")
            or col.startswith("spectral_entropy")
            or col.startswith("hjorth_")
            or col.startswith("qc_")
        )
    ]
    leakage_feature_cols = [col for col in feature_cols if col in forbidden_cols]
    if leakage_feature_cols:
        raise RuntimeError(f"Forbidden feature columns detected: {leakage_feature_cols}")
    demo_cols = [col for col in ["age", "sex", "grade"] if col in merged.columns]
    return merged, feature_cols, demo_cols


def make_models(seed: int) -> dict[str, object]:
    models: dict[str, object] = {
        "dummy_prior": DummyClassifier(strategy="prior"),
        "elasticnet_logreg": Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
                (
                    "model",
                    LogisticRegression(
                        penalty="elasticnet",
                        solver="saga",
                        l1_ratio=0.5,
                        C=1.0,
                        class_weight="balanced",
                        max_iter=5000,
                        random_state=seed,
                    ),
                ),
            ]
        ),
        "random_forest": Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
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
        ),
    }
    if LGBMClassifier is not None:
        models["lightgbm"] = Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
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
                    ),
                ),
            ]
        )
    return models


def make_demo_model(demo_cols: list[str], seed: int) -> Pipeline:
    categorical = [col for col in demo_cols if col in {"sex", "grade"}]
    numeric = [col for col in demo_cols if col == "age"]
    transformer = ColumnTransformer(
        [
            ("num", Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]), numeric),
            (
                "cat",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("onehot", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                categorical,
            ),
        ]
    )
    return Pipeline(
        [
            ("prep", transformer),
            (
                "model",
                LogisticRegression(
                    class_weight="balanced",
                    max_iter=2000,
                    random_state=seed,
                ),
            ),
        ]
    )


def choose_threshold(y_true: np.ndarray, y_score: np.ndarray) -> float:
    precision, recall, thresholds = precision_recall_curve(y_true, y_score)
    if len(thresholds) == 0:
        return 0.5
    f1 = 2 * precision[:-1] * recall[:-1] / np.maximum(precision[:-1] + recall[:-1], 1e-12)
    return float(thresholds[int(np.nanargmax(f1))])


def metric_row(model_name: str, fold: int | str, y_true: np.ndarray, y_score: np.ndarray, threshold: float) -> dict[str, object]:
    y_pred = (y_score >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    return {
        "model": model_name,
        "fold": fold,
        "n": int(len(y_true)),
        "threshold": threshold,
        "auroc": float(roc_auc_score(y_true, y_score)) if len(np.unique(y_true)) == 2 else np.nan,
        "auprc": float(average_precision_score(y_true, y_score)) if len(np.unique(y_true)) == 2 else np.nan,
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "sensitivity": float(tp / (tp + fn)) if (tp + fn) else np.nan,
        "specificity": float(tn / (tn + fp)) if (tn + fp) else np.nan,
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "brier": float(brier_score_loss(y_true, y_score)),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
    }


def predict_score(model: object, x_test: pd.DataFrame) -> np.ndarray:
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(x_test)
        return np.asarray(proba)[:, 1]
    decision = model.decision_function(x_test)
    return 1.0 / (1.0 + np.exp(-decision))


def run_cv(data: pd.DataFrame, feature_cols: list[str], label_col: str, args: argparse.Namespace) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    y = data[label_col].to_numpy(dtype=int)
    cv = StratifiedKFold(n_splits=args.n_splits, shuffle=True, random_state=args.seed)
    models = make_models(args.seed)
    metrics = []
    predictions = []
    splits = []
    for fold, (train_idx, test_idx) in enumerate(cv.split(data[feature_cols], y), start=1):
        train_ids = set(data.iloc[train_idx]["L_id"])
        test_ids = set(data.iloc[test_idx]["L_id"])
        if train_ids & test_ids:
            raise RuntimeError("Subject leakage detected between train and test.")
        x_train = data.iloc[train_idx][feature_cols]
        y_train = y[train_idx]
        x_test = data.iloc[test_idx][feature_cols]
        y_test = y[test_idx]
        for lid in data.iloc[train_idx]["L_id"]:
            splits.append({"fold": fold, "L_id": lid, "split": "train"})
        for lid in data.iloc[test_idx]["L_id"]:
            splits.append({"fold": fold, "L_id": lid, "split": "test"})
        for model_name, model in models.items():
            model.fit(x_train, y_train)
            train_score = predict_score(model, x_train)
            threshold = choose_threshold(y_train, train_score)
            test_score = predict_score(model, x_test)
            metrics.append(metric_row(model_name, fold, y_test, test_score, threshold))
            for lid, true_value, score in zip(data.iloc[test_idx]["L_id"], y_test, test_score, strict=False):
                predictions.append(
                    {
                        "model": model_name,
                        "fold": fold,
                        "L_id": lid,
                        "y_true": int(true_value),
                        "y_score": float(score),
                        "threshold": threshold,
                        "y_pred": int(score >= threshold),
                    }
                )
    pred_df = pd.DataFrame(predictions)
    for model_name, group in pred_df.groupby("model"):
        metrics.append(
            metric_row(
                model_name,
                "overall_oof",
                group["y_true"].to_numpy(dtype=int),
                group["y_score"].to_numpy(dtype=float),
                float(group["threshold"].median()),
            )
        )
    return pd.DataFrame(metrics), pred_df, pd.DataFrame(splits)


def run_demographics_cv(data: pd.DataFrame, demo_cols: list[str], label_col: str, args: argparse.Namespace) -> pd.DataFrame:
    if not demo_cols:
        return pd.DataFrame()
    y = data[label_col].to_numpy(dtype=int)
    cv = StratifiedKFold(n_splits=args.n_splits, shuffle=True, random_state=args.seed)
    rows = []
    all_true = []
    all_score = []
    thresholds = []
    for fold, (train_idx, test_idx) in enumerate(cv.split(data[demo_cols], y), start=1):
        model = make_demo_model(demo_cols, args.seed)
        x_train = data.iloc[train_idx][demo_cols]
        y_train = y[train_idx]
        x_test = data.iloc[test_idx][demo_cols]
        y_test = y[test_idx]
        model.fit(x_train, y_train)
        train_score = predict_score(model, x_train)
        threshold = choose_threshold(y_train, train_score)
        test_score = predict_score(model, x_test)
        rows.append(metric_row("demographics_only_logreg", fold, y_test, test_score, threshold))
        all_true.extend(y_test.tolist())
        all_score.extend(test_score.tolist())
        thresholds.append(threshold)
    rows.append(
        metric_row(
            "demographics_only_logreg",
            "overall_oof",
            np.asarray(all_true, dtype=int),
            np.asarray(all_score, dtype=float),
            float(np.median(thresholds)),
        )
    )
    return pd.DataFrame(rows)


def write_report(path: Path, data: pd.DataFrame, metrics: pd.DataFrame, demo_metrics: pd.DataFrame, args: argparse.Namespace) -> None:
    overall = metrics[metrics["fold"] == "overall_oof"].sort_values("auroc", ascending=False)
    label_counts = data[args.label].value_counts().sort_index().to_dict()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        f.write("# EEG Rest Baseline Report\n\n")
        f.write("## Run Summary\n\n")
        f.write(f"- Label: `{args.label}`\n")
        f.write(f"- Subjects used: {len(data)}\n")
        f.write(f"- Label counts: `{json.dumps(label_counts, ensure_ascii=False)}`\n")
        f.write(f"- CV: {args.n_splits}-fold stratified subject-level CV\n")
        f.write(f"- Seed: {args.seed}\n")
        f.write("- Feature family: EEG-only Rest bandpower, asymmetry, spectral entropy, Hjorth, and QC features.\n")
        f.write("- Forbidden clinical scale and diagnosis fields are excluded from features.\n\n")
        f.write("## Overall Out-of-Fold Metrics\n\n")
        if overall.empty:
            f.write("No metrics available.\n\n")
        else:
            f.write(overall.to_markdown(index=False, floatfmt=".4f"))
            f.write("\n\n")
        if not demo_metrics.empty:
            f.write("## Demographics-Only Sanity Baseline\n\n")
            f.write(demo_metrics[demo_metrics["fold"] == "overall_oof"].to_markdown(index=False, floatfmt=".4f"))
            f.write("\n\n")
        f.write("## QA Notes\n\n")
        f.write("- Predictions are out-of-fold; no subject appears in both train and test within a fold.\n")
        f.write("- Accuracy alone is not used as a success criterion; AUROC, AUPRC, balanced accuracy, sensitivity, specificity, F1, and Brier are reported.\n")
        f.write("- This report covers Rest EEG only; Oddball and 1BACK are reserved for later v1 expansion.\n")


def main() -> None:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    args.report_dir.mkdir(parents=True, exist_ok=True)
    data, feature_cols, demo_cols = load_dataset(args)
    min_class_count = int(data[args.label].value_counts().min())
    if min_class_count < 2:
        raise RuntimeError("Need at least two samples per class for cross-validation.")
    if args.n_splits > min_class_count:
        args.n_splits = min_class_count
    metrics, predictions, splits = run_cv(data, feature_cols, args.label, args)
    demo_metrics = run_demographics_cv(data, demo_cols, args.label, args)
    metrics_with_demo = pd.concat([metrics, demo_metrics], ignore_index=True)
    metrics_path = args.out_dir / "rest_primary_metrics.csv"
    predictions_path = args.out_dir / "rest_primary_predictions.csv"
    splits_path = args.out_dir / "rest_primary_cv_splits.csv"
    report_path = args.report_dir / "eeg_rest_baseline_report.md"
    metrics_with_demo.to_csv(metrics_path, index=False)
    predictions.to_csv(predictions_path, index=False)
    splits.to_csv(splits_path, index=False)
    write_report(report_path, data, metrics, demo_metrics, args)
    print(
        json.dumps(
            {
                "subjects": len(data),
                "features": len(feature_cols),
                "metrics": str(metrics_path),
                "predictions": str(predictions_path),
                "splits": str(splits_path),
                "report": str(report_path),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
