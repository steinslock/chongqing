"""Re-derive EEG epochs from raw BDF, driven by the paradigm specification.

Goal 2.7 read a v1 window cache that had been built with a hardcoded
`event_codes: ["22"]`, so the Oddball standard condition was absent and
target/standard ERP looked impossible. This module goes back to the raw
recordings and epochs every condition the specification declares.
"""

from __future__ import annotations

import re
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ..paradigm import load_paradigm_spec
from ..paradigm.spec import EegTaskSpec, ParadigmSpec
from .config import cv_subjects, ensure_output, load_goal_config, project_path

warnings.filterwarnings("ignore")

L_ID_RE = re.compile(r"(?<![A-Za-z0-9])L\d+(?![A-Za-z0-9])", re.IGNORECASE)


@dataclass
class SubjectEpochs:
    l_id: str
    status: str
    reason: str = ""
    counts: dict[str, int] | None = None
    rejected: int = 0
    total_candidate: int = 0
    duration_sec: float = float("nan")
    evoked: dict[str, np.ndarray] | None = None
    channels: list[str] | None = None
    times: np.ndarray | None = None


def extract_l_id(text: str) -> str:
    match = L_ID_RE.search(text)
    return match.group(0).upper() if match else ""


def subject_dirs(raw_root: Path, task_spec: EegTaskSpec, eeg_common: dict[str, Any]) -> dict[str, Path]:
    task_dir = raw_root / eeg_common["raw_dir"] / task_spec.raw_dir
    out: dict[str, Path] = {}
    if not task_dir.exists():
        return out
    for path in sorted(task_dir.glob("*")):
        if not path.is_dir():
            continue
        l_id = extract_l_id(path.name)
        if l_id and l_id not in out:
            out[l_id] = path
    return out


def _match_role(subject_dir: Path, patterns: list[str]) -> list[Path]:
    """Files for one role, across both naming conventions.

    Directories also hold a third BDF named after the participant. It is the
    same recording and is never matched here.
    """
    found: list[Path] = []
    for pattern in patterns:
        for path in sorted(subject_dir.glob(pattern)):
            if path not in found:
                found.append(path)
    return found


def process_subject(l_id: str, subject_dir: Path, task_spec: EegTaskSpec,
                    eeg_cfg: dict[str, Any], eeg_common: dict[str, Any]) -> SubjectEpochs:
    """Epoch one subject. Returns a status row even when it fails."""
    import mne

    mne.set_log_level("ERROR")

    data_files = _match_role(subject_dir, eeg_common["data_file_patterns"])
    evt_files = _match_role(subject_dir, eeg_common["event_file_patterns"])
    if not data_files:
        return SubjectEpochs(l_id, "blocked", "missing_data_bdf")
    if not evt_files:
        return SubjectEpochs(l_id, "blocked", "missing_event_bdf")

    try:
        raw = mne.io.read_raw_bdf(data_files[0], preload=True, verbose="ERROR")
        evt = mne.io.read_raw_bdf(evt_files[0], preload=False, verbose="ERROR")
    except Exception as exc:  # noqa: BLE001
        return SubjectEpochs(l_id, "blocked", f"read_error:{type(exc).__name__}")

    if raw.info["meas_date"] != evt.info["meas_date"]:
        return SubjectEpochs(l_id, "blocked", "event_data_meas_date_mismatch")

    expected_channels = list(eeg_common["channels"])
    if list(raw.ch_names) != expected_channels:
        return SubjectEpochs(l_id, "blocked", "unexpected_channel_set")

    duration = raw.n_times / raw.info["sfreq"]

    # Neuracle BDF returns microvolts labelled as volts; make them真 volts once.
    raw.apply_function(lambda x: x * float(eeg_cfg["bdf_to_volts_scale"]))
    raw.set_channel_types({name: "eeg" for name in raw.ch_names})
    try:
        raw.set_eeg_reference(list(eeg_cfg["reference"]), verbose="ERROR")
    except Exception as exc:  # noqa: BLE001
        return SubjectEpochs(l_id, "blocked", f"reference_error:{type(exc).__name__}")
    raw.filter(float(eeg_cfg["highpass_hz"]), float(eeg_cfg["lowpass_hz"]),
               fir_design="firwin", verbose="ERROR")

    codes = task_spec.codes_for_contrast()
    code_map = {code: index + 1 for index, code in enumerate(codes)}
    sfreq = raw.info["sfreq"]
    rows = [
        [int(round(float(onset) * sfreq)), 0, code_map[str(desc)]]
        for onset, desc in zip(evt.annotations.onset, evt.annotations.description)
        if str(desc) in code_map
    ]
    if not rows:
        return SubjectEpochs(l_id, "blocked", "no_spec_codes_in_event_file", duration_sec=duration)
    events = np.array(sorted(rows), dtype=int)

    tmin, tmax = task_spec.epoch_window
    baseline = task_spec.baseline
    threshold = eeg_cfg["reject_peak_to_peak_volts"]
    if isinstance(threshold, dict):
        threshold = threshold[task_spec.task]
    # Blinks dominate the frontopolar channels; keep them in the data but let
    # the centro-parietal channels decide whether an epoch survives.
    excluded = [c for c in eeg_cfg.get("reject_exclude_channels", []) if c in raw.ch_names]
    reject_picks = [c for c in raw.ch_names if c not in excluded]
    try:
        epochs = mne.Epochs(
            raw, events, event_id=code_map, tmin=tmin, tmax=tmax, baseline=baseline,
            preload=True, verbose="ERROR",
        )
        if reject_picks:
            keep = epochs.copy().pick(reject_picks)
            keep.drop_bad(reject=dict(eeg=float(threshold)), verbose="ERROR")
            epochs = epochs[[i for i, log in enumerate(keep.drop_log) if not log]]
    except Exception as exc:  # noqa: BLE001
        return SubjectEpochs(l_id, "blocked", f"epoch_error:{type(exc).__name__}", duration_sec=duration)

    candidate = len(events)
    kept = len(epochs)
    minimums = dict(eeg_cfg.get("min_trials", {}).get(task_spec.task, {}) or {})
    counts = {code: int(len(epochs[code])) if code in epochs.event_id else 0 for code in codes}
    for code, minimum in minimums.items():
        if counts.get(str(code), 0) < int(minimum):
            return SubjectEpochs(l_id, "blocked", f"too_few_trials_code_{code}",
                                 counts=counts, rejected=candidate - kept,
                                 total_candidate=candidate, duration_sec=duration)

    epochs.resample(int(eeg_cfg["resample_hz"]), verbose="ERROR")
    evoked = {code: epochs[code].average().get_data().astype(np.float32) for code in codes}
    return SubjectEpochs(
        l_id, "ok", "", counts=counts, rejected=candidate - kept, total_candidate=candidate,
        duration_sec=duration, evoked=evoked, channels=list(epochs.ch_names),
        times=epochs.times.astype(np.float32),
    )


