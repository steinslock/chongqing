# Goal 2.6 Face Results

Protocol: fixed `split_group == cv` only; subject-level OOF predictions; 3-fold inner CV for hyperparameters and thresholds; baseline-exposed pilot holdout excluded throughout.

## Feature Extraction

| cohort_name | modality | device | task | feature_set | n_subjects | feature_count | numeric_count | categorical_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| face_self_intro_native | face |  | self_intro | no_information | 3572 | 0 | 0 | 0 |
| face_self_intro_native | face |  | self_intro | demographics | 3572 | 4 | 1 | 3 |
| face_self_intro_native | face |  | self_intro | qc | 3572 | 20 | 19 | 1 |
| face_self_intro_native | face |  | self_intro | metadata | 3572 | 6 | 5 | 1 |
| face_self_intro_native | face |  | self_intro | full_frame | 3572 | 1024 | 1024 | 0 |
| face_self_intro_native | face |  | self_intro | face_crop | 3572 | 1024 | 1024 | 0 |
| face_self_intro_native | face |  | self_intro | background | 3572 | 1024 | 1024 | 0 |
| face_self_intro_native | face |  | self_intro | face_qc | 3572 | 1044 | 1043 | 1 |
| face_self_intro_native | face |  | self_intro | face_demographics | 3572 | 1028 | 1025 | 3 |
| face_self_intro_native | face |  | self_intro | face_qc_demographics | 3572 | 1048 | 1044 | 4 |
| face_task_native | face |  | task | no_information | 3567 | 0 | 0 | 0 |
| face_task_native | face |  | task | demographics | 3567 | 4 | 1 | 3 |
| face_task_native | face |  | task | qc | 3567 | 20 | 19 | 1 |
| face_task_native | face |  | task | metadata | 3567 | 6 | 5 | 1 |
| face_task_native | face |  | task | full_frame | 3567 | 1024 | 1024 | 0 |
| face_task_native | face |  | task | face_crop | 3567 | 1024 | 1024 | 0 |
| face_task_native | face |  | task | background | 3567 | 1024 | 1024 | 0 |
| face_task_native | face |  | task | face_qc | 3567 | 1044 | 1043 | 1 |
| face_task_native | face |  | task | face_demographics | 3567 | 1028 | 1025 | 3 |
| face_task_native | face |  | task | face_qc_demographics | 3567 | 1048 | 1044 | 4 |
| face_two_video_native | face |  | two_video | no_information | 3567 | 0 | 0 | 0 |
| face_two_video_native | face |  | two_video | demographics | 3567 | 4 | 1 | 3 |
| face_two_video_native | face |  | two_video | qc | 3567 | 40 | 38 | 2 |
| face_two_video_native | face |  | two_video | metadata | 3567 | 12 | 10 | 2 |
| face_two_video_native | face |  | two_video | full_frame | 3567 | 2048 | 2048 | 0 |
| face_two_video_native | face |  | two_video | face_crop | 3567 | 2048 | 2048 | 0 |
| face_two_video_native | face |  | two_video | background | 3567 | 2048 | 2048 | 0 |
| face_two_video_native | face |  | two_video | face_qc | 3567 | 2088 | 2086 | 2 |
| face_two_video_native | face |  | two_video | face_demographics | 3567 | 2052 | 2049 | 3 |
| face_two_video_native | face |  | two_video | face_qc_demographics | 3567 | 2092 | 2087 | 5 |
| core3_same_cohort | face |  | self_intro | demographics | 661 | 4 | 1 | 3 |
| core3_same_cohort | face |  | self_intro | modality | 661 | 1024 | 1024 | 0 |
| core3_same_cohort | face |  | self_intro | modality_demographics | 661 | 1028 | 1025 | 3 |

Encoder: `torchvision_resnet18`; frozen: `True`; sample frames: `8`. Face crops use the configured OpenCV Haar fallback detector, so face-only gains must be interpreted with shortcut/QC controls.

## Native-Cohort Performance

| cohort_name | task | feature_set | model | n_subjects | auroc | auprc | balanced_accuracy | macro_f1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| face_self_intro_native | self_intro | demographics | logistic_regression | 3572 | 0.6702 | 0.4305 | 0.6205 | 0.5918 |
| face_two_video_native | two_video | demographics | logistic_regression | 3567 | 0.6694 | 0.4291 | 0.6199 | 0.5912 |
| face_task_native | task | demographics | logistic_regression | 3567 | 0.6693 | 0.4290 | 0.6199 | 0.5912 |
| face_self_intro_native | self_intro | demographics | hist_gradient_boosting | 3572 | 0.6668 | 0.4166 | 0.6238 | 0.5493 |
| face_task_native | task | demographics | hist_gradient_boosting | 3567 | 0.6664 | 0.4155 | 0.6218 | 0.5512 |
| face_two_video_native | two_video | demographics | hist_gradient_boosting | 3567 | 0.6664 | 0.4155 | 0.6218 | 0.5512 |
| face_two_video_native | two_video | face_demographics | logistic_regression | 3567 | 0.6458 | 0.4173 | 0.5985 | 0.5488 |
| face_task_native | task | face_demographics | logistic_regression | 3567 | 0.6452 | 0.4176 | 0.6021 | 0.5751 |
| face_two_video_native | two_video | face_qc_demographics | logistic_regression | 3567 | 0.6449 | 0.4160 | 0.5960 | 0.5462 |
| face_two_video_native | two_video | full_frame | logistic_regression | 3567 | 0.6441 | 0.4082 | 0.6051 | 0.5788 |
| face_two_video_native | two_video | face_crop | logistic_regression | 3567 | 0.6440 | 0.4168 | 0.5945 | 0.5448 |
| face_task_native | task | face_qc_demographics | logistic_regression | 3567 | 0.6436 | 0.4153 | 0.6039 | 0.5514 |
| face_two_video_native | two_video | face_qc | logistic_regression | 3567 | 0.6431 | 0.4146 | 0.5941 | 0.5441 |
| face_task_native | task | face_crop | logistic_regression | 3567 | 0.6414 | 0.4141 | 0.5966 | 0.5713 |
| face_self_intro_native | self_intro | face_demographics | logistic_regression | 3572 | 0.6404 | 0.4097 | 0.6032 | 0.5745 |

