# Experiment Protocol

## Current Stage

Goal 2.7 is complete and is the current formal evidence baseline. Goal 2.8 is the
next decision gate. Do not start Goal 3, Goal 4, Goal 5, or multimodal fusion
without an explicit new goal and a go/no-go decision grounded in Goal 2.8.

## Subject-Level Unit

The unit of analysis is the subject, keyed by `L_id`. Windows, epochs, trials,
time slices, frames, clips, videos, and derived representations inherit the
subject split and may not be randomized independently.

## Co-Primary Outer CV

Protocol A, Standard fixed CV:

- split file: `artifacts/splits/subject_splits_v1.csv`
- development rows: `split_group == cv`
- outer fold: `cv_fold`

Protocol B, Group-aware fixed CV:

- split file: `artifacts/splits/subject_splits_group_robustness_v1.csv`
- development rows: `split_group == cv`
- outer fold: `robustness_fold`

Both protocols use the same predefined feature sets and model families. Results
from one protocol must not choose models or settings for the other.

## Inner CV and Preprocessing

Each outer training fold uses three-fold subject-level inner CV. Hyperparameters,
visual PCA dimensions, thresholds, imputation, scaling, categorical encoding,
variance filtering, and any feature selection are fit on outer-train only.

The outer validation labels are unavailable to model and threshold selection.
Every eligible `L_id` receives exactly one OOF prediction per
protocol/cohort/modality/device/task/feature-set/model/seed combination.

## Pilot Holdout Policy

The locked test set is a baseline-exposed pilot holdout. It is excluded from
feature extraction decisions, model development, threshold selection, early
stopping, checkpoint selection, result ranking, and Goal 2.7 reporting.

## Labels and Leakage

Use `primary_label_nonhealthy` only as the supervised outcome. Diagnosis fields,
clinical scales, self-harm/suicide variables, manual review, labels, and clinical
proxy totals are forbidden predictors.

Main demographics is age + sex + grade. Report these separately from objective
signal. `grade_group`, group proxy, and device are sensitivity/shortcut features,
not part of the minimal demographics baseline.

## Required Feature Comparisons

EEG and fNIRS include:

- signal vs demographics;
- signal+demographics vs demographics;
- signal+QC vs QC;
- signal+QC+demographics vs QC+demographics;
- signal+QC+demographics vs demographics;
- signal+demographics vs signal;
- signal+QC+demographics vs signal+QC.

Face additionally includes strict face vs background, full frame, metadata, and
QC, plus face+demographics vs background+demographics.

Each paired comparison uses identical subjects, outer folds, model family, seed,
and CV protocol, with at least 1000 paired subject bootstrap resamples for AUROC
and AUPRC differences.

## Metrics and Thresholds

Primary metrics are AUROC and AUPRC. Secondary metrics are balanced accuracy,
macro F1, sensitivity, specificity, accuracy, Brier score, ECE, and positive
prediction rate.

Report pooled OOF, per-fold, fold mean/std, and 95% subject bootstrap CI. For
threshold-dependent pooled metrics, apply each subject's fold-specific threshold
selected from that outer fold's inner OOF predictions. Keep fixed threshold 0.5
as a separate result.

## EEG Event Validity

- Rest is event-free and may use whole-recording/window-generic features.
- Oddball cached code `22` is `oddball_target_only_proxy`; target/non-target ERP
  and condition differences are blocked.
- 1BACK codes `18` and `19` are not semantically confirmed; condition-difference
  features are blocked and only generic task features are allowed.

## fNIRS Timing and Device Validity

- Yiruid and Bikom remain device-specific.
- Rest may use whole-recording features.
- Task response requires marker-confirmed or protocol-confirmed timing.
- The 20/60/20 segmentation fallback is forbidden for formal results.
- Bikom files are read in full; a fixed 2000-row cap is forbidden.
- Yiruid raw/log-intensity and OD-like features may not be described as HbO/HbR
  without wavelength and geometry confirmation.

## Face Protocol

- Use 16 uniformly sampled frames per video and at least 4 valid detected-face
  frames for strict face embeddings.
- Failed detections are excluded from strict face and strict background inputs.
- Strict background masks or blurs the detected face box.
- The frozen visual encoder does not use audio.
- Only visual embedding columns enter train-fold PCA; demographics, QC, metadata,
  and categorical one-hot features bypass PCA.
- Detector, checkpoint, threshold, detection rate, blocked count, and fallback
  usage must be recorded.

## Interpretation Rules

`INDEPENDENT_SIGNAL_SUPPORTED` requires a positive paired independent increment
whose AUROC CI excludes zero, at least 4/5 positive folds, positive Group CV
increment, and no dominant shortcut explanation.

Unsupported task semantics produce `BLOCKED_BY_INVALID_TASK_SEMANTICS` regardless
of point-estimate performance. Background/group/device performance near the
modality signal supports `SHORTCUT_DOMINATED` or a shortcut warning.

Goal 2.7 decisions:

- EEG: `BLOCKED_BY_INVALID_TASK_SEMANTICS + NO_CLEAR_SIGNAL`.
- fNIRS: `BLOCKED_BY_INVALID_TASK_SEMANTICS + NO_CLEAR_SIGNAL`.
- Face: `SHORTCUT_DOMINATED`.
- No modality reached `INDEPENDENT_SIGNAL_SUPPORTED`.

## Reproducibility and Release

Run in the `avmoe` environment with `PYTHONPATH=src`. The full model matrix can
be followed by restartable supplemental statistics from saved OOF predictions.
`scripts/build_goal2_7_release_manifest.py` creates deterministic compressed OOF
archives and a SHA-256 release manifest.

Large Face embeddings, intermediate checkpoints, uncompressed >100 MB OOF files,
and identifiable Face contact sheets remain local and are excluded from Git.
