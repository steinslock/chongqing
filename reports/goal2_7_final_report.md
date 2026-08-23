# Goal 2.7 Final Report

Goal 2.7 fixes the comparison protocol, threshold application, demographics decomposition, Face strict controls, and EEG/fNIRS event validity handling. Standard fixed CV and Group-aware fixed CV are co-primary; all model selection, PCA dimensions, and thresholds are fit inside outer-train only.

## Technical Summary

- No modality reaches `INDEPENDENT_SIGNAL_SUPPORTED`. Required native-cohort paired increments over demographics or QC+demographics are absent, negative, or have CIs crossing 0.
- No native EEG, fNIRS, or Face required independent-increment comparison had AUROC 95% CI fully above 0. Positive significant required rows are limited to Core3 Face sensitivity rows, not a consistent native-cohort conclusion.
- EEG task conclusions are blocked for formal Oddball target/non-target ERP and 1BACK condition contrasts; Rest and generic/task-proxy features show no independent increment beyond demographics/QC.
- fNIRS task-response conclusions are blocked without confirmed timing. Yiruid VFT remains the least weak fNIRS candidate by point estimate, but its signal+demographics and signal+QC+demographics increments do not clear paired bootstrap under Group CV.
- Face strict visual embeddings show above-background and above-metadata signal, but demographics/group proxy remain stronger and face+demographics rarely improves over demographics. Face remains shortcut-dominated for final decision-making.
- The most defensible next Goal is not deep modeling yet; it is a shortcut/event-semantics remediation Goal that recovers task protocols and tests residualized or group-balanced visual/demographic baselines.

## Scope, Protocol, and Outputs

- OOF predictions: Standard CV and Group CV, 36,720 bootstrap CI rows, 618 paired comparison rows.
- Models: Logistic Regression, Random Forest, and HistGradientBoosting only. HGB used the expanded predefined fallback grid.
- Metrics: AUROC/AUPRC plus balanced accuracy, macro F1, sensitivity, specificity, accuracy, Brier score, ECE, and positive prediction rate. Threshold-dependent pooled metrics use each subject's own outer-fold inner-CV threshold; fixed 0.5 metrics are retained.
- Pilot holdout was not used. Main demographics is age + sex + grade; grade_group and group proxy are sensitivity/decomposition sets.

## Key Standard and Group CV Results

The table gives the best row for each core feature family and protocol. It is evidence for interpretation, not a model-selection sweep.

