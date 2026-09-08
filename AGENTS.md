# Chongqing Binary Diagnosis Agents

Last updated: 2026-09-08

## Project Root

Use the directory containing this file as the project root. The current host
uses:

`/data/home/cqm/Project/Code/chongqing`

The project is relocatable and does not require this path on another host. Set
`CHONGQING_RAW_DATA_DIR` to the absolute raw-dataset path before running an
entry point when the new host does not use the current default. See
`MIGRATION.md`.

## Environment

There is exactly **one** project environment: `chongqing_v1`. The former
`avmoe` / `chongqing_v1` split was removed on 2026-09-07. `chongqing_v1` now
carries MNE, OpenCV, torch/torchvision, scikit-learn, scipy and openpyxl
together, so EEG, fNIRS, Face and spreadsheet work all run in one process.

```bash
source activate.local.sh    # activates chongqing_v1, sets PYTHONPATH=src and the raw data dir
```

Keep `avmoe` only if you need to reproduce historical Goal 2.7 artifacts. Do not
use it for new work, and do not reintroduce a second environment.

## No Hash Constraints

Hash-based restrictions are abolished. Agents working on this project must:

- never treat a SHA-256 value, a release manifest, or a checksum file as a
  reason not to edit a file;
- never gate, block, or defer a change because it would "invalidate a manifest";
- never emit hashes, checksum tables, or hash-verification steps in reports,
  plans, commit messages, or chat output;
- never add new checksum-generation or checksum-verification code.

If a file should change, change it. Provenance is carried by Git history and by
the dated entries in `PROGRESS.md`, not by checksums.

`artifacts/goal2_7/release_manifest.json` and
`scripts/build_goal2_7_release_manifest.py` are retired historical artifacts.
Do not extend, regenerate, or validate against them.

## Current Stage

Goal 2.7 is complete but its modality conclusions are **superseded**. Goal 2.8's
measurement is complete and its go/no-go decision is still open. Goal 2.9, the
behavioural feature layer, is the active stage.

Goal 2.7 concluded that no modality carried independent signal. That conclusion
rested on three incorrect readings of the raw data, each verified against the
source files on 2026-09-07:

- EEG Oddball raw `*_evt.bdf` contains **both** code `11` (500 Hz standard,
  about 125 per subject) and code `22` (1000 Hz deviant target, about 25 per
  subject). Only the v1 window cache was target-only, because
  `experiments/v1/eeg/scripts/cache_deep_windows.py` hardcodes
  `event_codes: ["22"]`. Target/standard ERP is fully recoverable.
- EEG 1BACK codes `18`/`19` are **positional**, not conditions: `19` is the
  first stimulus of each block (exactly 2 per subject), `18` is every later
  stimulus, SOA 2.0 s.
- Yiruid `.nirs` files are standard HOMER2 MATLAB files carrying
  `SD.Lambda = [690, 830]` nm, 16 sources, 16 detectors, 3D optode positions and
  a marker matrix. The old reader only inspected the file header, which is why
  wavelength and geometry looked unconfirmed.

fNIRS block timing is confirmed for every task and device from the paradigm
scripts, the recorded marker streams and `附件/脑机接口.pdf`. Face `面部2-任务`
is an approximately 11 minute multi-phase session, not a single clip.

The site/acquisition-group shortcut finding from Goal 2.7 stands and is
unaffected by the above.

## Goal 2.8

Goal 2.8 is event-semantics recovery and feature re-derivation. It keeps the
fixed splits, the evaluation protocol and the shortcut controls unchanged, and
replaces only the feature layer:

- drive all event codes, block counts, durations and segment boundaries from a
  single attachment-sourced paradigm specification;
- re-derive EEG epochs from raw BDF with both Oddball conditions, starting with
  Oddball and extending to 1BACK and Rest after it verifies;
- read `.nirs` contents in full, apply the modified Beer-Lambert law to obtain
  real HbO/HbR, and segment all five fNIRS tasks by confirmed block timing;
- segment Face task video into its positive/neutral/negative movie phases and
  model the within-subject valence contrast;
- rerun the model matrix under the same protocol and issue an explicit go/no-go
  for Goal 3, Goal 4 and Goal 5.

