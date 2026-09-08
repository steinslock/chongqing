#!/usr/bin/env python3
"""Segment the Face task session and extract within-subject valence contrasts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from chongqing_binary.goal2_8.face import extract_face_features, merge_face_shards  # noqa: E402
from chongqing_binary.goal2_8.face_segments import build_segment_index  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", default="all", choices=["all", "index", "features", "merge"])
    parser.add_argument("--shard", type=int, default=0)
    parser.add_argument("--n-shards", type=int, default=1)
    parser.add_argument("--config", default="configs/goal2_8/face.yaml")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--n-jobs", type=int, default=None)
    args = parser.parse_args()

    if args.stage in ("all", "index"):
        print(json.dumps(build_segment_index(args.config, limit=args.limit, n_jobs=args.n_jobs),
                         ensure_ascii=False, indent=2), flush=True)
    if args.stage in ("all", "features"):
        print(json.dumps(extract_face_features(args.config, limit=args.limit,
                                               shard=args.shard, n_shards=args.n_shards),
                         ensure_ascii=False, indent=2), flush=True)
    if args.stage == "merge":
        print(json.dumps(merge_face_shards(args.config), ensure_ascii=False, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
