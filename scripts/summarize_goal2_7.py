#!/usr/bin/env python3
"""Write Goal 2.7 markdown reports from result tables."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from chongqing_binary.goal2_7.report import write_goal2_7_reports


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/goal2_7/models.yaml")
    args = parser.parse_args()
    print(json.dumps(write_goal2_7_reports(args.config), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