Goal 2.8's measurement is complete and its results are recorded in
`reports/goal2_8_final_report.md`. Over the 216 required increments **over
demographics**, none was significantly positive and 78 were significantly
negative, under both CV protocols. Face has 14 significant wins against
background, which are shortcut controls rather than increments over
demographics.

No go/no-go decision has been issued. Do not start Goal 3, Goal 4, Goal 5, deep
training, or multimodal fusion until one is.

## Goal 2.9

Goal 2.9 adds the one feature layer no earlier goal used: the trial-level
keypresses the paradigms recorded next to every fNIRS task. It changes nothing
else. Same fixed splits, same inner CV, same model families and grids, same
1000-resample bootstrap and paired tests, same pilot-holdout exclusion.

Five units carry usable behaviour: Yiruid 1BACK, Oddball and Doors, and Bikom
1BACK and Doors, plus one combined cohort per device. Bikom Oddball is excluded
because that build never collected the keypress.

Goal 2.9 is not Goal 3/4/5 and not fusion. It is a feature layer under the
existing gate, and it does not lift that gate.

Goal 2.9's measurement is complete and its results are recorded in
`reports/goal2_9_final_report.md`. Over the 168 increments over demographics, 8
intervals excluded zero on the positive side and **none is credited**, because
every one of them beat a demographics baseline that was itself below chance; 25
were significantly negative. No go/no-go decision has been issued.

A credited increment now requires the comparator it beat to be **above chance**
in that cohort and protocol. Beating a broken baseline is not an increment. See
`chongqing_binary.goal2_9.report.credit_increments`; this rule applies to any
future stage, not only Goal 2.9.

The paired bootstrap resamples subjects, not folds, so it does not see how
unstable the fit itself is. Any credited increment from a cohort under about 500
subjects must be verified by label permutation on that cohort before it is
reported. `python scripts/verify_goal2_9_positive.py` is the worked example: it
runs a transfer check, a pooling check and a 100-permutation null on the cohort
that produced Goal 2.9's positive result.

## Behaviour Rules

- Trial structure, column names, condition coding and the known log defects come
  from the `behaviour:` section of each fNIRS task in
  `configs/goal2_8/paradigm_spec.yaml`, through
  `chongqing_binary.paradigm.spec.BehaviourTaskSpec`. Do not hardcode them.
- The 1BACK match/non-match label is **derived from the stimulus sequence**, not
  read from the logged condition column. Both devices write an authoritative
  condition on every non-block-initial trial and they agree with the sequence
  exactly, but Bikom writes an arbitrary condition on the block-initial trial
  where no predecessor exists. Agreement is recorded per subject in QC.
- Block-initial trials are excluded from every 1BACK contrast, and lag-1
  measures never cross a block boundary.
- Doors feedback code `1` is **loss** (`-1`, red down arrow) and `2` is **win**
  (`+2`, green up arrow), on both devices. An earlier revision of the
  specification had this reversed; no code had read it.
- Doors feedback is predetermined by the condition file and does not depend on
  the door chosen, so win-stay/lose-shift measures reactivity to feedback, not
  learning.
- Yiruid Doors is **sensitivity-only**: its response window runs 0 to 1.0 s while
  the doors are on screen from 0.5 to 4.5 s, so only 38 percent of choices are
  recorded and RT is censored at 1 s. Bikom Doors records the same task with a
  4 s window at a 98 percent response rate and is the primary device for reward
  behaviour. That is the reverse of the fNIRS signal, where Yiruid is primary.
- Bikom 1BACK has 50 subjects on an earlier arrow-key build whose condition list
  contains no repeated stimulus at all. They are excluded, not coerced.
- The behaviour QC table records log integrity only: files found, trials found
  and expected, block count, conformance, condition agreement. Task performance
  such as response rate belongs to the signal side, otherwise the `signal_qc vs
  qc` comparison tests nothing.
- `脑机接口.pdf` describes an older Doors design (3 blocks of 20, +50/-25, mouse
  clicks) that was not the one run. It is recorded as an antipattern.

## Paradigm-Conformance Rules

The dataset attachments are the authority on how each experiment was actually
run. Code must not drift from them.

