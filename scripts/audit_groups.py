#!/usr/bin/env python3
"""Audit site/batch/device proxy groups."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from chongqing_binary.groups import write_group_outputs
from chongqing_binary.readiness import environment_snapshot, load_readiness_config, write_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/readiness/default.yaml")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--smoke-limit", type=int, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_readiness_config(args.config)
    if args.seed is not None:
        config.setdefault("run", {})["seed"] = args.seed
    result = write_group_outputs(config)
    write_json(
        "artifacts/groups/group_audit_manifest.json",
        {
            "n_subjects": len(result["rows"]),
            "n_groups": len(result["summaries"]),
            "config_path": config.get("_config_path", ""),
            "seed": config.get("run", {}).get("seed"),
            "environment": environment_snapshot(),
        },
    )


if __name__ == "__main__":
    main()
