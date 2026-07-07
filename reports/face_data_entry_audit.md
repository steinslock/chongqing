# Face Data Entry Audit

Each Face table inherits `subject_splits_v1.csv`; one row per `L_id` and video task.

## self_intro

| metric | value |
|---|---:|
| `rows` | 4497 |
| `file_exists` | 4468 |
| `file_readable` | 4468 |
| `qc_pass` | 4467 |
| `duplicate_l_id_files` | 0 |

## task

| metric | value |
|---|---:|
| `rows` | 4497 |
| `file_exists` | 4462 |
| `file_readable` | 4458 |
| `qc_pass` | 4458 |
| `duplicate_l_id_files` | 0 |

## Checks

- Same `L_id` fold consistency is inherited from the global split table.
- Duplicate `L_id` video files are counted by task.
- Full frame-by-frame corruption and face-detection audit is not run at full scale in Goal 2.5; smoke tests validate that the path is executable on CV-pool samples.
- Codec/resolution/fps are retained as shortcut-risk variables and must be tested before formal Face modeling.