- Event codes, block counts, trial counts, SOA, durations, marker semantics and
  segment boundaries must come from `configs/goal2_8/paradigm_spec.yaml` via
  `chongqing_binary.paradigm.spec`. Do not hardcode them in feature code.
- Every value in the specification carries a `source:` field naming the
  attachment it came from.
- `scripts/check_paradigm_conformance.py` validates the specification against
  sampled raw files. A task whose raw data disagrees with the specification is
  reported, not silently coerced.
- When the attachments and the recorded data disagree, record both and prefer
  the recorded data; state the disagreement in the report.

## Read-Only Inputs

Treat these as read-only. On a relocated host, the raw dataset is the path in
`CHONGQING_RAW_DATA_DIR`:

- Raw dataset: `${CHONGQING_RAW_DATA_DIR}` (current default: `/data/home/cqm/Project/Dataset/Chongqing`)
- Existing report bundle: `inputs/derived_reports/chongqing_binary_diagnosis_report`

All generated features, caches, predictions, metrics, models, logs, and reports
must remain under the project root, primarily in `artifacts/`, `results/`,
`reports/`, and `checkpoints/`.

## Split and Evaluation Rules

- Use only subjects with `split_group == cv` for development and reporting.
- Standard CV inherits `artifacts/splits/subject_splits_v1.csv` and `cv_fold`.
- Group CV inherits `artifacts/splits/subject_splits_group_robustness_v1.csv`
  and `robustness_fold`.
- Do not regenerate or overwrite the split files. The pilot holdout is already
  baseline-exposed, so re-splitting cannot recover a clean test set and would
  destroy comparability with every earlier result.
- The same `L_id` must stay in one outer fold across every modality and derived
  unit.
- Hyperparameters, PCA, imputation, scaling, feature selection, and thresholds
  are fit only inside outer-train, using three-fold subject-level inner CV.
- The baseline-exposed pilot holdout is excluded from all development decisions.
- Pooled threshold-dependent metrics must apply each subject's own outer-fold
  inner-CV threshold; fixed threshold 0.5 remains a separate sensitivity result.

## Leakage Rules

Never use diagnosis, labels, clinical scales, self-harm/suicide fields, manual
review fields, or other clinical proxies as objective modality predictors.
Forbidden fields include `diag3`, `primary_label_nonhealthy`, sensitivity labels,
CDRS, CES-DC, HAMA, SCARED, suicide/self-harm, diagnosis, manual-review, and
clinical-scale totals.

Main demographics is age + sex + grade. `grade_group`, acquisition-group proxies,
and fNIRS device are separate sensitivity/shortcut variables. Report objective
modality-only, demographics-only, QC-only, and incremental combinations
separately. Never fold the site proxy into a figure labelled `demographics`:
`demographics_group` and `demographics_group_device` are different feature sets,
and the Goal 2.8 report originally conflated them (corrected 2026-09-08).

On the full 3597-subject development cohort age+sex+grade reaches 0.643 to 0.671
under both protocols and all three model families. Every demographics figure in
the result tables is measured inside a modality cohort of 342 to 3381 subjects
and is lower; quote it with its cohort. `scripts/verify_demographics_baseline.py`
produces the reference.

## Task-Semantics Rules

These replace the Goal 2.7 rules, which asserted blockers that the raw data
does not support.

EEG:

- Rest is event-free and may use whole-recording/window-generic features.
- Oddball code `11` is the frequent 500 Hz standard requiring no response; code
  `22` is the rare 1000 Hz deviant target requiring a keypress. Target/standard
  ERP and the target-minus-standard difference wave are permitted and expected.
- 1BACK code `19` marks the first stimulus of each block and is excluded from
  condition contrasts; code `18` marks every later stimulus. Codes `66`/`77`
  encode response correct/incorrect but are **lagged by one trial**, because the
  paradigm emits them at Begin Routine from the previous trial's result. Code
  `88` is unresolved and must not be used.
- 1BACK block 2 is systematically truncated; block 1 always has 15 stimuli while
  block 2 has 3 to 11. Record the truncation, do not impute it.
- EEG 1BACK match/non-match is **not recoverable** from the archived data. Do
  not fabricate it.

fNIRS:

