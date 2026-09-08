# Experiment Protocol

## Current Stage

Goal 2.9 is the current model matrix. Goal 2.8's measurement is complete and its
results are recorded in `reports/goal2_8_final_report.md`; Goal 2.7's modality
conclusions are superseded, see `reports/goal2_7_superseded_notice.md`.

Goal 2.9 keeps this protocol unchanged and adds one feature layer: the
trial-level behavioural logs. Its measurement is complete and recorded in
`reports/goal2_9_final_report.md`: 0 of 168 increments over demographics are
credited. It is not Goal 3, Goal 4, Goal 5 or fusion, and it does not lift their
gate. No go/no-go decision has been issued. Do not start Goal 3, Goal 4, Goal 5,
or multimodal fusion until one is.

An increment is only credited over demographics. Wins against background or QC
are shortcut controls and are reported separately.

## Subject-Level Unit

The unit of analysis is the subject, keyed by `L_id`. Windows, epochs, trials,
time slices, frames, clips, videos, and derived representations inherit the
subject split and may not be randomized independently.

## Co-Primary Outer CV

Protocol A, Standard fixed CV:

- split file: `artifacts/splits/subject_splits_v1.csv`
- development rows: `split_group == cv`
- outer fold: `cv_fold`

Protocol B, Group-aware fixed CV:

- split file: `artifacts/splits/subject_splits_group_robustness_v1.csv`
- development rows: `split_group == cv`
- outer fold: `robustness_fold`

Both protocols use the same predefined feature sets and model families. Results
from one protocol must not choose models or settings for the other. The split
files are fixed and must not be regenerated.

## Inner CV and Preprocessing

Each outer training fold uses three-fold subject-level inner CV. Hyperparameters,
visual PCA dimensions, thresholds, imputation, scaling, categorical encoding,
variance filtering, and any feature selection are fit on outer-train only.

The outer validation labels are unavailable to model and threshold selection.
Every eligible `L_id` receives exactly one OOF prediction per
protocol/cohort/modality/device/task/feature-set/model/seed combination.

## Pilot Holdout Policy

The locked test set is a baseline-exposed pilot holdout. It is excluded from
feature extraction decisions, model development, threshold selection, early
stopping, checkpoint selection, result ranking, and reporting.

## Labels and Leakage

Use `primary_label_nonhealthy` only as the supervised outcome. Diagnosis fields,
clinical scales, self-harm/suicide variables, manual review, labels, and clinical
proxy totals are forbidden predictors.

Main demographics is age + sex + grade. Report these separately from objective
signal. `grade_group`, group proxy, and device are sensitivity/shortcut features,
not part of the minimal demographics baseline.

## Paradigm Conformance

The dataset attachments define how each experiment was actually run, and code
must follow them.

- Event codes, block counts, trial counts, SOA, durations, marker semantics and
  segment boundaries are read from `configs/goal2_8/paradigm_spec.yaml` through
  `chongqing_binary.paradigm.spec`. Feature code must not hardcode them.
- Every specification value carries a `source:` field naming its attachment.
- `scripts/check_paradigm_conformance.py` checks the specification against
  sampled raw files and writes `artifacts/goal2_8/paradigm_conformance.csv`.
- A file whose contents contradict its task label is reported as
  `file_task_mismatch` and excluded, not coerced.
- Where attachments and recorded data disagree, record both, prefer the recorded
  data, and state the disagreement in the report.

## EEG Event Validity

- Rest is event-free and may use whole-recording/window-generic features.
- Oddball code `11` is the frequent 500 Hz standard with no response; code `22`
  is the rare 1000 Hz deviant target requiring a keypress, at 25:5 per block
  across 5 blocks with 1.0 s SOA. Target/standard ERP and the target-minus-
  standard difference wave are the primary Oddball features.
- 1BACK code `19` is the block-initial stimulus and is excluded from condition
  contrasts; code `18` is every later stimulus, at 2.0 s SOA over 2 blocks.
- 1BACK codes `66`/`77` encode response correct/incorrect but lag by one trial.
  Code `88` is unresolved and unusable.
