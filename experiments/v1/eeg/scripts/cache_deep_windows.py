#!/usr/bin/env python3
"""Cache anonymized EEG windows for deep-learning baselines.

The script reads raw BDF data, writes preprocessed float32 windows under v1, and
never writes inside the original dataset. Metadata contains L_id and task/event
fields only; named main BDF files are ignored.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path

import mne
import numpy as np
import pandas as pd
from tqdm import tqdm


DATA_ROOT = Path("/home/qiangminc/codes/data4_qiangminc/datasets_qiangmin/chongqing")
V1_ROOT = Path("/home/qiangminc/codes/data4_qiangminc/code/chongqing/experiments/v1")
MANIFEST = Path(
    "/home/qiangminc/codes/data4_qiangminc/code/chongqing/"
    "inputs/derived_reports/chongqing_binary_diagnosis_report/data/subject_manifest.csv"
)
OUT_DIR = V1_ROOT / "eeg" / "artifacts" / "deep" / "windows"

CHANNELS = [
    "Fp1",
    "Fp2",
    "Fz",
    "F3",
    "F4",
    "F7",
    "F8",
    "FC1",
    "FC2",
    "FC5",
    "FC6",
    "Cz",
    "C3",
    "C4",
    "T7",
    "T8",
    "A1",
    "A2",
    "CP1",
    "CP2",
    "CP5",
    "CP6",
    "Pz",
    "P3",
    "P4",
    "P7",
    "P8",
    "PO3",
    "PO4",
    "Oz",
    "O1",
    "O2",
]


TASKS = {
    "rest": {
        "dir": "1_rest-1334",
        "data_suffix": "1",
        "window_sec": 5.0,
        "epoch_tmin": 0.0,
        "epoch_tmax": 5.0,
        "event_codes": [],
    },
    "oddball": {
        "dir": "2_Oldball-2358",
        "data_suffix": "2",
        "window_sec": 1.0,
        "epoch_tmin": -0.2,
        "epoch_tmax": 0.8,
        "event_codes": ["22"],
    },
    "1back": {
        "dir": "4_1BACK-1810",
        "data_suffix": "4",
        "window_sec": 2.0,
        "epoch_tmin": -0.2,
        "epoch_tmax": 1.8,
        "event_codes": ["18", "19"],
    },
}


@dataclass
class SubjectFiles:
    l_id: str
    subject_dir: str
    data_file: Path
    evt_file: Path | None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", choices=sorted(TASKS), required=True)
    parser.add_argument("--label", default="primary_label_nonhealthy")
    parser.add_argument("--data-root", type=Path, default=DATA_ROOT)
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    parser.add_argument("--limit-subjects", type=int, default=None)
    parser.add_argument("--max-windows-per-subject", type=int, default=None)
    parser.add_argument("--sfreq", type=float, default=250.0)
    parser.add_argument("--reject-threshold", type=float, default=200.0)
    return parser.parse_args()


def parse_l_id(path: Path) -> str:
    match = re.search(r"L\d+", path.name, flags=re.IGNORECASE)
    return match.group(0).upper() if match else ""


def role_file(subject_dir: Path, role: str) -> Path | None:
    files = sorted(subject_dir.glob("*.bdf"))
    if role == "data":
        matches = [p for p in files if p.name.lower().endswith("_data.bdf")]
        matches += [p for p in files if p.name.lower() == "data.bdf"]
    elif role == "evt":
        matches = [p for p in files if p.name.lower().endswith("_evt.bdf")]
        matches += [p for p in files if p.name.lower() == "evt.bdf"]
    else:
        raise ValueError(role)
    return matches[0] if matches else None


def collect_subject_files(args: argparse.Namespace) -> list[SubjectFiles]:
    task_root = args.data_root / "脑电" / TASKS[args.task]["dir"]
    out = []
    for subject_dir in sorted(p for p in task_root.iterdir() if p.is_dir()):
        l_id = parse_l_id(subject_dir)
        data_file = role_file(subject_dir, "data")
        evt_file = role_file(subject_dir, "evt")
        if l_id and data_file is not None:
            out.append(SubjectFiles(l_id=l_id, subject_dir=subject_dir.name, data_file=data_file, evt_file=evt_file))
    if args.limit_subjects is not None:
        out = out[: args.limit_subjects]
    return out


def load_labels(path: Path, label_col: str) -> dict[str, int]:
    manifest = pd.read_csv(path, dtype={"L_id": str, label_col: "string"})
    manifest = manifest[manifest[label_col].isin(["0", "1", 0, 1])].copy()
    manifest[label_col] = manifest[label_col].astype(int)
    return dict(zip(manifest["L_id"], manifest[label_col], strict=False))


def clean_channel_names(raw: mne.io.BaseRaw) -> None:
    raw.rename_channels({ch: ch.strip().replace(" ", "") for ch in raw.ch_names})


def load_preprocessed_raw(path: Path, sfreq: float) -> mne.io.BaseRaw:
    raw = mne.io.read_raw_bdf(path, preload=True, verbose="ERROR")
    clean_channel_names(raw)
    missing = [ch for ch in CHANNELS if ch not in raw.ch_names]
    if missing:
        raise RuntimeError(f"missing_channels:{missing}")
    raw.pick(CHANNELS)
    montage = mne.channels.make_standard_montage("standard_1020")
    raw.set_montage(montage, match_case=False, on_missing="ignore", verbose="ERROR")
    raw.set_eeg_reference("average", projection=False, verbose="ERROR")
    raw.notch_filter(freqs=[50.0], verbose="ERROR")
    raw.filter(l_freq=0.5, h_freq=45.0, verbose="ERROR")
    raw.resample(sfreq, verbose="ERROR")
    return raw


def good_window(window: np.ndarray, reject_threshold: float) -> bool:
    if not np.isfinite(window).all():
        return False
    ptp = np.ptp(window, axis=1)
    if np.any(ptp > reject_threshold):
        return False
    if np.any(ptp < 0.1):
        return False
    return True


def standardize_window(window: np.ndarray) -> np.ndarray:
    centered = window - window.mean(axis=1, keepdims=True)
    scale = centered.std(axis=1, keepdims=True)
    scale = np.where(scale < 1e-6, 1.0, scale)
    return (centered / scale).astype(np.float32)


def event_annotations(evt_file: Path | None, codes: list[str]) -> list[tuple[float, str]]:
    if evt_file is None:
        return []
    raw_evt = mne.io.read_raw_bdf(evt_file, preload=False, verbose="ERROR")
    out = []
    allowed = set(codes)
    for onset, desc in zip(raw_evt.annotations.onset, raw_evt.annotations.description, strict=False):
        desc_s = str(desc)
        if desc_s in allowed:
            out.append((float(onset), desc_s))
    return out


def extract_windows(files: SubjectFiles, label: int, args: argparse.Namespace) -> tuple[list[np.ndarray], list[dict[str, object]], dict[str, object]]:
    spec = TASKS[args.task]
    qc = {
        "L_id": files.l_id,
        "task": args.task,
        "status": "fail",
        "error": "",
        "windows": 0,
        "rejected_windows": 0,
    }
    windows: list[np.ndarray] = []
    meta: list[dict[str, object]] = []
    try:
        raw = load_preprocessed_raw(files.data_file, args.sfreq)
        data = raw.get_data()
        sfreq = float(raw.info["sfreq"])
        if args.task == "rest":
            win_samples = int(round(spec["window_sec"] * sfreq))
            total = data.shape[1] // win_samples
            for i in range(total):
                start = i * win_samples
                stop = start + win_samples
                window = data[:, start:stop]
                if not good_window(window, args.reject_threshold):
                    qc["rejected_windows"] += 1
                    continue
                windows.append(standardize_window(window))
                meta.append(
                    {
                        "L_id": files.l_id,
                        "task": args.task,
                        "label": label,
                        "window_in_subject": i,
                        "event_code": "",
                        "event_onset_sec": "",
                        "start_sec": start / sfreq,
                        "stop_sec": stop / sfreq,
                        "n_samples": win_samples,
                    }
                )
                if args.max_windows_per_subject is not None and len(windows) >= args.max_windows_per_subject:
                    break
        else:
            tmin = float(spec["epoch_tmin"])
            tmax = float(spec["epoch_tmax"])
            win_samples = int(round((tmax - tmin) * sfreq))
            events = event_annotations(files.evt_file, list(spec["event_codes"]))
            for i, (onset, event_code) in enumerate(events):
                start = int(round((onset + tmin) * sfreq))
                stop = start + win_samples
                if start < 0 or stop > data.shape[1]:
                    qc["rejected_windows"] += 1
                    continue
                window = data[:, start:stop]
                if not good_window(window, args.reject_threshold):
                    qc["rejected_windows"] += 1
                    continue
                windows.append(standardize_window(window))
                meta.append(
                    {
                        "L_id": files.l_id,
                        "task": args.task,
                        "label": label,
                        "window_in_subject": i,
                        "event_code": event_code,
                        "event_onset_sec": onset,
                        "start_sec": start / sfreq,
                        "stop_sec": stop / sfreq,
                        "n_samples": win_samples,
                    }
                )
                if args.max_windows_per_subject is not None and len(windows) >= args.max_windows_per_subject:
                    break
        qc["windows"] = len(windows)
        qc["status"] = "ok" if windows else "fail"
        if not windows:
            qc["error"] = "no_valid_windows"
        return windows, meta, qc
    except Exception as exc:  # noqa: BLE001
        qc["error"] = repr(exc)
        return [], [], qc


def write_outputs(
    windows: list[np.ndarray],
    metadata: list[dict[str, object]],
    qc_rows: list[dict[str, object]],
    args: argparse.Namespace,
) -> None:
    args.out_dir.mkdir(parents=True, exist_ok=True)
    x_path = args.out_dir / f"X_{args.task}.npy"
    meta_path = args.out_dir / f"metadata_{args.task}.csv"
    qc_path = args.out_dir / f"qa_{args.task}.csv"
    report_path = args.out_dir / f"qa_{args.task}.md"
    if windows:
        x = np.stack(windows).astype(np.float32)
    else:
        n_samples = int(round(TASKS[args.task]["window_sec"] * args.sfreq))
        x = np.empty((0, len(CHANNELS), n_samples), dtype=np.float32)
    np.save(x_path, x)
    fields = ["L_id", "task", "label", "window_in_subject", "event_code", "event_onset_sec", "start_sec", "stop_sec", "n_samples"]
    with meta_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(metadata)
    with qc_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["L_id", "task", "status", "error", "windows", "rejected_windows"])
        writer.writeheader()
        writer.writerows(qc_rows)
    meta_df = pd.DataFrame(metadata)
    qc_df = pd.DataFrame(qc_rows)
    status_counts = qc_df["status"].value_counts(dropna=False).to_dict() if not qc_df.empty else {}
    label_counts = meta_df.drop_duplicates("L_id")["label"].value_counts().sort_index().to_dict() if not meta_df.empty else {}
    event_counts = meta_df["event_code"].value_counts(dropna=False).to_dict() if "event_code" in meta_df else {}
    with report_path.open("w", encoding="utf-8") as f:
        f.write(f"# Deep EEG Window Cache QA: {args.task}\n\n")
        f.write(f"- X path: `{x_path}`\n")
        f.write(f"- Metadata path: `{meta_path}`\n")
        f.write(f"- Tensor shape: `{tuple(x.shape)}`\n")
        f.write(f"- Subject QC status: `{json.dumps(status_counts, ensure_ascii=False)}`\n")
        f.write(f"- Subject label counts: `{json.dumps(label_counts, ensure_ascii=False)}`\n")
        f.write(f"- Event counts: `{json.dumps(event_counts, ensure_ascii=False)}`\n")
        f.write("- Metadata contains L_id only; no names or clinical scale fields are written.\n")


def main() -> None:
    args = parse_args()
    labels = load_labels(args.manifest, args.label)
    subjects = [s for s in collect_subject_files(args) if s.l_id in labels]
    all_windows: list[np.ndarray] = []
    all_metadata: list[dict[str, object]] = []
    qc_rows: list[dict[str, object]] = []
    for files in tqdm(subjects, desc=f"Cache {args.task} windows"):
        windows, metadata, qc = extract_windows(files, labels[files.l_id], args)
        all_windows.extend(windows)
        all_metadata.extend(metadata)
        qc_rows.append(qc)
    write_outputs(all_windows, all_metadata, qc_rows, args)
    print(
        json.dumps(
            {
                "task": args.task,
                "subjects_attempted": len(subjects),
                "windows": len(all_windows),
                "out_dir": str(args.out_dir),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()

