# Progress Log

## 2026-07-07 - Goal0 Project Initialization

Status: complete.

Completed:

- Read `inputs/derived_reports/chongqing_binary_diagnosis_report/DATASET_DESCRIPTION.md`.
- Selected `/data/home/cqm/Project/Code/chongqing` as the project root.
- Confirmed existing inputs:
  - Raw dataset at `/data/home/cqm/Project/Dataset/Chongqing`.
  - Existing derived report bundle at `inputs/derived_reports/chongqing_binary_diagnosis_report/`.
  - Prior EEG v1 baseline under `experiments/v1/`.
- Created root project documentation:
  - `AGENTS.md`
  - `PROJECT_SPEC.md`
  - `EXPERIMENT_PROTOCOL.md`
  - `PROGRESS.md`
- Created required root directories:
  - `configs/`
  - `src/`
  - `scripts/`
  - `tests/`
  - `artifacts/`
  - `results/`
  - `reports/`
  - `checkpoints/`
- Created configuration files:
  - `configs/default.yaml`
  - `configs/smoke.yaml`
  - `configs/leakage_forbidden_fields.yaml`
- Marked read-only inputs in config and docs:
  - Raw dataset: `/data/home/cqm/Project/Dataset/Chongqing`
  - Existing report bundle: `/data/home/cqm/Project/Code/chongqing/inputs/derived_reports/chongqing_binary_diagnosis_report`
- Created unified framework interfaces under `src/chongqing_binary/`:
  - `config.py`: YAML config loading, path resolution, and read-only write guard.
  - `data.py`: subject-level manifest interface, label filtering, smoke sampling, subject-level split, feature matrix.
  - `log.py`: logger setup.
  - `models.py`: binary classifier protocol and smoke-only majority baseline.
  - `evaluation.py`: subject-level binary metrics.
  - `leakage.py`: forbidden clinical/diagnosis feature guard.
  - `environment.py`: Python, CUDA, PyTorch, and dependency version collection.
  - `smoke.py`: manifest-only Goal0 smoke pipeline.
- Created command-line scripts:
  - `scripts/check_leakage.py`
  - `scripts/smoke_test.py`
  - `scripts/record_environment.py`
- Created standard-library unit tests:
  - `tests/test_config.py`
  - `tests/test_data_interface.py`
  - `tests/test_leakage_guard.py`
  - `tests/test_evaluation_and_model.py`
- Added automatic leakage tests confirming diagnosis, label, CDRS, CES-DC, HAMA, and suicide-related fields are rejected as feature inputs.
- Recorded environment versions:
  - JSON: `artifacts/environment_versions.json`
  - Markdown: `reports/environment_versions.md`
- Ran Goal0 smoke test:
  - Metrics: `artifacts/smoke/smoke_metrics.json`
  - Predictions: `results/smoke/smoke_predictions.csv`
  - Sample size: 32 subjects.
  - Split: 24 train subjects and 8 test subjects.
  - Features: non-clinical modality coverage fields only.
  - Model: `MajorityClassModel`, a trivial smoke-only baseline.
- Added `.gitignore` rules for Python caches and generated output directories while preserving `.gitkeep` placeholders.

Verification:

- Compile check passed:
  - `/data/home/cqm/miniconda3/envs/chongqing_v1/bin/python -m compileall -q src scripts tests`
- Unit tests passed:
  - `/data/home/cqm/miniconda3/envs/chongqing_v1/bin/python -m unittest discover -s tests`
  - Result: `Ran 13 tests ... OK`
- Leakage script passed:
  - `/data/home/cqm/miniconda3/envs/chongqing_v1/bin/python scripts/check_leakage.py --config configs/smoke.yaml`
- Smoke test passed:
  - `/data/home/cqm/miniconda3/envs/chongqing_v1/bin/python scripts/smoke_test.py --config configs/smoke.yaml`
- Environment recording passed:
  - `/data/home/cqm/miniconda3/envs/chongqing_v1/bin/python scripts/record_environment.py --config configs/default.yaml`
- Read-only input check passed:
  - No smoke, environment, or test output files were found under the raw dataset directory or existing report bundle.

Notes:

- No raw dataset files were modified.
- No existing report files under `inputs/derived_reports/chongqing_binary_diagnosis_report/` were modified during Goal0 initialization.
- No full training was started.
- The current smoke test verifies wiring only and should not be interpreted as model performance.

## 2026-07-07 - Root Structure Reorganization

Status: complete.

Completed:

- Removed root-level legacy entries for the manually grouped folders.
- Moved the existing derived report bundle into the new input area:
  - From `chongqing_binary_diagnosis_report/`
  - To `inputs/derived_reports/chongqing_binary_diagnosis_report/`
- Moved versioned experiment workspaces into the new experiment area:
  - From `v1/` to `experiments/v1/`
  - From `v2/` to `experiments/v2/`
- Did not keep root-level compatibility symlinks, per user request that the root should align fully to the new structure.
- Added structure documentation:
  - `inputs/README.md`
  - `experiments/README.md`
- Updated project configs to use the new manifest and report-input paths:
  - `configs/default.yaml`
- Updated project docs:
  - `AGENTS.md`
  - `PROJECT_SPEC.md`
  - `PROGRESS.md`
- Updated `experiments/v1` path references in README, agent notes, and EEG scripts so v1 still points at its new experiment location and the manifest under `inputs/derived_reports/`.
- Updated path references in migrated report docs where the old project-root report path appeared.

Verification:

- Root directory now contains only the new high-level structure:
  - `artifacts/`
  - `checkpoints/`
  - `configs/`
  - `experiments/`
  - `inputs/`
  - `reports/`
  - `results/`
  - `scripts/`
  - `src/`
  - `tests/`
- Compile check passed:
  - `/data/home/cqm/miniconda3/envs/chongqing_v1/bin/python -m compileall -q src scripts tests experiments/v1/eeg/scripts`
- Unit tests passed:
  - `/data/home/cqm/miniconda3/envs/chongqing_v1/bin/python -m unittest discover -s tests`
  - Result: `Ran 13 tests ... OK`
- Leakage script passed:
  - `/data/home/cqm/miniconda3/envs/chongqing_v1/bin/python scripts/check_leakage.py --config configs/smoke.yaml`
- Smoke test passed:
  - `/data/home/cqm/miniconda3/envs/chongqing_v1/bin/python scripts/smoke_test.py --config configs/smoke.yaml`

Notes:

- Raw dataset files were not modified.
- No full training was started.

## 2026-07-07 - Subject-Level Data Audit, Cohorts, and Fixed Splits

Status: complete.

Completed:

- Added reproducible audit and split construction code:
  - `src/chongqing_binary/audit.py`
  - `src/chongqing_binary/splits.py`
  - `src/chongqing_binary/reports.py`
  - `scripts/build_subject_splits.py`
- Built required cohort artifacts:
  - `artifacts/cohorts/coverage_maximized.csv`
  - `artifacts/cohorts/matched_eeg_fnirs_face.csv`
  - `artifacts/cohorts/missing_modality.csv`
- Built required split artifacts:
  - `artifacts/splits/subject_splits_v1.csv`
  - `artifacts/splits/subject_splits_v1.sha256`
- Built required reports:
  - `reports/data_audit.md`
  - `reports/split_report.md`
  - `reports/leakage_audit.md`
- Added automatic split artifact tests:
  - `tests/test_subject_splits.py`

Audit results:

- Manifest rows: `4610`.
- `A_id` duplicate count: `0`.
- `L_id` duplicate count: `0`.
- Primary label `primary_label_nonhealthy`: `0=3126`, `1=1372`, missing/excluded `112`.
- `sensitivity_label_clear_diagnosis`: `0=3126`, `1=628`, missing/excluded `856`.
- `sensitivity_label_mdd_highrisk`: `0=3126`, `1=1234`, missing/excluded `250`.
- Modality coverage:
  - EEG: `2498`.
  - fNIRS: `3284`.
  - Face: `4573`.
  - Eye direct: `291`.
  - Eye name-mapped: `871`.
- Demographic issues:
  - Missing sex rows: `6`.
  - Missing age rows: `6`.
  - Missing grade rows: `6`.
  - Age rows missing, non-numeric, `<9`, or `>20`: `8`, including two abnormal numeric ages `33` and `36`.
- Metadata-level duplicate file checks:
  - EEG role-file duplicates: `0` data role duplicates and `0` event role duplicates across Rest/Oddball/1BACK.
  - Face duplicate MP4 `L_id` count: `0` for both face tasks.
  - fNIRS duplicate L-id directory or `.nirs` file counts: `0` in audited source tasks.
  - Eye tracking filename-level duplicate stems: Tobii raw xlsx `0`, Qixin csv `0`, Tobii `.rec` duplicate stems `5`.

Cohorts:

- `coverage_maximized`: `4497` subjects, defined as primary-label valid and at least one objective modality available.
- `matched_eeg_fnirs_face`: `2376` subjects, defined as primary-label valid and EEG+fNIRS+Face all available.
- `missing_modality`: `3837` subjects, defined as primary-label valid, at least one modality available, and not complete across EEG+fNIRS+Face+name-mapped eye.

Fixed split:

- Split scope: `coverage_maximized`.
- Locked test set: `900` subjects (`20.0%`).
- Cross-validation pool: `3597` subjects (`80.0%`).
- Five CV validation folds: `720`, `720`, `719`, `719`, `719` subjects.
- Locked test label counts: `0=627`, `1=273`.
- CV pool label counts: `0=2499`, `1=1098`.
- Split balancing used deterministic stratification that prioritizes primary label, sex, age bin, grade group, modality pattern, and inferred fNIRS device; rare fine-grained strata were collapsed as needed.
- SHA256 for `subject_splits_v1.csv`: recorded in `artifacts/splits/subject_splits_v1.sha256`.
- The locked test set is documented as final-evaluation-only and must not be used for feature selection, model selection, threshold tuning, or early stopping.

Verification:

- Build command passed:
  - `/data/home/cqm/miniconda3/envs/chongqing_v1/bin/python scripts/build_subject_splits.py --config configs/default.yaml`
- Compile check passed:
  - `/data/home/cqm/miniconda3/envs/chongqing_v1/bin/python -m compileall -q src scripts tests`
- Unit tests passed:
  - `/data/home/cqm/miniconda3/envs/chongqing_v1/bin/python -m unittest discover -s tests`
  - Result: `Ran 20 tests ... OK`
- Leakage script passed:
  - `/data/home/cqm/miniconda3/envs/chongqing_v1/bin/python scripts/check_leakage.py --config configs/smoke.yaml`
- Smoke test passed:
  - `/data/home/cqm/miniconda3/envs/chongqing_v1/bin/python scripts/smoke_test.py --config configs/smoke.yaml`
- SHA256 check passed from `artifacts/splits/`:
  - `sha256sum -c subject_splits_v1.sha256`
- Automatic split tests confirm:
  - `A_id` and `L_id` are unique in `subject_splits_v1.csv`.
  - Locked test subjects do not overlap with CV pool subjects by `A_id` or `L_id`.
  - Each CV fold's validation subjects do not overlap with that fold's training subjects by `A_id` or `L_id`.

Notes:

- No formal deep model training was run.
- Raw dataset files were not modified.

## 2026-07-07 - Fixed-Split Traditional Baselines

Status: complete.

Completed:

- Added fixed-split baseline configuration:
  - `configs/baselines/default.yaml`
  - `configs/baselines/smoke.yaml`
- Added reusable baseline implementation:
  - `src/chongqing_binary/baselines.py`
  - `scripts/run_baselines.py`
- Added automatic baseline tests:
  - `tests/test_baselines.py`
  - `tests/test_baseline_artifacts.py`
- Ran required no-information baselines:
  - `no_information_majority`
  - `no_information_stratified_random`
- Ran required demographics-only baselines using cleaned ordinary demographics only:
  - `demographics_logistic_regression`
  - `demographics_lightgbm`
- Ran existing EEG Rest traditional feature baselines using the available v1 feature table:
  - `eeg_rest_logistic_regression`
  - `eeg_rest_random_forest`
  - `eeg_rest_lightgbm`
- Did not report fNIRS or Face model results because no reliable subject-level traditional fNIRS or Face feature table is currently configured. Reusable config/interface placeholders are present for both.
- Used fixed `artifacts/splits/subject_splits_v1.csv`:
  - CV out-of-fold evaluation uses only the non-locked CV pool.
  - Locked-test evaluation trains final estimators only on the CV pool.
  - Locked test is not used for feature selection, hyperparameter tuning, threshold tuning, or early stopping.
- Ensured all preprocessing is inside sklearn pipelines and is fit only on the current training fold or final CV-pool training set.
- Enforced leakage guards for baseline feature columns:
  - Diagnosis, labels, CDRS, CES-DC, HAMA, SCARED, self-harm, suicide, and related clinical scale fields are forbidden as model inputs.
- Output required metrics with 95% bootstrap confidence intervals:
  - AUROC
  - AUPRC
  - Balanced Accuracy
  - Macro-F1
  - Sensitivity
  - Specificity
  - PPV
  - NPV
  - Brier Score
  - Expected Calibration Error
  - Maximum Calibration Error
- Recorded `zero_division=0` for PPV, NPV, F1, sensitivity, and specificity when a denominator is empty.
- Confirmed this run used CPU estimators only. LightGBM used its default CPU backend; no CUDA/GPU training was enabled.

Outputs:

- Main results:
  - `results/baseline_results.csv`
- Main report:
  - `reports/baseline_report.md`
