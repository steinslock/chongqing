#!/usr/bin/env python
"""Rebuild the Goal 2.8 Oddball epochs and keep the single trials.

Goal 2.8 kept only the condition averages. Goal 3 needs the trials, so this
re-runs the same epoching from raw BDF under the same configuration. Run
`verify_goal3_trial_cache.py` afterwards: the cache is only usable if averaging
it by condition reproduces the Goal 2.8 evoked arrays.
"""

from __future__ import annotations

import argparse
import json

from chongqing_binary.goal3.trials import build_trial_cache


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/goal3/common.yaml")
    parser.add_argument("--n-jobs", type=int, default=32)
    parser.add_argument("--limit", type=int, default=None, help="smoke-test subject cap")
    args = parser.parse_args()
    manifest = build_trial_cache(args.config, limit=args.limit, n_jobs=args.n_jobs)
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
