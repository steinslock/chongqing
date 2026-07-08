"""Face Goal 2.6 frozen visual embeddings and QC."""

from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

import cv2  # type: ignore
import numpy as np
import pandas as pd
import torch
from PIL import Image, ImageDraw
from torchvision.models import ResNet18_Weights, resnet18

from .config import ensure_output, load_goal_config, project_path
from .io import cv_subjects
from .stats import clean_name

L_ID_RE = re.compile(r"(?<![A-Za-z0-9])L\d+(?![A-Za-z0-9])", re.IGNORECASE)


def extract_face_features(config_path: str | Path = "configs/goal2_6/face.yaml") -> dict[str, Any]:
    config = load_goal_config(config_path)
    split = cv_subjects(config)
    cv_lids = set(split["L_id"].astype(str))
    raw_root = project_path(config["paths"]["raw_data_dir"])
    model, device = _load_encoder()
    detector = _load_haar_detector()
    manifest: dict[str, Any] = {
        "config": str(project_path(config_path)),
        "encoder": dict(config["face"]["encoder"], device=str(device)),
        "detector": config["face"]["detector"],
        "tasks": {},
    }
    contact_images: list[Image.Image] = []
    for task, spec in config["face"]["tasks"].items():
        videos = _collect_videos(raw_root / spec["raw_dir"])
        availability = pd.read_csv(project_path(spec["availability_csv"]), dtype={"L_id": str})
        availability = availability[availability["L_id"].isin(cv_lids)].copy()
        rows_signal: list[dict[str, Any]] = []
        rows_qc: list[dict[str, Any]] = []
        signal_part = ensure_output(str(spec["signal_features"]).replace(".csv", ".part.csv"), config)
        qc_part = ensure_output(str(spec["qc_features"]).replace(".csv", ".part.csv"), config)
        processed: set[str] = set()
        if signal_part.exists() and qc_part.exists():
            old_signal = pd.read_csv(signal_part, dtype={"L_id": str})
            old_qc = pd.read_csv(qc_part, dtype={"L_id": str})
            rows_signal.extend(old_signal.to_dict(orient="records"))
            rows_qc.extend(old_qc.to_dict(orient="records"))
            processed = set(old_qc["L_id"].astype(str))
        checkpoint_every = int(config["face"].get("checkpoint_every_videos", 100))
        for index, (_, avail) in enumerate(availability.sort_values("L_id").iterrows(), start=1):
            l_id = str(avail["L_id"])
            if l_id in processed:
                continue
            path = videos.get(l_id)
            if path is None:
                rows_qc.append(_blocked_qc(l_id, task, "video_file_missing", config, avail))
                continue
            signal, qc, samples = _process_video(l_id, task, path, avail, model, device, detector, config)
            if signal:
                rows_signal.append(signal)
            rows_qc.append(qc)
            if len(contact_images) < 100:
                contact_images.extend(samples[: max(0, 100 - len(contact_images))])
            if checkpoint_every > 0 and index % checkpoint_every == 0:
                pd.DataFrame(rows_signal).to_csv(signal_part, index=False)
                pd.DataFrame(rows_qc).to_csv(qc_part, index=False)
        signal_df = _attach_split(pd.DataFrame(rows_signal), split, config)
        qc_df = _attach_split(pd.DataFrame(rows_qc), split, config)
        signal_path = ensure_output(spec["signal_features"], config)
        qc_path = ensure_output(spec["qc_features"], config)
        signal_df.to_csv(signal_path, index=False)
        qc_df.to_csv(qc_path, index=False)
        pd.DataFrame(rows_signal).to_csv(signal_part, index=False)
        pd.DataFrame(rows_qc).to_csv(qc_part, index=False)
        manifest["tasks"][task] = {
            "signal_features": str(signal_path),
            "qc_features": str(qc_path),
            "subjects_signal": int(len(signal_df)),
            "subjects_qc": int(len(qc_df)),
            "sample_frames": int(config["face"]["sample_frames"]),
        }
    _write_contact_sheet(contact_images, ensure_output(config["face"]["outputs"]["contact_sheet"], config))
    manifest_path = ensure_output(config["face"]["outputs"]["manifest"], config)
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest


