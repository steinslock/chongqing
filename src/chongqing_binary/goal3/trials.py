"""Single-trial Oddball epochs for Goal 3.

Goal 2.8 epoched the raw BDF correctly and then kept only the condition
averages, so `artifacts/goal2_8/eeg/oddball_erp.npz` holds one evoked response
per subject per condition and no single trials. A deep model needs the trials,
so this module rebuilds them.

It is a re-derivation, not a new pipeline. Every preprocessing decision is read
from `configs/goal2_8/eeg.yaml` and `configs/goal2_8/paradigm_spec.yaml`
unchanged, and the operation order is the one in
`chongqing_binary.goal2_8.eeg_epochs.process_subject`. The proof that it is the
same data is not the shared config but the numerical identity check in
`verify_cache`: averaging these trials by condition must reproduce the Goal 2.8
evoked arrays element-wise.
"""

from __future__ import annotations

import json
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ..goal2_8.eeg_epochs import subject_dirs, _match_role
from ..paradigm import load_paradigm_spec
from ..paradigm.spec import EegTaskSpec, ParadigmSpec
from .config import ensure_output, load_goal_config, project_path

warnings.filterwarnings("ignore")

TASK = "oddball"


@dataclass
class SubjectTrials:
    """One subject's outcome. A failure still returns a row."""

    l_id: str
    status: str
    reason: str = ""
    n_events: int = 0
    n_constructed: int = 0
    n_kept: int = 0
    counts: dict[str, int] = field(default_factory=dict)
    duration_sec: float = float("nan")
    construction_drops: int = 0
    codes: np.ndarray | None = None
    onsets: np.ndarray | None = None
    channels: list[str] | None = None
    times: np.ndarray | None = None


