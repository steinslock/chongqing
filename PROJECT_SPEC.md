# Chongqing Health/Non-Health Binary Diagnosis Project Spec

## Purpose

Build a reproducible subject-level framework for health/non-health binary
diagnosis using the Chongqing multimodal dataset. Goal 2.7 is the current
formalized evidence baseline: it evaluates EEG, fNIRS, and Face with repaired
protocols and asks whether each modality adds predictive information beyond
demographics, QC, acquisition group, device, metadata, or background shortcuts.

Goal 2.5 established data and protocol readiness, and Goal 2.6 established the
initial lightweight baselines. Goal 2.7 supersedes them as the current formal
evidence baseline while preserving their reports as historical records.

Goal 2.7 is complete. Its decision is a hold before deep models: no modality met
the independent-signal criterion, EEG/fNIRS formal task interpretations remain
blocked by semantics, and Face remains shortcut-dominated.

## Data Sources

Read-only raw dataset:

`/data4/qiangminc/datasets_qiangmin/chongqing`

Read-only existing report bundle:

`/data4/qiangminc/code/chongqing/inputs/derived_reports/chongqing_binary_diagnosis_report`

Canonical subject manifest:

`inputs/derived_reports/chongqing_binary_diagnosis_report/data/subject_manifest.csv`

Fixed Standard split:

`artifacts/splits/subject_splits_v1.csv`

Fixed Group-aware split:

`artifacts/splits/subject_splits_group_robustness_v1.csv`

The locked test portion was exposed during the baseline stage and is the
**baseline-exposed pilot holdout**. It is unavailable for feature, model,
threshold, or reporting decisions.

## Task Definition

Primary task: health vs non-health/high-risk/disease binary classification at
subject level.

Primary label: `primary_label_nonhealthy`.

- `0`: healthy
- `1`: non-healthy/high-risk/disease
- empty: excluded from supervised evaluation

Sensitivity labels, when used, must be reported separately and must not drive
model selection.

## Goal 2.7 Scope

Goal 2.7 formalizes:

- Standard fixed five-fold CV and Group-aware fixed five-fold CV as co-primary;
- three-fold subject-level inner CV for all model/PCA/threshold decisions;
- Logistic Regression, Random Forest, and HistGradientBoosting only;
- pooled OOF, per-fold metrics, 1000-resample subject bootstrap CIs, and
  1000-resample paired subject bootstrap comparisons;
- main demographics age + sex + grade, with grade_group/group/device separated;
- strict Face crop/background controls with visual-only PCA;
- event/timing audits that block unsupported EEG and fNIRS task claims;
- Core3 same-subject comparison named
  `core3_rest_yiruidvft_selfintro_intersection`.

It explicitly excludes pilot-holdout evaluation, neural-network training,
multimodal fusion, visual encoder fine-tuning, and post-result model expansion.

## Engineering Structure

| Directory | Purpose |
|---|---|
| `configs/goal2_7/` | Frozen Goal 2.7 protocol and model grids |
| `src/chongqing_binary/goal2_7/` | Reusable feature, runner, statistics, and report code |
| `scripts/*goal2_7*.py` | Audits, extraction, experiment, report, and release entry points |
| `tests/test_goal2_7_protocol.py` | Goal 2.7 protocol and output tests |
| `artifacts/goal2_7/` | Feature/QC tables, event inventories, manifests, and local caches |
| `results/goal2_7/` | OOF predictions, metrics, CIs, paired tests, and diagnostics |
| `reports/goal2_7_*.md` | Audit, modality, protocol, Core3, and final reports |
| `PROGRESS.md` | Chronological project status and verified commands |

## Evidence and Decision

- EEG: `BLOCKED_BY_INVALID_TASK_SEMANTICS + NO_CLEAR_SIGNAL`.
- fNIRS: `BLOCKED_BY_INVALID_TASK_SEMANTICS + NO_CLEAR_SIGNAL`.
- Face: `SHORTCUT_DOMINATED`.
- No native required independent-increment comparison had an AUROC 95% CI
  entirely above zero.
- Positive required rows were limited to Core3 Face sensitivity analyses and did
  not establish a robust native-cohort conclusion.

The authoritative narrative is `reports/goal2_7_final_report.md`; authoritative
machine-readable summaries are under `results/goal2_7/`.

## Output and Publication Policy

Raw data and the existing input report bundle must never be modified.
`artifacts/splits/subject_splits_v1.csv` must not be overwritten.

GitHub contains source, configs, tests, reports, manifests, compact features,
metrics, and compressed OOF archives. It does not contain large Face embedding
dumps, intermediate `.part.csv` files, uncompressed >100 MB OOF files, or Face
contact sheets. The release manifest records local and published artifacts with
SHA-256 hashes.

## Roadmap

- Goal 2.8: event-semantics and shortcut-remediation decision gate.
- Goal 3: EEG deep/single-modality experiments only after an explicit Goal 2.8 go.
- Goal 4: fNIRS deep/single-modality experiments only after timing and signal
  semantics are confirmed.
- Goal 5: Face deep/single-modality experiments only after stricter shortcut
  controls justify continuation.
- Goal 6: fair same-cohort comparison after eligible single-modality protocols.
- Goal 7: multimodal fusion only after independent single-modality evidence.
