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

## Engineering Structure

| Directory | Purpose |
|---|---|
| `configs/goal2_8/` | Goal 2.8 protocol, model grids, and the paradigm specification |
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
- Goal 3: EEG deep/single-modality experiments only after an explicit Goal 2.8 go.
- Goal 4: fNIRS deep/single-modality experiments only after a Goal 2.8 go.
- Goal 5: Face deep/single-modality experiments only after a Goal 2.8 go.
- Goal 6: fair same-cohort comparison after eligible single-modality protocols.
- Goal 7: multimodal fusion only after independent single-modality evidence.