def _process_video(
    l_id: str,
    task: str,
    path: Path,
    availability: pd.Series,
    model: torch.nn.Module,
    device: torch.device,
    detector: cv2.CascadeClassifier,
    config: dict[str, Any],
) -> tuple[dict[str, Any] | None, dict[str, Any], list[Image.Image]]:
    frames, decode_success = _sample_frames(path, int(config["face"]["sample_frames"]))
    if not frames:
        return None, _blocked_qc(l_id, task, "no_decodable_sampled_frames", config, availability), []
    variants: dict[str, list[np.ndarray]] = {"full": [], "face": [], "background": []}
    face_counts: list[int] = []
    face_areas: list[float] = []
    blur_scores: list[float] = []
    brightness: list[float] = []
    static_scores: list[float] = []
    contact: list[Image.Image] = []
    previous_gray: np.ndarray | None = None
    for frame in frames:
        h, w = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        boxes = _detect_faces(detector, gray)
        face_counts.append(len(boxes))
        box = _largest_box(boxes)
        if box is not None:
            x, y, bw, bh = _expand_box(box, w, h, scale=1.35)
            crop = frame[y : y + bh, x : x + bw].copy()
            background = frame.copy()
            background[y : y + bh, x : x + bw] = 0
            face_areas.append((bw * bh) / max(float(w * h), 1.0))
            if len(contact) < 2:
                contact.append(_annotated_image(frame, (x, y, bw, bh), l_id, task))
        else:
            crop = _center_crop(frame)
            background = frame.copy()
            face_areas.append(0.0)
        variants["full"].append(frame)
        variants["face"].append(crop)
        variants["background"].append(background)
        blur_scores.append(float(cv2.Laplacian(gray, cv2.CV_64F).var()))
        brightness.append(float(np.mean(gray)))
        if previous_gray is not None:
            resized = cv2.resize(gray, (64, 64))
            prev = cv2.resize(previous_gray, (64, 64))
            static_scores.append(float(np.mean(np.abs(resized.astype(float) - prev.astype(float))) < 1.0))
        previous_gray = gray
    all_frames = variants["full"] + variants["face"] + variants["background"]
    all_embeddings = _embed_frames(all_frames, model, device, int(config["face"]["batch_size"]), int(config["face"]["input_size"]))
    n = len(variants["full"])
    embeddings: dict[str, np.ndarray] = {
        "full": all_embeddings[:n],
        "face": all_embeddings[n : 2 * n],
        "background": all_embeddings[2 * n : 3 * n],
    }
    signal = {
        "L_id": l_id,
        "modality": "face",
        "device": "",
        "task": task,
        "feature_version": config["face"]["feature_version"],
        "preprocessing_version": config["face"]["preprocessing_version"],
        "encoder_name": config["face"]["encoder"]["name"],
        "detector_name": config["face"]["detector"]["name"],
    }
    for name, emb in embeddings.items():
        signal.update(_embedding_pool(f"signal_{name}", emb))
    qc = {
        "L_id": l_id,
        "modality": "face",
        "device": "",
        "task": task,
        "feature_version": config["face"]["feature_version"],
        "preprocessing_version": config["face"]["preprocessing_version"],
        "qc_feature_status": "ok",
        "qc_failure_reason": "",
        "qc_decode_success_rate": float(decode_success),
        "qc_sampled_frame_count": int(len(frames)),
        "qc_face_detection_rate": float(np.mean(np.asarray(face_counts) > 0)),
        "qc_no_face_rate": float(np.mean(np.asarray(face_counts) == 0)),
        "qc_multi_face_rate": float(np.mean(np.asarray(face_counts) > 1)),
        "qc_average_face_area_ratio": float(np.mean(face_areas)),
        "qc_face_area_variability": float(np.std(face_areas)),
        "qc_blur_score_mean": float(np.mean(blur_scores)),
        "qc_brightness_mean": float(np.mean(brightness)),
        "qc_brightness_variation": float(np.std(brightness)),
        "qc_head_pose_proxy": float(np.std(face_areas)),
        "qc_occlusion_proxy": float(np.mean(np.asarray(face_areas) < 0.02)),
        "qc_static_frame_rate": float(np.mean(static_scores)) if static_scores else 0.0,
        "qc_resolution_width": _safe_num(availability.get("width")),
        "qc_resolution_height": _safe_num(availability.get("height")),
        "qc_fps": _safe_num(availability.get("fps")),
        "qc_duration_sec": _safe_num(availability.get("duration_sec")),
        "qc_aspect_ratio": _safe_num(availability.get("width")) / max(_safe_num(availability.get("height")), 1.0),
        "qc_codec": str(availability.get("codec", "")),
        "qc_detector_formal_status": "fallback_detector_not_retinaface_mtcnn_or_mediapipe",
        "qc_audio_used": 0,
    }
    return signal, qc, contact


