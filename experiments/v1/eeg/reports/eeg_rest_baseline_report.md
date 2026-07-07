# EEG Rest Baseline Report

## Run Summary

- Label: `primary_label_nonhealthy`
- Subjects used: 1247
- Label counts: `{"0": 824, "1": 423}`
- CV: 5-fold stratified subject-level CV
- Seed: 20260703
- Feature family: EEG-only Rest bandpower, asymmetry, spectral entropy, Hjorth, and QC features.
- Forbidden clinical scale and diagnosis fields are excluded from features.

## Overall Out-of-Fold Metrics

| model             | fold        |    n |   threshold |   auroc |   auprc |   balanced_accuracy |   sensitivity |   specificity |     f1 |   brier |   tn |   fp |   fn |   tp |
|:------------------|:------------|-----:|------------:|--------:|--------:|--------------------:|--------------:|--------------:|-------:|--------:|-----:|-----:|-----:|-----:|
| random_forest     | overall_oof | 1247 |      0.5446 |  0.5145 |  0.3502 |              0.5020 |        0.0331 |        0.9709 | 0.0607 |  0.2315 |  800 |   24 |  409 |   14 |
| lightgbm          | overall_oof | 1247 |      0.9633 |  0.5123 |  0.3413 |              0.4994 |        0.0000 |        0.9988 | 0.0000 |  0.2717 |  823 |    1 |  423 |    0 |
| elasticnet_logreg | overall_oof | 1247 |      0.5117 |  0.5009 |  0.3482 |              0.4999 |        0.4137 |        0.5862 | 0.3727 |  0.3101 |  483 |  341 |  248 |  175 |
| dummy_prior       | overall_oof | 1247 |      0.3390 |  0.4981 |  0.3383 |              0.4990 |        0.7991 |        0.1990 | 0.4757 |  0.2241 |  164 |  660 |   85 |  338 |

## Demographics-Only Sanity Baseline

| model                    | fold        |    n |   threshold |   auroc |   auprc |   balanced_accuracy |   sensitivity |   specificity |     f1 |   brier |   tn |   fp |   fn |   tp |
|:-------------------------|:------------|-----:|------------:|--------:|--------:|--------------------:|--------------:|--------------:|-------:|--------:|-----:|-----:|-----:|-----:|
| demographics_only_logreg | overall_oof | 1247 |      0.4191 |  0.5635 |  0.3739 |              0.5194 |        0.8227 |        0.2160 | 0.4912 |  0.2465 |  178 |  646 |   75 |  348 |

## QA Notes

- Predictions are out-of-fold; no subject appears in both train and test within a fold.
- Accuracy alone is not used as a success criterion; AUROC, AUPRC, balanced accuracy, sensitivity, specificity, F1, and Brier are reported.
- This report covers Rest EEG only; Oddball and 1BACK are reserved for later v1 expansion.
