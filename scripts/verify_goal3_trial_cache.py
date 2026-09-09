#!/usr/bin/env python
"""Goal 3 measurement gate.

Two layers. First, numerical identity: averaging the single-trial cache by
condition must reproduce `artifacts/goal2_8/eeg/oddball_erp.npz` over the same
subjects to within a float32 epsilon, which proves the trials are the Goal 2.8
epochs rather than a similar-looking re-derivation. The criterion is relative
because Goal 2.8 stored float32, so the residual scales with the amplitude of
the recording. Second, the paradigm effect recomputed
from the trials: parietal maximum, Fz negative, Pz P3b with Cohen d above 0.8.

A failure stops Goal 3. It is not worked around.
"""

from __future__ import annotations

import argparse
import json
import sys

from chongqing_binary.goal3.trials import verify_cache


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/goal3/common.yaml")
    parser.add_argument("--relative-tolerance", type=float, default=4e-7,
                        help="max |difference| / max |reference|, in float32 epsilons")
    args = parser.parse_args()
    report = verify_cache(args.config, relative_tolerance=args.relative_tolerance)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if not report["gate_passed"]:
        print("\nGATE FAILED: Goal 3 must not proceed to modelling.", file=sys.stderr)
        raise SystemExit(1)
    print("\nGATE PASSED")


if __name__ == "__main__":
    main()
