# Goal 2.6 Final Report

Protocol: fixed `split_group == cv` only; subject-level OOF predictions; 3-fold inner CV for hyperparameters and thresholds; baseline-exposed pilot holdout excluded throughout.

## Executive Summary

- eeg: best native/core row `eeg_oddball_native` `demographics` `logistic_regression` with AUROC `0.6024` and AUPRC `0.4242` on `1827` subjects.
- fnirs: best native/core row `fnirs_bikom_1back_native` `demographics` `logistic_regression` with AUROC `0.6258` and AUPRC `0.4395` on `985` subjects.
- face: best native/core row `face_self_intro_native` `demographics` `logistic_regression` with AUROC `0.6702` and AUPRC `0.4305` on `3572` subjects.

## Best Native Results

| modality | cohort_name | device | task | feature_set | model | n_subjects | auroc | auprc | balanced_accuracy | macro_f1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| eeg | eeg_oddball_native |  | oddball | demographics | logistic_regression | 1827 | 0.6024 | 0.4242 | 0.5869 | 0.5645 |
| face | face_self_intro_native |  | self_intro | demographics | logistic_regression | 3572 | 0.6702 | 0.4305 | 0.6205 | 0.5918 |
| fnirs | fnirs_bikom_1back_native | bikom | 1back | demographics | logistic_regression | 985 | 0.6258 | 0.4395 | 0.5903 | 0.5905 |

## Feature Coverage