def _load_encoder() -> tuple[torch.nn.Module, torch.device]:
    weights = ResNet18_Weights.DEFAULT
    model = resnet18(weights=weights)
    model.fc = torch.nn.Identity()
    model.eval()
    for param in model.parameters():
        param.requires_grad_(False)
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    model.to(device)
    return model, device


def _embed_frames(frames: list[np.ndarray], model: torch.nn.Module, device: torch.device, batch_size: int, input_size: int) -> np.ndarray:
    chunks: list[np.ndarray] = []
    with torch.no_grad():
        for start in range(0, len(frames), batch_size):
            batch = _preprocess_frames(frames[start : start + batch_size], input_size).to(device)
            out = model(batch).detach().cpu().numpy().astype(np.float32)
            chunks.append(out)
    return np.concatenate(chunks, axis=0) if chunks else np.empty((0, 512), dtype=np.float32)


def _preprocess_frames(frames: list[np.ndarray], input_size: int) -> torch.Tensor:
    arrays = []
    mean = np.asarray([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.asarray([0.229, 0.224, 0.225], dtype=np.float32)
    for frame in frames:
        resized = cv2.resize(frame, (input_size, input_size), interpolation=cv2.INTER_AREA)
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        rgb = (rgb - mean) / std
        arrays.append(np.transpose(rgb, (2, 0, 1)))
    return torch.from_numpy(np.stack(arrays).astype(np.float32))


def _embedding_pool(prefix: str, emb: np.ndarray) -> dict[str, float]:
    if emb.size == 0:
        return {}
    mean = np.mean(emb, axis=0)
    std = np.std(emb, axis=0)
    out: dict[str, float] = {}
    for idx, value in enumerate(mean):
        out[f"{prefix}_mean_{idx:03d}"] = float(value)
    for idx, value in enumerate(std):
        out[f"{prefix}_std_{idx:03d}"] = float(value)
    return out


def _sample_frames(path: Path, n_frames: int) -> tuple[list[np.ndarray], float]:
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        return [], 0.0
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    if frame_count <= 0:
        cap.release()
        return [], 0.0
    indices = np.linspace(0, max(frame_count - 1, 0), n_frames, dtype=int)
    frames: list[np.ndarray] = []
    attempts = 0
    for idx in indices:
        attempts += 1
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
        ok, frame = cap.read()
        if ok and frame is not None:
            frames.append(frame)
    cap.release()
    return frames, len(frames) / attempts if attempts else 0.0


def _load_haar_detector() -> cv2.CascadeClassifier:
    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    detector = cv2.CascadeClassifier(cascade_path)
    if detector.empty():
        raise RuntimeError("OpenCV Haar cascade could not be loaded.")
    return detector


def _detect_faces(detector: cv2.CascadeClassifier, gray: np.ndarray) -> list[tuple[int, int, int, int]]:
    height, width = gray.shape[:2]
    target_width = 320
    if width > target_width:
        scale = target_width / float(width)
        small = cv2.resize(gray, (target_width, max(1, int(round(height * scale)))), interpolation=cv2.INTER_AREA)
        boxes = detector.detectMultiScale(small, scaleFactor=1.1, minNeighbors=4, minSize=(18, 18))
        inv = 1.0 / scale
        return [(int(x * inv), int(y * inv), int(w * inv), int(h * inv)) for x, y, w, h in boxes]
    boxes = detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(32, 32))
    return [(int(x), int(y), int(w), int(h)) for x, y, w, h in boxes]


def _largest_box(boxes: list[tuple[int, int, int, int]]) -> tuple[int, int, int, int] | None:
    if not boxes:
        return None
    return max(boxes, key=lambda b: b[2] * b[3])


def _expand_box(box: tuple[int, int, int, int], width: int, height: int, scale: float) -> tuple[int, int, int, int]:
    x, y, w, h = box
    cx = x + w / 2.0
    cy = y + h / 2.0
    size = max(w, h) * scale
    nx = max(0, int(round(cx - size / 2.0)))
    ny = max(0, int(round(cy - size / 2.0)))
    nw = min(width - nx, int(round(size)))
    nh = min(height - ny, int(round(size)))
    return nx, ny, max(1, nw), max(1, nh)


def _center_crop(frame: np.ndarray) -> np.ndarray:
    h, w = frame.shape[:2]
    size = min(h, w)
    y = (h - size) // 2
    x = (w - size) // 2
    return frame[y : y + size, x : x + size].copy()


def _to_pil(frame_bgr: np.ndarray) -> Image.Image:
    rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    return Image.fromarray(rgb)


def _annotated_image(frame_bgr: np.ndarray, box: tuple[int, int, int, int], l_id: str, task: str) -> Image.Image:
    image = _to_pil(cv2.resize(frame_bgr, (240, 135)))
    draw = ImageDraw.Draw(image)
    x, y, w, h = box
    sx = 240 / frame_bgr.shape[1]
    sy = 135 / frame_bgr.shape[0]
    draw.rectangle([x * sx, y * sy, (x + w) * sx, (y + h) * sy], outline="red", width=2)
    draw.text((4, 4), f"{clean_name(l_id)} {task}", fill="yellow")
    return image


def _write_contact_sheet(images: list[Image.Image], path: Path) -> None:
    if not images:
        Image.new("RGB", (240, 135), "black").save(path)
        return
    cols = 10
    rows = int(math.ceil(len(images) / cols))
    w, h = images[0].size
    sheet = Image.new("RGB", (cols * w, rows * h), "white")
    for idx, image in enumerate(images):
        sheet.paste(image, ((idx % cols) * w, (idx // cols) * h))
    sheet.save(path, quality=90)


def _collect_videos(task_dir: Path) -> dict[str, Path]:
    out: dict[str, Path] = {}
    if not task_dir.exists():
        return out
    for path in sorted(task_dir.glob("*.mp4")):
        l_id = _extract_l_id(path.stem)
        if l_id and l_id not in out:
            out[l_id] = path
    return out


def _extract_l_id(text: str) -> str:
    match = L_ID_RE.search(text)
    return match.group(0).upper() if match else ""


def _attach_split(frame: pd.DataFrame, split: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
    if frame.empty:
        return frame
    label_col = config.get("run", {}).get("label_column", "primary_label_nonhealthy")
    keep = [
        "L_id",
        "A_id",
        label_col,
        "split_group",
        "split_role",
        "is_locked_test",
        "cv_fold",
        "sex",
        "age",
        "grade",
        "grade_group",
        "fnirs_device",
    ]
    keep = [col for col in keep if col in split.columns]
    merged = split[keep].merge(frame, on="L_id", how="inner")
    if pd.to_numeric(merged.get("is_locked_test", 0), errors="coerce").fillna(0).astype(int).any():
        raise ValueError("Goal 2.6 Face features unexpectedly include pilot-holdout subjects.")
    return merged.sort_values("L_id").reset_index(drop=True)


def _blocked_qc(l_id: str, task: str, reason: str, config: dict[str, Any], availability: pd.Series | None = None) -> dict[str, Any]:
    availability = availability if availability is not None else pd.Series(dtype=object)
    return {
        "L_id": l_id,
        "modality": "face",
        "device": "",
        "task": task,
        "feature_version": config["face"]["feature_version"],
        "preprocessing_version": config["face"]["preprocessing_version"],
        "qc_feature_status": "blocked",
        "qc_failure_reason": reason,
        "qc_resolution_width": _safe_num(availability.get("width")),
        "qc_resolution_height": _safe_num(availability.get("height")),
        "qc_fps": _safe_num(availability.get("fps")),
        "qc_duration_sec": _safe_num(availability.get("duration_sec")),
        "qc_codec": str(availability.get("codec", "")),
        "qc_audio_used": 0,
    }


def _safe_num(value: object) -> float:
    try:
        out = float(value)  # type: ignore[arg-type]
    except Exception:
        return math.nan
    return out if math.isfinite(out) else math.nan
