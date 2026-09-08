#!/usr/bin/env python3
"""Run the Goal 2.8 model matrix over the re-derived features."""

from __future__ import annotations

import argparse
import os

# Cap OpenMP threads before sklearn is imported. HistGradientBoosting is
# OpenMP-backed and oversubscribes badly on a many-core host.
os.environ.setdefault("OMP_NUM_THREADS", "4")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "4")
os.environ.setdefault("MKL_NUM_THREADS", "4")

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from chongqing_binary.goal2_8.runner import run_goal2_8  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--modalities", nargs="*", default=None,
                        choices=["eeg", "fnirs", "face"])
    parser.add_argument("--config", default="configs/goal2_8/models.yaml")
    parser.add_argument("--n-workers", type=int, default=None,
                        help="datasets fitted concurrently")
    parser.add_argument("--skip-supplemental", action="store_true",
                        help="skip bootstrap CIs and paired tests")
    args = parser.parse_args()
    print(json.dumps(run_goal2_8(args.modalities, args.config,
                                 include_supplemental=not args.skip_supplemental,
                                 n_workers=args.n_workers),
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
