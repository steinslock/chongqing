"""Face Goal 2.7 strict frozen visual embeddings and QC."""

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


def extract_face_features(config_path: str | Path = "configs/goal2_7/face.yaml") -> dict[str, Any]:
    config = load_goal_config(config_path)
    split = cv_subjects(config)
    cv_lids = set(split["L_id"].astype(str))
    raw_root = project_path(config["paths"]["raw_data_dir"])
    model, device = _load_encoder()
    detector = _load_detector(config)
    manifest: dict[str, Any] = {
        "config": str(project_path(config_path)),
        "encoder": dict(config["face"]["encoder"], device=str(device)),
        "detector": config["face"]["detector"],
        "tasks": {},
    }
    contact_dir = ensure_output(config["face"]["outputs"]["contact_sheet_dir"] + "/.keep", config).parent
    contact_written = 0
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
            if contact_written < 200 and samples:
                _write_contact_sheet(samples, contact_dir / f"{task}_{clean_name(l_id)}.jpg")
                contact_written += 1
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
    manifest["contact_sheets_written"] = int(contact_written)
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
    detector: dict[str, Any],
    config: dict[str, Any],
) -> tuple[dict[str, Any] | None, dict[str, Any], list[Image.Image]]:
    frames, decode_success = _sample_frames(path, int(config["face"]["sample_frames"]))
    if not frames:
        return None, _blocked_qc(l_id, task, "no_decodable_sampled_frames", config, availability), []
    variants: dict[str, list[np.ndarray]] = {"full": [], "face": [], "background": [], "background_blur": []}
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
        detections = _detect_faces(detector, frame, gray)
        boxes = [det["box"] for det in detections]
        face_counts.append(len(boxes))
        det = _largest_detection(detections)
        box = det["box"] if det else None
        if box is not None:
            x, y, bw, bh = _expand_box(box, w, h, scale=1.35)
            crop = frame[y : y + bh, x : x + bw].copy()
            background = _mask_box(frame, (x, y, bw, bh))
            background_blur = _blur_box(frame, (x, y, bw, bh))
            face_areas.append((bw * bh) / max(float(w * h), 1.0))
            if len(contact) < 4:
                contact.extend(_contact_panels(frame, (x, y, bw, bh), crop, background, detector, det, l_id, task))
        else:
            face_areas.append(0.0)
        variants["full"].append(frame)
        if box is not None:
            variants["face"].append(crop)
            variants["background"].append(background)
            variants["background_blur"].append(background_blur)
        blur_scores.append(float(cv2.Laplacian(gray, cv2.CV_64F).var()))
        brightness.append(float(np.mean(gray)))
        if previous_gray is not None:
            resized = cv2.resize(gray, (64, 64))
            prev = cv2.resize(previous_gray, (64, 64))
            static_scores.append(float(np.mean(np.abs(resized.astype(float) - prev.astype(float))) < 1.0))
        previous_gray = gray
    min_valid = int(config["face"].get("min_valid_face_frames", 4))
    valid_face_frames = len(variants["face"])
    face_feature_blocked = valid_face_frames < min_valid
    all_frames = variants["full"] + variants["face"] + variants["background"] + variants["background_blur"]
    all_embeddings = _embed_frames(all_frames, model, device, int(config["face"]["batch_size"]), int(config["face"]["input_size"]))
    n = len(variants["full"])
    nf = len(variants["face"])
    embeddings: dict[str, np.ndarray] = {
        "full": all_embeddings[:n],
        "face": all_embeddings[n : n + nf],
        "background": all_embeddings[n + nf : n + 2 * nf],
        "background_blur": all_embeddings[n + 2 * nf : n + 3 * nf],
    }
    signal = {
        "L_id": l_id,
        "modality": "face",
        "device": "",
        "task": task,
        "feature_version": config["face"]["feature_version"],
        "preprocessing_version": config["face"]["preprocessing_version"],
        "encoder_name": config["face"]["encoder"]["name"],
        "detector_name": detector["name"],
        "event_validity_status": "not_applicable_face",
        "face_feature_blocked": int(face_feature_blocked),
    }
    for name, emb in embeddings.items():
        if name in {"face", "background", "background_blur"} and face_feature_blocked:
            continue
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
        "event_validity_status": "not_applicable_face",
        "qc_decode_success_rate": float(decode_success),
        "qc_sampled_frame_count": int(len(frames)),
        "qc_effective_face_frame_count": int(valid_face_frames),
        "qc_min_valid_face_frames": int(min_valid),
        "qc_face_feature_blocked": int(face_feature_blocked),
        "qc_face_feature_block_reason": "valid_face_frames_below_threshold" if face_feature_blocked else "",
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
        "detector_name": detector["name"],
        "detector_checkpoint": detector.get("checkpoint", ""),
        "detector_threshold": str(detector.get("threshold", "")),
        "qc_detector_formal_status": detector["formal_status"],
        "qc_detector_fallback_used": int(detector["fallback_used"]),
        "qc_detector_fallback_rate": float(detector["fallback_used"]),
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


