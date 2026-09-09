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

Goal 2.7 is complete but its modality conclusions are **superseded**. Goal 2.8
and Goal 2.9 are measured and their go/no-go decision is still open. **Goal 2.10,
the eye-tracking feature layer, is measured and complete**, and it too issues no
go/no-go decision.

Five feature layers have now returned **no increment over demographics**: EEG,
fNIRS, Face, behaviour and eye tracking. Goal 2.10 credits 0 of 576 increments
over demographics across twelve `device x task` units.

**Goal 3 is measured and complete**; see Goal 3 below. It credits 0 of 26
decision rows and does not lift any gate. Goal 4, Goal 5 and multimodal fusion
remain gated and must not be started.

Six feature layers and one representation layer have now returned no increment
over demographics.

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

No unconditional go/no-go decision has been issued. The conditional go of
2026-09-09 opens Goal 3 for EEG Oddball only and changes nothing else; Goal 4,
Goal 5 and multimodal fusion stay gated.

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

## Goal 2.10

Status: **measurement complete**. Over the 576 increments over demographics,
**0 are credited**; 18 intervals excluded zero and every one of them beat a
demographics baseline below chance, all of them Group CV and all of them
`qixin_120` cohorts, which is the mechanism Goal 2.9 withdrew a result over.
152 were significantly negative. All twelve units return
`NO_INDEPENDENT_SIGNAL`. See `reports/goal2_10_final_report.md`.

Two results from this stage bind future work.

- **The free-viewing valence contrast is not measurable in this paradigm**: 0 of
  46 contrast features reach split-half 0.5 on any device, against 53 of 75
  absolute features. A null on that block is evidence about the paradigm, not
  about attentional bias as a construct, and must never be reported as the
  latter.
- **A coarse validity check that passes is not evidence that a parse is right.**
  The face-box dwell check passed at 18x chance on every device while a
  device-dependent vertical gaze offset was reversing the eye-versus-mouth
  contrast, because the face box is symmetric about screen centre.

Goal 2.10 adds the eye-tracking modality, the one objective modality no earlier
goal used. It changes nothing else: same fixed splits, same inner CV, same model
families and grids, same 1000-resample bootstrap and paired tests, same
pilot-holdout exclusion, same decision rule including the Goal 2.9 requirement
that a credited increment beat a comparator that is itself above chance.

The design, the literature it rests on, and the predictions recorded before any
model was run are in `reports/goal2_10_eye_method_design.md`. The readiness
audit is `reports/eye_readiness_audit.md`.

## Goal 3

Status: **measurement complete**. Over the 26 decision rows,
**0 credit independent signal**; the confirmatory increment is +0.0016 under
Standard CV and -0.0031 under Group CV, both intervals containing zero, and 0 of
24 exploratory rows survive. See `reports/goal3_final_report.md`.

Three results from this stage bind future work.

- **The positive controls make this null readable.** The same EEGNet, the same
  mean-and-std pooling, the same 1820 subjects and folds reach **0.82 for age**
  and **0.77 for sex** while the disease label reaches 0.55, and trial-level
  target-versus-standard reaches 0.82 on held-out subjects. Subject-level
  aggregation is not the weak link, so this null is about the label and not
  about the pipeline. Any future deep stage in this project should carry
  controls of this kind; without them a null cannot be distinguished from a
  broken model.
- **Cross-fitted probability stacking removes the dilution artefact.** Goal 2.8
  recorded 78 significantly negative increments over demographics out of 216;
  Goal 3 records 0 negative and 0 positive out of 56, spanning -0.0078 to
  +0.0045. An uninformative component gets a near-zero weight instead of being
  paid for. Prefer this design over feature concatenation for every future
  increment test.
- **A deep score is seed-unstable at a scale that dwarfs these effects.**
  Between-seed AUROC standard deviation for `eeg_deep` averages 0.0249 under
  Group CV and reaches 0.0527, against increments of about 0.005. The paired
  bootstrap resamples subjects and is blind to it. A single-seed deep result on
  this cohort is not interpretable.

Opened by a conditional go.

```
CONDITIONAL_GO_FOR_GOAL3_EEG_REPRESENTATION_BENCHMARK
issued 2026-09-09
```

Goal 2.8 established that **hand-crafted** EEG features carry no increment over
age, sex and grade. It did not establish that the **representation** carries
none: the correctly recovered Oddball has never been given a deep model under a
protocol this project would accept. The old EEGNet / InceptionTime runs at
0.50-0.53 used the target-only v1 cache and a different split and stopping
protocol, so they are historical reference and not evidence about Goal 3.