- Configs:
  - `configs/baselines/default.yaml`
  - `configs/baselines/smoke.yaml`
- Checkpoints:
  - `checkpoints/baselines/no_information__no_information_majority.joblib`
  - `checkpoints/baselines/no_information__no_information_stratified_random.joblib`
  - `checkpoints/baselines/demographics__demographics_logistic_regression.joblib`
  - `checkpoints/baselines/demographics__demographics_lightgbm.joblib`
  - `checkpoints/baselines/eeg_rest__eeg_rest_logistic_regression.joblib`
  - `checkpoints/baselines/eeg_rest__eeg_rest_random_forest.joblib`
  - `checkpoints/baselines/eeg_rest__eeg_rest_lightgbm.joblib`
- Supporting artifacts:
  - `artifacts/baselines/baseline_predictions.csv`
  - `artifacts/baselines/baseline_fold_metrics.csv`
  - `artifacts/baselines/feature_availability.json`
  - `artifacts/baselines/baseline_run_manifest.json`

Result summary:

- `baseline_results.csv` contains `14` rows: `7` models times `2` evaluation stages (`cv_oof` and `locked_test`).
- Locked-test subjects:
  - No-information and demographics baselines: `900` subjects, `273` positive.
  - EEG Rest baselines: `248` subjects, `83` positive, limited to subjects with existing EEG Rest traditional features.
- Locked-test AUROC:
  - `demographics_lightgbm`: `0.6765`
  - `demographics_logistic_regression`: `0.6687`
  - `eeg_rest_logistic_regression`: `0.5832`
  - `eeg_rest_lightgbm`: `0.5418`
  - `eeg_rest_random_forest`: `0.5127`
  - `no_information_majority`: `0.5000`
  - `no_information_stratified_random`: `0.4944`

Verification:

- Baseline smoke run passed:
  - `/data/home/cqm/miniconda3/envs/chongqing_v1/bin/python scripts/run_baselines.py --config configs/baselines/smoke.yaml`
- Formal baseline run passed:
  - `/data/home/cqm/miniconda3/envs/chongqing_v1/bin/python scripts/run_baselines.py --config configs/baselines/default.yaml`
- Completion audit confirmed:
  - All required models are present in `results/baseline_results.csv`.
  - Both `cv_oof` and `locked_test` stages are present for each required model.
  - All requested metrics and `_ci_low`/`_ci_high` 95% CI columns are present and finite.
  - fNIRS and Face are explicitly skipped in `artifacts/baselines/feature_availability.json` without fake result rows.
  - Prediction rows respect the locked-test boundary.
  - All checkpoint paths recorded in `artifacts/baselines/baseline_run_manifest.json` exist.
- Compile check passed:
  - `/data/home/cqm/miniconda3/envs/chongqing_v1/bin/python -m compileall -q src scripts tests`
- Unit tests passed:
  - `/data/home/cqm/miniconda3/envs/chongqing_v1/bin/python -m unittest discover -s tests -v`
  - Result: `Ran 29 tests ... OK`
- Leakage script passed:
  - `/data/home/cqm/miniconda3/envs/chongqing_v1/bin/python scripts/check_leakage.py --config configs/smoke.yaml`
- Goal0 smoke test still passed:
  - `/data/home/cqm/miniconda3/envs/chongqing_v1/bin/python scripts/smoke_test.py --config configs/smoke.yaml`
- GPU check:
  - `nvidia-smi` showed two `NVIDIA RTX A6000` GPUs at `0%` utilization and no compute processes during post-run inspection.

Notes:

- Raw dataset files were not modified.
- Read-only derived input files were not modified.
- No deep model training was run.

## 2026-07-07 - Goal 2.5 EEG/fNIRS/Face Readiness

Completed Goal 2.5 readiness work:

- Updated `AGENTS.md`, `PROJECT_SPEC.md`, and `EXPERIMENT_PROTOCOL.md` for Goal 2.5, baseline-exposed pilot holdout policy, CV-pool OOF development, modality readiness gates, and Goal 3-7 roadmap.
- Added modular code under `src/chongqing_binary/cohorts.py`, `groups.py`, `eeg/`, `fnirs/`, `face/`, and `readiness.py`.
- Added readiness configs under `configs/readiness/`.
- Added scripts: `audit_eeg_readiness.py`, `audit_fnirs_readiness.py`, `audit_face_readiness.py`, `build_cohorts_v2.py`, `audit_groups.py`, `generate_goal2_5_reports.py`.
- Generated EEG, fNIRS, and Face task/video availability tables, smoke artifacts, cohort reconciliation, group/confound audit, modality design docs, and multimodal readiness report.

Commands run:

- `/data/home/cqm/miniconda3/envs/avmoe/bin/python scripts/audit_eeg_readiness.py --config configs/readiness/eeg_smoke.yaml --smoke-limit 2 --seed 20260707`
- `/data/home/cqm/miniconda3/envs/avmoe/bin/python scripts/audit_fnirs_readiness.py --config configs/readiness/fnirs_smoke.yaml --smoke-limit 2 --seed 20260707`
- `/data/home/cqm/miniconda3/envs/avmoe/bin/python scripts/audit_face_readiness.py --config configs/readiness/face_smoke.yaml --smoke-limit 2 --seed 20260707`
- `/data/home/cqm/miniconda3/envs/avmoe/bin/python scripts/build_cohorts_v2.py --config configs/readiness/default.yaml --seed 20260707`
- `/data/home/cqm/miniconda3/envs/avmoe/bin/python scripts/audit_groups.py --config configs/readiness/default.yaml --seed 20260707`
- `/data/home/cqm/miniconda3/envs/avmoe/bin/python scripts/generate_goal2_5_reports.py`
- `/data/home/cqm/miniconda3/envs/avmoe/bin/python -m compileall -q src scripts tests`
- `/data/home/cqm/miniconda3/envs/avmoe/bin/python -m unittest discover -s tests -v`
- `/data/home/cqm/miniconda3/envs/avmoe/bin/python scripts/check_leakage.py --config configs/smoke.yaml`

Key counts:

- EEG flag/file/QC: 2448/2448/2437
- fNIRS flag/file/QC: 3202/3190/3190
- Face flag/file/QC: 4468/4468/4468
- core3 flag/file/QC complete: 2376/2365/2354
- 2376 is reproduced as current core3 flag-complete. 2189 is not reproduced from the canonical manifest and is recorded as an older/stricter unresolved denominator.

Readiness:

- EEG: `READY_WITH_FIXES`.
- fNIRS: `READY_WITH_FIXES`.
- Face: `READY_WITH_FIXES`.

Blocking items before formal training:

- EEG: refactor old v1 code to fixed split, add inner validation, clean imbalance handling, and subject-balanced windows.
- fNIRS: confirm event/channel/region alignment and keep device-specific modeling until merge conditions are met.
- Face: expand full face detection/QC and run shortcut controls for background/device/video metadata.

Recommended next Goal: Goal 3 EEG fixed-split formal single-modality experiment, with Face QC/shortcut work as the strongest parallel candidate.

Verification:

- Compile check passed with no errors.
- Unit tests passed: `Ran 50 tests ... OK`.
- Leakage guard passed for configured smoke feature columns.
- EEG smoke, fNIRS smoke, and Face smoke all recorded `passed: true` and `pilot_holdout_used: false`.
- `subject_splits_v1.csv` SHA256 still matches `artifacts/splits/subject_splits_v1.sha256`.
- Raw dataset remains protected by the read-only input guard; no script writes under the raw input tree.

## 2026-07-08 - Goal 2.6 Fixed-CV Lightweight Multimodal Baselines

Completed Goal 2.6 under the fixed CV-only protocol:

- Added Goal 2.6 configs under `configs/goal2_6/` for shared protocol, bootstrap, EEG, fNIRS, Face, and model grids.
- Added reusable implementation under `src/chongqing_binary/goal2_6/`:
  - `eeg.py`: subject-level EEG signal/QC features from v1 deep-window caches for Rest, Oddball, and 1BACK.
  - `fnirs.py`: device-aware Yiruid `.nirs` and Bikom vendor CSV features for Rest, VFT, and 1BACK.
  - `face.py`: frozen `torchvision_resnet18` visual embeddings for self-introduction and task videos, with full-frame, face-crop, and background variants.
  - `runner.py`: fixed outer CV OOF modeling, inner 3-fold hyperparameter/threshold selection, train-fold PCA for high-dimensional Face embeddings, bootstrap CIs, paired comparisons, core3 same-cohort comparison, shortcut baselines, and group-robustness supplemental checks.
  - `report.py`: source-backed markdown reports.
- Added scripts:
  - `extract_eeg_goal2_6_features.py`
  - `extract_fnirs_goal2_6_features.py`
  - `extract_face_goal2_6_features.py`
  - `run_goal2_6_eeg.py`
  - `run_goal2_6_fnirs.py`
  - `run_goal2_6_face.py`
  - `run_goal2_6_core3.py`
  - `summarize_goal2_6.py`
- Added Goal 2.6 protocol tests in `tests/test_goal2_6_protocol.py`, including checks for CV-only predictions, fNIRS 1BACK, Face two-video, PCA diagnostics, group robustness, paired bootstrap, and core3 subject-set identity.

Commands run:

- `/data/home/cqm/miniconda3/envs/avmoe/bin/python scripts/extract_eeg_goal2_6_features.py --config configs/goal2_6/eeg.yaml`
- `/data/home/cqm/miniconda3/envs/avmoe/bin/python scripts/extract_fnirs_goal2_6_features.py --config configs/goal2_6/fnirs.yaml`
- `/data/home/cqm/miniconda3/envs/avmoe/bin/python scripts/extract_face_goal2_6_features.py --config configs/goal2_6/face.yaml`
- `/data/home/cqm/miniconda3/envs/avmoe/bin/python - <<'PY' ... run_goal2_6(['eeg', 'fnirs', 'face', 'core3', 'shortcut']) ... PY`
- `/data/home/cqm/miniconda3/envs/avmoe/bin/python scripts/summarize_goal2_6.py --config configs/goal2_6/models.yaml`
- `/data/home/cqm/miniconda3/envs/avmoe/bin/python -m compileall -q src scripts tests`
- `/data/home/cqm/miniconda3/envs/avmoe/bin/python -m unittest discover -s tests -v`
- `/data/home/cqm/miniconda3/envs/avmoe/bin/python scripts/check_leakage.py --config configs/smoke.yaml`
- `sha256sum -c subject_splits_v1.sha256` from `artifacts/splits/`

Feature extraction counts:

- EEG signal/QC:
  - Rest: 1022/1033 CV subjects; 11 QC-blocked for too few valid windows.
  - Oddball: 1827/1837 CV subjects; 10 QC-blocked for too few valid windows.
  - 1BACK: 1154/1345 CV subjects; 191 QC-blocked for too few valid windows.
- fNIRS signal/QC:
  - Yiruid Rest: 1514/1514.
  - Yiruid VFT: 1480/1480.
  - Yiruid 1BACK: 1422/1423; 1 QC-blocked file read failure.
  - Bikom Rest: 1017/1017.
  - Bikom VFT: 1022/1022.
  - Bikom 1BACK: 985/995; 10 QC-blocked missing HbO/HbR CSV rows.
- Face signal/QC:
  - Self-introduction: 3572/3597; 25 video-file-missing QC-blocked rows.
  - Task video: 3567/3597; 30 video-file-missing QC-blocked rows.
  - Two-video native cohort: 3567 CV subjects with self-introduction and task signal/QC intersection.
  - Frozen encoder: `torchvision_resnet18`, ImageNet weights, 8 sampled frames per video, OpenCV Haar fallback detector. Face embedding extraction used `cuda:0`; the sklearn baseline matrix and bootstrap statistics ran on CPU.
- Core3 same-cohort comparison uses 661 shared CV subjects across EEG Rest, Yiruid VFT, and Face self-introduction.

Model results:

- Unified run wrote:
  - 105 model datasets and 261 model/feature/cohort groups.
  - `results/goal2_6/all_oof_predictions.csv`: 453,480 subject-level OOF prediction rows.
  - `results/goal2_6/all_pooled_metrics.csv`: 522 pooled metric rows, with 261 `inner_cv` and 261 fixed-0.5 threshold rows.
  - `results/goal2_6/all_fold_metrics.csv`: 2,610 fold metric rows.
  - `results/goal2_6/bootstrap_confidence_intervals.csv`: 2,610 CI rows, all with 1000 bootstrap resamples.
  - `results/goal2_6/paired_model_comparisons.csv`: 130 paired comparison rows, all with 1000 paired bootstrap resamples.
  - `results/goal2_6/selected_hyperparameters.csv`: 1,305 outer-fold selected-parameter rows.
  - `results/goal2_6/pca_explained_variance.csv`: 1,245 PCA diagnostic rows; high-dimensional Face/Core3 models used at most 64 components.
  - `results/goal2_6/group_robustness_summary.csv`: 13 supplemental group-robustness rows.
  - `results/goal2_6/feature_counts.csv`, `native_cohort_summary.csv`, `core3_same_cohort_summary.csv`, `shortcut_baseline_summary.csv`, and `exclusion_summary.csv`.
