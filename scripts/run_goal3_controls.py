#!/usr/bin/env python
"""Goal 3 positive controls and the acquisition-group shortcut probe.

PC1 (target versus standard, trial level) is a hard gate: below 0.70 AUROC the
pipeline is broken and no label result may be reported. PC2 (sex) and PC3 (age)
are reported rather than gated -- they calibrate how much subject-level
information the aggregation can extract at all, and gating on them would stop
the goal on a literature prior rather than on this dataset.

The group probe asks whether the learned representation encodes the recording
site, which is a shortcut risk whatever it does for the label.
"""

from __future__ import annotations

import argparse

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from chongqing_binary.goal3.config import ensure_output, load_goal_config, project_path
from chongqing_binary.goal3.controls import run_condition_decoding, run_group_probe
from chongqing_binary.goal3.protocol import load_cohort
from chongqing_binary.goal3.runner import Configuration, run_deep_job
from chongqing_binary.goal3.train import candidate_devices


def _control_cohort(cohort: pd.DataFrame) -> pd.DataFrame:
    out = cohort.copy()
    sex = out["sex"].astype("string").str.strip()
    out["control_sex"] = np.where(sex.eq("男"), 1, np.where(sex.eq("女"), 0, np.nan))
    age = pd.to_numeric(out["age"], errors="coerce")
    out["control_age_high"] = (age > age.median()).astype(float).where(age.notna())
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/goal3/common.yaml")
    parser.add_argument("--stage", choices=["pc1", "subject", "group", "all"], default="all")
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    config = load_goal_config(args.config)
    results_dir = project_path(config["paths"]["results_dir"])
    rows: list[pd.DataFrame] = []

    if args.stage in {"pc1", "all"}:
        pc1 = run_condition_decoding(config, encoder="eegnet", seed=args.seed)
        pc1.to_csv(ensure_output(results_dir / "control_pc1_condition_decoding.csv", config), index=False)
        print(pc1.groupby("cv_protocol")["auroc"].agg(["mean", "min", "max"]).round(4))
        rows.append(pc1.assign(control="pc1_target_vs_standard"))

    if args.stage in {"subject", "all"}:
        cohort = _control_cohort(load_cohort(config))
        configuration = Configuration("eegnet", "condition_aware", arm="control")
        for label_column, name in [("control_sex", "pc2_sex"), ("control_age_high", "pc3_age")]:
            usable = cohort[cohort[label_column].notna()].copy()
            usable[label_column] = usable[label_column].astype(int)
            for protocol in config["protocol"]["cv_protocols"]:
                result = run_deep_job(
                    config, configuration, protocol, args.seed, label_column=label_column,
                    devices=candidate_devices(min_free_mb=int(config["deep"]["min_free_mb"])),
                    cohort=usable, use_tabular=False,
                )
                predictions = result["predictions"]
                predictions.to_csv(
                    ensure_output(results_dir / f"control_{name}_{protocol}.csv", config), index=False)
                auroc = roc_auc_score(predictions["label"], predictions["probability"])
                per_fold = predictions.groupby("outer_fold").apply(
                    lambda g: roc_auc_score(g["label"], g["probability"]), include_groups=False)
                print(f"{name} {protocol}: pooled AUROC {auroc:.4f}  "
                      f"folds {np.round(per_fold.to_numpy(), 3).tolist()}  n={predictions['L_id'].nunique()}")
                rows.append(pd.DataFrame([{
                    "control": name, "cv_protocol": protocol, "seed": args.seed,
                    "n_subjects": int(predictions["L_id"].nunique()), "auroc": float(auroc),
                    "auroc_fold_min": float(per_fold.min()), "auroc_fold_max": float(per_fold.max()),
                }]))

    if args.stage in {"group", "all"}:
        cohort = load_cohort(config)
        files = sorted(project_path(config["outputs"]["jobs_dir"]).glob("*.embeddings.csv"))
        if not files:
            print("no embeddings found; run the confirmatory deep jobs first")
        else:
            probes = []
            for path in files:
                embeddings = pd.read_csv(path, dtype={"L_id": str})
                try:
                    probe = run_group_probe(config, embeddings, cohort, seed=args.seed)
                except ValueError as exc:
                    print(f"skipping {path.name}: {exc}")
                    continue
                if not probe.empty:
                    probe.insert(0, "source", path.name)
                    probes.append(probe)
            if probes:
                out = pd.concat(probes, ignore_index=True)
                out.to_csv(ensure_output(config["outputs"]["group_probe"], config), index=False)
                print(out.to_string(index=False))

    if rows:
        summary = pd.concat(rows, ignore_index=True)
        summary.to_csv(ensure_output(config["outputs"]["positive_controls"], config), index=False)


if __name__ == "__main__":
    main()