The conditional go therefore opens EEG Oddball single-modality deep
representation work, and nothing else. fNIRS, Face, eye tracking, behaviour and
multimodal fusion keep the Goal 2.8 gate.

Goal 3 answers three questions and stops:

1. does EEG itself carry a reproducible label signal on unseen subjects;
2. does a deep spatio-temporal representation beat the Goal 2.8 hand-crafted
   representation on identical subjects and identical folds;
3. does EEG add anything over `age + sex + grade`.

Question 3 decides go/no-go. It is answered by cross-fitted probability
stacking, not by concatenating an embedding onto demographics, because this
project has measured that appending uninformative columns to demographics costs
0.008 to 0.055 AUROC on its own. The traditional feature block passes through
the same stacking, so `p_EEG` and `p_traditional` enter the comparison with
identical dimensionality.

The design and the predictions recorded before any model was trained are in
`reports/goal3_method_design.md`.

## Goal 3 Rules

- **Scope is EEG Oddball.** Rest and 1BACK are out of scope: the standard-only
  control already answers whether an effect is deviance processing or general
  EEG individual difference, and adding tasks multiplies the comparison count
  without answering a new question.
- **Preprocessing is Goal 2.8's, unchanged.** Single-trial epochs are re-derived
  from raw BDF with `configs/goal2_8/eeg.yaml` exactly as written: linked-mastoid
  reference, 0.1-40 Hz, 250 Hz, 150 uV peak-to-peak with Fp1/Fp2 excluded from
  the rejection decision, `min_trials` 20 standard and 5 target. Goal 2.8 kept
  only the condition averages, which is why the cache has to be rebuilt at all.
- **The measurement gate is numerical identity, not a qualitative check.**
  Averaging the new single-trial cache by condition must reproduce
  `artifacts/goal2_8/eeg/oddball_erp.npz` element-wise to floating-point
  tolerance, over exactly the same 1820 subjects. The P3b checks (Pz +6.43 uV,
  Cohen d 1.08, 88.7 percent of subjects positive, parietal maximum, Fz
  negative) are the second layer. A failure stops the goal; it does not get
  worked around.
- **Positive controls are mandatory and run before the label.** The same
  architecture, aggregation, splits and protocol must decode target vs standard
  at the trial level, and sex and age at the subject level. A null on the
  disease label may not be reported unless the positive controls pass. This is
  the deep-model form of the Goal 2.10 rule that a null on an unmeasurable
  quantity is evidence about the instrument, not about the construct.
- **Subject-level unit, subject-balanced learning.** Labels are subject-level.
  Every epoch of training draws a fixed quota of target trials and a fixed quota
  of standard trials from every subject, sampling with replacement where a
  subject has too few, so neither trial count nor the 22:109 condition ratio
  weights a subject. Inference averages over repeated fixed-size draws.
- **One primary comparison, declared in advance.** The condition-aware
  representation on the primary architecture, under both CV protocols,
  `p_Demo + p_EEG` against `p_Demo`. Everything else is secondary and may not be
  promoted to the headline after the fact.
- **Three seeds per configuration.** The paired bootstrap resamples subjects and
  is blind to the instability of the fit, which is larger for deep models than
  for the sklearn families. The primary score is the seed-averaged one and the
  spread is reported with it.
- **Shortcut probes are part of the result, not an appendix.** Report the
  acquisition-group decoding AUROC of the EEG embedding, and run the amplitude
  ablation (no per-subject normalisation, which is the primary setting and
  matches the traditional features, against per-subject robust z-scoring). A
  result that exists only unnormalised, only under Standard CV, is
  shortcut-sensitive and cannot support a go.
- **Cross-fitted scores must come from one generating process.** The three inner
  models of an outer fold produce the inner-OOF scores that train the meta model
  and, averaged, the outer-validation score. Training a separate full-outer-train
  model for the outer prediction would give the meta model train and test scores
  from different distributions.
- The fixed splits, the inner-CV-only selection of every hyperparameter,
  threshold and stopping point, and the exclusion of the baseline-exposed pilot
  holdout are unchanged from the standing protocol.

## Eye Rules

- Eye recordings are keyed on **`A_id`**, never `L_id` and never on subject
  name. `has_eye_direct` in the manifest counts 291 subjects because
  `chongqing_binary.audit._extract_l_ids` greps paths for `L\d+` and no eye path
  carries one. Joining on `A_id` finds 1187 subjects, 919 of them in the
  development split. Do not use `has_eye_direct` or `has_eye_name_mapped` to
  build an eye cohort. Name-based mapping is forbidden; it is what made
  `has_eye_name_mapped` unreliable.
