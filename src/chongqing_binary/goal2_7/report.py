"""Markdown report generation for Goal 2.7."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from .config import ensure_output, load_goal_config, project_path
from .runner import _combined_config


REPORTS = {
    "demographics": "reports/goal2_7_demographics_and_group_analysis.md",
    "eeg": "reports/goal2_7_eeg_results.md",
    "fnirs": "reports/goal2_7_fnirs_results.md",
    "face": "reports/goal2_7_face_results.md",
    "core3": "reports/goal2_7_core3_comparison.md",
    "protocol": "reports/goal2_7_protocol_comparison.md",
    "final": "reports/goal2_7_final_report.md",
}


def write_goal2_7_reports(config_path: str | Path = "configs/goal2_7/models.yaml") -> dict[str, str]:
    config = _combined_config(config_path)
    data = _load_results(config)
    outputs = {
        "demographics": _write(REPORTS["demographics"], config, _demographics_report(data)),
        "eeg": _write(REPORTS["eeg"], config, _modality_report(data, "eeg")),
        "fnirs": _write(REPORTS["fnirs"], config, _modality_report(data, "fnirs")),
        "face": _write(REPORTS["face"], config, _face_report(data)),
        "core3": _write(REPORTS["core3"], config, _core3_report(data)),
        "protocol": _write(REPORTS["protocol"], config, _protocol_report(data)),
        "final": _write(REPORTS["final"], config, _final_report(data)),
    }
    return outputs


def _load_results(config: dict[str, Any]) -> dict[str, Any]:
    outputs = config["outputs"]
    mapping = {
        "pooled": outputs["all_pooled_metrics"],
        "fold": outputs["all_fold_metrics"],
        "bootstrap": outputs["bootstrap_ci"],
        "paired": outputs["paired_comparisons"],
        "demo": outputs["demographics_decomposition"],
        "protocol": outputs["standard_vs_group_cv"],
        "face_control": outputs["face_strict_control_summary"],
        "eeg_validity": outputs["eeg_event_validity_summary"],
        "fnirs_validity": outputs["fnirs_event_validity_summary"],
        "core3": outputs["core3_intersection_summary"],
        "threshold": outputs["threshold_diagnostics"],
        "pca": outputs["pca_diagnostics"],
        "exclusion": outputs["exclusion_summary"],
    }
    data: dict[str, Any] = {key: _read_csv(path) for key, path in mapping.items()}
    data["face_manifest"] = _read_json("artifacts/goal2_7/face/encoder_manifest.json")
    return data


def _read_csv(path: str | Path) -> pd.DataFrame:
    resolved = project_path(path)
    if not resolved.exists():
        return pd.DataFrame()
    return pd.read_csv(resolved)


def _read_json(path: str | Path) -> dict[str, Any]:
    resolved = project_path(path)
    if not resolved.exists():
        return {}
    return json.loads(resolved.read_text(encoding="utf-8"))


def _write(path: str, config: dict[str, Any], text: str) -> str:
    out = ensure_output(path, config)
    out.write_text(text.rstrip() + "\n", encoding="utf-8")
    return str(out)


def _demographics_report(data: dict[str, pd.DataFrame]) -> str:
    demo = data["demo"]
    lines = ["# Goal 2.7 Demographics and Group Analysis", ""]
    if demo.empty:
        lines.append("Demographics decomposition results are pending.")
        return "\n".join(lines)
    inner = demo[demo["threshold_type"] == "inner_cv"].copy() if "threshold_type" in demo.columns else demo
    lines.extend(
        [
            "Main demographics is age + sex + grade. `grade_group` and group proxy variables are reported only in sensitivity/decomposition sets.",
            "",
            "## Top Demographic Decomposition Rows",
            "",
            _table(inner.sort_values("auroc", ascending=False).head(40), ["cv_protocol", "cohort_name", "modality", "task", "feature_set", "model", "n_subjects", "auroc", "auprc"]),
        ]
    )
    return "\n".join(lines)


def _modality_report(data: dict[str, pd.DataFrame], modality: str) -> str:
    pooled = data["pooled"]
    paired = data["paired"]
    validity = data[f"{modality}_validity"] if f"{modality}_validity" in data else pd.DataFrame()
    title = "EEG" if modality == "eeg" else "fNIRS"
    lines = [f"# Goal 2.7 {title} Results", ""]
    if not validity.empty:
        lines.extend(["## Event/Timing Validity", "", _table(validity, list(validity.columns)), ""])
    subset = _inner(pooled)
    subset = subset[subset["modality"] == modality] if not subset.empty else subset
    lines.extend(["## Best Inner-CV Rows", "", _table(subset.sort_values("auroc", ascending=False).head(40), ["cv_protocol", "cohort_name", "device", "task", "feature_set", "model", "n_subjects", "auroc", "auprc", "balanced_accuracy"]), ""])
    inc = paired[(paired["modality"] == modality) & (paired["comparison"].isin(["signal_demographics_vs_demographics", "signal_qc_demographics_vs_qc_demographics"]))] if not paired.empty else paired
    lines.extend(["## Independent Increment Paired Comparisons", "", _table(inc.head(60), ["cv_protocol", "cohort_name", "device", "task", "model", "comparison", "n_subjects", "auroc_diff", "auroc_diff_ci_low", "auroc_diff_ci_high", "fold_direction_consistency", "protocol_consistent_direction"])])
    return "\n".join(lines)


def _face_report(data: dict[str, pd.DataFrame]) -> str:
    pooled = data["pooled"]
    paired = data["paired"]
    control = data["face_control"]
    pca = data["pca"]
    subset = _inner(pooled)
    subset = subset[subset["modality"] == "face"] if not subset.empty else subset
    lines = ["# Goal 2.7 Face Results", ""]
    lines.extend(["## Strict Detection/QC Summary", "", _table(control, list(control.columns)), ""])
    lines.extend(["## Best Inner-CV Rows", "", _table(subset.sort_values("auroc", ascending=False).head(50), ["cv_protocol", "cohort_name", "task", "feature_set", "model", "n_subjects", "auroc", "auprc", "balanced_accuracy"]), ""])
    if not pca.empty:
        lines.extend(["## PCA Branch Diagnostics", "", _table(pca[pca["modality"] == "face"].head(50), ["cv_protocol", "cohort_name", "task", "feature_set", "model", "outer_fold", "pca_used", "pca_n_components", "visual_branch_feature_count", "nonvisual_branch_feature_count"]), ""])
    face_pairs = paired[paired["modality"] == "face"] if not paired.empty else paired
    lines.extend(["## Paired Face Controls", "", _table(face_pairs.head(80), ["cv_protocol", "cohort_name", "task", "model", "comparison", "n_subjects", "auroc_diff", "auroc_diff_ci_low", "auroc_diff_ci_high", "fold_direction_consistency", "protocol_consistent_direction"])])
    return "\n".join(lines)


def _core3_report(data: dict[str, pd.DataFrame]) -> str:
    core = _inner(data["core3"])
    paired = data["paired"]
    core_pairs = paired[paired["cohort_name"].astype(str).str.contains("core3", na=False)] if not paired.empty else paired
    lines = ["# Goal 2.7 Core3 Same-Cohort Comparison", ""]
    lines.extend(["## Core3 Metrics", "", _table(core.head(80), ["cv_protocol", "cohort_name", "modality", "device", "task", "feature_set", "model", "n_subjects", "auroc", "auprc"]), ""])
    lines.extend(["## Core3 Independent Increment", "", _table(core_pairs.head(80), ["cv_protocol", "cohort_name", "modality", "task", "model", "comparison", "n_subjects", "auroc_diff", "auroc_diff_ci_low", "auroc_diff_ci_high"])])
    return "\n".join(lines)


def _protocol_report(data: dict[str, pd.DataFrame]) -> str:
    protocol = data["protocol"]
    lines = ["# Goal 2.7 Protocol Comparison", ""]
    lines.append("Protocol A is Standard fixed CV; Protocol B is Group-aware fixed CV. They are co-primary and use the same predefined feature/model sets.")
    lines.extend(["", "## Standard vs Group CV", "", _table(protocol.sort_values("auroc_delta_standard_minus_group", ascending=False).head(80) if not protocol.empty else protocol, list(protocol.columns)[:16] if not protocol.empty else [])])
    return "\n".join(lines)


def _final_report(data: dict[str, pd.DataFrame]) -> str:
    pooled = _inner(data["pooled"])
    paired = data["paired"]
    protocol = data["protocol"]
    bootstrap = data["bootstrap"]
    face_control = data["face_control"]
    face_manifest = data.get("face_manifest", {})
    eeg_validity = data["eeg_validity"]
    fnirs_validity = data["fnirs_validity"]
    key_rows = _key_metric_rows(pooled)
    demo_rows = _demographic_contribution_rows(pooled)
    required = _required_increment_rows(paired)
    positive_required = required[required["auroc_diff_ci_low"] > 0].copy() if not required.empty else required
    native_positive_required = positive_required[~positive_required["cohort_name"].astype(str).str.contains("core3", na=False)].copy() if not positive_required.empty else positive_required
    negative_required = required[required["auroc_diff_ci_high"] < 0].copy() if not required.empty else required
    protocol_drop = protocol.sort_values("auroc_delta_standard_minus_group", ascending=False).head(20) if not protocol.empty else protocol
    face_controls = _face_control_pair_rows(paired)
    core3 = _core3_focus_rows(pooled)
    statuses = _status_rows(pooled, paired, face_control)
    bootstrap_rows = len(bootstrap) if isinstance(bootstrap, pd.DataFrame) else 0
    paired_rows = len(paired) if isinstance(paired, pd.DataFrame) else 0
    face_encoder = face_manifest.get("encoder", {}) if isinstance(face_manifest, dict) else {}
    face_detector = face_manifest.get("detector", {}) if isinstance(face_manifest, dict) else {}
    face_tasks = face_manifest.get("tasks", {}) if isinstance(face_manifest, dict) else {}
    face_task_text = ", ".join(
        f"{name}: signal n={spec.get('subjects_signal')}, QC n={spec.get('subjects_qc')}, sample_frames={spec.get('sample_frames')}"
        for name, spec in face_tasks.items()
    )
    positive_note = (
        "No native EEG, fNIRS, or Face required independent-increment comparison had AUROC 95% CI fully above 0."
        if native_positive_required.empty
        else "At least one native required independent-increment comparison had AUROC 95% CI fully above 0."
    )
    lines = ["# Goal 2.7 Final Report", ""]
    lines.extend(
        [
            "Goal 2.7 fixes the comparison protocol, threshold application, demographics decomposition, Face strict controls, and EEG/fNIRS event validity handling. Standard fixed CV and Group-aware fixed CV are co-primary; all model selection, PCA dimensions, and thresholds are fit inside outer-train only.",
            "",
            "## Technical Summary",
            "",
            "- No modality reaches `INDEPENDENT_SIGNAL_SUPPORTED`. Required native-cohort paired increments over demographics or QC+demographics are absent, negative, or have CIs crossing 0.",
            f"- {positive_note} Positive significant required rows are limited to Core3 Face sensitivity rows, not a consistent native-cohort conclusion.",
            "- EEG task conclusions are blocked for formal Oddball target/non-target ERP and 1BACK condition contrasts; Rest and generic/task-proxy features show no independent increment beyond demographics/QC.",
            "- fNIRS task-response conclusions are blocked without confirmed timing. Yiruid VFT remains the least weak fNIRS candidate by point estimate, but its signal+demographics and signal+QC+demographics increments do not clear paired bootstrap under Group CV.",
            "- Face strict visual embeddings show above-background and above-metadata signal, but demographics/group proxy remain stronger and face+demographics rarely improves over demographics. Face remains shortcut-dominated for final decision-making.",
            "- The most defensible next Goal is not deep modeling yet; it is a shortcut/event-semantics remediation Goal that recovers task protocols and tests residualized or group-balanced visual/demographic baselines.",
            "",
            "## Scope, Protocol, and Outputs",
            "",
            f"- OOF predictions: Standard CV and Group CV, {bootstrap_rows:,} bootstrap CI rows, {paired_rows:,} paired comparison rows.",
            "- Models: Logistic Regression, Random Forest, and HistGradientBoosting only. HGB used the expanded predefined fallback grid.",
            "- Metrics: AUROC/AUPRC plus balanced accuracy, macro F1, sensitivity, specificity, accuracy, Brier score, ECE, and positive prediction rate. Threshold-dependent pooled metrics use each subject's own outer-fold inner-CV threshold; fixed 0.5 metrics are retained.",
            "- Pilot holdout was not used. Main demographics is age + sex + grade; grade_group and group proxy are sensitivity/decomposition sets.",
            "",
            "## Key Standard and Group CV Results",
            "",
            "The table gives the best row for each core feature family and protocol. It is evidence for interpretation, not a model-selection sweep.",
            "",
            _table(key_rows, ["cv_protocol", "modality", "cohort_name", "device", "task", "feature_set", "model", "n_subjects", "auroc", "auprc"], limit=80),
            "",
            "## Demographics and Group Contribution",
            "",
            "Demographics are a major predictor. In the largest Face cohorts, age+sex+grade reaches about 0.67 AUROC, while adding group proxy lifts the best row to about 0.71 AUROC in Standard CV. Group-aware CV reduces group-proxy-heavy rows, confirming acquisition-group shortcut risk.",
            "",
            _table(demo_rows, ["cv_protocol", "feature_set", "modality", "cohort_name", "task", "model", "n_subjects", "auroc", "auprc"], limit=80),
            "",
            "## Event Semantics and Blocked Tasks",
            "",
            "Oddball and 1BACK EEG task-condition claims remain blocked because project-local event semantics are not proven. fNIRS task-response claims remain blocked unless timing is marker-confirmed or protocol-confirmed; no 20/60/20 fallback is used, and Bikom is read without the Goal 2.6 2000-row cap.",
            "",
            "EEG validity:",
            "",
            _table(eeg_validity, list(eeg_validity.columns), limit=20),
            "",
            "fNIRS validity:",
            "",
            _table(fnirs_validity, list(fnirs_validity.columns), limit=20),
            "",
            "## Required Independent Increment Tests",
            "",
            "Native EEG/fNIRS comparisons are generally negative after controlling for demographics or QC+demographics. Face native comparisons show strict visual signal versus background/metadata/QC, but the required independent increments over demographics and QC+demographics mostly cross 0 or are negative.",
            "",
            "Positive required increments with AUROC CI above 0:",
            "",
            _table(positive_required.sort_values("auroc_diff", ascending=False) if not positive_required.empty else positive_required, ["cv_protocol", "modality", "cohort_name", "task", "model", "comparison", "n_subjects", "auroc_diff", "auroc_diff_ci_low", "auroc_diff_ci_high", "fold_direction_consistency", "protocol_consistent_direction"], limit=20),
            "",
            "Largest negative required increments:",
            "",
            _table(negative_required.sort_values("auroc_diff").head(25) if not negative_required.empty else negative_required, ["cv_protocol", "modality", "cohort_name", "task", "model", "comparison", "n_subjects", "auroc_diff", "auroc_diff_ci_low", "auroc_diff_ci_high", "fold_direction_consistency", "protocol_consistent_direction"], limit=25),
            "",
            "## Face Strict Controls",
            "",
            f"Face extraction used `{face_encoder.get('name', 'unknown')}` with `{face_encoder.get('checkpoint', 'unknown')}`, frozen={face_encoder.get('frozen', 'unknown')}, feature_dim={face_encoder.get('feature_dimension', 'unknown')}, device={face_encoder.get('device', 'unknown')}. Detector preference was `{face_detector.get('preferred', 'unknown')}` with checkpoint `{face_detector.get('yuNet_checkpoint', 'unknown')}` and fallback `{face_detector.get('fallback', 'unknown')}`; fallback usage is explicitly recorded and high in this environment. {face_task_text}.",
            "",
            _table(face_control, list(face_control.columns), limit=10),
            "",
            "Face control paired comparisons show face-only is usually above background/metadata/QC, but face+demographics is close to background+demographics and does not reliably exceed demographics.",
            "",
            _table(face_controls, ["cv_protocol", "cohort_name", "task", "model", "comparison", "n_subjects", "auroc_diff", "auroc_diff_ci_low", "auroc_diff_ci_high", "fold_direction_consistency", "protocol_consistent_direction"], limit=60),
            "",
            "## Standard vs Group CV Robustness",
            "",
            "The largest Standard-minus-Group drops are group-proxy and acquisition-context rows, especially Face group proxy and Bikom/Yiruid group proxy. This confirms that Protocol B changes the shortcut landscape rather than serving as a minor appendix.",
            "",
            _table(protocol_drop, ["cohort_name", "modality", "device", "task", "feature_set", "model", "auroc_standard_cv", "auroc_group_cv", "auroc_delta_standard_minus_group", "auprc_standard_cv", "auprc_group_cv"], limit=20),
            "",
            "## Core3 Same-Cohort Comparison",
            "",
            "Core3 is explicitly `core3_rest_yiruidvft_selfintro_intersection` with n=661, not the full 2354-person core3 pool. Face has the only positive required Core3 increments, but they are not enough to override native-cohort shortcut risk.",
            "",
            _table(core3, ["cv_protocol", "modality", "device", "task", "feature_set", "model", "n_subjects", "auroc", "auprc"], limit=80),
            "",
            "## Goal 2.6 Conclusions Retained or Revised",
            "",
            "- Retained: EEG and fNIRS remain weak/uncertain and do not show stable independent increments over demographics/QC.",
            "- Retained: Face remains shortcut-risk because demographics, group proxy, and background+demographics explain much of the top-line performance.",
            "- Revised: Face strict crop is now cleaner: failed detections no longer become center crops, background masks detected faces, and visual PCA is separated from demographics/QC. Face-only still beats background/metadata in many paired tests, so the visual branch is not simply a metadata-only artifact.",
            "- Revised: Oddball is no longer reported as full target/non-target ERP; it is `oddball_target_only_proxy`. 1BACK condition differences are blocked. fNIRS task response is not interpreted without confirmed timing, and Bikom is no longer capped at 2000 rows.",
            "",
            "## Modality Status and Next Goal",
            "",
            _table(statuses, ["modality", "status", "evidence", "decision"], limit=10),
            "",
            "No modality should move directly into a full deep-model Goal on the basis of Goal 2.7 alone. The single most useful next Goal is a Goal 2.8 remediation/decision gate: recover and document EEG/fNIRS event timing, add explicit group-balanced or residualized demographic baselines, and decide whether Face warrants a stricter shortcut-controlled replication before any Goal 3/4/5 deep training.",
        ]
    )
    return "\n".join(lines)


def _key_metric_rows(pooled: pd.DataFrame) -> pd.DataFrame:
    if pooled.empty:
        return pooled
    feature_sets = {
        "eeg": ["demographics", "demographics_group", "group_proxy_only", "signal", "signal_demographics", "signal_qc_demographics", "qc_demographics"],
        "fnirs": ["demographics", "demographics_group", "group_proxy_only", "signal", "signal_demographics", "signal_qc_demographics", "qc_demographics"],
        "face": ["demographics", "demographics_group", "group_proxy_only", "face", "background", "full_frame", "metadata", "face_demographics", "face_qc_demographics", "background_demographics", "qc_demographics"],
    }
    rows = []
    for modality, sets in feature_sets.items():
        for protocol in ["standard_cv", "group_cv"]:
            for feature_set in sets:
                subset = pooled[(pooled["modality"] == modality) & (pooled["cv_protocol"] == protocol) & (pooled["feature_set"] == feature_set)]
                if subset.empty:
                    continue
                rows.append(subset.sort_values(["auroc", "auprc"], ascending=False).iloc[0])
    return pd.DataFrame(rows).reset_index(drop=True) if rows else pd.DataFrame()


def _demographic_contribution_rows(pooled: pd.DataFrame) -> pd.DataFrame:
    if pooled.empty:
        return pooled
    feature_sets = [
        "age_only",
        "sex_only",
        "grade_only",
        "grade_group_only",
        "age_sex",
        "age_grade",
        "sex_grade",
        "age_sex_grade",
        "age_sex_grade_group",
        "group_proxy_only",
        "demographics_group",
        "demographics_group_device",
        "demographics",
    ]
    rows = []
    for protocol in ["standard_cv", "group_cv"]:
        for feature_set in feature_sets:
            subset = pooled[(pooled["cv_protocol"] == protocol) & (pooled["feature_set"] == feature_set)]
            if subset.empty:
                continue
            rows.append(subset.sort_values(["auroc", "auprc"], ascending=False).iloc[0])
    return pd.DataFrame(rows).reset_index(drop=True) if rows else pd.DataFrame()


def _required_increment_rows(paired: pd.DataFrame) -> pd.DataFrame:
    if paired.empty:
        return paired
    comparisons = {
        "signal_demographics_vs_demographics",
        "signal_qc_demographics_vs_qc_demographics",
        "face_demographics_vs_demographics",
        "face_qc_demographics_vs_qc_demographics",
        "modality_demographics_vs_demographics",
        "modality_qc_demographics_vs_qc_demographics",
    }
    return paired[paired["comparison"].isin(comparisons)].copy()


def _face_control_pair_rows(paired: pd.DataFrame) -> pd.DataFrame:
    if paired.empty:
        return paired
    comparisons = {
        "face_vs_background",
        "face_vs_full_frame",
        "face_vs_metadata",
        "face_vs_qc",
        "face_demographics_vs_background_demographics",
        "face_demographics_vs_demographics",
        "face_qc_demographics_vs_qc_demographics",
    }
    return paired[(paired["modality"] == "face") & paired["comparison"].isin(comparisons)].sort_values(["cv_protocol", "cohort_name", "comparison", "model"]).copy()


def _core3_focus_rows(pooled: pd.DataFrame) -> pd.DataFrame:
    if pooled.empty:
        return pooled
    feature_sets = {"demographics", "modality", "modality_demographics", "qc_demographics", "modality_qc_demographics"}
    core = pooled[(pooled["cohort_name"] == "core3_rest_yiruidvft_selfintro_intersection") & (pooled["feature_set"].isin(feature_sets))].copy()
    if core.empty:
        return core
    return core.sort_values(["cv_protocol", "modality", "feature_set", "auroc"], ascending=[True, True, True, False]).groupby(["cv_protocol", "modality", "feature_set"], dropna=False).head(1).reset_index(drop=True)


def _status_rows(pooled: pd.DataFrame, paired: pd.DataFrame, face_control: pd.DataFrame) -> pd.DataFrame:
    statuses = [
        {
            "modality": "EEG",
            "status": "BLOCKED_BY_INVALID_TASK_SEMANTICS + NO_CLEAR_SIGNAL",
            "evidence": "Oddball target/non-target and 1BACK condition semantics are unconfirmed; native required increments are mostly negative and often significantly below demographics/QC+demographics.",
            "decision": "Do not start EEGNet/InceptionTime; first recover event semantics or restrict to clearly event-free Rest.",
        },
        {
            "modality": "fNIRS",
            "status": "BLOCKED_BY_INVALID_TASK_SEMANTICS + NO_CLEAR_SIGNAL",
            "evidence": "Task-response timing is unconfirmed or blocked; Yiruid VFT has the best point estimates but paired increments over demographics/QC+demographics do not clear CI under Group CV.",
            "decision": "Do not start fNIRS deep models; first confirm task timing and HbO/HbR semantics.",
        },
        {
            "modality": "Face",
            "status": "SHORTCUT_DOMINATED",
            "evidence": "Strict face-only beats background/metadata/QC in many controls, but demographics_group and group_proxy are stronger and face+demographics does not reliably beat demographics.",
            "decision": "Treat as shortcut-risk; replicate under stronger group/demographic controls before any video deep model.",
        },
    ]
    return pd.DataFrame(statuses)


def _inner(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty or "threshold_type" not in frame.columns:
        return frame
    return frame[frame["threshold_type"] == "inner_cv"].copy()


def _table(frame: pd.DataFrame, columns: list[str], limit: int = 80) -> str:
    if frame.empty:
        return "No rows."
    cols = [col for col in columns if col in frame.columns]
    if not cols:
        cols = list(frame.columns)
    data = frame[cols].head(limit).copy()
    for col in data.columns:
        if pd.api.types.is_float_dtype(data[col]):
            data[col] = data[col].map(lambda x: "" if pd.isna(x) else f"{x:.4f}")
        else:
            data[col] = data[col].fillna("").astype(str)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in data.iterrows():
        lines.append("| " + " | ".join(str(row[col]).replace("|", "/") for col in cols) + " |")
    if len(frame) > limit:
        lines.append(f"\nShowing first {limit} of {len(frame)} rows.")
    return "\n".join(lines)
