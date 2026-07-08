#!/usr/bin/env python3
"""Run Goal 2.6 fNIRS fixed-CV models."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from chongqing_binary.goal2_6.runner import run_goal2_6


if __name__ == "__main__":
    print(json.dumps(run_goal2_6(["fnirs"]), ensure_ascii=False))