- Three devices recorded the same three tasks on near-disjoint cohorts: Tobii
  Pro Nano at 60 Hz, 七鑫易维 at 120 Hz, 七鑫易维 F500 at 500 Hz. Only 2 subjects
  appear under more than one device, and each device owns a distinct set of
  `A_id` site prefixes. Device and acquisition site cannot be separated. Units
  are `device x task`; **raw features are never merged across devices**, exactly
  as for fNIRS Yiruid/Bikom.
- Sampling rate decides which features exist. Velocity-derived features
  (saccade peak velocity, pursuit velocity gain) are **forbidden on Tobii** at
  60 Hz and must never be pooled with the 120/500 Hz devices. Dwell, fixation
  counts and durations, AOI shares and pupil measures are permitted on all
  three. `EyeDeviceSpec.velocity_features_permitted` carries this.
- Task structure comes from `configs/goal2_10/eye_paradigm_spec.yaml` through
  `chongqing_binary.eye.spec`. Do not hardcode it. It was recovered from the
  stimulus media and the recorded timelines before any paradigm document
  existed; `附件/重医眼动范式及参数.docx` arrived 2026-09-09 and confirms it on
  every quantity it states. Every value still names its source, and the
  document is now the authority for the ones it covers.
- **The paradigm document contains a second table that is not this dataset.**
  It describes a gaze-contingent battery (800 ms held fixation gate, 8°
  targets in four directions, plus 记忆引导扫视 and 双步扫视) belonging to the
  集思鸣智 device, whose section heading follows it and whose data is not in
  `眼动/` at all. Our stimuli are fixed-length MP4s and cannot gate on gaze;
  no memory-guided or double-step stimulus exists anywhere in the projects.
  Read only section (1) 七鑫易维、Tobii设备. See `document_scope` in the spec
  and `reports/goal2_10_paradigm_document_review.md`.
- 七鑫易维 stimulus onsets are **not** in the per-subject export. Every
  `*_annotation.csv` is header-only. They come from the project `.asdata` file,
  `experimentPoMap[*].recordPoMap[*].mediaInRecordMap`.
- The 七鑫易维 sample clock drifts against the presentation clock: on F500 the
  samples span about 0.4 percent longer than the recorded `duration`, which is
  a 300-400 ms misalignment by the end of a 136 s block. Map every trace with
  `chongqing_binary.eye.qixin.aligned_time_ms` before any trial-locked use.
  Uncorrected, the pursuit gaze-target correlation reads 0.64-0.72 instead of
  0.95-0.96.
- Tobii `Recording timestamp` is in **microseconds** while `Recording duration`
  is in milliseconds. The reader converts and records the agreement.
- 自由观看 is a **single-stimulus** paradigm: one face on screen at a time. It
  therefore does not yield the competitive attentional-bias score that most of
  the free-viewing depression literature reports. The available contrast is
  between trials (sad vs happy vs neutral), not within a trial. Never describe
  the between-trial contrast as a competitive attentional bias.
- Free-viewing presentation order is fixed and identical for every subject, so
  trial index and valence are confounded by design. Report any trial-index
  effect alongside any valence effect.
- Each saccade block holds only **8 formal trials**. A direction-error rate on 8
  trials has a resolution of 0.125. Report its split-half reliability with it,
  and do not treat it as comparable to the 40-100 trial antisaccade batteries in
  the literature. Antisaccade error also falls steeply with age and plateaus
  around 14-15 years, inside this cohort's 9-20 range, so report
  `Spearman(feature, age)` and the residual univariate AUROC after regressing
  out age.
- Free-viewing regions come from YuNet's five landmarks on the 36 stimulus
  images, scaled by the inter-ocular distance, giving `eyes`, `mouth`,
  `face_other` and `off_face`. A gaze sample is assigned to exactly one region,
  first match wins, so the four shares sum to one. The regions depend only on
  the stimulus, never on a subject, so they cannot leak. YuNet detects all 36
  with a lowest score of 0.907; a Haar fallback here is an error, not a
  downgrade. The multipliers live in the specification under
  `tasks.free_viewing.aoi` and carry `source: analysis_choice`, so they are not
  mistaken for recovered paradigm fact.
- **Gaze must be drift-corrected before any region feature.** All three
  trackers report gaze below the true fixation point by a device-dependent
  amount: median vertical offset +0.035 of screen height at 120 Hz and +0.059
  on F500. The eye and mouth bands are each about 0.10 of screen height, so
  uncorrected the eye-minus-mouth contrast reads -0.122 and -0.117 on the two
  七鑫易维 devices while holding positive on Tobii. Since device is collinear
  with acquisition site, that difference would enter a model as a site
  shortcut. `chongqing_binary.eye.drift.estimate_drift` takes the median gaze
  over a recording's 1 s fixation crosses minus screen centre; after it, eyes
  minus mouth is +0.261 and +0.250 and the two devices agree to within 0.02 on
  every region share. Use the recording-level median, not the preceding cross,
  so trial-level variance stays in the signal. The estimated offset is an
  acquisition property and belongs to the **QC** feature set only.