| cv_protocol | modality | cohort_name | device | task | feature_set | model | n_subjects | auroc | auprc |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| standard_cv | eeg | eeg_oddball_native |  | oddball | demographics | logistic_regression | 1827 | 0.6030 | 0.4236 |
| standard_cv | eeg | eeg_oddball_native |  | oddball | demographics_group | random_forest | 1827 | 0.6434 | 0.4417 |
| standard_cv | eeg | eeg_rest_native |  | rest | group_proxy_only | hist_gradient_boosting | 1022 | 0.6188 | 0.4271 |
| standard_cv | eeg | eeg_oddball_native |  | oddball | signal | logistic_regression | 1827 | 0.5446 | 0.3691 |
| standard_cv | eeg | eeg_oddball_native |  | oddball | signal_demographics | logistic_regression | 1827 | 0.5863 | 0.4107 |
| standard_cv | eeg | eeg_oddball_native |  | oddball | signal_qc_demographics | logistic_regression | 1827 | 0.5839 | 0.4070 |
| standard_cv | eeg | eeg_rest_native |  | rest | qc_demographics | logistic_regression | 1022 | 0.6063 | 0.4137 |
| group_cv | eeg | eeg_oddball_native |  | oddball | demographics | logistic_regression | 1827 | 0.5928 | 0.4113 |
| group_cv | eeg | eeg_oddball_native |  | oddball | demographics_group | random_forest | 1827 | 0.5908 | 0.4065 |
| group_cv | eeg | eeg_1back_native |  | 1back | group_proxy_only | logistic_regression | 1154 | 0.5778 | 0.3345 |
| group_cv | eeg | eeg_oddball_native |  | oddball | signal | logistic_regression | 1827 | 0.5236 | 0.3500 |
| group_cv | eeg | eeg_oddball_native |  | oddball | signal_demographics | hist_gradient_boosting | 1827 | 0.5742 | 0.3885 |
| group_cv | eeg | eeg_oddball_native |  | oddball | signal_qc_demographics | hist_gradient_boosting | 1827 | 0.5746 | 0.3827 |
| group_cv | eeg | eeg_rest_native |  | rest | qc_demographics | logistic_regression | 1022 | 0.5899 | 0.4050 |
| standard_cv | fnirs | fnirs_bikom_1back_native | bikom | 1back | demographics | logistic_regression | 985 | 0.6286 | 0.4419 |
| standard_cv | fnirs | fnirs_yiruid_1back_native | yiruid | 1back | demographics_group | logistic_regression | 1422 | 0.6645 | 0.5407 |
| standard_cv | fnirs | fnirs_yiruid_1back_native | yiruid | 1back | group_proxy_only | logistic_regression | 1422 | 0.6302 | 0.5119 |
| standard_cv | fnirs | fnirs_yiruid_vft_native | yiruid | vft | signal | random_forest | 1480 | 0.5860 | 0.4602 |
| standard_cv | fnirs | fnirs_yiruid_vft_native | yiruid | vft | signal_demographics | random_forest | 1480 | 0.5878 | 0.4598 |
| standard_cv | fnirs | fnirs_yiruid_vft_native | yiruid | vft | signal_qc_demographics | random_forest | 1480 | 0.5887 | 0.4628 |
| standard_cv | fnirs | fnirs_bikom_vft_native | bikom | vft | qc_demographics | logistic_regression | 1022 | 0.6296 | 0.4503 |
| group_cv | fnirs | fnirs_bikom_rest_native | bikom | rest | demographics | logistic_regression | 1017 | 0.6051 | 0.4229 |
| group_cv | fnirs | fnirs_bikom_1back_native | bikom | 1back | demographics_group | logistic_regression | 985 | 0.6219 | 0.4283 |
| group_cv | fnirs | fnirs_yiruid_1back_native | yiruid | 1back | group_proxy_only | hist_gradient_boosting | 1422 | 0.5711 | 0.4401 |
| group_cv | fnirs | fnirs_bikom_vft_native | bikom | vft | signal | logistic_regression | 1022 | 0.5733 | 0.3731 |
| group_cv | fnirs | fnirs_yiruid_vft_native | yiruid | vft | signal_demographics | logistic_regression | 1480 | 0.5811 | 0.4437 |
| group_cv | fnirs | fnirs_yiruid_vft_native | yiruid | vft | signal_qc_demographics | logistic_regression | 1480 | 0.5846 | 0.4465 |
| group_cv | fnirs | fnirs_yiruid_vft_native | yiruid | vft | qc_demographics | logistic_regression | 1480 | 0.5976 | 0.4613 |
| standard_cv | face | face_self_intro_native |  | self_intro | demographics | random_forest | 3572 | 0.6728 | 0.4259 |
| standard_cv | face | face_self_intro_native |  | self_intro | demographics_group | logistic_regression | 3572 | 0.7083 | 0.4955 |
| standard_cv | face | face_self_intro_native |  | self_intro | group_proxy_only | logistic_regression | 3572 | 0.6768 | 0.4653 |
| standard_cv | face | face_self_intro_native |  | self_intro | face | logistic_regression | 3565 | 0.6451 | 0.4177 |
| standard_cv | face | face_two_video_native |  | two_video | background | random_forest | 3567 | 0.6283 | 0.3979 |
| standard_cv | face | face_two_video_native |  | two_video | full_frame | logistic_regression | 3567 | 0.6452 | 0.4146 |
| standard_cv | face | face_two_video_native |  | two_video | metadata | logistic_regression | 3567 | 0.5553 | 0.3361 |
| standard_cv | face | face_self_intro_native |  | self_intro | face_demographics | logistic_regression | 3565 | 0.6802 | 0.4455 |
| standard_cv | face | face_two_video_native |  | two_video | face_qc_demographics | logistic_regression | 3567 | 0.6955 | 0.4629 |
| standard_cv | face | face_two_video_native |  | two_video | background_demographics | logistic_regression | 3567 | 0.6819 | 0.4453 |
| standard_cv | face | face_two_video_native |  | two_video | qc_demographics | hist_gradient_boosting | 3567 | 0.6929 | 0.4580 |
| group_cv | face | face_self_intro_native |  | self_intro | demographics | logistic_regression | 3572 | 0.6608 | 0.4252 |
| group_cv | face | face_self_intro_native |  | self_intro | demographics_group | logistic_regression | 3572 | 0.6710 | 0.4410 |
| group_cv | face | core3_rest_yiruidvft_selfintro_intersection |  | self_intro | group_proxy_only | random_forest | 661 | 0.5421 | 0.3624 |
| group_cv | face | face_two_video_native |  | two_video | face | logistic_regression | 3567 | 0.6343 | 0.4102 |
| group_cv | face | face_two_video_native |  | two_video | background | hist_gradient_boosting | 3567 | 0.5893 | 0.3637 |
| group_cv | face | face_task_native |  | task | full_frame | logistic_regression | 3567 | 0.6197 | 0.3877 |
| group_cv | face | face_task_native |  | task | metadata | logistic_regression | 3567 | 0.5454 | 0.3313 |
| group_cv | face | face_self_intro_native |  | self_intro | face_demographics | hist_gradient_boosting | 3565 | 0.6627 | 0.4253 |
| group_cv | face | face_two_video_native |  | two_video | face_qc_demographics | logistic_regression | 3567 | 0.6856 | 0.4558 |
| group_cv | face | face_task_native |  | task | background_demographics | random_forest | 3558 | 0.6715 | 0.4314 |
| group_cv | face | face_two_video_native |  | two_video | qc_demographics | hist_gradient_boosting | 3567 | 0.6892 | 0.4535 |

## Demographics and Group Contribution

Demographics are a major predictor. In the largest Face cohorts, age+sex+grade reaches about 0.67 AUROC, while adding group proxy lifts the best row to about 0.71 AUROC in Standard CV. Group-aware CV reduces group-proxy-heavy rows, confirming acquisition-group shortcut risk.

