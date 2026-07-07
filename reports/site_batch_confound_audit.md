# Goal 2.5 Site/Batch/Device Confound Audit

A direct clinical site or school identifier is not present in the canonical manifest. The most stable available grouping proxy is the anonymized `A_id` prefix. Goal 2.5 writes `group_code = first three characters of A_id` as a batch/site-proxy for audit and robustness only.

## Summary

| metric | value |
|---|---:|
| `subjects` | 4497 |
| `a_prefix3_groups` | 51 |
| `groups_n_ge_20` | 36 |
| `groups_high_shortcut_risk` | 6 |

## Interpretation

- `A_id` prefix is reliable as a stable anonymized grouping key, but its real-world meaning is not confirmed.
- fNIRS device is an explicit device confound and is retained in `subject_groups.csv` and cohort outputs.
- Face codec/resolution/fps are audited in Face video tables and should be tested as shortcut-only features before formal Face modeling.
- `subject_splits_group_robustness_v1.csv` is generated only for robustness analysis. It does not replace `subject_splits_v1.csv` and must not be used for model selection based on performance.

## Attempted Variables

- Manifest: `A_id`, demographics, modality flags, fNIRS device.
- Raw directories: EEG task naming, fNIRS device/task directories, Face video metadata.
- Direct school/site/camera fields were not found in the canonical manifest.
