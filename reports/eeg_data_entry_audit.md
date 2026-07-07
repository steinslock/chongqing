# EEG Data Entry Audit

Task-level tables inherit `subject_splits_v1.csv`; one row per `L_id` per task.

## rest

| metric | value |
|---|---:|
| `rows` | 4497 |
| `data_bdf_exists` | 1296 |
| `data_bdf_readable` | 1296 |
| `event_bdf_readable` | 1296 |
| `qc_pass` | 1283 |
| `traditional_feature_exists` | 1247 |
| `deep_window_cache_exists` | 1296 |

## oddball

| metric | value |
|---|---:|
| `rows` | 4497 |
| `data_bdf_exists` | 2309 |
| `data_bdf_readable` | 2309 |
| `event_bdf_readable` | 2309 |
| `qc_pass` | 2285 |
| `traditional_feature_exists` | 0 |
| `deep_window_cache_exists` | 2309 |

## 1back

| metric | value |
|---|---:|
| `rows` | 4497 |
| `data_bdf_exists` | 1773 |
| `data_bdf_readable` | 1773 |
| `event_bdf_readable` | 1773 |
| `qc_pass` | 1694 |
| `traditional_feature_exists` | 0 |
| `deep_window_cache_exists` | 1773 |

## Notes

- Header readability is checked without loading full BDF signals.
- Event code counts are taken from existing v1 deep-window metadata where present.
- Old v1 features/cache are treated as readiness evidence only, not as fixed-split model results.
