#!/usr/bin/env python3
"""Re-derive EEG epochs from raw BDF using the paradigm specification.

Replaces the v1 window cache, whose hardcoded `event_codes: ["22"]` removed the
Oddball standard condition and made target/standard ERP look impossible.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from chongqing_binary.goal2_8.eeg_epochs import build_task_epochs  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", default="oddball", choices=["oddball", "1back", "rest"])
    parser.add_argument("--config", default="configs/goal2_8/eeg.yaml")
    parser.add_argument("--limit", type=int, default=None, help="cap subjects, for smoke runs")
    parser.add_argument("--n-jobs", type=int, default=None)
    args = parser.parse_args()

    summary = build_task_epochs(args.task, args.config, limit=args.limit, n_jobs=args.n_jobs)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["subjects_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