- Best inner-CV-threshold rows:
  - EEG Rest: best overall demographics HGB, n=1022, AUROC 0.6012, AUPRC 0.4174; best signal-like signal+demographics LR, AUROC 0.5599, AUPRC 0.3831.
  - EEG Oddball: best overall demographics LR, n=1827, AUROC 0.6024, AUPRC 0.4242; best signal-like signal+QC+demographics HGB, AUROC 0.5873, AUPRC 0.3944.
  - EEG 1BACK: best overall demographics LR, n=1154, AUROC 0.5981, AUPRC 0.3557; best signal-like signal+demographics LR, AUROC 0.5399, AUPRC 0.3190.
  - EEG old Rest v1 fixed-split control: best signal HGB, n=999, AUROC 0.5459, AUPRC 0.3697; demographics LR reached AUROC 0.5954.
  - fNIRS Yiruid Rest: best overall demographics RF, n=1514, AUROC 0.5924, AUPRC 0.4498; best signal-like signal+demographics HGB, AUROC 0.5882, AUPRC 0.4630.
  - fNIRS Yiruid VFT: best overall and signal-like signal+QC RF, n=1480, AUROC 0.5908, AUPRC 0.4684; demographics LR AUROC 0.5873.
  - fNIRS Yiruid 1BACK: best overall demographics LR, n=1422, AUROC 0.5859, AUPRC 0.4399; best signal-like signal+demographics LR, AUROC 0.5604, AUPRC 0.4305.
  - fNIRS Bikom Rest: best overall demographics LR, n=1017, AUROC 0.6243, AUPRC 0.4360; best signal-like signal+demographics LR, AUROC 0.5542, AUPRC 0.3476.
  - fNIRS Bikom VFT: best overall demographics LR, n=1022, AUROC 0.6212, AUPRC 0.4261; best signal-like signal+demographics LR, AUROC 0.5735, AUPRC 0.3975.
  - fNIRS Bikom 1BACK: best overall demographics LR, n=985, AUROC 0.6258, AUPRC 0.4395; best signal-like signal+demographics LR, AUROC 0.5865, AUPRC 0.4014.
  - Face self-introduction: best overall demographics LR, n=3572, AUROC 0.6702, AUPRC 0.4305; best face signal-like face+demographics LR, AUROC 0.6404, AUPRC 0.4097; background-only LR AUROC 0.6028.
  - Face task video: best overall demographics LR, n=3567, AUROC 0.6693, AUPRC 0.4290; best face signal-like face+demographics LR, AUROC 0.6452, AUPRC 0.4176; background-only LR AUROC 0.6230.
  - Face two-video: best overall demographics LR, n=3567, AUROC 0.6694, AUPRC 0.4291; best face signal-like face+demographics LR, AUROC 0.6458, AUPRC 0.4173; background-only LR AUROC 0.6179.
  - Shortcut group/device: logistic regression, n=3597, AUROC 0.6778, AUPRC 0.4671.
- Core3 same-cohort:
  - The 24 core3 prediction groups all share the same 661 `L_id` subject set.
  - EEG Rest: demographics LR AUROC 0.5754; EEG modality-only LR AUROC 0.5143.
  - fNIRS Yiruid VFT: modality-only RF AUROC 0.5845; demographics LR AUROC 0.5754.
  - Face self-introduction: demographics LR AUROC 0.5754; Face modality-only LR AUROC 0.5670.
- Paired bootstrap examples:
  - No signal-only EEG/fNIRS feature set significantly beat demographics; 23 signal-vs-demographics comparisons had AUROC CIs entirely below zero.
  - Oddball signal vs QC improved for HGB by AUROC +0.0458, 95% CI [0.0103, 0.0860], and signal+QC+demographics improved over signal by +0.0633, CI [0.0308, 0.0951].
  - Face crop beat background in 5 comparisons, but with modest AUROC gains of about +0.0248 to +0.0409.
  - Face self-introduction face-crop vs metadata improved AUROC by +0.1345, 95% CI [0.1067, 0.1627], 5/5 fold direction consistency.
  - Face task face-crop vs metadata improved AUROC by +0.0878 to +0.0902 depending on model, CI excluding zero.
- Group robustness:
  - EEG Oddball signal+demographics best robustness AUROC 0.5892.
  - fNIRS Yiruid VFT signal+QC best robustness AUROC 0.5840.
  - Face task face+demographics best robustness AUROC 0.6197.
  - Face two-video face+demographics best robustness AUROC 0.6247.
  - Shortcut group/device robustness still reached AUROC 0.6023 with HGB.

Reports generated:

- `reports/goal2_6_eeg_results.md`
- `reports/goal2_6_fnirs_results.md`
- `reports/goal2_6_face_results.md`
- `reports/goal2_6_shortcut_analysis.md`
- `reports/goal2_6_core3_comparison.md`
- `reports/goal2_6_final_report.md`

Protocol and QA evidence:

- Predictions are CV-only: `split_group` in predictions is `{'cv': 453480}` after merge with `subject_splits_v1.csv`.
- Locked-test subjects are absent from all OOF predictions: locked sum `0`.
- Outer folds are `[0, 1, 2, 3, 4]`; prediction fold assignments exactly match `subject_splits_v1.csv`.
- All 261 model/feature/cohort OOF groups have one row per `L_id`; no duplicate subject predictions under the full cohort/modality/device/task/feature/model/seed/fold key.
- Bootstrap and paired comparisons both use 1000 resamples.
- Required post-audit scopes are present in `feature_counts.csv`: `fnirs_yiruid_1back_native`, `fnirs_bikom_1back_native`, and `face_two_video_native`.
- `pca_explained_variance.csv` and `group_robustness_summary.csv` are nonempty and covered by tests.
- `subject_splits_v1.csv` SHA256 still matches `artifacts/splits/subject_splits_v1.sha256`.
- Final verification:
  - Compile check passed.
  - Unit tests passed: `Ran 60 tests ... OK`.
  - Leakage guard passed for configured smoke feature columns.

Limitations and interpretation:

- The baseline-exposed pilot holdout remains excluded from feature extraction, model selection, threshold selection, and reporting.
- LightGBM/XGBoost are not installed in the `avmoe` environment; `HistGradientBoostingClassifier` is recorded as the boosting fallback, with a lightweight grid (`max_iter=10`, `max_leaf_nodes=7`) for tractable full-matrix runs.
- Yiruid fNIRS features do not claim formal HbO/HbR conversion; they use raw/log-intensity and OD-like summaries. Bikom uses vendor HbO/HbR/HbT CSV channels with a configured row cap.
- Face uses OpenCV Haar as a fallback detector because MediaPipe/MTCNN/RetinaFace are unavailable. Face shortcut controls are therefore central to interpretation.
- Shortcut signal is substantial: group/device reaches AUROC 0.6778, and Face background reaches AUROC about 0.603 to 0.623. Any apparent Face signal gains should be treated as shortcut-sensitive until source/site/background effects are further controlled.
- Final modality statuses in `reports/goal2_6_final_report.md`: EEG `WEAK_OR_UNCERTAIN_SIGNAL`; fNIRS `WEAK_OR_UNCERTAIN_SIGNAL`; Face `SHORTCUT_RISK`.

Recommended next Goal: Goal 3 EEG fixed-CV formal single-modality modeling, while carrying forward shortcut mitigation for Face and Hb/event validation for fNIRS before stronger modality-specific deep models.

## 2026-07-09 - Goal 2.7 Protocol Repair, Independent Increment, and Shortcut Calibration

Completed Goal 2.7 as a co-primary Standard CV and Group-aware CV rerun:

- Added Goal 2.7 configs under `configs/goal2_7/` for shared protocol, bootstrap, EEG, fNIRS, Face, and model grids.
- Added `src/chongqing_binary/goal2_7/` with repaired feature loading, Standard/Group protocol cloning, fold-specific threshold metrics, Face visual-only PCA branching, paired bootstrap, supplemental restart support, and source-backed markdown reports.
- Added scripts:
  - `scripts/extract_eeg_goal2_7_features.py`
  - `scripts/extract_fnirs_goal2_7_features.py`
  - `scripts/extract_face_goal2_7_features.py`
  - `scripts/audit_goal2_7_events.py`
  - `scripts/run_goal2_7.py`
  - `scripts/summarize_goal2_7.py`
- Added `tests/test_goal2_7_protocol.py`; full test discovery now covers Goal 2.7 result integrity, double-CV outputs, event blocked status, Face strict controls, bootstrap/paired requirements, Core3 naming, and leakage guards.

Commands run:

- `/data/home/cqm/miniconda3/envs/avmoe/bin/python scripts/extract_eeg_goal2_7_features.py --config configs/goal2_7/eeg.yaml`
- `/data/home/cqm/miniconda3/envs/avmoe/bin/python scripts/extract_fnirs_goal2_7_features.py --config configs/goal2_7/fnirs.yaml`
- `/data/home/cqm/miniconda3/envs/avmoe/bin/python scripts/extract_face_goal2_7_features.py --config configs/goal2_7/face.yaml`
- `/data/home/cqm/miniconda3/envs/avmoe/bin/python scripts/audit_goal2_7_events.py`
- `PYTHONPATH=src PYTHONUNBUFFERED=1 /data/home/cqm/miniconda3/envs/avmoe/bin/python scripts/run_goal2_7.py --skip-supplemental`
- `PYTHONPATH=src PYTHONUNBUFFERED=1 /data/home/cqm/miniconda3/envs/avmoe/bin/python scripts/run_goal2_7.py --supplemental-only`
- `PYTHONPATH=src PYTHONUNBUFFERED=1 /data/home/cqm/miniconda3/envs/avmoe/bin/python scripts/summarize_goal2_7.py`
- `PYTHONPATH=src /data/home/cqm/miniconda3/envs/avmoe/bin/python -m compileall -q src scripts tests`
- `PYTHONPATH=src /data/home/cqm/miniconda3/envs/avmoe/bin/python -m unittest discover -s tests`

Feature and audit outputs:

- Preimplementation audit: `reports/goal2_7_preimplementation_audit.md`.
- EEG event audit:
  - Rest is event-free.
  - Oddball cache contains only code `22`; formal target/non-target ERP is blocked and retained only as `oddball_target_only_proxy`.
  - 1BACK codes `18`/`19` lack confirmed condition semantics; condition-difference features are blocked and only generic features are used.
- fNIRS event/timing audit:
  - Rest is modeled as whole-recording.
  - Yiruid VFT/1BACK markers are present but timing semantics are unconfirmed.
  - Bikom VFT has no usable task markers for formal task-response modeling.
  - Bikom full files are read; the Goal 2.6 fixed 2000-row cap is removed. Bikom Rest audit records rows beyond 2000 and markers after row 2000.
  - Yiruid features remain raw/log-intensity or OD-like; no HbO/HbR claim is made.
- Face strict extraction:
  - Frozen encoder: `torchvision_resnet18`, `ResNet18_Weights.IMAGENET1K_V1`, 512-dimensional features, frozen, device `cuda:0`.
  - Detector preference: OpenCV YuNet checkpoint; actual fallback detector usage is recorded as OpenCV Haar in this environment.
  - `sample_frames: 16`, `min_valid_face_frames: 4`, strict face frames do not use center-crop fallback, and strict background masks detected face boxes.
  - Contact sheets written: 200.
  - Self-introduction: 3597 QC videos, 3565 strict-face-valid, 32 blocked, mean detection rate 0.9904, fallback videos 3572, audio used 0.
  - Task video: 3597 QC videos, 3558 strict-face-valid, 39 blocked, mean detection rate 0.9831, fallback videos 3567, audio used 0.

Result outputs:

- `results/goal2_7/all_oof_predictions_standard_cv.csv`: 1,528,167 rows.
- `results/goal2_7/all_oof_predictions_group_cv.csv`: 1,528,167 rows.
- `results/goal2_7/all_pooled_metrics.csv`: 3,672 rows.
- `results/goal2_7/all_fold_metrics.csv`: 18,360 rows.
- `results/goal2_7/bootstrap_confidence_intervals.csv`: 36,720 rows, all with 1000 resamples and 10 metrics.
- `results/goal2_7/paired_increment_comparisons.csv`: 618 rows, all with 1000 paired subject bootstrap resamples.
- `results/goal2_7/demographics_decomposition.csv`: 1,188 rows.
- `results/goal2_7/standard_vs_group_cv.csv`: 918 rows.
- `results/goal2_7/pca_diagnostics.csv`: 9,060 rows.
- `results/goal2_7/threshold_diagnostics.csv`: 9,180 rows.
- Required OOF fields are present, including `selected_threshold_per_subject`, `selected_threshold_per_fold`, and `threshold_source`.

Key results:

- No native EEG, fNIRS, or Face required independent-increment comparison had AUROC 95% CI fully above 0.
- Positive significant required increment rows were limited to Core3 Face sensitivity rows, not native-cohort evidence.
- EEG:
  - Standard CV best demographics-like rows reached about 0.64 AUROC with group variables; signal-only was weaker.
  - Group CV best signal rows were around 0.52-0.57 AUROC.
  - Required signal+demographics vs demographics and signal+QC+demographics vs QC+demographics comparisons were mostly negative and often significantly below zero.
- fNIRS:
  - Yiruid VFT remained the least weak signal candidate by point estimate: best signal+QC+demographics around 0.5887 AUROC in Standard CV and 0.5846 in Group CV.
  - Demographics/group rows stayed stronger than signal rows; required increments did not clear paired bootstrap.
- Face:
  - Standard CV best face-only AUROC was about 0.645; Group CV best face-only AUROC was about 0.634.
  - Standard CV demographics_group reached 0.7083 AUROC, and group_proxy_only reached 0.6768 AUROC.
  - Face-only significantly beat background/metadata/QC in many paired controls, but face+demographics did not reliably beat demographics and was close to background+demographics.
