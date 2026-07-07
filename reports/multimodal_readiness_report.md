# Multimodal Readiness Report

## Technical Summary

Goal 2.5 establishes reproducible EEG, fNIRS, and Face data entry points on the fixed subject split. All smoke tests use CV-pool subjects only and no formal training or pilot-holdout evaluation was run.

## Overall Cohorts

| metric | value |
|---|---:|
| `at_least_one_core3_flag` | 4497 |
| `core3_file_complete` | 2365 |
| `core3_flag_complete` | 2376 |
| `core3_qc_complete` | 2354 |
| `eeg_file` | 2448 |
| `eeg_flag` | 2448 |
| `eeg_qc` | 2437 |
| `face_file` | 4468 |
| `face_flag` | 4468 |
| `face_qc` | 4468 |
| `fnirs_file` | 3190 |
| `fnirs_flag` | 3202 |
| `fnirs_qc` | 3190 |
| `four_modality_complete_direct_flag` | 227 |
| `four_modality_complete_name_mapped_flag` | 660 |
| `primary_label_valid` | 4497 |

The 2376 count is the current manifest/split flag-complete EEG+fNIRS+Face cohort. The 2189 count was not reproduced from the canonical manifest and is best treated as an older or stricter denominator. File-verified core3 is 2365 and metadata-QC core3 is 2354, so future fair comparison should use the verified `cohorts_v2` tables.

## EEG Status

| metric | value |
|---|---:|
| `eeg_rest` | {'file': 1296, 'qc': 1283, 'deep_cache': 1296, 'traditional': 1247} |
| `eeg_oddball` | {'file': 2309, 'qc': 2285, 'deep_cache': 2309, 'traditional': 0} |
| `eeg_1back` | {'file': 1773, 'qc': 1694, 'deep_cache': 1773, 'traditional': 0} |

EEG is `READY_WITH_FIXES`: raw task files, BDF headers, old traditional Rest features, and deep window caches are available, and smoke forward-shape checks passed. Formal Goal 3 still needs fixed-split training refactor, inner validation, imbalance handling cleanup, threshold protocol, and subject-balanced window weighting.

## fNIRS Status

| metric | value |
|---|---:|
| `fnirs_yiruid_rest` | {'file': 1894, 'qc': 1894} |
| `fnirs_yiruid_oddball` | {'file': 676, 'qc': 676} |
| `fnirs_yiruid_vft` | {'file': 1851, 'qc': 1851} |
| `fnirs_yiruid_1back` | {'file': 1772, 'qc': 1772} |
| `fnirs_yiruid_doors` | {'file': 1033, 'qc': 1033} |
| `fnirs_bikom_rest` | {'file': 1275, 'qc': 1275} |
| `fnirs_bikom_oddball` | {'file': 633, 'qc': 633} |
| `fnirs_bikom_vft` | {'file': 1281, 'qc': 1281} |
| `fnirs_bikom_1back` | {'file': 1245, 'qc': 1245} |
| `fnirs_bikom_doors` | {'file': 641, 'qc': 641} |

fNIRS is `READY_WITH_FIXES`: both devices have readable files and smoke metadata checks passed, but Yiruid and Bikom cannot be treated as the same raw channel space yet. Goal 4 must be device-aware and must complete event/channel/region alignment before merged-device modeling.

## Face Status

| metric | value |
|---|---:|
| `face_self_intro` | {'file': 4468, 'qc': 4467} |
| `face_task` | {'file': 4458, 'qc': 4458} |

Face is `READY_WITH_FIXES`: coverage is high, metadata decoding works, and visual smoke passed. Formal Goal 5 must expand face detection/QC beyond smoke samples and run shortcut controls for background, codec, resolution, fps, and demographics.

## Confounds

An anonymized `A_id` prefix group variable was built as a batch/site proxy. It is stable enough for robustness analysis but its real-world meaning is not confirmed. fNIRS device and Face codec/resolution/fps are explicit shortcut-risk variables.

## Recommended Next Goal

Recommend Goal 3 EEG first if the priority is the fastest formal fixed-split model, because EEG already has mature preprocessing artifacts and model code to repair. In parallel, Face QC/shortcut work is attractive because file coverage is highest; fNIRS should proceed device-specific until alignment is settled.
