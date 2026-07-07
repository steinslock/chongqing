# fNIRS Data Entry Audit

All tables inherit `subject_splits_v1.csv`; each device/task table has one row per `L_id`.

## yiruid_rest

| metric | value |
|---|---:|
| `rows` | 4497 |
| `raw_file_exists` | 1894 |
| `file_readable` | 1894 |
| `hbo_hbr_exists_or_computable` | 1894 |
| `event_marker_exists` | 1894 |
| `qc_pass` | 1894 |

## yiruid_oddball

| metric | value |
|---|---:|
| `rows` | 4497 |
| `raw_file_exists` | 676 |
| `file_readable` | 676 |
| `hbo_hbr_exists_or_computable` | 676 |
| `event_marker_exists` | 676 |
| `qc_pass` | 676 |

## yiruid_vft

| metric | value |
|---|---:|
| `rows` | 4497 |
| `raw_file_exists` | 1851 |
| `file_readable` | 1851 |
| `hbo_hbr_exists_or_computable` | 1851 |
| `event_marker_exists` | 1851 |
| `qc_pass` | 1851 |

## yiruid_1back

| metric | value |
|---|---:|
| `rows` | 4497 |
| `raw_file_exists` | 1772 |
| `file_readable` | 1772 |
| `hbo_hbr_exists_or_computable` | 1772 |
| `event_marker_exists` | 1771 |
| `qc_pass` | 1772 |

## yiruid_doors

| metric | value |
|---|---:|
| `rows` | 4497 |
| `raw_file_exists` | 1033 |
| `file_readable` | 1033 |
| `hbo_hbr_exists_or_computable` | 1033 |
| `event_marker_exists` | 1033 |
| `qc_pass` | 1033 |

## bikom_rest

| metric | value |
|---|---:|
| `rows` | 4497 |
| `raw_file_exists` | 1275 |
| `file_readable` | 1275 |
| `hbo_hbr_exists_or_computable` | 1275 |
| `event_marker_exists` | 1275 |
| `qc_pass` | 1275 |

## bikom_oddball

| metric | value |
|---|---:|
| `rows` | 4497 |
| `raw_file_exists` | 633 |
| `file_readable` | 633 |
| `hbo_hbr_exists_or_computable` | 633 |
| `event_marker_exists` | 633 |
| `qc_pass` | 633 |

## bikom_vft

| metric | value |
|---|---:|
| `rows` | 4497 |
| `raw_file_exists` | 1281 |
| `file_readable` | 1281 |
| `hbo_hbr_exists_or_computable` | 1281 |
| `event_marker_exists` | 1281 |
| `qc_pass` | 1281 |

## bikom_1back

| metric | value |
|---|---:|
| `rows` | 4497 |
| `raw_file_exists` | 1245 |
| `file_readable` | 1245 |
| `hbo_hbr_exists_or_computable` | 1245 |
| `event_marker_exists` | 1245 |
| `qc_pass` | 1245 |

## bikom_doors

| metric | value |
|---|---:|
| `rows` | 4497 |
| `raw_file_exists` | 645 |
| `file_readable` | 641 |
| `hbo_hbr_exists_or_computable` | 641 |
| `event_marker_exists` | 645 |
| `qc_pass` | 641 |

## Notes

- Yiruid `.nirs` files expose MATLAB variables such as `d`, `t`, `ml`, `s`, and `Mark_infor` when readable.
- Bikom CSV files provide HbO/HbR/HbT/Mes-style outputs; raw light intensity is not present in the CSV probe.
- Full motion/channel QC and Hb conversion require Goal 4 device-specific preprocessing, not Goal 2.5 formal training.