## Shortcut Controls

| cohort_name | task | feature_set | model | n_subjects | auroc | auprc |
| --- | --- | --- | --- | --- | --- | --- |
| face_two_video_native | two_video | full_frame | logistic_regression | 3567 | 0.6441 | 0.4082 |
| face_two_video_native | two_video | face_crop | logistic_regression | 3567 | 0.6440 | 0.4168 |
| face_task_native | task | face_crop | logistic_regression | 3567 | 0.6414 | 0.4141 |
| face_self_intro_native | self_intro | full_frame | logistic_regression | 3572 | 0.6399 | 0.4049 |
| face_task_native | task | full_frame | logistic_regression | 3567 | 0.6380 | 0.4014 |
| face_self_intro_native | self_intro | face_crop | logistic_regression | 3572 | 0.6366 | 0.4061 |
| face_two_video_native | two_video | face_crop | hist_gradient_boosting | 3567 | 0.6275 | 0.3907 |
| face_self_intro_native | self_intro | face_crop | hist_gradient_boosting | 3572 | 0.6272 | 0.3997 |
| face_task_native | task | face_crop | hist_gradient_boosting | 3567 | 0.6258 | 0.3924 |
| face_task_native | task | background | logistic_regression | 3567 | 0.6230 | 0.3917 |
| face_two_video_native | two_video | background | logistic_regression | 3567 | 0.6179 | 0.3913 |
| face_self_intro_native | self_intro | background | logistic_regression | 3572 | 0.6028 | 0.3802 |

## Paired Checks

| cohort_name | task | model | model_a | model_b | n_subjects | auroc_diff | auroc_diff_ci_low | auroc_diff_ci_high | fold_direction_consistency | folds_compared |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| face_self_intro_native | self_intro | logistic_regression | face_crop | metadata | 3572 | 0.1345 | 0.1067 | 0.1627 | 5 | 5 |
| face_self_intro_native | self_intro | hist_gradient_boosting | face_crop | metadata | 3572 | 0.1278 | 0.1006 | 0.1549 | 5 | 5 |
| face_self_intro_native | self_intro | logistic_regression | face_crop | qc | 3572 | 0.0984 | 0.0730 | 0.1245 | 5 | 5 |
| face_task_native | task | hist_gradient_boosting | face_crop | metadata | 3567 | 0.0902 | 0.0617 | 0.1200 | 5 | 5 |
| face_two_video_native | two_video | logistic_regression | face_crop | metadata | 3567 | 0.0888 | 0.0600 | 0.1166 | 5 | 5 |
| face_task_native | task | logistic_regression | face_crop | metadata | 3567 | 0.0878 | 0.0566 | 0.1151 | 5 | 5 |
| face_self_intro_native | self_intro | hist_gradient_boosting | face_crop | qc | 3572 | 0.0858 | 0.0590 | 0.1110 | 5 | 5 |
| face_task_native | task | hist_gradient_boosting | face_crop | qc | 3567 | 0.0842 | 0.0583 | 0.1123 | 5 | 5 |
| face_task_native | task | logistic_regression | face_crop | qc | 3567 | 0.0791 | 0.0533 | 0.1055 | 5 | 5 |
| face_two_video_native | two_video | logistic_regression | face_crop | qc | 3567 | 0.0783 | 0.0526 | 0.1041 | 5 | 5 |
| face_two_video_native | two_video | hist_gradient_boosting | face_crop | qc | 3567 | 0.0748 | 0.0491 | 0.1010 | 5 | 5 |
| face_two_video_native | two_video | hist_gradient_boosting | face_crop | metadata | 3567 | 0.0745 | 0.0474 | 0.1025 | 5 | 5 |
| face_self_intro_native | self_intro | hist_gradient_boosting | face_crop | background | 3572 | 0.0409 | 0.0170 | 0.0638 | 4 | 5 |
| face_task_native | task | hist_gradient_boosting | face_crop | background | 3567 | 0.0381 | 0.0151 | 0.0603 | 5 | 5 |
| face_self_intro_native | self_intro | logistic_regression | face_crop | background | 3572 | 0.0338 | 0.0128 | 0.0550 | 5 | 5 |

## Status

Face: best AUROC `0.6702` from `face_self_intro_native` / `demographics` / `logistic_regression` on `3572` subjects.
