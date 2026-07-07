# Experiment Protocol

## Current Stage

Goal0: project initialization only.

No full model training is allowed in this stage. Only unit tests, leakage checks, environment recording, and small smoke tests may run.

## Subject-Level Unit

The unit of analysis is the subject, keyed by `L_id`.

All future training, validation, and testing must split by subject. Derived units such as EEG windows, fNIRS trials, face frames, video clips, eye-tracking fixations, or task epochs from the same subject must never cross train/test boundaries.

## Label Policy

Default supervised label:

`primary_label_nonhealthy`

Use only rows where the label is `0` or `1`. Empty labels are excluded.

Sensitivity labels are available for future experiments:

- `sensitivity_label_clear_diagnosis`
- `sensitivity_label_mdd_highrisk`

Any report must state which label was used and how many subjects were excluded.

## Feature Leakage Policy

Clinical labels and label-proxy fields are forbidden as model inputs. This includes:

- Diagnosis columns and manual review columns.
- Label columns such as `primary_label_nonhealthy`, `sensitivity_label_*`, and `diag3`.
- CDRS, CES-DC, HAMA, SCARED, suicide, self-harm, and clinical scale total fields.
- Any field whose name includes obvious clinical-scale or diagnosis markers.

The leakage guard in `src/chongqing_binary/leakage.py` must be run before any feature set is accepted.

## Read-Only Input Policy

The following paths are inputs only:

- `/home/qiangminc/codes/data4_qiangminc/datasets_qiangmin/chongqing`
- `/home/qiangminc/codes/data4_qiangminc/code/chongqing/inputs/derived_reports/chongqing_binary_diagnosis_report`

Do not write outputs, caches, checkpoints, logs, or transformed datasets into these paths.

## Smoke Test Protocol

Goal0 smoke tests:

- Read `subject_manifest.csv`.
- Select a small balanced labeled sample.
- Use only non-clinical modality availability fields.
- Validate feature columns through the leakage guard.
- Fit a trivial smoke-only majority baseline through the model interface.
- Write small metrics and prediction files under `artifacts/smoke/` and `results/smoke/`.

The smoke test exists to verify wiring, not model quality.

## Future Full Experiment Requirements

Before any full experiment, add:

- A named config file under `configs/`.
- A subject-level split file under `artifacts/`.
- Leakage validation for all feature columns.
- Logs and environment metadata.
- Metrics, predictions, and per-fold subject IDs.
- A report stating label policy, modality coverage, exclusions, split policy, and limitations.

