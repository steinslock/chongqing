# Progress Log

## 2026-07-07 - Goal0 Project Initialization

Status: complete.

Completed:

- Read `inputs/derived_reports/chongqing_binary_diagnosis_report/DATASET_DESCRIPTION.md`.
- Selected `/home/qiangminc/codes/data4_qiangminc/code/chongqing` as the project root.
- Confirmed existing inputs:
  - Raw dataset at `/home/qiangminc/codes/data4_qiangminc/datasets_qiangmin/chongqing`.
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
  - Raw dataset: `/home/qiangminc/codes/data4_qiangminc/datasets_qiangmin/chongqing`
  - Existing report bundle: `/home/qiangminc/codes/data4_qiangminc/code/chongqing/inputs/derived_reports/chongqing_binary_diagnosis_report`
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
  - `/home/qiangminc/codes/data4_qiangminc/code/.venvs/chongqing_v1/bin/python -m compileall -q src scripts tests`
- Unit tests passed:
  - `/home/qiangminc/codes/data4_qiangminc/code/.venvs/chongqing_v1/bin/python -m unittest discover -s tests`
  - Result: `Ran 13 tests ... OK`
- Leakage script passed:
  - `/home/qiangminc/codes/data4_qiangminc/code/.venvs/chongqing_v1/bin/python scripts/check_leakage.py --config configs/smoke.yaml`
- Smoke test passed:
  - `/home/qiangminc/codes/data4_qiangminc/code/.venvs/chongqing_v1/bin/python scripts/smoke_test.py --config configs/smoke.yaml`
- Environment recording passed:
  - `/home/qiangminc/codes/data4_qiangminc/code/.venvs/chongqing_v1/bin/python scripts/record_environment.py --config configs/default.yaml`
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
  - `/home/qiangminc/codes/data4_qiangminc/code/.venvs/chongqing_v1/bin/python -m compileall -q src scripts tests experiments/v1/eeg/scripts`
- Unit tests passed:
  - `/home/qiangminc/codes/data4_qiangminc/code/.venvs/chongqing_v1/bin/python -m unittest discover -s tests`
  - Result: `Ran 13 tests ... OK`
- Leakage script passed:
  - `/home/qiangminc/codes/data4_qiangminc/code/.venvs/chongqing_v1/bin/python scripts/check_leakage.py --config configs/smoke.yaml`
- Smoke test passed:
  - `/home/qiangminc/codes/data4_qiangminc/code/.venvs/chongqing_v1/bin/python scripts/smoke_test.py --config configs/smoke.yaml`

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
  - `/home/qiangminc/codes/data4_qiangminc/code/.venvs/chongqing_v1/bin/python scripts/build_subject_splits.py --config configs/default.yaml`
- Compile check passed:
  - `/home/qiangminc/codes/data4_qiangminc/code/.venvs/chongqing_v1/bin/python -m compileall -q src scripts tests`
- Unit tests passed:
  - `/home/qiangminc/codes/data4_qiangminc/code/.venvs/chongqing_v1/bin/python -m unittest discover -s tests`
  - Result: `Ran 20 tests ... OK`
- Leakage script passed:
  - `/home/qiangminc/codes/data4_qiangminc/code/.venvs/chongqing_v1/bin/python scripts/check_leakage.py --config configs/smoke.yaml`
- Smoke test passed:
  - `/home/qiangminc/codes/data4_qiangminc/code/.venvs/chongqing_v1/bin/python scripts/smoke_test.py --config configs/smoke.yaml`
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
  - `/home/qiangminc/codes/data4_qiangminc/code/.venvs/chongqing_v1/bin/python scripts/run_baselines.py --config configs/baselines/smoke.yaml`
- Formal baseline run passed:
  - `/home/qiangminc/codes/data4_qiangminc/code/.venvs/chongqing_v1/bin/python scripts/run_baselines.py --config configs/baselines/default.yaml`
- Completion audit confirmed:
  - All required models are present in `results/baseline_results.csv`.
  - Both `cv_oof` and `locked_test` stages are present for each required model.
  - All requested metrics and `_ci_low`/`_ci_high` 95% CI columns are present and finite.
  - fNIRS and Face are explicitly skipped in `artifacts/baselines/feature_availability.json` without fake result rows.
  - Prediction rows respect the locked-test boundary.
  - All checkpoint paths recorded in `artifacts/baselines/baseline_run_manifest.json` exist.
- Compile check passed:
  - `/home/qiangminc/codes/data4_qiangminc/code/.venvs/chongqing_v1/bin/python -m compileall -q src scripts tests`
- Unit tests passed:
  - `/home/qiangminc/codes/data4_qiangminc/code/.venvs/chongqing_v1/bin/python -m unittest discover -s tests -v`
  - Result: `Ran 29 tests ... OK`
- Leakage script passed:
  - `/home/qiangminc/codes/data4_qiangminc/code/.venvs/chongqing_v1/bin/python scripts/check_leakage.py --config configs/smoke.yaml`
- Goal0 smoke test still passed:
  - `/home/qiangminc/codes/data4_qiangminc/code/.venvs/chongqing_v1/bin/python scripts/smoke_test.py --config configs/smoke.yaml`
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

- `/home/qiangminc/miniconda3/envs/avmoe/bin/python scripts/audit_eeg_readiness.py --config configs/readiness/eeg_smoke.yaml --smoke-limit 2 --seed 20260707`
- `/home/qiangminc/miniconda3/envs/avmoe/bin/python scripts/audit_fnirs_readiness.py --config configs/readiness/fnirs_smoke.yaml --smoke-limit 2 --seed 20260707`
- `/home/qiangminc/miniconda3/envs/avmoe/bin/python scripts/audit_face_readiness.py --config configs/readiness/face_smoke.yaml --smoke-limit 2 --seed 20260707`
- `/home/qiangminc/miniconda3/envs/avmoe/bin/python scripts/build_cohorts_v2.py --config configs/readiness/default.yaml --seed 20260707`
- `/home/qiangminc/miniconda3/envs/avmoe/bin/python scripts/audit_groups.py --config configs/readiness/default.yaml --seed 20260707`
- `/home/qiangminc/miniconda3/envs/avmoe/bin/python scripts/generate_goal2_5_reports.py`
- `/home/qiangminc/miniconda3/envs/avmoe/bin/python -m compileall -q src scripts tests`
- `/home/qiangminc/miniconda3/envs/avmoe/bin/python -m unittest discover -s tests -v`
- `/home/qiangminc/miniconda3/envs/avmoe/bin/python scripts/check_leakage.py --config configs/smoke.yaml`

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

- `/home/qiangminc/miniconda3/envs/avmoe/bin/python scripts/extract_eeg_goal2_6_features.py --config configs/goal2_6/eeg.yaml`
- `/home/qiangminc/miniconda3/envs/avmoe/bin/python scripts/extract_fnirs_goal2_6_features.py --config configs/goal2_6/fnirs.yaml`
- `/home/qiangminc/miniconda3/envs/avmoe/bin/python scripts/extract_face_goal2_6_features.py --config configs/goal2_6/face.yaml`
- `/home/qiangminc/miniconda3/envs/avmoe/bin/python - <<'PY' ... run_goal2_6(['eeg', 'fnirs', 'face', 'core3', 'shortcut']) ... PY`
- `/home/qiangminc/miniconda3/envs/avmoe/bin/python scripts/summarize_goal2_6.py --config configs/goal2_6/models.yaml`
- `/home/qiangminc/miniconda3/envs/avmoe/bin/python -m compileall -q src scripts tests`
- `/home/qiangminc/miniconda3/envs/avmoe/bin/python -m unittest discover -s tests -v`
- `/home/qiangminc/miniconda3/envs/avmoe/bin/python scripts/check_leakage.py --config configs/smoke.yaml`
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

- `/home/qiangminc/miniconda3/envs/avmoe/bin/python scripts/extract_eeg_goal2_7_features.py --config configs/goal2_7/eeg.yaml`
- `/home/qiangminc/miniconda3/envs/avmoe/bin/python scripts/extract_fnirs_goal2_7_features.py --config configs/goal2_7/fnirs.yaml`
- `/home/qiangminc/miniconda3/envs/avmoe/bin/python scripts/extract_face_goal2_7_features.py --config configs/goal2_7/face.yaml`
- `/home/qiangminc/miniconda3/envs/avmoe/bin/python scripts/audit_goal2_7_events.py`
- `PYTHONPATH=src PYTHONUNBUFFERED=1 /home/qiangminc/miniconda3/envs/avmoe/bin/python scripts/run_goal2_7.py --skip-supplemental`
- `PYTHONPATH=src PYTHONUNBUFFERED=1 /home/qiangminc/miniconda3/envs/avmoe/bin/python scripts/run_goal2_7.py --supplemental-only`
- `PYTHONPATH=src PYTHONUNBUFFERED=1 /home/qiangminc/miniconda3/envs/avmoe/bin/python scripts/summarize_goal2_7.py`
- `PYTHONPATH=src /home/qiangminc/miniconda3/envs/avmoe/bin/python -m compileall -q src scripts tests`
- `PYTHONPATH=src /home/qiangminc/miniconda3/envs/avmoe/bin/python -m unittest discover -s tests`

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
  `/data4/qiangminc`.

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