- Rest is event-free whole-recording for both devices.
- Block timing is confirmed for Yiruid Rest/VFT/1BACK/Oddball/Doors and for
  Bikom Rest/1BACK/Oddball/Doors. Task-response features are permitted where the
  specification is conformant.
- Bikom marks are labelled: `ST`/`ED` bound the recording, `A0`/`A1` open and
  close block 1, `B0`/`B1` block 2. Keep the labels; do not reduce them to 0/1.
- Bikom VFT has no markers. Its timing is protocol-derived, carries
  `timing_confidence: low`, and may only support sensitivity analyses.
- The `Stim Time[s] A,51,B,15,...` header line is identical across all five
  Bikom tasks. It is a leftover device template and must be ignored.
- Yiruid HbO/HbR obtained by the modified Beer-Lambert law from the recorded
  690/830 nm wavelengths and optode geometry may be named as such. Raw or
  log-intensity summaries must still be named as intensity, not haemoglobin.
- Bikom files are read in full; do not reintroduce a fixed 2000-row cap.

## Face Rules

- `面部1-自我介绍1分钟` is a single ~60 s self-introduction clip.
- `面部2-任务` is an ~11 minute session. Segment it with
  `附件/网页数据.xlsx` before extracting features; do not sample uniformly
  across the whole session.
- Movie order is fixed positive, neutral, negative. Stimulus durations are
  93.16 s, 86.64 s and 125.00 s, taken from `面部/面部任务.zip`.
- The primary Face contrast is the within-subject valence contrast, which
  cancels identity, appearance and room background.
- Use the YuNet detector. Falling back to Haar is a QC failure to be recorded,
  not a silent downgrade.
- Frozen visual embeddings may use GPU; classical classifiers and bootstrap are
  CPU workflows.
- Visual embeddings alone enter PCA. Demographics, QC, and metadata bypass PCA
  and are concatenated afterward.
- Failed detections must not become center-crop face samples.
- Strict background uses only detected-face frames with the face region masked
  or blurred.
- Face audio is excluded.
- Contact sheets are local sensitive audit material and must not be pushed to Git.

## Goal 2.8 Entry Points

- Paradigm conformance: `python scripts/check_paradigm_conformance.py`
- EEG epochs: `python scripts/build_eeg_goal2_8_epochs.py`
- EEG features: `python scripts/extract_eeg_goal2_8_features.py`
- fNIRS features: `python scripts/extract_fnirs_goal2_8_features.py`
- Face segments: `python scripts/build_face_goal2_8_segments.py`
- Face features: `python scripts/extract_face_goal2_8_features.py`
- Model matrix: `python scripts/run_goal2_8.py`
- Reports: `python scripts/summarize_goal2_8.py`
- Unit tests: `python -m unittest discover -s tests`

## Goal 2.9 Entry Points

- Behavioural features: `python scripts/extract_behaviour_goal2_9_features.py`
- Model matrix: `python scripts/run_goal2_9.py --n-workers 24`
- Reports: `python scripts/summarize_goal2_9.py`
- Positive-result verification: `python scripts/verify_goal2_9_positive.py`
- Demographics reference baseline: `python scripts/verify_demographics_baseline.py`

## Goal 2.7 Entry Points (historical)

Retained so Goal 2.7 remains reproducible. Its conclusions are superseded.

- Event audit: `python scripts/audit_goal2_7_events.py`
- EEG features: `python scripts/extract_eeg_goal2_7_features.py`
- fNIRS features: `python scripts/extract_fnirs_goal2_7_features.py`
- Face features: `python scripts/extract_face_goal2_7_features.py`
- Full model matrix: `python scripts/run_goal2_7.py --skip-supplemental`
- Restartable bootstrap/paired outputs: `python scripts/run_goal2_7.py --supplemental-only`
- Reports: `python scripts/summarize_goal2_7.py`

Goal 2.6 code, scripts and tests were deleted on 2026-09-07. Its configs,
results and reports are retained as the historical record.

## Publication Policy

Track source, configs, tests, reports, compact features, metrics, and
deterministic compressed OOF archives. Keep the following local:

- uncompressed OOF CSVs larger than GitHub's per-file limit;
- Face embedding CSVs and `.part.csv` checkpoints;
- Face contact sheets and other identifiable source-video frames.

Raw data and the existing input report bundle must never be modified.
