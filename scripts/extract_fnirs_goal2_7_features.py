#!/usr/bin/env python3
"""Extract Goal 2.7 fNIRS full-read event-audited features."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from chongqing_binary.goal2_7.fnirs import extract_fnirs_features


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/goal2_7/fnirs.yaml")
    args = parser.parse_args()
    manifest = extract_fnirs_features(args.config)
    print(json.dumps(manifest, ensure_ascii=False))


if __name__ == "__main__":
    main()
