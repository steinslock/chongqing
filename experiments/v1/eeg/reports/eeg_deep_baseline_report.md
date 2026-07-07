# EEG Deep Baseline Report

## Scope

This report summarizes anonymous cached-window EEG deep baselines for Rest, Oddball, and 1BACK. Predictions are trained at the window level and evaluated after subject-level aggregation. Raw BDF files remain in the original dataset directory and are not copied here.

## Cached Window Inventory

| task    |   subjects |   windows | label_counts      | event_counts              |
|:--------|-----------:|----------:|:------------------|:--------------------------|
| rest    |       1284 |     67332 | {0: 846, 1: 438}  | {}                        |
| oddball |       2285 |     52193 | {0: 1519, 1: 766} | {'22': 52193}             |
| 1back   |       1694 |     24780 | {0: 1173, 1: 521} | {'18': 22845, '19': 1935} |

## Overall Out-of-Fold Comparison

| family               | task    | model                    |   n_subjects |   auroc |   auprc |   balanced_accuracy |   sensitivity |   specificity |     f1 |   brier |   tn |   fp |   fn |   tp |
|:---------------------|:--------|:-------------------------|-------------:|--------:|--------:|--------------------:|--------------:|--------------:|-------:|--------:|-----:|-----:|-----:|-----:|
| deep_windows         | 1back   | eegnet                   |         1694 |  0.5337 |  0.3396 |              0.5197 |        0.5662 |        0.4731 | 0.4114 |  0.2314 |  555 |  618 |  226 |  295 |
| deep_windows         | 1back   | inceptiontime            |         1694 |  0.5265 |  0.3311 |              0.5077 |        0.0537 |        0.9616 | 0.0943 |  0.2540 | 1128 |   45 |  493 |   28 |
| deep_windows         | oddball | eegnet                   |         2285 |  0.5281 |  0.3559 |              0.5212 |        0.5914 |        0.4510 | 0.4413 |  0.2539 |  685 |  834 |  313 |  453 |
| deep_windows         | oddball | inceptiontime            |         2285 |  0.5148 |  0.3458 |              0.5000 |        0.0091 |        0.9908 | 0.0178 |  0.2597 | 1505 |   14 |  759 |    7 |
| deep_windows         | rest    | eegnet                   |         1284 |  0.5027 |  0.3485 |              0.4974 |        0.4132 |        0.5816 | 0.3720 |  0.2621 |  492 |  354 |  257 |  181 |
| deep_windows         | rest    | inceptiontime            |         1284 |  0.5106 |  0.3460 |              0.4940 |        0.2694 |        0.7187 | 0.2972 |  0.3027 |  608 |  238 |  320 |  118 |
| demographics_sanity  | rest    | demographics_only_logreg |         1247 |  0.5635 |  0.3739 |              0.5194 |        0.8227 |        0.2160 | 0.4912 |  0.2465 |  178 |  646 |   75 |  348 |
| traditional_features | rest    | dummy_prior              |         1247 |  0.4981 |  0.3383 |              0.4990 |        0.7991 |        0.1990 | 0.4757 |  0.2241 |  164 |  660 |   85 |  338 |
| traditional_features | rest    | elasticnet_logreg        |         1247 |  0.5009 |  0.3482 |              0.4999 |        0.4137 |        0.5862 | 0.3727 |  0.3101 |  483 |  341 |  248 |  175 |
| traditional_features | rest    | lightgbm                 |         1247 |  0.5123 |  0.3413 |              0.4994 |        0.0000 |        0.9988 | 0.0000 |  0.2717 |  823 |    1 |  423 |    0 |
| traditional_features | rest    | random_forest            |         1247 |  0.5145 |  0.3502 |              0.5020 |        0.0331 |        0.9709 | 0.0607 |  0.2315 |  800 |   24 |  409 |   14 |

## Deep Fold Mean/Std

| task    | model         |   folds |   auroc_mean |   auroc_std |   auprc_mean |   auprc_std |   balanced_accuracy_mean |   balanced_accuracy_std |   f1_mean |   f1_std |   brier_mean |   brier_std |
|:--------|:--------------|--------:|-------------:|------------:|-------------:|------------:|-------------------------:|------------------------:|----------:|---------:|-------------:|------------:|
| 1back   | eegnet        |       5 |       0.5368 |      0.0370 |       0.3475 |      0.0246 |                   0.5254 |                  0.0202 |    0.4034 |   0.0420 |       0.2314 |      0.0116 |
| 1back   | inceptiontime |       5 |       0.5326 |      0.0397 |       0.3458 |      0.0331 |                   0.5130 |                  0.0374 |    0.1345 |   0.1832 |       0.2540 |      0.0086 |
| oddball | eegnet        |       5 |       0.5255 |      0.0231 |       0.3626 |      0.0165 |                   0.5158 |                  0.0296 |    0.4406 |   0.0310 |       0.2539 |      0.0105 |
| oddball | inceptiontime |       5 |       0.5166 |      0.0344 |       0.3521 |      0.0286 |                   0.4989 |                  0.0018 |    0.0216 |   0.0275 |       0.2597 |      0.0245 |
| rest    | eegnet        |       5 |       0.5049 |      0.0394 |       0.3596 |      0.0405 |                   0.4955 |                  0.0500 |    0.3773 |   0.0557 |       0.2621 |      0.0181 |
| rest    | inceptiontime |       5 |       0.5165 |      0.0494 |       0.3667 |      0.0329 |                   0.5192 |                  0.0633 |    0.3211 |   0.1370 |       0.3026 |      0.0588 |

## QA Notes

- All deep outputs use `L_id` only; names and clinical scale columns are not model features.
- Every deep model writes `cv_splits.csv`; train/test overlap checks should be performed on `L_id` per fold.
- The demographics-only sanity baseline is included when parseable from the traditional Rest report.
- If deep EEG performance is not above the demographics-only baseline, this v1 result should be treated as a baseline rather than evidence of diagnostic validity.
