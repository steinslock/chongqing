# Goal 2.8 Final Report

Date: 2026-09-08

Goal 2.8 rebuilt every objective feature layer from an attachment-sourced
paradigm specification and reran the Goal 2.7 protocol without modification.
This report records what was measured. It does not issue a go/no-go decision.

## What Changed and What Did Not

Unchanged: the fixed Standard and Group-aware five-fold splits, three-fold inner
CV for hyperparameters and thresholds, the Logistic Regression / Random Forest /
HistGradientBoosting families and their grids, 1000-resample subject bootstrap
CIs and 1000-resample paired increment tests, and the exclusion of the
baseline-exposed pilot holdout.

Changed: the features. Every event code, block boundary, duration and marker
meaning now comes from `configs/goal2_8/paradigm_spec.yaml`, which carries the
dataset attachment each value was taken from, and is checked against sampled raw
files by `scripts/check_paradigm_conformance.py` (68 of 68 checks pass).

## The Goal 2.7 Premises That Did Not Hold

Each was verified against the raw files. Details and root causes are in
`reports/goal2_7_superseded_notice.md`.

| Goal 2.7 premise | What the raw data shows |
|---|---|
| The Oddball cache holds only code 22, so target/standard ERP is impossible | Raw `*_evt.bdf` holds both code 11 (500 Hz standard, median 123/subject) and code 22 (1000 Hz deviant target, median 25/subject) in 313 of 313 sampled subjects. The target-only cache came from a hardcoded `event_codes: ["22"]` in the v1 window builder |
| 1BACK codes 18/19 have unconfirmed condition semantics | They are positional: 19 marks the first stimulus of each of two blocks (exactly 2 per subject), 18 marks every later stimulus, SOA 2.00 s |
| Yiruid wavelengths and optode geometry are unconfirmed | Every `.nirs` file carries `SD.Lambda = [690, 830]` nm, 16 sources, 16 detectors, 3D optode positions and a measurement list. The old reader inspected file headers only |
| fNIRS task timing is unconfirmed, so task-response features are blocked | Block timing is confirmed for all five tasks on both devices from marker streams, paradigm scripts and `附件/脑机接口.pdf` |
| Face is shortcut-dominated (measured on unsegmented video) | `面部2-任务` is an approximately 11-minute multi-phase session; Goal 2.7 sampled 16 frames uniformly across the whole session |

## Re-derived Features

| Modality | Unit | Subjects | Signal features |
|---|---|---|---|
| EEG | oddball | 1820 / 1853 | 321 |
| EEG | 1back | 1278 / 1413 | 181 |
| EEG | rest | 1003 / 1043 | 63 |
| fNIRS Yiruid | rest / vft / 1back / oddball / doors | 1514 / 1480 / 1423 / 524 / 825 | 38 / 80 / 80 / 80 / 80 |
| fNIRS Bikom | rest / vft / 1back / oddball / doors | 1017 / 1022 / 995 / 508 / 515 | 40 / 40 / 86 / 86 / 86 |
| Face | valence contrast and per-segment | 3381 / 3382 | 512 per block |

Signal validity was confirmed independently of any label:

- The Oddball target-minus-standard difference wave over 1820 subjects peaks at
  Pz at +6.40 uV in the 0.28-0.55 s window, with a parietal maximum, Fz negative
  at -2.45 uV, positive in 88.1 percent of subjects, Cohen d = 1.08.
- Every Yiruid fNIRS task shows the canonical haemodynamic response with block
  counts matching the specification: VFT +0.343 / -0.128 uM over 4 blocks and
  left-lateralised, 1BACK +0.632 / -0.215 over 2, Oddball +0.405 / -0.130 over
  10, Doors +0.055 / -0.068 over 6.
- Face detection with YuNet reached a rate of 1.000 across 48 frames per
  subject. The within-subject valence contrast has 17.4 percent of the magnitude
  of a raw segment embedding, so most of the raw embedding is subject-constant
  and cancels.

## Model Matrix

380 datasets across two CV protocols, 2200 pooled metric rows, 1,623,018
subject-level OOF predictions, 22,000 bootstrap CI rows, 444 paired comparisons.
Bikom was excluded from the primary matrix (see Device Confound below).

Best pooled AUROC by feature-set family, inner-CV thresholds:

