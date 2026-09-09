#!/usr/bin/env python3
"""Build subject-level eye-tracking features for Goal 2.10.

Consumes the readiness audit's deduplicated recording table, so discovery,
`A_id` resolution and QC are not repeated here and both stages see the same
take of every recording. Run `scripts/audit_eye_readiness.py` first.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from chongqing_binary.eye.extract import extract_unit  # noqa: E402
from chongqing_binary.eye.spec import load_eye_spec  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", default="all")
    parser.add_argument("--task", default="all")
    parser.add_argument("--config", default="configs/goal2_10/features.yaml")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--n-jobs", type=int, default=None)
    args = parser.parse_args()

    spec = load_eye_spec()
    units = [
        (device, task)
        for device in spec.devices
        for task in spec.tasks
        if args.device in ("all", device) and args.task in ("all", task)
    ]
    if not units:
        parser.error(f"no eye unit matches device={args.device} task={args.task}")

    for device, task in units:
        manifest = extract_unit(device, task, args.config, limit=args.limit, n_jobs=args.n_jobs, spec=spec)
        print(json.dumps(manifest, ensure_ascii=False, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
