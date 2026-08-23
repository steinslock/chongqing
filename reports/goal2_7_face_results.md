# Goal 2.7 Face Results

## Strict Detection/QC Summary

| task | n_videos | strict_face_valid_videos | blocked_videos | mean_detection_rate | mean_effective_face_frames | fallback_videos | multi_face_rate_mean | audio_used_sum |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| self_intro | 3597 | 3565 | 32 | 0.9904 | 15.8365 | 3572 | 0.0234 | 0 |
| task | 3597 | 3558 | 39 | 0.9831 | 15.7199 | 3567 | 0.0217 | 0 |

## Best Inner-CV Rows

| cv_protocol | cohort_name | task | feature_set | model | n_subjects | auroc | auprc | balanced_accuracy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| standard_cv | face_self_intro_native | self_intro | demographics_group | logistic_regression | 3572 | 0.7083 | 0.4955 | 0.6543 |
| standard_cv | face_self_intro_native | self_intro | demographics_group_device | logistic_regression | 3572 | 0.7073 | 0.4969 | 0.6559 |
| standard_cv | face_task_native | task | demographics_group | logistic_regression | 3567 | 0.7070 | 0.4928 | 0.6523 |
| standard_cv | face_task_native | task | demographics_group_device | logistic_regression | 3567 | 0.7066 | 0.4916 | 0.6556 |
| standard_cv | face_self_intro_native | self_intro | demographics_group_device | hist_gradient_boosting | 3572 | 0.7058 | 0.4780 | 0.6477 |
| standard_cv | face_task_native | task | demographics_group_device | hist_gradient_boosting | 3567 | 0.7057 | 0.4791 | 0.6458 |
| standard_cv | face_task_native | task | demographics_group | hist_gradient_boosting | 3567 | 0.7054 | 0.4779 | 0.6465 |
| standard_cv | face_self_intro_native | self_intro | demographics_group_device | random_forest | 3572 | 0.7052 | 0.4821 | 0.6542 |
| standard_cv | face_self_intro_native | self_intro | demographics_group | hist_gradient_boosting | 3572 | 0.7052 | 0.4798 | 0.6531 |
| standard_cv | face_self_intro_native | self_intro | demographics_group | random_forest | 3572 | 0.7051 | 0.4843 | 0.6452 |
| standard_cv | face_task_native | task | demographics_group | random_forest | 3567 | 0.7035 | 0.4817 | 0.6427 |
| standard_cv | face_task_native | task | demographics_group_device | random_forest | 3567 | 0.7035 | 0.4826 | 0.6517 |
| standard_cv | face_two_video_native | two_video | background_qc_demographics | logistic_regression | 3567 | 0.6977 | 0.4676 | 0.6465 |
| standard_cv | face_task_native | task | background_qc_demographics | logistic_regression | 3558 | 0.6967 | 0.4662 | 0.6458 |
| standard_cv | face_two_video_native | two_video | background_qc_demographics | random_forest | 3567 | 0.6967 | 0.4581 | 0.6497 |
| standard_cv | face_two_video_native | two_video | face_qc_demographics | logistic_regression | 3567 | 0.6955 | 0.4629 | 0.6401 |
| standard_cv | face_task_native | task | background_qc_demographics | hist_gradient_boosting | 3558 | 0.6934 | 0.4562 | 0.6462 |
| standard_cv | face_two_video_native | two_video | qc_demographics | hist_gradient_boosting | 3567 | 0.6929 | 0.4580 | 0.6392 |
| standard_cv | face_task_native | task | qc_demographics | logistic_regression | 3567 | 0.6923 | 0.4539 | 0.6420 |
| standard_cv | face_task_native | task | face_qc_demographics | hist_gradient_boosting | 3558 | 0.6920 | 0.4581 | 0.6412 |
| standard_cv | face_two_video_native | two_video | face_qc_demographics | random_forest | 3567 | 0.6920 | 0.4613 | 0.6428 |
| standard_cv | face_task_native | task | face_qc_demographics | logistic_regression | 3558 | 0.6920 | 0.4604 | 0.6376 |
| standard_cv | face_task_native | task | qc_demographics | random_forest | 3567 | 0.6912 | 0.4602 | 0.6406 |
| standard_cv | face_two_video_native | two_video | face_qc_demographics | hist_gradient_boosting | 3567 | 0.6908 | 0.4581 | 0.6427 |
| standard_cv | face_two_video_native | two_video | qc_demographics | logistic_regression | 3567 | 0.6908 | 0.4560 | 0.6428 |
| standard_cv | face_task_native | task | background_qc_demographics | random_forest | 3558 | 0.6904 | 0.4568 | 0.6533 |
| standard_cv | face_task_native | task | qc_demographics | hist_gradient_boosting | 3567 | 0.6892 | 0.4533 | 0.6393 |
| group_cv | face_two_video_native | two_video | qc_demographics | hist_gradient_boosting | 3567 | 0.6892 | 0.4535 | 0.6386 |
| standard_cv | face_two_video_native | two_video | background_qc_demographics | hist_gradient_boosting | 3567 | 0.6883 | 0.4533 | 0.6501 |
| group_cv | face_task_native | task | qc_demographics | logistic_regression | 3567 | 0.6874 | 0.4513 | 0.6408 |
| group_cv | face_two_video_native | two_video | qc_demographics | logistic_regression | 3567 | 0.6872 | 0.4538 | 0.6301 |
| standard_cv | face_task_native | task | face_qc_demographics | random_forest | 3558 | 0.6870 | 0.4582 | 0.6316 |
| group_cv | face_two_video_native | two_video | face_qc_demographics | logistic_regression | 3567 | 0.6856 | 0.4558 | 0.6353 |
| group_cv | face_task_native | task | face_qc_demographics | logistic_regression | 3558 | 0.6841 | 0.4480 | 0.6394 |
| group_cv | face_task_native | task | qc_demographics | hist_gradient_boosting | 3567 | 0.6829 | 0.4490 | 0.6356 |
| standard_cv | face_two_video_native | two_video | qc_demographics | random_forest | 3567 | 0.6829 | 0.4464 | 0.6349 |
| standard_cv | face_two_video_native | two_video | background_demographics | logistic_regression | 3567 | 0.6819 | 0.4453 | 0.6236 |
| group_cv | face_task_native | task | background_qc_demographics | logistic_regression | 3558 | 0.6818 | 0.4446 | 0.6300 |
| standard_cv | face_task_native | task | background_demographics | logistic_regression | 3558 | 0.6818 | 0.4466 | 0.6332 |
| standard_cv | face_self_intro_native | self_intro | background_demographics | logistic_regression | 3565 | 0.6815 | 0.4505 | 0.6307 |
| group_cv | face_task_native | task | qc_demographics | random_forest | 3567 | 0.6814 | 0.4509 | 0.6309 |
| group_cv | face_two_video_native | two_video | face_qc_demographics | random_forest | 3567 | 0.6811 | 0.4400 | 0.6313 |
| group_cv | face_task_native | task | background_qc_demographics | hist_gradient_boosting | 3558 | 0.6806 | 0.4437 | 0.6351 |
| group_cv | face_two_video_native | two_video | background_qc_demographics | logistic_regression | 3567 | 0.6804 | 0.4469 | 0.6277 |
| standard_cv | face_self_intro_native | self_intro | face_demographics | logistic_regression | 3565 | 0.6802 | 0.4455 | 0.6389 |
| group_cv | face_two_video_native | two_video | face_qc_demographics | hist_gradient_boosting | 3567 | 0.6797 | 0.4378 | 0.6369 |
| standard_cv | face_self_intro_native | self_intro | face_qc_demographics | logistic_regression | 3565 | 0.6792 | 0.4445 | 0.6336 |
| group_cv | face_task_native | task | background_qc_demographics | random_forest | 3558 | 0.6790 | 0.4471 | 0.6177 |
| standard_cv | face_self_intro_native | self_intro | background_qc_demographics | logistic_regression | 3565 | 0.6787 | 0.4488 | 0.6289 |
| group_cv | face_two_video_native | two_video | qc_demographics | random_forest | 3567 | 0.6786 | 0.4432 | 0.6282 |