- 1BACK block 2 is systematically truncated. Record it; never impute it.
- EEG 1BACK match/non-match is not recoverable from the archived data and must
  not be fabricated.

## fNIRS Timing and Device Validity

- Yiruid and Bikom remain device-specific.
- Rest is whole-recording for both devices.
- Block timing is confirmed for Yiruid Rest/VFT/1BACK/Oddball/Doors and Bikom
  Rest/1BACK/Oddball/Doors. Task-response features are permitted there.
- Bikom marks keep their labels: `ST`/`ED` bound the recording, `A0`/`A1` open
  and close block 1, `B0`/`B1` block 2.
- Bikom VFT has no markers; its timing is protocol-derived, carries
  `timing_confidence: low`, and may only support sensitivity analyses.
- The Bikom `Stim Time[s]` header line is a device template identical across all
  five tasks and must be ignored.
- Yiruid HbO/HbR derived by the modified Beer-Lambert law from the recorded
  690/830 nm wavelengths and optode geometry may be named as haemoglobin. Raw
  and log-intensity summaries must still be named as intensity.
- Bikom files are read in full; a fixed 2000-row cap is forbidden.

## Behavioural Log Validity

The paradigms wrote a trial-level log next to every fNIRS task that takes a
keypress. Structure, column names, condition coding and defects come from the
`behaviour:` section of each task in `configs/goal2_8/paradigm_spec.yaml`.

- Usable units are Yiruid 1BACK, Oddball and Doors, and Bikom 1BACK and Doors,
  plus one combined cohort per device.
- Bikom Oddball is excluded: that build never collected the keypress, in the
  vendor's own reference run as well as in 610 of 640 recorded subjects.
- 1BACK match/non-match is derived from the stimulus sequence, not read from the
  logged condition column, and the agreement between the two is recorded per
  subject. Block-initial trials are excluded; lag-1 measures never cross a block
  boundary.
- Doors feedback code `1` is loss and `2` is win on both devices, from the
  stimulus images. Feedback is predetermined and independent of the door chosen.
- Yiruid Doors is sensitivity-only: its 1 s response window closes 0.5 s after
  the doors appear, so only 38 percent of choices are recorded and RT is censored
  at 1 s. Bikom Doors is the primary device for reward behaviour.
- The 50 Bikom 1BACK subjects on the arrow-key build have no match trials at all
  and are excluded rather than coerced.
- The behaviour QC table carries log integrity only. Task performance stays on
  the signal side so the `signal_qc vs qc` comparison remains a real control.

## Face Protocol

- `面部2-任务` is segmented with `附件/网页数据.xlsx` before feature extraction.
  Uniform sampling across the whole session is forbidden.
- Movie order is fixed positive, neutral, negative, with stimulus durations
  93.16 s, 86.64 s and 125.00 s.
- Segment boundaries whose duration disagrees with the stimulus duration are
  flagged `segment_timing_mismatch` and excluded.
- The primary Face contrast is the within-subject valence contrast.
- Use the YuNet detector; a Haar fallback is a recorded QC failure.
- Use uniformly sampled frames within each segment and at least 4 valid detected
  face frames for strict face embeddings.
- Failed detections are excluded from strict face and strict background inputs.
- Strict background masks or blurs the detected face box.
- The frozen visual encoder does not use audio.
- Only visual embedding columns enter train-fold PCA; demographics, QC, metadata,
  and categorical one-hot features bypass PCA.
- Detector, checkpoint, threshold, detection rate, blocked count, and fallback
  usage must be recorded.

## Required Feature Comparisons

Behaviour uses the same required list as EEG and fNIRS, per device/task unit and
per combined cohort.

EEG and fNIRS include:

- signal vs demographics;
- signal+demographics vs demographics;
- signal+QC vs QC;
- signal+QC+demographics vs QC+demographics;
- signal+QC+demographics vs demographics;
- signal+demographics vs signal;
- signal+QC+demographics vs signal+QC.

