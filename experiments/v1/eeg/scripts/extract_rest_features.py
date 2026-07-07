#!/usr/bin/env python3
"""Extract subject-level resting EEG features for Chongqing v1."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import mne
import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from scipy.signal import welch
from tqdm import tqdm


V1_ROOT = Path("/home/qiangminc/codes/data4_qiangminc/code/chongqing/experiments/v1")
INDEX_DIR = V1_ROOT / "eeg" / "artifacts" / "index"
FEATURE_DIR = V1_ROOT / "eeg" / "artifacts" / "features"

BANDS = {
    "delta": (1.0, 4.0),
    "theta": (4.0, 8.0),
    "alpha": (8.0, 13.0),
    "beta": (13.0, 30.0),
    "gamma": (30.0, 45.0),
}

REGIONS = {
    "frontal": ["Fp1", "Fp2", "Fz", "F3", "F4", "F7", "F8"],
    "central": ["FC1", "FC2", "FC5", "FC6", "Cz", "C3", "C4"],
    "temporal": ["T7", "T8"],
    "parietal": ["CP1", "CP2", "CP5", "CP6", "Pz", "P3", "P4", "P7", "P8"],
    "occipital": ["PO3", "PO4", "Oz", "O1", "O2"],
    "left": ["Fp1", "F3", "F7", "FC1", "FC5", "C3", "T7", "CP1", "CP5", "P3", "P7", "PO3", "O1"],
    "right": ["Fp2", "F4", "F8", "FC2", "FC6", "C4", "T8", "CP2", "CP6", "P4", "P8", "PO4", "O2"],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", choices=["rest"], default="rest")
    parser.add_argument("--limit", type=int, default=None, help="Limit indexed subjects for smoke tests.")
    parser.add_argument("--n-jobs", type=int, default=4)
    parser.add_argument("--index-csv", type=Path, default=INDEX_DIR / "eeg_rest_file_index.csv")
    parser.add_argument("--out-dir", type=Path, default=FEATURE_DIR)
    parser.add_argument("--epoch-sec", type=float, default=5.0)
    parser.add_argument("--min-good-epochs", type=int, default=20)
    parser.add_argument("--reject-uv", type=float, default=200.0)
    return parser.parse_args()


def clean_channel_names(raw: mne.io.BaseRaw) -> None:
    mapping = {}
    for ch in raw.ch_names:
        clean = ch.strip().replace(" ", "")
        mapping[ch] = clean
    raw.rename_channels(mapping)


def load_raw(path: str) -> mne.io.BaseRaw:
    raw = mne.io.read_raw_bdf(path, preload=True, verbose="ERROR")
    clean_channel_names(raw)
    raw.pick("eeg", exclude=[])
    montage = mne.channels.make_standard_montage("standard_1020")
    raw.set_montage(montage, match_case=False, on_missing="ignore", verbose="ERROR")
    raw.set_eeg_reference("average", projection=False, verbose="ERROR")
    raw.notch_filter(freqs=[50.0], verbose="ERROR")
    raw.filter(l_freq=0.5, h_freq=45.0, verbose="ERROR")
    raw.resample(250.0, verbose="ERROR")
    return raw


def epoch_good_data(raw: mne.io.BaseRaw, epoch_sec: float, reject_uv: float) -> tuple[np.ndarray, dict[str, float]]:
    # The BDF header uses a nonstandard physical dimension ("uV/mm"). MNE keeps
    # the native physical scale in get_data(); asking for units="uV" multiplies
    # these values by 1e6 and makes artifact rejection unusable.
    data = raw.get_data()
    sfreq = float(raw.info["sfreq"])
    epoch_len = int(round(epoch_sec * sfreq))
    n_epochs = data.shape[1] // epoch_len
    if n_epochs <= 0:
        return np.empty((0, data.shape[0], epoch_len)), {
            "sfreq": sfreq,
            "n_epochs_total": 0,
            "n_epochs_good": 0,
            "bad_epoch_rate": 1.0,
        }
    trimmed = data[:, : n_epochs * epoch_len]
    epochs = trimmed.reshape(data.shape[0], n_epochs, epoch_len).transpose(1, 0, 2)
    finite = np.isfinite(epochs).all(axis=(1, 2))
    ptp = np.ptp(epochs, axis=2)
    too_large = (ptp > reject_uv).any(axis=1)
    too_flat = (ptp < 0.1).any(axis=1)
    good_mask = finite & ~too_large & ~too_flat
    good = epochs[good_mask]
    qc = {
        "sfreq": sfreq,
        "n_epochs_total": int(n_epochs),
        "n_epochs_good": int(good.shape[0]),
        "bad_epoch_rate": float(1.0 - (good.shape[0] / n_epochs)),
    }
    return good, qc


def bandpower_features(epochs: np.ndarray, sfreq: float, ch_names: list[str]) -> dict[str, float]:
    flat = epochs.transpose(1, 0, 2).reshape(len(ch_names), -1)
    nperseg = min(int(round(4 * sfreq)), flat.shape[1])
    freqs, psd = welch(flat, fs=sfreq, nperseg=nperseg, axis=1)
    psd = np.maximum(psd, np.finfo(float).tiny)
    total_mask = (freqs >= 1.0) & (freqs <= 45.0)
    total_power = np.trapezoid(psd[:, total_mask], freqs[total_mask], axis=1)
    total_power = np.maximum(total_power, np.finfo(float).tiny)
    features: dict[str, float] = {}
    band_values: dict[str, np.ndarray] = {}
    for band, (lo, hi) in BANDS.items():
        mask = (freqs >= lo) & (freqs < hi)
        power = np.trapezoid(psd[:, mask], freqs[mask], axis=1)
        power = np.maximum(power, np.finfo(float).tiny)
        rel = power / total_power
        band_values[band] = power
        for ch, pwr, rpwr in zip(ch_names, power, rel, strict=False):
            features[f"bp_log_{band}_{ch}"] = float(np.log10(pwr))
            features[f"bp_rel_{band}_{ch}"] = float(rpwr)
    label_to_idx = {ch: i for i, ch in enumerate(ch_names)}
    for region, channels in REGIONS.items():
        idx = [label_to_idx[ch] for ch in channels if ch in label_to_idx]
        if not idx:
            continue
        for band, power in band_values.items():
            region_power = np.maximum(power[idx], np.finfo(float).tiny)
            features[f"region_log_{region}_{band}"] = float(np.log10(np.mean(region_power)))
            features[f"region_rel_{region}_{band}"] = float(np.mean(region_power / total_power[idx]))
    for band, power in band_values.items():
        left_idx = [label_to_idx[ch] for ch in REGIONS["left"] if ch in label_to_idx]
        right_idx = [label_to_idx[ch] for ch in REGIONS["right"] if ch in label_to_idx]
        if left_idx and right_idx:
            left = float(np.mean(power[left_idx]))
            right = float(np.mean(power[right_idx]))
            features[f"asym_left_right_{band}"] = float(np.log((right + 1e-12) / (left + 1e-12)))
    psd_norm = psd[:, total_mask] / psd[:, total_mask].sum(axis=1, keepdims=True)
    entropy = -(psd_norm * np.log(psd_norm + 1e-12)).sum(axis=1) / math.log(psd_norm.shape[1])
    for ch, ent in zip(ch_names, entropy, strict=False):
        features[f"spectral_entropy_{ch}"] = float(ent)
    features["spectral_entropy_mean"] = float(np.mean(entropy))
    return features


def hjorth_features(epochs: np.ndarray, ch_names: list[str]) -> dict[str, float]:
    flat = epochs.transpose(1, 0, 2).reshape(len(ch_names), -1)
    diff1 = np.diff(flat, axis=1)
    diff2 = np.diff(diff1, axis=1)
    var0 = np.var(flat, axis=1) + 1e-12
    var1 = np.var(diff1, axis=1) + 1e-12
    var2 = np.var(diff2, axis=1) + 1e-12
    activity = var0
    mobility = np.sqrt(var1 / var0)
    complexity = np.sqrt(var2 / var1) / mobility
    features: dict[str, float] = {}
    for ch, act, mob, comp in zip(ch_names, activity, mobility, complexity, strict=False):
        features[f"hjorth_activity_{ch}"] = float(np.log10(act))
        features[f"hjorth_mobility_{ch}"] = float(mob)
        features[f"hjorth_complexity_{ch}"] = float(comp)
    features["hjorth_activity_mean"] = float(np.mean(np.log10(activity)))
    features["hjorth_mobility_mean"] = float(np.mean(mobility))
    features["hjorth_complexity_mean"] = float(np.mean(complexity))
    return features


def process_one(row: dict[str, object], args: argparse.Namespace) -> tuple[dict[str, object], dict[str, object]]:
    base = {
        "L_id": row["L_id"],
        "task": row["task"],
        "data_file": row["data_file"],
    }
    qc = {
        "L_id": row["L_id"],
        "task": row["task"],
        "feature_status": "fail",
        "feature_error": "",
    }
    try:
        if not row["data_file"]:
            raise FileNotFoundError("missing data_file")
        raw = load_raw(str(row["data_file"]))
        epochs, epoch_qc = epoch_good_data(raw, args.epoch_sec, args.reject_uv)
        qc.update(epoch_qc)
        qc["n_channels_used"] = len(raw.ch_names)
        qc["duration_sec_loaded"] = float(raw.times[-1]) if len(raw.times) else 0.0
        if epochs.shape[0] < args.min_good_epochs:
            qc["feature_status"] = "fail"
            qc["feature_error"] = f"too_few_good_epochs:{epochs.shape[0]}"
            return base, qc
        features = dict(base)
        features.update({f"qc_{k}": v for k, v in qc.items() if k not in {"L_id", "task", "feature_status", "feature_error"}})
        features.update(bandpower_features(epochs, float(raw.info["sfreq"]), raw.ch_names))
        features.update(hjorth_features(epochs, raw.ch_names))
        qc["feature_status"] = "ok"
        return features, qc
    except Exception as exc:  # noqa: BLE001 - write per-subject failure instead of aborting batch.
        qc["feature_error"] = repr(exc)
        return base, qc


def write_report(path: Path, features: pd.DataFrame, qc: pd.DataFrame, args: argparse.Namespace) -> None:
    status_counts = qc["feature_status"].value_counts(dropna=False).to_dict() if not qc.empty else {}
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        f.write("# EEG Rest Feature Extraction QA\n\n")
        f.write(f"- Index CSV: `{args.index_csv}`\n")
        f.write(f"- Subjects attempted: {len(qc)}\n")
        f.write(f"- Feature rows written: {len(features)}\n")
        f.write(f"- Feature status counts: `{json.dumps(status_counts, ensure_ascii=False)}`\n")
        if not qc.empty and "bad_epoch_rate" in qc:
            f.write(f"- Median bad epoch rate: {qc['bad_epoch_rate'].median(skipna=True):.4f}\n")
        f.write("- Feature columns exclude clinical labels and clinical scale fields.\n")


def main() -> None:
    args = parse_args()
    if not args.index_csv.exists():
        raise FileNotFoundError(f"Missing index CSV: {args.index_csv}. Run index_eeg_files.py first.")
    index = pd.read_csv(args.index_csv)
    index = index[index["qc_status"].isin(["ok", "warn"])].copy()
    index = index[index["data_header_status"] == "ok"].copy()
    if args.limit is not None:
        index = index.head(args.limit)
    rows = index.to_dict(orient="records")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    iterator = tqdm(rows, desc="Extract EEG Rest features")
    if args.n_jobs == 1:
        results = [process_one(row, args) for row in iterator]
    else:
        results = Parallel(n_jobs=args.n_jobs)(
            delayed(process_one)(row, args) for row in iterator
        )
    features = pd.DataFrame([feat for feat, qc in results if qc.get("feature_status") == "ok"])
    qc = pd.DataFrame([qc for _, qc in results])
    features_path = args.out_dir / "eeg_rest_features.csv"
    qc_path = args.out_dir / "eeg_rest_feature_qc.csv"
    report_path = args.out_dir / "eeg_rest_feature_qc.md"
    features.to_csv(features_path, index=False)
    qc.to_csv(qc_path, index=False)
    write_report(report_path, features, qc, args)
    print(json.dumps({"features": str(features_path), "qc": str(qc_path), "rows": len(features)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