def _load_detector(config: dict[str, Any]) -> dict[str, Any]:
    detector_cfg = config["face"].get("detector", {})
    yunet_path = project_path(detector_cfg.get("yuNet_checkpoint", ""))
    if yunet_path.exists() and hasattr(cv2, "FaceDetectorYN_create"):
        model = cv2.FaceDetectorYN_create(
            str(yunet_path),
            "",
            (320, 320),
            float(detector_cfg.get("score_threshold", 0.6)),
            float(detector_cfg.get("nms_threshold", 0.3)),
            int(detector_cfg.get("top_k", 5000)),
        )
        return {
            "name": "opencv_yunet",
            "model": model,
            "fallback_model": _load_haar_detector(),
            "checkpoint": str(yunet_path),
            "threshold": f"score>={detector_cfg.get('score_threshold', 0.6)}",
            "formal_status": "preferred_yunet_checkpoint",
            "fallback_used": 0,
        }
    return {
        "name": "opencv_haar",
        "model": _load_haar_detector(),
        "checkpoint": cv2.data.haarcascades + "haarcascade_frontalface_default.xml",
        "threshold": str(detector_cfg.get("haar_threshold", "minNeighbors=4")),
        "formal_status": "haar_fallback_no_yunet_checkpoint",
        "fallback_used": 1,
    }


def _load_haar_detector() -> cv2.CascadeClassifier:
    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    detector = cv2.CascadeClassifier(cascade_path)
    if detector.empty():
        raise RuntimeError("OpenCV Haar cascade could not be loaded.")
    return detector


def _detect_faces(detector: dict[str, Any], frame: np.ndarray, gray: np.ndarray) -> list[dict[str, Any]]:
    if detector["name"] == "opencv_yunet":
        try:
            return _detect_faces_yunet(detector, frame)
        except cv2.error:
            detector["name"] = "opencv_haar"
            detector["model"] = detector["fallback_model"]
            detector["checkpoint"] = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            detector["threshold"] = "minNeighbors=4"
            detector["formal_status"] = "haar_runtime_fallback_yunet_dnn_error"
            detector["fallback_used"] = 1
    return _detect_faces_haar(detector["model"], gray)


def _detect_faces_yunet(detector: dict[str, Any], frame: np.ndarray) -> list[dict[str, Any]]:
    height, width = frame.shape[:2]
    model = detector["model"]
    input_size = (320, 320)
    resized = cv2.resize(frame, input_size, interpolation=cv2.INTER_AREA)
    model.setInputSize(input_size)
    _, faces = model.detect(resized)
    out: list[dict[str, Any]] = []
    if faces is None:
        return out
    sx = width / float(input_size[0])
    sy = height / float(input_size[1])
    for row in faces:
        x, y, w, h = row[:4]
        score = float(row[-1])
        out.append({"box": (int(x * sx), int(y * sy), int(w * sx), int(h * sy)), "confidence": score})
    return out


def _detect_faces_haar(detector: cv2.CascadeClassifier, gray: np.ndarray) -> list[dict[str, Any]]:
    height, width = gray.shape[:2]
    target_width = 320
    if width > target_width:
        scale = target_width / float(width)
        small = cv2.resize(gray, (target_width, max(1, int(round(height * scale)))), interpolation=cv2.INTER_AREA)
        boxes = detector.detectMultiScale(small, scaleFactor=1.1, minNeighbors=4, minSize=(18, 18))
        inv = 1.0 / scale
        return [{"box": (int(x * inv), int(y * inv), int(w * inv), int(h * inv)), "confidence": math.nan} for x, y, w, h in boxes]
    boxes = detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(32, 32))
    return [{"box": (int(x), int(y), int(w), int(h)), "confidence": math.nan} for x, y, w, h in boxes]


def _largest_detection(detections: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not detections:
        return None
    return max(detections, key=lambda det: det["box"][2] * det["box"][3])


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


def _mask_box(frame: np.ndarray, box: tuple[int, int, int, int]) -> np.ndarray:
    x, y, w, h = box
    out = frame.copy()
    out[y : y + h, x : x + w] = 0
    return out


def _blur_box(frame: np.ndarray, box: tuple[int, int, int, int]) -> np.ndarray:
    x, y, w, h = box
    out = frame.copy()
    roi = out[y : y + h, x : x + w]
    if roi.size:
        k = max(15, (min(w, h) // 4) | 1)
        out[y : y + h, x : x + w] = cv2.GaussianBlur(roi, (k, k), 0)
    return out


def _to_pil(frame_bgr: np.ndarray) -> Image.Image:
    rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    return Image.fromarray(rgb)


def _annotated_image(
    frame_bgr: np.ndarray,
    box: tuple[int, int, int, int],
    l_id: str,
    task: str,
    detector: dict[str, Any],
    detection: dict[str, Any],
) -> Image.Image:
    image = _to_pil(cv2.resize(frame_bgr, (240, 135)))
    draw = ImageDraw.Draw(image)
    x, y, w, h = box
    sx = 240 / frame_bgr.shape[1]
    sy = 135 / frame_bgr.shape[0]
    draw.rectangle([x * sx, y * sy, (x + w) * sx, (y + h) * sy], outline="red", width=2)
    conf = detection.get("confidence", math.nan)
    conf_text = "nan" if not math.isfinite(float(conf)) else f"{float(conf):.2f}"
    draw.text((4, 4), f"{clean_name(l_id)} {task} {detector['name']} {conf_text}", fill="yellow")
    return image


def _contact_panels(
    frame_bgr: np.ndarray,
    box: tuple[int, int, int, int],
    crop_bgr: np.ndarray,
    background_bgr: np.ndarray,
    detector: dict[str, Any],
    detection: dict[str, Any],
    l_id: str,
    task: str,
) -> list[Image.Image]:
    return [
        _to_pil(cv2.resize(frame_bgr, (240, 135))),
        _annotated_image(frame_bgr, box, l_id, task, detector, detection),
        _to_pil(cv2.resize(crop_bgr, (240, 135))),
        _to_pil(cv2.resize(background_bgr, (240, 135))),
    ]


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