| cv_protocol | feature_set | modality | cohort_name | task | model | n_subjects | auroc | auprc |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| standard_cv | age_only | face | face_self_intro_native | self_intro | hist_gradient_boosting | 3572 | 0.6244 | 0.3735 |
| standard_cv | sex_only | face | face_self_intro_native | self_intro | random_forest | 3572 | 0.5927 | 0.3567 |
| standard_cv | grade_only | face | face_self_intro_native | self_intro | logistic_regression | 3572 | 0.6370 | 0.3858 |
| standard_cv | grade_group_only | face | face_task_native | task | random_forest | 3567 | 0.6017 | 0.3578 |
| standard_cv | age_sex | face | face_self_intro_native | self_intro | hist_gradient_boosting | 3572 | 0.6663 | 0.4108 |
| standard_cv | age_grade | face | face_self_intro_native | self_intro | logistic_regression | 3572 | 0.6399 | 0.4012 |
| standard_cv | sex_grade | face | face_self_intro_native | self_intro | hist_gradient_boosting | 3572 | 0.6709 | 0.4202 |
| standard_cv | age_sex_grade | face | face_self_intro_native | self_intro | random_forest | 3572 | 0.6728 | 0.4259 |
| standard_cv | age_sex_grade_group | face | face_self_intro_native | self_intro | random_forest | 3572 | 0.6720 | 0.4238 |
| standard_cv | group_proxy_only | face | face_self_intro_native | self_intro | logistic_regression | 3572 | 0.6768 | 0.4653 |
| standard_cv | demographics_group | face | face_self_intro_native | self_intro | logistic_regression | 3572 | 0.7083 | 0.4955 |
| standard_cv | demographics_group_device | face | face_self_intro_native | self_intro | logistic_regression | 3572 | 0.7073 | 0.4969 |
| standard_cv | demographics | face | face_self_intro_native | self_intro | random_forest | 3572 | 0.6728 | 0.4259 |
| group_cv | age_only | face | face_self_intro_native | self_intro | logistic_regression | 3572 | 0.6193 | 0.3640 |
| group_cv | sex_only | face | face_task_native | task | logistic_regression | 3567 | 0.6013 | 0.3814 |
| group_cv | grade_only | face | face_self_intro_native | self_intro | hist_gradient_boosting | 3572 | 0.6268 | 0.3799 |
| group_cv | grade_group_only | face | face_self_intro_native | self_intro | hist_gradient_boosting | 3572 | 0.5503 | 0.3194 |
| group_cv | age_sex | face | face_task_native | task | random_forest | 3567 | 0.6552 | 0.4079 |
| group_cv | age_grade | face | face_self_intro_native | self_intro | random_forest | 3572 | 0.6281 | 0.3825 |
| group_cv | sex_grade | face | face_self_intro_native | self_intro | logistic_regression | 3572 | 0.6617 | 0.4179 |
| group_cv | age_sex_grade | face | face_self_intro_native | self_intro | logistic_regression | 3572 | 0.6608 | 0.4252 |
| group_cv | age_sex_grade_group | face | face_self_intro_native | self_intro | logistic_regression | 3572 | 0.6607 | 0.4245 |
| group_cv | group_proxy_only | eeg | eeg_1back_native | 1back | logistic_regression | 1154 | 0.5778 | 0.3345 |
| group_cv | demographics_group | face | face_self_intro_native | self_intro | logistic_regression | 3572 | 0.6710 | 0.4410 |
| group_cv | demographics_group_device | face | face_self_intro_native | self_intro | logistic_regression | 3572 | 0.6775 | 0.4413 |
| group_cv | demographics | face | face_self_intro_native | self_intro | logistic_regression | 3572 | 0.6608 | 0.4252 |

## Event Semantics and Blocked Tasks

Oddball and 1BACK EEG task-condition claims remain blocked because project-local event semantics are not proven. fNIRS task-response claims remain blocked unless timing is marker-confirmed or protocol-confirmed; no 20/60/20 fallback is used, and Bikom is read without the Goal 2.6 2000-row cap.

EEG validity:

| modality | device | task | event_validity_status | subjects |
| --- | --- | --- | --- | --- |
| eeg |  | rest | event_free_rest | 1033 |
| eeg |  | oddball | blocked_target_nontarget_semantics_unconfirmed_target_only_proxy | 1837 |
| eeg |  | 1back | blocked_condition_semantics_unconfirmed_generic_signal_only | 1345 |

fNIRS validity:

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

## Required Independent Increment Tests

Native EEG/fNIRS comparisons are generally negative after controlling for demographics or QC+demographics. Face native comparisons show strict visual signal versus background/metadata/QC, but the required independent increments over demographics and QC+demographics mostly cross 0 or are negative.

Positive required increments with AUROC CI above 0:

| cv_protocol | modality | cohort_name | task | model | comparison | n_subjects | auroc_diff | auroc_diff_ci_low | auroc_diff_ci_high | fold_direction_consistency | protocol_consistent_direction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| group_cv | face | core3_rest_yiruidvft_selfintro_intersection | self_intro | random_forest | modality_demographics_vs_demographics | 661 | 0.0656 | 0.0129 | 0.1245 | 4 | 1 |
| group_cv | face | core3_rest_yiruidvft_selfintro_intersection | self_intro | hist_gradient_boosting | modality_demographics_vs_demographics | 661 | 0.0576 | 0.0012 | 0.1128 | 3 | 1 |
| standard_cv | face | core3_rest_yiruidvft_selfintro_intersection | self_intro | logistic_regression | modality_qc_demographics_vs_qc_demographics | 661 | 0.0449 | 0.0015 | 0.0918 | 5 | 1 |

Largest negative required increments:

| cv_protocol | modality | cohort_name | task | model | comparison | n_subjects | auroc_diff | auroc_diff_ci_low | auroc_diff_ci_high | fold_direction_consistency | protocol_consistent_direction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| standard_cv | fnirs | fnirs_bikom_rest_native | rest | logistic_regression | signal_demographics_vs_demographics | 1017 | -0.1065 | -0.1507 | -0.0632 | 0 | 1 |
| standard_cv | fnirs | fnirs_bikom_rest_native | rest | logistic_regression | signal_qc_demographics_vs_qc_demographics | 1017 | -0.1051 | -0.1460 | -0.0623 | 0 | 1 |
| group_cv | fnirs | fnirs_bikom_rest_native | rest | random_forest | signal_qc_demographics_vs_qc_demographics | 1017 | -0.0919 | -0.1401 | -0.0468 | 1 | 1 |
| group_cv | fnirs | fnirs_bikom_rest_native | rest | logistic_regression | signal_demographics_vs_demographics | 1017 | -0.0908 | -0.1314 | -0.0490 | 0 | 1 |
| group_cv | fnirs | fnirs_bikom_vft_native | vft | random_forest | signal_demographics_vs_demographics | 1022 | -0.0891 | -0.1341 | -0.0422 | 1 | 1 |
| standard_cv | eeg | eeg_rest_native | rest | hist_gradient_boosting | signal_demographics_vs_demographics | 1022 | -0.0848 | -0.1266 | -0.0407 | 0 | 1 |
| standard_cv | eeg | core3_rest_yiruidvft_selfintro_intersection | rest | random_forest | modality_qc_demographics_vs_qc_demographics | 661 | -0.0838 | -0.1385 | -0.0276 | 0 | 1 |
| group_cv | fnirs | fnirs_bikom_rest_native | rest | hist_gradient_boosting | signal_demographics_vs_demographics | 1017 | -0.0835 | -0.1328 | -0.0329 | 0 | 1 |
| group_cv | eeg | eeg_rest_native | rest | random_forest | signal_qc_demographics_vs_qc_demographics | 1022 | -0.0824 | -0.1251 | -0.0405 | 0 | 1 |
| group_cv | fnirs | fnirs_yiruid_1back_native | 1back | random_forest | signal_demographics_vs_demographics | 1422 | -0.0808 | -0.1163 | -0.0425 | 1 | 1 |
| group_cv | fnirs | fnirs_bikom_rest_native | rest | random_forest | signal_demographics_vs_demographics | 1017 | -0.0803 | -0.1295 | -0.0317 | 0 | 1 |
| group_cv | eeg | core3_rest_yiruidvft_selfintro_intersection | rest | hist_gradient_boosting | modality_qc_demographics_vs_qc_demographics | 661 | -0.0793 | -0.1396 | -0.0218 | 1 | 1 |
| group_cv | eeg | eeg_rest_native | rest | logistic_regression | signal_qc_demographics_vs_qc_demographics | 1022 | -0.0793 | -0.1127 | -0.0449 | 0 | 1 |
| standard_cv | eeg | core3_rest_yiruidvft_selfintro_intersection | rest | random_forest | modality_demographics_vs_demographics | 661 | -0.0778 | -0.1362 | -0.0170 | 0 | 1 |
| standard_cv | eeg | core3_rest_yiruidvft_selfintro_intersection | rest | hist_gradient_boosting | modality_qc_demographics_vs_qc_demographics | 661 | -0.0758 | -0.1354 | -0.0210 | 0 | 1 |
| standard_cv | eeg | eeg_rest_native | rest | random_forest | signal_demographics_vs_demographics | 1022 | -0.0742 | -0.1172 | -0.0303 | 0 | 1 |
| group_cv | fnirs | fnirs_bikom_rest_native | rest | logistic_regression | signal_qc_demographics_vs_qc_demographics | 1017 | -0.0716 | -0.1124 | -0.0271 | 1 | 1 |
| standard_cv | fnirs | fnirs_bikom_vft_native | vft | logistic_regression | signal_qc_demographics_vs_qc_demographics | 1022 | -0.0712 | -0.1162 | -0.0257 | 0 | 1 |
| group_cv | fnirs | fnirs_bikom_rest_native | rest | hist_gradient_boosting | signal_qc_demographics_vs_qc_demographics | 1017 | -0.0693 | -0.1192 | -0.0231 | 1 | 1 |
| group_cv | eeg | eeg_1back_native | 1back | random_forest | signal_demographics_vs_demographics | 1154 | -0.0686 | -0.1147 | -0.0258 | 1 | 1 |
| standard_cv | fnirs | fnirs_bikom_vft_native | vft | logistic_regression | signal_demographics_vs_demographics | 1022 | -0.0684 | -0.1140 | -0.0259 | 0 | 1 |
| group_cv | eeg | eeg_rest_native | rest | random_forest | signal_demographics_vs_demographics | 1022 | -0.0673 | -0.1118 | -0.0216 | 1 | 1 |
| standard_cv | fnirs | fnirs_bikom_1back_native | 1back | hist_gradient_boosting | signal_demographics_vs_demographics | 985 | -0.0670 | -0.1148 | -0.0215 | 0 | 1 |
| standard_cv | fnirs | fnirs_bikom_rest_native | rest | random_forest | signal_demographics_vs_demographics | 1017 | -0.0654 | -0.1132 | -0.0157 | 0 | 1 |
| group_cv | eeg | eeg_rest_native | rest | logistic_regression | signal_demographics_vs_demographics | 1022 | -0.0654 | -0.1017 | -0.0253 | 1 | 1 |

## Face Strict Controls

Face extraction used `torchvision_resnet18` with `ResNet18_Weights.IMAGENET1K_V1`, frozen=True, feature_dim=512, device=cuda:0. Detector preference was `opencv_yunet` with checkpoint `artifacts/goal2_7/face/models/face_detection_yunet_2023mar.onnx` and fallback `opencv_haar`; fallback usage is explicitly recorded and high in this environment. self_intro: signal n=3572, QC n=3597, sample_frames=16, task: signal n=3567, QC n=3597, sample_frames=16.