def _epoch_subject(l_id: str, subject_dir: Path, task_spec: EegTaskSpec,
                   eeg_cfg: dict[str, Any], eeg_common: dict[str, Any],
                   out_dir: Path) -> SubjectTrials:
    """Re-run the Goal 2.8 epoching and keep the trials instead of the average.

    The sequence below mirrors `goal2_8.eeg_epochs.process_subject` step for
    step. Any divergence would show up as a mismatch in `verify_cache`.
    """
    import mne

    mne.set_log_level("ERROR")

    data_files = _match_role(subject_dir, eeg_common["data_file_patterns"])
    evt_files = _match_role(subject_dir, eeg_common["event_file_patterns"])
    if not data_files:
        return SubjectTrials(l_id, "blocked", "missing_data_bdf")
    if not evt_files:
        return SubjectTrials(l_id, "blocked", "missing_event_bdf")

    try:
        raw = mne.io.read_raw_bdf(data_files[0], preload=True, verbose="ERROR")
        evt = mne.io.read_raw_bdf(evt_files[0], preload=False, verbose="ERROR")
    except Exception as exc:  # noqa: BLE001
        return SubjectTrials(l_id, "blocked", f"read_error:{type(exc).__name__}")

    if raw.info["meas_date"] != evt.info["meas_date"]:
        return SubjectTrials(l_id, "blocked", "event_data_meas_date_mismatch")
    if list(raw.ch_names) != list(eeg_common["channels"]):
        return SubjectTrials(l_id, "blocked", "unexpected_channel_set")

    duration = raw.n_times / raw.info["sfreq"]

    raw.apply_function(lambda x: x * float(eeg_cfg["bdf_to_volts_scale"]))
    raw.set_channel_types({name: "eeg" for name in raw.ch_names})
    try:
        raw.set_eeg_reference(list(eeg_cfg["reference"]), verbose="ERROR")
    except Exception as exc:  # noqa: BLE001
        return SubjectTrials(l_id, "blocked", f"reference_error:{type(exc).__name__}")
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
        return SubjectTrials(l_id, "blocked", "no_spec_codes_in_event_file", duration_sec=duration)
    events = np.array(sorted(rows), dtype=int)

    tmin, tmax = task_spec.epoch_window
    baseline = task_spec.baseline
    threshold = eeg_cfg["reject_peak_to_peak_volts"]
    if isinstance(threshold, dict):
        threshold = threshold[task_spec.task]
    excluded = [c for c in eeg_cfg.get("reject_exclude_channels", []) if c in raw.ch_names]
    reject_picks = [c for c in raw.ch_names if c not in excluded]
    try:
        epochs = mne.Epochs(
            raw, events, event_id=code_map, tmin=tmin, tmax=tmax, baseline=baseline,
            preload=True, verbose="ERROR",
        )
        n_constructed = len(epochs)
        if reject_picks:
            keep = epochs.copy().pick(reject_picks)
            keep.drop_bad(reject=dict(eeg=float(threshold)), verbose="ERROR")
            epochs = epochs[[i for i, log in enumerate(keep.drop_log) if not log]]
    except Exception as exc:  # noqa: BLE001
        return SubjectTrials(l_id, "blocked", f"epoch_error:{type(exc).__name__}", duration_sec=duration)

    minimums = dict(eeg_cfg.get("min_trials", {}).get(task_spec.task, {}) or {})
    counts = {code: int(len(epochs[code])) if code in epochs.event_id else 0 for code in codes}
    for code, minimum in minimums.items():
        if counts.get(str(code), 0) < int(minimum):
            return SubjectTrials(l_id, "blocked", f"too_few_trials_code_{code}", counts=counts,
                                 n_events=len(events), n_constructed=n_constructed,
                                 duration_sec=duration)

    epochs.resample(int(eeg_cfg["resample_hz"]), verbose="ERROR")

    inverse = {value: key for key, value in code_map.items()}
    data = epochs.get_data().astype(np.float32)
    trial_codes = np.array([inverse[int(v)] for v in epochs.events[:, 2]], dtype="<U4")
    onsets = epochs.events[:, 0].astype(np.int64)

    out_dir.mkdir(parents=True, exist_ok=True)
    np.save(out_dir / f"{l_id}.npy", data)

    return SubjectTrials(
        l_id, "ok", "", n_events=len(events), n_constructed=n_constructed,
        n_kept=len(epochs), counts=counts, duration_sec=duration,
        construction_drops=len(events) - n_constructed,
        codes=trial_codes, onsets=onsets, channels=list(epochs.ch_names),
        times=epochs.times.astype(np.float32),
    )


