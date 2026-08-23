# Goal 2.7 fNIRS Results

## Event/Timing Validity

| modality | device | task | event_validity_status | subjects |
| --- | --- | --- | --- | --- |
| fnirs | yiruid | rest | event_free_rest_whole_recording | 1514 |
| fnirs | yiruid | vft | yiruid_vft_markers_present_timing_semantics_unconfirmed | 1480 |
| fnirs | yiruid | 1back | yiruid_1back_markers_present_timing_semantics_unconfirmed | 1422 |
| fnirs | yiruid | 1back | yiruid_1back_no_markers_task_response_blocked | 1 |
| fnirs | bikom | rest | event_free_rest_whole_recording | 1017 |
| fnirs | bikom | vft | bikom_vft_no_markers_task_response_blocked | 1022 |
| fnirs | bikom | 1back | bikom_1back_markers_present_timing_semantics_unconfirmed | 985 |
| fnirs | bikom | 1back | bikom_1back_no_markers_task_response_blocked | 10 |

## Best Inner-CV Rows

| cv_protocol | cohort_name | device | task | feature_set | model | n_subjects | auroc | auprc | balanced_accuracy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| standard_cv | fnirs_yiruid_1back_native | yiruid | 1back | demographics_group_device | logistic_regression | 1422 | 0.6645 | 0.5408 | 0.6078 |
| standard_cv | fnirs_yiruid_1back_native | yiruid | 1back | demographics_group | logistic_regression | 1422 | 0.6645 | 0.5407 | 0.6078 |
| standard_cv | fnirs_yiruid_rest_native | yiruid | rest | demographics_group | logistic_regression | 1514 | 0.6616 | 0.5407 | 0.6318 |
| standard_cv | fnirs_yiruid_rest_native | yiruid | rest | demographics_group_device | logistic_regression | 1514 | 0.6616 | 0.5407 | 0.6318 |
| standard_cv | fnirs_yiruid_1back_native | yiruid | 1back | demographics_group_device | hist_gradient_boosting | 1422 | 0.6611 | 0.5458 | 0.6105 |
| standard_cv | fnirs_yiruid_1back_native | yiruid | 1back | demographics_group | hist_gradient_boosting | 1422 | 0.6611 | 0.5458 | 0.6105 |
| standard_cv | fnirs_yiruid_1back_native | yiruid | 1back | demographics_group_device | random_forest | 1422 | 0.6610 | 0.5492 | 0.6238 |
| standard_cv | fnirs_yiruid_vft_native | yiruid | vft | demographics_group | logistic_regression | 1480 | 0.6592 | 0.5355 | 0.6144 |
| standard_cv | fnirs_yiruid_rest_native | yiruid | rest | demographics_group | random_forest | 1514 | 0.6590 | 0.5448 | 0.6186 |
| standard_cv | fnirs_yiruid_rest_native | yiruid | rest | demographics_group | hist_gradient_boosting | 1514 | 0.6587 | 0.5419 | 0.6127 |
| standard_cv | fnirs_yiruid_rest_native | yiruid | rest | demographics_group_device | hist_gradient_boosting | 1514 | 0.6587 | 0.5419 | 0.6127 |
| standard_cv | fnirs_yiruid_vft_native | yiruid | vft | demographics_group_device | logistic_regression | 1480 | 0.6586 | 0.5370 | 0.6132 |
| standard_cv | fnirs_yiruid_rest_native | yiruid | rest | demographics_group_device | random_forest | 1514 | 0.6586 | 0.5431 | 0.6160 |
| standard_cv | fnirs_yiruid_vft_native | yiruid | vft | demographics_group | random_forest | 1480 | 0.6551 | 0.5418 | 0.6162 |
| standard_cv | fnirs_yiruid_vft_native | yiruid | vft | demographics_group_device | hist_gradient_boosting | 1480 | 0.6541 | 0.5395 | 0.6074 |
| standard_cv | fnirs_yiruid_vft_native | yiruid | vft | demographics_group | hist_gradient_boosting | 1480 | 0.6541 | 0.5395 | 0.6074 |
| standard_cv | fnirs_yiruid_1back_native | yiruid | 1back | demographics_group | random_forest | 1422 | 0.6531 | 0.5432 | 0.6202 |
| standard_cv | fnirs_bikom_1back_native | bikom | 1back | demographics_group_device | logistic_regression | 985 | 0.6513 | 0.4375 | 0.5870 |
| standard_cv | fnirs_bikom_1back_native | bikom | 1back | demographics_group | logistic_regression | 985 | 0.6512 | 0.4375 | 0.5870 |
| standard_cv | fnirs_yiruid_vft_native | yiruid | vft | demographics_group_device | random_forest | 1480 | 0.6501 | 0.5368 | 0.6041 |
| standard_cv | fnirs_bikom_vft_native | bikom | vft | demographics_group_device | logistic_regression | 1022 | 0.6417 | 0.4289 | 0.5815 |
| standard_cv | fnirs_bikom_vft_native | bikom | vft | demographics_group | logistic_regression | 1022 | 0.6416 | 0.4288 | 0.5815 |
| standard_cv | fnirs_bikom_rest_native | bikom | rest | demographics_group_device | logistic_regression | 1017 | 0.6406 | 0.4344 | 0.5922 |
| standard_cv | fnirs_bikom_rest_native | bikom | rest | demographics_group | logistic_regression | 1017 | 0.6406 | 0.4344 | 0.5922 |
| standard_cv | fnirs_yiruid_1back_native | yiruid | 1back | group_proxy_only | logistic_regression | 1422 | 0.6302 | 0.5119 | 0.6122 |
| standard_cv | fnirs_bikom_vft_native | bikom | vft | qc_demographics | logistic_regression | 1022 | 0.6296 | 0.4503 | 0.5744 |
| standard_cv | fnirs_bikom_1back_native | bikom | 1back | demographics_group | hist_gradient_boosting | 985 | 0.6292 | 0.4190 | 0.5762 |
| standard_cv | fnirs_bikom_1back_native | bikom | 1back | demographics_group_device | hist_gradient_boosting | 985 | 0.6292 | 0.4190 | 0.5762 |
| standard_cv | fnirs_yiruid_1back_native | yiruid | 1back | group_proxy_only | random_forest | 1422 | 0.6291 | 0.5123 | 0.6110 |
| standard_cv | fnirs_bikom_1back_native | bikom | 1back | age_sex_grade | logistic_regression | 985 | 0.6286 | 0.4419 | 0.5814 |
| standard_cv | fnirs_bikom_1back_native | bikom | 1back | demographics | logistic_regression | 985 | 0.6286 | 0.4419 | 0.5814 |
| standard_cv | fnirs_yiruid_rest_native | yiruid | rest | group_proxy_only | logistic_regression | 1514 | 0.6278 | 0.5097 | 0.6098 |
| standard_cv | fnirs_yiruid_vft_native | yiruid | vft | group_proxy_only | random_forest | 1480 | 0.6275 | 0.5107 | 0.6125 |
| standard_cv | fnirs_bikom_1back_native | bikom | 1back | demographics_group_device | random_forest | 985 | 0.6275 | 0.4261 | 0.5930 |
| standard_cv | fnirs_bikom_vft_native | bikom | vft | demographics_group | hist_gradient_boosting | 1022 | 0.6274 | 0.4175 | 0.5628 |
| standard_cv | fnirs_bikom_vft_native | bikom | vft | demographics_group_device | hist_gradient_boosting | 1022 | 0.6274 | 0.4175 | 0.5628 |
| standard_cv | fnirs_yiruid_1back_native | yiruid | 1back | group_proxy_only | hist_gradient_boosting | 1422 | 0.6268 | 0.5129 | 0.5993 |
| standard_cv | fnirs_yiruid_vft_native | yiruid | vft | group_proxy_only | logistic_regression | 1480 | 0.6268 | 0.5103 | 0.6123 |
| standard_cv | fnirs_bikom_1back_native | bikom | 1back | demographics_group | random_forest | 985 | 0.6266 | 0.4234 | 0.5780 |
| standard_cv | fnirs_yiruid_rest_native | yiruid | rest | group_proxy_only | random_forest | 1514 | 0.6265 | 0.5107 | 0.6045 |

