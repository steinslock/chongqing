"""Goal 3 summarisation and decision.

Reuses the Goal 2.7 pooled-metric, bootstrap and paired-increment machinery so
Goal 3 numbers are directly comparable with Goal 2.8's, and adds what this stage
needs on top: seed averaging, two-sided bootstrap p-values with FDR control over
the declared exploratory family, and the confirmatory/exploratory verdict.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from ..goal2_7.runner import (
    _bootstrap_table,
    _bootstrap_weights,
    _paired_comparisons,
    _pooled_metrics,
    _stable_seed,
    _weighted_auc_samples,
)
from .config import load_goal_config, project_path
from .runner import declared_configurations

GROUP_COLS = ["cv_protocol", "cohort_name", "modality", "device", "task", "feature_set", "model", "seed"]


def load_jobs(config: dict[str, Any]) -> pd.DataFrame:
    directory = project_path(config["outputs"]["jobs_dir"])
    files = sorted(p for p in directory.glob("*.csv")
                   if not p.name.endswith((".diagnostics.csv", ".embeddings.csv")))
    if not files:
        return pd.DataFrame()
    frames = [pd.read_csv(p, dtype={"L_id": str, "device": str}) for p in files]
    out = pd.concat(frames, ignore_index=True)
    out["device"] = out["device"].fillna("")
    return out


def add_seed_average(predictions: pd.DataFrame) -> pd.DataFrame:
    """Seed-averaged rows, which are the primary result.

    The paired bootstrap resamples subjects and is blind to how unstable the fit
    itself is; averaging three seeds is what makes the primary score robust to
    that, and the per-seed rows are kept so the spread can be reported.
    """
    keys = [c for c in GROUP_COLS if c != "seed"] + ["outer_fold", "L_id", "label"]
    averaged = (predictions.groupby(keys, dropna=False, as_index=False)
                .agg(probability=("probability", "mean"),
                     fold_specific_threshold=("fold_specific_threshold", "mean"),
                     n_seeds=("seed", "nunique")))
    averaged["seed"] = "mean"
    out = pd.concat([predictions, averaged.drop(columns=["n_seeds"])], ignore_index=True)
    # `seed` now holds both integers and the literal "mean"; pandas cannot group
    # on a mixed-type column, and every downstream table groups on it.
    out["seed"] = out["seed"].astype(str)
    return out


def seed_spread(predictions: pd.DataFrame) -> pd.DataFrame:
    """Per-seed AUROC and its spread, per configuration and feature set."""
    rows = []
    keys = [c for c in GROUP_COLS if c != "seed"]
    for key, group in predictions[predictions["seed"] != "mean"].groupby(keys, dropna=False):
        per_seed = {}
        for seed, block in group.groupby("seed"):
            if block["label"].nunique() > 1:
                per_seed[str(seed)] = float(roc_auc_score(block["label"], block["probability"]))
        if not per_seed:
            continue
        values = np.array(list(per_seed.values()))
        rows.append({**dict(zip(keys, key)), "n_seeds": len(values),
                     "auroc_seed_mean": float(values.mean()),
                     "auroc_seed_std": float(values.std(ddof=1)) if len(values) > 1 else math.nan,
                     "auroc_seed_min": float(values.min()), "auroc_seed_max": float(values.max())})
    return pd.DataFrame(rows)


def paired_p_values(predictions: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
    """Two-sided bootstrap p-values for the declared pairs.

    `_paired_comparisons` gives intervals, which decide the confirmatory test.
    The exploratory family additionally needs FDR control, and that needs
    p-values, so the same paired subject bootstrap is run here for its tail
    probabilities.
    """
    pairs = [(str(a), str(b)) for a, b in config["protocol"]["paired_comparison_pairs"]]
    n_boot = int(config["bootstrap"]["paired_n_resamples"])
    seed = int(config["bootstrap"]["paired_seed"])
    keys = ["cv_protocol", "cohort_name", "modality", "device", "task", "model", "seed"]
    rows = []
    for key, group in predictions.groupby(keys, dropna=False):
        for left, right in pairs:
            a = group[group["feature_set"] == left]
            b = group[group["feature_set"] == right]
            if a.empty or b.empty:
                continue
            merged = a[["L_id", "label", "probability", "outer_fold"]].merge(
                b[["L_id", "label", "probability", "outer_fold"]],
                on=["L_id", "outer_fold"], suffixes=("_a", "_b"))
            if len(merged) < 10:
                continue
            y = merged["label_a"].to_numpy(dtype=int)
            rng = np.random.default_rng(_stable_seed(seed, *map(str, key), left, right))
            weights = _bootstrap_weights(len(merged), n_boot, rng)
            diffs = (_weighted_auc_samples(y, merged["probability_a"].to_numpy(float), weights)
                     - _weighted_auc_samples(y, merged["probability_b"].to_numpy(float), weights))
            finite = diffs[np.isfinite(diffs)]
            if finite.size == 0:
                continue
            tail = min(float((finite <= 0).mean()), float((finite >= 0).mean()))
            rows.append({**dict(zip(keys, key)), "comparison": f"{left}_vs_{right}",
                         "feature_set_a": left, "feature_set_b": right,
                         "auroc_diff": float(np.median(finite)),
                         "p_two_sided": float(min(1.0, max(2.0 * tail, 1.0 / n_boot)))})
    return pd.DataFrame(rows)


def benjamini_hochberg(p_values: np.ndarray, alpha: float = 0.05) -> np.ndarray:
    """Step-up FDR control. Returns the rejection mask."""
    order = np.argsort(p_values)
    ranked = p_values[order]
    n = len(p_values)
    passing = ranked <= (np.arange(1, n + 1) / n) * alpha
    mask = np.zeros(n, dtype=bool)
    if passing.any():
        cutoff = np.max(np.flatnonzero(passing))
        mask[order[: cutoff + 1]] = True
    return mask


def attach_comparators(paired: pd.DataFrame, pooled: pd.DataFrame) -> pd.DataFrame:
    """Record each comparison's comparator AUROC and whether it beats chance.

    Goal 2.9 introduced the rule that a credited increment must beat a
    comparator that is itself above chance, and Goal 2.10 withdrew eighteen rows
    under it. The rule was written for demographics comparators, but nothing in
    it is specific to demographics: an increment over a below-chance
    `eeg_traditional` is a statement about the traditional features, not about
    the deep representation. It is therefore applied to every comparison here.
    """
    reference = (pooled[pooled["threshold_type"] == "inner_cv"]
                 [["cv_protocol", "model", "seed", "feature_set", "auroc"]]
                 .rename(columns={"feature_set": "feature_set_b", "auroc": "comparator_auroc"})
                 .copy())
    reference["seed"] = reference["seed"].astype(str)
    out = paired.copy()
    out["seed"] = out["seed"].astype(str)
    out = out.merge(reference, on=["cv_protocol", "model", "seed", "feature_set_b"], how="left")
    out["comparator_above_chance"] = (out["comparator_auroc"] > 0.5).astype("Int64")
    return out


def build_decision(paired: pd.DataFrame, p_values: pd.DataFrame, pooled: pd.DataFrame,
                   config: dict[str, Any], alpha: float = 0.05) -> pd.DataFrame:
    """Apply the pre-registered decision rule, confirmatory and exploratory.

    Confirmatory: one declared test, no multiplicity correction. Exploratory: the
    enumerated closed family, with the same requirements plus FDR control, and a
    verdict that is a discovery needing replication rather than a go.
    """
    arms = {c.config_id: c.arm for c in declared_configurations()}
    primary = "demographics_eeg_deep_vs_demographics"
    if "comparator_above_chance" not in paired.columns:
        paired = attach_comparators(paired, pooled)
    rows = paired[(paired["comparison"] == primary) & (paired["seed"].astype(str) == "mean")].copy()
    if rows.empty:
        return pd.DataFrame()

    rows["arm"] = rows["model"].map(arms)
    merged = rows.merge(
        p_values[p_values["seed"].astype(str) == "mean"][["cv_protocol", "model", "comparison", "p_two_sided"]],
        on=["cv_protocol", "model", "comparison"], how="left")
    merged["comparator_above_chance"] = merged["comparator_above_chance"].fillna(0).astype(int)
    merged["interval_excludes_zero_positive"] = (merged["auroc_diff_ci_low"] > 0).astype(int)
    merged["folds_positive"] = merged["fold_direction_consistency"]

    exploratory = merged["arm"] == "exploratory"
    merged["fdr_significant"] = 0
    if exploratory.any():
        values = merged.loc[exploratory, "p_two_sided"].fillna(1.0).to_numpy(dtype=float)
        merged.loc[exploratory, "fdr_significant"] = benjamini_hochberg(values, alpha).astype(int)

    # Both protocols must agree for any verdict.
    positive_by_config: dict[str, set[str]] = {}
    for _, row in merged.iterrows():
        if row["interval_excludes_zero_positive"] and row["comparator_above_chance"]:
            positive_by_config.setdefault(row["model"], set()).add(row["cv_protocol"])
    merged["both_protocols_positive"] = [
        int(len(positive_by_config.get(m, set())) == 2) for m in merged["model"]
    ]

    verdicts = []
    for _, row in merged.iterrows():
        base = (row["interval_excludes_zero_positive"] and row["comparator_above_chance"]
                and row["both_protocols_positive"] and row["folds_positive"] >= 4)
        if row["arm"] == "confirmatory":
            verdicts.append("INDEPENDENT_SIGNAL_SUPPORTED" if base
                            else ("SHORTCUT_SENSITIVE" if row["interval_excludes_zero_positive"]
                                  and not row["both_protocols_positive"] else "NO_INDEPENDENT_SIGNAL"))
        elif row["arm"] == "exploratory":
            verdicts.append("EXPLORATORY_SIGNAL_REQUIRES_REPLICATION"
                            if base and row["fdr_significant"]
                            else ("SHORTCUT_SENSITIVE" if row["interval_excludes_zero_positive"]
                                  and not row["both_protocols_positive"] else "NO_INDEPENDENT_SIGNAL"))
        else:
            verdicts.append("ABLATION_NOT_A_VERDICT")
    merged["verdict"] = verdicts
    merged["permutation_verification_required"] = [
        int(v == "EXPLORATORY_SIGNAL_REQUIRES_REPLICATION") for v in verdicts
    ]
    return merged


def summarise(config_path: str | Path = "configs/goal3/common.yaml") -> dict[str, Any]:
    config = load_goal_config(config_path)
    predictions = load_jobs(config)
    if predictions.empty:
        raise SystemExit("no Goal 3 job outputs found; run scripts/run_goal3.py first")
    predictions = add_seed_average(predictions)

    outputs = config["outputs"]
    project_path(outputs["all_oof_predictions"]).parent.mkdir(parents=True, exist_ok=True)
    predictions.to_csv(project_path(outputs["all_oof_predictions"]), index=False)

    pooled = _pooled_metrics(predictions, config)
    pooled.to_csv(project_path(outputs["all_pooled_metrics"]), index=False)
    bootstrap = _bootstrap_table(predictions, config)
    bootstrap.to_csv(project_path(outputs["bootstrap_ci"]), index=False)
    paired = attach_comparators(_paired_comparisons(predictions, config), pooled)
    paired.to_csv(project_path(outputs["paired_comparisons"]), index=False)

    p_values = paired_p_values(predictions, config)
    p_values.to_csv(project_path(config["paths"]["results_dir"]) / "paired_p_values.csv", index=False)
    spread = seed_spread(predictions)
    spread.to_csv(project_path(config["paths"]["results_dir"]) / "seed_spread.csv", index=False)

    decision = build_decision(paired, p_values, pooled, config)
    decision.to_csv(project_path(outputs["decision"]), index=False)
    report_path = write_results_report(config, pooled, paired, decision, spread)
    return {
        "n_predictions": len(predictions),
        "n_pooled_rows": len(pooled),
        "n_paired_rows": len(paired),
        "n_decision_rows": len(decision),
        "verdicts": decision["verdict"].value_counts().to_dict() if not decision.empty else {},
        "report": str(report_path),
    }


def _markdown(frame: pd.DataFrame, limit: int = 60) -> str:
    if frame is None or frame.empty:
        return "_no rows_"
    shown = frame.head(limit)
    body = shown.to_markdown(index=False, floatfmt=".4f")
    if len(frame) > limit:
        body += f"\n\nShowing {limit} of {len(frame)} rows."
    return body


def write_results_report(config: dict[str, Any], pooled: pd.DataFrame, paired: pd.DataFrame,
                         decision: pd.DataFrame, spread: pd.DataFrame) -> Path:
    """Render the machine-generated results tables, as every earlier goal does."""
    reports_dir = project_path(config["paths"]["reports_dir"])
    reports_dir.mkdir(parents=True, exist_ok=True)

    mean = pooled[(pooled["seed"].astype(str) == "mean") & (pooled["threshold_type"] == "inner_cv")]
    headline = (mean[["cv_protocol", "model", "feature_set", "n_subjects", "auroc", "auprc"]]
                .sort_values(["cv_protocol", "model", "feature_set"]))
    primary = decision[decision["arm"] == "confirmatory"] if not decision.empty else pd.DataFrame()
    confirm_cols = ["cv_protocol", "model", "auroc_diff", "auroc_diff_ci_low", "auroc_diff_ci_high",
                    "comparator_auroc", "comparator_above_chance", "folds_positive",
                    "both_protocols_positive", "verdict"]
    explore_cols = confirm_cols[:-1] + ["p_two_sided", "fdr_significant", "verdict"]

    increments = (paired[paired["seed"].astype(str) == "mean"]
                  [["cv_protocol", "model", "comparison", "n_subjects", "auroc_diff",
                    "auroc_diff_ci_low", "auroc_diff_ci_high", "fold_direction_consistency",
                    "comparator_auroc", "comparator_above_chance"]]
                  .sort_values(["comparison", "cv_protocol", "auroc_diff"], ascending=[True, True, False]))

    lines = [
        "# Goal 3 Results",
        "",
        "Machine-generated from `results/goal3/`. The design, the decision rule and the",
        "predictions recorded before any model was trained are in",
        "`reports/goal3_method_design.md`; the reading of these numbers is in",
        "`reports/goal3_final_report.md`.",
        "",
        "Every row is the seed-averaged result over three seeds, on the same 1820 subjects",
        "and the same fixed folds as Goal 2.8, with inner-CV thresholds.",
        "",
        "## Confirmatory Test",
        "",
        "EEGNet, condition-aware, no per-subject normalisation: `p_Demo + p_EEG` against",
        "`p_Demo`, under both CV protocols. One pre-declared test, no multiplicity",
        "correction.",
        "",
        _markdown(primary[[c for c in confirm_cols if c in primary.columns]] if not primary.empty else primary),
        "",
        "## Exploratory Family",
        "",
        "Twelve configurations x two protocols, closed and enumerated before the run.",
        "Benjamini-Hochberg at 0.05 across the family, on two-sided paired bootstrap",
        "p-values, in addition to every confirmatory requirement.",
        "",
        _markdown(decision[decision["arm"] == "exploratory"][[c for c in explore_cols if c in decision.columns]]
                  if not decision.empty else decision, limit=30),
        "",
        "## All Paired Increments",
        "",
        _markdown(increments, limit=90),
        "",
        "## Pooled AUROC By Feature Set",
        "",
        _markdown(headline, limit=120),
        "",
        "## Between-Seed Spread",
        "",
        "The paired bootstrap resamples subjects and is blind to the instability of the fit.",
        "",
        _markdown(spread[["cv_protocol", "model", "feature_set", "n_seeds", "auroc_seed_mean",
                          "auroc_seed_std", "auroc_seed_min", "auroc_seed_max"]]
                  .sort_values(["feature_set", "cv_protocol", "model"])
                  if not spread.empty else spread, limit=90),
    ]
    path = reports_dir / "goal3_results.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