- Demographics decomposition:
  - In the largest Face cohorts, age_only reached about 0.624 AUROC, sex_only about 0.593, grade_only about 0.637, age+sex+grade about 0.673, group_proxy_only about 0.677, and demographics_group about 0.708 in Standard CV.
  - Group-aware CV reduced group-proxy-heavy rows, confirming acquisition-group shortcut risk.
- Core3:
  - Cohort name is fixed to `core3_rest_yiruidvft_selfintro_intersection`, n=661.
  - Core3 is not reported as the full 2354-person core3 pool.
  - Face had the only positive required Core3 increments, but this did not override native-cohort shortcut risk.

Reports generated:

- `reports/goal2_7_preimplementation_audit.md`
- `reports/goal2_7_eeg_event_audit.md`
- `reports/goal2_7_fnirs_event_audit.md`
- `reports/goal2_7_face_detection_audit.md`
- `reports/goal2_7_demographics_and_group_analysis.md`
- `reports/goal2_7_eeg_results.md`
- `reports/goal2_7_fnirs_results.md`
- `reports/goal2_7_face_results.md`
- `reports/goal2_7_core3_comparison.md`
- `reports/goal2_7_protocol_comparison.md`
- `reports/goal2_7_final_report.md`

Verification:

- Compile check passed.
- Unit test discovery passed: `Ran 105 tests ... OK`.
- Supplemental bootstrap/paired outputs are restartable from saved OOF predictions; the full model matrix does not need to be rerun for CI refresh.
- Both OOF files contain only their expected protocol labels: `standard_cv` and `group_cv`.
- Bootstrap and paired outputs use 1000 resamples.
- No native required independent-increment row has AUROC CI fully above 0.

Compute note:

- GPU was used for Face frozen embedding extraction (`cuda:0`).
- Traditional classifiers (Logistic Regression, Random Forest, HistGradientBoosting), OOF metric aggregation, bootstrap CIs, and paired comparisons are CPU-bound sklearn/statistical workloads.

Final modality statuses:

- EEG: `BLOCKED_BY_INVALID_TASK_SEMANTICS + NO_CLEAR_SIGNAL`.
- fNIRS: `BLOCKED_BY_INVALID_TASK_SEMANTICS + NO_CLEAR_SIGNAL`.
- Face: `SHORTCUT_DOMINATED`.
- No modality reaches `INDEPENDENT_SIGNAL_SUPPORTED`.

Recommended next Goal: a Goal 2.8 remediation/decision gate before Goal 3/4/5 deep modeling. It should recover and document EEG/fNIRS event timing, add group-balanced or residualized demographic baselines, and decide whether Face warrants stricter shortcut-controlled replication.

## 2026-08-23 - Goal 2.7 Formalization and GitHub Release

Goal 2.7 was promoted from a completed local experiment to the project's formal
lightweight multimodal evidence baseline.

Documentation updates:

- Updated `AGENTS.md`, `PROJECT_SPEC.md`, and `EXPERIMENT_PROTOCOL.md` from
  the stale Goal 2.5 stage to the completed Goal 2.7 protocol and decisions.
- Made Goal 2.8 the explicit remediation/decision gate before Goal 3/4/5.
- Added `reports/goal2_7_release_notes.md`,
  `results/goal2_7/README.md`, and `artifacts/goal2_7/README.md`.
- Canonicalized project/raw-data documentation and default config paths to
  `/data/home/cqm/Project`.

Release engineering:

- Added `scripts/build_goal2_7_release_manifest.py`.
- Added deterministic gzip archives for the two complete OOF prediction files.
- Added `artifacts/goal2_7/release_manifest.json` with row counts, byte sizes,
  SHA-256 hashes, release disposition, and local-only reasons.
- Added supplemental-run fallback so pandas can read tracked `.csv.gz` OOF
  archives when uncompressed CSVs are absent.
- Updated `.gitignore` so uncompressed >100 MB OOF CSVs, large Face embeddings,
  `.part.csv` checkpoints, and identifiable Face contact sheets remain local.

The formal release preserves all compact features, metrics, CIs, paired tests,
reports, code, configs, and complete compressed OOF predictions. Face contact
sheets are deliberately excluded from Git because they contain identifiable
source-video frames.

Formal-release verification:

- Full unit test discovery passed: `Ran 107 tests ... OK`.
- Goal 2.7 protocol tests passed: `Ran 47 tests ... OK`.
- Leakage audit, fixed-split SHA-256 validation, gzip integrity, archive row
  counts, and release-manifest hashes passed.

## 2026-09-07 - Goal 2.8 Opened: Environment Merge, Retirement, and Supersession

Status: WP0 complete; WP1 onward pending.

Verified against the raw dataset that the Goal 2.7 modality conclusions rest on
incorrect readings of the data. Evidence and root causes are recorded in
`reports/goal2_7_superseded_notice.md`. Summary:

- EEG Oddball raw `*_evt.bdf` contains both code `11` (500 Hz standard, median
  123/subject) and code `22` (1000 Hz deviant target, median 25/subject) across
  313 sampled subjects; the target-only cache comes from a hardcoded
  `event_codes: ["22"]` in `experiments/v1/eeg/scripts/cache_deep_windows.py`.
- EEG 1BACK codes `18`/`19` are positional: `19` is the block-initial stimulus
  (exactly 2/subject), `18` every later stimulus, SOA 2.00 s. Codes `66`/`77`
  lag one trial. Block 2 is systematically truncated.
- Yiruid `.nirs` files carry `SD.Lambda = [690, 830]`, 16 sources, 16 detectors,
  3D optode positions and a marker matrix; the old reader only probed headers.
- fNIRS block timing is confirmed for all five tasks on both devices.
- `面部2-任务` is an ~11 minute multi-phase session with 24 segments recoverable
  from `附件/网页数据.xlsx`; Goal 2.7 sampled 16 frames across the whole session.

Environment merge:

- `chongqing_v1` is now the single project environment. Installed
  `opencv-python-headless==4.12.0.88`, `openpyxl==3.1.5` and `et_xmlfile==2.0.0`
  with `--no-deps` through the local proxy; numpy, pandas, scipy, scikit-learn
  and torch were unchanged. `migration/chongqing-v1-requirements.lock.txt`
  updated to 67 packages.
- Verified in that environment: OpenCV decodes the face videos, YuNet loads and
  detects, torchvision ResNet18 loads offline from the local weight cache and
  moves to CUDA, MNE reads raw BDF and its events, scipy reads `.nirs` including
  `SD`, and openpyxl reads `网页数据.xlsx`. CUDA reports 8 devices.
- `activate.local.sh` now activates `chongqing_v1`; `activate.v1.local.sh` is a
  deprecated shim that sources it.

Retirement and clearing:

- Deleted Goal 2.6 code: `src/chongqing_binary/goal2_6/` (8 files), the 8
  `scripts/*goal2_6*.py`, and `tests/test_goal2_6_protocol.py`. Retained
  `configs/goal2_6/`, `results/goal2_6/` and the six `reports/goal2_6_*.md` as
  the historical record.
- Removed the Goal 2.6 config-loader assertions from `tests/test_config.py`.
- Archived four design documents written on superseded premises into
  `reports/archive/` with a superseded banner: `eeg_goal3_design.md`,
  `fnirs_goal4_design.md`, `face_goal5_design.md`, `face_shortcut_audit_plan.md`.
- Hash-based constraints abolished by user decision and written into `AGENTS.md`
  as the `No Hash Constraints` section. `artifacts/goal2_7/release_manifest.json`
  and `scripts/build_goal2_7_release_manifest.py` are retired historical files.

Documentation rewritten for Goal 2.8:

- `AGENTS.md`: new `Environment`, `No Hash Constraints`, `Current Stage`,
  `Goal 2.8`, `Paradigm-Conformance Rules`, rewritten `Task-Semantics Rules` and
  `Face Rules`, and Goal 2.8 entry points. The old tentative Goal 2.8 Gate is
  gone.
- `EXPERIMENT_PROTOCOL.md`: new `Paradigm Conformance`, rewritten EEG and fNIRS
  validity sections that unblock the confirmed semantics, updated Face protocol,
  a `SUPERSEDED` interpretation status, and single-environment reproducibility.
- `PROJECT_SPEC.md`: Goal 2.8 scope, updated engineering structure, and an
  `Evidence and Decision` section that separates what is superseded from the
  site/demographics shortcut finding that still stands.

Verification:

- `PYTHONPATH=src python -m unittest discover -s tests` → `Ran 99 tests ... OK`
  in `chongqing_v1` (down from 109 after removing the 10 Goal 2.6 protocol
  tests).
- Both split files are byte-identical to their committed state; no split was
  regenerated.
- Working-tree changes are limited to the lock file, the Goal 2.6 deletions,
  `tests/test_config.py`, the three governing documents, `PROGRESS.md`, the two
  activation scripts, and the new/archived reports.

Next: WP1, the attachment-sourced paradigm specification and its conformance
checker, then EEG Oddball re-derivation.

## 2026-09-07 - Goal 2.8 WP1/WP2: Paradigm Spec and EEG Re-derivation

Status: WP1 complete; WP2 complete for all three EEG tasks; WP3 reader complete.

Paradigm specification (WP1):

- `configs/goal2_8/paradigm_spec.yaml` records how every experiment was actually
  run, with a `source` on each value naming the dataset attachment it came from:
  event-code meanings, response keys, block structure, marker transport values,
  optode geometry, VFT categories, Doors win/loss amounts, and the Face movie
  order and stimulus durations. It also records two antipatterns that look
  authoritative but are not, and the gaps that are genuinely unrecoverable.
- `src/chongqing_binary/paradigm/` loads it and derives block windows;
  `scripts/check_paradigm_conformance.py` validates it against sampled raw files.
  All 68 checks pass. The first run failed 5 checks, every one of them because
  the specification was stricter than reality; the specification was corrected.
- Feature code takes task structure from here and must not hardcode it.

EEG re-derivation from raw BDF (WP2):

| task | subjects | signal features | note |
|---|---|---|---|
| oddball | 1820 / 1853 | 321 | target, standard, and the difference wave |
| 1back | 1278 / 1413 | 181 | code 18 only; 19 excluded as positional |
| rest | 1003 / 1043 | 63 | continuous windows, spectral path |

The Oddball difference wave over 1820 subjects is a textbook P3b: Pz +6.40 uV in
the 0.28-0.55 s window, parietal maximum, Fz negative at -2.45 uV, positive in
88.1 percent of subjects, Cohen d = 1.08. The Goal 2.7 premise that only code 22
existed is definitively refuted.

Diagnostic signal is nonetheless weak. The Pz P300 difference is +6.56 uV in
healthy against +6.06 uV in non-healthy, Mann-Whitney p = 0.055, univariate
AUROC 0.528. Recovering the correct contrast did not by itself produce a strong
classifier. Whether the multivariate feature set adds an increment over
demographics is for WP5 to decide under the unchanged protocol.

Defects found and fixed while building this:

- Two BDF naming conventions coexist, `<L_id>_data.bdf` and bare `data.bdf`. A
  glob of `*_data.bdf` alone dropped 329 Oddball subjects. Recorded in the
  specification and covered by a test.
- A single peak-to-peak rejection threshold rejected 65 percent of 1BACK epochs,
  because its 2 s epochs have far more opportunity to exceed it than 1 s Oddball
  epochs. Thresholds are now per task, and the blink-dominated Fp1/Fp2 channels
  no longer drive whole-epoch rejection. 1BACK usable subjects rose from 593 to
  1278; the epoch-selection alignment was verified against MNE's own selection.
- The 1BACK section of the specification had no ERP windows or channels, so
  feature extraction emitted a single column. Windows and channels appropriate
  to a visual 2 s epoch were added, giving 181 columns.
- Yiruid channels CH43 and CH49 span 67.1 mm while the other 51 sit at 30 mm.
  Flagged in the specification because their signal-to-noise and effective
  pathlength differ.

fNIRS reader (WP3, partial):

- `src/chongqing_binary/goal2_8/fnirs_io.py` reads `.nirs` in full including the
  `SD` structure, and converts to HbO/HbR by the modified Beer-Lambert law using
  the recorded 690/830 nm wavelengths, optode distances and an age-dependent
  DPF. A round-trip test forward-models known concentrations and recovers them.
- Bikom CSVs keep their `ST`/`A0`/`A1`/`B0`/`B1`/`ED` mark labels rather than
  being collapsed to a 0/1 indicator.

Verification: `Ran 125 tests ... OK`. All three EEG feature tables are CV-only
with zero pilot-holdout rows.

## 2026-09-07 - Goal 2.8 WP3: fNIRS Re-derivation, Five Tasks on Both Devices

Status: complete. Task-response features are unblocked and validated.

Goal 2.7 blocked every fNIRS task-response feature. Three separate defects were
behind that, all now fixed:

- the reader probed `.nirs` headers only, so wavelengths and geometry looked
  unconfirmed. `fnirs_io.py` now reads the file including `SD`, and applies the
  modified Beer-Lambert law with the recorded 690/830 nm wavelengths, per-channel
  source-detector distances and an age-dependent differential pathlength factor;
- the Bikom `Mark` column was collapsed to a 0/1 indicator, discarding the
  `A0`/`A1`/`B0`/`B1` labels that encode block on and off. Labels are preserved
  and block windows come straight from them;
- `_segments()` took the task window as first-marker-to-last-marker, which
  degenerates to a single sample for VFT and swallows all ten rest periods for
  Oddball. Block windows now come from the specification plus recorded markers.

