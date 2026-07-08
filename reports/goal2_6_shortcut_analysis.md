# Goal 2.6 Shortcut Analysis

Protocol: fixed `split_group == cv` only; subject-level OOF predictions; 3-fold inner CV for hyperparameters and thresholds; baseline-exposed pilot holdout excluded throughout.

## Shortcut Baselines

| cohort_name | modality | task | feature_set | model | n_subjects | auroc | auprc | balanced_accuracy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| shortcut_a_prefix_group_cv | shortcut | a_prefix_group | group_device | logistic_regression | 3597 | 0.6778 | 0.4671 | 0.6322 |
| shortcut_a_prefix_group_cv | shortcut | a_prefix_group | group_device | random_forest | 3597 | 0.6731 | 0.4555 | 0.6346 |
| shortcut_a_prefix_group_cv | shortcut | a_prefix_group | group_device | hist_gradient_boosting | 3597 | 0.6458 | 0.4111 | 0.6299 |
| face_task_native | face | task | background | logistic_regression | 3567 | 0.6230 | 0.3917 | 0.5929 |
| face_two_video_native | face | two_video | background | logistic_regression | 3567 | 0.6179 | 0.3913 | 0.5917 |
| face_self_intro_native | face | self_intro | background | logistic_regression | 3572 | 0.6028 | 0.3802 | 0.5737 |
| face_two_video_native | face | two_video | background | hist_gradient_boosting | 3567 | 0.6027 | 0.3730 | 0.5845 |
| face_task_native | face | task | background | hist_gradient_boosting | 3567 | 0.5877 | 0.3511 | 0.5642 |
| face_self_intro_native | face | self_intro | background | hist_gradient_boosting | 3572 | 0.5863 | 0.3578 | 0.5701 |
| face_two_video_native | face | two_video | qc | logistic_regression | 3567 | 0.5657 | 0.3535 | 0.5427 |
| face_task_native | face | task | qc | logistic_regression | 3567 | 0.5623 | 0.3470 | 0.5465 |
| face_two_video_native | face | two_video | metadata | logistic_regression | 3567 | 0.5553 | 0.3361 | 0.5394 |
| face_task_native | face | task | metadata | logistic_regression | 3567 | 0.5536 | 0.3349 | 0.5366 |
| face_two_video_native | face | two_video | metadata | hist_gradient_boosting | 3567 | 0.5529 | 0.3336 | 0.5425 |
| face_two_video_native | face | two_video | qc | hist_gradient_boosting | 3567 | 0.5527 | 0.3378 | 0.5458 |
| fnirs_yiruid_vft_native | fnirs | vft | qc | random_forest | 1480 | 0.5522 | 0.4345 | 0.5370 |
| face_task_native | face | task | qc | hist_gradient_boosting | 3567 | 0.5415 | 0.3353 | 0.5253 |
| face_self_intro_native | face | self_intro | qc | hist_gradient_boosting | 3572 | 0.5414 | 0.3389 | 0.5383 |
| eeg_1back_native | eeg | 1back | qc | logistic_regression | 1154 | 0.5396 | 0.3260 | 0.5331 |
| fnirs_yiruid_vft_native | fnirs | vft | qc | logistic_regression | 1480 | 0.5384 | 0.4279 | 0.5356 |

## Interpretation

Potential shortcut signal detected: `shortcut_a_prefix_group_cv` / `group_device` reached AUROC `0.6778`. Treat adjacent signal gains as shortcut-sensitive.
