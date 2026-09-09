# Eye-Tracking Readiness Audit (Goal 2.10)

Stage: readiness only. No features, no models, no labels in any check.

Specification: `configs/goal2_10/eye_paradigm_spec.yaml` (attachment-derived: False).

## Verdict

9 of 9 `device x task` units pass every readiness check.

| unit | verdict | failed checks |
|---|---|---|
| `qixin_120/free_viewing` | **READY** | - |
| `qixin_120/saccade` | **READY** | - |
| `qixin_120/smooth_pursuit` | **READY** | - |
| `qixin_500/free_viewing` | **READY** | - |
| `qixin_500/saccade` | **READY** | - |
| `qixin_500/smooth_pursuit` | **READY** | - |
| `tobii/free_viewing` | **READY** | - |
| `tobii/saccade` | **READY** | - |
| `tobii/smooth_pursuit` | **READY** | - |

Every threshold is fixed by the paradigm or by physiology, so a failure means a parsing or acquisition problem, not an absent effect. Thresholds: timeline_complete_rate 0.9, valid_sample_fraction 0.7, on_face_over_chance 5.0, pro_corr_x 0.3, anti_corr_x_max 0.0, pursuit_corr_x 0.5, aoi_eyes_minus_mouth 0.0.

## Coverage

3621 recordings on disk, 3481 kept after deduplication, covering **1187 unique subjects**, 1158 in the manifest and **919 in the development split**.

| device | subjects | CV subjects |
|---|---|---|
| `qixin_120` | 432 | 336 |
| `qixin_500` | 420 | 331 |
| `tobii` | 337 | 253 |

Subjects shared between devices: qixin_120&qixin_500 1, qixin_120&tobii 0, qixin_500&tobii 1.

### Manifest reconciliation

Joining on `A_id` finds 1187 subjects against the manifest's `has_eye_direct` = 281 and `has_eye_name_mapped` = 852. 911 subjects have a recording that `has_eye_direct` does not flag; 5 are flagged with no recording found.

has_eye_direct is computed by chongqing_binary.audit._extract_l_ids, which greps paths for L\d+. Eye paths carry A_id only, so the column undercounts. Eye cohorts must join on A_id.

## Paradigm conformance

| unit | n | expected segments | complete | rate | observed counts |
|---|---|---|---|---|---|
| `qixin_120/free_viewing` | 414 | 110 | 414 | 1.000 | 110x414 |
| `qixin_120/saccade` | 413 | 10 | 413 | 1.000 | 10x413 |
| `qixin_120/smooth_pursuit` | 431 | 2 | 431 | 1.000 | 2x431 |
| `qixin_500/free_viewing` | 390 | 109 | 388 | 0.995 | 109x388, 108x1, 0x1 |
| `qixin_500/saccade` | 404 | 10 | 404 | 1.000 | 10x404 |
| `qixin_500/smooth_pursuit` | 416 | 2 | 415 | 0.998 | 2x415, 0x1 |
| `tobii/free_viewing` | 336 | 109 | 336 | 1.000 | 109x336 |
| `tobii/saccade` | 337 | 10 | 337 | 1.000 | 10x337 |
| `tobii/smooth_pursuit` | 337 | 2 | 337 | 1.000 | 2x337 |

- `qixin_120/free_viewing` face presentation error against the specified 4000 ms: median 2.0 ms, largest absolute 3.0 ms.
- `qixin_500/free_viewing` face presentation error against the specified 4000 ms: median 2.0 ms, largest absolute 10.0 ms.
- `tobii/free_viewing` face presentation error against the specified 4000 ms: median -19.48 ms, largest absolute 19.56 ms.

## Acquisition quality

| device | read ok | read failures | valid sample fraction | sampling rate Hz | clock scale | long gaps | pupil mm | valid < 0.5 |
|---|---|---|---|---|---|---|---|---|
| `qixin_120` | 1258 | 0 | 0.980 [0.957, 0.994] | 120.1 [119.4, 120.1] | 0.99999 [0.99992, 1.00008] | 1.0 [0.0, 4.0] | 4.80 [4.32, 5.34] | 1 |
| `qixin_500` | 1210 | 0 | 0.975 [0.952, 0.988] | 501.0 [500.7, 501.2] | 0.99674 [0.99588, 0.99734] | 1.0 [0.0, 3.0] | 4.53 [3.97, 5.22] | 0 |
| `tobii` | 1010 | 0 | 0.897 [0.857, 0.926] | 60.9 [60.5, 61.3] | n/a | 5.0 [3.0, 9.0] | 4.64 [4.08, 5.28] | 9 |