- Duplicate takes are resolved deterministically, never averaged: complete
  timeline first, then most media segments, then longest recording, then latest.
  Every component comes from the recording, never from the label. The discarded
  paths are written to `artifacts/goal2_10/readiness/discarded_recordings.csv`.
- Recordings whose directory or filename carries no `A_id` are recorded and
  excluded, not recovered by name.
- Eye QC records acquisition integrity only: valid-sample fraction, tracking
  gaps, clock scale, calibration and validation accuracy, timeline conformance.
  Task performance belongs to the signal side, otherwise `signal_qc vs qc`
  tests nothing.
- Label-free validity must pass before any modelling: free-viewing dwell inside
  the stimulus face box far above its area share, eye-region dwell above
  mouth-region dwell, prosaccade gaze-target correlation positive and
  antisaccade negative, pursuit correlation high. A failure means the parse is
  wrong, which is the mistake Goal 2.7 made on EEG and fNIRS. The coarse
  face-box check passes even with a vertical offset, because the face box is
  symmetric about screen centre; only the eye-versus-mouth check catches it.

- One fixation detector for all three devices:
  `chongqing_binary.eye.events` applies I-DT to the drift-corrected gaze of
  every device. Each vendor ships its own classifier (Tobii I-VT per sample,
  七鑫易维 an I-DT event table); using both would make a feature of the same name
  mean two different things, and the vendor counts are kept only as a QC
  cross-check. Dispersion rather than velocity, because a velocity threshold
  behaves differently at 60 Hz and 500 Hz. The threshold is expressed as a
  **screen fraction**, but a degree value may now be asserted: the paradigm
  document's 6° and 12° saccade targets, against the decoded 0.1396 and 0.2823
  screen widths, fix the viewing distance at 1.3282 screen widths (both
  eccentricities agree to four significant figures, and only under a tangent
  mapping). The 0.025 threshold is 1.078° horizontally.
- **x is normalised by screen width and y by screen height, and nothing
  rescales them.** The same number is 1.078° horizontally and 0.607°
  vertically, and any `hypot` of the two axes adds different units. This
  affects `scanpath`, `bcea`, the 2-D pursuit `rmse` and `_catch_up`; it does
  not affect any AOI quantity, the drift correction, or the single-axis gains.
  It distorts a metric, it does not confound one — every recording used the
  same 1920x1080 stimulus — so it cannot have produced the Goal 2.10 null.
  Recorded as `known_defects/axis_anisotropy`; not yet fixed.
- Free-viewing features keep the absolute per-valence measures beside the
  contrasts, and every feature carries its own odd-even split-half estimate in
  `*_split_half_reliability.csv`.
- **The free-viewing valence contrasts are not measurable in this paradigm.**
  Measured on 249-322 subjects per device: **0 of 46** contrast features reach
  Spearman-Brown 0.5 on all three devices, the best reaches 0.326, and 33 have
  a negative median. **53 of 75** absolute features clear 0.5 on all three.
  The cause is arithmetic, not acquisition: a valence contrast is a difference
  of two means each estimated from 12 trials. This replicates, in this dataset,
  the difference-score reliability collapse the attentional-bias literature
  reports. Consequences that must be honoured:
  - the absolute and contrast blocks enter the matrix as **separate declared
    feature sets**, because mixing 46 noise columns into 75 informative ones
    would depress the free-viewing result for a reason unrelated to signal;
    this project has already measured that dilution effect;
  - a null increment on the contrast block says nothing about attentional bias
    as a construct, only that this paradigm cannot measure it at 12 trials per
    valence. Do not report such a null as evidence against the construct.
  - `results/goal2_10/free_viewing_reliability_summary.csv` carries the
    per-feature numbers.
- Pupil is a change from the tail of the fixation cross that precedes each
  trial, never an absolute diameter.
- The feature layer consumes
  `artifacts/goal2_10/readiness/recordings.csv` rather than repeating
  discovery, so both stages see the same take of every recording. Run the
  readiness audit first.
- Recordings resolving less than half their samples are excluded and the count
  is recorded per unit, never absorbed silently.

## Goal 2.10 Entry Points

- Readiness audit: `python scripts/audit_eye_readiness.py --n-workers 48`
- Eye features: `python scripts/extract_eye_goal2_10_features.py --n-jobs 32`

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