Channel-to-region mapping replaces the old `unconfirmed_channel_global_hemisphere_only`
status: Yiruid channels are assigned to 11 regions from the yrd-53 MNI
projections, Bikom to the provider's four-network partition.

| device | task | subjects | signal features | timing |
|---|---|---|---|---|
| yiruid | rest | 1514 | 38 | event-free |
| yiruid | vft | 1480 | 80 | high |
| yiruid | 1back | 1423 | 80 | high |
| yiruid | oddball | 524 | 80 | high |
| yiruid | doors | 825 | 80 | high |
| bikom | rest | 1017 | 23 | event-free |
| bikom | vft | 1022 | 23 | low, sensitivity only |
| bikom | 1back | 995 | 49 | high |
| bikom | oddball | 508 | 49 | high |
| bikom | doors | 515 | 49 | high |

Physiological validation. Every Yiruid task shows the canonical haemodynamic
response, HbO up and HbR down, with block counts exactly matching the
specification:

- VFT +0.343 / -0.128 uM over 4 blocks, peak at 8.4 s, and left-lateralised,
  which is what a verbal fluency task should produce;
- 1BACK +0.632 / -0.215 uM over 2 blocks;
- Oddball +0.405 / -0.130 uM over 10 blocks;
- Doors +0.055 / -0.068 uM over 6 blocks.

Bikom Oddball is also canonical. Bikom 1BACK and Doors show much smaller and
mixed-sign changes, which is consistent with its vendor-processed units being a
different quantity from MBLL-derived micromolar concentrations; the two devices
stay separate, as the protocol requires.

Defects found and fixed while building this:

- the `age` column carries sentinels such as `[missing]` and out-of-range values
  such as 33 and 36. Age drives the DPF, so it is coerced and clipped to the
  configured 9-20 range with a documented fallback;
- a subset of Bikom CSVs is exported with every line padded by trailing commas,
  so `Sampling Period[s]` parsed as `0.1,,,,,,`. Sixteen subjects were being
  dropped across three tasks; trailing empty fields are now stripped;
- some recordings carry channels that are NaN throughout, and numpy raises on an
  all-NaN slice rather than returning NaN. Bikom Doors crashed outright. All
  reductions now go through a nan-safe guard.

Verification: `Ran 125 tests ... OK`. All ten feature tables are CV-only with
zero pilot-holdout rows, 9823 subject-task rows in total.

## 2026-09-07 - Goal 2.8 WP4: Face Segmentation and the Valence Contrast

Status: complete. The result does not support the hypothesis that motivated it.

`面部2-任务` was segmented into its three emotion-movie phases using
`附件/网页数据.xlsx`, and features were extracted per segment plus as
within-subject valence contrasts.

Alignment. The `template.mp3` and split-point JSON that `run_video_process.py`
expects are not in the dataset, so `start.mp3` from `面部/面部任务.zip` was used
as the landmark. It clears a 0.6 correlation on only 474 of 3382 recordings,
because the microphone captures room playback. Two independent lines of evidence
fix the offset instead: confident detections give a lead-in of 0.63-0.77 s, and
`video_duration - (log_span + 60)` has an interquartile range of only 3 s. Both
say the recording starts under a second before `timevideostart1`. Confident
subjects use their own offset, the rest inherit the cohort median, and frames are
sampled from the middle 80 percent of each segment so a few seconds of error
cannot reach the features. The web log itself is trustworthy: all 3382 subjects'
segment durations match the stimulus durations, with zero mismatches.

Extraction: 3382 subjects indexed with all three movies, 3381 with features,
YuNet detection rate 1.000 across 48 frames per subject. Goal 2.7 had fallen back
to Haar on 99 percent of videos; a fallback is now a recorded QC failure.

The valence contrast has 17.4 percent of the magnitude of a raw segment
embedding, confirming that most of the raw embedding is subject-constant and
cancels within subject.

Result, PCA-64 plus logistic regression under the fixed folds:

| block | standard CV | group CV |
|---|---|---|
| face_negative | 0.6228 | 0.6096 |
| full_negative | 0.6250 | 0.5842 |
| background_negative | 0.6019 | 0.5418 |
| contrast negative-minus-positive | 0.5499 | 0.5345 |
| contrast negative-minus-positive background | 0.4962 | 0.4814 |
| contrast negative-minus-neutral | 0.4964 | not run |

Interpretation. Segmenting the session did **not** unlock a strong emotional
signal. Removing the subject-constant component drops AUROC from about 0.62 to
0.53-0.55, which means most of what the raw Face embedding predicts is appearance
and setting rather than facial dynamics. The Goal 2.7 `SHORTCUT_DOMINATED`
description was substantively right about Face, even though it was reached from
unsegmented video.

What the contrast does establish is a shortcut-free floor. Under group-aware CV
the contrast reaches 0.5345 against 0.4814 for its own background control, a gap
of about 0.053 that cannot be explained by identity, background or acquisition
site, because those cancel within subject. Group-aware CV deflates background by
0.060 and full frame by 0.041 while barely touching the face crop and the
contrast, which is the signature of an acquisition-site shortcut living in the
background rather than in the face.

These are single untuned models without inner-CV selection or confidence
intervals, and all of them sit below the roughly 0.67 that demographics alone
reached in Goal 2.7. The question that matters is whether Face adds anything
*over* demographics, which only the WP5 matrix can answer.

Verification: `Ran 137 tests ... OK`.

## 2026-09-08 - Goal 2.8 WP5/WP6: Model Matrix and Results

Status: measurement complete, results recorded. No go/no-go decision is issued
here; that remains open.

The Goal 2.7 protocol was rerun unmodified over the re-derived features: same
fixed splits, same inner CV, same model families and grids, same 1000-resample
bootstrap and paired tests, same pilot-holdout exclusion. Only the features are
new. Bikom was excluded from the primary matrix.

Matrix: 380 datasets across both protocols, 2200 pooled metric rows, 1,623,018
OOF predictions, 22,000 bootstrap CI rows, 444 paired comparisons.

Paired increments, 240 required comparisons:

| comparison group | rows | significant positive | significant negative |
|---|---|---|---|
| over demographics | 216 | 0 | 78 |
| over background (shortcut control) | 24 | 14 | 1 |

Per modality, increments over demographics: EEG 72 rows, 0 positive, 43
negative; fNIRS 120 rows, 0 positive, 19 negative; Face 24 rows, 0 positive, 16
negative. Face additionally has 14 positive rows against background, the largest
being Random Forest on the valence contrast under group CV at +0.1153, CI
[0.0858, 0.1450].

Signal validity was confirmed independently of the label: the Oddball difference
wave is a textbook P3b (Pz +6.40 uV, parietal maximum, Cohen d = 1.08, positive
in 88.1 percent of 1820 subjects), every Yiruid fNIRS task shows the canonical
haemodynamic response with specification-matching block counts, and YuNet face
detection reached 1.000.

Findings recorded alongside the matrix:

- The two fNIRS devices were used on disjoint cohorts, 1 subject in common, so
  device and acquisition site cannot be separated. Bikom features carry no
  univariate label signal (median AUROC 0.502) despite validated parsing.
- Demographic predictability is the same under all three label definitions
  (0.6697 / 0.6731 / 0.6730 for age+sex+grade), so removing the 744 high-risk
  subjects does not lower the demographic baseline.
- Eye tracking, still unused, matches 666 CV subjects when keyed on `A_id`
  rather than `L_id`, against the 291 recorded in the manifest.

Corrections made during this stage:

- The first decision rule counted any required comparison as evidence, which
  credited Face with independent signal on the strength of 14 wins against
  background. Beating background is a shortcut control, not an increment over
  demographics. The rule now separates the two groups and requires a positive
  demographics increment under both protocols; a test constructs a
  background-only win and asserts it is not credited.
- `configs/goal2_8/models.yaml` inherits Goal 2.7's grids for comparability, and
  inherited six `outputs` keys still pointing at `results/goal2_7/`. Nothing had
  been written through them, but they are redirected and a test now guards it.
- `RandomForestClassifier(n_jobs=-1)` in the shared runner cost about 0.8 s of
  scheduling per fit on this 192-core host, independent of problem size. It is
  now configurable and defaults to 4. Speed only; fitted models are unchanged.
  Weighted HistGradientBoosting is 57 times slower than unweighted in sklearn
  1.9, and the weighting was kept because dropping it would break comparability
  with Goal 2.7.

Verification: `Ran 148 tests ... OK`. All feature tables and OOF predictions are
CV-only with zero pilot-holdout rows. Split files are byte-identical to their
committed state.

Reports: `reports/goal2_8_final_report.md`, `reports/goal2_8_results.md`.
Machine-readable: `results/goal2_8/`, including `required_increments.csv` and
`modality_decision.csv`.

## 2026-09-08 - Goal 2.9: Behavioural Features from the Paradigm Trial Logs

Status: measurement complete, results recorded. No go/no-go decision is issued
here; that remains open.

Every fNIRS task that takes a keypress wrote a trial-level log next to the
recording, and no earlier goal read any of it. Goal 2.9 reads them under the
unchanged Goal 2.7 protocol: same fixed splits, same inner CV, same model
families and grids, same 1000-resample bootstrap and paired tests, same
pilot-holdout exclusion. Only the features are new.

Coverage and usability, measured over every subject directory:

| device | task | dirs | trials | response rate | usable |
|---|---|---|---|---|---|
| yiruid | 1back | 1821/1825 | 30 | 0.93 median | yes |
| yiruid | oddball | 701/701 | 300 | 0.167, the target proportion | yes |
| yiruid | doors | 1089/1089 | 60 | 0.38 | sensitivity only |
| bikom | 1back | 1271/1272 | 30 | 0.93 median | yes, minus 50 |
| bikom | oddball | 644/644 | 250 | 0.01 | no |
| bikom | doors | 644/649 | 60 | 1.00 median | yes |

Feature tables: yiruid 1back 1412 subjects / 38 features, oddball 524 / 25,
doors 843 / 28; bikom 1back 955 / 38, doors 515 / 28; plus one combined cohort
per device, yiruid 342 / 91 and bikom 513 / 66.

Four defects found in the logs, all recorded in the specification:

- Bikom Oddball never collected the keypress. `Slide3.RESP` is empty for 549 of
  640 subjects, the target hit rate is exactly 0.0 for 610, and `Slide3.CRESP`
  is empty even on target trials. The vendor's own reference run logs 0
  responses over 50 trials. The unit is excluded, not coerced.
- Yiruid Doors truncates its response window: `task_resp` runs 0 to 1.0 s while
  the doors are on screen 0.5 to 4.5 s. Response rate 0.383 against 0.983 on
  Bikom, median RT identical at 0.786 vs 0.765 s, RT skew reversed from -0.65 to
  +1.31, 6 usable choice pairs against 24. Bikom is therefore the primary device
  for reward behaviour, the reverse of the fNIRS signal.
- 50 Bikom 1BACK subjects ran a build whose condition list contains no repeated
  stimulus at all, so there is no match/non-match contrast to compute.
- The Bikom block-initial trial carries a meaningless condition (`YN` 1 in 254
  and 2 in 46 of 300 sampled blocks) that E-Prime scores accuracy against. The
  1BACK condition is derived from the stimulus sequence instead; it agrees with
  the logged column on every non-block-initial trial on both devices, and the
  per-subject agreement median is 1.000.

Two corrections to `configs/goal2_8/paradigm_spec.yaml`:

- Doors feedback code `1` is **loss** and `2` is **win**, from the stimulus
  images (`stim/1.png` is a red "-1", `stim/2.png` a green "+2", identical on
  both devices). The earlier revision had `{1: win, 2: loss}` with `+50/-25`
  amounts. No code had read it.
- `脑机接口.pdf` describes a Doors design that was not run (3 blocks of 20,
  mouse clicks, +50/-25). Recorded as an antipattern; the executed design is 6
  blocks of 10 with a keyboard 1/2 choice and +2/-1.

Label-free validity replicates across the two disjoint device cohorts and two
independent log readers. Yiruid vs Bikom 1BACK: accuracy 0.929 / 0.964, d-prime
2.57 / 2.95, criterion +0.25 / +0.19, RT 0.657 / 0.683 s, post-error slowing +98
/ +121 ms and positive in 76.5% / 76.4% of subjects, RT faster in block 2 in
76.5% / 76.5%. Yiruid Oddball: d-prime 4.53, hit rate 0.99, false-alarm rate
0.004, hit RT 370 ms.

Matrix: 294 datasets across both protocols, 1708 pooled metric rows, 622,688 OOF
predictions, 294 paired comparisons.

Result: over the 168 increments **over demographics**, 8 intervals excluded zero
on the positive side and **0 are credited**; 25 were significantly negative.
Behaviour reaches 0.51 to 0.59 AUROC, above chance everywhere but below
demographics in every cohort except one.

A positive result was found and withdrawn. The combined Yiruid cohort returned
`INDEPENDENT_SIGNAL_SUPPORTED` on 6 Standard-CV and 2 Group-CV increments with
point estimates +0.079 to +0.089 and all 24 of its rows positive in sign. Every
one of the eight beat a demographics baseline that was itself **below chance**:
0.472-0.520 under Standard CV and 0.429-0.467 under Group CV, against about 0.67
in the full cohort. That cohort is the intersection of three Yiruid tasks, drawn
from 10 sites instead of 51, with age compressed to 12-20 (sd 1.66) against 9-20
(sd 2.38) and univariate age AUROC down from 0.620 to 0.549. Behaviour's own
AUROC there is 0.585 / 0.534, below the site proxy's 0.669 in the same cohort.
The comparator collapsed; the signal did not rise.

