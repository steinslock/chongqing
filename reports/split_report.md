# Subject Split Report

## Technical Summary

- Split file: `artifacts/splits/subject_splits_v1.csv`.
- SHA256: `50680a42e69a0331e47fe59686050c6a01e385784b182f88f07a64aa6bc5f12c`.
- Eligible coverage-maximized subjects: `4497`.
- Locked test subjects: `900` (20.0%).
- Cross-validation pool subjects: `3597` (80.0%).
- Locked test set is for final evaluation only and must not be used for model selection.
- Each non-test subject is assigned exactly one validation fold; for fold `k`, train on non-test subjects where `cv_fold != k` and validate on `cv_fold == k`.

## Cohort Membership

| Cohort | Subjects |
|---|---:|
| `coverage_maximized` | 4497 |
| `matched_eeg_fnirs_face` | 2376 |
| `missing_modality` | 3837 |

## Split Sizes

| Split | Subjects |
|---|---:|
| locked_test | 900 |
| cv_pool | 3597 |
| cv_fold_0_validation | 720 |
| cv_fold_1_validation | 720 |
| cv_fold_2_validation | 719 |
| cv_fold_3_validation | 719 |
| cv_fold_4_validation | 719 |

## Distribution: `primary_label_nonhealthy`

| Value | all | locked_test | cv_pool | cv_fold_0 | cv_fold_1 | cv_fold_2 | cv_fold_3 | cv_fold_4 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `0` | 3126 | 627 | 2499 | 502 | 502 | 496 | 498 | 501 |
| `1` | 1371 | 273 | 1098 | 218 | 218 | 223 | 221 | 218 |

## Distribution: `sex`

| Value | all | locked_test | cv_pool | cv_fold_0 | cv_fold_1 | cv_fold_2 | cv_fold_3 | cv_fold_4 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `[missing]` | 1 | 0 | 1 | 0 | 0 | 1 | 0 | 0 |
| `女` | 2794 | 562 | 2232 | 449 | 446 | 443 | 447 | 447 |
| `男` | 1702 | 338 | 1364 | 271 | 274 | 275 | 272 | 272 |

## Distribution: `age_bin`

| Value | all | locked_test | cv_pool | cv_fold_0 | cv_fold_1 | cv_fold_2 | cv_fold_3 | cv_fold_4 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `age_09_11` | 872 | 175 | 697 | 140 | 140 | 139 | 139 | 139 |
| `age_12_14` | 1841 | 369 | 1472 | 297 | 294 | 296 | 294 | 291 |
| `age_15_17` | 1599 | 321 | 1278 | 253 | 256 | 255 | 256 | 258 |
| `age_18_20` | 182 | 35 | 147 | 30 | 29 | 28 | 30 | 30 |
| `age_abnormal` | 2 | 0 | 2 | 0 | 1 | 0 | 0 | 1 |
| `age_missing` | 1 | 0 | 1 | 0 | 0 | 1 | 0 | 0 |

## Distribution: `grade_group`

| Value | all | locked_test | cv_pool | cv_fold_0 | cv_fold_1 | cv_fold_2 | cv_fold_3 | cv_fold_4 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `grade_missing` | 1 | 0 | 1 | 0 | 0 | 1 | 0 | 0 |
| `high` | 1408 | 283 | 1125 | 226 | 224 | 225 | 225 | 225 |
| `middle` | 1974 | 398 | 1576 | 314 | 316 | 314 | 316 | 316 |
| `primary` | 1114 | 219 | 895 | 180 | 180 | 179 | 178 | 178 |

## Distribution: `modality_pattern`

| Value | all | locked_test | cv_pool | cv_fold_0 | cv_fold_1 | cv_fold_2 | cv_fold_3 | cv_fold_4 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `ENFY` | 660 | 133 | 527 | 107 | 108 | 103 | 103 | 106 |
| `ENFy` | 1716 | 346 | 1370 | 274 | 271 | 273 | 275 | 277 |
| `ENfy` | 23 | 4 | 19 | 6 | 3 | 3 | 4 | 3 |
| `EnFY` | 11 | 1 | 10 | 2 | 1 | 2 | 1 | 4 |
| `EnFy` | 38 | 8 | 30 | 3 | 4 | 8 | 9 | 6 |
| `eNFY` | 152 | 29 | 123 | 22 | 25 | 25 | 27 | 24 |
| `eNFy` | 645 | 132 | 513 | 102 | 104 | 103 | 104 | 100 |
| `eNfy` | 6 | 0 | 6 | 2 | 2 | 1 | 0 | 1 |
| `enFY` | 29 | 4 | 25 | 6 | 5 | 6 | 5 | 3 |
| `enFy` | 1217 | 243 | 974 | 196 | 197 | 195 | 191 | 195 |

## Distribution: `fnirs_device`

| Value | all | locked_test | cv_pool | cv_fold_0 | cv_fold_1 | cv_fold_2 | cv_fold_3 | cv_fold_4 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `bikom` | 1281 | 260 | 1021 | 208 | 200 | 199 | 209 | 205 |
| `both` | 1 | 0 | 1 | 0 | 0 | 1 | 0 | 0 |
| `none` | 1295 | 256 | 1039 | 207 | 207 | 211 | 206 | 208 |
| `yiruid` | 1920 | 384 | 1536 | 305 | 313 | 308 | 304 | 306 |

## Balancing Notes

- Split assignment used deterministic stratification labels that prioritize primary label, sex, age bin, grade group, modality pattern, and fNIRS device.
- Rare fine-grained strata were collapsed to coarser labels so that the 20% test split and 5-fold CV remain feasible.
- The split is deterministic for seed `20260707` and should be treated as fixed for downstream experiments.
