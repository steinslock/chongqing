#!/usr/bin/env python3
"""Generate Goal 2.5 design/readiness reports from current artifacts."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from chongqing_binary.readiness import ensure_output_path, read_csv, text_table


def main() -> None:
    counts = json.load(open(ROOT / "artifacts/cohorts_v2/cohort_counts.json", encoding="utf-8"))
    task_counts = collect_task_counts()
    write_design_docs()
    write_multimodal_report(counts, task_counts)
    append_progress(counts)


def collect_task_counts() -> dict[str, dict[str, int]]:
    out: dict[str, dict[str, int]] = {}
    for task in ("rest", "oddball", "1back"):
        rows = read_csv(f"artifacts/eeg/task_availability_{task}.csv")
        out[f"eeg_{task}"] = {
            "file": sum(row["data_bdf_readable"] == "1" for row in rows),
            "qc": sum(row["qc_pass"] == "1" for row in rows),
            "deep_cache": sum(row["deep_window_cache_exists"] == "1" for row in rows),
            "traditional": sum(row["traditional_feature_exists"] == "1" for row in rows),
        }
    for device in ("yiruid", "bikom"):
        for task in ("rest", "oddball", "vft", "1back", "doors"):
            rows = read_csv(f"artifacts/fnirs/task_availability_{device}_{task}.csv")
            out[f"fnirs_{device}_{task}"] = {
                "file": sum(row["file_readable"] == "1" for row in rows),
                "qc": sum(row["qc_pass"] == "1" for row in rows),
            }
    for task, path in [("self_intro", "artifacts/face/video_availability_self_intro.csv"), ("task", "artifacts/face/video_availability_task.csv")]:
        rows = read_csv(path)
        out[f"face_{task}"] = {
            "file": sum(row["file_readable"] == "1" for row in rows),
            "qc": sum(row["qc_pass"] == "1" for row in rows),
        }
    return out


def write_design_docs() -> None:
    ensure_output_path("reports/eeg_goal3_design.md").write_text(
        """# EEG Goal 3 Design

Goal 3 should convert the existing exploratory EEG code into a fixed-split, subject-level protocol.

## First Formal Models

- EEGNet.
- InceptionTime.

TSception is deferred unless EEGNet/InceptionTime fail basic fixed-split smoke or the task audit shows a need for stronger spatial-temporal inductive bias.

## Tasks

- Rest: traditional bandpower/Hjorth/entropy/asymmetry features plus deep windows.
- Oddball: event-locked windows using audited event codes.
- 1BACK: event-locked windows using audited event codes.

## Feature Families

- Signal-only: bandpower, regional power, asymmetry, spectral entropy, Hjorth, and deep window tensors.
- QC-only: duration, bad-window rate, channel count, rejected-window count, and task/file quality fields.
- Signal+QC: reported separately from signal-only.
- Demographics-only and signal+demographics must be separately reported on the same cohort.

## Training Protocol

- Use only CV-pool fixed fivefold OOF for model development.
- Use an inner validation split inside each training fold for early stopping and checkpoint selection.
- Do not use training loss alone for early stopping.
- Avoid double imbalance compensation; choose either subject-balanced sampling or loss weighting after an ablation.
- Sample windows subject-balanced so high-window subjects do not dominate.
- Aggregate window probabilities to subject-level means/medians and keep `L_id`.
- Select thresholds inside training/inner-validation only; report calibration.
- Run multiple seeds after the first fixed implementation passes smoke.
- Compare tasks and task fusion with paired bootstrap on subject-level OOF predictions.
""",
        encoding="utf-8",
    )
    ensure_output_path("reports/fnirs_goal4_design.md").write_text(
        """# fNIRS Goal 4 Design

Goal 4 should begin device-aware and task-aware. Yiruid and Bikom must not be merged as a single raw channel input space until channel layout, event semantics, and HbO/HbR representations are aligned.

## First Formal Models

- 1D-CNN.
- InceptionTime or 1D-ResNet; choose one after tensor shape and task segmentation are stable.

## Device Strategy

- Start with device-specific CV for Yiruid and Bikom.
- Use device-specific encoders for native-channel deep models.
- Use channel masks for missing or device-specific channels.
- Prefer region-level HbO/HbR features for cross-device comparison.
- Treat cross-device generalization as a robustness experiment, not as the first model-selection path.

## Tasks

Priority should start with Rest and VFT because they have broad coverage, then 1BACK, Oddball, and Doors. Each task needs event/segment validation before formal training.

## Feature Families

- Signal-only: HbO/HbR/HbT summary statistics, slopes, task contrasts, region-level features.
- QC-only: bad channels, saturation/low-signal rates, motion metrics, duration, device/task missingness.
- Demographics-only and signal+demographics must be reported separately on the same device/task cohort.

## Merge Preconditions

Merged-device models require confirmed HbO/HbR semantics, sampling rates, event definitions, channel or region mapping, and a documented device-confound ablation.
""",
        encoding="utf-8",
    )
    ensure_output_path("reports/face_goal5_design.md").write_text(
        """# Face Goal 5 Design

Goal 5 should start from frozen visual features rather than full video-model fine-tuning.

## First Formal Models

1. Frozen frame encoder + mean pooling + Logistic Regression.
2. Frozen frame encoder + MLP.
3. Frozen frame encoder + lightweight temporal aggregation using GRU, TCN, or attention pooling.

VideoMAE, MViT, TimeSformer, or full-parameter video fine-tuning are deferred until frozen-feature models show stable signal.

## Video Inputs

- Self-introduction video alone.
- Task video alone.
- Two-video subject-level fusion.
- Face crop only, aligned face crop, and full frame variants.

## Shortcut Controls

Run background blurred, background masked, face-masked background-only, QC-only, codec/resolution/fps-only, demographics-only, and Face+demographics experiments. If background-only or codec-only baselines approach face-crop performance, treat the Face signal as shortcut-contaminated.

## Protocol

- Decode and sample clips inside subject fold only.
- All clips from the same source video inherit `L_id` split and fold.
- Keep subject-level predictions with `L_id`.
- Report model performance on the same Face cohort for random, demographics-only, QC-only, signal-only, signal+QC, and signal+demographics.
""",
        encoding="utf-8",
    )


def write_multimodal_report(counts: dict, task_counts: dict[str, dict[str, int]]) -> None:
    lines = [
        "# Multimodal Readiness Report",
        "",
        "## Technical Summary",
        "",
        "Goal 2.5 establishes reproducible EEG, fNIRS, and Face data entry points on the fixed subject split. All smoke tests use CV-pool subjects only and no formal training or pilot-holdout evaluation was run.",
        "",
        "## Overall Cohorts",
        "",
        text_table(counts),
        "",
        "The 2376 count is the current manifest/split flag-complete EEG+fNIRS+Face cohort. The 2189 count was not reproduced from the canonical manifest and is best treated as an older or stricter denominator. File-verified core3 is 2365 and metadata-QC core3 is 2354, so future fair comparison should use the verified `cohorts_v2` tables.",
        "",
        "## EEG Status",
        "",
        text_table({k: v for k, v in task_counts.items() if k.startswith("eeg_")}),
        "",
        "EEG is `READY_WITH_FIXES`: raw task files, BDF headers, old traditional Rest features, and deep window caches are available, and smoke forward-shape checks passed. Formal Goal 3 still needs fixed-split training refactor, inner validation, imbalance handling cleanup, threshold protocol, and subject-balanced window weighting.",
        "",
        "## fNIRS Status",
        "",
        text_table({k: v for k, v in task_counts.items() if k.startswith("fnirs_")}),
        "",
        "fNIRS is `READY_WITH_FIXES`: both devices have readable files and smoke metadata checks passed, but Yiruid and Bikom cannot be treated as the same raw channel space yet. Goal 4 must be device-aware and must complete event/channel/region alignment before merged-device modeling.",
        "",
        "## Face Status",
        "",
        text_table({k: v for k, v in task_counts.items() if k.startswith("face_")}),
        "",
        "Face is `READY_WITH_FIXES`: coverage is high, metadata decoding works, and visual smoke passed. Formal Goal 5 must expand face detection/QC beyond smoke samples and run shortcut controls for background, codec, resolution, fps, and demographics.",
        "",
        "## Confounds",
        "",
        "An anonymized `A_id` prefix group variable was built as a batch/site proxy. It is stable enough for robustness analysis but its real-world meaning is not confirmed. fNIRS device and Face codec/resolution/fps are explicit shortcut-risk variables.",
        "",
        "## Recommended Next Goal",
        "",
        "Recommend Goal 3 EEG first if the priority is the fastest formal fixed-split model, because EEG already has mature preprocessing artifacts and model code to repair. In parallel, Face QC/shortcut work is attractive because file coverage is highest; fNIRS should proceed device-specific until alignment is settled.",
    ]
    ensure_output_path("reports/multimodal_readiness_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def append_progress(counts: dict) -> None:
    progress = ROOT / "PROGRESS.md"
    existing = progress.read_text(encoding="utf-8") if progress.exists() else ""
    marker = "## 2026-07-07 - Goal 2.5 EEG/fNIRS/Face Readiness"
    if marker in existing:
        existing = existing.split(marker)[0].rstrip() + "\n\n"
    block = f"""{marker}