def build_task_epochs(task: str, config_path: str | Path = "configs/goal2_8/eeg.yaml",
                      limit: int | None = None, n_jobs: int | None = None,
                      spec: ParadigmSpec | None = None) -> dict[str, Any]:
    """Epoch one EEG task across CV subjects and write the ERP archive."""
    from joblib import Parallel, delayed

    config = load_goal_config(config_path)
    spec = spec or load_paradigm_spec(config["paths"]["paradigm_spec"])
    task_spec = spec.eeg(task)
    eeg_cfg = config["eeg"]
    eeg_common = spec.eeg_common

    raw_root = project_path(config["paths"]["raw_data_dir"])
    available = subject_dirs(raw_root, task_spec, eeg_common)
    split = cv_subjects(config)
    cv_ids = [str(x) for x in split["L_id"]]
    targets = [(l_id, available[l_id]) for l_id in cv_ids if l_id in available]
    if limit:
        targets = targets[:limit]

    jobs = int(n_jobs if n_jobs is not None else config.get("run", {}).get("n_jobs", 1))
    if jobs == 1:
        results = [process_subject(l, d, task_spec, eeg_cfg, eeg_common) for l, d in targets]
    else:
        results = Parallel(n_jobs=jobs, backend="loky", verbose=5)(
            delayed(process_subject)(l, d, task_spec, eeg_cfg, eeg_common) for l, d in targets
        )

    codes = task_spec.codes_for_contrast()
    ok = [r for r in results if r.status == "ok"]
    index_rows: list[dict[str, Any]] = []
    for r in results:
        row: dict[str, Any] = {
            "L_id": r.l_id, "task": task, "status": r.status, "reason": r.reason,
            "duration_sec": r.duration_sec, "candidate_trials": r.total_candidate,
            "rejected_trials": r.rejected,
            "rejected_rate": (r.rejected / r.total_candidate) if r.total_candidate else np.nan,
        }
        for code in codes:
            row[f"n_trials_code_{code}"] = (r.counts or {}).get(code, 0)
            row[f"condition_code_{code}"] = task_spec.condition_of(code)
        index_rows.append(row)
    index = pd.DataFrame(index_rows)

    out_dir = Path(ensure_output(f"{eeg_cfg['outputs_dir']}/.keep", config)).parent
    index_path = out_dir / f"{task}_erp_index.csv"
    index.to_csv(index_path, index=False)

    archive_path = out_dir / f"{task}_erp.npz"
    if ok:
        arrays = {f"erp_{code}": np.stack([r.evoked[code] for r in ok]) for code in codes}
        np.savez_compressed(
            archive_path,
            l_ids=np.array([r.l_id for r in ok]),
            channels=np.array(ok[0].channels),
            times=ok[0].times,
            **arrays,
        )

    return {
        "task": task,
        "preprocessing_version": eeg_cfg["preprocessing_version"],
        "subjects_attempted": len(targets),
        "subjects_ok": len(ok),
        "subjects_blocked": len(results) - len(ok),
        "codes": codes,
        "conditions": {code: task_spec.condition_of(code) for code in codes},
        "index_csv": str(index_path),
        "erp_npz": str(archive_path) if ok else "",
        "block_reasons": index.loc[index["status"] != "ok", "reason"].value_counts().to_dict(),
    }