| task | n_videos | strict_face_valid_videos | blocked_videos | mean_detection_rate | mean_effective_face_frames | fallback_videos | multi_face_rate_mean | audio_used_sum |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| self_intro | 3597 | 3565 | 32 | 0.9904 | 15.8365 | 3572 | 0.0234 | 0 |
| task | 3597 | 3558 | 39 | 0.9831 | 15.7199 | 3567 | 0.0217 | 0 |

Face control paired comparisons show face-only is usually above background/metadata/QC, but face+demographics is close to background+demographics and does not reliably exceed demographics.

| cv_protocol | cohort_name | task | model | comparison | n_subjects | auroc_diff | auroc_diff_ci_low | auroc_diff_ci_high | fold_direction_consistency | protocol_consistent_direction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| group_cv | face_self_intro_native | self_intro | hist_gradient_boosting | face_demographics_vs_background_demographics | 3565 | 0.0103 | -0.0026 | 0.0233 | 5 | 1 |
| group_cv | face_self_intro_native | self_intro | logistic_regression | face_demographics_vs_background_demographics | 3565 | 0.0013 | -0.0090 | 0.0124 | 2 | 0 |
| group_cv | face_self_intro_native | self_intro | random_forest | face_demographics_vs_background_demographics | 3565 | -0.0029 | -0.0194 | 0.0130 | 3 | 0 |
| group_cv | face_self_intro_native | self_intro | hist_gradient_boosting | face_demographics_vs_demographics | 3565 | 0.0066 | -0.0061 | 0.0197 | 4 | 1 |
| group_cv | face_self_intro_native | self_intro | logistic_regression | face_demographics_vs_demographics | 3565 | -0.0017 | -0.0127 | 0.0091 | 1 | 0 |
| group_cv | face_self_intro_native | self_intro | random_forest | face_demographics_vs_demographics | 3565 | -0.0280 | -0.0409 | -0.0132 | 2 | 0 |
| group_cv | face_self_intro_native | self_intro | hist_gradient_boosting | face_qc_demographics_vs_qc_demographics | 3565 | 0.0062 | -0.0057 | 0.0178 | 5 | 1 |
| group_cv | face_self_intro_native | self_intro | logistic_regression | face_qc_demographics_vs_qc_demographics | 3565 | -0.0079 | -0.0175 | 0.0030 | 0 | 0 |
| group_cv | face_self_intro_native | self_intro | random_forest | face_qc_demographics_vs_qc_demographics | 3565 | -0.0003 | -0.0108 | 0.0105 | 3 | 1 |
| group_cv | face_self_intro_native | self_intro | hist_gradient_boosting | face_vs_background | 3565 | 0.0174 | -0.0070 | 0.0416 | 5 | 1 |
| group_cv | face_self_intro_native | self_intro | logistic_regression | face_vs_background | 3565 | 0.0516 | 0.0297 | 0.0729 | 5 | 1 |
| group_cv | face_self_intro_native | self_intro | random_forest | face_vs_background | 3565 | 0.0343 | 0.0088 | 0.0596 | 5 | 1 |
| group_cv | face_self_intro_native | self_intro | hist_gradient_boosting | face_vs_full_frame | 3565 | 0.0050 | -0.0158 | 0.0271 | 5 | 1 |
| group_cv | face_self_intro_native | self_intro | logistic_regression | face_vs_full_frame | 3565 | 0.0149 | -0.0046 | 0.0334 | 5 | 1 |
| group_cv | face_self_intro_native | self_intro | random_forest | face_vs_full_frame | 3565 | 0.0692 | 0.0491 | 0.0917 | 5 | 1 |
| group_cv | face_self_intro_native | self_intro | hist_gradient_boosting | face_vs_metadata | 3565 | 0.1100 | 0.0828 | 0.1406 | 5 | 1 |
| group_cv | face_self_intro_native | self_intro | logistic_regression | face_vs_metadata | 3565 | 0.1375 | 0.1110 | 0.1648 | 5 | 1 |
| group_cv | face_self_intro_native | self_intro | random_forest | face_vs_metadata | 3565 | 0.1365 | 0.1074 | 0.1670 | 5 | 1 |
| group_cv | face_self_intro_native | self_intro | hist_gradient_boosting | face_vs_qc | 3565 | 0.0698 | 0.0444 | 0.0950 | 5 | 1 |
| group_cv | face_self_intro_native | self_intro | logistic_regression | face_vs_qc | 3565 | 0.0831 | 0.0593 | 0.1069 | 5 | 1 |
| group_cv | face_self_intro_native | self_intro | random_forest | face_vs_qc | 3565 | 0.1048 | 0.0781 | 0.1297 | 5 | 1 |
| group_cv | face_task_native | task | hist_gradient_boosting | face_demographics_vs_background_demographics | 3558 | -0.0103 | -0.0236 | 0.0015 | 3 | 1 |
| group_cv | face_task_native | task | logistic_regression | face_demographics_vs_background_demographics | 3558 | 0.0021 | -0.0094 | 0.0130 | 2 | 0 |
| group_cv | face_task_native | task | random_forest | face_demographics_vs_background_demographics | 3558 | -0.0255 | -0.0384 | -0.0120 | 3 | 1 |
| group_cv | face_task_native | task | hist_gradient_boosting | face_demographics_vs_demographics | 3558 | -0.0123 | -0.0252 | 0.0008 | 1 | 0 |
| group_cv | face_task_native | task | logistic_regression | face_demographics_vs_demographics | 3558 | -0.0010 | -0.0109 | 0.0088 | 0 | 0 |
| group_cv | face_task_native | task | random_forest | face_demographics_vs_demographics | 3558 | -0.0127 | -0.0238 | -0.0008 | 1 | 0 |
| group_cv | face_task_native | task | hist_gradient_boosting | face_qc_demographics_vs_qc_demographics | 3558 | -0.0060 | -0.0144 | 0.0019 | 0 | 0 |
| group_cv | face_task_native | task | logistic_regression | face_qc_demographics_vs_qc_demographics | 3558 | -0.0040 | -0.0129 | 0.0055 | 1 | 1 |
| group_cv | face_task_native | task | random_forest | face_qc_demographics_vs_qc_demographics | 3558 | -0.0156 | -0.0262 | -0.0056 | 0 | 1 |
| group_cv | face_task_native | task | hist_gradient_boosting | face_vs_background | 3558 | 0.0240 | 0.0017 | 0.0456 | 4 | 1 |
| group_cv | face_task_native | task | logistic_regression | face_vs_background | 3558 | 0.0388 | 0.0187 | 0.0598 | 5 | 1 |
| group_cv | face_task_native | task | random_forest | face_vs_background | 3558 | 0.0549 | 0.0308 | 0.0799 | 4 | 1 |
| group_cv | face_task_native | task | hist_gradient_boosting | face_vs_full_frame | 3558 | -0.0062 | -0.0270 | 0.0152 | 3 | 0 |
| group_cv | face_task_native | task | logistic_regression | face_vs_full_frame | 3558 | 0.0079 | -0.0079 | 0.0248 | 3 | 1 |
| group_cv | face_task_native | task | random_forest | face_vs_full_frame | 3558 | -0.0170 | -0.0381 | 0.0027 | 3 | 0 |
| group_cv | face_task_native | task | hist_gradient_boosting | face_vs_metadata | 3558 | 0.0628 | 0.0338 | 0.0918 | 5 | 1 |
| group_cv | face_task_native | task | logistic_regression | face_vs_metadata | 3558 | 0.0829 | 0.0542 | 0.1136 | 4 | 1 |
| group_cv | face_task_native | task | random_forest | face_vs_metadata | 3558 | 0.0699 | 0.0437 | 0.1003 | 5 | 1 |
| group_cv | face_task_native | task | hist_gradient_boosting | face_vs_qc | 3558 | 0.0622 | 0.0366 | 0.0896 | 5 | 1 |
| group_cv | face_task_native | task | logistic_regression | face_vs_qc | 3558 | 0.0665 | 0.0402 | 0.0921 | 5 | 1 |
| group_cv | face_task_native | task | random_forest | face_vs_qc | 3558 | 0.0559 | 0.0293 | 0.0818 | 5 | 1 |
| group_cv | face_two_video_native | two_video | hist_gradient_boosting | face_demographics_vs_background_demographics | 3567 | 0.0131 | 0.0000 | 0.0261 | 5 | 1 |
| group_cv | face_two_video_native | two_video | logistic_regression | face_demographics_vs_background_demographics | 3567 | 0.0062 | -0.0056 | 0.0168 | 2 | 0 |
| group_cv | face_two_video_native | two_video | random_forest | face_demographics_vs_background_demographics | 3567 | -0.0490 | -0.0654 | -0.0318 | 3 | 0 |
| group_cv | face_two_video_native | two_video | hist_gradient_boosting | face_demographics_vs_demographics | 3567 | -0.0021 | -0.0149 | 0.0108 | 3 | 0 |
| group_cv | face_two_video_native | two_video | logistic_regression | face_demographics_vs_demographics | 3567 | 0.0009 | -0.0097 | 0.0119 | 2 | 1 |
| group_cv | face_two_video_native | two_video | random_forest | face_demographics_vs_demographics | 3567 | -0.0368 | -0.0514 | -0.0220 | 1 | 0 |
| group_cv | face_two_video_native | two_video | hist_gradient_boosting | face_qc_demographics_vs_qc_demographics | 3567 | -0.0095 | -0.0179 | -0.0002 | 2 | 1 |
| group_cv | face_two_video_native | two_video | logistic_regression | face_qc_demographics_vs_qc_demographics | 3567 | -0.0016 | -0.0108 | 0.0078 | 2 | 0 |
| group_cv | face_two_video_native | two_video | random_forest | face_qc_demographics_vs_qc_demographics | 3567 | 0.0026 | -0.0072 | 0.0128 | 4 | 1 |
| group_cv | face_two_video_native | two_video | hist_gradient_boosting | face_vs_background | 3567 | 0.0320 | 0.0094 | 0.0553 | 4 | 1 |
| group_cv | face_two_video_native | two_video | logistic_regression | face_vs_background | 3567 | 0.0573 | 0.0386 | 0.0751 | 5 | 1 |
| group_cv | face_two_video_native | two_video | random_forest | face_vs_background | 3567 | 0.0743 | 0.0513 | 0.0978 | 5 | 1 |
| group_cv | face_two_video_native | two_video | hist_gradient_boosting | face_vs_full_frame | 3567 | 0.0196 | 0.0006 | 0.0391 | 4 | 1 |
| group_cv | face_two_video_native | two_video | logistic_regression | face_vs_full_frame | 3567 | 0.0177 | 0.0023 | 0.0343 | 5 | 0 |
| group_cv | face_two_video_native | two_video | random_forest | face_vs_full_frame | 3567 | 0.0360 | 0.0154 | 0.0575 | 3 | 0 |
| group_cv | face_two_video_native | two_video | hist_gradient_boosting | face_vs_metadata | 3567 | 0.0764 | 0.0472 | 0.1071 | 5 | 1 |
| group_cv | face_two_video_native | two_video | logistic_regression | face_vs_metadata | 3567 | 0.0896 | 0.0590 | 0.1214 | 5 | 1 |
| group_cv | face_two_video_native | two_video | random_forest | face_vs_metadata | 3567 | 0.0696 | 0.0408 | 0.0985 | 5 | 1 |