## Independent Increment Paired Comparisons

| cv_protocol | cohort_name | device | task | model | comparison | n_subjects | auroc_diff | auroc_diff_ci_low | auroc_diff_ci_high | fold_direction_consistency | protocol_consistent_direction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| group_cv | fnirs_bikom_1back_native | bikom | 1back | hist_gradient_boosting | signal_demographics_vs_demographics | 985 | -0.0426 | -0.0881 | 0.0046 | 2 | 1 |
| group_cv | fnirs_bikom_1back_native | bikom | 1back | hist_gradient_boosting | signal_qc_demographics_vs_qc_demographics | 985 | -0.0135 | -0.0570 | 0.0385 | 0 | 1 |
| group_cv | fnirs_bikom_1back_native | bikom | 1back | logistic_regression | signal_demographics_vs_demographics | 985 | -0.0336 | -0.0808 | 0.0170 | 2 | 1 |
| group_cv | fnirs_bikom_1back_native | bikom | 1back | logistic_regression | signal_qc_demographics_vs_qc_demographics | 985 | -0.0324 | -0.0770 | 0.0110 | 1 | 1 |
| group_cv | fnirs_bikom_1back_native | bikom | 1back | random_forest | signal_demographics_vs_demographics | 985 | -0.0482 | -0.0965 | -0.0016 | 1 | 1 |
| group_cv | fnirs_bikom_1back_native | bikom | 1back | random_forest | signal_qc_demographics_vs_qc_demographics | 985 | -0.0460 | -0.0926 | 0.0016 | 1 | 1 |
| group_cv | fnirs_bikom_rest_native | bikom | rest | hist_gradient_boosting | signal_demographics_vs_demographics | 1017 | -0.0835 | -0.1328 | -0.0329 | 0 | 1 |
| group_cv | fnirs_bikom_rest_native | bikom | rest | hist_gradient_boosting | signal_qc_demographics_vs_qc_demographics | 1017 | -0.0693 | -0.1192 | -0.0231 | 1 | 1 |
| group_cv | fnirs_bikom_rest_native | bikom | rest | logistic_regression | signal_demographics_vs_demographics | 1017 | -0.0908 | -0.1314 | -0.0490 | 0 | 1 |
| group_cv | fnirs_bikom_rest_native | bikom | rest | logistic_regression | signal_qc_demographics_vs_qc_demographics | 1017 | -0.0716 | -0.1124 | -0.0271 | 1 | 1 |
| group_cv | fnirs_bikom_rest_native | bikom | rest | random_forest | signal_demographics_vs_demographics | 1017 | -0.0803 | -0.1295 | -0.0317 | 0 | 1 |
| group_cv | fnirs_bikom_rest_native | bikom | rest | random_forest | signal_qc_demographics_vs_qc_demographics | 1017 | -0.0919 | -0.1401 | -0.0468 | 1 | 1 |
| group_cv | fnirs_bikom_vft_native | bikom | vft | hist_gradient_boosting | signal_demographics_vs_demographics | 1022 | -0.0549 | -0.1010 | -0.0096 | 1 | 1 |
| group_cv | fnirs_bikom_vft_native | bikom | vft | hist_gradient_boosting | signal_qc_demographics_vs_qc_demographics | 1022 | -0.0312 | -0.0749 | 0.0116 | 2 | 1 |
| group_cv | fnirs_bikom_vft_native | bikom | vft | logistic_regression | signal_demographics_vs_demographics | 1022 | -0.0221 | -0.0685 | 0.0258 | 0 | 1 |
| group_cv | fnirs_bikom_vft_native | bikom | vft | logistic_regression | signal_qc_demographics_vs_qc_demographics | 1022 | -0.0106 | -0.0535 | 0.0335 | 2 | 1 |
| group_cv | fnirs_bikom_vft_native | bikom | vft | random_forest | signal_demographics_vs_demographics | 1022 | -0.0891 | -0.1341 | -0.0422 | 1 | 1 |
| group_cv | fnirs_bikom_vft_native | bikom | vft | random_forest | signal_qc_demographics_vs_qc_demographics | 1022 | -0.0351 | -0.0834 | 0.0073 | 2 | 1 |
| group_cv | fnirs_yiruid_1back_native | yiruid | 1back | hist_gradient_boosting | signal_demographics_vs_demographics | 1422 | -0.0449 | -0.0782 | -0.0088 | 1 | 1 |
| group_cv | fnirs_yiruid_1back_native | yiruid | 1back | hist_gradient_boosting | signal_qc_demographics_vs_qc_demographics | 1422 | -0.0288 | -0.0625 | 0.0043 | 1 | 1 |
| group_cv | fnirs_yiruid_1back_native | yiruid | 1back | logistic_regression | signal_demographics_vs_demographics | 1422 | -0.0277 | -0.0552 | 0.0026 | 1 | 1 |
| group_cv | fnirs_yiruid_1back_native | yiruid | 1back | logistic_regression | signal_qc_demographics_vs_qc_demographics | 1422 | -0.0324 | -0.0636 | -0.0050 | 1 | 1 |
| group_cv | fnirs_yiruid_1back_native | yiruid | 1back | random_forest | signal_demographics_vs_demographics | 1422 | -0.0808 | -0.1163 | -0.0425 | 1 | 1 |
| group_cv | fnirs_yiruid_1back_native | yiruid | 1back | random_forest | signal_qc_demographics_vs_qc_demographics | 1422 | -0.0645 | -0.0985 | -0.0272 | 0 | 1 |
| group_cv | fnirs_yiruid_rest_native | yiruid | rest | hist_gradient_boosting | signal_demographics_vs_demographics | 1514 | -0.0111 | -0.0405 | 0.0180 | 3 | 1 |
| group_cv | fnirs_yiruid_rest_native | yiruid | rest | hist_gradient_boosting | signal_qc_demographics_vs_qc_demographics | 1514 | -0.0139 | -0.0459 | 0.0232 | 2 | 0 |
| group_cv | fnirs_yiruid_rest_native | yiruid | rest | logistic_regression | signal_demographics_vs_demographics | 1514 | -0.0258 | -0.0547 | 0.0046 | 2 | 1 |
| group_cv | fnirs_yiruid_rest_native | yiruid | rest | logistic_regression | signal_qc_demographics_vs_qc_demographics | 1514 | -0.0237 | -0.0535 | 0.0040 | 2 | 1 |
| group_cv | fnirs_yiruid_rest_native | yiruid | rest | random_forest | signal_demographics_vs_demographics | 1514 | -0.0352 | -0.0672 | -0.0027 | 2 | 1 |
| group_cv | fnirs_yiruid_rest_native | yiruid | rest | random_forest | signal_qc_demographics_vs_qc_demographics | 1514 | -0.0166 | -0.0468 | 0.0136 | 3 | 1 |
| group_cv | fnirs_yiruid_vft_native | yiruid | vft | hist_gradient_boosting | signal_demographics_vs_demographics | 1480 | -0.0075 | -0.0426 | 0.0254 | 3 | 0 |
| group_cv | fnirs_yiruid_vft_native | yiruid | vft | hist_gradient_boosting | signal_qc_demographics_vs_qc_demographics | 1480 | -0.0141 | -0.0497 | 0.0198 | 3 | 1 |
| group_cv | fnirs_yiruid_vft_native | yiruid | vft | logistic_regression | signal_demographics_vs_demographics | 1480 | -0.0075 | -0.0428 | 0.0225 | 3 | 1 |
| group_cv | fnirs_yiruid_vft_native | yiruid | vft | logistic_regression | signal_qc_demographics_vs_qc_demographics | 1480 | -0.0130 | -0.0445 | 0.0203 | 4 | 1 |
| group_cv | fnirs_yiruid_vft_native | yiruid | vft | random_forest | signal_demographics_vs_demographics | 1480 | -0.0001 | -0.0352 | 0.0340 | 4 | 1 |
| group_cv | fnirs_yiruid_vft_native | yiruid | vft | random_forest | signal_qc_demographics_vs_qc_demographics | 1480 | -0.0260 | -0.0584 | 0.0058 | 2 | 1 |
| standard_cv | fnirs_bikom_1back_native | bikom | 1back | hist_gradient_boosting | signal_demographics_vs_demographics | 985 | -0.0670 | -0.1148 | -0.0215 | 0 | 1 |
| standard_cv | fnirs_bikom_1back_native | bikom | 1back | hist_gradient_boosting | signal_qc_demographics_vs_qc_demographics | 985 | -0.0488 | -0.0959 | 0.0030 | 1 | 1 |
| standard_cv | fnirs_bikom_1back_native | bikom | 1back | logistic_regression | signal_demographics_vs_demographics | 985 | -0.0437 | -0.0879 | 0.0022 | 1 | 1 |
| standard_cv | fnirs_bikom_1back_native | bikom | 1back | logistic_regression | signal_qc_demographics_vs_qc_demographics | 985 | -0.0491 | -0.0934 | -0.0056 | 1 | 1 |
| standard_cv | fnirs_bikom_1back_native | bikom | 1back | random_forest | signal_demographics_vs_demographics | 985 | -0.0540 | -0.1037 | -0.0045 | 1 | 1 |
| standard_cv | fnirs_bikom_1back_native | bikom | 1back | random_forest | signal_qc_demographics_vs_qc_demographics | 985 | -0.0506 | -0.0973 | -0.0046 | 1 | 1 |
| standard_cv | fnirs_bikom_rest_native | bikom | rest | hist_gradient_boosting | signal_demographics_vs_demographics | 1017 | -0.0550 | -0.1020 | -0.0091 | 0 | 1 |
| standard_cv | fnirs_bikom_rest_native | bikom | rest | hist_gradient_boosting | signal_qc_demographics_vs_qc_demographics | 1017 | -0.0638 | -0.1113 | -0.0177 | 0 | 1 |
| standard_cv | fnirs_bikom_rest_native | bikom | rest | logistic_regression | signal_demographics_vs_demographics | 1017 | -0.1065 | -0.1507 | -0.0632 | 0 | 1 |
| standard_cv | fnirs_bikom_rest_native | bikom | rest | logistic_regression | signal_qc_demographics_vs_qc_demographics | 1017 | -0.1051 | -0.1460 | -0.0623 | 0 | 1 |
| standard_cv | fnirs_bikom_rest_native | bikom | rest | random_forest | signal_demographics_vs_demographics | 1017 | -0.0654 | -0.1132 | -0.0157 | 0 | 1 |
| standard_cv | fnirs_bikom_rest_native | bikom | rest | random_forest | signal_qc_demographics_vs_qc_demographics | 1017 | -0.0382 | -0.0875 | 0.0082 | 1 | 1 |
| standard_cv | fnirs_bikom_vft_native | bikom | vft | hist_gradient_boosting | signal_demographics_vs_demographics | 1022 | -0.0379 | -0.0830 | 0.0120 | 1 | 1 |
| standard_cv | fnirs_bikom_vft_native | bikom | vft | hist_gradient_boosting | signal_qc_demographics_vs_qc_demographics | 1022 | -0.0228 | -0.0685 | 0.0272 | 2 | 1 |
| standard_cv | fnirs_bikom_vft_native | bikom | vft | logistic_regression | signal_demographics_vs_demographics | 1022 | -0.0684 | -0.1140 | -0.0259 | 0 | 1 |
| standard_cv | fnirs_bikom_vft_native | bikom | vft | logistic_regression | signal_qc_demographics_vs_qc_demographics | 1022 | -0.0712 | -0.1162 | -0.0257 | 0 | 1 |
| standard_cv | fnirs_bikom_vft_native | bikom | vft | random_forest | signal_demographics_vs_demographics | 1022 | -0.0391 | -0.0851 | 0.0091 | 0 | 1 |
| standard_cv | fnirs_bikom_vft_native | bikom | vft | random_forest | signal_qc_demographics_vs_qc_demographics | 1022 | -0.0496 | -0.0954 | -0.0037 | 0 | 1 |
| standard_cv | fnirs_yiruid_1back_native | yiruid | 1back | hist_gradient_boosting | signal_demographics_vs_demographics | 1422 | -0.0382 | -0.0730 | -0.0047 | 0 | 1 |
| standard_cv | fnirs_yiruid_1back_native | yiruid | 1back | hist_gradient_boosting | signal_qc_demographics_vs_qc_demographics | 1422 | -0.0318 | -0.0642 | 0.0004 | 1 | 1 |
| standard_cv | fnirs_yiruid_1back_native | yiruid | 1back | logistic_regression | signal_demographics_vs_demographics | 1422 | -0.0269 | -0.0560 | 0.0021 | 1 | 1 |
| standard_cv | fnirs_yiruid_1back_native | yiruid | 1back | logistic_regression | signal_qc_demographics_vs_qc_demographics | 1422 | -0.0280 | -0.0586 | 0.0033 | 1 | 1 |
| standard_cv | fnirs_yiruid_1back_native | yiruid | 1back | random_forest | signal_demographics_vs_demographics | 1422 | -0.0419 | -0.0773 | -0.0048 | 1 | 1 |
| standard_cv | fnirs_yiruid_1back_native | yiruid | 1back | random_forest | signal_qc_demographics_vs_qc_demographics | 1422 | -0.0253 | -0.0572 | 0.0067 | 1 | 1 |
