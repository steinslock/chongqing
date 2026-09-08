#!/usr/bin/env python3
"""Verify the one positive result Goal 2.9 produced, and record why it fails.

The combined Yiruid cohort returned eight increments over demographics whose
paired bootstrap intervals excluded zero, under both CV protocols, with
consistent fold direction. This script runs the three checks that decide whether
that is a real effect, and writes the numbers to `results/goal2_9/`.

1. Transfer. Score the same 342 subjects with the models trained on the larger
   per-task cohorts. If the gap is a property of these subjects, it survives. If
   it is a property of training inside a small cohort, it disappears.
2. Pooling. Compare the zero-information model's per-fold AUROC with its pooled
   AUROC. A no-information model must score 0.5 in every fold; any deviation in
   the pooled value is fold-imbalance distortion, not information.
3. Permutation. Shuffle the diagnoses on the exact cohort, features and folds
   that produced the result, and measure how often pure noise reproduces a gap
   as large as the one observed.
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
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

BEHAVIOUR = PROJECT_ROOT / "artifacts" / "goal2_9" / "behaviour"
RESULTS = PROJECT_ROOT / "results" / "goal2_9"
COHORT = "behaviour_yiruid_combined_native"
YIRUID_TASKS = ("1back", "oddball", "doors")
# The largest observed increment, and the smallest one that was called positive.
OBSERVED_MAX_DIFF = 0.0889
OBSERVED_MIN_DIFF = 0.0790


def _load_oof() -> pd.DataFrame:
    frames = []
    for protocol in ("standard_cv", "group_cv"):
        path = RESULTS / f"all_oof_predictions_{protocol}.csv"
        if not path.exists():
            raise SystemExit(f"missing {path}; run scripts/run_goal2_9.py first")
        frame = pd.read_csv(path, dtype={"L_id": str})
        frame["cv_protocol"] = protocol
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)


def _fold_mean_auroc(frame: pd.DataFrame) -> float:
    scores = [roc_auc_score(g["label"], g["probability"])
              for _, g in frame.groupby("outer_fold") if g["label"].nunique() > 1]
    return float(np.mean(scores)) if scores else float("nan")


def transfer_check(oof: pd.DataFrame) -> list[dict]:
    """The same subjects, scored by models trained on the larger cohorts."""
    members = set(oof.loc[oof["cohort_name"] == COHORT, "L_id"])
    rows = []
    cohorts = [f"behaviour_yiruid_{task}_native" for task in YIRUID_TASKS] + [COHORT]
    for cohort in cohorts:
        for protocol in ("standard_cv", "group_cv"):
            for feature_set in ("demographics", "signal"):
                for model in ("hist_gradient_boosting", "random_forest"):
                    g = oof[(oof["cohort_name"] == cohort) & (oof["cv_protocol"] == protocol)
                            & (oof["feature_set"] == feature_set) & (oof["model"] == model)]
                    g = g.drop_duplicates("L_id")
                    g = g[g["L_id"].isin(members)]
                    if len(g) < 50 or g["label"].nunique() < 2:
                        continue
                    rows.append({
                        "cohort": cohort, "trained_on": cohort.replace("behaviour_", "").replace("_native", ""),
                        "cv_protocol": protocol, "feature_set": feature_set, "model": model,
                        "n_scored": int(len(g)),
                        "pooled_auroc": float(roc_auc_score(g["label"], g["probability"])),
                        "fold_mean_auroc": _fold_mean_auroc(g),
                    })
    return rows


def pooling_check(oof: pd.DataFrame) -> list[dict]:
    """A no-information model scores 0.5 per fold; what does it score pooled?"""
    rows = []
    for protocol in ("standard_cv", "group_cv"):
        g = oof[(oof["cohort_name"] == COHORT) & (oof["cv_protocol"] == protocol)
                & (oof["feature_set"] == "no_information")].drop_duplicates("L_id")
        if g.empty or g["label"].nunique() < 2:
            continue
        folds = g.groupby("outer_fold").agg(n=("L_id", "size"), prevalence=("label", "mean"))
        rows.append({
            "cv_protocol": protocol,
            "pooled_auroc": float(roc_auc_score(g["label"], g["probability"])),
            "fold_mean_auroc": _fold_mean_auroc(g),
            "fold_sizes": folds["n"].tolist(),
            "fold_prevalences": [round(float(v), 3) for v in folds["prevalence"]],
        })
    return rows


def _combined_frame() -> tuple[pd.DataFrame, list[str]]:
    parts = []
    for task in YIRUID_TASKS:
        frame = pd.read_csv(BEHAVIOUR / f"yiruid_{task}_signal_features.csv", dtype={"L_id": str})
        columns = [c for c in frame.columns if c.startswith("signal_")]
        parts.append(frame[["L_id", *columns]].rename(columns={c: f"{task}_{c}" for c in columns}))
    joined = parts[0]
    for part in parts[1:]:
        joined = joined.merge(part, on="L_id", how="inner")
    meta = pd.read_csv(BEHAVIOUR / "yiruid_1back_signal_features.csv", dtype={"L_id": str})
    meta = meta[["L_id", "primary_label_nonhealthy", "cv_fold", "age", "sex", "grade"]]
    frame = joined.merge(meta, on="L_id", how="inner")
    frame = frame[pd.to_numeric(frame["primary_label_nonhealthy"], errors="coerce").notna()].reset_index(drop=True)
    frame["y"] = pd.to_numeric(frame["primary_label_nonhealthy"], errors="coerce").astype(int)
    frame["fold"] = pd.to_numeric(frame["cv_fold"], errors="coerce")
    frame["age_num"] = pd.to_numeric(frame["age"], errors="coerce").where(lambda s: s.between(9, 20))
    frame["sex_s"] = frame["sex"].astype(str)
    frame["grade_s"] = frame["grade"].astype(str)
    return frame, [c for c in frame.columns if "signal_" in c]


def _pipeline(numeric: list[str], categorical: list[str], model: str) -> Pipeline:
    transformers = [("n", Pipeline([("i", SimpleImputer(strategy="median")),
                                    ("s", StandardScaler())]), numeric)]
    if categorical:
        transformers.append(("c", Pipeline([
            ("i", SimpleImputer(strategy="most_frequent")),
            ("o", OneHotEncoder(handle_unknown="ignore", sparse_output=False))]), categorical))
    estimator = (RandomForestClassifier(n_estimators=300, min_samples_leaf=2, n_jobs=2,
                                        class_weight="balanced", random_state=0)
                 if model == "random_forest"
                 else HistGradientBoostingClassifier(max_iter=200, random_state=0))
    return Pipeline([("p", ColumnTransformer(transformers)), ("m", estimator)])


def _pooled_oof(frame: pd.DataFrame, label: str, numeric: list[str],
                categorical: list[str], model: str) -> float:
    prediction = np.full(len(frame), np.nan)
    for fold in sorted(frame["fold"].dropna().unique()):
        train, test = frame["fold"] != fold, frame["fold"] == fold
        if frame.loc[train, label].nunique() < 2 or test.sum() == 0:
            continue
        fitted = _pipeline(numeric, categorical, model).fit(
            frame.loc[train, numeric + categorical], frame.loc[train, label])
        prediction[test.to_numpy()] = fitted.predict_proba(
            frame.loc[test, numeric + categorical])[:, 1]
    ok = ~np.isnan(prediction)
    if frame[label][ok].nunique() < 2:
        return float("nan")
    return float(roc_auc_score(frame[label][ok], prediction[ok]))


def permutation_check(n_permutations: int, seed: int) -> dict:
    """How often does noise reproduce the observed gap on this exact cohort?"""
    frame, signal_columns = _combined_frame()
    rng = np.random.default_rng(seed)
    rows = []
    for rep in range(n_permutations + 1):
        frame["yp"] = frame["y"] if rep == 0 else rng.permutation(frame["y"].to_numpy())
        for model in ("random_forest", "hist_gradient_boosting"):
            demographics = _pooled_oof(frame, "yp", ["age_num"], ["sex_s", "grade_s"], model)
            signal = _pooled_oof(frame, "yp", signal_columns, [], model)
            rows.append({"rep": rep, "model": model, "demographics": demographics,
                         "signal": signal, "diff": signal - demographics})
    table = pd.DataFrame(rows)
    table.to_csv(RESULTS / "positive_result_permutation.csv", index=False)
    permuted = table[table["rep"] > 0]
    summary = {
        "n_subjects": int(len(frame)),
        "n_behaviour_features": len(signal_columns),
        "prevalence": round(float(frame["y"].mean()), 4),
        "n_permutations": n_permutations,
        "real_labels": table[table["rep"] == 0].set_index("model")[
            ["demographics", "signal", "diff"]].round(4).to_dict(orient="index"),
        "permuted": {},
    }
    for model, group in permuted.groupby("model"):
        summary["permuted"][model] = {
            "demographics_mean": round(float(group["demographics"].mean()), 4),
            "demographics_below_chance_rate": round(float((group["demographics"] < 0.5).mean()), 4),
            "signal_mean": round(float(group["signal"].mean()), 4),
            "diff_mean": round(float(group["diff"].mean()), 4),
            "diff_sd": round(float(group["diff"].std()), 4),
            "diff_max": round(float(group["diff"].max()), 4),
            "p_diff_ge_observed_min": round(float((group["diff"] >= OBSERVED_MIN_DIFF).mean()), 4),
            "p_diff_ge_observed_max": round(float((group["diff"] >= OBSERVED_MAX_DIFF).mean()), 4),
        }
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--permutations", type=int, default=100)
    parser.add_argument("--seed", type=int, default=20260908)
    args = parser.parse_args()

    oof = _load_oof()
    report = {
        "cohort": COHORT,
        "observed_increment_range": [OBSERVED_MIN_DIFF, OBSERVED_MAX_DIFF],
        "transfer": transfer_check(oof),
        "pooling": pooling_check(oof),
        "permutation": permutation_check(args.permutations, args.seed),
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(report["transfer"]).to_csv(RESULTS / "positive_result_transfer.csv", index=False)
    (RESULTS / "positive_result_verification.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "transfer"},
                     indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
