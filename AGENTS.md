# Chongqing Binary Diagnosis Agents

Last updated: 2026-07-07

## Project Root

Use this directory as the project root:

`/home/qiangminc/codes/data4_qiangminc/code/chongqing`

## Goal0 Scope

Goal0 initializes a reproducible engineering framework for the Chongqing health/non-health binary diagnosis project. It does not run full model training.

Allowed Goal0 work:

- Create project documentation, configs, source interfaces, scripts, tests, and output directories.
- Read the raw dataset and existing derived reports as read-only inputs.
- Run unit tests and a small manifest-only smoke test.
- Record Python, CUDA, PyTorch, and key dependency versions.

Disallowed Goal0 work:

- Modify, rename, move, normalize, or cache raw files under `/home/qiangminc/codes/data4_qiangminc/datasets_qiangmin/chongqing`.
- Modify existing derived reports under `inputs/derived_reports/chongqing_binary_diagnosis_report` unless a future task explicitly requests it.
- Run full EEG, fNIRS, face, eye-tracking, or multimodal training.
- Use clinical scale or diagnosis fields as model input features.

## Read-Only Inputs

Treat these as read-only:

- Raw dataset: `/home/qiangminc/codes/data4_qiangminc/datasets_qiangmin/chongqing`
- Existing report bundle: `/home/qiangminc/codes/data4_qiangminc/code/chongqing/inputs/derived_reports/chongqing_binary_diagnosis_report`

All new generated files should go under the project root directories:

- `artifacts/`
- `results/`
- `reports/`
- `checkpoints/`

## Safety Rules

- Split all experiments at subject level by `L_id`; never split windows, trials, frames, or epochs across train/test.
- Do not write names, phone numbers, school/class identities, or other direct identifiers to new artifacts.
- Do not use label-proxy clinical fields as model inputs. Forbidden predictors include diagnosis columns, labels, CDRS, CES-DC, HAMA, suicide/self-harm fields, manual review fields, and other clinical scale totals.
- Keep smoke tests small and fast. The default smoke test reads only the subject manifest and uses non-clinical modality availability fields.
- Future full runs must write configs, logs, metrics, predictions, and checkpoints outside read-only inputs.

## Current Entry Points

- Unit tests: `python -m unittest discover -s tests`
- Smoke test: `python scripts/smoke_test.py --config configs/smoke.yaml`
- Leakage guard check: `python scripts/check_leakage.py --config configs/smoke.yaml`
- Environment record: `python scripts/record_environment.py --config configs/default.yaml`
