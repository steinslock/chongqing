# Chongqing Binary Diagnosis Report Artifacts

This directory contains derived, read-only-analysis outputs for the Chongqing multimodal health/disease binary diagnosis planning task. No original dataset files are stored or modified here.

## Primary deliverable

- `report/chongqing_binary_diagnosis_survey.md`: Chinese technical survey report and recommended experimental roadmap.

## Data indexes and QA

- `data/subject_manifest.csv`: Subject-level manifest without names.
- `data/modality_coverage.csv`: Modality coverage summary.
- `data/qa_summary.json`: Reproducible QA summary.
- `data/qa_summary.md`: Human-readable QA summary.
- `data/literature_matrix.csv`: Literature matrix with 25 related papers/reviews.

## Scripts

- `scripts/build_manifest.py`: Rebuilds manifest and QA files from the original dataset in read-only mode.

