# Experiment Protocol

## Current Stage

Current stage: **Goal 2.5, EEG/fNIRS/Face readiness audit and protocol repair**.

This stage may build indexes, cohorts, task/video availability tables, QC summaries, smoke outputs, and design documents. It must not run formal full-scale EEG, fNIRS, Face, or multimodal training.

## Subject-Level Unit

The unit of analysis is the subject, keyed by `L_id`.

All modality data inherit `artifacts/splits/subject_splits_v1.csv`. Derived units from the same subject must never cross global splits or CV folds, including EEG windows/epochs, fNIRS trials/time slices, Face frames/clips, and future generated features or representations.

Forbidden split actions:

- random splitting of windows, trials, frames, clips, or epochs;
- per-task fold generation;
- per-modality fold generation;
- overwriting `subject_splits_v1.csv`.

## Pilot Holdout Policy

Goal 2 evaluated the locked test set. It is now the **baseline-exposed pilot holdout**.

Future development must not use the pilot holdout for feature selection, model selection, threshold selection, early stopping, checkpoint selection, hyperparameter search, model retention decisions, or any other development decision. CV-pool fixed fivefold OOF results are the development basis.

## Label Policy

Default supervised label:

`primary_label_nonhealthy`

Use only rows where the label is `0` or `1`. Sensitivity labels must be reported separately when used:

- `sensitivity_label_clear_diagnosis`
- `sensitivity_label_mdd_highrisk`

## Feature Leakage Policy

Clinical labels and label-proxy fields are forbidden as objective modality inputs. This includes:

- `diag3`, `primary_label_nonhealthy`, `sensitivity_label_clear_diagnosis`, `sensitivity_label_mdd_highrisk`;
- CDRS, CES-DC, HAMA, SCARED;
- suicide/self-harm fields;
- diagnosis fields;
- manual review fields;
- clinical scale totals and other clinical proxy fields.

Demographics may be used for demographics-only baselines, modality+demographics increment experiments, stratification, and confound audits. They must be reported separately from objective modality-only results.

## Modality Readiness Gates

Before formal training, each modality must have:

- one row per `L_id` task/video availability tables;
- inherited global split role and CV fold;
- file readability checks;
- minimum metadata-level QC;
- failure reasons for missing or unreadable files;
- smoke test using CV pool only;
- leakage guard for feature columns;
- subject-level feature/prediction outputs retaining `L_id`.

## Comparison Rules

Different modalities have different coverage. AUROC or other model metrics cannot be fairly ranked across different subject cohorts.

Each formal modality experiment must report:

1. random/no-information baseline on the same modality cohort;
2. demographics-only on the same modality cohort;
3. modality-only;
4. modality+demographics;
5. QC-only;
6. signal+QC;
7. fixed fivefold OOF;
8. fold mean and standard deviation;
9. subject-level predictions;
10. confidence intervals.

Fair cross-modality comparison requires rerunning all modalities on the same core3 complete cohort.

## fNIRS Device Policy

Yiruid and Bikom fNIRS data must not be directly concatenated as the same raw channel input space until the device alignment audit confirms compatibility. Device-specific encoders, channel masks, or region-level HbO/HbR representations are required before cross-device modeling.

## Face Shortcut Policy

Face models must test face crop, aligned crop, full frame, masked/background variants, QC-only, codec/resolution/fps-only, demographics-only, and two-video fusion before interpreting performance as face-dynamics signal. All clips from the same source video inherit the subject fold.