Goal 2.8 adds condition-contrast comparisons: EEG Oddball target-minus-standard,
fNIRS per-block haemoglobin change, fNIRS 1BACK match-minus-non-match, fNIRS
Doors win-minus-loss, and Face negative-minus-positive.

Face additionally includes strict face vs background, full frame, metadata, and
QC, plus face+demographics vs background+demographics.

Each paired comparison uses identical subjects, outer folds, model family, seed,
and CV protocol, with at least 1000 paired subject bootstrap resamples for AUROC
and AUPRC differences.

## Metrics and Thresholds

Primary metrics are AUROC and AUPRC. Secondary metrics are balanced accuracy,
macro F1, sensitivity, specificity, accuracy, Brier score, ECE, and positive
prediction rate.

Report pooled OOF, per-fold, fold mean/std, and 95% subject bootstrap CI. For
threshold-dependent pooled metrics, apply each subject's fold-specific threshold
selected from that outer fold's inner OOF predictions. Keep fixed threshold 0.5
as a separate result.

## Interpretation Rules

`INDEPENDENT_SIGNAL_SUPPORTED` requires a positive paired independent increment
whose AUROC CI excludes zero, at least 4/5 positive folds, positive Group CV
increment, and no dominant shortcut explanation.

It further requires the comparator to be **above chance** in that cohort and
protocol. An increment over a demographics baseline sitting at or below 0.5
AUROC is a statement about the comparator, not about the signal. Record
`comparator_auroc` and `comparator_above_chance` alongside every required
increment.

The paired bootstrap resamples subjects, not folds, so it captures subject
sampling noise and is blind to the instability of the fit itself. In a small
cohort that instability can push a weak baseline below chance and manufacture a
difference the interval then certifies. Any credited increment from a cohort
under about 500 subjects must therefore be verified by **label permutation** on
that cohort before it is reported: shuffle the outcome, refit, and measure how
often the observed gap appears under the null. Goal 2.9 found eight such rows in
a 342-subject cohort; permutation reproduced their gap 12 to 18 percent of the
time and all eight were withdrawn. See `scripts/verify_goal2_9_positive.py`.

`SUPERSEDED` marks a conclusion whose premises were later shown to be wrong. A
superseded conclusion is not evidence and must not be cited as a constraint on
new work.

Background/group/device performance near the modality signal supports
`SHORTCUT_DOMINATED` or a shortcut warning.

A **negative** increment means the modality features are uninformative, not that
they are harmful. The pipeline is impute, scale, fit, with the whole feature
block; inner CV selects hyperparameters, never which features to use, so a model
handed a block of uninformative columns cannot choose to ignore them and pays
for them. Bolting columns of pure random noise onto demographics on the full
development cohort costs 0.008 to 0.055 AUROC depending on how many and which
model, which brackets the observed drops. Report negative increments as absence
of signal, never as damage.

Demographics figures in the result tables are measured inside each modality
cohort, which is what the comparison requires but is not a reference value.
`scripts/verify_demographics_baseline.py` measures the reference on the full
development cohort and writes `results/demographics_reference/`. Quote a
cohort-internal demographics number only alongside the cohort it came from.

Goal 2.7 decisions, all now `SUPERSEDED`:

- EEG: `BLOCKED_BY_INVALID_TASK_SEMANTICS + NO_CLEAR_SIGNAL`.
- fNIRS: `BLOCKED_BY_INVALID_TASK_SEMANTICS + NO_CLEAR_SIGNAL`.
- Face: `SHORTCUT_DOMINATED`.

The Goal 2.7 site/acquisition-group shortcut finding is not superseded and
stands.

## Reproducibility and Release

Run in the single `chongqing_v1` environment with `PYTHONPATH=src`, via
`source activate.local.sh`. The full model matrix can be followed by restartable
supplemental statistics from saved OOF predictions.

Hash-based constraints are abolished; see `AGENTS.md`. Do not gate changes on
checksums, do not emit hashes in reports, and do not add checksum code.

Large Face embeddings, intermediate checkpoints, very large uncompressed OOF
files, and identifiable Face contact sheets remain local and are excluded from
Git.
