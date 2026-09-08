#!/usr/bin/env python3
"""Build subject-level behavioural features from the paradigm trial logs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from chongqing_binary.goal2_9.behaviour import extract_behaviour_features  # noqa: E402
from chongqing_binary.paradigm import load_paradigm_spec  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", default="all", choices=["all", "yiruid", "bikom"])
    parser.add_argument("--task", default="all")
    parser.add_argument("--config", default="configs/goal2_9/behaviour.yaml")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--n-jobs", type=int, default=None)
    args = parser.parse_args()

    spec = load_paradigm_spec()
    units = [
        (device, task) for device, task in spec.behaviour_units()
        if args.device in ("all", device) and args.task in ("all", task)
    ]
    if not units:
        parser.error(f"no behavioural unit matches device={args.device} task={args.task}")

    for device, task in units:
        manifest = extract_behaviour_features(device, task, args.config,
                                              limit=args.limit, n_jobs=args.n_jobs, spec=spec)
        print(json.dumps(manifest, ensure_ascii=False, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
