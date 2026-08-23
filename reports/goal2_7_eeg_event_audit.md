# Goal 2.7 EEG Event Audit

The audit uses v1 cached-window metadata and the v1 cache script. Code numbers are not interpreted as task semantics unless a project-local mapping is available.

## Event Inventory

| task | event_code | window_count | subject_count | semantic_status | epoch_tmin_sec | epoch_tmax_sec | baseline_interval |
| --- | --- | --- | --- | --- | --- | --- | --- |
| rest |  | 67332 | 1284 | event_free_rest | 0.0 | 5.0 | not_confirmed |
| oddball | 22 | 52193 | 2285 | blocked_target_nontarget_not_confirmed_cache_code22_only | -0.2 | 0.8 | not_confirmed |
| 1back | 18 | 22845 | 1686 | blocked_condition_semantics_not_confirmed | -0.2 | 1.8 | not_confirmed |
| 1back | 19 | 1935 | 1273 | blocked_condition_semantics_not_confirmed | -0.2 | 1.8 | not_confirmed |

## Interpretation

- Rest is event-free and usable as whole-recording/window-generic signal.
- Oddball cache contains only code `22` windows with approximately -0.2 to 0.8 s epochs; target/non-target semantics are not proven, so formal Oddball ERP is blocked and the cache is used only as `oddball_target_only_proxy`.
- 1BACK cache contains codes `18` and `19` with approximately -0.2 to 1.8 s epochs; code semantics are not proven, so condition-difference features are blocked and only generic signal features are used.
- Baseline intervals were not confirmed from project-local documentation.
