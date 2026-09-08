"""Resting-state EEG features for Goal 2.8.

Rest carries no events, so it uses continuous fixed-length windows and spectral
features instead of the event-locked ERP path. Frontal alpha asymmetry is
computed explicitly because it is a long-standing depression marker.
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
from .eeg_epochs import _match_role, subject_dirs

BAND_ORDER = ["delta", "theta", "alpha", "beta", "gamma"]


def _subject_rest_features(l_id: str, subject_dir: Path, eeg_cfg: dict[str, Any],
                           eeg_common: dict[str, Any]) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    import mne

    mne.set_log_level("ERROR")
    rest_cfg = eeg_cfg["rest"]
    qc: dict[str, Any] = {"L_id": l_id, "task": "rest", "qc_feature_status": "blocked", "qc_failure_reason": ""}

    data_files = _match_role(subject_dir, eeg_common["data_file_patterns"])
    if not data_files:
        qc["qc_failure_reason"] = "missing_data_bdf"
        return None, qc
    try:
        raw = mne.io.read_raw_bdf(data_files[0], preload=True, verbose="ERROR")
    except Exception as exc:  # noqa: BLE001
        qc["qc_failure_reason"] = f"read_error:{type(exc).__name__}"
        return None, qc
    if list(raw.ch_names) != list(eeg_common["channels"]):
        qc["qc_failure_reason"] = "unexpected_channel_set"
        return None, qc

    duration = raw.n_times / raw.info["sfreq"]
    raw.apply_function(lambda x: x * float(eeg_cfg["bdf_to_volts_scale"]))
    raw.set_channel_types({name: "eeg" for name in raw.ch_names})
    try:
        raw.set_eeg_reference(list(eeg_cfg["reference"]), verbose="ERROR")
    except Exception as exc:  # noqa: BLE001
        qc["qc_failure_reason"] = f"reference_error:{type(exc).__name__}"
        return None, qc
    raw.filter(float(rest_cfg["highpass_hz"]), float(rest_cfg["lowpass_hz"]),
               fir_design="firwin", verbose="ERROR")

    epochs = mne.make_fixed_length_epochs(raw, duration=float(rest_cfg["window_sec"]),
                                          preload=True, verbose="ERROR")
    candidate = len(epochs)
    threshold = eeg_cfg["reject_peak_to_peak_volts"]
    if isinstance(threshold, dict):
        threshold = threshold["rest"]
    # Blinks dominate the frontopolar channels; keep them but let the rest decide.
    excluded = [c for c in eeg_cfg.get("reject_exclude_channels", []) if c in raw.ch_names]
    reject_picks = [c for c in epochs.ch_names if c not in excluded]
    if reject_picks:
        keep = epochs.copy().pick(reject_picks)
        keep.drop_bad(reject=dict(eeg=float(threshold)), verbose="ERROR")
        epochs = epochs[[i for i, log in enumerate(keep.drop_log) if not log]]
    if len(epochs) < int(rest_cfg["min_valid_windows"]):
        qc.update({"qc_failure_reason": "too_few_valid_windows",
                   "qc_candidate_windows": candidate, "qc_valid_windows": len(epochs),
                   "qc_recording_duration_sec": duration})
        return None, qc

    max_windows = int(rest_cfg.get("max_windows", 0) or 0)
    if max_windows and len(epochs) > max_windows:
        keep = np.linspace(0, len(epochs) - 1, max_windows).astype(int)
        epochs = epochs[keep]

    spectrum = epochs.compute_psd(method="welch", fmin=float(rest_cfg["highpass_hz"]),
                                  fmax=float(rest_cfg["lowpass_hz"]), verbose="ERROR")
    psd = spectrum.get_data().mean(axis=0)          # (n_channels, n_freqs)
    freqs = spectrum.freqs
    channels = list(epochs.ch_names)
    ch_index = {c: i for i, c in enumerate(channels)}

    bands = {k: [float(v[0]), float(v[1])] for k, v in rest_cfg["bands"].items()}
    total_mask = (freqs >= float(rest_cfg["highpass_hz"])) & (freqs <= float(rest_cfg["lowpass_hz"]))
    total_power = np.trapezoid(psd[:, total_mask], freqs[total_mask], axis=1)

    signal: dict[str, Any] = {
        "L_id": l_id, "modality": "eeg", "task": "rest",
        "feature_version": "goal2_8_eeg_rest_spectral_v1",
        "preprocessing_version": eeg_cfg["preprocessing_version"],
        "event_validity_status": "event_free_rest",
    }
    band_power: dict[str, np.ndarray] = {}
    for band in BAND_ORDER:
        lo, hi = bands[band]
        mask = (freqs >= lo) & (freqs <= hi)
        power = np.trapezoid(psd[:, mask], freqs[mask], axis=1)
        band_power[band] = power
        relative = power / np.maximum(total_power, 1e-30)
        signal[f"signal_rest_{band}_abs_mean"] = float(np.nanmean(np.log10(np.maximum(power, 1e-30))))
        signal[f"signal_rest_{band}_rel_mean"] = float(np.nanmean(relative))
        signal[f"signal_rest_{band}_rel_std"] = float(np.nanstd(relative))
        for channel in ("Fz", "Cz", "Pz", "O1", "O2", "F3", "F4"):
            if channel in ch_index:
                signal[f"signal_rest_{band}_rel_{channel}"] = float(relative[ch_index[channel]])

    signal["signal_rest_theta_alpha_ratio"] = float(
        np.nanmean(band_power["theta"] / np.maximum(band_power["alpha"], 1e-30)))
    signal["signal_rest_alpha_beta_ratio"] = float(
        np.nanmean(band_power["alpha"] / np.maximum(band_power["beta"], 1e-30)))

    lo, hi = rest_cfg["alpha_peak_search_hz"]
    peak_mask = (freqs >= float(lo)) & (freqs <= float(hi))
    if np.any(peak_mask):
        posterior = [ch_index[c] for c in ("Pz", "O1", "O2", "P3", "P4") if c in ch_index]
        if posterior:
            profile = psd[posterior][:, peak_mask].mean(axis=0)
            signal["signal_rest_alpha_peak_hz"] = float(freqs[peak_mask][int(np.argmax(profile))])
            signal["signal_rest_alpha_peak_power"] = float(np.log10(max(profile.max(), 1e-30)))

    # Alpha asymmetry: log(right) - log(left).
    for name, (left, right) in rest_cfg["asymmetry_pairs"].items():
        if left in ch_index and right in ch_index:
            lp = max(float(band_power["alpha"][ch_index[left]]), 1e-30)
            rp = max(float(band_power["alpha"][ch_index[right]]), 1e-30)
            signal[f"signal_rest_alpha_asymmetry_{name}"] = float(np.log(rp) - np.log(lp))

    data = epochs.get_data()
    diff1 = np.diff(data, axis=2)
    diff2 = np.diff(diff1, axis=2)
    var0 = np.var(data, axis=2) + 1e-30
    var1 = np.var(diff1, axis=2) + 1e-30
    mobility = np.sqrt(var1 / var0)
    complexity = np.sqrt(np.var(diff2, axis=2) / var1) / mobility
    signal["signal_rest_hjorth_activity_mean"] = float(np.nanmean(np.log10(var0)))
    signal["signal_rest_hjorth_mobility_mean"] = float(np.nanmean(mobility))
    signal["signal_rest_hjorth_complexity_mean"] = float(np.nanmean(complexity))

    flat = data.transpose(1, 0, 2).reshape(len(channels), -1)
    corr = np.corrcoef(flat)
    upper = corr[np.triu_indices_from(corr, k=1)]
    signal["signal_rest_connectivity_mean"] = float(np.nanmean(upper))
    signal["signal_rest_connectivity_std"] = float(np.nanstd(upper))

    qc.update({
        "qc_feature_status": "ok", "qc_failure_reason": "",
        "qc_recording_duration_sec": duration,
        "qc_candidate_windows": candidate, "qc_valid_windows": len(epochs),
        "qc_rejected_rate": float(1 - len(epochs) / candidate) if candidate else np.nan,
        "qc_total_power_log10_mean": float(np.nanmean(np.log10(np.maximum(total_power, 1e-30)))),
        "qc_sampling_rate": float(raw.info["sfreq"]),
    })
    return signal, qc


def extract_rest_features(config_path: str | Path = "configs/goal2_8/eeg.yaml",
                          limit: int | None = None, n_jobs: int | None = None,
                          spec: ParadigmSpec | None = None) -> dict[str, Any]:
    from joblib import Parallel, delayed

    config = load_goal_config(config_path)
    spec = spec or load_paradigm_spec(config["paths"]["paradigm_spec"])
    task_spec = spec.eeg("rest")
    eeg_cfg = config["eeg"]
    eeg_common = spec.eeg_common

    raw_root = project_path(config["paths"]["raw_data_dir"])
    available = subject_dirs(raw_root, task_spec, eeg_common)
    split = cv_subjects(config)
    targets = [(str(l), available[str(l)]) for l in split["L_id"] if str(l) in available]
    if limit:
        targets = targets[:limit]

    jobs = int(n_jobs if n_jobs is not None else config.get("run", {}).get("n_jobs", 1))
    if jobs == 1:
        results = [_subject_rest_features(l, d, eeg_cfg, eeg_common) for l, d in targets]
    else:
        results = Parallel(n_jobs=jobs, backend="loky", verbose=5)(
            delayed(_subject_rest_features)(l, d, eeg_cfg, eeg_common) for l, d in targets
        )

    signal = pd.DataFrame([s for s, _ in results if s])
    qc = pd.DataFrame([q for _, q in results])

    keep = [c for c in ["L_id", "A_id", "primary_label_nonhealthy", "split_group", "split_role",
                        "is_locked_test", "cv_fold", "sex", "age", "grade", "grade_group",
                        "fnirs_device"] if c in split.columns]
    signal_out = split[keep].merge(signal, on="L_id", how="inner").sort_values("L_id").reset_index(drop=True)
    qc_out = split[keep].merge(qc, on="L_id", how="inner").sort_values("L_id").reset_index(drop=True)
    for frame, label in ((signal_out, "signal"), (qc_out, "qc")):
        if pd.to_numeric(frame.get("is_locked_test", 0), errors="coerce").fillna(0).astype(int).any():
            raise ValueError(f"Goal 2.8 rest {label} features include pilot-holdout subjects.")

    out_dir = Path(ensure_output(f"{eeg_cfg['outputs_dir']}/.keep", config)).parent
    signal_path = out_dir / "rest_signal_features.csv"
    qc_path = out_dir / "rest_qc_features.csv"
    signal_out.to_csv(signal_path, index=False)
    qc_out.to_csv(qc_path, index=False)

    manifest = {
        "task": "rest",
        "feature_version": "goal2_8_eeg_rest_spectral_v1",
        "subjects_attempted": len(targets),
        "subjects_signal": int(len(signal_out)),
        "subjects_qc": int(len(qc_out)),
        "signal_feature_columns": int(sum(1 for c in signal_out.columns if c.startswith("signal_"))),
        "block_reasons": qc.loc[qc["qc_feature_status"] != "ok", "qc_failure_reason"].value_counts().to_dict(),
        "signal_features": str(signal_path),
        "qc_features": str(qc_path),
    }
    (out_dir / "rest_feature_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest
