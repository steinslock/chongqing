# Chongqing Health/Non-Health Binary Diagnosis Project Spec

## Purpose

Build a reproducible, subject-level engineering framework for health/non-health binary diagnosis using the Chongqing multimodal dataset. The current stage is Goal 2.5: repair the experimental protocol and establish reliable EEG, fNIRS, and Face data readiness before formal single-modality training.

## Data Sources

Read-only raw dataset:

`/home/qiangminc/codes/data4_qiangminc/datasets_qiangmin/chongqing`

Read-only existing report bundle:

`/home/qiangminc/codes/data4_qiangminc/code/chongqing/inputs/derived_reports/chongqing_binary_diagnosis_report`

Canonical subject manifest:

`inputs/derived_reports/chongqing_binary_diagnosis_report/data/subject_manifest.csv`

Fixed global split:

`artifacts/splits/subject_splits_v1.csv`

The fixed split was already used in the baseline stage. Its locked test portion is therefore a **baseline-exposed pilot holdout** and is not available for future model development decisions.

## Task Definition

Primary task:

Health vs non-health/high-risk/disease binary classification at subject level.

Primary label:

`primary_label_nonhealthy`

Label semantics:

- `0`: healthy
- `1`: non-healthy/high-risk/disease
- empty: excluded from supervised training/evaluation

Sensitivity labels:

- `sensitivity_label_clear_diagnosis`: healthy vs clear diagnosis, excluding high-risk.
- `sensitivity_label_mdd_highrisk`: healthy vs high-risk+MDD.

## Engineering Structure

| Directory | Purpose |
|---|---|
| `configs/` | YAML configs for baselines, readiness, and future experiments |
| `src/` | Reusable Python interfaces and framework code |
| `scripts/` | Command-line entry points |
| `tests/` | Unit and protocol tests |
| `artifacts/` | Generated indexes, cohorts, QC tables, smoke outputs |
| `results/` | Predictions, metrics, and result tables |
| `reports/` | Project reports and design documents |
| `checkpoints/` | Future model checkpoints |
| `inputs/derived_reports/` | Read-only existing dataset reports |
| `experiments/v1/` | Prior exploratory EEG work, not directly comparable to fixed-split formal results |

## Required Interfaces

Existing interfaces:

- Subject-level data interface.
- Configuration interface.
- Logging interface.
- Model interface.
- Evaluation interface.
- Leakage guard.

Goal 2.5 adds:

- `src/chongqing_binary/cohorts.py`: core3 and eye-extension cohort reconciliation.
- `src/chongqing_binary/groups.py`: site/batch/device proxy audit.
- `src/chongqing_binary/eeg/`: EEG file indexing, BDF header IO, QC, preprocessing plan, feature-family definitions.
- `src/chongqing_binary/fnirs/`: fNIRS device/task indexing, file probes, QC, preprocessing plan, feature-family definitions, device-alignment policy.
- `src/chongqing_binary/face/`: Face video indexing, metadata IO, QC, detection, sampling, frozen-feature smoke helpers.

## Output Policy

Raw data and read-only existing reports must never be modified. Derived full subject-level indexes, QC tables, task availability tables, features, predictions, checkpoints, and reports are allowed under the project root output directories.

`artifacts/splits/subject_splits_v1.csv` must not be overwritten. Additional split files, such as group robustness splits, are allowed only as supplemental analysis artifacts and must not replace the global split.

## Experiment Roadmap

- Goal 3: EEG single-modality formal experiments after Goal 2.5 readiness fixes.
- Goal 4: fNIRS single-modality formal experiments with device-specific handling.
- Goal 5: Face single-modality formal experiments starting from frozen visual features.
- Goal 6: fair same-cohort comparison on core3 complete subjects.
- Goal 7: multimodal fusion only after single-modality protocols are stable.

Before any formal modality experiment, the modality must pass file, task/video, QC, split-consistency, leakage, and smoke checks.
