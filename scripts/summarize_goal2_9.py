#!/usr/bin/env python3
"""Build the Goal 2.9 reports from the model matrix outputs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from chongqing_binary.goal2_9.report import build_reports  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/goal2_9/models.yaml")
    args = parser.parse_args()
    print(json.dumps(build_reports(args.config), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