The withdrawal was verified with three independent checks, all reproducible via
`python scripts/verify_goal2_9_positive.py` and recorded in
`results/goal2_9/positive_result_verification.json`:

- **Transfer.** The same 342 subjects scored by models trained on the larger
  per-task cohorts show demographics 0.507-0.550 and behaviour 0.462-0.545, with
  no gap. Only models trained inside the 342 produce one (0.484 vs 0.573). The
  effect belongs to the fitting, not to the subjects; the subgroup is not
  inherently demographics-proof.
- **Pooling.** The zero-information model scores exactly 0.500 in every fold of
  this cohort but 0.404 pooled under Standard CV and 0.347 under Group CV, whose
  folds hold 74/169/37/55/7 subjects at prevalences 0.19 to 0.56. Pooling across
  folds that unbalanced pushes uninformative predictors below chance
  mechanically.
- **Permutation.** Shuffling the diagnoses on the exact cohort, features and
  folds, 100 times: demographics falls below chance in 58 to 67 percent of runs,
  the behaviour-minus-demographics gap averages +0.014 to +0.019 with sd 0.067,
  and it reaches the observed +0.079 in **17 to 18 percent** of runs. The
  reported increment sits about 1.2 sd above the null mean.

Behaviour's own bootstrap AUROC interval in this cohort includes 0.5 in 5 of 6
model-by-protocol combinations.

Why the paired test missed it: the bootstrap resamples subjects, not folds, so
it measures subject sampling noise and is blind to the instability of the fit
itself. In a cohort this small the demographics fit is unstable enough to land
below chance, and a below-chance comparator manufactures a positive difference
that the interval then certifies. Fold-direction consistency does not help,
because the same unstable fit is unstable in the same direction in every fold —
all eight rows passed the 4/5-fold requirement.

The decision rule now requires a credited increment to beat a comparator that is
itself above chance. `results/goal2_9/required_increments.csv` carries
`comparator_auroc`, `comparator_above_chance` and
`significant_positive_credited`, and a test constructs a comparator-at-chance
win and asserts it is not credited. `EXPERIMENT_PROTOCOL.md` additionally
requires label-permutation verification for any credited increment from a cohort
under about 500 subjects. This is the second decision-rule hole this project has
closed after finding it in a live result; Goal 2.8's first rule credited Face
for beating a background control.

Control rows behave as they should: `signal_qc vs qc` positive in 11 of 42 rows
and `signal_demographics vs signal` in 19 of 42. Adding demographics to
behaviour helps; adding behaviour to demographics does not.

Behaviour correlates with age in the expected direction, Spearman rho -0.22 for
RT dispersion, -0.18 for RT means and +0.18 for Oddball d-prime, which is the
developmental effect age already captures.

Verification: `Ran 182 tests ... OK`. All feature tables and OOF predictions are
CV-only with zero pilot-holdout rows. Split files are byte-identical to their
committed state.

Reports: `reports/goal2_9_final_report.md`, `reports/goal2_9_results.md`.
Machine-readable: `results/goal2_9/`, including `required_increments.csv` and
`unit_decision.csv`.

## 2026-09-08 - Demographics Baseline Re-verified

Status: verification only, no new modelling decisions.

The demographics baseline was recomputed independently of every result table,
rebuilding the cohort from the split file and rerunning the project's own
pipeline and grids. `scripts/verify_demographics_baseline.py` reproduces it and
writes `results/demographics_reference/`.

On the full 3597-subject development cohort, age + sex + grade:

| protocol | logistic regression | random forest | hist gradient boosting |
|---|---|---|---|
| standard_cv | 0.6688 | 0.6708 | 0.6689 |
| group_cv | 0.6596 | 0.6551 | 0.6430 |

Per-fold values run 0.61 to 0.73 with no fold below 0.60, so the figure is
stable. Decomposition: age alone 0.57-0.62, sex alone 0.54-0.59, grade alone
0.60-0.63, age+sex 0.63-0.67. The site proxy alone reaches 0.67 under Standard
CV and exactly 0.500 in every fold under Group CV, which is Group CV working as
designed because it holds out whole sites. Demographics plus site proxy reaches
0.706 / 0.666. Input quality is not a limitation: 99.92 percent of ages parse
inside 9-20, sex has one missing value, grade has nine real levels.

Two things this corrected.

**A conflated column in the Goal 2.8 final report.** Its best-row table listed
the `demographics` figure as 0.6470 for EEG and 0.6943 for fNIRS. Those rows are
`demographics_group_device` and `demographics_group`, which include the
acquisition-site proxy. Pure age+sex+grade reaches 0.6074 and 0.5960 in those
cohorts. The Face figure, 0.6721, was already pure demographics. The table now
carries the two as separate columns and the report states the correction.

**The absence of a reference baseline.** Every demographics number in every
result table is measured inside a modality cohort, because that is what the
paired comparison needs. No run had ever measured demographics on the full
development cohort, so 0.55 in a 524-subject fNIRS cohort and 0.67 in a
3381-subject Face cohort had nothing to be read against. They differ because the
modality cohorts are restricted samples, not because anything is wrong.

Why adding a modality to demographics often lowers it. Over the 90 comparable
rows in Goal 2.8 and Goal 2.9, adding demographics to a modality helps in 85.6
percent of rows, while adding a modality to demographics hurts in 65.6 percent,
by a mean of -0.03 to +0.005 and at worst -0.077. The size of the drop tracks how
uninformative the added features are (correlation 0.64 with the modality's own
AUROC): when the modality is at or below chance the mean drop is -0.045, and when
it reaches 0.55-0.60 the combination gains +0.015. It is worst for random forest,
which samples sqrt(p) features per split and so rarely sees the three demographic
columns among 324.

This is dilution, not a defect, and the pipeline has no mechanism to avoid it:
impute, scale, fit over the whole feature block, with inner CV selecting
hyperparameters and never features. Bolting columns of pure random noise onto
demographics on the full cohort costs -0.008 to -0.055 depending on count and
model, which brackets the observed drops. Feature counts were checked and are
exact: `signal_demographics` always equals the signal block plus one numeric and
two categorical columns.

`EXPERIMENT_PROTOCOL.md` now records that a negative increment means absence of
signal, not damage, and that a cohort-internal demographics figure must be quoted
with its cohort.

## 2026-09-08 - Goal 2.10 Step 1: Eye-Tracking Readiness Audit

Status: readiness complete. No features, no models, no labels in any check. No
go/no-go decision is issued here.

Eye tracking is the last unused objective modality. Before any of it was
modelled, the literature it would rest on was reviewed and a method was written
down with its predictions, in `reports/goal2_10_eye_method_design.md`. This
entry records the audit that followed.

### Coverage: the manifest undercounts eye by a factor of four

`has_eye_direct` records 281 subjects in the split file because
`chongqing_binary.audit._extract_l_ids` greps paths for `L\d+`, and no eye path
carries one; they carry `A_id` (`A02062_<name>_251105161924`,
`眼动-tobbi E16284<name>_free.xlsx`). Joining on `A_id`:

| device | sampling rate | subjects | CV subjects |
|---|---|---|---|
| `qixin_120` (七鑫易维) | 120 Hz | 432 | 336 |
| `qixin_500` (七鑫易维 F500) | 500 Hz | 420 | 331 |
| `tobii` (Tobii Pro Nano) | 60 Hz | 337 | 253 |
| union | | 1187 | **919** |

3621 recordings on disk, 3481 kept, all 3481 read. 911 subjects have a recording
that `has_eye_direct` does not flag; 5 are flagged with no recording found.
Within the CV cohort about 80 percent also have EEG, 95 percent fNIRS and 99
percent Face. Positive rate is 0.334 to 0.360 across the nine units.

Only 2 subjects appear under more than one device, and each device owns a
distinct set of `A_id` site prefixes: `qixin_120` holds B14/B15/B16/C02/C17/C18/
D08 alone, `qixin_500` holds A04/A10/B01/B03/B05/D13/E06 alone, and Tobii shares
qixin_500's schools but never its subjects. Device and acquisition site cannot be
separated, exactly as for the two fNIRS devices, so units are `device x task`
and raw features are never merged across devices.

### The paradigm was recovered without an attachment

`附件/` holds paradigm scripts for EEG, fNIRS and Face and nothing for eye
tracking. `configs/goal2_10/eye_paradigm_spec.yaml` is therefore the project's
first specification that is not attachment-derived, and it says so:
`attachment_available: false`, with every value naming whether it came from the
archived stimulus media or from the recorded presentation timeline. The two
sources agree.

- **自由观看**: 36 trials of cross 1.0 s, single CFAPS-style greyscale face
  4.0 s, blank 1.0 s. Valence and sex fully crossed: 12 happy, 12 sad, 12
  neutral, 18 male, 18 female. Presentation order is fixed and identical for
  every subject, so trial index and valence are confounded by design. One face
  is on screen at a time, so this yields a between-trial valence contrast, not
  the competitive attentional-bias score most of the free-viewing literature
  reports.
- **扫视**: prosaccade instruction, 10 s practice, 20 s formal; then the same
  for antisaccade. Each formal block holds exactly **8 trials**, first onset
  1500 ms, period 2500 ms, target on 1000 ms, four leftward and four rightward,
  four small (0.140 of screen width) and four large (0.282).
- **平滑追随**: instruction then a 135.99 s continuous target sweeping 229
  distinct horizontal positions.

Stimulus onsets are not in the per-subject 七鑫易维 export; every
`*_annotation.csv` there is header-only. They come from the project `.asdata`
file. Target positions exist nowhere in the recorded data and were decoded from
the stimulus videos, which are byte-identical across both 七鑫易维 projects and
were the same files Tobii presented.

Conformance over all 3481 recordings: timeline complete in 1.000 of units except
`qixin_500/free_viewing` at 0.995 and `qixin_500/smooth_pursuit` at 0.998. Face
presentation error against the specified 4000 ms is 2 ms on both 七鑫易维
devices and -19.5 ms on Tobii, which is one 60 Hz sample interval.

### Two timing defects that would have corrupted every trial-locked feature

- Tobii `Recording timestamp` is in **microseconds** while `Recording duration`
  is in milliseconds. The reader converts and stores the agreement, which is
  1.0000.
- The 七鑫易维 sample clock is not the presentation clock. On F500 the samples
  span about 0.4 percent longer than the `duration` the project file reports,
  which accumulates to 300-400 ms by the end of a 136 s block. Measured clock
  scale is 0.99674 [0.99588, 0.99734] on F500 against 0.99999 [0.99992, 1.00008]
  at 120 Hz. Uncorrected, the pursuit gaze-target correlation reads 0.64 to 0.72;
  after mapping the samples onto the presentation clock it reads 0.935 [0.913,
  0.953], and the residual best lag falls to +100 to +150 ms, which is the
  ordinary physiological pursuit lag. `chongqing_binary.eye.qixin.aligned_time_ms`
  applies it and a test pins it.

Neither defect announces itself. Both would have silently rescaled or shifted
every trial-locked feature on a third of the cohort.

### Label-free validity passes on all nine units

Every threshold is fixed by the paradigm or by physiology, so a failure would
mean a parsing problem rather than an absent effect. Median [Q1, Q3] over all
recordings:

| check | tobii | qixin_120 | qixin_500 |
|---|---|---|---|
| free-viewing dwell inside the face box | 0.981 [0.953, 0.993] | 0.963 [0.924, 0.984] | 0.972 [0.929, 0.990] |
| the same, over the box's 0.053 area share | 18.6x | 18.3x | 18.4x |
| prosaccade gaze-target correlation | 0.822 | 0.771 | 0.756 |
| antisaccade gaze-target correlation | -0.614 | -0.552 | -0.531 |
| pursuit gaze-target correlation | 0.971 [0.940, 0.987] | 0.942 [0.917, 0.965] | 0.935 [0.913, 0.953] |
| trials scored per saccade block | 8 | 8 | 8 |

The antisaccade correlation is negative on all three devices, which validates
the block identification and the pro/anti semantics at the same time. All 9
`device x task` units are marked READY.

### Acquisition quality differs by device

| device | valid sample fraction | long gaps | recordings below 0.5 valid |
|---|---|---|---|
| `qixin_120` | 0.980 [0.957, 0.994] | 1 [0, 4] | 1 |
| `qixin_500` | 0.975 [0.952, 0.988] | 1 [0, 3] | 0 |
| `tobii` | 0.897 [0.857, 0.926] | 5 [3, 9] | 9 |

Tobii resolves less of the recording and loses tracking more often. Since device
is collinear with site, this is a shortcut candidate, and QC therefore enters as
its own feature set so the `signal_qc vs qc` control can expose it.

### Defects recorded, not coerced

113 duplicate takes were resolved deterministically, never averaged: complete
timeline first, then most media segments, then longest recording, then latest,
every component from the recording and none from the label. 27 recordings carry
no `A_id` (`User1_251028130305`, `<name>_251022130431`, `C17049-<name>`,
`B16072--_<name>`, Tobii `Recording8.xlsx`) and are excluded; name-based mapping
is not permitted, since that is what made `has_eye_name_mapped` unreliable.

### One prediction is already weaker than it was written

The design document predicted that antisaccade error rate would carry a moderate
univariate signal that the age baseline would then absorb. The audit adds a
second reason to expect little from it: each block holds only **8 trials**, so a
direction-error rate has a resolution of 0.125 and cannot be compared with the
40-100 trial batteries the literature reports. Its split-half reliability must
be reported with it.

