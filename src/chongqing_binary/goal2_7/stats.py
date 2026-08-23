"""Small numerical feature helpers shared by Goal 2.6 extractors."""

from __future__ import annotations

import math
from typing import Iterable

import numpy as np
from scipy.signal import welch


BANDS = {
    "delta": (1.0, 4.0),
    "theta": (4.0, 8.0),
    "alpha": (8.0, 13.0),
    "beta": (13.0, 30.0),
    "gamma": (30.0, 45.0),
}

EEG_REGIONS = {
    "frontal": ["Fp1", "Fp2", "Fz", "F3", "F4", "F7", "F8"],
    "central": ["FC1", "FC2", "FC5", "FC6", "Cz", "C3", "C4"],
    "temporal": ["T7", "T8"],
    "parietal": ["CP1", "CP2", "CP5", "CP6", "Pz", "P3", "P4", "P7", "P8"],
    "occipital": ["PO3", "PO4", "Oz", "O1", "O2"],
    "left": ["Fp1", "F3", "F7", "FC1", "FC5", "C3", "T7", "CP1", "CP5", "P3", "P7", "PO3", "O1"],
    "right": ["Fp2", "F4", "F8", "FC2", "FC6", "C4", "T8", "CP2", "CP6", "P4", "P8", "PO4", "O2"],
}


def safe_float(value: object, default: float = math.nan) -> float:
    try:
        out = float(value)  # type: ignore[arg-type]
    except Exception:
        return default
    return out if math.isfinite(out) else default


def summarize_vector(prefix: str, values: Iterable[float]) -> dict[str, float]:
    arr = np.asarray(list(values), dtype=float)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        return {
            f"{prefix}_mean": math.nan,
            f"{prefix}_std": math.nan,
            f"{prefix}_min": math.nan,
            f"{prefix}_max": math.nan,
            f"{prefix}_p25": math.nan,
            f"{prefix}_p50": math.nan,
            f"{prefix}_p75": math.nan,
        }
    return {
        f"{prefix}_mean": float(np.mean(arr)),
        f"{prefix}_std": float(np.std(arr)),
        f"{prefix}_min": float(np.min(arr)),
        f"{prefix}_max": float(np.max(arr)),
        f"{prefix}_p25": float(np.percentile(arr, 25)),
        f"{prefix}_p50": float(np.percentile(arr, 50)),
        f"{prefix}_p75": float(np.percentile(arr, 75)),
    }


def basic_time_features(prefix: str, data: np.ndarray) -> dict[str, float]:
    arr = np.asarray(data, dtype=float)
    flat = arr.reshape(-1)
    flat = flat[np.isfinite(flat)]
    if flat.size == 0:
        return {}
    centered = flat - float(np.mean(flat))
    std = float(np.std(flat))
    skew = float(np.mean(centered**3) / (std**3 + 1e-12))
    kurt = float(np.mean(centered**4) / (std**4 + 1e-12))
    return {
        f"{prefix}_mean": float(np.mean(flat)),
        f"{prefix}_std": std,
        f"{prefix}_skewness": skew,
        f"{prefix}_kurtosis": kurt,
        f"{prefix}_abs_mean": float(np.mean(np.abs(flat))),
        f"{prefix}_p01": float(np.percentile(flat, 1)),
        f"{prefix}_p50": float(np.percentile(flat, 50)),
        f"{prefix}_p99": float(np.percentile(flat, 99)),
    }


def channel_time_features(prefix: str, data: np.ndarray, channel_names: list[str], max_channels: int = 0) -> dict[str, float]:
    arr = np.asarray(data, dtype=float)
    if arr.ndim == 3:
        arr = arr.transpose(1, 0, 2).reshape(arr.shape[1], -1)
    if arr.ndim != 2:
        return {}
    out: dict[str, float] = {}
    channel_std = np.nanstd(arr, axis=1)
    channel_mean = np.nanmean(arr, axis=1)
    out.update(summarize_vector(f"{prefix}_channel_mean", channel_mean))
    out.update(summarize_vector(f"{prefix}_channel_std", channel_std))
    if max_channels:
        for idx, name in enumerate(channel_names[: min(max_channels, arr.shape[0])]):
            values = arr[idx]
            out[f"{prefix}_ch_{clean_name(name)}_mean"] = float(np.nanmean(values))
            out[f"{prefix}_ch_{clean_name(name)}_std"] = float(np.nanstd(values))
            out[f"{prefix}_ch_{clean_name(name)}_slope"] = slope(values)
    return out


def hjorth_features(prefix: str, data: np.ndarray) -> dict[str, float]:
    arr = np.asarray(data, dtype=float)
    if arr.ndim == 3:
        arr = arr.transpose(1, 0, 2).reshape(arr.shape[1], -1)
    if arr.ndim != 2 or arr.shape[1] < 4:
        return {}
    diff1 = np.diff(arr, axis=1)
    diff2 = np.diff(diff1, axis=1)
    var0 = np.nanvar(arr, axis=1) + 1e-12
    var1 = np.nanvar(diff1, axis=1) + 1e-12
    var2 = np.nanvar(diff2, axis=1) + 1e-12
    activity = var0
    mobility = np.sqrt(var1 / var0)
    complexity = np.sqrt(var2 / var1) / (mobility + 1e-12)
    out = {}
    out.update(summarize_vector(f"{prefix}_hjorth_activity", np.log10(activity)))
    out.update(summarize_vector(f"{prefix}_hjorth_mobility", mobility))
    out.update(summarize_vector(f"{prefix}_hjorth_complexity", complexity))
    return out


