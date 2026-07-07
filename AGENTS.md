# Chongqing Binary Diagnosis Agents

Last updated: 2026-07-07

## Project Root

Use this directory as the project root:

`/home/qiangminc/codes/data4_qiangminc/code/chongqing`

## Current Stage

Current stage: **Goal 2.5, EEG/fNIRS/Face data readiness audit and protocol repair**.

Goal 0 through Goal 2 have already established the engineering framework, data audit, fixed subject split, leakage guard, demographics baseline, and EEG Rest traditional baseline. Goal 2 evaluated the locked test split, so that split is now called the **baseline-exposed pilot holdout**.

Goal 2.5 may build modality indexes, file/QC availability tables, smoke artifacts, cohort reconciliations, and reports. It must not run formal full-scale training, multimodal fusion, model search, or any pilot-holdout evaluation.

## Roadmap

- Goal 3: EEG single-modality fixed-split experiments.
- Goal 4: fNIRS single-modality fixed-split experiments.
- Goal 5: Face single-modality fixed-split experiments.
- Goal 6: same-cohort fair comparison across modalities.
- Goal 7: multimodal fusion after single-modality protocols are stable.

Eye tracking is extension-only for now and is not part of the first core multimodal system.

## Read-Only Inputs

Treat these as read-only:

- Raw dataset: `/home/qiangminc/codes/data4_qiangminc/datasets_qiangmin/chongqing`
- Existing report bundle: `/home/qiangminc/codes/data4_qiangminc/code/chongqing/inputs/derived_reports/chongqing_binary_diagnosis_report`

All generated indexes, caches, intermediate results, features, predictions, models, splits for robustness, and reports must be written under the project root, especially:

- `artifacts/`
- `results/`
- `reports/`
- `checkpoints/`

## Split Rules

All modality data inherit `artifacts/splits/subject_splits_v1.csv` using subject key `L_id`.

The same subject's EEG tasks/windows, fNIRS devices/tasks/trials/time slices, Face videos/frames/clips, and all future derived features or representations must stay in the same global split and CV fold. Do not create per-window, per-trial, per-frame, per-task, or per-modality random splits.

Model development, feature selection, architecture selection, threshold selection, early stopping, checkpoint selection, and ablations must use fixed fivefold OOF results from the CV pool. The baseline-exposed pilot holdout is not used for development decisions.

## Leakage Rules

Never use diagnosis, labels, clinical scales, self-harm/suicide fields, manual review fields, or other clinical proxy fields as objective modality model inputs. Forbidden predictors include `diag3`, `primary_label_nonhealthy`, `sensitivity_label_*`, CDRS, CES-DC, HAMA, SCARED, suicide/self-harm, diagnosis, manual-review, and clinical-scale total fields.

Demographics may be used only as a separately reported demographics-only baseline, modality+demographics increment, stratification variable, or confound variable.

## Current Entry Points

- EEG readiness: `python scripts/audit_eeg_readiness.py --config configs/readiness/eeg_smoke.yaml`
- fNIRS readiness: `python scripts/audit_fnirs_readiness.py --config configs/readiness/fnirs_smoke.yaml`
- Face readiness: `python scripts/audit_face_readiness.py --config configs/readiness/face_smoke.yaml`
- Cohort reconciliation: `python scripts/build_cohorts_v2.py --config configs/readiness/default.yaml`
- Group/confound audit: `python scripts/audit_groups.py --config configs/readiness/default.yaml`
- Unit tests: `python -m unittest discover -s tests`
- Leakage guard: `python scripts/check_leakage.py --config configs/smoke.yaml`