## PCA Branch Diagnostics

| cv_protocol | cohort_name | task | feature_set | model | outer_fold | pca_used | pca_n_components | visual_branch_feature_count | nonvisual_branch_feature_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| standard_cv | face_self_intro_native | self_intro | demographics | logistic_regression | 0 | 0 | 0 | 0 | 0 |
| standard_cv | face_self_intro_native | self_intro | demographics | logistic_regression | 1 | 0 | 0 | 0 | 0 |
| standard_cv | face_self_intro_native | self_intro | demographics | logistic_regression | 2 | 0 | 0 | 0 | 0 |
| standard_cv | face_self_intro_native | self_intro | demographics | logistic_regression | 3 | 0 | 0 | 0 | 0 |
| standard_cv | face_self_intro_native | self_intro | demographics | logistic_regression | 4 | 0 | 0 | 0 | 0 |
| standard_cv | face_self_intro_native | self_intro | demographics | random_forest | 0 | 0 | 0 | 0 | 0 |
| standard_cv | face_self_intro_native | self_intro | demographics | random_forest | 1 | 0 | 0 | 0 | 0 |
| standard_cv | face_self_intro_native | self_intro | demographics | random_forest | 2 | 0 | 0 | 0 | 0 |
| standard_cv | face_self_intro_native | self_intro | demographics | random_forest | 3 | 0 | 0 | 0 | 0 |
| standard_cv | face_self_intro_native | self_intro | demographics | random_forest | 4 | 0 | 0 | 0 | 0 |
| standard_cv | face_self_intro_native | self_intro | demographics | hist_gradient_boosting | 0 | 0 | 0 | 0 | 0 |
| standard_cv | face_self_intro_native | self_intro | demographics | hist_gradient_boosting | 1 | 0 | 0 | 0 | 0 |
| standard_cv | face_self_intro_native | self_intro | demographics | hist_gradient_boosting | 2 | 0 | 0 | 0 | 0 |
| standard_cv | face_self_intro_native | self_intro | demographics | hist_gradient_boosting | 3 | 0 | 0 | 0 | 0 |
| standard_cv | face_self_intro_native | self_intro | demographics | hist_gradient_boosting | 4 | 0 | 0 | 0 | 0 |
| standard_cv | face_self_intro_native | self_intro | qc | logistic_regression | 0 | 0 | 0 | 0 | 0 |
| standard_cv | face_self_intro_native | self_intro | qc | logistic_regression | 1 | 0 | 0 | 0 | 0 |
| standard_cv | face_self_intro_native | self_intro | qc | logistic_regression | 2 | 0 | 0 | 0 | 0 |
| standard_cv | face_self_intro_native | self_intro | qc | logistic_regression | 3 | 0 | 0 | 0 | 0 |
| standard_cv | face_self_intro_native | self_intro | qc | logistic_regression | 4 | 0 | 0 | 0 | 0 |
| standard_cv | face_self_intro_native | self_intro | qc | random_forest | 0 | 0 | 0 | 0 | 0 |
| standard_cv | face_self_intro_native | self_intro | qc | random_forest | 1 | 0 | 0 | 0 | 0 |
| standard_cv | face_self_intro_native | self_intro | qc | random_forest | 2 | 0 | 0 | 0 | 0 |
| standard_cv | face_self_intro_native | self_intro | qc | random_forest | 3 | 0 | 0 | 0 | 0 |
| standard_cv | face_self_intro_native | self_intro | qc | random_forest | 4 | 0 | 0 | 0 | 0 |
| standard_cv | face_self_intro_native | self_intro | qc | hist_gradient_boosting | 0 | 0 | 0 | 0 | 0 |
| standard_cv | face_self_intro_native | self_intro | qc | hist_gradient_boosting | 1 | 0 | 0 | 0 | 0 |
| standard_cv | face_self_intro_native | self_intro | qc | hist_gradient_boosting | 2 | 0 | 0 | 0 | 0 |
| standard_cv | face_self_intro_native | self_intro | qc | hist_gradient_boosting | 3 | 0 | 0 | 0 | 0 |
| standard_cv | face_self_intro_native | self_intro | qc | hist_gradient_boosting | 4 | 0 | 0 | 0 | 0 |
| standard_cv | face_self_intro_native | self_intro | qc_demographics | logistic_regression | 0 | 0 | 0 | 0 | 0 |
| standard_cv | face_self_intro_native | self_intro | qc_demographics | logistic_regression | 1 | 0 | 0 | 0 | 0 |
| standard_cv | face_self_intro_native | self_intro | qc_demographics | logistic_regression | 2 | 0 | 0 | 0 | 0 |
| standard_cv | face_self_intro_native | self_intro | qc_demographics | logistic_regression | 3 | 0 | 0 | 0 | 0 |
| standard_cv | face_self_intro_native | self_intro | qc_demographics | logistic_regression | 4 | 0 | 0 | 0 | 0 |
| standard_cv | face_self_intro_native | self_intro | qc_demographics | random_forest | 0 | 0 | 0 | 0 | 0 |
| standard_cv | face_self_intro_native | self_intro | qc_demographics | random_forest | 1 | 0 | 0 | 0 | 0 |
| standard_cv | face_self_intro_native | self_intro | qc_demographics | random_forest | 2 | 0 | 0 | 0 | 0 |
| standard_cv | face_self_intro_native | self_intro | qc_demographics | random_forest | 3 | 0 | 0 | 0 | 0 |
| standard_cv | face_self_intro_native | self_intro | qc_demographics | random_forest | 4 | 0 | 0 | 0 | 0 |
| standard_cv | face_self_intro_native | self_intro | qc_demographics | hist_gradient_boosting | 0 | 0 | 0 | 0 | 0 |
| standard_cv | face_self_intro_native | self_intro | qc_demographics | hist_gradient_boosting | 1 | 0 | 0 | 0 | 0 |
| standard_cv | face_self_intro_native | self_intro | qc_demographics | hist_gradient_boosting | 2 | 0 | 0 | 0 | 0 |
| standard_cv | face_self_intro_native | self_intro | qc_demographics | hist_gradient_boosting | 3 | 0 | 0 | 0 | 0 |
| standard_cv | face_self_intro_native | self_intro | qc_demographics | hist_gradient_boosting | 4 | 0 | 0 | 0 | 0 |
| standard_cv | face_self_intro_native | self_intro | metadata | logistic_regression | 0 | 0 | 0 | 0 | 0 |
| standard_cv | face_self_intro_native | self_intro | metadata | logistic_regression | 1 | 0 | 0 | 0 | 0 |
| standard_cv | face_self_intro_native | self_intro | metadata | logistic_regression | 2 | 0 | 0 | 0 | 0 |
| standard_cv | face_self_intro_native | self_intro | metadata | logistic_regression | 3 | 0 | 0 | 0 | 0 |
| standard_cv | face_self_intro_native | self_intro | metadata | logistic_regression | 4 | 0 | 0 | 0 | 0 |

