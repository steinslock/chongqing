# Goal 2.7 fNIRS Event and Timing Audit

The audit inspects Yiruid `.nirs` marker arrays and Bikom CSV `Mark` columns. Formal task-response features require marker-confirmed or protocol-confirmed timing; the old 20/60/20 fallback is not used.

## Marker Inventory

| device | task | marker_count | subjects | segment_status |
| --- | --- | --- | --- | --- |
| yiruid | vft | 1 | 1904 | markers_present_but_timing_semantics_unconfirmed |
| yiruid | 1back | -1 | 1 | segment_blocked_no_markers |
| yiruid | 1back | 2 | 1823 | markers_present_but_timing_semantics_unconfirmed |
| yiruid | rest | 0 | 1949 | event_free_whole_recording |
| bikom | vft | 0 | 1307 | segment_blocked_no_markers |
| bikom | vft | 1 | 1 | markers_present_but_timing_semantics_unconfirmed |
| bikom | 1back | 0 | 14 | segment_blocked_no_markers |
| bikom | 1back | 5 | 1 | markers_present_but_timing_semantics_unconfirmed |
| bikom | 1back | 6 | 1257 | markers_present_but_timing_semantics_unconfirmed |
| bikom | rest | 0 | 81 | event_free_whole_recording |
| bikom | rest | 1 | 292 | event_free_whole_recording |
| bikom | rest | 2 | 916 | event_free_whole_recording |
| bikom | rest | 3 | 13 | event_free_whole_recording |

## Timing Summary

| device | task | subjects | raw_rows_min | raw_rows_median | raw_rows_max | duration_min_sec | duration_median_sec | duration_max_sec | rows_gt_2000 | markers_after_2000 | formal_task_response_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| yiruid | vft | 1904 | 3000 | 3000.0 | 3020 | 149.95000000000002 | 149.95000000000002 | 150.95000000000002 | 1904 | 0 | blocked_without_confirmed_timing |
| yiruid | 1back | 1824 | 3080 | 3140.0 | 6720 | 153.95000000000002 | 156.95000000000002 | 335.95000000000005 | 1823 | 1 | blocked_without_confirmed_timing |
| yiruid | rest | 1949 | 6500 | 7000.0 | 9260 | 324.95000000000005 | 349.95000000000005 | 462.95000000000005 | 1949 | 0 | whole_recording |
| bikom | vft | 1308 | 1251 | 1700.0 | 1709 | 125.0 | 169.9 | 170.8 | 0 | 0 | blocked_without_confirmed_timing |
| bikom | 1back | 1272 | 0 | 1553.0 | 1559 | 124.3 | 155.2 | 155.8 | 0 | 0 | blocked_without_confirmed_timing |
| bikom | rest | 1302 | 57 | 3497.0 | 6771 | 5.6 | 349.6 | 677.0 | 1295 | 939 | whole_recording |

## Interpretation

- Rest is modeled as whole-recording.
- VFT and 1BACK task-response features are blocked unless a later protocol document confirms segment timing.
- Bikom is audited with full-file rows; the Goal 2.6 fixed 2000-row cap is not used.
- Yiruid features are named raw/log-intensity or OD-like; no HbO/HbR claim is made.