Showing first 60 of 126 rows.

## Standard vs Group CV Robustness

The largest Standard-minus-Group drops are group-proxy and acquisition-context rows, especially Face group proxy and Bikom/Yiruid group proxy. This confirms that Protocol B changes the shortcut landscape rather than serving as a minor appendix.

| cohort_name | modality | device | task | feature_set | model | auroc_standard_cv | auroc_group_cv | auroc_delta_standard_minus_group | auprc_standard_cv | auprc_group_cv |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| face_task_native | face |  | task | group_proxy_only | logistic_regression | 0.6768 | 0.4518 | 0.2249 | 0.4652 | 0.2953 |
| face_self_intro_native | face |  | self_intro | group_proxy_only | logistic_regression | 0.6768 | 0.4525 | 0.2243 | 0.4653 | 0.2952 |
| face_self_intro_native | face |  | self_intro | group_proxy_only | random_forest | 0.6762 | 0.4613 | 0.2150 | 0.4629 | 0.2996 |
| face_task_native | face |  | task | group_proxy_only | hist_gradient_boosting | 0.6728 | 0.4604 | 0.2124 | 0.4477 | 0.3002 |
| fnirs_bikom_vft_native | fnirs | bikom | vft | group_proxy_only | logistic_regression | 0.5900 | 0.3912 | 0.1989 | 0.3806 | 0.2642 |
| face_task_native | face |  | task | group_proxy_only | random_forest | 0.6755 | 0.4879 | 0.1876 | 0.4598 | 0.3137 |
| face_self_intro_native | face |  | self_intro | group_proxy_only | hist_gradient_boosting | 0.6734 | 0.4889 | 0.1845 | 0.4482 | 0.3170 |
| fnirs_bikom_rest_native | fnirs | bikom | rest | group_proxy_only | random_forest | 0.6002 | 0.4384 | 0.1619 | 0.3969 | 0.2962 |
| fnirs_bikom_1back_native | fnirs | bikom | 1back | group_proxy_only | logistic_regression | 0.5893 | 0.4284 | 0.1609 | 0.3747 | 0.2900 |
| fnirs_bikom_vft_native | fnirs | bikom | vft | group_proxy_only | random_forest | 0.5969 | 0.4380 | 0.1589 | 0.3885 | 0.2963 |
| fnirs_yiruid_vft_native | fnirs | yiruid | vft | group_proxy_only | hist_gradient_boosting | 0.6213 | 0.4638 | 0.1575 | 0.5081 | 0.3746 |
| eeg_oddball_native | eeg |  | oddball | group_proxy_only | logistic_regression | 0.6019 | 0.4454 | 0.1565 | 0.3881 | 0.3048 |
| fnirs_bikom_1back_native | fnirs | bikom | 1back | group_proxy_only | random_forest | 0.5958 | 0.4439 | 0.1519 | 0.3870 | 0.2972 |
| fnirs_yiruid_rest_native | fnirs | yiruid | rest | group_proxy_only | hist_gradient_boosting | 0.6245 | 0.4781 | 0.1464 | 0.5104 | 0.3850 |
| fnirs_yiruid_1back_native | fnirs | yiruid | 1back | group_proxy_only | logistic_regression | 0.6302 | 0.4892 | 0.1411 | 0.5119 | 0.3787 |
| fnirs_yiruid_rest_native | fnirs | yiruid | rest | group_proxy_only | random_forest | 0.6265 | 0.4855 | 0.1411 | 0.5107 | 0.3705 |
| fnirs_bikom_1back_native | fnirs | bikom | 1back | group_proxy_only | hist_gradient_boosting | 0.5933 | 0.4548 | 0.1385 | 0.3836 | 0.3017 |
| eeg_oddball_native | eeg |  | oddball | group_proxy_only | random_forest | 0.6040 | 0.4655 | 0.1385 | 0.3873 | 0.3177 |
| fnirs_yiruid_rest_native | fnirs | yiruid | rest | group_proxy_only | logistic_regression | 0.6278 | 0.4952 | 0.1326 | 0.5097 | 0.3799 |
| fnirs_yiruid_vft_native | fnirs | yiruid | vft | group_proxy_only | logistic_regression | 0.6268 | 0.4991 | 0.1277 | 0.5103 | 0.3885 |

