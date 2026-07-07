# Leakage Audit

## Technical Summary

- No model training was run in this stage.
- Cohort and split artifacts retain labels and diagnosis fields only for auditing, stratification, and future evaluation joins.
- Feature inputs for the Goal0 smoke path remain limited to non-clinical modality availability fields.
- Automated tests cover forbidden clinical/diagnosis feature detection and split ID non-overlap.

## Forbidden Feature Policy

Exact forbidden fields:

- `diag3`
- `primary_label_nonhealthy`
- `sensitivity_label_clear_diagnosis`
- `sensitivity_label_mdd_highrisk`
- `CDRS_score`

Forbidden patterns:

- `(?i)cdrs`
- `(?i)ces[-_ ]?dc`
- `(?i)hama`
- `(?i)scared`
- `(?i)suicid`
- `(?i)diagn`
- `(?i)label`
- `诊断`
- `量表`
- `总分`
- `自杀`
- `自伤`
- `复核`
- `人工`

## Split Artifact Label Columns

The split file intentionally includes the following label/diagnosis columns for auditability, not as model features:

- `diag3`
- `primary_label_nonhealthy`
- `sensitivity_label_clear_diagnosis`
- `sensitivity_label_mdd_highrisk`

## Required Downstream Use

- Before feature matrices are accepted, run `validate_feature_columns` from `src/chongqing_binary/leakage.py`.
- Do not include CDRS, CES-DC, HAMA, SCARED, suicide/self-harm, diagnosis, label, manual review, or clinical scale total columns in model inputs.
- Do not use the locked test set for feature selection, hyperparameter tuning, threshold selection, early stopping, model family choice, or any other model-selection decision.