| cohort_name | modality | device | task | feature_set | n_subjects | feature_count |
| --- | --- | --- | --- | --- | --- | --- |
| eeg_rest_native | eeg |  | rest | no_information | 1022 | 0 |
| eeg_rest_native | eeg |  | rest | demographics | 1022 | 4 |
| eeg_rest_native | eeg |  | rest | qc | 1022 | 16 |
| eeg_rest_native | eeg |  | rest | signal | 1022 | 217 |
| eeg_rest_native | eeg |  | rest | signal_qc | 1022 | 233 |
| eeg_rest_native | eeg |  | rest | signal_demographics | 1022 | 221 |
| eeg_rest_native | eeg |  | rest | signal_qc_demographics | 1022 | 237 |
| eeg_oddball_native | eeg |  | oddball | no_information | 1827 | 0 |
| eeg_oddball_native | eeg |  | oddball | demographics | 1827 | 4 |
| eeg_oddball_native | eeg |  | oddball | qc | 1827 | 16 |
| eeg_oddball_native | eeg |  | oddball | signal | 1827 | 231 |
| eeg_oddball_native | eeg |  | oddball | signal_qc | 1827 | 247 |
| eeg_oddball_native | eeg |  | oddball | signal_demographics | 1827 | 235 |
| eeg_oddball_native | eeg |  | oddball | signal_qc_demographics | 1827 | 251 |
| eeg_1back_native | eeg |  | 1back | no_information | 1154 | 0 |
| eeg_1back_native | eeg |  | 1back | demographics | 1154 | 4 |
| eeg_1back_native | eeg |  | 1back | qc | 1154 | 16 |
| eeg_1back_native | eeg |  | 1back | signal | 1154 | 246 |
| eeg_1back_native | eeg |  | 1back | signal_qc | 1154 | 262 |
| eeg_1back_native | eeg |  | 1back | signal_demographics | 1154 | 250 |
| eeg_1back_native | eeg |  | 1back | signal_qc_demographics | 1154 | 266 |
| eeg_rest_v1_features_fixed_split | eeg |  | rest_v1_control | signal | 999 | 527 |
| eeg_rest_v1_features_fixed_split | eeg |  | rest_v1_control | demographics | 999 | 4 |
| fnirs_yiruid_rest_native | fnirs | yiruid | rest | no_information | 1514 | 0 |
| fnirs_yiruid_rest_native | fnirs | yiruid | rest | demographics | 1514 | 4 |
| fnirs_yiruid_rest_native | fnirs | yiruid | rest | qc | 1514 | 17 |
| fnirs_yiruid_rest_native | fnirs | yiruid | rest | signal | 1514 | 281 |
| fnirs_yiruid_rest_native | fnirs | yiruid | rest | signal_qc | 1514 | 298 |
| fnirs_yiruid_rest_native | fnirs | yiruid | rest | signal_demographics | 1514 | 285 |
| fnirs_yiruid_rest_native | fnirs | yiruid | rest | signal_qc_demographics | 1514 | 302 |
| fnirs_yiruid_vft_native | fnirs | yiruid | vft | no_information | 1480 | 0 |
| fnirs_yiruid_vft_native | fnirs | yiruid | vft | demographics | 1480 | 4 |
| fnirs_yiruid_vft_native | fnirs | yiruid | vft | qc | 1480 | 17 |
| fnirs_yiruid_vft_native | fnirs | yiruid | vft | signal | 1480 | 289 |
| fnirs_yiruid_vft_native | fnirs | yiruid | vft | signal_qc | 1480 | 306 |
| fnirs_yiruid_vft_native | fnirs | yiruid | vft | signal_demographics | 1480 | 293 |
| fnirs_yiruid_vft_native | fnirs | yiruid | vft | signal_qc_demographics | 1480 | 310 |
| fnirs_yiruid_1back_native | fnirs | yiruid | 1back | no_information | 1422 | 0 |
| fnirs_yiruid_1back_native | fnirs | yiruid | 1back | demographics | 1422 | 4 |
| fnirs_yiruid_1back_native | fnirs | yiruid | 1back | qc | 1422 | 16 |
| fnirs_yiruid_1back_native | fnirs | yiruid | 1back | signal | 1422 | 289 |
| fnirs_yiruid_1back_native | fnirs | yiruid | 1back | signal_qc | 1422 | 305 |
| fnirs_yiruid_1back_native | fnirs | yiruid | 1back | signal_demographics | 1422 | 293 |
| fnirs_yiruid_1back_native | fnirs | yiruid | 1back | signal_qc_demographics | 1422 | 309 |
| fnirs_bikom_rest_native | fnirs | bikom | rest | no_information | 1017 | 0 |
| fnirs_bikom_rest_native | fnirs | bikom | rest | demographics | 1017 | 4 |
| fnirs_bikom_rest_native | fnirs | bikom | rest | qc | 1017 | 18 |
| fnirs_bikom_rest_native | fnirs | bikom | rest | signal | 1017 | 380 |
| fnirs_bikom_rest_native | fnirs | bikom | rest | signal_qc | 1017 | 398 |
| fnirs_bikom_rest_native | fnirs | bikom | rest | signal_demographics | 1017 | 384 |
| fnirs_bikom_rest_native | fnirs | bikom | rest | signal_qc_demographics | 1017 | 402 |
| fnirs_bikom_vft_native | fnirs | bikom | vft | no_information | 1022 | 0 |
| fnirs_bikom_vft_native | fnirs | bikom | vft | demographics | 1022 | 4 |
| fnirs_bikom_vft_native | fnirs | bikom | vft | qc | 1022 | 18 |
| fnirs_bikom_vft_native | fnirs | bikom | vft | signal | 1022 | 396 |
| fnirs_bikom_vft_native | fnirs | bikom | vft | signal_qc | 1022 | 414 |
| fnirs_bikom_vft_native | fnirs | bikom | vft | signal_demographics | 1022 | 400 |
| fnirs_bikom_vft_native | fnirs | bikom | vft | signal_qc_demographics | 1022 | 418 |
| fnirs_bikom_1back_native | fnirs | bikom | 1back | no_information | 985 | 0 |
| fnirs_bikom_1back_native | fnirs | bikom | 1back | demographics | 985 | 4 |
| fnirs_bikom_1back_native | fnirs | bikom | 1back | qc | 985 | 17 |
| fnirs_bikom_1back_native | fnirs | bikom | 1back | signal | 985 | 396 |
| fnirs_bikom_1back_native | fnirs | bikom | 1back | signal_qc | 985 | 413 |
| fnirs_bikom_1back_native | fnirs | bikom | 1back | signal_demographics | 985 | 400 |
| fnirs_bikom_1back_native | fnirs | bikom | 1back | signal_qc_demographics | 985 | 417 |
| face_self_intro_native | face |  | self_intro | no_information | 3572 | 0 |
| face_self_intro_native | face |  | self_intro | demographics | 3572 | 4 |
| face_self_intro_native | face |  | self_intro | qc | 3572 | 20 |
| face_self_intro_native | face |  | self_intro | metadata | 3572 | 6 |
| face_self_intro_native | face |  | self_intro | full_frame | 3572 | 1024 |
| face_self_intro_native | face |  | self_intro | face_crop | 3572 | 1024 |
| face_self_intro_native | face |  | self_intro | background | 3572 | 1024 |
| face_self_intro_native | face |  | self_intro | face_qc | 3572 | 1044 |
| face_self_intro_native | face |  | self_intro | face_demographics | 3572 | 1028 |
| face_self_intro_native | face |  | self_intro | face_qc_demographics | 3572 | 1048 |
| face_task_native | face |  | task | no_information | 3567 | 0 |
| face_task_native | face |  | task | demographics | 3567 | 4 |
| face_task_native | face |  | task | qc | 3567 | 20 |
| face_task_native | face |  | task | metadata | 3567 | 6 |
| face_task_native | face |  | task | full_frame | 3567 | 1024 |
| face_task_native | face |  | task | face_crop | 3567 | 1024 |
| face_task_native | face |  | task | background | 3567 | 1024 |
| face_task_native | face |  | task | face_qc | 3567 | 1044 |
| face_task_native | face |  | task | face_demographics | 3567 | 1028 |
| face_task_native | face |  | task | face_qc_demographics | 3567 | 1048 |
| face_two_video_native | face |  | two_video | no_information | 3567 | 0 |
| face_two_video_native | face |  | two_video | demographics | 3567 | 4 |
| face_two_video_native | face |  | two_video | qc | 3567 | 40 |
| face_two_video_native | face |  | two_video | metadata | 3567 | 12 |
| face_two_video_native | face |  | two_video | full_frame | 3567 | 2048 |
| face_two_video_native | face |  | two_video | face_crop | 3567 | 2048 |
| face_two_video_native | face |  | two_video | background | 3567 | 2048 |
| face_two_video_native | face |  | two_video | face_qc | 3567 | 2088 |
| face_two_video_native | face |  | two_video | face_demographics | 3567 | 2052 |
| face_two_video_native | face |  | two_video | face_qc_demographics | 3567 | 2092 |
| core3_same_cohort | eeg |  | rest | demographics | 661 | 4 |
| core3_same_cohort | eeg |  | rest | modality | 661 | 217 |
| core3_same_cohort | eeg |  | rest | modality_demographics | 661 | 221 |
| core3_same_cohort | fnirs | yiruid | vft | demographics | 661 | 4 |
| core3_same_cohort | fnirs | yiruid | vft | modality | 661 | 289 |
| core3_same_cohort | fnirs | yiruid | vft | modality_demographics | 661 | 293 |
| core3_same_cohort | face |  | self_intro | demographics | 661 | 4 |
| core3_same_cohort | face |  | self_intro | modality | 661 | 1024 |
| core3_same_cohort | face |  | self_intro | modality_demographics | 661 | 1028 |
| shortcut_a_prefix_group_cv | shortcut |  | a_prefix_group | group_device | 3597 | 5 |

