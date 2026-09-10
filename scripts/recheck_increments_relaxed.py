#!/usr/bin/env python
"""Re-check every stage's `modality + demographics vs demographics` increment.

The project's decision rule accumulated clauses across Goal 2.7 to Goal 3, each
added because a specific result turned out to be an artefact. A fair question is
what the clauses cost: how many increments would be credited if most of them
were dropped.

This script answers it directly. It reads every stage's paired comparison table,
attaches the demographics comparator each row was measured against, and reports
how many rows survive at each level of strictness, from "the interval excludes
zero" upward. It adds no criterion of its own and issues no verdict; the output
is a ladder for a human to read.

Scope is the comparison that matters for a go decision, `X + demographics`
against `demographics`. Comparisons against background, QC or a modality alone
are shortcut controls and are excluded.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

GOALS = ["goal2_7", "goal2_8", "goal2_9", "goal2_10", "goal3"]

# Grouping keys shared by the paired and pooled tables in every stage.
KEYS = ["cv_protocol", "cohort_name", "modality", "device", "task", "model", "seed"]

# Every naming the stages used for "modality + demographics against demographics".
INCREMENTS = {
    "signal_demographics_vs_demographics",
    "signal_qc_demographics_vs_demographics",
    "face_demographics_vs_demographics",
    "face_qc_demographics_vs_demographics",
    "modality_demographics_vs_demographics",
    "signal_absolute_demographics_vs_demographics",
    "signal_contrast_demographics_vs_demographics",
    "demographics_eeg_deep_vs_demographics",
    "demographics_eeg_traditional_vs_demographics",
}


def load(root: Path) -> pd.DataFrame:
    frames = []
    for goal in GOALS:
        paired_path = root / "results" / goal / "paired_increment_comparisons.csv"
        pooled_path = root / "results" / goal / "all_pooled_metrics.csv"
        if not paired_path.exists() or not pooled_path.exists():
            continue
        paired = pd.read_csv(paired_path)
        # Goal 3 already carries these; drop them so the merge does not suffix
        # and silently leave the column empty for that stage.
        paired = paired.drop(columns=[c for c in ("comparator_auroc", "comparator_above_chance")
                                      if c in paired.columns])
        pooled = pd.read_csv(pooled_path)
        for frame in (paired, pooled):
            for key in KEYS:
                if key in frame.columns:
                    frame[key] = frame[key].fillna("").astype(str)
        pooled = pooled[(pooled["threshold_type"] == "inner_cv")
                        & (pooled["feature_set"] == "demographics")]
        comparator = (pooled[KEYS + ["auroc"]]
                      .rename(columns={"auroc": "comparator_auroc"})
                      .drop_duplicates(KEYS))
        block = paired[paired["comparison"].isin(INCREMENTS)].merge(comparator, on=KEYS, how="left")
        block["goal"] = goal
        frames.append(block)
    out = pd.concat(frames, ignore_index=True)
    out["interval_excludes_zero"] = out["auroc_diff_ci_low"] > 0
    out["comparator_above_chance"] = out["comparator_auroc"] > 0.5
    out["folds_at_least_4"] = out["fold_direction_consistency"] >= 4
    return out


def ladder(frame: pd.DataFrame, by: str) -> pd.DataFrame:
    def counts(block: pd.DataFrame) -> pd.Series:
        a = block["interval_excludes_zero"]
        b = a & block["comparator_above_chance"]
        c = b & block["folds_at_least_4"]
        return pd.Series({
            "rows": len(block),
            "L1_interval_excludes_zero": int(a.sum()),
            "L2_and_comparator_above_chance": int(b.sum()),
            "L3_and_at_least_4_of_5_folds": int(c.sum()),
        })

    return frame.groupby(by).apply(counts, include_groups=False).reset_index()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = Path(args.root)

    frame = load(root)
    out_dir = root / "results" / "increment_recheck"
    out_dir.mkdir(parents=True, exist_ok=True)

    by_modality = ladder(frame, "modality")
    by_goal = ladder(frame, "goal")
    credited = frame[frame["interval_excludes_zero"] & frame["comparator_above_chance"]]

    frame.to_csv(out_dir / "all_increments_with_comparators.csv", index=False)
    by_modality.to_csv(out_dir / "ladder_by_modality.csv", index=False)
    by_goal.to_csv(out_dir / "ladder_by_goal.csv", index=False)
    credited.to_csv(out_dir / "credited_under_relaxed_rule.csv", index=False)

    print(f"rows: {len(frame)}   missing comparator: {int(frame['comparator_auroc'].isna().sum())}")
    print("\nBy modality:\n")
    print(by_modality.to_string(index=False))
    print("\nBy stage:\n")
    print(by_goal.to_string(index=False))
    print("\nCredited at L2, by stage and comparison:\n")
    if credited.empty:
        print("  none")
    else:
        print(credited.groupby(["goal", "modality", "comparison"]).size()
              .rename("rows").to_string())
    print(f"\nWritten to {out_dir}")


if __name__ == "__main__":
    main()
