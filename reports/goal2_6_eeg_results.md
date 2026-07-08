# Goal 2.6 EEG Results

Protocol: fixed `split_group == cv` only; subject-level OOF predictions; 3-fold inner CV for hyperparameters and thresholds; baseline-exposed pilot holdout excluded throughout.

## Feature Extraction

| cohort_name | modality | device | task | feature_set | n_subjects | feature_count | numeric_count | categorical_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| eeg_rest_native | eeg |  | rest | no_information | 1022 | 0 | 0 | 0 |
| eeg_rest_native | eeg |  | rest | demographics | 1022 | 4 | 1 | 3 |
| eeg_rest_native | eeg |  | rest | qc | 1022 | 16 | 16 | 0 |
| eeg_rest_native | eeg |  | rest | signal | 1022 | 217 | 217 | 0 |
| eeg_rest_native | eeg |  | rest | signal_qc | 1022 | 233 | 233 | 0 |
| eeg_rest_native | eeg |  | rest | signal_demographics | 1022 | 221 | 218 | 3 |
| eeg_rest_native | eeg |  | rest | signal_qc_demographics | 1022 | 237 | 234 | 3 |
| eeg_oddball_native | eeg |  | oddball | no_information | 1827 | 0 | 0 | 0 |
| eeg_oddball_native | eeg |  | oddball | demographics | 1827 | 4 | 1 | 3 |
| eeg_oddball_native | eeg |  | oddball | qc | 1827 | 16 | 16 | 0 |
| eeg_oddball_native | eeg |  | oddball | signal | 1827 | 231 | 231 | 0 |
| eeg_oddball_native | eeg |  | oddball | signal_qc | 1827 | 247 | 247 | 0 |
| eeg_oddball_native | eeg |  | oddball | signal_demographics | 1827 | 235 | 232 | 3 |
| eeg_oddball_native | eeg |  | oddball | signal_qc_demographics | 1827 | 251 | 248 | 3 |
| eeg_1back_native | eeg |  | 1back | no_information | 1154 | 0 | 0 | 0 |
| eeg_1back_native | eeg |  | 1back | demographics | 1154 | 4 | 1 | 3 |
| eeg_1back_native | eeg |  | 1back | qc | 1154 | 16 | 16 | 0 |
| eeg_1back_native | eeg |  | 1back | signal | 1154 | 246 | 246 | 0 |
| eeg_1back_native | eeg |  | 1back | signal_qc | 1154 | 262 | 262 | 0 |
| eeg_1back_native | eeg |  | 1back | signal_demographics | 1154 | 250 | 247 | 3 |
| eeg_1back_native | eeg |  | 1back | signal_qc_demographics | 1154 | 266 | 263 | 3 |
| eeg_rest_v1_features_fixed_split | eeg |  | rest_v1_control | signal | 999 | 527 | 527 | 0 |
| eeg_rest_v1_features_fixed_split | eeg |  | rest_v1_control | demographics | 999 | 4 | 1 | 3 |
| core3_same_cohort | eeg |  | rest | demographics | 661 | 4 | 1 | 3 |
| core3_same_cohort | eeg |  | rest | modality | 661 | 217 | 217 | 0 |
| core3_same_cohort | eeg |  | rest | modality_demographics | 661 | 221 | 218 | 3 |

The Goal 2.6 EEG features are subject-level summaries derived from the v1 deep-window cache: resting band-power/connectivity-style summaries plus task-window ERP/proxy summaries for Oddball and 1BACK. They are not the old locked-test baseline metrics.

## Native-Cohort Performance