## Paired Bootstrap

| cohort_name | modality | task | model | model_a | model_b | n_subjects | auroc_diff | auroc_diff_ci_low | auroc_diff_ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| core3_same_cohort | eeg | rest | hist_gradient_boosting | modality | demographics | 661 | -0.0637 | -0.1299 | 0.0004 |
| core3_same_cohort | eeg | rest | hist_gradient_boosting | modality_demographics | modality | 661 | 0.0042 | -0.0194 | 0.0273 |
| core3_same_cohort | eeg | rest | logistic_regression | modality | demographics | 661 | -0.0611 | -0.1251 | -0.0006 |
| core3_same_cohort | eeg | rest | logistic_regression | modality_demographics | modality | 661 | 0.0390 | 0.0126 | 0.0642 |
| core3_same_cohort | eeg | rest | random_forest | modality | demographics | 661 | -0.0578 | -0.1212 | 0.0073 |
| core3_same_cohort | eeg | rest | random_forest | modality_demographics | modality | 661 | 0.0118 | -0.0174 | 0.0399 |
| core3_same_cohort | face | self_intro | hist_gradient_boosting | modality | demographics | 661 | -0.0006 | -0.0602 | 0.0548 |
| core3_same_cohort | face | self_intro | hist_gradient_boosting | modality_demographics | modality | 661 | -0.0112 | -0.0459 | 0.0222 |
| core3_same_cohort | face | self_intro | logistic_regression | modality | demographics | 661 | -0.0084 | -0.0638 | 0.0493 |
| core3_same_cohort | face | self_intro | logistic_regression | modality_demographics | modality | 661 | 0.0033 | -0.0003 | 0.0069 |
| core3_same_cohort | fnirs | vft | hist_gradient_boosting | modality | demographics | 661 | -0.0023 | -0.0613 | 0.0512 |
| core3_same_cohort | fnirs | vft | hist_gradient_boosting | modality_demographics | modality | 661 | 0.0000 | 0.0000 | 0.0000 |
| core3_same_cohort | fnirs | vft | logistic_regression | modality | demographics | 661 | -0.0455 | -0.1069 | 0.0119 |
| core3_same_cohort | fnirs | vft | logistic_regression | modality_demographics | modality | 661 | 0.0036 | -0.0055 | 0.0137 |
| core3_same_cohort | fnirs | vft | random_forest | modality | demographics | 661 | 0.0251 | -0.0299 | 0.0845 |
| core3_same_cohort | fnirs | vft | random_forest | modality_demographics | modality | 661 | -0.0056 | -0.0265 | 0.0149 |
| eeg_1back_native | eeg | 1back | hist_gradient_boosting | signal | demographics | 1154 | -0.0651 | -0.1116 | -0.0191 |
| eeg_1back_native | eeg | 1back | hist_gradient_boosting | signal | qc | 1154 | 0.0281 | -0.0163 | 0.0732 |
| eeg_1back_native | eeg | 1back | hist_gradient_boosting | signal_qc_demographics | signal | 1154 | 0.0242 | -0.0005 | 0.0495 |
| eeg_1back_native | eeg | 1back | logistic_regression | signal | demographics | 1154 | -0.1060 | -0.1536 | -0.0596 |
| eeg_1back_native | eeg | 1back | logistic_regression | signal | qc | 1154 | -0.0476 | -0.0947 | -0.0012 |
| eeg_1back_native | eeg | 1back | logistic_regression | signal_qc_demographics | signal | 1154 | 0.0391 | 0.0197 | 0.0619 |
| eeg_1back_native | eeg | 1back | random_forest | signal | demographics | 1154 | -0.0616 | -0.1120 | -0.0139 |
| eeg_1back_native | eeg | 1back | random_forest | signal | qc | 1154 | 0.0151 | -0.0312 | 0.0587 |
| eeg_1back_native | eeg | 1back | random_forest | signal_qc_demographics | signal | 1154 | 0.0145 | -0.0117 | 0.0411 |
| eeg_oddball_native | eeg | oddball | hist_gradient_boosting | signal | demographics | 1827 | -0.0757 | -0.1154 | -0.0357 |
| eeg_oddball_native | eeg | oddball | hist_gradient_boosting | signal | qc | 1827 | 0.0458 | 0.0103 | 0.0860 |
| eeg_oddball_native | eeg | oddball | hist_gradient_boosting | signal_qc_demographics | signal | 1827 | 0.0633 | 0.0308 | 0.0951 |
| eeg_oddball_native | eeg | oddball | logistic_regression | signal | demographics | 1827 | -0.0578 | -0.0908 | -0.0215 |
| eeg_oddball_native | eeg | oddball | logistic_regression | signal | qc | 1827 | 0.0438 | 0.0051 | 0.0820 |

