# Chongqing Health/Non-Health Binary Diagnosis Project Spec

## Purpose

Build a reproducible, subject-level engineering framework for health/non-health binary diagnosis using the Chongqing multimodal dataset. Goal0 only initializes the framework; it does not perform full training.

## Data Sources

Read-only raw dataset:

`/home/qiangminc/codes/data4_qiangminc/datasets_qiangmin/chongqing`

Read-only existing report bundle:

`/home/qiangminc/codes/data4_qiangminc/code/chongqing/inputs/derived_reports/chongqing_binary_diagnosis_report`

Primary dataset description:

`inputs/derived_reports/chongqing_binary_diagnosis_report/DATASET_DESCRIPTION.md`

Canonical manifest:

`inputs/derived_reports/chongqing_binary_diagnosis_report/data/subject_manifest.csv`

The manifest is the initial subject-level interface. It contains anonymous `A_id` and `L_id` identifiers, diagnosis labels, demographic fields, and modality coverage flags.

## Task Definition

Primary task:

Health vs non-health/high-risk/disease binary classification at subject level.

Primary label:

`primary_label_nonhealthy`

Label semantics:

- `0`: healthy
- `1`: non-healthy/high-risk/disease
- empty: excluded from supervised training/evaluation

The positive class includes high-risk, MDD, anxiety disorder, ADHD, schizophrenia, OCD, bipolar disorder, PTSD, and other non-healthy states. It is not a pure MDD label.

Sensitivity labels:

- `sensitivity_label_clear_diagnosis`: healthy vs clear diagnosis, excluding high-risk.
- `sensitivity_label_mdd_highrisk`: healthy vs high-risk+MDD.

## Engineering Structure

Root-level directories:

| Directory | Purpose |
|---|---|
| `configs/` | YAML experiment and smoke-test configs |
| `src/` | Reusable Python interfaces and framework code |
| `scripts/` | Command-line entry points |
| `tests/` | Standard-library unit tests |
| `artifacts/` | Intermediate generated artifacts |
| `results/` | Predictions, metrics, and result tables |
| `reports/` | Generated project reports and environment records |
| `checkpoints/` | Future model checkpoints |

Organized legacy and versioned workspaces:

- `inputs/derived_reports/chongqing_binary_diagnosis_report/`: read-only derived dataset report and manifest.
- `experiments/v1/`: prior EEG baseline work.
- `experiments/v2/`: reserved for future work.

## Required Interfaces

Goal0 establishes these interfaces under `src/chongqing_binary`:

- Subject-level data interface: manifest loading, schema validation, label filtering, modality flags, and smoke sampling.
- Configuration interface: YAML loading, path resolution, defaults, and read-only input declarations.
- Logging interface: reproducible console/file logging setup.
- Model interface: small protocol for binary classifiers plus a smoke-only majority baseline.
- Evaluation interface: subject-level binary metrics from labels and probabilities.
- Leakage guard: automatic validation that forbidden clinical/diagnosis fields are not used as feature columns.

## Output Policy

New outputs must be written under `artifacts/`, `results/`, `reports/`, or `checkpoints/`.

Writes under the raw dataset directory or the existing report bundle are blocked by the project path guard.

## Dependency Policy

Goal0 code uses the Python standard library for tests and core interfaces where practical. YAML config loading uses `pyyaml`, which is already present in the existing `chongqing_v1` environment.

No new dependency is installed during Goal0.
