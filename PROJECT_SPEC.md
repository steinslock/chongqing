# Chongqing Health/Non-Health Binary Diagnosis Project Spec

## Purpose

Build a reproducible subject-level framework for health/non-health binary
diagnosis using the Chongqing multimodal dataset.

Goal 2.5 established data and protocol readiness, Goal 2.6 established the
initial lightweight baselines, and Goal 2.7 established the evaluation protocol
that is still in force: co-primary Standard and Group-aware fixed CV, inner-CV
model and threshold selection, paired subject bootstrap increments, and an
explicit battery of demographic, acquisition-group, device, QC, metadata and
background shortcut controls.

Goal 2.8 keeps that protocol unchanged and replaces the feature layer, because
the Goal 2.7 feature layer did not reflect how the experiments were actually
run.

## Data Sources

Read-only raw dataset:

`/data/home/cqm/Project/Dataset/Chongqing`

Read-only existing report bundle:

`/data/home/cqm/Project/Code/chongqing/inputs/derived_reports/chongqing_binary_diagnosis_report`

Canonical subject manifest:

`inputs/derived_reports/chongqing_binary_diagnosis_report/data/subject_manifest.csv`

Fixed Standard split:

`artifacts/splits/subject_splits_v1.csv`

Fixed Group-aware split:

`artifacts/splits/subject_splits_group_robustness_v1.csv`

The locked test portion was exposed during the baseline stage and is the
**baseline-exposed pilot holdout**. It is unavailable for feature, model,
threshold, or reporting decisions. The split files must not be regenerated.

The dataset attachments under `Dataset/Chongqing/附件` and
`Dataset/Chongqing/面部/面部任务.zip` are the authority on experiment design:
paradigm scripts, condition tables, the protocol PDF, optode geometry and
cortical projections, the web presentation log, and the face stimulus set.

## Task Definition

Primary task: health vs non-health/high-risk/disease binary classification at
subject level.

Primary label: `primary_label_nonhealthy`.

- `0`: healthy
- `1`: non-healthy/high-risk/disease
- empty: excluded from supervised evaluation

Sensitivity labels, when used, must be reported separately and must not drive
model selection.

## Goal 2.8 Scope

Goal 2.8 is event-semantics recovery and feature re-derivation. It includes:

- a single attachment-sourced paradigm specification plus a conformance checker,
  which all feature code must read from instead of hardcoding task structure;
- EEG re-epoched from raw BDF with both Oddball conditions, giving target,
  standard and target-minus-standard ERP features, starting with Oddball and
  extending to 1BACK and Rest after it verifies;
- fNIRS read in full including optode geometry and wavelengths, converted to
  HbO/HbR by the modified Beer-Lambert law, segmented by confirmed block timing
  across all five tasks and both devices, with behavioural logs supplying
  condition contrasts;
- Face task video segmented into its positive/neutral/negative movie phases,
  with the within-subject valence contrast as the primary feature;
- a rerun of the model matrix under the unchanged protocol and controls;
- an explicit go/no-go decision for Goal 3, Goal 4 and Goal 5.

It excludes pilot-holdout evaluation, neural-network training, multimodal
fusion, visual encoder fine-tuning, and post-result model expansion.

## Goal 2.9 Scope

Goal 2.9 is the behavioural feature layer. Every fNIRS task that takes a keypress
wrote a trial-level log next to the recording, and no earlier goal used any of
it. Goal 2.9 reads those logs and derives subject-level measures of working
memory, attention, impulse control and reward reactivity:

- accuracy, hit and false-alarm rates, d-prime and criterion;
- reaction-time central tendency, dispersion, skew and drift across blocks;
- post-error slowing and the match-minus-non-match contrast in 1BACK;
- vigilance decrement across the ten Oddball blocks;
- win-stay, lose-shift, switch rate and post-feedback slowing in Doors, the one
  reward paradigm in the battery.

It keeps the protocol, the splits, the controls and the decision rule unchanged,
and adds a paradigm-conformance layer for the logs in the same specification the
neural features already read. It excludes pilot-holdout evaluation, deep
training, multimodal fusion, and any change to the Goal 2.8 gate.

## Goal 3 Scope

Goal 3 is the EEG Oddball deep representation benchmark, and the first stage in
this project to train a neural network. It changes no measurement: the single
trials are re-derived from raw BDF under the Goal 2.8 preprocessing unchanged,
and the gate for using them is numerical identity with the Goal 2.8 evoked
arrays rather than a qualitative check.

It answers three questions and stops. Does EEG carry a reproducible label signal
on unseen subjects; does a deep spatio-temporal representation beat the Goal 2.8
hand-crafted one on identical subjects and folds; and does EEG add anything over
age, sex and grade. The third decides go/no-go and is answered by cross-fitted
probability stacking rather than feature concatenation, because appending
uninformative columns to demographics has a measured cost in this project.

It excludes Rest and 1BACK, every other modality, multimodal fusion, and
pilot-holdout evaluation. Its measurement is complete and recorded in
`reports/goal3_final_report.md`.

## Engineering Structure