## PCA Diagnostics

| cohort_name | modality | task | feature_set | model | folds | pca_n_components | explained_variance_mean | explained_variance_min |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| core3_same_cohort | face | self_intro | modality | hist_gradient_boosting | 5 | 64.0000 | 0.7103 | 0.7089 |
| core3_same_cohort | face | self_intro | modality | logistic_regression | 5 | 64.0000 | 0.7103 | 0.7089 |
| core3_same_cohort | face | self_intro | modality_demographics | hist_gradient_boosting | 5 | 64.0000 | 0.7096 | 0.7082 |
| core3_same_cohort | face | self_intro | modality_demographics | logistic_regression | 5 | 64.0000 | 0.7096 | 0.7082 |
| face_self_intro_native | face | self_intro | background | hist_gradient_boosting | 5 | 64.0000 | 0.6316 | 0.6308 |
| face_self_intro_native | face | self_intro | background | logistic_regression | 5 | 64.0000 | 0.6316 | 0.6308 |
| face_self_intro_native | face | self_intro | face_crop | hist_gradient_boosting | 5 | 64.0000 | 0.6428 | 0.6421 |
| face_self_intro_native | face | self_intro | face_crop | logistic_regression | 5 | 64.0000 | 0.6428 | 0.6421 |
| face_self_intro_native | face | self_intro | face_demographics | hist_gradient_boosting | 5 | 64.0000 | 0.6419 | 0.6413 |
| face_self_intro_native | face | self_intro | face_demographics | logistic_regression | 5 | 64.0000 | 0.6419 | 0.6413 |
| face_self_intro_native | face | self_intro | face_qc | hist_gradient_boosting | 5 | 64.0000 | 0.6384 | 0.6383 |
| face_self_intro_native | face | self_intro | face_qc | logistic_regression | 5 | 64.0000 | 0.6384 | 0.6383 |
| face_self_intro_native | face | self_intro | face_qc_demographics | hist_gradient_boosting | 5 | 64.0000 | 0.6376 | 0.6375 |
| face_self_intro_native | face | self_intro | face_qc_demographics | logistic_regression | 5 | 64.0000 | 0.6376 | 0.6375 |
| face_self_intro_native | face | self_intro | full_frame | hist_gradient_boosting | 5 | 64.0000 | 0.6318 | 0.6310 |
| face_self_intro_native | face | self_intro | full_frame | logistic_regression | 5 | 64.0000 | 0.6318 | 0.6310 |
| face_task_native | face | task | background | hist_gradient_boosting | 5 | 64.0000 | 0.6294 | 0.6285 |
| face_task_native | face | task | background | logistic_regression | 5 | 64.0000 | 0.6294 | 0.6285 |
| face_task_native | face | task | face_crop | hist_gradient_boosting | 5 | 64.0000 | 0.6392 | 0.6384 |
| face_task_native | face | task | face_crop | logistic_regression | 5 | 64.0000 | 0.6392 | 0.6384 |
| face_task_native | face | task | face_demographics | hist_gradient_boosting | 5 | 64.0000 | 0.6384 | 0.6376 |
| face_task_native | face | task | face_demographics | logistic_regression | 5 | 64.0000 | 0.6384 | 0.6376 |
| face_task_native | face | task | face_qc | hist_gradient_boosting | 5 | 64.0000 | 0.6355 | 0.6346 |
| face_task_native | face | task | face_qc | logistic_regression | 5 | 64.0000 | 0.6355 | 0.6346 |
| face_task_native | face | task | face_qc_demographics | hist_gradient_boosting | 5 | 64.0000 | 0.6347 | 0.6338 |
| face_task_native | face | task | face_qc_demographics | logistic_regression | 5 | 64.0000 | 0.6347 | 0.6338 |
| face_task_native | face | task | full_frame | hist_gradient_boosting | 5 | 64.0000 | 0.6300 | 0.6291 |
| face_task_native | face | task | full_frame | logistic_regression | 5 | 64.0000 | 0.6300 | 0.6291 |
| face_two_video_native | face | two_video | background | hist_gradient_boosting | 5 | 64.0000 | 0.5958 | 0.5950 |
| face_two_video_native | face | two_video | background | logistic_regression | 5 | 64.0000 | 0.5958 | 0.5950 |
| face_two_video_native | face | two_video | face_crop | hist_gradient_boosting | 5 | 64.0000 | 0.6075 | 0.6071 |
| face_two_video_native | face | two_video | face_crop | logistic_regression | 5 | 64.0000 | 0.6075 | 0.6071 |
| face_two_video_native | face | two_video | face_demographics | hist_gradient_boosting | 5 | 64.0000 | 0.6072 | 0.6067 |
| face_two_video_native | face | two_video | face_demographics | logistic_regression | 5 | 64.0000 | 0.6072 | 0.6067 |
| face_two_video_native | face | two_video | face_qc | hist_gradient_boosting | 5 | 64.0000 | 0.6034 | 0.6028 |
| face_two_video_native | face | two_video | face_qc | logistic_regression | 5 | 64.0000 | 0.6034 | 0.6028 |
| face_two_video_native | face | two_video | face_qc_demographics | hist_gradient_boosting | 5 | 64.0000 | 0.6031 | 0.6025 |
| face_two_video_native | face | two_video | face_qc_demographics | logistic_regression | 5 | 64.0000 | 0.6031 | 0.6025 |
| face_two_video_native | face | two_video | full_frame | hist_gradient_boosting | 5 | 64.0000 | 0.6042 | 0.6033 |
| face_two_video_native | face | two_video | full_frame | logistic_regression | 5 | 64.0000 | 0.6042 | 0.6033 |

