#!/usr/bin/env python
"""Summarise Goal 3: pooled metrics, bootstrap intervals, paired increments, decision."""

from __future__ import annotations

import argparse
import json

from chongqing_binary.goal3.report import summarise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/goal3/common.yaml")
    args = parser.parse_args()
    print(json.dumps(summarise(args.config), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
