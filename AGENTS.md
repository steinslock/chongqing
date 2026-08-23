# Chongqing Binary Diagnosis Agents

Last updated: 2026-08-23

## Project Root

Use this directory as the project root:

`/data4/qiangminc/code/chongqing`

The historical `/home/qiangminc/codes/data4_qiangminc/...` path resolves to the
same storage, but new documentation and manifests use the canonical `/data4`
path.

## Current Stage

Goal 2.7 is complete and formalized. It repaired the lightweight multimodal
evaluation protocol, made Standard fixed CV and Group-aware fixed CV co-primary,
added demographics/group decomposition and paired independent-increment tests,
and tightened Face, EEG-event, fNIRS-timing, and threshold handling.

Current modality decisions:

- EEG: `BLOCKED_BY_INVALID_TASK_SEMANTICS + NO_CLEAR_SIGNAL`.
- fNIRS: `BLOCKED_BY_INVALID_TASK_SEMANTICS + NO_CLEAR_SIGNAL`.
- Face: `SHORTCUT_DOMINATED`.
- No modality reached `INDEPENDENT_SIGNAL_SUPPORTED`.

The next authorized planning stage is Goal 2.8, a remediation and decision gate.
Do not start Goal 3, Goal 4, Goal 5, deep training, or multimodal fusion merely
because Goal 2.7 is complete.

## Goal 2.8 Gate

Before stronger modality-specific models, Goal 2.8 should:

- recover and document EEG Oddball and 1BACK event semantics;
- confirm fNIRS task timing and Yiruid signal semantics;
- add group-balanced or residualized demographic/shortcut controls;
- decide whether a stricter Face shortcut-controlled replication is warranted;
- issue an explicit go/no-go decision for Goal 3, Goal 4, or Goal 5.

## Read-Only Inputs

Treat these as read-only:

- Raw dataset: `/data4/qiangminc/datasets_qiangmin/chongqing`
- Existing report bundle: `/data4/qiangminc/code/chongqing/inputs/derived_reports/chongqing_binary_diagnosis_report`

All generated features, caches, predictions, metrics, models, logs, and reports
must remain under the project root, primarily in `artifacts/`, `results/`,
`reports/`, and `checkpoints/`.

## Split and Evaluation Rules

- Use only subjects with `split_group == cv` for development and reporting.
- Standard CV inherits `artifacts/splits/subject_splits_v1.csv` and `cv_fold`.
- Group CV inherits `artifacts/splits/subject_splits_group_robustness_v1.csv`
  and `robustness_fold`.
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
separately.

## Task-Semantics Rules

- EEG Oddball code-22 cache is `oddball_target_only_proxy`; do not claim formal
  target/non-target ERP until semantics and raw reconstruction are confirmed.
- EEG 1BACK condition differences are blocked until codes 18/19 are confirmed.
- fNIRS task-response features require marker-confirmed or protocol-confirmed
  timing; the 20/60/20 fallback is forbidden for formal claims.
- Bikom files are read in full; do not reintroduce a fixed 2000-row cap.
- Yiruid raw/log-intensity and OD-like features must not be called HbO/HbR.

## Face Rules

- Frozen visual embeddings may use GPU; classical classifiers and bootstrap are
  CPU workflows.
- Visual embeddings alone enter PCA. Demographics, QC, and metadata bypass PCA
  and are concatenated afterward.
- Failed detections must not become center-crop face samples.
- Strict background uses only detected-face frames with the face region masked
  or blurred.
- Face audio is excluded.
- Contact sheets are local sensitive audit material and must not be pushed to Git.

## Goal 2.7 Entry Points

- Event audit: `python scripts/audit_goal2_7_events.py`
- EEG features: `python scripts/extract_eeg_goal2_7_features.py`
- fNIRS features: `python scripts/extract_fnirs_goal2_7_features.py`
- Face features: `python scripts/extract_face_goal2_7_features.py`
- Full model matrix: `python scripts/run_goal2_7.py --skip-supplemental`
- Restartable bootstrap/paired outputs: `python scripts/run_goal2_7.py --supplemental-only`
- Reports: `python scripts/summarize_goal2_7.py`
- Release archives/manifest: `python scripts/build_goal2_7_release_manifest.py`
- Unit tests: `python -m unittest discover -s tests`

Use the `avmoe` environment and set `PYTHONPATH=src` for project entry points.

## GitHub Release Policy

Track source, configs, tests, reports, manifests, compact features, metrics, and
deterministic compressed OOF archives. Keep the following local:

- uncompressed Goal 2.7 OOF CSVs larger than GitHub's per-file limit;
- Face embedding CSVs and `.part.csv` checkpoints;
- Face contact sheets and other identifiable source-video frames.

`artifacts/goal2_7/release_manifest.json` records sizes, SHA-256 hashes, and the
release disposition for Goal 2.7 files.