Completed Goal 2.5 readiness work:

- Updated `AGENTS.md`, `PROJECT_SPEC.md`, and `EXPERIMENT_PROTOCOL.md` for Goal 2.5, baseline-exposed pilot holdout policy, CV-pool OOF development, modality readiness gates, and Goal 3-7 roadmap.
- Added modular code under `src/chongqing_binary/cohorts.py`, `groups.py`, `eeg/`, `fnirs/`, `face/`, and `readiness.py`.
- Added readiness configs under `configs/readiness/`.
- Added scripts: `audit_eeg_readiness.py`, `audit_fnirs_readiness.py`, `audit_face_readiness.py`, `build_cohorts_v2.py`, `audit_groups.py`, `generate_goal2_5_reports.py`.
- Generated EEG, fNIRS, and Face task/video availability tables, smoke artifacts, cohort reconciliation, group/confound audit, modality design docs, and multimodal readiness report.

Commands run:

- `/home/qiangminc/miniconda3/envs/avmoe/bin/python scripts/audit_eeg_readiness.py --config configs/readiness/eeg_smoke.yaml --smoke-limit 2 --seed 20260707`
- `/home/qiangminc/miniconda3/envs/avmoe/bin/python scripts/audit_fnirs_readiness.py --config configs/readiness/fnirs_smoke.yaml --smoke-limit 2 --seed 20260707`
- `/home/qiangminc/miniconda3/envs/avmoe/bin/python scripts/audit_face_readiness.py --config configs/readiness/face_smoke.yaml --smoke-limit 2 --seed 20260707`
- `/home/qiangminc/miniconda3/envs/avmoe/bin/python scripts/build_cohorts_v2.py --config configs/readiness/default.yaml --seed 20260707`
- `/home/qiangminc/miniconda3/envs/avmoe/bin/python scripts/audit_groups.py --config configs/readiness/default.yaml --seed 20260707`

Key counts:

- EEG flag/file/QC: {counts['eeg_flag']}/{counts['eeg_file']}/{counts['eeg_qc']}
- fNIRS flag/file/QC: {counts['fnirs_flag']}/{counts['fnirs_file']}/{counts['fnirs_qc']}
- Face flag/file/QC: {counts['face_flag']}/{counts['face_file']}/{counts['face_qc']}
- core3 flag/file/QC complete: {counts['core3_flag_complete']}/{counts['core3_file_complete']}/{counts['core3_qc_complete']}
- 2376 is reproduced as current core3 flag-complete. 2189 is not reproduced from the canonical manifest and is recorded as an older/stricter unresolved denominator.

Readiness:

- EEG: `READY_WITH_FIXES`.
- fNIRS: `READY_WITH_FIXES`.
- Face: `READY_WITH_FIXES`.

Blocking items before formal training:

- EEG: refactor old v1 code to fixed split, add inner validation, clean imbalance handling, and subject-balanced windows.
- fNIRS: confirm event/channel/region alignment and keep device-specific modeling until merge conditions are met.
- Face: expand full face detection/QC and run shortcut controls for background/device/video metadata.

Recommended next Goal: Goal 3 EEG fixed-split formal single-modality experiment, with Face QC/shortcut work as the strongest parallel candidate.
"""
    progress.write_text(existing.rstrip() + "\n\n" + block + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