Verification: `Ran 199 tests ... OK` (182 before this stage, 17 new). No label
column was read by any check in this audit.

Entry point: `python scripts/audit_eye_readiness.py --n-workers 48`.
Report: `reports/eye_readiness_audit.md`. Machine-readable:
`artifacts/goal2_10/readiness/`, plus stimulus-side products in
`artifacts/goal2_10/stimuli/`.

## 2026-09-09 - Goal 2.10 Steps 2-3: Stimulus Regions and Gaze Drift Correction

Status: stimulus-side products complete. Still readiness only, no features, no
models, no labels in any check.

### Regions

The free-viewing regions are built from YuNet's five landmarks on the 36
stimulus images and scaled by each stimulus's inter-ocular distance, giving
`eyes`, `mouth`, `face_other` and `off_face`. A gaze sample falls in exactly one
region, first match wins, so the four shares sum to one. Because the regions
depend only on the stimulus images, the same geometry applies to every subject
in every fold and cannot leak.

YuNet detects all 36 stimuli, lowest score 0.907, so no Haar fallback arises;
here that fallback would be an error rather than a downgrade, because it would
change the region geometry for one stimulus only. Eye and mouth bands are
disjoint on all 36 and both lie inside the visible face. Median screen-area
share: eyes 0.0150, mouth 0.0106, face 0.0529.

The multipliers live in `configs/goal2_10/eye_paradigm_spec.yaml` under
`tasks.free_viewing.aoi` and carry `source: analysis_choice`, which distinguishes
them from the recovered paradigm facts in the same file.

### A device-level gaze offset that the coarse check could not see

Adding the regions immediately failed a check that no earlier one could reach.
Eye-region dwell exceeds mouth-region dwell in every population studied, so it is
a parse check rather than a finding. Measured raw, over all 1140 free-viewing
recordings:

| device | eyes | mouth | eyes minus mouth |
|---|---|---|---|
| `tobii` | - | - | +0.245 [-0.027, 0.481] |
| `qixin_120` | - | - | **-0.103** [-0.341, 0.153] |
| `qixin_500` | - | - | **-0.145** [-0.324, 0.090] |

The contrast reverses on both 七鑫易维 devices. The cause is a systematic
downward gaze offset that differs by device: median vertical offset, measured
against the paradigm's own fixation cross, is +0.015 of screen height on Tobii,
+0.056 at 120 Hz and +0.052 on F500. The eye and mouth bands are each about 0.10
of screen height, so an offset that size moves a large share of samples from one
band into the other.

Two things make this worth recording rather than quietly fixing.

First, **the Step 1 face-box check passes with the offset in place**. Dwell
inside the stimulus face box was 18x its area share on every device. The face box
spans y 0.335 to 0.665, symmetric about screen centre, so a vertical shift keeps
gaze inside it. Only a region finer than the face caught this. A coarse validity
check that passes is not evidence that the coordinate frame is right.

Second, **device is collinear with acquisition site in this dataset**. An
uncorrected 0.04 difference in reported gaze position between devices would have
entered any eye-region model as a site shortcut wearing the clothes of a
behavioural finding. This is the same failure mode as the site proxy that Goal
2.7 found, arriving through a new door.

### The correction, and what it does

The paradigm supplies its own: a 1 s fixation cross at screen centre precedes
every trial. `chongqing_binary.eye.drift.estimate_drift` takes the median gaze
over a recording's crosses, minus (0.5, 0.5), skipping the first 200 ms of each
cross and requiring at least 10 usable crosses. Recordings have 36 or 37. It uses
no label, and a recording-level median rather than the immediately preceding
cross, so trial-level variance stays in the signal instead of being absorbed by
the correction.

After it, over all 1140 recordings:

| device | eyes | mouth | face_other | off_face | eyes minus mouth |
|---|---|---|---|---|---|
| `tobii` | 0.539 | 0.172 | 0.242 | 0.020 | +0.362 [0.230, 0.526] |
| `qixin_120` | 0.524 | 0.180 | 0.243 | 0.029 | +0.339 [0.184, 0.474] |
| `qixin_500` | 0.481 | 0.208 | 0.260 | 0.018 | +0.269 [0.159, 0.405] |

The between-device spread in eyes-minus-mouth falls from 0.390 to 0.093, and the
contrast is positive and large on all three devices, which is what face viewing
does. The estimated offset is an acquisition property and enters the **QC**
feature set only; it must never enter the signal feature set.

A residual device difference remains, 0.481 to 0.539 in eye share. It is small
against the raw spread but it is not zero, so device stays a modelling unit and
raw features are still never merged across devices.

Verification: all 9 `device x task` units remain READY over all 3481 recordings,
with `eyes_above_mouth` added to the verdict. `Ran 205 tests ... OK` (23 in the
eye suite, 6 of them new). No label column was read by any check.

Report: `reports/eye_readiness_audit.md`. Machine-readable:
`artifacts/goal2_10/readiness/` and `artifacts/goal2_10/stimuli/`, the latter now
including `free_viewing_aois.json`.

## 2026-09-09 - Goal 2.10: Eye Tracking, the Fifth Feature Layer

Status: measurement complete, results recorded. No go/no-go decision is issued
here; that remains open.

Eye tracking is the last objective modality no earlier goal used. The protocol
is unchanged from Goal 2.7, 2.8 and 2.9: same fixed splits, same inner CV, same
model families and grids, same 1000-resample bootstrap and paired tests, same
pilot-holdout exclusion, same Goal 2.9 rule that a credited increment must beat
a comparator that is itself above chance. Only the features are new.

The literature was reviewed and the method, with its predictions, was written
down before anything was modelled, in `reports/goal2_10_eye_method_design.md`.

### Result

**Over the 576 increments over demographics, 0 are credited.** Eighteen
intervals excluded zero on the positive side; 152 were significantly negative.
All twelve `device x task` units return `NO_INDEPENDENT_SIGNAL`. Matrix: 600
datasets, 518,592 OOF predictions, 3504 pooled metric rows, 864 paired
comparisons.

Every one of the eighteen positives is Group CV, every one is a `qixin_120`
cohort, and every comparator sits at 0.435 to 0.467. That device's demographics
baseline is 0.555-0.563 under Standard CV and collapses to 0.435-0.462 under
Group CV, while `qixin_500` holds 0.657-0.678 and 0.643-0.659. This is the
mechanism Goal 2.9 had to withdraw a result over, and the rule caught all
eighteen. Without it, `qixin_120` would have been reported as showing
independent eye signal in three of four cohorts.

### Coverage, and a manifest column that undercounts by a factor of four

`has_eye_direct` records 281 subjects because
`chongqing_binary.audit._extract_l_ids` greps paths for `L\d+` and no eye path
carries one; they carry `A_id`. Joining on `A_id`: 1187 subjects, **919 in the
development split**, 3481 recordings, across three devices on near-disjoint
cohorts (Tobii 60 Hz / 253 CV, 七鑫易维 120 Hz / 336, F500 500 Hz / 331; two
subjects in common). Each device owns a distinct set of site prefixes, so
device and site cannot be separated and units are `device x task`.

### The paradigm, recovered without an attachment

`附件/` holds nothing for eye tracking, so
`configs/goal2_10/eye_paradigm_spec.yaml` is this project's first specification
that is not attachment-derived and declares itself as such. Recovered from the
stimulus media and the recorded timeline, which agree:

- 自由观看: 36 trials of cross 1.0 s, one CFAPS-style face 4.0 s, blank 1.0 s;
  12 happy / 12 sad / 12 neutral, 18 male / 18 female, fixed order.
- 扫视: pro and anti, 10 s practice and 20 s formal each, **8 trials** per
  formal block, first onset 1500 ms, period 2500 ms, target on 1000 ms.
- 平滑追随: six 21 s sinusoidal blocks with 2 s gaps, three conditions twice:
  horizontal 0.381 Hz, 3:4 Lissajous 0.143/0.190 Hz, and the same Lissajous at
  exactly double the frequency and identical amplitude. An earlier revision of
  the specification called this task continuous; nothing had read it.

### Four defects, none of which announced itself

- Tobii `Recording timestamp` is microseconds; `Recording duration` is ms.
- The 七鑫易维 sample clock is not the presentation clock. F500 samples span
  about 0.4 percent longer than the recorded `duration`, a 300-400 ms drift by
  the end of a 136 s block. Uncorrected the pursuit correlation reads 0.64-0.72;
  corrected, 0.935, with a residual lag of the ordinary physiological 100-150 ms.
- All three trackers report gaze below the true fixation point, by
  device-dependent amounts (+0.015, +0.056, +0.052 of screen height). The eye
  and mouth bands are each about 0.10 of screen height, so uncorrected the
  eye-minus-mouth contrast reads -0.103 and -0.145 on the two 七鑫易维 devices
  against +0.245 on Tobii: the universal eyes-above-mouth rule reverses. Since
  device is collinear with site that is a site shortcut. The paradigm's own 1 s
  fixation cross corrects it: +0.362 / +0.339 / +0.269, between-device spread
  down from 0.390 to 0.093.
- Catch-up saccades cannot be counted with a dispersion detector. During pursuit
  the eye moves smoothly, so I-DT chops that motion at its threshold and the
  rate tracks eye speed; that version reported the highest rate in the slowest
  condition, which is how it was found. A velocity-residual detector gives 1.23,
  1.26 and 1.84 Hz across horizontal, slow and fast.

The third is the one to carry forward. The face-box check passed with the offset
in place, at 18x its area share on every device, because the face box is
symmetric about screen centre. **A coarse validity check that passes is not
evidence that the coordinate frame is right.**

### Label-free validity passes on all three devices

Medians over all recordings: face-box dwell 18.3-18.6x its area share;
eye-minus-mouth +0.269 to +0.362; prosaccade gaze-target correlation 0.756-0.822
and antisaccade -0.531 to -0.614; pursuit 0.935-0.971; prosaccade gain
1.007-1.019; antisaccade corrected-error rate 1.000.

Three replicate as textbook effects. The **inhibition cost** is +100 / +107 /
+86 ms across devices while absolute latency differs by 84 ms between them, so
absolute latency is not comparable across devices and the within-subject
contrast is. **Mouth dwell is highest for happy faces** on all three devices
(0.231 / 0.242 / 0.262 against 0.121 / 0.124 / 0.144 neutral), which is the
smile being the diagnostic feature and validates the whole valence-to-region
chain. **Pursuit degrades with target speed** on every measure: `fast minus
slow` RMSE +0.014 positive in 83 percent of subjects, smooth fraction -0.055,
catch-up rate +0.53 Hz positive in 92 percent.

### The measurement result that decides how to read the null

Odd-even split half, Spearman-Brown corrected, 249-322 subjects per device:

| block | features | median | above 0.5 on all three devices |
|---|---|---|---|
| absolute per-valence | 75 | 0.698 | **53** |
| valence contrasts | 46 | -0.051 | **0** |

Best contrast 0.326; 33 of 46 have a negative median. Each contrast is a
difference of two means estimated from 12 trials each, which keeps both errors
and cancels the shared true variance. This is the difference-score reliability
collapse the attentional-bias literature reports, replicated here on three
devices independently.

The two blocks therefore entered the matrix as separate declared feature sets,
because mixing 46 unreliable columns into 75 informative ones would depress the
result for a reason unrelated to signal. And **a null on the contrast block is
evidence about this paradigm, not about attentional bias as a construct**: the
valence contrast was the primary theoretical motivation for the whole
free-viewing analysis and it is not measurable at 12 trials per valence. The
absolute block, which is measurable, also returns 0 credited increments.

### Controls behave as controls

`signal_qc vs qc` is positive in 6 of 72 rows and negative in 8, median +0.005;
the signal block's median AUROC of 0.510 is indistinguishable from QC's 0.508.
`signal_demographics vs signal` is positive in 21 of 72, median +0.025. Adding
eye features to demographics lowers AUROC in 74 percent of rows, median -0.039,
which is the dilution already documented. The site proxy alone reaches 0.589
under Standard CV and 0.420 under Group CV.

### A reporting conflation caught before publication

The first summary counted credited increments over the whole required table,
which mixed the demographic increments with the controls and reported "1
credited". The single credited row was
`signal_absolute_demographics vs signal_contrast_demographics`, a control that
says the reliable block beats the unreliable one, which is a restatement of the
reliability finding rather than evidence of signal. The two counts are now
separated, as they should have been: 0 of 576 over demographics, 1 of 72 on
controls. Goal 2.8's report had to correct the same class of conflation between
`demographics` and `demographics_group`.

### What this adds

Eye tracking is the fifth feature layer to return no increment, after EEG,
fNIRS, Face and behaviour. Three things separate this null.

It is the first where the **primary construct was shown to be unmeasurable
rather than merely unrewarding**. It is the first with **three independent
devices** at three sampling rates on three near-disjoint cohorts, whose validity
checks agree and whose label increments agree in returning nothing. And the
decision rule earned its keep for the second time.

Verification: `Ran 237 tests ... OK` (182 before Goal 2.10, 55 new). All feature
tables and OOF predictions are CV-only with zero pilot-holdout rows. Split files
are unchanged.

Reports: `reports/goal2_10_final_report.md`, `reports/goal2_10_results.md`,
`reports/eye_readiness_audit.md`. Machine-readable: `results/goal2_10/`.

