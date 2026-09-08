#!/usr/bin/env python3
"""Verify the demographics baseline, and what happens when features are added to it.

Every demographics number in the Goal 2.7 / 2.8 / 2.9 result tables is computed
*inside* a modality cohort, because that is the cohort each comparison needs. No
run ever measured demographics on the full development cohort, so the headline
figure had no reference point. This script supplies one, and answers the two
questions that follow from it.

1. Reference. Age, sex and grade on all `split_group == cv` subjects with a
   label, under both fixed CV protocols, all three model families, with the
   same three-fold inner CV over the same grids. Reported pooled, as a fold mean
   and per fold, plus the single-variable decomposition and the site proxy.
2. Dilution. Demographics plus K columns of pure random noise. If the observed
   "demographics + modality is worse than demographics" drops sit inside the
   range that noise produces, the modality features are behaving like noise and
   the drop is dilution rather than a defect.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "4")

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from chongqing_binary.goal2_7.config import load_goal_config  # noqa: E402

SEED = 20260907
MODELS = ("logistic_regression", "random_forest", "hist_gradient_boosting")


def _cohort(config: dict) -> pd.DataFrame:
    standard = pd.read_csv(PROJECT_ROOT / config["paths"]["split_file"],
                           dtype={"L_id": str, "A_id": str})
    group = pd.read_csv(PROJECT_ROOT / config["paths"]["group_split_file"], dtype={"L_id": str})
    frame = standard[standard["split_group"] == "cv"].copy()
    frame["robustness_fold"] = frame["L_id"].map(dict(zip(group["L_id"], group["robustness_fold"])))
    label = config.get("run", {}).get("label_column", "primary_label_nonhealthy")
    frame["y"] = pd.to_numeric(frame[label], errors="coerce")
    frame = frame[frame["y"].notna()].reset_index(drop=True)
    frame["y"] = frame["y"].astype(int)
    demo = config.get("demographics", {})
    low, high = float(demo.get("age_min", 9)), float(demo.get("age_max", 20))
    frame["age_clean"] = pd.to_numeric(frame["age"], errors="coerce").where(lambda s: s.between(low, high))
    for source, clean in (("sex", "sex_clean"), ("grade", "grade_clean")):
        frame[clean] = frame[source].astype(str).str.strip().replace(
            {"": np.nan, "nan": np.nan, "[missing]": np.nan})
    frame["site_proxy"] = frame["A_id"].astype(str).str[:3]
    return frame


def _estimator(model: str, params: dict):
    if model == "logistic_regression":
        # The grid carries its own solver; supply one only when it does not.
        params = {"solver": "liblinear", **params}
        return LogisticRegression(max_iter=2000, class_weight="balanced", **params)
    if model == "random_forest":
        return RandomForestClassifier(class_weight="balanced", n_jobs=4, random_state=SEED, **params)
    return HistGradientBoostingClassifier(random_state=SEED, **params)


def _pipeline(model: str, params: dict, numeric: list[str], categorical: list[str]) -> Pipeline:
    steps = []
    if numeric:
        steps.append(("n", Pipeline([("i", SimpleImputer(strategy="median")),
                                     ("s", StandardScaler())]), numeric))
    if categorical:
        steps.append(("c", Pipeline([("i", SimpleImputer(strategy="most_frequent")),
                                     ("o", OneHotEncoder(handle_unknown="ignore",
                                                         sparse_output=False))]), categorical))
    return Pipeline([("p", ColumnTransformer(steps)), ("m", _estimator(model, params))])


def _grids(config: dict) -> dict[str, list[dict]]:
    """The project grids, with the `model__` prefix stripped."""
    out: dict[str, list[dict]] = {}
    for model, grid in config["hyperparameters"].items():
        out[model] = [{k.replace("model__", ""): v for k, v in params.items() if v is not None}
                      or {} for params in grid]
    return out


def _outer_cv(frame: pd.DataFrame, fold_column: str, numeric: list[str],
              categorical: list[str], model: str, grid: list[dict],
              inner_folds: int) -> tuple[float, float, list[float]]:
    prediction = np.full(len(frame), np.nan)
    for fold in sorted(frame[fold_column].dropna().unique()):
        train, test = frame[fold_column] != fold, frame[fold_column] == fold
        x_train, y_train = frame.loc[train, numeric + categorical], frame.loc[train, "y"]
        best, best_score = grid[0], -np.inf
        inner = StratifiedKFold(inner_folds, shuffle=True, random_state=SEED)
        for params in grid:
            scores = []
            for i_train, i_test in inner.split(x_train, y_train):
                fitted = _pipeline(model, params, numeric, categorical).fit(
                    x_train.iloc[i_train], y_train.iloc[i_train])
                scores.append(roc_auc_score(y_train.iloc[i_test],
                                            fitted.predict_proba(x_train.iloc[i_test])[:, 1]))
            if float(np.mean(scores)) > best_score:
                best_score, best = float(np.mean(scores)), params
        fitted = _pipeline(model, best, numeric, categorical).fit(x_train, y_train)
        prediction[test.to_numpy()] = fitted.predict_proba(
            frame.loc[test, numeric + categorical])[:, 1]
    ok = ~np.isnan(prediction)
    per_fold = []
    for fold in sorted(frame[fold_column].dropna().unique()):
        mask = ok & (frame[fold_column] == fold).to_numpy()
        if frame["y"][mask].nunique() > 1:
            per_fold.append(float(roc_auc_score(frame["y"][mask], prediction[mask])))
    return (float(roc_auc_score(frame["y"][ok], prediction[ok])),
            float(np.mean(per_fold)) if per_fold else float("nan"),
            per_fold)


FEATURE_SETS = {
    "age_only": (["age_clean"], []),
    "sex_only": ([], ["sex_clean"]),
    "grade_only": ([], ["grade_clean"]),
    "age_sex": (["age_clean"], ["sex_clean"]),
    "demographics": (["age_clean"], ["sex_clean", "grade_clean"]),
    "demographics_site": (["age_clean"], ["sex_clean", "grade_clean", "site_proxy"]),
    "site_proxy_only": ([], ["site_proxy"]),
}
PROTOCOLS = (("standard_cv", "cv_fold"), ("group_cv", "robustness_fold"))


def reference(frame: pd.DataFrame, grids: dict, inner_folds: int) -> list[dict]:
    rows = []
    for name, (numeric, categorical) in FEATURE_SETS.items():
        for protocol, column in PROTOCOLS:
            for model in MODELS:
                pooled, fold_mean, per_fold = _outer_cv(
                    frame, column, numeric, categorical, model, grids[model], inner_folds)
                rows.append({"feature_set": name, "cv_protocol": protocol, "model": model,
                             "n_subjects": int(len(frame)), "auroc": round(pooled, 4),
                             "auroc_fold_mean": round(fold_mean, 4),
                             "auroc_per_fold": [round(v, 4) for v in per_fold]})
                print(f'{name:20s}{protocol:12s}{model:24s}{pooled:8.4f}', flush=True)
    return rows


def dilution(frame: pd.DataFrame, grids: dict, inner_folds: int,
             sizes: tuple[int, ...]) -> list[dict]:
    rng = np.random.default_rng(SEED)
    rows = []
    baseline = {}
    for model in MODELS:
        baseline[model], _, _ = _outer_cv(frame, "cv_fold", ["age_clean"],
                                          ["sex_clean", "grade_clean"], model,
                                          grids[model], inner_folds)
        rows.append({"n_noise_columns": 0, "model": model,
                     "auroc": round(baseline[model], 4), "drop": 0.0})
        print(f'noise=  0 {model:24s}{baseline[model]:8.4f}', flush=True)
    for size in sizes:
        noise = pd.DataFrame(rng.standard_normal((len(frame), size)),
                             columns=[f"z{i}" for i in range(size)])
        wide = pd.concat([frame, noise], axis=1)
        for model in MODELS:
            auroc, _, _ = _outer_cv(wide, "cv_fold", ["age_clean", *noise.columns],
                                    ["sex_clean", "grade_clean"], model, grids[model], inner_folds)
            rows.append({"n_noise_columns": size, "model": model, "auroc": round(auroc, 4),
                         "drop": round(auroc - baseline[model], 4)})
            print(f'noise={size:3d} {model:24s}{auroc:8.4f}  {auroc - baseline[model]:+.4f}', flush=True)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/goal2_8/models.yaml")
    parser.add_argument("--noise-sizes", type=int, nargs="*", default=[25, 40, 80, 320])
    parser.add_argument("--skip-dilution", action="store_true")
    args = parser.parse_args()

    config = load_goal_config(args.config)
    frame = _cohort(config)
    grids = _grids(config)
    inner_folds = int(config["protocol"].get("inner_cv_folds", 3))

    report = {
        "n_subjects": int(len(frame)),
        "prevalence": round(float(frame["y"].mean()), 4),
        "age_usable_fraction": round(float(frame["age_clean"].notna().mean()), 4),
        "inner_cv_folds": inner_folds,
        "reference": reference(frame, grids, inner_folds),
    }
    if not args.skip_dilution:
        report["dilution"] = dilution(frame, grids, inner_folds, tuple(args.noise_sizes))

    out_dir = PROJECT_ROOT / "results" / "demographics_reference"
    out_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(report["reference"]).to_csv(out_dir / "demographics_reference.csv", index=False)
    if "dilution" in report:
        pd.DataFrame(report["dilution"]).to_csv(out_dir / "demographics_dilution.csv", index=False)
    (out_dir / "demographics_reference.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k not in ("reference", "dilution")},
                     indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
