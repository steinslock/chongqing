# Goal 2.6 fNIRS Results

Protocol: fixed `split_group == cv` only; subject-level OOF predictions; 3-fold inner CV for hyperparameters and thresholds; baseline-exposed pilot holdout excluded throughout.

## Feature Extraction

| cohort_name | modality | device | task | feature_set | n_subjects | feature_count | numeric_count | categorical_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fnirs_yiruid_rest_native | fnirs | yiruid | rest | no_information | 1514 | 0 | 0 | 0 |
| fnirs_yiruid_rest_native | fnirs | yiruid | rest | demographics | 1514 | 4 | 1 | 3 |
| fnirs_yiruid_rest_native | fnirs | yiruid | rest | qc | 1514 | 17 | 17 | 0 |
| fnirs_yiruid_rest_native | fnirs | yiruid | rest | signal | 1514 | 281 | 281 | 0 |
| fnirs_yiruid_rest_native | fnirs | yiruid | rest | signal_qc | 1514 | 298 | 298 | 0 |
| fnirs_yiruid_rest_native | fnirs | yiruid | rest | signal_demographics | 1514 | 285 | 282 | 3 |
| fnirs_yiruid_rest_native | fnirs | yiruid | rest | signal_qc_demographics | 1514 | 302 | 299 | 3 |
| fnirs_yiruid_vft_native | fnirs | yiruid | vft | no_information | 1480 | 0 | 0 | 0 |
| fnirs_yiruid_vft_native | fnirs | yiruid | vft | demographics | 1480 | 4 | 1 | 3 |
| fnirs_yiruid_vft_native | fnirs | yiruid | vft | qc | 1480 | 17 | 17 | 0 |
| fnirs_yiruid_vft_native | fnirs | yiruid | vft | signal | 1480 | 289 | 289 | 0 |
| fnirs_yiruid_vft_native | fnirs | yiruid | vft | signal_qc | 1480 | 306 | 306 | 0 |
| fnirs_yiruid_vft_native | fnirs | yiruid | vft | signal_demographics | 1480 | 293 | 290 | 3 |
| fnirs_yiruid_vft_native | fnirs | yiruid | vft | signal_qc_demographics | 1480 | 310 | 307 | 3 |
| fnirs_yiruid_1back_native | fnirs | yiruid | 1back | no_information | 1422 | 0 | 0 | 0 |
| fnirs_yiruid_1back_native | fnirs | yiruid | 1back | demographics | 1422 | 4 | 1 | 3 |
| fnirs_yiruid_1back_native | fnirs | yiruid | 1back | qc | 1422 | 16 | 16 | 0 |
| fnirs_yiruid_1back_native | fnirs | yiruid | 1back | signal | 1422 | 289 | 289 | 0 |
| fnirs_yiruid_1back_native | fnirs | yiruid | 1back | signal_qc | 1422 | 305 | 305 | 0 |
| fnirs_yiruid_1back_native | fnirs | yiruid | 1back | signal_demographics | 1422 | 293 | 290 | 3 |
| fnirs_yiruid_1back_native | fnirs | yiruid | 1back | signal_qc_demographics | 1422 | 309 | 306 | 3 |
| fnirs_bikom_rest_native | fnirs | bikom | rest | no_information | 1017 | 0 | 0 | 0 |
| fnirs_bikom_rest_native | fnirs | bikom | rest | demographics | 1017 | 4 | 1 | 3 |
| fnirs_bikom_rest_native | fnirs | bikom | rest | qc | 1017 | 18 | 18 | 0 |
| fnirs_bikom_rest_native | fnirs | bikom | rest | signal | 1017 | 380 | 380 | 0 |
| fnirs_bikom_rest_native | fnirs | bikom | rest | signal_qc | 1017 | 398 | 398 | 0 |
| fnirs_bikom_rest_native | fnirs | bikom | rest | signal_demographics | 1017 | 384 | 381 | 3 |
| fnirs_bikom_rest_native | fnirs | bikom | rest | signal_qc_demographics | 1017 | 402 | 399 | 3 |
| fnirs_bikom_vft_native | fnirs | bikom | vft | no_information | 1022 | 0 | 0 | 0 |
| fnirs_bikom_vft_native | fnirs | bikom | vft | demographics | 1022 | 4 | 1 | 3 |
| fnirs_bikom_vft_native | fnirs | bikom | vft | qc | 1022 | 18 | 18 | 0 |
| fnirs_bikom_vft_native | fnirs | bikom | vft | signal | 1022 | 396 | 396 | 0 |
| fnirs_bikom_vft_native | fnirs | bikom | vft | signal_qc | 1022 | 414 | 414 | 0 |
| fnirs_bikom_vft_native | fnirs | bikom | vft | signal_demographics | 1022 | 400 | 397 | 3 |
| fnirs_bikom_vft_native | fnirs | bikom | vft | signal_qc_demographics | 1022 | 418 | 415 | 3 |
| fnirs_bikom_1back_native | fnirs | bikom | 1back | no_information | 985 | 0 | 0 | 0 |
| fnirs_bikom_1back_native | fnirs | bikom | 1back | demographics | 985 | 4 | 1 | 3 |
| fnirs_bikom_1back_native | fnirs | bikom | 1back | qc | 985 | 17 | 17 | 0 |
| fnirs_bikom_1back_native | fnirs | bikom | 1back | signal | 985 | 396 | 396 | 0 |
| fnirs_bikom_1back_native | fnirs | bikom | 1back | signal_qc | 985 | 413 | 413 | 0 |

