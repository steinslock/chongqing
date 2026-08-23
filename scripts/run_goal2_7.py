#!/usr/bin/env python3
"""Run Goal 2.7 fixed-CV and group-aware models."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from chongqing_binary.goal2_7.runner import run_goal2_7, write_supplemental_outputs


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/goal2_7/models.yaml")
    parser.add_argument("--modalities", nargs="*", default=None)
    parser.add_argument("--skip-supplemental", action="store_true", help="Write OOF/main metric outputs only; skip bootstrap and paired tables.")
    parser.add_argument("--supplemental-only", action="store_true", help="Compute bootstrap and paired tables from existing OOF predictions.")
    args = parser.parse_args()
    if args.supplemental_only:
        print(json.dumps(write_supplemental_outputs(args.config), ensure_ascii=False))
    else:
        print(json.dumps(run_goal2_7(args.modalities, args.config, include_supplemental=not args.skip_supplemental), ensure_ascii=False))


if __name__ == "__main__":
    main()
