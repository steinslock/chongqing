#!/usr/bin/env python3
"""Build subject-level EEG features from the Goal 2.8 ERP archive."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from chongqing_binary.goal2_8.eeg import extract_eeg_features  # noqa: E402
from chongqing_binary.goal2_8.eeg_rest import extract_rest_features  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", default="oddball", choices=["oddball", "1back", "rest"])
    parser.add_argument("--config", default="configs/goal2_8/eeg.yaml")
    parser.add_argument("--limit", type=int, default=None, help="cap subjects, rest only")
    parser.add_argument("--n-jobs", type=int, default=None, help="rest only")
    args = parser.parse_args()

    # Rest carries no events, so it uses the continuous spectral path.
    if args.task == "rest":
        summary = extract_rest_features(args.config, limit=args.limit, n_jobs=args.n_jobs)
    else:
        summary = extract_eeg_features(args.task, args.config)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