## Core3 Same-Cohort Comparison

Core3 is explicitly `core3_rest_yiruidvft_selfintro_intersection` with n=661, not the full 2354-person core3 pool. Face has the only positive required Core3 increments, but they are not enough to override native-cohort shortcut risk.

| cv_protocol | modality | device | task | feature_set | model | n_subjects | auroc | auprc |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| group_cv | eeg |  | rest | demographics | logistic_regression | 661 | 0.5753 | 0.4008 |
| group_cv | eeg |  | rest | modality | logistic_regression | 661 | 0.4955 | 0.3329 |
| group_cv | eeg |  | rest | modality_demographics | logistic_regression | 661 | 0.5272 | 0.3483 |
| group_cv | eeg |  | rest | modality_qc_demographics | logistic_regression | 661 | 0.5150 | 0.3525 |
| group_cv | eeg |  | rest | qc_demographics | hist_gradient_boosting | 661 | 0.5789 | 0.3895 |
| group_cv | face |  | self_intro | demographics | logistic_regression | 661 | 0.5753 | 0.4008 |
| group_cv | face |  | self_intro | modality | logistic_regression | 661 | 0.6084 | 0.4527 |
| group_cv | face |  | self_intro | modality_demographics | logistic_regression | 661 | 0.6214 | 0.4493 |
| group_cv | face |  | self_intro | modality_qc_demographics | logistic_regression | 661 | 0.5855 | 0.4249 |
| group_cv | face |  | self_intro | qc_demographics | logistic_regression | 661 | 0.5716 | 0.3969 |
| group_cv | fnirs | yiruid | vft | demographics | logistic_regression | 661 | 0.5753 | 0.4008 |
| group_cv | fnirs | yiruid | vft | modality | random_forest | 661 | 0.5580 | 0.4161 |
| group_cv | fnirs | yiruid | vft | modality_demographics | random_forest | 661 | 0.5632 | 0.4149 |
| group_cv | fnirs | yiruid | vft | modality_qc_demographics | random_forest | 661 | 0.5693 | 0.4148 |
| group_cv | fnirs | yiruid | vft | qc_demographics | logistic_regression | 661 | 0.5815 | 0.4213 |
| standard_cv | eeg |  | rest | demographics | logistic_regression | 661 | 0.5767 | 0.3926 |
| standard_cv | eeg |  | rest | modality | logistic_regression | 661 | 0.5143 | 0.3575 |
| standard_cv | eeg |  | rest | modality_demographics | logistic_regression | 661 | 0.5486 | 0.3807 |
| standard_cv | eeg |  | rest | modality_qc_demographics | logistic_regression | 661 | 0.5544 | 0.3890 |
| standard_cv | eeg |  | rest | qc_demographics | hist_gradient_boosting | 661 | 0.5868 | 0.3994 |
| standard_cv | face |  | self_intro | demographics | logistic_regression | 661 | 0.5767 | 0.3926 |
| standard_cv | face |  | self_intro | modality | random_forest | 661 | 0.5794 | 0.4057 |
| standard_cv | face |  | self_intro | modality_demographics | random_forest | 661 | 0.6016 | 0.4209 |
| standard_cv | face |  | self_intro | modality_qc_demographics | logistic_regression | 661 | 0.6019 | 0.4306 |
| standard_cv | face |  | self_intro | qc_demographics | random_forest | 661 | 0.5999 | 0.4280 |
| standard_cv | fnirs | yiruid | vft | demographics | logistic_regression | 661 | 0.5767 | 0.3926 |
| standard_cv | fnirs | yiruid | vft | modality | hist_gradient_boosting | 661 | 0.5987 | 0.4593 |
| standard_cv | fnirs | yiruid | vft | modality_demographics | hist_gradient_boosting | 661 | 0.6003 | 0.4666 |
| standard_cv | fnirs | yiruid | vft | modality_qc_demographics | hist_gradient_boosting | 661 | 0.5879 | 0.4625 |
| standard_cv | fnirs | yiruid | vft | qc_demographics | logistic_regression | 661 | 0.5990 | 0.4488 |

