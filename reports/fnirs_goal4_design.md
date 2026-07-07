# fNIRS Goal 4 Design

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