Values are median [Q1, Q3] across recordings.

## Label-free validity

| unit | check | median [Q1, Q3] |
|---|---|---|
| `qixin_120/free_viewing` | on_face_fraction | 0.971 [0.947, 0.988] |
| `qixin_120/free_viewing` | on_face_over_chance | 18.426 [17.975, 18.747] |
| `qixin_120/free_viewing` | chance_fraction | 0.053 [0.053, 0.053] |
| `qixin_120/free_viewing` | aoi_eyes_share | 0.524 [0.417, 0.614] |
| `qixin_120/free_viewing` | aoi_mouth_share | 0.180 [0.130, 0.239] |
| `qixin_120/free_viewing` | aoi_face_other_share | 0.243 [0.197, 0.293] |
| `qixin_120/free_viewing` | aoi_off_face_share | 0.029 [0.012, 0.053] |
| `qixin_120/free_viewing` | aoi_eyes_minus_mouth | 0.339 [0.184, 0.474] |
| `qixin_120/free_viewing` | raw_aoi_eyes_minus_mouth | -0.103 [-0.341, 0.153] |
| `qixin_120/free_viewing` | drift_dx | 0.002 [-0.004, 0.012] |
| `qixin_120/free_viewing` | drift_dy | 0.056 [0.033, 0.086] |
| `qixin_120/free_viewing` | drift_n_crosses | 37.000 [37.000, 37.000] |
| `qixin_120/saccade` | pro_corr_x | 0.771 [0.731, 0.807] |
| `qixin_120/saccade` | anti_corr_x | -0.552 [-0.621, -0.466] |
| `qixin_120/saccade` | pro_direction_correct_rate | 1.000 [1.000, 1.000] |
| `qixin_120/saccade` | anti_direction_correct_rate | 1.000 [1.000, 1.000] |
| `qixin_120/saccade` | pro_n_trials_scored | 8.000 [8.000, 8.000] |
| `qixin_120/saccade` | anti_n_trials_scored | 8.000 [8.000, 8.000] |
| `qixin_120/smooth_pursuit` | pursuit_corr_x | 0.942 [0.917, 0.965] |
| `qixin_120/smooth_pursuit` | pursuit_corr_y | 0.920 [0.884, 0.950] |
| `qixin_500/free_viewing` | on_face_fraction | 0.982 [0.956, 0.994] |
| `qixin_500/free_viewing` | on_face_over_chance | 18.628 [18.143, 18.857] |
| `qixin_500/free_viewing` | chance_fraction | 0.053 [0.053, 0.053] |
| `qixin_500/free_viewing` | aoi_eyes_share | 0.481 [0.403, 0.569] |
| `qixin_500/free_viewing` | aoi_mouth_share | 0.208 [0.163, 0.258] |
| `qixin_500/free_viewing` | aoi_face_other_share | 0.260 [0.224, 0.310] |
| `qixin_500/free_viewing` | aoi_off_face_share | 0.018 [0.006, 0.044] |
| `qixin_500/free_viewing` | aoi_eyes_minus_mouth | 0.269 [0.159, 0.405] |
| `qixin_500/free_viewing` | raw_aoi_eyes_minus_mouth | -0.145 [-0.324, 0.090] |
| `qixin_500/free_viewing` | drift_dx | -0.002 [-0.008, 0.004] |
| `qixin_500/free_viewing` | drift_dy | 0.052 [0.029, 0.081] |
| `qixin_500/free_viewing` | drift_n_crosses | 36.000 [36.000, 36.000] |
| `qixin_500/saccade` | pro_corr_x | 0.756 [0.718, 0.792] |
| `qixin_500/saccade` | anti_corr_x | -0.531 [-0.598, -0.444] |
| `qixin_500/saccade` | pro_direction_correct_rate | 1.000 [1.000, 1.000] |
| `qixin_500/saccade` | anti_direction_correct_rate | 1.000 [0.875, 1.000] |
| `qixin_500/saccade` | pro_n_trials_scored | 8.000 [8.000, 8.000] |
| `qixin_500/saccade` | anti_n_trials_scored | 8.000 [8.000, 8.000] |
| `qixin_500/smooth_pursuit` | pursuit_corr_x | 0.935 [0.913, 0.953] |
| `qixin_500/smooth_pursuit` | pursuit_corr_y | 0.903 [0.864, 0.933] |
| `tobii/free_viewing` | on_face_fraction | 0.980 [0.950, 0.993] |
| `tobii/free_viewing` | on_face_over_chance | 18.598 [18.020, 18.831] |
| `tobii/free_viewing` | chance_fraction | 0.053 [0.053, 0.053] |
| `tobii/free_viewing` | aoi_eyes_share | 0.539 [0.446, 0.649] |
| `tobii/free_viewing` | aoi_mouth_share | 0.172 [0.118, 0.223] |
| `tobii/free_viewing` | aoi_face_other_share | 0.242 [0.182, 0.279] |
| `tobii/free_viewing` | aoi_off_face_share | 0.020 [0.007, 0.050] |
| `tobii/free_viewing` | aoi_eyes_minus_mouth | 0.362 [0.230, 0.526] |
| `tobii/free_viewing` | raw_aoi_eyes_minus_mouth | 0.245 [-0.027, 0.481] |
| `tobii/free_viewing` | drift_dx | -0.001 [-0.004, 0.003] |
| `tobii/free_viewing` | drift_dy | 0.015 [0.001, 0.031] |
| `tobii/free_viewing` | drift_n_crosses | 36.000 [36.000, 36.000] |
| `tobii/saccade` | pro_corr_x | 0.822 [0.779, 0.849] |
| `tobii/saccade` | anti_corr_x | -0.614 [-0.672, -0.532] |
| `tobii/saccade` | pro_direction_correct_rate | 1.000 [1.000, 1.000] |
| `tobii/saccade` | anti_direction_correct_rate | 1.000 [1.000, 1.000] |
| `tobii/saccade` | pro_n_trials_scored | 8.000 [8.000, 8.000] |
| `tobii/saccade` | anti_n_trials_scored | 8.000 [8.000, 8.000] |
| `tobii/smooth_pursuit` | pursuit_corr_x | 0.971 [0.940, 0.987] |
| `tobii/smooth_pursuit` | pursuit_corr_y | 0.939 [0.892, 0.967] |