## Goal 2.6 Conclusions Retained or Revised

- Retained: EEG and fNIRS remain weak/uncertain and do not show stable independent increments over demographics/QC.
- Retained: Face remains shortcut-risk because demographics, group proxy, and background+demographics explain much of the top-line performance.
- Revised: Face strict crop is now cleaner: failed detections no longer become center crops, background masks detected faces, and visual PCA is separated from demographics/QC. Face-only still beats background/metadata in many paired tests, so the visual branch is not simply a metadata-only artifact.
- Revised: Oddball is no longer reported as full target/non-target ERP; it is `oddball_target_only_proxy`. 1BACK condition differences are blocked. fNIRS task response is not interpreted without confirmed timing, and Bikom is no longer capped at 2000 rows.

## Modality Status and Next Goal

| modality | status | evidence | decision |
| --- | --- | --- | --- |
| EEG | BLOCKED_BY_INVALID_TASK_SEMANTICS + NO_CLEAR_SIGNAL | Oddball target/non-target and 1BACK condition semantics are unconfirmed; native required increments are mostly negative and often significantly below demographics/QC+demographics. | Do not start EEGNet/InceptionTime; first recover event semantics or restrict to clearly event-free Rest. |
| fNIRS | BLOCKED_BY_INVALID_TASK_SEMANTICS + NO_CLEAR_SIGNAL | Task-response timing is unconfirmed or blocked; Yiruid VFT has the best point estimates but paired increments over demographics/QC+demographics do not clear CI under Group CV. | Do not start fNIRS deep models; first confirm task timing and HbO/HbR semantics. |
| Face | SHORTCUT_DOMINATED | Strict face-only beats background/metadata/QC in many controls, but demographics_group and group_proxy are stronger and face+demographics does not reliably beat demographics. | Treat as shortcut-risk; replicate under stronger group/demographic controls before any video deep model. |

No modality should move directly into a full deep-model Goal on the basis of Goal 2.7 alone. The single most useful next Goal is a Goal 2.8 remediation/decision gate: recover and document EEG/fNIRS event timing, add explicit group-balanced or residualized demographic baselines, and decide whether Face warrants a stricter shortcut-controlled replication before any Goal 3/4/5 deep training.
