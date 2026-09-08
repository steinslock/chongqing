"""Subject-level behavioural features for Goal 2.9.

Goal 2.8 measured what the brain did during each task and found no increment
over demographics. It never measured what the subject did. These are the
keypresses: accuracy, reaction time, signal-detection sensitivity, vigilance
decrement, and reward reactivity in the one reward paradigm the battery has.

Every structural fact comes from `configs/goal2_8/paradigm_spec.yaml`. The
match/non-match condition is derived from the stimulus sequence rather than the
logged condition column, because the logged column is meaningless on the
block-initial trial of the Bikom 1BACK; the two agree exactly everywhere else
and that agreement is recorded in QC.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ..paradigm import load_paradigm_spec
from ..paradigm.spec import BehaviourTaskSpec, ParadigmSpec
from .config import cv_subjects, ensure_output, load_goal_config, project_path
from .behaviour_io import (
    collect_subject_dirs,
    eprime_trial_files,
    psychopy_trial_files,
    read_trials,
)

FEATURE_VERSION = "goal2_9_behaviour_trial_level_v1"


# -- small statistics ------------------------------------------------------

def _safe(value: float) -> float:
    return float(value) if np.isfinite(value) else float("nan")


def _mean(values: Any) -> float:
    array = np.asarray(pd.to_numeric(pd.Series(list(values)), errors="coerce"), dtype=float)
    array = array[np.isfinite(array)]
    return float(array.mean()) if array.size else float("nan")


def _describe_rt(prefix: str, values: pd.Series) -> dict[str, float]:
    """Central tendency, dispersion and shape of a reaction-time sample."""
    array = np.asarray(pd.to_numeric(values, errors="coerce"), dtype=float)
    array = array[np.isfinite(array)]
    out: dict[str, float] = {f"{prefix}_n": float(array.size)}
    if array.size == 0:
        return out
    mean = float(array.mean())
    std = float(array.std(ddof=1)) if array.size > 1 else float("nan")
    out[f"{prefix}_mean_sec"] = mean
    out[f"{prefix}_median_sec"] = float(np.median(array))
    out[f"{prefix}_sd_sec"] = _safe(std)
    out[f"{prefix}_cv"] = _safe(std / mean) if mean else float("nan")
    out[f"{prefix}_iqr_sec"] = float(np.percentile(array, 75) - np.percentile(array, 25))
    out[f"{prefix}_min_sec"] = float(array.min())
    out[f"{prefix}_max_sec"] = float(array.max())
    if array.size > 2 and std and np.isfinite(std) and std > 0:
        centred = (array - mean) / std
        out[f"{prefix}_skew"] = float((centred ** 3).mean())
    return out


def _rate_with_loglinear(hits: float, n: float) -> float:
    """Hit/false-alarm rate with the log-linear correction.

    Keeps d-prime finite when a subject is at ceiling or floor, which happens
    often here because the 1BACK is easy and the Oddball has only 50 targets.
    """
    if n <= 0:
        return float("nan")
    return (hits + 0.5) / (n + 1.0)


def _norm_ppf(p: float) -> float:
    """Inverse standard normal CDF (Acklam), so scipy is not needed here."""
    if not np.isfinite(p) or p <= 0.0 or p >= 1.0:
        return float("nan")
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00]
    plow, phigh = 0.02425, 1 - 0.02425
    if p < plow:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    if p > phigh:
        q = math.sqrt(-2 * math.log(1 - p))
        return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    q = p - 0.5
    r = q * q
    return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)


def _signal_detection(prefix: str, hits: float, n_signal: float,
                      false_alarms: float, n_noise: float) -> dict[str, float]:
    out: dict[str, float] = {}
    hit_rate = _rate_with_loglinear(hits, n_signal)
    fa_rate = _rate_with_loglinear(false_alarms, n_noise)
    if np.isfinite(hit_rate):
        out[f"{prefix}_hit_rate"] = float(hits / n_signal) if n_signal else float("nan")
    if np.isfinite(fa_rate):
        out[f"{prefix}_false_alarm_rate"] = float(false_alarms / n_noise) if n_noise else float("nan")
    z_hit, z_fa = _norm_ppf(hit_rate), _norm_ppf(fa_rate)
    if np.isfinite(z_hit) and np.isfinite(z_fa):
        out[f"{prefix}_dprime"] = float(z_hit - z_fa)
        out[f"{prefix}_criterion"] = float(-0.5 * (z_hit + z_fa))
    return out


def _slope_over_blocks(values: list[float]) -> float:
    """Linear slope of a per-block series, in units per block."""
    array = np.asarray(values, dtype=float)
    mask = np.isfinite(array)
    if mask.sum() < 2:
        return float("nan")
    x = np.arange(array.size, dtype=float)[mask]
    return float(np.polyfit(x, array[mask], 1)[0])


# -- condition derivation --------------------------------------------------

def derive_nback_conditions(trials: pd.DataFrame) -> pd.DataFrame:
    """Label each 1BACK trial match/non-match from the stimulus sequence.

    The block-initial trial has no predecessor and is labelled `block_initial`.
    Its logged condition is empty on Yiruid but arbitrary on Bikom, which is why
    the sequence rather than the log is the authority.
    """
    out = trials.copy()
    derived: list[str] = []
    for _, block in out.groupby("block", sort=True, dropna=False):
        previous: str | None = None
        for stimulus in block["stimulus"]:
            if previous is None:
                derived.append("block_initial")
            else:
                derived.append("match" if stimulus == previous else "non_match")
            previous = stimulus
    order = out.sort_values(["block", "trial"], kind="stable").index
    out.loc[order, "derived_condition"] = pd.Series(derived, index=order).values
    return out


# -- per-task features -----------------------------------------------------

def nback_features(trials: pd.DataFrame, bspec: BehaviourTaskSpec) -> tuple[dict[str, float], dict[str, Any]]:
    """Working memory: accuracy, sensitivity, reaction time and its drift."""
    qc: dict[str, Any] = {}
    labelled = derive_nback_conditions(trials.sort_values(["block", "trial"], kind="stable"))
    usable = labelled[labelled["derived_condition"] != "block_initial"].copy()
    qc["qc_trials_total"] = int(len(labelled))
    qc["qc_trials_used"] = int(len(usable))
    qc["qc_blocks"] = int(labelled["block"].nunique(dropna=True))

    logged = usable["condition"].astype(str)
    comparable = logged.isin(("match", "non_match"))
    qc["qc_condition_agreement"] = (
        float((logged[comparable] == usable.loc[comparable, "derived_condition"]).mean())
        if comparable.any() else float("nan"))
    qc["qc_condition_comparable_trials"] = int(comparable.sum())

    if usable.empty:
        return {}, qc

    match = usable[usable["derived_condition"] == "match"]
    non_match = usable[usable["derived_condition"] == "non_match"]
    responded = usable["response"].astype(str) != ""
    # Response "2" means "same as the previous picture" on both devices.
    said_match = usable["response"].astype(str) == "2"
    correct = ((usable["derived_condition"] == "match") == said_match) & responded

    out: dict[str, float] = {
        "signal_n_trials": float(len(usable)),
        "signal_n_match": float(len(match)),
        "signal_n_non_match": float(len(non_match)),
        "signal_response_rate": float(responded.mean()),
        "signal_omission_rate": float(1.0 - responded.mean()),
        "signal_accuracy": float(correct.mean()),
    }
    if len(match):
        out["signal_accuracy_match"] = float(correct[usable["derived_condition"] == "match"].mean())
    if len(non_match):
        out["signal_accuracy_non_match"] = float(correct[usable["derived_condition"] == "non_match"].mean())
    if "signal_accuracy_match" in out and "signal_accuracy_non_match" in out:
        out["signal_accuracy_match_minus_non_match"] = (
            out["signal_accuracy_match"] - out["signal_accuracy_non_match"])

    out.update(_signal_detection(
        "signal", hits=float((said_match & (usable["derived_condition"] == "match")).sum()),
        n_signal=float(len(match)),
        false_alarms=float((said_match & (usable["derived_condition"] == "non_match")).sum()),
        n_noise=float(len(non_match))))

    correct_rt = usable.loc[correct, "rt_sec"]
    out.update(_describe_rt("signal_rt_correct", correct_rt))
    out.update(_describe_rt("signal_rt_all", usable.loc[responded, "rt_sec"]))
    match_rt = _mean(usable.loc[correct & (usable["derived_condition"] == "match"), "rt_sec"])
    non_match_rt = _mean(usable.loc[correct & (usable["derived_condition"] == "non_match"), "rt_sec"])
    out["signal_rt_match_mean_sec"] = match_rt
    out["signal_rt_non_match_mean_sec"] = non_match_rt
    out["signal_rt_match_minus_non_match_sec"] = _safe(match_rt - non_match_rt)

    # Practice or fatigue across the two blocks, and drift within them.
    per_block_acc: list[float] = []
    per_block_rt: list[float] = []
    for _, block in usable.groupby("block", sort=True, dropna=False):
        block_correct = correct.loc[block.index]
        per_block_acc.append(float(block_correct.mean()))
        per_block_rt.append(_mean(block.loc[block_correct, "rt_sec"]))
    if len(per_block_acc) >= 2:
        out["signal_accuracy_last_minus_first_block"] = _safe(per_block_acc[-1] - per_block_acc[0])
        out["signal_rt_last_minus_first_block_sec"] = _safe(per_block_rt[-1] - per_block_rt[0])
    if len(per_block_acc) >= 3:
        # With the two blocks this task normally has, the slope is the
        # last-minus-first difference again, so only emit it when it adds.
        out["signal_accuracy_block_slope"] = _slope_over_blocks(per_block_acc)
        out["signal_rt_block_slope_sec"] = _slope_over_blocks(per_block_rt)

    # Post-error slowing: the classic control adjustment index.
    after_error: list[float] = []
    after_correct: list[float] = []
    for _, block in usable.groupby("block", sort=True, dropna=False):
        flags = correct.loc[block.index].tolist()
        rts = block["rt_sec"].tolist()
        for i in range(1, len(flags)):
            if not np.isfinite(rts[i]):
                continue
            (after_correct if flags[i - 1] else after_error).append(rts[i])
    if after_error and after_correct:
        out["signal_post_error_slowing_sec"] = _safe(float(np.mean(after_error)) - float(np.mean(after_correct)))
    out["signal_n_after_error_trials"] = float(len(after_error))
    return out, qc


def oddball_features(trials: pd.DataFrame, bspec: BehaviourTaskSpec) -> tuple[dict[str, float], dict[str, Any]]:
    """Attention and impulse control: hits, false alarms, and vigilance drift."""
    qc: dict[str, Any] = {}
    ordered = trials.sort_values(["block", "trial"], kind="stable")
    qc["qc_trials_total"] = int(len(ordered))
    qc["qc_blocks"] = int(ordered["block"].nunique(dropna=True))
    if ordered.empty:
        return {}, qc

    is_target = ordered["stimulus"].astype(str) == "target"
    responded = ordered["response"].astype(str) != ""
    qc["qc_n_targets"] = int(is_target.sum())
    qc["qc_n_standards"] = int((~is_target).sum())
    if not is_target.any():
        qc["qc_failure_reason"] = "no_target_trials"
        return {}, qc

    hits = int((is_target & responded).sum())
    false_alarms = int((~is_target & responded).sum())
    out: dict[str, float] = {
        "signal_n_trials": float(len(ordered)),
        "signal_n_targets": float(is_target.sum()),
        "signal_n_standards": float((~is_target).sum()),
        "signal_response_rate": float(responded.mean()),
        "signal_miss_rate": float(1.0 - hits / max(1, int(is_target.sum()))),
    }
    out.update(_signal_detection("signal", hits=float(hits), n_signal=float(is_target.sum()),
                                 false_alarms=float(false_alarms), n_noise=float((~is_target).sum())))
    out.update(_describe_rt("signal_rt_hit", ordered.loc[is_target & responded, "rt_sec"]))
    # Most subjects commit no false alarm at all, so only the count and the mean
    # survive as columns; higher moments would be missing for most of the cohort.
    false_alarm_rt = ordered.loc[~is_target & responded, "rt_sec"]
    out["signal_rt_false_alarm_n"] = float(pd.to_numeric(false_alarm_rt, errors="coerce").notna().sum())
    out["signal_rt_false_alarm_mean_sec"] = _mean(false_alarm_rt)

    per_block_hit: list[float] = []
    per_block_fa: list[float] = []
    per_block_rt: list[float] = []
    for _, block in ordered.groupby("block", sort=True, dropna=False):
        block_target = block["stimulus"].astype(str) == "target"
        block_resp = block["response"].astype(str) != ""
        per_block_hit.append(float((block_target & block_resp).sum() / max(1, int(block_target.sum()))))
        per_block_fa.append(float((~block_target & block_resp).sum() / max(1, int((~block_target).sum()))))
        per_block_rt.append(_mean(block.loc[block_target & block_resp, "rt_sec"]))
    out["signal_hit_rate_block_slope"] = _slope_over_blocks(per_block_hit)
    out["signal_false_alarm_block_slope"] = _slope_over_blocks(per_block_fa)
    out["signal_rt_hit_block_slope_sec"] = _slope_over_blocks(per_block_rt)
    if len(per_block_hit) >= 2:
        half = len(per_block_hit) // 2
        out["signal_hit_rate_second_minus_first_half"] = _safe(
            _mean(per_block_hit[half:]) - _mean(per_block_hit[:half]))
        out["signal_rt_hit_second_minus_first_half_sec"] = _safe(
            _mean(per_block_rt[half:]) - _mean(per_block_rt[:half]))
    return out, qc


def doors_features(trials: pd.DataFrame, bspec: BehaviourTaskSpec) -> tuple[dict[str, float], dict[str, Any]]:
    """Reward reactivity: win-stay/lose-shift and post-feedback slowing.

    Feedback is predetermined by the condition file and does not depend on the
    door chosen, so a choice change after feedback measures reactivity to the
    feedback itself rather than learning.
    """
    qc: dict[str, Any] = {}
    ordered = trials.sort_values(["block", "trial"], kind="stable")
    qc["qc_trials_total"] = int(len(ordered))
    qc["qc_blocks"] = int(ordered["block"].nunique(dropna=True))
    feedback = ordered["feedback"].astype(str)
    qc["qc_n_win"] = int((feedback == "win").sum())
    qc["qc_n_loss"] = int((feedback == "loss").sum())
    if ordered.empty:
        return {}, qc

    responded = ordered["response"].astype(str) != ""
    out: dict[str, float] = {
        "signal_n_trials": float(len(ordered)),
        "signal_response_rate": float(responded.mean()),
        "signal_omission_rate": float(1.0 - responded.mean()),
    }
    if responded.any():
        out["signal_choice_door2_rate"] = float(
            (ordered.loc[responded, "response"].astype(str) == "2").mean())
        out["signal_choice_bias"] = abs(out["signal_choice_door2_rate"] - 0.5)
    out.update(_describe_rt("signal_rt", ordered.loc[responded, "rt_sec"]))

    stay_after_win: list[int] = []
    stay_after_loss: list[int] = []
    rt_after_win: list[float] = []
    rt_after_loss: list[float] = []
    responded_after_win: list[int] = []
    responded_after_loss: list[int] = []
    switches: list[int] = []
    for _, block in ordered.groupby("block", sort=True, dropna=False):
        rows = block.to_dict("records")
        for i in range(1, len(rows)):
            previous, current = rows[i - 1], rows[i]
            previous_feedback = str(previous.get("feedback") or "")
            if previous_feedback not in ("win", "loss"):
                continue
            has_response = bool(str(current.get("response") or ""))
            (responded_after_win if previous_feedback == "win" else responded_after_loss).append(int(has_response))
            if has_response and np.isfinite(current.get("rt_sec", float("nan"))):
                (rt_after_win if previous_feedback == "win" else rt_after_loss).append(float(current["rt_sec"]))
            if not has_response or not str(previous.get("response") or ""):
                continue
            stayed = int(str(current["response"]) == str(previous["response"]))
            switches.append(1 - stayed)
            (stay_after_win if previous_feedback == "win" else stay_after_loss).append(stayed)

    if switches:
        out["signal_switch_rate"] = float(np.mean(switches))
    if stay_after_win:
        out["signal_win_stay_rate"] = float(np.mean(stay_after_win))
        out["signal_n_win_stay_pairs"] = float(len(stay_after_win))
    if stay_after_loss:
        out["signal_lose_shift_rate"] = float(1.0 - np.mean(stay_after_loss))
        out["signal_n_lose_shift_pairs"] = float(len(stay_after_loss))
    if stay_after_win and stay_after_loss:
        # Above 0 means the subject's next choice tracks the feedback it just saw.
        out["signal_feedback_sensitivity"] = float(
            out["signal_win_stay_rate"] + out["signal_lose_shift_rate"] - 1.0)
    if rt_after_win:
        out["signal_rt_after_win_mean_sec"] = float(np.mean(rt_after_win))
    if rt_after_loss:
        out["signal_rt_after_loss_mean_sec"] = float(np.mean(rt_after_loss))
    if rt_after_win and rt_after_loss:
        out["signal_rt_after_loss_minus_win_sec"] = _safe(
            out["signal_rt_after_loss_mean_sec"] - out["signal_rt_after_win_mean_sec"])
    if responded_after_win and responded_after_loss:
        out["signal_response_rate_after_win"] = float(np.mean(responded_after_win))
        out["signal_response_rate_after_loss"] = float(np.mean(responded_after_loss))
        out["signal_response_rate_after_loss_minus_win"] = _safe(
            out["signal_response_rate_after_loss"] - out["signal_response_rate_after_win"])

    per_block_response: list[float] = []
    per_block_rt: list[float] = []
    for _, block in ordered.groupby("block", sort=True, dropna=False):
        block_resp = block["response"].astype(str) != ""
        per_block_response.append(float(block_resp.mean()))
        per_block_rt.append(_mean(block.loc[block_resp, "rt_sec"]))
    out["signal_response_rate_block_slope"] = _slope_over_blocks(per_block_response)
    out["signal_rt_block_slope_sec"] = _slope_over_blocks(per_block_rt)
    return out, qc


TASK_FEATURES = {
    "1back": nback_features,
    "oddball": oddball_features,
    "doors": doors_features,
}


# -- per-subject driver ----------------------------------------------------

def process_subject(l_id: str, subject_dir: Path, device: str, task: str,
                    bspec: BehaviourTaskSpec) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    qc: dict[str, Any] = {
        "L_id": l_id, "modality": "behaviour", "device": device, "task": task,
        "qc_feature_status": "blocked", "qc_failure_reason": "",
        "qc_timing_confidence": bspec.timing_confidence,
        "qc_sensitivity_only": int(bspec.sensitivity_only),
    }
    if bspec.log_format == "eprime_block_trial_txt":
        files = eprime_trial_files(subject_dir, bspec.column("trial_file_glob", "*.txt"))
    else:
        files = psychopy_trial_files(subject_dir)
    qc["qc_log_files_found"] = len(files)
    if not files:
        qc["qc_failure_reason"] = "no_trial_log"
        return None, qc

    try:
        trials = read_trials(files[-1], bspec)
    except Exception as exc:  # noqa: BLE001
        qc["qc_failure_reason"] = f"read_error:{type(exc).__name__}"
        return None, qc

    if trials.empty:
        qc["qc_failure_reason"] = "no_trial_rows"
        return None, qc

    excluded = bspec.raw.get("excluded_variant") or {}
    if task == "1back" and excluded and trials["condition"].astype(str).eq("").all():
        # The arrow-key build logs a condition this loader cannot map and its
        # stimulus list contains no repeat at all, so there is no contrast.
        qc["qc_failure_reason"] = f"excluded_variant:{excluded.get('name', 'unknown')}"
        qc["qc_variant"] = str(excluded.get("name", ""))
        return None, qc

    features, task_qc = TASK_FEATURES[task](trials, bspec)
    qc.update(task_qc)
    if not features:
        qc["qc_failure_reason"] = qc.get("qc_failure_reason") or "no_usable_trials"
        return None, qc

    expected = bspec.expected_trials
    qc["qc_trials_expected"] = expected if expected is not None else np.nan
    qc["qc_trial_count_conformant"] = int(expected is None or qc.get("qc_trials_total") == expected)
    # The QC table stays a log-integrity control: how complete and conformant
    # the recorded log is. Response rate is task performance, so it lives on the
    # signal side only; putting it here would contaminate the `qc` baseline that
    # `signal_qc vs qc` is meant to test against.
    qc["qc_feature_status"] = "ok"
    qc["qc_failure_reason"] = ""

    signal: dict[str, Any] = {
        "L_id": l_id, "modality": "behaviour", "device": device, "task": task,
        "feature_version": FEATURE_VERSION,
        "event_validity_status": "confirmed_from_paradigm_spec",
    }
    signal.update(features)
    return signal, qc


def extract_behaviour_features(device: str, task: str,
                               config_path: str | Path = "configs/goal2_9/behaviour.yaml",
                               limit: int | None = None, n_jobs: int | None = None,
                               spec: ParadigmSpec | None = None) -> dict[str, Any]:
    from joblib import Parallel, delayed

    config = load_goal_config(config_path)
    spec = spec or load_paradigm_spec(config["paths"]["paradigm_spec"])
    bspec = spec.behaviour(device, task)
    out_dir = Path(ensure_output(f"{config['behaviour']['outputs_dir']}/.keep", config)).parent
    stem = f"{device}_{task}"

    if not bspec.usable:
        manifest = {
            "device": device, "task": task, "feature_version": FEATURE_VERSION,
            "status": "not_extracted", "reason": bspec.unusable_reason,
            "detail": str(bspec.raw.get("unusable_detail", "")).strip(),
        }
        (out_dir / f"{stem}_feature_manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
        return manifest

    raw_root = project_path(config["paths"]["raw_data_dir"])
    found = collect_subject_dirs(raw_root / bspec.raw_dir, bspec.column("subject_dir_glob", "*"))
    split = cv_subjects(config)
    targets = [(l, found[l]) for l in map(str, split["L_id"]) if l in found]
    if limit:
        targets = targets[:limit]

    work = [(l, path, device, task, bspec) for l, path in targets]
    jobs = int(n_jobs if n_jobs is not None else config.get("run", {}).get("n_jobs", 1))
    if jobs == 1:
        results = [process_subject(*item) for item in work]
    else:
        results = Parallel(n_jobs=jobs, backend="loky", verbose=5)(
            delayed(process_subject)(*item) for item in work)

    signal = pd.DataFrame([s for s, _ in results if s])
    qc = pd.DataFrame([q for _, q in results])

    keep = [c for c in ["L_id", "A_id", "primary_label_nonhealthy", "split_group", "split_role",
                        "is_locked_test", "cv_fold", "sex", "age", "grade", "grade_group",
                        "fnirs_device"] if c in split.columns]
    signal_out = split[keep].merge(signal, on="L_id", how="inner").sort_values("L_id").reset_index(drop=True)
    qc_out = split[keep].merge(qc, on="L_id", how="inner").sort_values("L_id").reset_index(drop=True)
    for frame, label in ((signal_out, "signal"), (qc_out, "qc")):
        if pd.to_numeric(frame.get("is_locked_test", 0), errors="coerce").fillna(0).astype(int).any():
            raise ValueError(f"Goal 2.9 behaviour {label} features include pilot-holdout subjects.")

    signal_path = out_dir / f"{stem}_signal_features.csv"
    qc_path = out_dir / f"{stem}_qc_features.csv"
    signal_out.to_csv(signal_path, index=False)
    qc_out.to_csv(qc_path, index=False)

    manifest = {
        "device": device, "task": task, "feature_version": FEATURE_VERSION,
        "status": "extracted",
        "timing_confidence": bspec.timing_confidence,
        "sensitivity_only": bspec.sensitivity_only,
        "subjects_attempted": len(work),
        "subjects_signal": int(len(signal_out)), "subjects_qc": int(len(qc_out)),
        "signal_feature_columns": int(sum(1 for c in signal_out.columns if c.startswith("signal_"))),
        "block_reasons": (qc.loc[qc["qc_feature_status"] != "ok", "qc_failure_reason"]
                          .value_counts().to_dict() if len(qc) else {}),
        "signal_features": str(signal_path), "qc_features": str(qc_path),
    }
    (out_dir / f"{stem}_feature_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest
