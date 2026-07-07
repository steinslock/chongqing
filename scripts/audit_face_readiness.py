#!/usr/bin/env python3
"""Audit Face video availability and run a CV-pool visual smoke test."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from chongqing_binary.face.detection import detect_faces
from chongqing_binary.face.features import simple_frozen_embedding, temporal_forward_shape
from chongqing_binary.face.index import collect_videos, write_video_availability
from chongqing_binary.face.sampling import sample_frames
from chongqing_binary.readiness import ensure_output_path, environment_snapshot, load_readiness_config, raw_data_dir, text_table, write_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/readiness/face_smoke.yaml")
    parser.add_argument("--smoke-limit", type=int, default=None)
    parser.add_argument("--seed", type=int, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_readiness_config(args.config)
    if args.seed is not None:
        config.setdefault("run", {})["seed"] = args.seed
    if args.smoke_limit is not None:
        config.setdefault("run", {})["smoke_limit_per_class"] = args.smoke_limit
    outputs = write_video_availability(config)
    write_face_entry_report(outputs)
    write_shortcut_plan()
    smoke = run_smoke(config, outputs)
    write_json("artifacts/face/smoke/smoke_metrics.json", smoke)
    ensure_output_path("reports/face_smoke_report.md").write_text(smoke_report(smoke), encoding="utf-8")


def run_smoke(config: dict, outputs: dict) -> dict:
    limit = int(config.get("run", {}).get("smoke_limit_per_class", 2))
    n_frames = int(config.get("face", {}).get("smoke_sample_frames", 4))
    raw = raw_data_dir(config)
    file_maps = {
        name: collect_videos(raw / task_cfg["raw_dir"])
        for name, task_cfg in config["face"]["tasks"].items()
    }
    checks = []
    for task, rows in outputs.items():
        selected = []
        for label in ("0", "1"):
            group = [
                row
                for row in rows
                if row.get("split_group") == "cv"
                and row.get("primary_label_nonhealthy") == label
                and str(row.get("file_readable")) == "1"
            ][:limit]
            selected.extend(group)
        for row in selected:
            path = (file_maps.get(task, {}).get(row["L_id"]) or [None])[0]
            frames = sample_frames(path, n_frames) if path else []
            detections = [detect_faces(frame) for frame in frames]
            embeddings = [simple_frozen_embedding(frame) for frame in frames]
            embeddings = [emb for emb in embeddings if emb]
            checks.append(
                {
                    "video_task": task,
                    "L_id": row["L_id"],
                    "label": row["primary_label_nonhealthy"],
                    "split_group": row["split_group"],
                    "frames_decoded": len(frames),
                    "face_detection_attempted": bool(frames),
                    "frames_with_face": sum(1 for boxes in detections if boxes),
                    "embedding_shape": temporal_forward_shape(embeddings),
                    "mean_pool_shape": [len(embeddings[0])] if embeddings else [],
                    "lightweight_temporal_forward_shape": [1, len(embeddings[0])] if embeddings else [],
                }
            )
    passed = bool(checks) and all(item["split_group"] == "cv" for item in checks) and any(item["frames_decoded"] for item in checks)
    return {
        "stage": "Goal 2.5 Face smoke",
        "pilot_holdout_used": False,
        "formal_training": False,
        "config": {"path": config.get("_config_path", ""), "seed": int(config.get("run", {}).get("seed", 20260707))},
        "visual_only_no_audio": True,
        "checks": checks,
        "environment": environment_snapshot(),
        "passed": passed,
        "failure_reason": "" if passed else "no_decodable_cv_pool_face_videos",
    }


def write_face_entry_report(outputs: dict) -> None:
    lines = ["# Face Data Entry Audit", "", "Each Face table inherits `subject_splits_v1.csv`; one row per `L_id` and video task."]
    for task, rows in outputs.items():
        stats = {
            "rows": len(rows),
            "file_exists": sum(1 for row in rows if _one(row.get("file_exists"))),
            "file_readable": sum(1 for row in rows if _one(row.get("file_readable"))),
            "qc_pass": sum(1 for row in rows if _one(row.get("qc_pass"))),
            "duplicate_l_id_files": sum(1 for row in rows if int(row.get("file_count") or 0) > 1),
        }
        lines.extend(["", f"## {task}", "", text_table(stats)])
    lines.extend(
        [
            "",
            "## Checks",
            "",
            "- Same `L_id` fold consistency is inherited from the global split table.",
            "- Duplicate `L_id` video files are counted by task.",
            "- Full frame-by-frame corruption and face-detection audit is not run at full scale in Goal 2.5; smoke tests validate that the path is executable on CV-pool samples.",
            "- Codec/resolution/fps are retained as shortcut-risk variables and must be tested before formal Face modeling.",
        ]
    )
    ensure_output_path("reports/face_data_entry_audit.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_shortcut_plan() -> None:
    text = """# Face Shortcut Audit Plan

Goal 5 must treat video background, device, codec, resolution, frame rate, and quality as possible shortcuts. All clips from the same `L_id` and source video inherit the same global fold.

## Required Future Experiments

1. face crop only
2. aligned face crop
3. full frame
4. background blurred
5. background masked
6. face masked background-only
7. QC-only
8. codec/resolution/fps-only
9. demographics-only
10. Face+demographics
11. self-introduction video only
12. task video only
13. two-video fusion

## Interpretation Rules

- Background-only or codec-only performance near face-crop performance indicates shortcut risk.
- Full-frame performance that exceeds face-crop while background-masked drops suggests background or acquisition-batch leakage.
- Stable face-crop/aligned-crop signal with weak background-only/QC-only baselines is stronger evidence for face dynamics.
- Two-video fusion should aggregate subject-level predictions only after both videos are processed within the same fold.
"""
    ensure_output_path("reports/face_shortcut_audit_plan.md").write_text(text, encoding="utf-8")


def smoke_report(smoke: dict) -> str:
    return "\n".join(
        [
            "# Face Smoke Report",
            "",
            f"- Passed: `{smoke['passed']}`",
            "- Formal training: `False`",
            "- Pilot holdout used: `False`",
            "- Visual only, no audio: `True`",
            f"- Smoke checks: {len(smoke['checks'])}",
            f"- Failure reason: `{smoke.get('failure_reason','')}`",
            f"- First check: `{json.dumps(smoke['checks'][0] if smoke['checks'] else {}, ensure_ascii=False)}`",
        ]
    ) + "\n"


def _one(value: object) -> bool:
    return str(value) in {"1", "true", "True"}


if __name__ == "__main__":
    main()
