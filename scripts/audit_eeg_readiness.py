#!/usr/bin/env python3
"""Audit EEG task availability and run a CV-pool smoke test."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from chongqing_binary.eeg.index import write_task_availability
from chongqing_binary.readiness import (
    ensure_output_path,
    environment_snapshot,
    load_readiness_config,
    require_cv_only,
    stable_subject_sample,
    text_table,
    write_json,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/readiness/eeg_smoke.yaml")
    parser.add_argument("--smoke-limit", type=int, default=None)
    parser.add_argument("--seed", type=int, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_readiness_config(args.config)
    if args.seed is not None:
        config.setdefault("run", {})["seed"] = args.seed
    if args.smoke_limit is not None:
        config.setdefault("run", {})["smoke_limit_per_class"] = args.smoke_limit

    outputs = write_task_availability(config)
    write_eeg_entry_report(outputs)
    write_eeg_v1_code_audit()
    smoke = run_smoke(config, outputs)
    write_json("artifacts/eeg/smoke/smoke_metrics.json", smoke)
    ensure_output_path("reports/eeg_smoke_report.md").write_text(smoke_report(smoke), encoding="utf-8")


def run_smoke(config: dict, outputs: dict) -> dict:
    seed = int(config.get("run", {}).get("seed", 20260707))
    limit = int(config.get("run", {}).get("smoke_limit_per_class", 2))
    all_rows = {row["L_id"]: row for rows in outputs.values() for row in rows}
    sample = stable_subject_sample(list(all_rows.values()), limit, seed)
    require_cv_only(sample)
    checks = []
    for row in sample:
        per_task = {}
        for task, rows in outputs.items():
            task_row = next((item for item in rows if item["L_id"] == row["L_id"]), None)
            if task_row:
                per_task[task] = {
                    "data_bdf_readable": task_row.get("data_bdf_readable"),
                    "required_channels_complete": task_row.get("required_channels_complete"),
                    "duration_sec": task_row.get("duration_sec"),
                    "qc_pass": task_row.get("qc_pass"),
                }
        checks.append({"L_id": row["L_id"], "label": row["primary_label_nonhealthy"], "split_group": row["split_group"], "tasks": per_task})
    model_shapes = torch_forward_shapes()
    passed = bool(sample) and all(row.get("split_group") == "cv" for row in sample) and model_shapes.get("torch_available") is True
    return {
        "stage": "Goal 2.5 EEG smoke",
        "pilot_holdout_used": False,
        "formal_training": False,
        "config": {"path": config.get("_config_path", ""), "seed": seed},
        "sample_subjects": [{"L_id": row["L_id"], "label": row["primary_label_nonhealthy"], "split_group": row["split_group"]} for row in sample],
        "checks": checks,
        "model_forward_shapes": model_shapes,
        "environment": environment_snapshot(),
        "passed": passed,
        "failure_reason": "" if passed else "torch_missing_or_no_cv_sample",
    }


def torch_forward_shapes() -> dict:
    try:
        import torch  # type: ignore
        from torch import nn  # type: ignore

        class TinyEEGNet(nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.net = nn.Sequential(nn.Conv2d(1, 4, (1, 16), padding=(0, 8)), nn.ELU(), nn.AdaptiveAvgPool2d((1, 1)))
                self.fc = nn.Linear(4, 1)

            def forward(self, x):
                return self.fc(self.net(x.unsqueeze(1)).flatten(1))

        class TinyInception(nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.a = nn.Conv1d(32, 8, 9, padding=4)
                self.b = nn.Conv1d(32, 8, 19, padding=9)
                self.fc = nn.Linear(16, 1)

            def forward(self, x):
                z = torch.cat([self.a(x), self.b(x)], dim=1).mean(dim=-1)
                return self.fc(z)

        x = torch.zeros(2, 32, 250)
        return {
            "torch_available": True,
            "eegnet_input_shape": list(x.shape),
            "eegnet_output_shape": list(TinyEEGNet()(x).shape),
            "inceptiontime_input_shape": list(x.shape),
            "inceptiontime_output_shape": list(TinyInception()(x).shape),
        }
    except Exception as exc:
        return {"torch_available": False, "error": type(exc).__name__ + ":" + str(exc)[:160]}


def write_eeg_entry_report(outputs: dict) -> None:
    lines = ["# EEG Data Entry Audit", "", "Task-level tables inherit `subject_splits_v1.csv`; one row per `L_id` per task."]
    for task, rows in outputs.items():
        stats = {
            "rows": len(rows),
            "data_bdf_exists": sum(1 for row in rows if _one(row.get("data_bdf_exists"))),
            "data_bdf_readable": sum(1 for row in rows if _one(row.get("data_bdf_readable"))),
            "event_bdf_readable": sum(1 for row in rows if _one(row.get("event_bdf_readable"))),
            "qc_pass": sum(1 for row in rows if _one(row.get("qc_pass"))),
            "traditional_feature_exists": sum(1 for row in rows if _one(row.get("traditional_feature_exists"))),
            "deep_window_cache_exists": sum(1 for row in rows if _one(row.get("deep_window_cache_exists"))),
        }
        lines.extend(["", f"## {task}", "", text_table(stats)])
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Header readability is checked without loading full BDF signals.",
            "- Event code counts are taken from existing v1 deep-window metadata where present.",
            "- Old v1 features/cache are treated as readiness evidence only, not as fixed-split model results.",
        ]
    )
    ensure_output_path("reports/eeg_data_entry_audit.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _one(value: object) -> bool:
    return str(value) in {"1", "true", "True"}


def write_eeg_v1_code_audit() -> None:
    text = """# EEG v1 Code Audit

## Main Findings

- The v1 traditional Rest baseline and deep EEG scripts do not inherit `artifacts/splits/subject_splits_v1.csv`; they generate their own `StratifiedKFold` splits and therefore are not directly comparable with the fixed-split baseline.
- The deep training script defaults to `--device cuda:0`, uses `WeightedRandomSampler` and `BCEWithLogitsLoss(pos_weight)` together, and can double-compensate class imbalance.
- Early stopping/checkpoint selection is based on training loss rather than an independent inner validation split.
- Thresholds are selected from training subject predictions in the old deep script, so threshold-dependent metrics are optimistic unless redesigned.
- Window-level datasets are split through subject IDs in the old deep script, but subjects with more accepted windows can still receive implicit larger training weight.
- Rest/Oddball/1BACK window definitions and event codes are encoded in v1 scripts, but the raw event structure still needs task-level audit before formal Goal 3.

## Comparability

Treat v1 EEG results as exploratory. Goal 3 must use the global fixed CV pool, subject-level OOF aggregation, inner validation for checkpointing/early stopping, and no pilot-holdout decisions.
"""
    ensure_output_path("reports/eeg_v1_code_audit.md").write_text(text, encoding="utf-8")


def smoke_report(smoke: dict) -> str:
    return "\n".join(
        [
            "# EEG Smoke Report",
            "",
            f"- Passed: `{smoke['passed']}`",
            "- Formal training: `False`",
            "- Pilot holdout used: `False`",
            f"- Sample subjects: {len(smoke['sample_subjects'])}",
            f"- Model forward shapes: `{json.dumps(smoke['model_forward_shapes'], ensure_ascii=False)}`",
            f"- Failure reason: `{smoke.get('failure_reason','')}`",
        ]
    ) + "\n"


if __name__ == "__main__":
    main()