def spectral_features(prefix: str, data: np.ndarray, sfreq: float, channel_names: list[str] | None = None) -> dict[str, float]:
    arr = np.asarray(data, dtype=float)
    if arr.ndim == 3:
        arr = arr.transpose(1, 0, 2).reshape(arr.shape[1], -1)
    if arr.ndim != 2 or arr.shape[1] < 8:
        return {}
    nperseg = min(max(8, int(round(4 * sfreq))), arr.shape[1])
    freqs, psd = welch(arr, fs=sfreq, nperseg=nperseg, axis=1)
    psd = np.maximum(psd, np.finfo(float).tiny)
    total_mask = (freqs >= 0.01) & (freqs <= min(45.0, sfreq / 2.0))
    total = np.trapz(psd[:, total_mask], freqs[total_mask], axis=1)
    total = np.maximum(total, np.finfo(float).tiny)
    out: dict[str, float] = {}
    band_values: dict[str, np.ndarray] = {}
    for band, (lo, hi) in BANDS.items():
        if hi >= sfreq / 2.0:
            continue
        mask = (freqs >= lo) & (freqs < hi)
        if not np.any(mask):
            continue
        power = np.trapz(psd[:, mask], freqs[mask], axis=1)
        power = np.maximum(power, np.finfo(float).tiny)
        band_values[band] = power
        out.update(summarize_vector(f"{prefix}_log_{band}", np.log10(power)))
        out.update(summarize_vector(f"{prefix}_rel_{band}", power / total))
    theta = band_values.get("theta")
    alpha = band_values.get("alpha")
    beta = band_values.get("beta")
    if theta is not None and alpha is not None:
        out.update(summarize_vector(f"{prefix}_theta_alpha_ratio", theta / np.maximum(alpha, 1e-12)))
    if beta is not None and alpha is not None:
        out.update(summarize_vector(f"{prefix}_beta_alpha_ratio", beta / np.maximum(alpha, 1e-12)))
    if np.any(total_mask):
        norm = psd[:, total_mask] / np.maximum(psd[:, total_mask].sum(axis=1, keepdims=True), 1e-12)
        entropy = -(norm * np.log(norm + 1e-12)).sum(axis=1) / max(math.log(norm.shape[1]), 1e-12)
        out.update(summarize_vector(f"{prefix}_spectral_entropy", entropy))
    if channel_names:
        out.update(region_spectral_features(prefix, band_values, total, channel_names))
    return out


def region_spectral_features(prefix: str, band_values: dict[str, np.ndarray], total: np.ndarray, channel_names: list[str]) -> dict[str, float]:
    label_to_idx = {name: idx for idx, name in enumerate(channel_names)}
    out: dict[str, float] = {}
    for region, channels in EEG_REGIONS.items():
        idx = [label_to_idx[ch] for ch in channels if ch in label_to_idx]
        if not idx:
            continue
        for band, power in band_values.items():
            out[f"{prefix}_region_{region}_{band}_log_mean"] = float(np.mean(np.log10(power[idx] + 1e-12)))
            out[f"{prefix}_region_{region}_{band}_rel_mean"] = float(np.mean(power[idx] / np.maximum(total[idx], 1e-12)))
    left = [label_to_idx[ch] for ch in EEG_REGIONS["left"] if ch in label_to_idx]
    right = [label_to_idx[ch] for ch in EEG_REGIONS["right"] if ch in label_to_idx]
    if left and right:
        for band, power in band_values.items():
            out[f"{prefix}_asym_left_right_{band}"] = float(np.log((np.mean(power[right]) + 1e-12) / (np.mean(power[left]) + 1e-12)))
    return out


def connectivity_features(prefix: str, data: np.ndarray) -> dict[str, float]:
    arr = np.asarray(data, dtype=float)
    if arr.ndim == 3:
        arr = arr.transpose(1, 0, 2).reshape(arr.shape[1], -1)
    if arr.ndim != 2 or arr.shape[0] < 3:
        return {}
    corr = np.corrcoef(arr)
    vals = corr[np.triu_indices(corr.shape[0], k=1)]
    vals = vals[np.isfinite(vals)]
    return summarize_vector(f"{prefix}_channel_corr", vals)


def slope(values: np.ndarray) -> float:
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    if arr.size < 2:
        return math.nan
    x = np.linspace(0.0, 1.0, arr.size)
    return float(np.polyfit(x, arr, deg=1)[0])


def autocorr_lag1(values: np.ndarray) -> float:
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    if arr.size < 3:
        return math.nan
    a = arr[:-1] - np.mean(arr[:-1])
    b = arr[1:] - np.mean(arr[1:])
    den = np.sqrt(np.sum(a * a) * np.sum(b * b))
    return float(np.sum(a * b) / den) if den else math.nan


def clean_name(name: object) -> str:
    text = str(name).strip().replace(" ", "_").replace("-", "_")
    return "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in text)