## 2026-09-09 - Goal 2.10 re-audit against the hospital paradigm document

Status: complete. Goal 2.10 conclusion unchanged.

The hospital supplied `附件/重医眼动范式及参数.docx` after Goal 2.10 had been
extracted, modelled and reported. It is the first external check on a
specification this project had recovered entirely from recorded data.

Confirmed, with nothing revised to make it agree:

- Free viewing: cross 1 s, face 4 s, blank 1 s, single centred face, 12 neutral
  / 12 happy / 12 sad, sex balanced. 呈现单张 confirms as fact what the spec had
  argued as a judgement call — no competing stimulus, so no within-trial
  attentional-bias score exists in this paradigm.
- Saccade: cross 1.5 s, target 1 s, horizontal at 6 deg or 12 deg, each of four
  positions twice, 8 trials. The decoded video is 1200 frames at 60 fps =
  8 x (1.5 + 1.0) s exactly.
- Pursuit: three trajectories, each 20 s, each repeated twice, fast Lissajous at
  exactly twice the frequency of slow. This confirms the recovered blocked
  structure and the whole `fast minus slow` contrast.
- Both quantities that had been corrected mid-analysis after producing
  implausible results — the 8 saccade trials and the blocked pursuit design —
  are confirmed by a document written independently of the analysis.
- The stimulus set is named outright as CFAPS, where the spec could only infer
  "CFAPS-style" from filename codes.
- The document's cited source paper for free viewing scores dwell on eye versus
  mouth regions, the same contrast the AOI block was independently built to
  measure.

Corrected:

- Pursuit frequencies were quoted 4.8 percent low in spec_version 1 (0.381 /
  0.143,0.190 / 0.286,0.381 Hz). They came from an FFT over the whole 21 s
  block, which opens with 1.0 s of stationary target. Each is an exact integer
  cycle count over the block (8, 3, 4, 6, 8); dividing by the document's 20 s of
  motion returns the document's own 0.4 / 0.2 / 0.4 Hz. Timing reconciles as
  6 x 21 + 5 x 2 = 136 s observed, the 21 s block being 1 s settle plus 20 s
  motion. No feature was affected: `_pursuit_block` reads only `blocks` from
  that mapping and takes the target from the decoded track.
- Every statement in the project that a visual angle could not be computed
  because viewing distance was unrecorded. It can now. The document's 6 deg and
  12 deg targets against the decoded 0.1396 and 0.2823 screen widths solve to a
  viewing distance of 1.3282 and 1.3281 screen widths respectively — agreement
  to four significant figures, and only under a tangent mapping (a linear scale
  misses at 5.967 and 12.067 deg). Screen subtends 41.26 x 23.91 deg. This
  confirms the I-DT threshold of 0.025 screen widths as 1.078 deg horizontally,
  the value it had been chosen to approximate under an explicitly nominal
  geometry.

Exposed, and previously unfixable rather than overlooked:

- `known_defects/axis_anisotropy`. x is normalised by screen width and y by
  screen height, aspect 0.5625, and no code rescales them, so every two-axis
  `hypot` adds different units and the same I-DT threshold is 1.078 deg
  horizontally but 0.607 deg vertically. Affects `scanpath`, `bcea`, the 2-D
  pursuit `rmse` and `_catch_up`. Does not affect any AOI quantity (built in
  pixels, tested per axis), the drift correction (per-axis median), or the
  single-axis gains and `_velocity_gain`. Every recording used the same
  1920x1080 stimulus, so the distortion is identical for every subject on every
  device: it distorts a metric without confounding one, and cannot have
  produced the null. Not yet fixed; fixing it requires re-extraction.

Scope finding:

- The document contains a second table describing a gaze-contingent battery
  (800 ms held fixation gate, 8 deg targets in four directions, plus
  记忆引导扫视 and 双步扫视) that is NOT this dataset. It belongs to 集思鸣智,
  whose heading follows it and whose section is empty. Settled by four
  independent facts: it contradicts table 1 on the same task names; gaze-
  contingent gating is impossible with fixed-length MP4 stimuli; no
  memory-guided or double-step stimulus, directory or timeline exists in either
  七鑫易维 project or the Tobii export; and there is no 集思鸣智 directory under
  `眼动/` at all.
- **A third eye-tracking device is named in the study protocol and none of its
  recordings are in this dataset.** Worth asking the hospital whether that
  cohort exists and was meant to be delivered. Coverage question, not a
  re-analysis question: its paradigm could not be pooled with these three.

Changed:

- `configs/goal2_10/eye_paradigm_spec.yaml` to spec_version 2: provenance
  header, `document_scope`, `viewing_geometry`, corrected pursuit frequencies
  with cycle counts, documented saccade and free-viewing facts, and the new
  defect entry.
- `src/chongqing_binary/eye/events.py`, `src/chongqing_binary/eye/spec.py`,
  `scripts/audit_eye_readiness.py`, `AGENTS.md`, `EXPERIMENT_PROTOCOL.md`,
  `reports/goal2_10_final_report.md` for the superseded claims.
- `tests/test_goal2_10_eye.py`: the guard that pinned
  `attachment_available == False` was rewritten rather than removed, since the
  risk it protected against has moved — a reader mistaking the document's
  second table for these recordings. Two tests added, asserting that the
  viewing geometry closes against the decoded amplitudes under a tangent
  mapping and that every pursuit frequency is a whole cycle count of the motion
  window.

New: `reports/goal2_10_paradigm_document_review.md`.

Result: **unchanged. 0 of 576 increments over demographics credited, all twelve
device x task units NO_INDEPENDENT_SIGNAL.** No re-extraction is needed to
defend it. A re-extraction with the anisotropy fixed and features reported in
degrees would improve an external write-up and is not needed to check the
answer.

## 2026-09-10 - Goal 3: EEG Oddball deep representation benchmark

Status: complete. **0 of 26 decision rows credit independent signal.**

Goal 3 is the first stage in this project to train a neural network. It exists
because Goal 2.8 measured 321 hand-crafted features and found no increment over
demographics, which is a result about features rather than about the recording:
the correctly recovered Oddball had never been given a deep model under a
protocol this project would accept. The old v1 EEGNet and InceptionTime runs at
0.50-0.53 read a cache built with a hardcoded `event_codes: ["22"]`, so the
standard condition was absent entirely, and used a different split and stopping
rule. They are historical reference and were not compared against.

The user issued `CONDITIONAL_GO_FOR_GOAL3_EEG_REPRESENTATION_BENCHMARK` on
2026-09-09, opening EEG Oddball alone. Every other gate stayed closed.

### The design was fixed before anything was trained

`reports/goal3_method_design.md` records the representations, the architectures,
the closed exploratory family, the decision rule and seven numbered predictions,
written before the first model. Six of the seven held; the one that missed is
recorded with its reasoning error.

Two design points came from the user and corrected the first draft.

The first was a real leak. The obvious two-level design monitors early stopping
on the same inner-val fold that produces the inner-OOF prediction, so that
prediction is read at an epoch chosen to be good on exactly those subjects, and
the meta model then learns its weight on an inflated column while meeting an
honest one at outer-validation time. The fix is a third split level: inside each
inner-fit pool a 20 percent **stopping subset** makes every training decision,
and inner-val makes none. It costs each inner model about 14 percent of its
training subjects.

The second was that the first draft barred every non-primary configuration from
ever producing a finding, which is a design that can confirm but never discover.
Replaced with a confirmatory arm of one declared test and an exploratory arm
that is enumerated, closed, FDR-controlled, and returns
`EXPLORATORY_SIGNAL_REQUIRES_REPLICATION` rather than a go.

### The measurement gate

Goal 2.8 kept only the condition averages, so the trials had to be rebuilt from
raw BDF under `configs/goal2_8/eeg.yaml` unchanged. The gate is numerical
identity, not a qualitative check: averaging the new cache by condition
reproduces `oddball_erp.npz` over **1820 of 1820** subjects with a worst relative
difference of **1.10 float32 epsilons** and zero mismatches. Pz P3b recomputed
from the trials is +6.426 uV, d = 1.079, 88.7 percent positive, parietal
maximum, Fz -2.483 uV.

### Result

84 jobs, 1260 trained models, 1,019,200 subject-level OOF predictions.

Confirmatory increment `p_Demo + p_EEG` against `p_Demo`: **+0.0016
[-0.0059, +0.0084]** under Standard CV and **-0.0031 [-0.0150, +0.0094]** under
Group CV, both comparators above chance. Exploratory family: **0 of 24**
intervals exclude zero, 0 survive Benjamini-Hochberg. The amplitude ablation
changes nothing. EEG alone spans 0.4825 to 0.5580 with 16 of 28 rows above
chance, against demographics at 0.5909 and 0.6023 in the same 1820 subjects.

### What makes this null different from the five before it

The positive controls. Same architecture, same pooling, same subjects, same
folds, different target: **age 0.8209 / 0.8029, sex 0.7734 / 0.7672**,
trial-level target-versus-standard **0.8243 / 0.8229** on held-out subjects,
against the disease label at 0.55. Subject-level aggregation is demonstrably not
the weak link, so the null is about the label rather than about the pipeline.
Goal 2.10 established that a null on an unmeasurable quantity is evidence about
the instrument; this is the converse.

PC1 was a hard gate at 0.70 and all ten folds cleared it. PC2 and PC3 were
deliberately not gates — gating on them would have staked the stage on a
literature prior about how decodable sex is from a 1 s ERP epoch.

### The near-miss that the rule caught

Under Group CV, 7 of 14 configurations beat `eeg_traditional` with intervals
excluding zero, up to +0.0647. Every one is a win over a comparator sitting at
**0.4933, below chance**. Under Standard CV, where the traditional block is
above chance, 0 of 14 intervals exclude zero.

The Goal 2.9 above-chance comparator rule was written for demographics
comparators. Goal 3 extended it to every comparison, from the structure of the
comparison and before these numbers existed. Without that extension this report
would have claimed a deep-versus-traditional win, which would have been the
project's third instance of the same error after Goal 2.9 withdrew eight rows
and Goal 2.10 withdrew eighteen.

### Two findings that should change how future stages are run

**Cross-fitted stacking removes the dilution artefact.** Goal 2.8 recorded 78
significantly negative increments over demographics out of 216. Goal 3 records
**0 negative and 0 positive** out of 56, spanning -0.0078 to +0.0045. EEG did
not become less harmful; the increment test stopped punishing a block it could
not ignore. The protocol paragraph explaining that a negative increment means
absence rather than damage is no longer needed under this design.

**A deep score is seed-unstable at a scale that dwarfs these effects.**
Between-seed AUROC standard deviation for `eeg_deep` averages 0.0249 under Group
CV and reaches 0.0527, against increments of about 0.005; one configuration
spans 0.4775 to 0.5760 across three seeds of the same fit. The paired bootstrap
resamples subjects and is blind to it. This also sets a detection floor: an
effect below about 0.02 AUROC was not separable from fit noise here.

### Three amendments, all label-free, all recorded before the matrix was read

- **30 channels, not 32.** Goal 2.8 excluded Fp1/Fp2 from its rejection decision
  because blinks dominate them, so its 150 uV bound constrains every channel
  except those two: over 237,774 trials every other channel stays below 144.5 uV
  while Fp2 reaches **118,990 uV**, and all fifty highest-amplitude subjects peak
  on Fp1 or Fp2. Goal 2.8's parietal ERP features were insulated; a network on
  the raw array is not.
- **The identity gate is relative.** The absolute 1e-10 V tolerance was
  measuring amplitude, not identity, and its worst offender was the subject with
  the largest blinks. The relative residual is one float32 epsilon everywhere.
- **The above-chance rule covers every comparison.** See above.

### Shortcut probes

The EEG embedding decodes the acquisition group at 5.4 to 5.8 times chance under
Group CV and 1.5 times under Standard CV. The asymmetry is domain shift: under
Group CV the model meets sites it never trained on and displaces their
embeddings systematically. Trial count, standard count and rejection rate carry
no label information (0.4955 to 0.5180 univariate AUROC, all p > 0.2).

### Infrastructure, on a fully contended shared host

All eight GPUs were saturated by other users for most of the run and the CPU
load reached 400 on 192 cores. Four things were needed and all affect speed
only, never a fit: per-training device re-query rather than once per job, so a
job is not locked to CPU by a transient; explicit per-worker thread limits,
since torch otherwise grabs all 192 cores per worker and 4 threads beat 8 by
2.4x; the trial cache staged into `/dev/shm`, after `vmstat` showed workers in
uninterruptible disk wait with a third of the cores idle; and a broadened device
failure detector.

The last was a real bug. `CUBLAS_STATUS_ALLOC_FAILED when calling
cublasCreate(handle)` is an allocation failure whose message never contains "out
of memory", so the fallback declined to handle it and seven jobs died. It only
appeared once the free-memory threshold was lowered to use other users'
leftovers. The detector now covers the cuBLAS and cuDNN allocation statuses and
disables CUDA for the rest of a process once its context has failed, while
letting genuine errors propagate; a test pins both halves.

Verification: `Ran 262 tests ... OK` (237 before Goal 3, 25 new). All 84 job
files carry 9100 rows with no truncation and no missing configuration. All
predictions are CV-only with zero pilot-holdout rows. The split files are
unchanged.

Reports: `reports/goal3_final_report.md`, `reports/goal3_results.md`,
`reports/goal3_method_design.md`. Machine-readable: `results/goal3/`.

**Goal 3 does not lift the gate on Goal 4, Goal 5 or multimodal fusion.**