## Group Robustness

| cohort_name | modality | task | feature_set | model | n_subjects | auroc | auprc | balanced_accuracy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| eeg_oddball_native_group_robustness | eeg | oddball | signal_demographics | hist_gradient_boosting | 1827 | 0.5892 | 0.3950 | 0.5717 |
| eeg_oddball_native_group_robustness | eeg | oddball | signal_demographics | logistic_regression | 1827 | 0.5600 | 0.3970 | 0.5411 |
| eeg_oddball_native_group_robustness | eeg | oddball | signal_demographics | random_forest | 1827 | 0.5101 | 0.3339 | 0.5104 |
| face_task_native_group_robustness | face | task | face_demographics | hist_gradient_boosting | 3567 | 0.5952 | 0.3636 | 0.5740 |
| face_task_native_group_robustness | face | task | face_demographics | logistic_regression | 3567 | 0.6197 | 0.3961 | 0.5797 |
| face_two_video_native_group_robustness | face | two_video | face_demographics | hist_gradient_boosting | 3567 | 0.6056 | 0.3717 | 0.5959 |
| face_two_video_native_group_robustness | face | two_video | face_demographics | logistic_regression | 3567 | 0.6247 | 0.4019 | 0.5835 |
| fnirs_yiruid_vft_native_group_robustness | fnirs | vft | signal_qc | hist_gradient_boosting | 1480 | 0.5840 | 0.4646 | 0.5638 |
| fnirs_yiruid_vft_native_group_robustness | fnirs | vft | signal_qc | logistic_regression | 1480 | 0.5700 | 0.4354 | 0.5518 |
| fnirs_yiruid_vft_native_group_robustness | fnirs | vft | signal_qc | random_forest | 1480 | 0.5470 | 0.4365 | 0.5290 |
| shortcut_a_prefix_group_cv_group_robustness | shortcut | a_prefix_group | group_device | hist_gradient_boosting | 3597 | 0.6023 | 0.3673 | 0.5817 |
| shortcut_a_prefix_group_cv_group_robustness | shortcut | a_prefix_group | group_device | logistic_regression | 3597 | 0.4890 | 0.3243 | 0.5339 |
| shortcut_a_prefix_group_cv_group_robustness | shortcut | a_prefix_group | group_device | random_forest | 3597 | 0.5906 | 0.3640 | 0.5492 |

