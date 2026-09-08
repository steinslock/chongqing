"""Segment-wise Face features and the within-subject valence contrast.

The valence contrast subtracts one segment's embedding from another's within the
same subject, which cancels identity, appearance, clothing and room background.
Those are exactly the shortcuts that dominated the Goal 2.7 Face result, so the
contrast is the primary feature here and the per-segment embeddings and
background variants are retained as controls.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ..paradigm import load_paradigm_spec
from ..paradigm.spec import ParadigmSpec
from .config import cv_subjects, ensure_output, load_goal_config, project_path


def _load_encoder(config: dict[str, Any]):
    import torch
    from torchvision.models import ResNet18_Weights, resnet18

    model = resnet18(weights=ResNet18_Weights.IMAGENET1K_V1)
    model.fc = torch.nn.Identity()
    model.eval()
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    return model.to(device), device


def _load_detector(config: dict[str, Any]):
    import cv2

    cfg = config["face"]["detector"]
    checkpoint = project_path(cfg["checkpoint"])
    if not checkpoint.exists():
        raise FileNotFoundError(f"YuNet checkpoint missing: {checkpoint}")
    detector = cv2.FaceDetectorYN_create(
        str(checkpoint), "", (320, 320),
        float(cfg["score_threshold"]), float(cfg["nms_threshold"]), int(cfg["top_k"]))
    return detector


def _sample_times(start: float, end: float, n: int, interior: float) -> list[float]:
    """Times inside the segment, avoiding the boundaries where alignment error lives."""
    span = end - start
    margin = span * (1.0 - interior) / 2.0
    lo, hi = start + margin, end - margin
    if hi <= lo:
        lo, hi = start, end
    return list(np.linspace(lo, hi, n))


def _largest_box(faces) -> tuple[int, int, int, int] | None:
    if faces is None or len(faces) == 0:
        return None
    best = max(faces, key=lambda f: float(f[2]) * float(f[3]))
    x, y, w, h = (int(round(float(v))) for v in best[:4])
    return x, y, w, h


def _expand(box: tuple[int, int, int, int], width: int, height: int,
            scale: float = 1.35) -> tuple[int, int, int, int]:
    x, y, w, h = box
    cx, cy = x + w / 2.0, y + h / 2.0
    nw, nh = w * scale, h * scale
    nx, ny = int(max(0, cx - nw / 2)), int(max(0, cy - nh / 2))
    return nx, ny, int(min(width - nx, nw)), int(min(height - ny, nh))


def _process_subject(l_id: str, video: Path, segments: dict[str, tuple[float, float]],
                     config: dict[str, Any], model, device, detector) -> tuple[dict[str, np.ndarray] | None, dict[str, Any]]:
    import cv2
    import torch

    face_cfg = config["face"]
    n_frames = int(face_cfg["frames_per_segment"])
    interior = float(face_cfg["segment_interior_fraction"])
    size = int(face_cfg["input_size"])
    min_valid = int(face_cfg["min_valid_face_frames"])

    qc: dict[str, Any] = {"L_id": l_id, "modality": "face", "qc_feature_status": "blocked",
                          "qc_failure_reason": "", "qc_detector": "opencv_yunet"}
    capture = cv2.VideoCapture(str(video))
    if not capture.isOpened():
        qc["qc_failure_reason"] = "video_unreadable"
        return None, qc

    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)

    def embed(images: list[np.ndarray]) -> np.ndarray:
        if not images:
            return np.zeros((0, 512), dtype=np.float32)
        batch = np.stack([
            (cv2.cvtColor(cv2.resize(im, (size, size)), cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0 - mean) / std
            for im in images
        ]).transpose(0, 3, 1, 2)
        with torch.no_grad():
            out = model(torch.from_numpy(batch).to(device))
        return out.cpu().numpy().astype(np.float32)

    per_segment: dict[str, dict[str, np.ndarray]] = {}
    detection_rates: dict[str, float] = {}
    try:
        for name, (start, end) in segments.items():
            faces_imgs: list[np.ndarray] = []
            backgrounds: list[np.ndarray] = []
            fulls: list[np.ndarray] = []
            detected = 0
            times = _sample_times(start, end, n_frames, interior)
            for t in times:
                capture.set(cv2.CAP_PROP_POS_MSEC, max(0.0, t) * 1000.0)
                ok, frame = capture.read()
                if not ok or frame is None:
                    continue
                height, width = frame.shape[:2]
                fulls.append(frame)
                detector.setInputSize((width, height))
                _, faces = detector.detect(frame)
                box = _largest_box(faces)
                if box is None:
                    continue
                detected += 1
                x, y, w, h = _expand(box, width, height)
                if w <= 0 or h <= 0:
                    continue
                faces_imgs.append(frame[y:y + h, x:x + w].copy())
                masked = frame.copy()
                masked[y:y + h, x:x + w] = 0
                backgrounds.append(masked)
            detection_rates[name] = detected / max(1, len(times))
            if len(faces_imgs) < min_valid:
                continue
            per_segment[name] = {
                "face": embed(faces_imgs).mean(axis=0),
                "background": embed(backgrounds).mean(axis=0),
                "full": embed(fulls).mean(axis=0),
                "n_face_frames": np.array([len(faces_imgs)], dtype=np.float32),
            }
    finally:
        capture.release()

    if not per_segment:
        qc["qc_failure_reason"] = "no_segment_reached_min_valid_faces"
        qc["qc_mean_detection_rate"] = float(np.mean(list(detection_rates.values()) or [0.0]))
        return None, qc

    qc.update({
        "qc_feature_status": "ok", "qc_failure_reason": "",
        "qc_segments_valid": len(per_segment),
        "qc_mean_detection_rate": float(np.mean(list(detection_rates.values()))),
        "qc_min_detection_rate": float(np.min(list(detection_rates.values()))),
        "qc_face_frames_total": int(sum(int(v["n_face_frames"][0]) for v in per_segment.values())),
        "qc_detector_fallback_used": 0,
    })
    for name, rate in detection_rates.items():
        qc[f"qc_detection_rate_{name}"] = float(rate)
    return per_segment, qc


def extract_face_features(config_path: str | Path = "configs/goal2_8/face.yaml",
                          limit: int | None = None, spec: ParadigmSpec | None = None,
                          shard: int = 0, n_shards: int = 1) -> dict[str, Any]:
    config = load_goal_config(config_path)
    spec = spec or load_paradigm_spec(config["paths"]["paradigm_spec"])
    face_cfg = config["face"]
    order = spec.face["task"]["movie_order"]
    pairs = [tuple(p) for p in spec.face["task"]["primary_contrast"]["pairs"]]

    out_dir = Path(ensure_output(f"{face_cfg['outputs_dir']}/.keep", config)).parent
    index = pd.read_csv(out_dir / "segment_index.csv", dtype={"L_id": str, "A_id": str})
    raw_root = project_path(config["paths"]["raw_data_dir"])
    video_dir = raw_root / spec.face["task"]["dir"]

    usable = index[[f"{n}_start_sec" for n in order]].notna().all(axis=1)
    index = index[usable].sort_values("L_id").reset_index(drop=True)
    if limit:
        index = index.head(limit)
    # Video decoding dominates the cost, so the work is sharded across processes.
    if n_shards > 1:
        index = index.iloc[shard::n_shards].copy()
    suffix = "" if n_shards == 1 else f"_shard{shard:02d}"

    model, device = _load_encoder(config)
    detector = _load_detector(config)

    l_ids: list[str] = []
    stacks: dict[str, list[np.ndarray]] = {}
    qc_rows: list[dict[str, Any]] = []
    for row in index.itertuples():
        segments = {n: (float(getattr(row, f"{n}_start_sec")), float(getattr(row, f"{n}_end_sec")))
                    for n in order}
        result, qc = _process_subject(str(row.L_id), video_dir / f"{row.L_id}.mp4",
                                      segments, config, model, device, detector)
        qc_rows.append(qc)
        if result is None or len(result) < len(order):
            continue
        l_ids.append(str(row.L_id))
        for name in order:
            for variant in ("face", "background", "full"):
                stacks.setdefault(f"{variant}_{name}", []).append(result[name][variant])
        # The within-subject contrast: identity and background cancel.
        for minuend, subtrahend in pairs:
            key = f"contrast_{minuend}_minus_{subtrahend}"
            stacks.setdefault(key, []).append(result[minuend]["face"] - result[subtrahend]["face"])
            stacks.setdefault(key + "_background", []).append(
                result[minuend]["background"] - result[subtrahend]["background"])

    archive = out_dir / f"face_segment_embeddings{suffix}.npz"
    if l_ids:
        np.savez_compressed(archive, l_ids=np.array(l_ids),
                            **{k: np.stack(v) for k, v in stacks.items()})

    qc_frame = pd.DataFrame(qc_rows)
    split = cv_subjects(config)
    keep = [c for c in ["L_id", "A_id", "primary_label_nonhealthy", "split_group", "split_role",
                        "is_locked_test", "cv_fold", "sex", "age", "grade", "grade_group"]
            if c in split.columns]
    qc_out = split[keep].merge(qc_frame, on="L_id", how="inner").sort_values("L_id").reset_index(drop=True)
    if pd.to_numeric(qc_out.get("is_locked_test", 0), errors="coerce").fillna(0).astype(int).any():
        raise ValueError("Goal 2.8 Face QC includes pilot-holdout subjects.")
    qc_path = out_dir / f"face_qc_features{suffix}.csv"
    qc_out.to_csv(qc_path, index=False)

    manifest = {
        "shard": shard, "n_shards": n_shards,
        "feature_version": "goal2_8_face_segment_valence_v1",
        "preprocessing_version": face_cfg["preprocessing_version"],
        "encoder": face_cfg["encoder"]["name"],
        "detector": "opencv_yunet",
        "movie_order": order,
        "contrast_pairs": [list(p) for p in pairs],
        "frames_per_segment": int(face_cfg["frames_per_segment"]),
        "subjects_attempted": int(len(index)),
        "subjects_with_all_segments": len(l_ids),
        "embedding_blocks": sorted(stacks),
        "embeddings_npz": str(archive) if l_ids else "",
        "qc_features": str(qc_path),
    }
    (out_dir / f"face_feature_manifest{suffix}.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest


def merge_face_shards(config_path: str | Path = "configs/goal2_8/face.yaml") -> dict[str, Any]:
    """Combine sharded outputs into one archive and one QC table."""
    config = load_goal_config(config_path)
    out_dir = Path(ensure_output(f"{config['face']['outputs_dir']}/.keep", config)).parent

    archives = sorted(out_dir.glob("face_segment_embeddings_shard*.npz"))
    qc_files = sorted(out_dir.glob("face_qc_features_shard*.csv"))
    if not archives:
        raise FileNotFoundError("no shard archives to merge")

    l_ids: list[str] = []
    blocks: dict[str, list[np.ndarray]] = {}
    for path in archives:
        data = np.load(path, allow_pickle=False)
        l_ids.extend(str(x) for x in data["l_ids"])
        for key in data.files:
            if key != "l_ids":
                blocks.setdefault(key, []).append(data[key])

    order = np.argsort(l_ids)
    merged = {k: np.concatenate(v)[order] for k, v in blocks.items()}
    archive = out_dir / "face_segment_embeddings.npz"
    np.savez_compressed(archive, l_ids=np.array(l_ids)[order], **merged)

    qc = pd.concat([pd.read_csv(f, dtype={"L_id": str, "A_id": str}) for f in qc_files],
                   ignore_index=True).sort_values("L_id").reset_index(drop=True)
    qc_path = out_dir / "face_qc_features.csv"
    qc.to_csv(qc_path, index=False)

    for path in archives + qc_files:
        path.unlink()
    for path in out_dir.glob("face_feature_manifest_shard*.json"):
        path.unlink()

    manifest = {
        "feature_version": "goal2_8_face_segment_valence_v1",
        "shards_merged": len(archives),
        "subjects_with_all_segments": len(l_ids),
        "subjects_qc": int(len(qc)),
        "qc_ok": int((qc["qc_feature_status"] == "ok").sum()),
        "embedding_blocks": sorted(merged),
        "embeddings_npz": str(archive),
        "qc_features": str(qc_path),
    }
    (out_dir / "face_feature_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest
