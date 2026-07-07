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
