# Goal 2.5 Cohort Reconciliation

This report recomputes EEG/fNIRS/Face cohorts from `subject_splits_v1.csv` plus task-level file/QC availability tables. Eye tracking is extension-only and is not part of any `core3` definition.

## Count Summary

| metric | value |
|---|---:|
| `primary_label_valid` | 4497 |
| `at_least_one_core3_flag` | 4497 |
| `eeg_flag` | 2448 |
| `eeg_file` | 2448 |
| `eeg_qc` | 2437 |
| `fnirs_flag` | 3202 |
| `fnirs_file` | 3190 |
| `fnirs_qc` | 3190 |
| `face_flag` | 4468 |
| `face_file` | 4468 |
| `face_qc` | 4468 |
| `core3_flag_complete` | 2376 |
| `core3_file_complete` | 2365 |
| `core3_qc_complete` | 2354 |
| `four_modality_complete_direct_flag` | 227 |
| `four_modality_complete_name_mapped_flag` | 660 |

## 2189 vs 2376

The existing Goal 1 `matched_eeg_fnirs_face.csv` count of 2376 is a manifest/split flag count for labeled subjects with EEG, fNIRS, and Face flags. A previously documented 2189 count is not reproduced by the current canonical manifest alone and is treated as an older or stricter denominator likely affected by manifest version, label filtering, actual file matching, task requirements, or QC rules.

For model development after Goal 2.5, use the file-verified and QC-verified `artifacts/cohorts_v2/` cohorts rather than either historical number by itself.

## Definitions

- `core3_complete_flag`: manifest/split flags for EEG, fNIRS, and Face are all 1.
- `core3_complete_file`: at least one readable task/video file is available for each of EEG, fNIRS, and Face.
- `core3_complete_qc`: the minimum metadata-level QC pass is true for each of EEG, fNIRS, and Face.
- `core3_incomplete`: at least one core3 flag is present, but QC-complete core3 is not satisfied.
- Eye tracking is written only to `eye_extension_*` tables.
