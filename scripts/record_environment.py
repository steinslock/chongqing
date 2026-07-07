#!/usr/bin/env python3
"""Record Python, CUDA, PyTorch, and key dependency versions."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from chongqing_binary.config import load_config
from chongqing_binary.environment import write_environment_report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/default.yaml", help="YAML config path.")
    args = parser.parse_args()

    config = load_config(args.config)
    json_path, md_path = write_environment_report(config)
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

