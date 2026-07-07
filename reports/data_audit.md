# Chongqing Subject-Level Data Audit

## Technical Summary

- Manifest subjects: `4610`.
- Duplicate `A_id` count: `0`.
- Duplicate `L_id` count: `0`.
- Audit scope: subject manifest, modality coverage flags, demographic fields, fNIRS device inferred from raw path metadata, and metadata-level duplicate file checks.

## Label Counts

### `primary_label_nonhealthy`

| Value | Count |
|---|---:|
| `0` | 3126 |
| `1` | 1372 |
| `[missing]` | 112 |

### `sensitivity_label_clear_diagnosis`

| Value | Count |
|---|---:|
| `0` | 3126 |
| `[missing]` | 856 |
| `1` | 628 |

### `sensitivity_label_mdd_highrisk`

| Value | Count |
|---|---:|
| `0` | 3126 |
| `1` | 1234 |
| `[missing]` | 250 |

## Modality Coverage

### `has_EEG`

| Value | Count |
|---|---:|
| `1` | 2498 |
| `0` | 2112 |
| `[missing]` | 0 |

### `has_fNIRS`

| Value | Count |
|---|---:|
| `1` | 3284 |
| `0` | 1326 |
| `[missing]` | 0 |

### `has_face`

| Value | Count |
|---|---:|
| `1` | 4573 |
| `0` | 37 |
| `[missing]` | 0 |

### `has_eye_direct`

| Value | Count |
|---|---:|
| `0` | 4319 |
| `1` | 291 |
| `[missing]` | 0 |

### `has_eye_name_mapped`

| Value | Count |
|---|---:|
| `0` | 3739 |
| `1` | 871 |
| `[missing]` | 0 |

## Cohort Sizes

| Cohort | Subjects |
|---|---:|
| `coverage_maximized` | 4497 |
| `matched_eeg_fnirs_face` | 2376 |
| `missing_modality` | 3837 |

## Demographics

### `sex`

| Value | Count |
|---|---:|
| `女` | 2863 |
| `男` | 1741 |
| `#N/A` | 6 |

### `age_bin`

| Value | Count |
|---|---:|
| `age_12_14` | 1895 |
| `age_15_17` | 1637 |
| `age_09_11` | 882 |
| `age_18_20` | 188 |
| `age_missing` | 6 |
| `age_abnormal` | 2 |

### `grade_group`

| Value | Count |
|---|---:|
| `middle` | 2026 |
| `high` | 1449 |
| `primary` | 1129 |
| `grade_missing` | 6 |

### Missing Demographics

| Field | Missing rows |
|---|---:|
| `sex` | 6 |
| `age` | 6 |
| `grade` | 6 |

### Abnormal Age Rows

- Rows with missing, non-numeric, `<9`, or `>20` age: `8`.

| A_id | L_id | age |
|---|---|---:|
| `B09012` | `L1240` | `#N/A` |
| `E12008` | `L4166` | `33` |
| `E12010` | `L4168` | `36` |
| `C08009` | `L1947` | `#N/A` |
| `C08035` | `L1971` | `#N/A` |
| `C08041` | `L1975` | `#N/A` |
| `E06058` | `L3986` | `#N/A` |
| `E16010` | `L4198` | `#N/A` |

## fNIRS Device Coverage

### `fnirs_device`

| Value | Count |
|---|---:|
| `yiruid` | 1976 |
| `none` | 1326 |
| `bikom` | 1307 |
| `both` | 1 |

## Duplicate File Checks

These are metadata-level checks; large raw files were not content-hashed.

### EEG Role Files

| Task | Subject dirs | Duplicate data role | Duplicate evt role | Missing data role | Missing evt role |
|---|---:|---:|---:|---:|---:|
| `rest` | 1334 | 0 | 0 | 0 | 0 |
| `oddball` | 2358 | 0 | 0 | 0 | 0 |
| `1back` | 1810 | 0 | 0 | 0 | 0 |

### Face MP4 Files

| Task | L_ids | Duplicate L_id count |
|---|---:|---:|
| `面部1-自我介绍1分钟` | 4574 | 0 |
| `面部2-任务` | 4568 | 0 |

### fNIRS Subject Directories

| Source task | Subject dirs with L_id | Duplicate L_id dir count | `.nirs` L_ids | Duplicate `.nirs` L_id count |
|---|---:|---:|---:|---:|
| `依瑞德近红外/1.Rest_1949` | 0 | 0 | 1949 | 0 |
| `依瑞德近红外/2.Oddball_702` | 0 | 0 | 702 | 0 |
| `依瑞德近红外/3.VFT_1904` | 1904 | 0 | 1904 | 0 |
| `依瑞德近红外/4.1_back_1824` | 0 | 0 | 1824 | 0 |
| `依瑞德近红外/5.Doors_1065` | 0 | 0 | 1065 | 0 |
| `必可明近红外/1.Rest_1302` | 1302 | 0 | 0 | 0 |
| `必可明近红外/2.Oddball_644` | 644 | 0 | 0 | 0 |
| `必可明近红外/3.VFT_1308` | 1308 | 0 | 0 | 0 |
| `必可明近红外/4.1-Back_1272` | 1272 | 0 | 0 | 0 |
| `必可明近红外/5.Doors_649` | 649 | 0 | 0 | 0 |

### Eye-Tracking Files

Eye-tracking raw paths mostly do not contain stable `L_id`; this is a filename-level duplicate check.

| Source | Files | Unique stems | Duplicate stem count | L_ids in paths |
|---|---:|---:|---:|---:|
| `Tobbi原始数据_xlsx` | 1015 | 1015 | 0 | 0 |
| `七鑫易维原始工程_csv` | 23354 | 23354 | 0 | 0 |
| `Tobbi工程原文件_rec` | 1076 | 1071 | 5 | 0 |

## Interpretation

- `A_id` and `L_id` uniqueness should remain a hard gate before any model run.
- `primary_label_nonhealthy` is the default split label; sensitivity labels are counted here but not used for split assignment.
- fNIRS device balance is approximate because device is inferred from raw path metadata and some manifest fNIRS rows have unknown device source.
- Eye-tracking direct and name-mapped coverage are kept separate. The split uses name-mapped eye coverage for the four-modality missingness pattern.