def build_trial_cache(config_path: str | Path = "configs/goal3/common.yaml",
                      limit: int | None = None, n_jobs: int = 32,
                      spec: ParadigmSpec | None = None) -> dict[str, Any]:
    """Epoch every Goal 2.8 Oddball subject and store the single trials."""
    from joblib import Parallel, delayed

    config = load_goal_config(config_path)
    eeg_config = load_goal_config(config["paths"]["eeg_preprocessing_config"])
    spec = spec or load_paradigm_spec(eeg_config["paths"]["paradigm_spec"])
    task_spec = spec.eeg(TASK)
    eeg_cfg = eeg_config["eeg"]
    eeg_common = spec.eeg_common

    raw_root = project_path(eeg_config["paths"]["raw_data_dir"])
    available = subject_dirs(raw_root, task_spec, eeg_common)

    # The cohort is Goal 2.8's, so the comparison is exact by construction and
    # not by a filter that could drift.
    reference_index = pd.read_csv(project_path(config["paths"]["goal2_8_erp_index"]), dtype={"L_id": str})
    cohort = [str(x) for x in reference_index.loc[reference_index["status"] == "ok", "L_id"]]
    targets = [(l_id, available[l_id]) for l_id in cohort if l_id in available]
    missing = [l_id for l_id in cohort if l_id not in available]
    if limit:
        targets = targets[:limit]

    out_dir = project_path(config["paths"]["trial_cache_dir"])
    shard_dir = out_dir / "subjects"
    if n_jobs == 1:
        results = [_epoch_subject(l, d, task_spec, eeg_cfg, eeg_common, shard_dir) for l, d in targets]
    else:
        results = Parallel(n_jobs=n_jobs, backend="loky", verbose=5)(
            delayed(_epoch_subject)(l, d, task_spec, eeg_cfg, eeg_common, shard_dir)
            for l, d in targets
        )

    ok = [r for r in results if r.status == "ok"]
    status_rows = [
        {
            "L_id": r.l_id, "task": TASK, "status": r.status, "reason": r.reason,
            "duration_sec": r.duration_sec, "n_events": r.n_events,
            "n_constructed": r.n_constructed, "n_kept": r.n_kept,
            "construction_drops": r.construction_drops,
            **{f"n_trials_code_{code}": r.counts.get(code, 0) for code in task_spec.codes_for_contrast()},
        }
        for r in results
    ]
    status = pd.DataFrame(status_rows)
    status.to_csv(ensure_output(out_dir / f"{TASK}_subject_status.csv", config), index=False)

    n_total = int(sum(r.n_kept for r in ok))
    n_channels = len(ok[0].channels)
    n_times = len(ok[0].times)
    array_path = out_dir / f"{TASK}_trials.npy"
    memmap = np.lib.format.open_memmap(
        array_path, mode="w+", dtype=np.float32, shape=(n_total, n_channels, n_times)
    )
    index_rows: list[dict[str, Any]] = []
    cursor = 0
    for r in ok:
        block = np.load(shard_dir / f"{r.l_id}.npy")
        memmap[cursor:cursor + block.shape[0]] = block
        for offset in range(block.shape[0]):
            index_rows.append({
                "row": cursor + offset,
                "L_id": r.l_id,
                "code": r.codes[offset],
                "condition": task_spec.condition_of(r.codes[offset]),
                "trial_in_recording": offset,
                "onset_sample": int(r.onsets[offset]),
            })
        cursor += block.shape[0]
    memmap.flush()
    del memmap
    for r in ok:
        (shard_dir / f"{r.l_id}.npy").unlink(missing_ok=True)
    shard_dir.rmdir()

    index = pd.DataFrame(index_rows)
    index.to_csv(ensure_output(out_dir / f"{TASK}_trial_index.csv", config), index=False)
    np.save(out_dir / f"{TASK}_channels.npy", np.array(ok[0].channels))
    np.save(out_dir / f"{TASK}_times.npy", ok[0].times)

    manifest = {
        "task": TASK,
        "preprocessing_version": eeg_cfg["preprocessing_version"],
        "preprocessing_config": str(config["paths"]["eeg_preprocessing_config"]),
        "note": "re-derivation of the Goal 2.8 epoching, keeping single trials",
        "cohort_source": str(config["paths"]["goal2_8_erp_index"]),
        "cohort_requested": len(cohort),
        "cohort_missing_raw_dir": missing,
        "subjects_attempted": len(targets),
        "subjects_ok": len(ok),
        "subjects_blocked": len(results) - len(ok),
        "block_reasons": status.loc[status["status"] != "ok", "reason"].value_counts().to_dict(),
        "n_trials": n_total,
        "n_channels": n_channels,
        "n_times": n_times,
        "condition_counts": index["condition"].value_counts().to_dict(),
        # An epoch that MNE cannot construct shifts the drop_log indices the
        # Goal 2.8 rejection step reads. Recorded so the identity check has
        # something to be checked against rather than assumed.
        "subjects_with_construction_drops": int((status["construction_drops"] > 0).sum()),
        "total_construction_drops": int(status["construction_drops"].sum()),
        "array": str(array_path),
    }
    with ensure_output(out_dir / f"{TASK}_trial_manifest.json", config).open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, ensure_ascii=False)
    return manifest