Yiruid features use validated `.nirs` raw/log-intensity and OD-like summaries; the report does not claim formal HbO/HbR conversion for Yiruid. Bikom features use vendor CSV HbO/HbR/HbT channels with the configured row cap recorded in QC.

## Native-Cohort Performance

| cohort_name | device | task | feature_set | model | n_subjects | auroc | auprc | balanced_accuracy | macro_f1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fnirs_bikom_1back_native | bikom | 1back | demographics | logistic_regression | 985 | 0.6258 | 0.4395 | 0.5903 | 0.5905 |
| fnirs_bikom_rest_native | bikom | rest | demographics | logistic_regression | 1017 | 0.6243 | 0.4360 | 0.5842 | 0.5843 |
| fnirs_bikom_vft_native | bikom | vft | demographics | logistic_regression | 1022 | 0.6212 | 0.4261 | 0.5788 | 0.5638 |
| fnirs_bikom_vft_native | bikom | vft | demographics | random_forest | 1022 | 0.6046 | 0.4105 | 0.5702 | 0.5506 |
| fnirs_bikom_1back_native | bikom | 1back | demographics | random_forest | 985 | 0.6046 | 0.4065 | 0.5735 | 0.5304 |
| fnirs_bikom_rest_native | bikom | rest | demographics | hist_gradient_boosting | 1017 | 0.6034 | 0.4018 | 0.5839 | 0.5590 |
| fnirs_bikom_1back_native | bikom | 1back | demographics | hist_gradient_boosting | 985 | 0.6020 | 0.3989 | 0.5801 | 0.5571 |
| fnirs_bikom_rest_native | bikom | rest | demographics | random_forest | 1017 | 0.6017 | 0.4091 | 0.5613 | 0.5451 |
| fnirs_bikom_vft_native | bikom | vft | demographics | hist_gradient_boosting | 1022 | 0.6013 | 0.4008 | 0.5831 | 0.5583 |
| fnirs_yiruid_rest_native | yiruid | rest | demographics | random_forest | 1514 | 0.5924 | 0.4498 | 0.5630 | 0.5439 |
| fnirs_yiruid_vft_native | yiruid | vft | signal_qc | random_forest | 1480 | 0.5908 | 0.4684 | 0.5603 | 0.5593 |
| fnirs_yiruid_vft_native | yiruid | vft | signal_demographics | random_forest | 1480 | 0.5903 | 0.4729 | 0.5750 | 0.5704 |
| fnirs_yiruid_rest_native | yiruid | rest | demographics | logistic_regression | 1514 | 0.5898 | 0.4426 | 0.5724 | 0.5265 |
| fnirs_yiruid_rest_native | yiruid | rest | signal_demographics | hist_gradient_boosting | 1514 | 0.5882 | 0.4630 | 0.5587 | 0.5497 |
| fnirs_yiruid_rest_native | yiruid | rest | signal_qc_demographics | hist_gradient_boosting | 1514 | 0.5882 | 0.4630 | 0.5587 | 0.5497 |

## Device/Task Notes

| device | task | n_subjects | best_feature_set | best_model | best_auroc | best_auprc |
| --- | --- | --- | --- | --- | --- | --- |
| bikom | 1back | 985 | demographics | logistic_regression | 0.6258 | 0.4395 |
| bikom | rest | 1017 | demographics | logistic_regression | 0.6243 | 0.4360 |
| bikom | vft | 1022 | demographics | logistic_regression | 0.6212 | 0.4261 |
| yiruid | 1back | 1422 | demographics | logistic_regression | 0.5859 | 0.4399 |
| yiruid | rest | 1514 | demographics | random_forest | 0.5924 | 0.4498 |
| yiruid | vft | 1480 | signal_qc | random_forest | 0.5908 | 0.4684 |

## Status

fNIRS: best AUROC `0.6258` from `fnirs_bikom_1back_native` / `demographics` / `logistic_regression` on `985` subjects.