## Paired Face Controls

| cv_protocol | cohort_name | task | model | comparison | n_subjects | auroc_diff | auroc_diff_ci_low | auroc_diff_ci_high | fold_direction_consistency | protocol_consistent_direction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| group_cv | core3_rest_yiruidvft_selfintro_intersection | self_intro | hist_gradient_boosting | modality_vs_demographics | 661 | 0.0477 | -0.0094 | 0.1099 | 3 | 0 |
| group_cv | core3_rest_yiruidvft_selfintro_intersection | self_intro | hist_gradient_boosting | modality_demographics_vs_demographics | 661 | 0.0576 | 0.0012 | 0.1128 | 3 | 1 |
| group_cv | core3_rest_yiruidvft_selfintro_intersection | self_intro | hist_gradient_boosting | modality_qc_demographics_vs_qc_demographics | 661 | 0.0498 | -0.0084 | 0.1066 | 2 | 0 |
| group_cv | core3_rest_yiruidvft_selfintro_intersection | self_intro | logistic_regression | modality_vs_demographics | 661 | 0.0331 | -0.0258 | 0.0922 | 4 | 0 |
| group_cv | core3_rest_yiruidvft_selfintro_intersection | self_intro | logistic_regression | modality_demographics_vs_demographics | 661 | 0.0461 | -0.0044 | 0.0936 | 4 | 1 |
| group_cv | core3_rest_yiruidvft_selfintro_intersection | self_intro | logistic_regression | modality_qc_demographics_vs_qc_demographics | 661 | 0.0139 | -0.0383 | 0.0640 | 3 | 1 |
| group_cv | core3_rest_yiruidvft_selfintro_intersection | self_intro | random_forest | modality_vs_demographics | 661 | 0.0690 | 0.0119 | 0.1252 | 4 | 1 |
| group_cv | core3_rest_yiruidvft_selfintro_intersection | self_intro | random_forest | modality_demographics_vs_demographics | 661 | 0.0656 | 0.0129 | 0.1245 | 4 | 1 |
| group_cv | core3_rest_yiruidvft_selfintro_intersection | self_intro | random_forest | modality_qc_demographics_vs_qc_demographics | 661 | 0.0112 | -0.0368 | 0.0579 | 3 | 0 |
| group_cv | face_self_intro_native | self_intro | hist_gradient_boosting | face_vs_demographics | 3565 | -0.0552 | -0.0771 | -0.0345 | 0 | 1 |
| group_cv | face_self_intro_native | self_intro | hist_gradient_boosting | face_demographics_vs_demographics | 3565 | 0.0066 | -0.0061 | 0.0197 | 4 | 1 |
| group_cv | face_self_intro_native | self_intro | hist_gradient_boosting | face_qc_vs_qc | 3565 | 0.0777 | 0.0534 | 0.1020 | 5 | 1 |
| group_cv | face_self_intro_native | self_intro | hist_gradient_boosting | face_qc_demographics_vs_qc_demographics | 3565 | 0.0062 | -0.0057 | 0.0178 | 5 | 1 |
| group_cv | face_self_intro_native | self_intro | hist_gradient_boosting | face_qc_demographics_vs_demographics | 3565 | 0.0078 | -0.0055 | 0.0195 | 4 | 0 |
| group_cv | face_self_intro_native | self_intro | hist_gradient_boosting | face_vs_background | 3565 | 0.0174 | -0.0070 | 0.0416 | 5 | 1 |
| group_cv | face_self_intro_native | self_intro | hist_gradient_boosting | face_vs_full_frame | 3565 | 0.0050 | -0.0158 | 0.0271 | 5 | 1 |
| group_cv | face_self_intro_native | self_intro | hist_gradient_boosting | face_vs_metadata | 3565 | 0.1100 | 0.0828 | 0.1406 | 5 | 1 |
| group_cv | face_self_intro_native | self_intro | hist_gradient_boosting | face_vs_qc | 3565 | 0.0698 | 0.0444 | 0.0950 | 5 | 1 |
| group_cv | face_self_intro_native | self_intro | hist_gradient_boosting | face_demographics_vs_background_demographics | 3565 | 0.0103 | -0.0026 | 0.0233 | 5 | 1 |
| group_cv | face_self_intro_native | self_intro | logistic_regression | face_vs_demographics | 3565 | -0.0306 | -0.0515 | -0.0115 | 0 | 1 |
| group_cv | face_self_intro_native | self_intro | logistic_regression | face_demographics_vs_demographics | 3565 | -0.0017 | -0.0127 | 0.0091 | 1 | 0 |
| group_cv | face_self_intro_native | self_intro | logistic_regression | face_qc_vs_qc | 3565 | 0.0814 | 0.0576 | 0.1056 | 5 | 1 |
| group_cv | face_self_intro_native | self_intro | logistic_regression | face_qc_demographics_vs_qc_demographics | 3565 | -0.0079 | -0.0175 | 0.0030 | 0 | 0 |
| group_cv | face_self_intro_native | self_intro | logistic_regression | face_qc_demographics_vs_demographics | 3565 | -0.0043 | -0.0153 | 0.0069 | 0 | 0 |
| group_cv | face_self_intro_native | self_intro | logistic_regression | face_vs_background | 3565 | 0.0516 | 0.0297 | 0.0729 | 5 | 1 |
| group_cv | face_self_intro_native | self_intro | logistic_regression | face_vs_full_frame | 3565 | 0.0149 | -0.0046 | 0.0334 | 5 | 1 |
| group_cv | face_self_intro_native | self_intro | logistic_regression | face_vs_metadata | 3565 | 0.1375 | 0.1110 | 0.1648 | 5 | 1 |
| group_cv | face_self_intro_native | self_intro | logistic_regression | face_vs_qc | 3565 | 0.0831 | 0.0593 | 0.1069 | 5 | 1 |
| group_cv | face_self_intro_native | self_intro | logistic_regression | face_demographics_vs_background_demographics | 3565 | 0.0013 | -0.0090 | 0.0124 | 2 | 0 |
| group_cv | face_self_intro_native | self_intro | random_forest | face_vs_demographics | 3565 | -0.0351 | -0.0573 | -0.0135 | 0 | 1 |
| group_cv | face_self_intro_native | self_intro | random_forest | face_demographics_vs_demographics | 3565 | -0.0280 | -0.0409 | -0.0132 | 2 | 0 |
| group_cv | face_self_intro_native | self_intro | random_forest | face_qc_vs_qc | 3565 | 0.0454 | 0.0205 | 0.0684 | 5 | 1 |
| group_cv | face_self_intro_native | self_intro | random_forest | face_qc_demographics_vs_qc_demographics | 3565 | -0.0003 | -0.0108 | 0.0105 | 3 | 1 |
| group_cv | face_self_intro_native | self_intro | random_forest | face_qc_demographics_vs_demographics | 3565 | -0.0036 | -0.0174 | 0.0098 | 2 | 1 |
| group_cv | face_self_intro_native | self_intro | random_forest | face_vs_background | 3565 | 0.0343 | 0.0088 | 0.0596 | 5 | 1 |
| group_cv | face_self_intro_native | self_intro | random_forest | face_vs_full_frame | 3565 | 0.0692 | 0.0491 | 0.0917 | 5 | 1 |
| group_cv | face_self_intro_native | self_intro | random_forest | face_vs_metadata | 3565 | 0.1365 | 0.1074 | 0.1670 | 5 | 1 |
| group_cv | face_self_intro_native | self_intro | random_forest | face_vs_qc | 3565 | 0.1048 | 0.0781 | 0.1297 | 5 | 1 |
| group_cv | face_self_intro_native | self_intro | random_forest | face_demographics_vs_background_demographics | 3565 | -0.0029 | -0.0194 | 0.0130 | 3 | 0 |
| group_cv | face_task_native | task | hist_gradient_boosting | face_vs_demographics | 3558 | -0.0541 | -0.0764 | -0.0336 | 0 | 1 |
| group_cv | face_task_native | task | hist_gradient_boosting | face_demographics_vs_demographics | 3558 | -0.0123 | -0.0252 | 0.0008 | 1 | 0 |
| group_cv | face_task_native | task | hist_gradient_boosting | face_qc_vs_qc | 3558 | 0.0843 | 0.0616 | 0.1079 | 5 | 1 |
| group_cv | face_task_native | task | hist_gradient_boosting | face_qc_demographics_vs_qc_demographics | 3558 | -0.0060 | -0.0144 | 0.0019 | 0 | 0 |
| group_cv | face_task_native | task | hist_gradient_boosting | face_qc_demographics_vs_demographics | 3558 | 0.0234 | 0.0088 | 0.0385 | 5 | 1 |
| group_cv | face_task_native | task | hist_gradient_boosting | face_vs_background | 3558 | 0.0240 | 0.0017 | 0.0456 | 4 | 1 |
| group_cv | face_task_native | task | hist_gradient_boosting | face_vs_full_frame | 3558 | -0.0062 | -0.0270 | 0.0152 | 3 | 0 |
| group_cv | face_task_native | task | hist_gradient_boosting | face_vs_metadata | 3558 | 0.0628 | 0.0338 | 0.0918 | 5 | 1 |
| group_cv | face_task_native | task | hist_gradient_boosting | face_vs_qc | 3558 | 0.0622 | 0.0366 | 0.0896 | 5 | 1 |
| group_cv | face_task_native | task | hist_gradient_boosting | face_demographics_vs_background_demographics | 3558 | -0.0103 | -0.0236 | 0.0015 | 3 | 1 |
| group_cv | face_task_native | task | logistic_regression | face_vs_demographics | 3558 | -0.0319 | -0.0516 | -0.0114 | 0 | 1 |
| group_cv | face_task_native | task | logistic_regression | face_demographics_vs_demographics | 3558 | -0.0010 | -0.0109 | 0.0088 | 0 | 0 |
| group_cv | face_task_native | task | logistic_regression | face_qc_vs_qc | 3558 | 0.0846 | 0.0630 | 0.1087 | 5 | 1 |
| group_cv | face_task_native | task | logistic_regression | face_qc_demographics_vs_qc_demographics | 3558 | -0.0040 | -0.0129 | 0.0055 | 1 | 1 |
| group_cv | face_task_native | task | logistic_regression | face_qc_demographics_vs_demographics | 3558 | 0.0245 | 0.0119 | 0.0375 | 5 | 1 |
| group_cv | face_task_native | task | logistic_regression | face_vs_background | 3558 | 0.0388 | 0.0187 | 0.0598 | 5 | 1 |
| group_cv | face_task_native | task | logistic_regression | face_vs_full_frame | 3558 | 0.0079 | -0.0079 | 0.0248 | 3 | 1 |
| group_cv | face_task_native | task | logistic_regression | face_vs_metadata | 3558 | 0.0829 | 0.0542 | 0.1136 | 4 | 1 |
| group_cv | face_task_native | task | logistic_regression | face_vs_qc | 3558 | 0.0665 | 0.0402 | 0.0921 | 5 | 1 |
| group_cv | face_task_native | task | logistic_regression | face_demographics_vs_background_demographics | 3558 | 0.0021 | -0.0094 | 0.0130 | 2 | 0 |
| group_cv | face_task_native | task | random_forest | face_vs_demographics | 3558 | -0.0574 | -0.0771 | -0.0379 | 1 | 1 |
| group_cv | face_task_native | task | random_forest | face_demographics_vs_demographics | 3558 | -0.0127 | -0.0238 | -0.0008 | 1 | 0 |
| group_cv | face_task_native | task | random_forest | face_qc_vs_qc | 3558 | 0.0490 | 0.0278 | 0.0713 | 5 | 1 |
| group_cv | face_task_native | task | random_forest | face_qc_demographics_vs_qc_demographics | 3558 | -0.0156 | -0.0262 | -0.0056 | 0 | 1 |
| group_cv | face_task_native | task | random_forest | face_qc_demographics_vs_demographics | 3558 | 0.0070 | -0.0085 | 0.0227 | 4 | 1 |
| group_cv | face_task_native | task | random_forest | face_vs_background | 3558 | 0.0549 | 0.0308 | 0.0799 | 4 | 1 |
| group_cv | face_task_native | task | random_forest | face_vs_full_frame | 3558 | -0.0170 | -0.0381 | 0.0027 | 3 | 0 |
| group_cv | face_task_native | task | random_forest | face_vs_metadata | 3558 | 0.0699 | 0.0437 | 0.1003 | 5 | 1 |
| group_cv | face_task_native | task | random_forest | face_vs_qc | 3558 | 0.0559 | 0.0293 | 0.0818 | 5 | 1 |
| group_cv | face_task_native | task | random_forest | face_demographics_vs_background_demographics | 3558 | -0.0255 | -0.0384 | -0.0120 | 3 | 1 |
| group_cv | face_two_video_native | two_video | hist_gradient_boosting | face_vs_demographics | 3567 | -0.0354 | -0.0558 | -0.0133 | 1 | 1 |
| group_cv | face_two_video_native | two_video | hist_gradient_boosting | face_demographics_vs_demographics | 3567 | -0.0021 | -0.0149 | 0.0108 | 3 | 0 |
| group_cv | face_two_video_native | two_video | hist_gradient_boosting | face_qc_vs_qc | 3567 | 0.0765 | 0.0531 | 0.0981 | 5 | 1 |
| group_cv | face_two_video_native | two_video | hist_gradient_boosting | face_qc_demographics_vs_qc_demographics | 3567 | -0.0095 | -0.0179 | -0.0002 | 2 | 1 |
| group_cv | face_two_video_native | two_video | hist_gradient_boosting | face_qc_demographics_vs_demographics | 3567 | 0.0231 | 0.0086 | 0.0379 | 5 | 1 |
| group_cv | face_two_video_native | two_video | hist_gradient_boosting | face_vs_background | 3567 | 0.0320 | 0.0094 | 0.0553 | 4 | 1 |
| group_cv | face_two_video_native | two_video | hist_gradient_boosting | face_vs_full_frame | 3567 | 0.0196 | 0.0006 | 0.0391 | 4 | 1 |
| group_cv | face_two_video_native | two_video | hist_gradient_boosting | face_vs_metadata | 3567 | 0.0764 | 0.0472 | 0.1071 | 5 | 1 |
| group_cv | face_two_video_native | two_video | hist_gradient_boosting | face_vs_qc | 3567 | 0.0648 | 0.0405 | 0.0901 | 5 | 1 |
| group_cv | face_two_video_native | two_video | hist_gradient_boosting | face_demographics_vs_background_demographics | 3567 | 0.0131 | 0.0000 | 0.0261 | 5 | 1 |
| group_cv | face_two_video_native | two_video | logistic_regression | face_vs_demographics | 3567 | -0.0255 | -0.0458 | -0.0053 | 0 | 1 |