| Directory | Purpose |
|---|---|
| `configs/goal2_8/` | Goal 2.8 protocol, model grids, and the paradigm specification |
| `configs/goal3/` | Goal 3 protocol, deep training settings and the declared model family |
| `src/chongqing_binary/goal3/` | Trial cache, encoders, training, nested splits, stacking, controls, report |
| `scripts/*goal3*.py` | Trial build, gate, tabular cross-fit, matrix, controls, summary, permutation |
| `tests/test_goal3_protocol.py` | Split, sampler, model, stacking, FDR and device-failure tests |
| `artifacts/goal3/` | Single-trial cache, cross-fitted comparator scores, gate verification |
| `results/goal3/` | OOF predictions, metrics, CIs, paired tests, controls, decision |
| `reports/goal3_*.md` | Method design and pre-registration, results, final report |
| `configs/goal2_9/` | Goal 2.9 protocol and model grids |
| `src/chongqing_binary/goal2_9/` | Behavioural log readers, features, runner, and report code |
| `scripts/*goal2_9*.py` | Behavioural extraction, experiment, and report entry points |
| `tests/test_goal2_9_behaviour.py` | Behavioural log, feature, and matrix-config tests |
| `artifacts/goal2_9/` | Behavioural feature and QC tables |
| `results/goal2_9/` | OOF predictions, metrics, CIs, paired tests, and decisions |
| `reports/goal2_9_*.md` | Behavioural results reports |
| `src/chongqing_binary/paradigm/` | Paradigm specification loader and conformance checking |
| `src/chongqing_binary/goal2_8/` | Goal 2.8 feature, runner, and report code |
| `scripts/*goal2_8*.py` | Audits, extraction, experiment, and report entry points |
| `tests/test_paradigm_spec.py` | Specification coverage and raw-data conformance tests |
| `artifacts/goal2_8/` | Feature/QC tables, epochs, conformance tables, and local caches |
| `results/goal2_8/` | OOF predictions, metrics, CIs, paired tests, and diagnostics |
| `reports/goal2_8_*.md` | Audit, modality, and final reports |
| `configs/goal2_7/`, `src/chongqing_binary/goal2_7/`, `results/goal2_7/` | Goal 2.7, retained and reproducible; conclusions superseded |
| `configs/goal2_6/`, `results/goal2_6/`, `reports/goal2_6_*.md` | Goal 2.6 historical record; its code was deleted on 2026-09-07 |
| `reports/archive/` | Superseded design documents |
| `PROGRESS.md` | Chronological project status and verified commands |

## Evidence and Decision

The Goal 2.7 modality conclusions are **superseded**. They were:

- EEG: `BLOCKED_BY_INVALID_TASK_SEMANTICS + NO_CLEAR_SIGNAL`
- fNIRS: `BLOCKED_BY_INVALID_TASK_SEMANTICS + NO_CLEAR_SIGNAL`
- Face: `SHORTCUT_DOMINATED`

Each rested on a premise contradicted by the raw data: the Oddball standard
condition exists in the raw event files, the 1BACK codes are positional rather
than conditional, the Yiruid wavelengths and optode geometry are recorded in
every `.nirs` file, fNIRS block timing is confirmed for every task, and the Face
task video is a multi-phase session that was never segmented. Details and root
causes are in `reports/goal2_7_superseded_notice.md`.

What still stands from Goal 2.7:

- the evaluation protocol and its shortcut control battery;
- the finding that acquisition site and demographics are strong predictors,
  with the `A_id`-prefix group proxy alone reaching about 0.68 AUROC, and that
  Group-aware CV deflates group-proxy-heavy rows.

Goal 2.8 recomputed the modality results from paradigm-conformant features. Its
measurement is complete and recorded in `reports/goal2_8_final_report.md`: over
216 required increments over demographics, zero were significantly positive and
78 were significantly negative under both CV protocols. Face shows 14 significant
wins against background, which are shortcut controls, not increments over
demographics. No go/no-go decision has been issued.

Goal 2.9 added the behavioural feature layer under the same protocol. Its
measurement is complete and recorded in `reports/goal2_9_final_report.md`: over
168 increments over demographics, 8 intervals excluded zero on the positive side
and none is credited, because every one beat a demographics baseline that was
itself below chance in a 342-subject cohort whose age range had been compressed
by task intersection. 25 were significantly negative. The behavioural measures
are demonstrably valid — post-error slowing replicates at 76.5 percent in two
disjoint device cohorts, 1BACK d-prime is 2.6 to 2.9 and Oddball d-prime 4.5 —
and they carry univariate label information up to AUROC 0.57, but they add
nothing over age, sex and grade.

The decision rule gained one clause as a result: a credited increment must beat
a comparator that is itself above chance.

## Output and Publication Policy

Raw data and the existing input report bundle must never be modified. The split
files must not be overwritten.

Hash-based constraints are abolished; see `AGENTS.md`. Provenance is carried by
Git history and `PROGRESS.md`.

GitHub contains source, configs, tests, reports, compact features, metrics, and
compressed OOF archives. It does not contain large Face embedding dumps,
intermediate `.part.csv` files, very large uncompressed OOF files, or Face
contact sheets.

## Roadmap

- Goal 2.8: event-semantics recovery and feature re-derivation. Measurement
  complete and recorded; the go/no-go decision is still open.
- Goal 2.9: behavioural feature layer from the paradigm trial logs, under the
  unchanged protocol. Measurement complete and recorded; 0 of 168 increments
  over demographics credited. It does not lift the Goal 2.8 gate.
- Goal 3: EEG Oddball deep representation benchmark, opened 2026-09-09 under
  `CONDITIONAL_GO_FOR_GOAL3_EEG_REPRESENTATION_BENCHMARK` on the grounds that
  Goal 2.8 measured hand-crafted features rather than representations.
  Measurement complete: **0 of 26 decision rows credit independent signal**,
  with positive controls on the same pipeline reaching 0.82 for age and 0.77 for
  sex. It does not lift the gate on Goal 4, Goal 5 or fusion.
- Goal 4: fNIRS deep/single-modality experiments only after a Goal 2.8 go.
- Goal 5: Face deep/single-modality experiments only after a Goal 2.8 go.
- Goal 6: fair same-cohort comparison after eligible single-modality protocols.
- Goal 7: multimodal fusion only after independent single-modality evidence.
