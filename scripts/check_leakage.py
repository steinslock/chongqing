#!/usr/bin/env python3
"""Validate configured feature columns against the leakage guard."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from chongqing_binary.config import load_config
from chongqing_binary.leakage import validate_feature_columns


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/smoke.yaml", help="YAML config path.")
    args = parser.parse_args()

    config = load_config(args.config)
    validate_feature_columns(
        config.smoke_feature_columns,
        exact=config.forbidden_feature_exact,
        patterns=config.forbidden_feature_patterns,
    )
    print("Leakage guard passed for configured smoke feature columns.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

