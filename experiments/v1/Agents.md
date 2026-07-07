# Chongqing v1 Agents

Last updated: 2026-07-04

## Project Goal

Build v1 single-modality baselines for the Chongqing multimodal health/disease binary diagnosis project. The first milestone is an end-to-end resting-state EEG baseline, then the same interfaces will be reused for fNIRS, face, and eye tracking.

## Non-Negotiable Constraints

- Treat `/home/qiangminc/codes/data4_qiangminc/datasets_qiangmin/chongqing` as read-only.
- Never delete, move, rename, rewrite, normalize, or cache raw dataset files in place.
- Do not copy raw BDF, video, fNIRS, or eye-tracking source files into `experiments/v1` artifacts.
- Do not write names, phone numbers, school/class identity fields, or other direct identifiers to `experiments/v1` outputs.
- Clinical scales that define or closely proxy labels must not enter model features: CDRS, CES-DC, HAMA, suicide scales, diagnosis columns, and manual review columns are forbidden predictors.
- Split, train, and evaluate at subject level. Windows, epochs, trials, frames, or task segments from the same subject must never cross train/test boundaries.

## Canonical Inputs

- Dataset root: `/home/qiangminc/codes/data4_qiangminc/datasets_qiangmin/chongqing`
- Manifest: `/home/qiangminc/codes/data4_qiangminc/code/chongqing/inputs/derived_reports/chongqing_binary_diagnosis_report/data/subject_manifest.csv`
- Primary label: `primary_label_nonhealthy`
- Positive class: non-healthy/high-risk/disease `1`
- Negative class: healthy `0`
- Excluded labels: empty label values from the manifest.

## Output Policy

- v1 project root: `/home/qiangminc/codes/data4_qiangminc/code/chongqing/experiments/v1`
- EEG artifacts: `experiments/v1/eeg/artifacts/`
- EEG reports: `experiments/v1/eeg/reports/`
- All generated features, predictions, metrics, splits, and reports must stay under `experiments/v1`.
- Raw file paths in indexes may point to non-identifying `*_data.bdf`, `data.bdf`, `*_evt.bdf`, or `evt.bdf` files only. Do not record the named main BDF path.

## Reproducibility Defaults

- Random seed: `20260703`
- First EEG milestone: resting-state EEG traditional ML baseline.
- First EEG deep milestone: Rest, Oddball, and 1BACK cached-window baselines with EEGNet and InceptionTime.
- Default EEG feature extraction parallelism: 4 workers.
- Default EEG CV: 5-fold stratified subject-level cross-validation.
- Smoke tests must support `--limit N`.

## Stage Log

- 2026-07-03: v1 scaffolding started. First implementation target is EEG Rest file indexing, EEG-only feature extraction, and baseline model training.
- 2026-07-03: EEG Rest v1 full run completed. Indexed 1334 Rest subjects, extracted 1279 valid feature rows, and trained primary-label baselines on 1247 labeled subjects with 5-fold subject-level CV. EEG-only Rest models were near chance; demographics-only sanity baseline was higher and should be treated as a confounding/stratification signal to inspect before expanding claims.
- 2026-07-04: EEG deep baseline full run completed for Rest, Oddball, and 1BACK using anonymous cached windows plus EEGNet/InceptionTime. Cached-window coverage: Rest 1284 subjects / 67332 windows, Oddball 2285 / 52193, 1BACK 1694 / 24780. Best deep AUROC was weak (1BACK EEGNet 0.534, Oddball EEGNet 0.528, Rest InceptionTime 0.511) and below the demographics-only sanity baseline; treat this as a reproducible baseline, not evidence of diagnostic validity.