## Stimulus regions

36 stimuli, detector `opencv_yunet`, lowest detection score 0.907. Eye and mouth bands disjoint: True; both inside the visible face: True. Median screen-area share: eyes 0.0150, mouth 0.0106, face 0.0529.

## Device and acquisition site

| A_id prefix | `qixin_120` | `qixin_500` | `tobii` |
|---|---|---|---|
| A02 | 26 | 46 | 37 |
| A04 | 0 | 28 | 23 |
| A10 | 0 | 33 | 20 |
| B01 | 0 | 26 | 25 |
| B03 | 0 | 52 | 37 |
| B05 | 0 | 17 | 12 |
| B14 | 35 | 0 | 0 |
| B15 | 18 | 0 | 0 |
| B16 | 23 | 0 | 0 |
| C02 | 17 | 0 | 0 |
| C17 | 10 | 0 | 0 |
| C18 | 102 | 0 | 0 |
| D08 | 54 | 0 | 0 |
| D13 | 0 | 37 | 27 |
| E06 | 0 | 39 | 38 |
| E16 | 51 | 53 | 34 |

CV subjects only. A prefix served by a single device means device and acquisition site cannot be separated there, exactly as for the two fNIRS devices.

## Deduplication

Discard reasons: missing_a_id 27, duplicate_take 113.

Duplicate takes per unit: qixin_120/free_viewing 25, qixin_120/saccade 22, qixin_120/smooth_pursuit 8, qixin_500/free_viewing 17, qixin_500/saccade 10, qixin_500/smooth_pursuit 31.

The kept take is the one with a complete presentation timeline, then the most media segments, then the longest recording, then the latest. Every component comes from the recording, never from the label.

## Stimulus-side products

36 free-viewing face stimuli, median face box covering 0.0529 of the screen, x in [0.420, 0.580], y in [0.335, 0.665].

| video | frames | fps | duration ms | target x | trials |
|---|---|---|---|---|---|
| prosaccade_formal | 1200 | 60 | 20000 | 0.218, 0.36, 0.5, 0.64, 0.782 | 8 |
| antisaccade_formal | 1200 | 60 | 20000 | 0.218, 0.36, 0.5, 0.64, 0.782 | 8 |
| prosaccade_practice | 600 | 60 | 10000 | 0.218, 0.36, 0.5, 0.64, 0.782 | 4 |
| antisaccade_practice | 600 | 60 | 10000 | 0.218, 0.36, 0.5, 0.64, 0.782 | 4 |
| pursuit | 8160 | 60 | 136000 | continuous, 229 distinct in [0.202, 0.798] | - |