## Exclusions And QC

| modality | qc_feature_status | qc_failure_reason | subjects |
| --- | --- | --- | --- |
| eeg | blocked | too_few_valid_windows | 11 |
| eeg | ok |  | 1022 |
| eeg | blocked | too_few_valid_windows | 10 |
| eeg | ok |  | 1827 |
| eeg | blocked | too_few_valid_windows | 191 |
| eeg | ok |  | 1154 |
| fnirs | ok |  | 1514 |
| fnirs | ok |  | 1480 |
| fnirs | blocked | OSError:could not read bytes | 1 |
| fnirs | ok |  | 1422 |
| fnirs | ok |  | 1017 |
| fnirs | ok |  | 1022 |
| fnirs | blocked | missing_hbo_or_hbr_csv | 10 |
| fnirs | ok |  | 985 |
| face | blocked | video_file_missing | 25 |
| face | ok |  | 3572 |
| face | blocked | video_file_missing | 30 |
| face | ok |  | 3567 |

## Final Modality Status

- EEG: `WEAK_OR_UNCERTAIN_SIGNAL`. Best signal-like AUROC is `0.5873`; signal improves over QC in some paired tests but does not beat demographics robustly.
- fNIRS: `WEAK_OR_UNCERTAIN_SIGNAL`. Best signal-like AUROC is `0.5908`; device/task evidence is positive but still modest and device-specific.
- Face: `SHORTCUT_RISK`. Best face signal-like AUROC is `0.6458`, but background-only reaches `0.6230` and group/device shortcut reaches `0.6778`.

## Recommended Next Goal

Proceed to Goal 3 EEG formal single-modality modeling with the fixed-CV protocol, using the Goal 2.6 EEG native/cohort results as the tabular baseline. In parallel, keep Face shortcut mitigation and fNIRS Hb/event validation as prerequisites before stronger deep models.
