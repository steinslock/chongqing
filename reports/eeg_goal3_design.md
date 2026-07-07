# EEG Goal 3 Design

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