| cohort_name | task | feature_set | model | n_subjects | auroc | auprc | balanced_accuracy | macro_f1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| eeg_oddball_native | oddball | demographics | logistic_regression | 1827 | 0.6024 | 0.4242 | 0.5869 | 0.5645 |
| eeg_rest_native | rest | demographics | hist_gradient_boosting | 1022 | 0.6012 | 0.4174 | 0.5760 | 0.5484 |
| eeg_rest_native | rest | demographics | logistic_regression | 1022 | 0.6004 | 0.4132 | 0.5784 | 0.5592 |
| eeg_oddball_native | oddball | demographics | hist_gradient_boosting | 1827 | 0.5998 | 0.4117 | 0.5758 | 0.5572 |
| eeg_1back_native | 1back | demographics | logistic_regression | 1154 | 0.5981 | 0.3557 | 0.5876 | 0.5540 |
| eeg_oddball_native | oddball | demographics | random_forest | 1827 | 0.5960 | 0.4100 | 0.5668 | 0.5668 |
| eeg_rest_v1_features_fixed_split | rest_v1_control | demographics | logistic_regression | 999 | 0.5954 | 0.4141 | 0.5768 | 0.5569 |
| eeg_rest_native | rest | demographics | random_forest | 1022 | 0.5947 | 0.4176 | 0.5747 | 0.5029 |
| eeg_rest_v1_features_fixed_split | rest_v1_control | demographics | hist_gradient_boosting | 999 | 0.5928 | 0.4068 | 0.5700 | 0.5383 |
| eeg_oddball_native | oddball | signal_qc_demographics | hist_gradient_boosting | 1827 | 0.5873 | 0.3944 | 0.5398 | 0.4176 |
| eeg_oddball_native | oddball | signal_demographics | logistic_regression | 1827 | 0.5863 | 0.4107 | 0.5562 | 0.5440 |
| eeg_oddball_native | oddball | signal_demographics | hist_gradient_boosting | 1827 | 0.5840 | 0.3903 | 0.5418 | 0.4191 |
| eeg_oddball_native | oddball | signal_qc_demographics | logistic_regression | 1827 | 0.5839 | 0.4071 | 0.5546 | 0.5426 |
| eeg_rest_v1_features_fixed_split | rest_v1_control | demographics | random_forest | 999 | 0.5831 | 0.4064 | 0.5678 | 0.4945 |
| core3_same_cohort | rest | demographics | logistic_regression | 661 | 0.5754 | 0.3942 | 0.5691 | 0.5521 |

## Signal Increment Checks

| cohort_name | task | model | model_a | model_b | n_subjects | auroc_diff | auroc_diff_ci_low | auroc_diff_ci_high | fold_direction_consistency | folds_compared |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| eeg_rest_native | rest | logistic_regression | signal_qc_demographics | signal | 1022 | 0.0646 | 0.0364 | 0.0910 | 5 | 5 |
| eeg_oddball_native | oddball | hist_gradient_boosting | signal_qc_demographics | signal | 1827 | 0.0633 | 0.0308 | 0.0951 | 5 | 5 |
| eeg_rest_native | rest | hist_gradient_boosting | signal_qc_demographics | signal | 1022 | 0.0508 | 0.0048 | 0.0958 | 4 | 5 |
| eeg_oddball_native | oddball | hist_gradient_boosting | signal | qc | 1827 | 0.0458 | 0.0103 | 0.0860 | 5 | 5 |
| eeg_oddball_native | oddball | logistic_regression | signal | qc | 1827 | 0.0438 | 0.0051 | 0.0820 | 4 | 5 |
| eeg_oddball_native | oddball | random_forest | signal_qc_demographics | signal | 1827 | 0.0413 | 0.0195 | 0.0651 | 3 | 5 |
| eeg_oddball_native | oddball | logistic_regression | signal_qc_demographics | signal | 1827 | 0.0394 | 0.0225 | 0.0558 | 5 | 5 |
| eeg_1back_native | 1back | logistic_regression | signal_qc_demographics | signal | 1154 | 0.0391 | 0.0197 | 0.0619 | 5 | 5 |
| core3_same_cohort | rest | logistic_regression | modality_demographics | modality | 661 | 0.0390 | 0.0126 | 0.0642 | 4 | 5 |
| eeg_oddball_native | oddball | random_forest | signal | qc | 1827 | 0.0337 | -0.0022 | 0.0722 | 4 | 5 |
| eeg_rest_native | rest | random_forest | signal_qc_demographics | signal | 1022 | 0.0291 | -0.0041 | 0.0596 | 5 | 5 |
| eeg_1back_native | 1back | hist_gradient_boosting | signal | qc | 1154 | 0.0281 | -0.0163 | 0.0732 | 4 | 5 |
| eeg_1back_native | 1back | hist_gradient_boosting | signal_qc_demographics | signal | 1154 | 0.0242 | -0.0005 | 0.0495 | 4 | 5 |
| eeg_1back_native | 1back | random_forest | signal | qc | 1154 | 0.0151 | -0.0312 | 0.0587 | 3 | 5 |
| eeg_1back_native | 1back | random_forest | signal_qc_demographics | signal | 1154 | 0.0145 | -0.0117 | 0.0411 | 3 | 5 |

## Status

EEG: best AUROC `0.6024` from `eeg_oddball_native` / `demographics` / `logistic_regression` on `1827` subjects.
