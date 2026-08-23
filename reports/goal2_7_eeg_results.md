# Goal 2.7 EEG Results

## Event/Timing Validity

| modality | device | task | event_validity_status | subjects |
| --- | --- | --- | --- | --- |
| eeg |  | rest | event_free_rest | 1033 |
| eeg |  | oddball | blocked_target_nontarget_semantics_unconfirmed_target_only_proxy | 1837 |
| eeg |  | 1back | blocked_condition_semantics_unconfirmed_generic_signal_only | 1345 |

## Best Inner-CV Rows

| cv_protocol | cohort_name | device | task | feature_set | model | n_subjects | auroc | auprc | balanced_accuracy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| standard_cv | eeg_oddball_native |  | oddball | demographics_group_device | random_forest | 1827 | 0.6444 | 0.4399 | 0.5926 |
| standard_cv | eeg_oddball_native |  | oddball | demographics_group | random_forest | 1827 | 0.6434 | 0.4417 | 0.5860 |
| standard_cv | eeg_oddball_native |  | oddball | demographics_group_device | logistic_regression | 1827 | 0.6425 | 0.4308 | 0.5971 |
| standard_cv | eeg_oddball_native |  | oddball | demographics_group | logistic_regression | 1827 | 0.6423 | 0.4317 | 0.5983 |
| standard_cv | eeg_rest_native |  | rest | demographics_group_device | logistic_regression | 1022 | 0.6412 | 0.4423 | 0.5893 |
| standard_cv | eeg_rest_native |  | rest | demographics_group | logistic_regression | 1022 | 0.6408 | 0.4423 | 0.5943 |
| standard_cv | eeg_1back_native |  | 1back | demographics_group_device | logistic_regression | 1154 | 0.6396 | 0.3895 | 0.6035 |
| standard_cv | eeg_1back_native |  | 1back | demographics_group | logistic_regression | 1154 | 0.6391 | 0.3879 | 0.5909 |
| standard_cv | eeg_rest_native |  | rest | demographics_group | random_forest | 1022 | 0.6383 | 0.4511 | 0.5886 |
| standard_cv | eeg_oddball_native |  | oddball | demographics_group | hist_gradient_boosting | 1827 | 0.6374 | 0.4381 | 0.5813 |
| standard_cv | eeg_rest_native |  | rest | demographics_group_device | random_forest | 1022 | 0.6369 | 0.4504 | 0.5808 |
| standard_cv | eeg_1back_native |  | 1back | demographics_group | random_forest | 1154 | 0.6361 | 0.3876 | 0.5876 |
| standard_cv | eeg_oddball_native |  | oddball | demographics_group_device | hist_gradient_boosting | 1827 | 0.6360 | 0.4368 | 0.5879 |
| standard_cv | eeg_1back_native |  | 1back | demographics_group_device | random_forest | 1154 | 0.6299 | 0.3828 | 0.5871 |
| standard_cv | eeg_rest_native |  | rest | demographics_group | hist_gradient_boosting | 1022 | 0.6292 | 0.4343 | 0.5683 |
| standard_cv | eeg_1back_native |  | 1back | demographics_group | hist_gradient_boosting | 1154 | 0.6273 | 0.3834 | 0.5852 |
| standard_cv | eeg_1back_native |  | 1back | demographics_group_device | hist_gradient_boosting | 1154 | 0.6263 | 0.3885 | 0.5789 |
| standard_cv | core3_rest_yiruidvft_selfintro_intersection |  | rest | demographics_group | logistic_regression | 661 | 0.6249 | 0.4352 | 0.5885 |
| standard_cv | core3_rest_yiruidvft_selfintro_intersection |  | rest | demographics_group_device | logistic_regression | 661 | 0.6249 | 0.4352 | 0.5885 |
| standard_cv | eeg_rest_native |  | rest | demographics_group_device | hist_gradient_boosting | 1022 | 0.6244 | 0.4399 | 0.5809 |
| standard_cv | eeg_rest_native |  | rest | group_proxy_only | hist_gradient_boosting | 1022 | 0.6188 | 0.4271 | 0.5799 |
| standard_cv | core3_rest_yiruidvft_selfintro_intersection |  | rest | demographics_group_device | random_forest | 661 | 0.6184 | 0.4378 | 0.5928 |
| standard_cv | core3_rest_yiruidvft_selfintro_intersection |  | rest | demographics_group | random_forest | 661 | 0.6176 | 0.4320 | 0.6009 |
| standard_cv | eeg_rest_native |  | rest | group_proxy_only | random_forest | 1022 | 0.6173 | 0.4183 | 0.5853 |
| standard_cv | eeg_rest_native |  | rest | group_proxy_only | logistic_regression | 1022 | 0.6159 | 0.4195 | 0.5853 |
| standard_cv | core3_rest_yiruidvft_selfintro_intersection |  | rest | demographics_group_device | hist_gradient_boosting | 661 | 0.6141 | 0.4392 | 0.5933 |
| standard_cv | core3_rest_yiruidvft_selfintro_intersection |  | rest | demographics_group | hist_gradient_boosting | 661 | 0.6141 | 0.4392 | 0.5933 |
| standard_cv | eeg_rest_native |  | rest | qc_demographics | logistic_regression | 1022 | 0.6063 | 0.4137 | 0.5691 |
| standard_cv | eeg_1back_native |  | 1back | group_proxy_only | hist_gradient_boosting | 1154 | 0.6059 | 0.3560 | 0.5950 |
| standard_cv | eeg_oddball_native |  | oddball | sex_grade | random_forest | 1827 | 0.6054 | 0.4178 | 0.5761 |
| standard_cv | eeg_oddball_native |  | oddball | group_proxy_only | hist_gradient_boosting | 1827 | 0.6050 | 0.3908 | 0.5982 |
| standard_cv | eeg_oddball_native |  | oddball | sex_grade | hist_gradient_boosting | 1827 | 0.6045 | 0.4156 | 0.5718 |
| standard_cv | eeg_oddball_native |  | oddball | group_proxy_only | random_forest | 1827 | 0.6040 | 0.3873 | 0.5893 |
| standard_cv | eeg_1back_native |  | 1back | group_proxy_only | random_forest | 1154 | 0.6034 | 0.3565 | 0.5898 |
| standard_cv | eeg_oddball_native |  | oddball | demographics | logistic_regression | 1827 | 0.6030 | 0.4236 | 0.5869 |
| standard_cv | eeg_oddball_native |  | oddball | age_sex_grade | logistic_regression | 1827 | 0.6030 | 0.4236 | 0.5869 |
| standard_cv | eeg_oddball_native |  | oddball | sex_grade | logistic_regression | 1827 | 0.6026 | 0.4120 | 0.5877 |
| standard_cv | eeg_oddball_native |  | oddball | age_sex_grade_group | logistic_regression | 1827 | 0.6024 | 0.4242 | 0.5869 |
| standard_cv | core3_rest_yiruidvft_selfintro_intersection |  | rest | group_proxy_only | logistic_regression | 661 | 0.6022 | 0.4123 | 0.5882 |
| standard_cv | eeg_oddball_native |  | oddball | group_proxy_only | logistic_regression | 1827 | 0.6019 | 0.3881 | 0.5878 |