def verify_cache(config_path: str | Path = "configs/goal3/common.yaml",
                 relative_tolerance: float = 4e-7) -> dict[str, Any]:
    """The measurement gate: are these the Goal 2.8 epochs?

    Layer one is numerical identity. Averaging the trial cache by condition must
    reproduce the stored Goal 2.8 evoked arrays, subject by subject, over the
    same subject set.

    The criterion is **relative**, not absolute. Goal 2.8 stored its evoked
    arrays as float32, so the residual scales with the amplitude of the
    recording rather than being a fixed voltage: over all 3640
    subject-condition pairs, `max|difference| / max|reference|` lies between
    3.4e-8 and 1.3e-7, one float32 epsilon (1.19e-7), while the absolute
    residual spans 1.3e-13 to 2.4e-10 only because one blink-contaminated
    recording is three orders of magnitude larger than the rest. An absolute
    tolerance would test amplitude, not identity. Recorded as amendment 2 in
    `reports/goal3_method_design.md`.

    Layer two is the paradigm effect recomputed from the trials: parietal
    maximum, Fz negative, Pz P3b with Cohen d above 0.8 in more than 80 percent
    of subjects.
    """
    config = load_goal_config(config_path)
    cache_dir = project_path(config["paths"]["trial_cache_dir"])
    index = pd.read_csv(cache_dir / f"{TASK}_trial_index.csv", dtype={"L_id": str, "code": str})
    trials = np.load(cache_dir / f"{TASK}_trials.npy", mmap_mode="r")
    channels = [str(c) for c in np.load(cache_dir / f"{TASK}_channels.npy")]
    times = np.load(cache_dir / f"{TASK}_times.npy")

    reference = np.load(project_path(config["paths"]["goal2_8_erp_npz"]), allow_pickle=True)
    ref_ids = [str(x) for x in reference["l_ids"]]
    ref_channels = [str(c) for c in reference["channels"]]
    ref_times = np.asarray(reference["times"])
    # A compressed NpzFile decompresses the whole array on every key access, so
    # the evoked arrays are materialised once instead of inside the subject loop.
    ref_erp = {key[len("erp_"):]: reference[key] for key in reference.files if key.startswith("erp_")}

    checks: dict[str, Any] = {
        "subjects_cache": int(index["L_id"].nunique()),
        "subjects_reference": len(ref_ids),
        "subject_sets_identical": sorted(set(index["L_id"])) == sorted(ref_ids),
        "channels_identical": channels == ref_channels,
        "times_identical": bool(np.array_equal(times, ref_times)),
    }

    position = {l_id: i for i, l_id in enumerate(ref_ids)}
    excluded = set(str(c) for c in config.get("deep", {}).get("input_channels_excluded", []))
    kept_idx = [i for i, name in enumerate(channels) if name not in excluded]
    dropped_idx = [i for i, name in enumerate(channels) if name in excluded]

    worst_relative, worst_absolute, worst_subject = 0.0, 0.0, ""
    peak_kept, peak_dropped = 0.0, 0.0
    mismatches: list[str] = []
    evoked_by_subject: dict[str, dict[str, np.ndarray]] = {}

    # A subject's trials were written contiguously, so each block is read once in
    # order and split by condition in memory. Selecting conditions separately
    # would page the same block in twice, scattered, which on a 7.6 GB memmap
    # costs minutes rather than seconds.
    for l_id, rows in index.groupby("L_id", sort=False):
        start, stop = int(rows["row"].min()), int(rows["row"].max()) + 1
        if stop - start != len(rows):
            mismatches.append(f"{l_id}:non_contiguous_rows")
            continue
        raw_block = np.asarray(trials[start:stop])
        magnitude = np.abs(raw_block)
        peak_kept = max(peak_kept, float(magnitude[:, kept_idx].max()) * 1e6)
        if dropped_idx:
            peak_dropped = max(peak_dropped, float(magnitude[:, dropped_idx].max()) * 1e6)

        block = raw_block.astype(np.float64)
        codes_here = rows["code"].to_numpy()
        evoked = {code: block[codes_here == code].mean(axis=0) for code in np.unique(codes_here)}
        evoked_by_subject[str(l_id)] = evoked
        if l_id not in position:
            mismatches.append(f"{l_id}:absent_from_reference")
            continue
        i = position[l_id]
        for code, mine in evoked.items():
            theirs = ref_erp[code][i].astype(np.float64)
            delta = float(np.abs(mine - theirs).max())
            relative = delta / max(float(np.abs(theirs).max()), 1e-12)
            worst_absolute = max(worst_absolute, delta)
            if relative > worst_relative:
                worst_relative, worst_subject = relative, f"{l_id}/code{code}"
            if relative > relative_tolerance:
                mismatches.append(f"{l_id}/code{code}:{relative:.3e}")

    checks["max_relative_difference"] = worst_relative
    checks["max_relative_difference_in_float32_eps"] = worst_relative / float(np.finfo(np.float32).eps)
    checks["max_abs_difference_volts"] = worst_absolute
    checks["max_abs_difference_uv"] = worst_absolute * 1e6
    checks["relative_tolerance"] = relative_tolerance
    checks["worst_subject"] = worst_subject
    checks["n_mismatched"] = len(mismatches)
    checks["mismatches"] = mismatches[:20]
    checks["identity_gate_passed"] = bool(
        not mismatches and checks["subject_sets_identical"]
        and checks["channels_identical"] and checks["times_identical"]
    )

    # What the deep model will actually read, and what it will not.
    amplitude = {
        "model_input_channels_excluded": sorted(excluded),
        "model_input_channels": len(kept_idx),
        "max_abs_uv_model_input": peak_kept,
        "max_abs_uv_excluded_channels": peak_dropped,
        "note": ("the cache keeps all 32 channels and is identical to Goal 2.8; "
                 "the exclusion is a model-input choice, see amendment 1"),
    }

    spec = load_paradigm_spec(load_goal_config(config["paths"]["eeg_preprocessing_config"])["paths"]["paradigm_spec"])
    task_spec = spec.eeg(TASK)
    contrast = task_spec.primary_contrast or {}
    minuend = str(contrast.get("minuend", "22"))
    subtrahend = str(contrast.get("subtrahend", "11"))
    window = task_spec.raw["erp_windows"]["p300"]
    mask = (times >= float(window[0])) & (times <= float(window[1]))

    ids = sorted(evoked_by_subject)
    diff = np.stack([evoked_by_subject[i][minuend] - evoked_by_subject[i][subtrahend] for i in ids])

    validity: dict[str, Any] = {"n_subjects": len(ids), "p300_window_sec": [float(w) for w in window]}
    for name in ["Pz", "Cz", "Fz", "Oz"]:
        values = diff[:, channels.index(name)][:, mask].mean(axis=1) * 1e6
        validity[f"{name}_uv_mean"] = float(values.mean())
        validity[f"{name}_cohens_d"] = float(values.mean() / values.std(ddof=1))
        validity[f"{name}_fraction_positive"] = float((values > 0).mean())
    topography = diff[:, :, mask].mean(axis=(0, 2)) * 1e6
    validity["peak_channel"] = channels[int(np.argmax(topography))]
    validity["parietal_maximum"] = bool(validity["peak_channel"] in task_spec.raw["erp_channels"])
    validity["frontal_negative"] = bool(validity["Fz_uv_mean"] < 0)
    validity["validity_gate_passed"] = bool(
        validity["parietal_maximum"] and validity["frontal_negative"]
        and validity["Pz_uv_mean"] > 0 and validity["Pz_cohens_d"] > 0.8
        and validity["Pz_fraction_positive"] > 0.8
    )

    counts = index.groupby(["L_id", "condition"]).size().unstack(fill_value=0)
    trial_counts = {f"{column}_{stat}": float(getattr(counts[column], stat)())
                    for column in counts.columns for stat in ["mean", "min", "max"]}

    report = {
        "identity": checks,
        "amplitude": amplitude,
        "paradigm_validity": validity,
        "trial_counts": trial_counts,
        "gate_passed": bool(checks["identity_gate_passed"] and validity["validity_gate_passed"]),
    }
    with ensure_output(cache_dir / f"{TASK}_cache_verification.json", config).open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    return report
