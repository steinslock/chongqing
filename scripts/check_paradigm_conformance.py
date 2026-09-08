#!/usr/bin/env python3
"""Check the Goal 2.8 paradigm specification against sampled raw recordings.

The specification records how each experiment was actually run, sourced from the
dataset attachments. This script opens real files and reports whether they
agree. Disagreements are reported, never silently coerced.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from chongqing_binary.paradigm.conformance import run_conformance  # noqa: E402
from chongqing_binary.paradigm.spec import load_paradigm_spec  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", default="configs/goal2_8/paradigm_spec.yaml")
    parser.add_argument("--subjects", type=int, default=25, help="subjects sampled per task")
    parser.add_argument("--out", default="artifacts/goal2_8/paradigm_conformance.csv")
    args = parser.parse_args()

    spec = load_paradigm_spec(args.spec)
    rows = run_conformance(args.spec, n_subjects=args.subjects)
    frame = pd.DataFrame(rows, columns=["modality", "device", "task", "check", "expected", "observed", "status", "n_subjects"])

    out_path = PROJECT_ROOT / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(out_path, index=False)

    width = {c: max(len(c), int(frame[c].astype(str).str.len().max())) for c in frame.columns}
    print(f"Paradigm spec: {spec.version}  ({spec.path})")
    print(f"Sampled up to {args.subjects} subjects per task\n")
    header = "  ".join(c.ljust(width[c]) for c in frame.columns)
    print(header)
    print("-" * len(header))
    for _, row in frame.iterrows():
        print("  ".join(str(row[c]).ljust(width[c]) for c in frame.columns))

    counts = frame["status"].value_counts().to_dict()
    print(f"\nsummary: {counts}")
    print(f"written: {out_path}")
    return 1 if counts.get("FAIL") else 0


if __name__ == "__main__":
    raise SystemExit(main())
