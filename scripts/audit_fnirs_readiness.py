#!/usr/bin/env python3
"""Audit fNIRS device/task availability and smoke-read file semantics."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from chongqing_binary.fnirs.devices import alignment_policy
from chongqing_binary.fnirs.index import write_task_availability
from chongqing_binary.readiness import ensure_output_path, environment_snapshot, load_readiness_config, text_table, write_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/readiness/fnirs_smoke.yaml")
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
    write_fnirs_entry_report(outputs)
    write_device_alignment_report(outputs)
    smoke = run_smoke(config, outputs)
    write_json("artifacts/fnirs/smoke/smoke_metrics.json", smoke)
    ensure_output_path("reports/fnirs_smoke_report.md").write_text(smoke_report(smoke), encoding="utf-8")


def run_smoke(config: dict, outputs: dict) -> dict:
    limit = int(config.get("run", {}).get("smoke_limit_per_class", 2))
    checks = []
    for key, rows in outputs.items():
        selected = []
        for label in ("0", "1"):
            group = [
                row
                for row in rows
                if row.get("split_group") == "cv"
                and row.get("primary_label_nonhealthy") == label
                and str(row.get("file_readable")) == "1"
            ][:limit]
            selected.extend(group)
        for row in selected:
            checks.append(
                {
                    "device_task": key,
                    "L_id": row["L_id"],
                    "label": row["primary_label_nonhealthy"],
                    "split_group": row["split_group"],
                    "file_format": row.get("file_format"),
                    "file_readable": row.get("file_readable"),
                    "raw_intensity_exists": row.get("raw_intensity_exists"),
                    "optical_density_computable": row.get("optical_density_computable"),
                    "hbo_hbr_exists_or_computable": row.get("hbo_hbr_exists_or_computable"),
                    "event_marker_exists": row.get("event_marker_exists"),
                    "tensor_shape_check": "metadata_shape_only",
                    "traditional_feature_output": "planned_not_materialized_goal2_5",
                }
            )
    passed = bool(checks) and all(item["split_group"] == "cv" for item in checks)
    return {
        "stage": "Goal 2.5 fNIRS smoke",
        "pilot_holdout_used": False,
        "formal_training": False,
        "config": {"path": config.get("_config_path", ""), "seed": int(config.get("run", {}).get("seed", 20260707))},
        "checks": checks,
        "alignment_policy": alignment_policy(),
        "environment": environment_snapshot(),
        "passed": passed,
        "failure_reason": "" if passed else "no_readable_cv_pool_fnirs_files",
    }


def write_fnirs_entry_report(outputs: dict) -> None:
    lines = ["# fNIRS Data Entry Audit", "", "All tables inherit `subject_splits_v1.csv`; each device/task table has one row per `L_id`."]
    for key, rows in outputs.items():
        stats = {
            "rows": len(rows),
            "raw_file_exists": sum(1 for row in rows if _one(row.get("raw_file_exists"))),
            "file_readable": sum(1 for row in rows if _one(row.get("file_readable"))),
            "hbo_hbr_exists_or_computable": sum(1 for row in rows if _one(row.get("hbo_hbr_exists_or_computable"))),
            "event_marker_exists": sum(1 for row in rows if _one(row.get("event_marker_exists"))),
            "qc_pass": sum(1 for row in rows if _one(row.get("qc_pass"))),
        }
        lines.extend(["", f"## {key}", "", text_table(stats)])
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Yiruid `.nirs` files expose MATLAB variables such as `d`, `t`, `ml`, `s`, and `Mark_infor` when readable.",
            "- Bikom CSV files provide HbO/HbR/HbT/Mes-style outputs; raw light intensity is not present in the CSV probe.",
            "- Full motion/channel QC and Hb conversion require Goal 4 device-specific preprocessing, not Goal 2.5 formal training.",
        ]
    )
    ensure_output_path("reports/fnirs_data_entry_audit.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_device_alignment_report(outputs: dict) -> None:
    policy = alignment_policy()
    yiruid_rows = [row for key, rows in outputs.items() if key.startswith("yiruid") for row in rows]
    bikom_rows = [row for key, rows in outputs.items() if key.startswith("bikom") for row in rows]
    stats = {
        "yiruid_readable_rows": sum(1 for row in yiruid_rows if _one(row.get("file_readable"))),
        "bikom_readable_rows": sum(1 for row in bikom_rows if _one(row.get("file_readable"))),
        "raw_channel_merge_allowed": "False",
    }
    text = "\n".join(
        [
            "# fNIRS Device Alignment Audit",
            "",
            "## Direct Answers",
            "",
            "1. Direct same raw channel model: **No**. Yiruid and Bikom do not expose the same raw input space in the current audit.",
            "2. Region-level alignment: **Possibly**, but only after channel layout/source-detector geometry is mapped.",
            "3. Event definitions: task names align at directory level, but event codes/segments need device-specific confirmation.",
            "4. Device-specific modeling: all five tasks should start device-specific until alignment is proven.",
            "5. Unified HbO/HbR: possible as a representation goal, not confirmed for direct raw merge.",
            "6. Device-specific encoder: required for any early deep model using device-native channels.",
            "7. Channel mask: required if channel-level tensors are used.",
            "8. Region-level representation: recommended before cross-device comparison.",
            "",
            "## Policy",
            "",
            text_table(policy),
            "",
            "## Evidence Summary",
            "",
            text_table(stats),
        ]
    )
    ensure_output_path("reports/fnirs_device_alignment_audit.md").write_text(text + "\n", encoding="utf-8")


def smoke_report(smoke: dict) -> str:
    return "\n".join(
        [
            "# fNIRS Smoke Report",
            "",
            f"- Passed: `{smoke['passed']}`",
            "- Formal training: `False`",
            "- Pilot holdout used: `False`",
            f"- Smoke checks: {len(smoke['checks'])}",
            f"- Failure reason: `{smoke.get('failure_reason','')}`",
            f"- Alignment policy: `{json.dumps(smoke['alignment_policy'], ensure_ascii=False)}`",
        ]
    ) + "\n"


def _one(value: object) -> bool:
    return str(value) in {"1", "true", "True"}


if __name__ == "__main__":
    main()