## Independent Increment Paired Comparisons

| cv_protocol | cohort_name | device | task | model | comparison | n_subjects | auroc_diff | auroc_diff_ci_low | auroc_diff_ci_high | fold_direction_consistency | protocol_consistent_direction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| group_cv | eeg_1back_native |  | 1back | hist_gradient_boosting | signal_demographics_vs_demographics | 1154 | -0.0512 | -0.0979 | -0.0060 | 1 | 1 |
| group_cv | eeg_1back_native |  | 1back | hist_gradient_boosting | signal_qc_demographics_vs_qc_demographics | 1154 | -0.0250 | -0.0701 | 0.0186 | 1 | 1 |
| group_cv | eeg_1back_native |  | 1back | logistic_regression | signal_demographics_vs_demographics | 1154 | -0.0531 | -0.0944 | -0.0132 | 1 | 1 |
| group_cv | eeg_1back_native |  | 1back | logistic_regression | signal_qc_demographics_vs_qc_demographics | 1154 | -0.0570 | -0.0962 | -0.0178 | 0 | 1 |
| group_cv | eeg_1back_native |  | 1back | random_forest | signal_demographics_vs_demographics | 1154 | -0.0686 | -0.1147 | -0.0258 | 1 | 1 |
| group_cv | eeg_1back_native |  | 1back | random_forest | signal_qc_demographics_vs_qc_demographics | 1154 | -0.0205 | -0.0608 | 0.0217 | 1 | 1 |
| group_cv | eeg_oddball_native |  | oddball | hist_gradient_boosting | signal_demographics_vs_demographics | 1827 | -0.0086 | -0.0380 | 0.0212 | 3 | 1 |
| group_cv | eeg_oddball_native |  | oddball | hist_gradient_boosting | signal_qc_demographics_vs_qc_demographics | 1827 | 0.0179 | -0.0099 | 0.0459 | 3 | 0 |
| group_cv | eeg_oddball_native |  | oddball | logistic_regression | signal_demographics_vs_demographics | 1827 | -0.0328 | -0.0565 | -0.0081 | 0 | 1 |
| group_cv | eeg_oddball_native |  | oddball | logistic_regression | signal_qc_demographics_vs_qc_demographics | 1827 | -0.0166 | -0.0411 | 0.0100 | 2 | 1 |
| group_cv | eeg_oddball_native |  | oddball | random_forest | signal_demographics_vs_demographics | 1827 | -0.0397 | -0.0673 | -0.0105 | 2 | 1 |
| group_cv | eeg_oddball_native |  | oddball | random_forest | signal_qc_demographics_vs_qc_demographics | 1827 | -0.0513 | -0.0819 | -0.0222 | 2 | 1 |
| group_cv | eeg_rest_native |  | rest | hist_gradient_boosting | signal_demographics_vs_demographics | 1022 | -0.0486 | -0.0905 | -0.0055 | 1 | 1 |
| group_cv | eeg_rest_native |  | rest | hist_gradient_boosting | signal_qc_demographics_vs_qc_demographics | 1022 | -0.0496 | -0.0940 | -0.0059 | 1 | 1 |
| group_cv | eeg_rest_native |  | rest | logistic_regression | signal_demographics_vs_demographics | 1022 | -0.0654 | -0.1017 | -0.0253 | 1 | 1 |
| group_cv | eeg_rest_native |  | rest | logistic_regression | signal_qc_demographics_vs_qc_demographics | 1022 | -0.0793 | -0.1127 | -0.0449 | 0 | 1 |
| group_cv | eeg_rest_native |  | rest | random_forest | signal_demographics_vs_demographics | 1022 | -0.0673 | -0.1118 | -0.0216 | 1 | 1 |
| group_cv | eeg_rest_native |  | rest | random_forest | signal_qc_demographics_vs_qc_demographics | 1022 | -0.0824 | -0.1251 | -0.0405 | 0 | 1 |
| standard_cv | eeg_1back_native |  | 1back | hist_gradient_boosting | signal_demographics_vs_demographics | 1154 | -0.0492 | -0.0933 | -0.0063 | 0 | 1 |
| standard_cv | eeg_1back_native |  | 1back | hist_gradient_boosting | signal_qc_demographics_vs_qc_demographics | 1154 | -0.0149 | -0.0545 | 0.0249 | 2 | 1 |
| standard_cv | eeg_1back_native |  | 1back | logistic_regression | signal_demographics_vs_demographics | 1154 | -0.0454 | -0.0815 | -0.0086 | 1 | 1 |
| standard_cv | eeg_1back_native |  | 1back | logistic_regression | signal_qc_demographics_vs_qc_demographics | 1154 | -0.0473 | -0.0821 | -0.0115 | 1 | 1 |
| standard_cv | eeg_1back_native |  | 1back | random_forest | signal_demographics_vs_demographics | 1154 | -0.0532 | -0.0994 | -0.0040 | 0 | 1 |
| standard_cv | eeg_1back_native |  | 1back | random_forest | signal_qc_demographics_vs_qc_demographics | 1154 | -0.0247 | -0.0677 | 0.0204 | 3 | 1 |
| standard_cv | eeg_oddball_native |  | oddball | hist_gradient_boosting | signal_demographics_vs_demographics | 1827 | -0.0244 | -0.0538 | 0.0053 | 1 | 1 |
| standard_cv | eeg_oddball_native |  | oddball | hist_gradient_boosting | signal_qc_demographics_vs_qc_demographics | 1827 | -0.0050 | -0.0349 | 0.0252 | 2 | 0 |
| standard_cv | eeg_oddball_native |  | oddball | logistic_regression | signal_demographics_vs_demographics | 1827 | -0.0168 | -0.0422 | 0.0073 | 2 | 1 |
| standard_cv | eeg_oddball_native |  | oddball | logistic_regression | signal_qc_demographics_vs_qc_demographics | 1827 | -0.0097 | -0.0343 | 0.0128 | 2 | 1 |
| standard_cv | eeg_oddball_native |  | oddball | random_forest | signal_demographics_vs_demographics | 1827 | -0.0370 | -0.0671 | -0.0079 | 0 | 1 |
| standard_cv | eeg_oddball_native |  | oddball | random_forest | signal_qc_demographics_vs_qc_demographics | 1827 | -0.0326 | -0.0632 | 0.0012 | 0 | 1 |
| standard_cv | eeg_rest_native |  | rest | hist_gradient_boosting | signal_demographics_vs_demographics | 1022 | -0.0848 | -0.1266 | -0.0407 | 0 | 1 |
| standard_cv | eeg_rest_native |  | rest | hist_gradient_boosting | signal_qc_demographics_vs_qc_demographics | 1022 | -0.0559 | -0.0962 | -0.0168 | 1 | 1 |
| standard_cv | eeg_rest_native |  | rest | logistic_regression | signal_demographics_vs_demographics | 1022 | -0.0408 | -0.0764 | -0.0046 | 2 | 1 |
| standard_cv | eeg_rest_native |  | rest | logistic_regression | signal_qc_demographics_vs_qc_demographics | 1022 | -0.0474 | -0.0778 | -0.0190 | 1 | 1 |
| standard_cv | eeg_rest_native |  | rest | random_forest | signal_demographics_vs_demographics | 1022 | -0.0742 | -0.1172 | -0.0303 | 0 | 1 |
| standard_cv | eeg_rest_native |  | rest | random_forest | signal_qc_demographics_vs_qc_demographics | 1022 | -0.0648 | -0.1054 | -0.0218 | 1 | 1 |
