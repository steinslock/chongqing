"""Build Face video readiness tables."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..readiness import base_subject_fields, extract_l_ids, path_hash, raw_data_dir, split_rows, write_csv
from .io import probe_video
from .qc import minimum_qc_pass


def collect_videos(task_root: Path) -> dict[str, list[Path]]:
    found: dict[str, list[Path]] = {}
    if not task_root.exists():
        return found
    for path in sorted(task_root.glob("*.mp4")):
        ids = extract_l_ids(path.stem)
        if ids:
            found.setdefault(ids[0], []).append(path)
    return found


def build_video_availability(config: Mapping[str, Any], task: str) -> list[dict[str, Any]]:
    task_cfg = config["face"]["tasks"][task]
    task_root = raw_data_dir(config) / task_cfg["raw_dir"]
    files = collect_videos(task_root)
    unique_paths = sorted({path for paths in files.values() for path in paths})
    meta_by_path = _probe_many(unique_paths)
    min_duration = float(task_cfg.get("expected_min_duration_seconds", 30))
    run_face_detection = int(config.get("face", {}).get("full_audit_sample_frames", 0)) > 0
    rows: list[dict[str, Any]] = []
    for split_row in split_rows(config):
        l_id = split_row["L_id"]
        row = base_subject_fields(split_row)
        row.update({"video_task": task_cfg.get("label", task)})
        paths = files.get(l_id, [])
        path = paths[0] if paths else None
        meta = meta_by_path.get(path) if path else probe_video("__missing__")
        qc_pass, reason = minimum_qc_pass(meta, min_duration)
        row.update(
            {
                "file_exists": int(bool(path)),
                "file_readable": int(meta.readable),
                "file_count": len(paths),
                "video_file_hash": path_hash(path) if path else "",
                "codec": meta.codec,
                "container_format": meta.container,
                "duration_sec": meta.duration_sec,
                "resolution": f"{meta.width}x{meta.height}" if meta.width and meta.height else "",
                "width": meta.width,
                "height": meta.height,
                "fps": meta.fps,
                "frame_count": meta.frame_count,
                "full_decode_success": "",
                "corrupt_frame_count": "",
                "sampled_frame_count": 0,
                "audio_track_exists": "",
                "face_detection_success_rate": "" if not run_face_detection else "",
                "no_face_frame_rate": "" if not run_face_detection else "",
                "single_face_frame_rate": "" if not run_face_detection else "",
                "multi_face_frame_rate": "" if not run_face_detection else "",
                "mean_face_box_area": "" if not run_face_detection else "",
                "std_face_box_area": "" if not run_face_detection else "",
                "mean_blurriness": "",
                "mean_brightness": "",
                "brightness_std": "",
                "head_pose_proxy": "",
                "occlusion_proxy": "",
                "still_frame_rate": "",
                "qc_pass": int(qc_pass),
                "failure_reason": reason,
                "face_detection_full_audit": int(run_face_detection),
            }
        )
        if not path:
            row["failure_reason"] = "video_file_missing"
        rows.append(row)
    return rows


def _probe_many(paths: list[Path]) -> dict[Path, Any]:
    out: dict[Path, Any] = {}
    if not paths:
        return out
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(probe_video, path): path for path in paths}
        for future in as_completed(futures):
            path = futures[future]
            try:
                out[path] = future.result()
            except Exception:
                out[path] = probe_video("__missing__")
    return out


def write_video_availability(config: Mapping[str, Any]) -> dict[str, list[dict[str, Any]]]:
    outputs: dict[str, list[dict[str, Any]]] = {}
    for task in ("self_intro", "task"):
        rows = build_video_availability(config, task)
        write_csv(config["face"]["tasks"][task]["output_csv"], rows)
        outputs[task] = rows
    return outputs