| modality | protocol | signal / face | shortcut (background, group proxy, full frame) | demographics |
|---|---|---|---|---|
| eeg | standard_cv | 0.5904 | 0.6245 | 0.6470 |
| eeg | group_cv | 0.5640 | 0.5532 | 0.5947 |
| fnirs | standard_cv | 0.6003 | 0.6756 | 0.6943 |
| fnirs | group_cv | 0.5940 | 0.6042 | 0.6235 |
| face | standard_cv | 0.6685 | 0.6798 | 0.6721 |
| face | group_cv | 0.6659 | 0.6573 | 0.6602 |

Demographic decomposition in the largest cohorts, Standard CV: age alone 0.52 to
0.53, sex alone 0.57, grade alone 0.54 to 0.56, age+sex+grade 0.59 to 0.60,
acquisition-group proxy alone 0.60 to 0.63, demographics plus group 0.64 to 0.66.

## Paired Increments

240 required comparisons. The decision-relevant subset is the 216 increments
**over demographics**; the remaining 24 are shortcut controls against background.

| comparison group | rows | significant positive | significant negative |
|---|---|---|---|
| over demographics | 216 | **0** | 78 |
| over background (shortcut control) | 24 | 14 | 1 |

Across the 216 demographics increments the AUROC difference ranges from -0.1243
to +0.0467, and no interval excludes zero on the positive side.

| modality | demographics-increment rows | positive standard_cv | positive group_cv | negative | positive over shortcut controls |
|---|---|---|---|---|---|
| eeg | 72 | 0 | 0 | 43 | 0 |
| fnirs | 120 | 0 | 0 | 19 | 0 |
| face | 24 | 0 | 0 | 16 | 14 |

The 14 positive rows are all Face against background: `face_vs_background` in 10
rows and `face_demographics_vs_background_demographics` in 4, under both
protocols. The largest is Random Forest on the valence contrast under group CV at
+0.1153, 95 percent CI [0.0858, 0.1450]. No `face_vs_demographics` or
`face_demographics_vs_demographics` row is positive.

So Face carries information beyond the room and the recording setting, including
under a contrast that cancels identity, appearance and acquisition site within
subject, while not exceeding age, sex and grade.

## Device Confound

The two fNIRS devices were used on disjoint cohorts: 1527 Yiruid subjects, 1022
Bikom subjects, **1 subject in common**, which the split file itself records as
`fnirs_device = both` for exactly one row. Five of 22 sites used both devices;
most sites are device-exclusive. Label prevalence differs (Yiruid 0.387, Bikom
0.315). Device and acquisition site therefore cannot be separated, and no
within-subject device comparison is possible.

Bikom features carry no univariate label signal: median univariate AUROC 0.502,
with 2 of 22 features beyond 0.03 of chance against 44 of 77 for Yiruid. Its
parsing is validated independently (group-mean HbO change point at 29.5 s, mark
sequences matching exactly, canonical Oddball block responses), and its feature
distributions are well formed. Under group-aware CV it falls below chance, which
is the expected consequence of fitting site structure and testing on other sites.
Bikom was excluded from the primary matrix on that basis.

## Label Definition

Demographic predictability does not depend on how the label is cut. Under
Standard CV with age, sex and grade: `primary_label_nonhealthy` 0.6697,
`sensitivity_label_mdd_highrisk` 0.6731, `sensitivity_label_clear_diagnosis`
0.6730. Adding the site proxy gives 0.7062, 0.7076 and 0.7215 respectively.
Removing the 744 high-risk subjects does not lower the demographic baseline.

## Reproducibility

Single environment `chongqing_v1`; `source activate.local.sh`.

```
python scripts/check_paradigm_conformance.py
python scripts/build_eeg_goal2_8_epochs.py --task {oddball,1back}
python scripts/extract_eeg_goal2_8_features.py --task {oddball,1back,rest}
python scripts/extract_fnirs_goal2_8_features.py --device all --task all
python scripts/extract_face_goal2_8_features.py --stage index
python scripts/extract_face_goal2_8_features.py --stage features --shard i --n-shards 8
python scripts/extract_face_goal2_8_features.py --stage merge
python scripts/run_goal2_8.py --n-workers 24
python scripts/summarize_goal2_8.py
python -m unittest discover -s tests
```

148 unit tests pass. All feature tables and OOF predictions contain only
`split_group == cv` rows with zero pilot-holdout subjects. The split files are
byte-identical to their committed state.

Machine-readable outputs are under `results/goal2_8/`, including
`required_increments.csv` and `modality_decision.csv`. The uncompressed OOF CSVs
and the ERP and embedding arrays stay local; deterministic gzip archives of both
OOF files are tracked.
