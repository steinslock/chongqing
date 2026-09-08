# Goal 2.8 Results

Goal 2.8 rebuilt every feature layer from the paradigm specification and reran the
Goal 2.7 protocol unchanged: the same fixed folds, the same inner-CV selection, the
same model families, the same 1000-resample bootstrap. Only the features are new.

Bikom is excluded from the primary matrix. Its cohort is disjoint from Yiruid's
(one shared subject), so device cannot be separated from acquisition site, and its
features carry no univariate label signal.

## Modality Decision

| modality | demographic_increment_rows | positive_over_demographics_standard_cv | positive_over_demographics_group_cv | negative_over_demographics | positive_over_shortcut_controls | decision |
| --- | --- | --- | --- | --- | --- | --- |
| eeg | 72 | 0 | 0 | 43 | 0 | NO_INDEPENDENT_SIGNAL |
| face | 24 | 0 | 0 | 16 | 14 | NO_INDEPENDENT_SIGNAL |
| fnirs | 120 | 0 | 0 | 19 | 0 | NO_INDEPENDENT_SIGNAL |

A modality is only credited with independent signal when an increment **over
demographics** has a paired bootstrap AUROC interval excluding zero under **both** CV
protocols. Beating a background or QC baseline is reported separately: it shows the
modality carries more than the room or the recording conditions, not that it adds
anything a questionnaire does not already supply.

## Required Increments

Positive and significant: **14** of 240 rows.
Negative and significant: **79**.

| cv_protocol | cohort_name | modality | device | task | model | comparison | auroc_diff | auroc_diff_ci_low | auroc_diff_ci_high | significant_positive | significant_negative |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| group_cv | face_segment_raw | face |  | task | hist_gradient_boosting | face_vs_background | 0.0511 | 0.0278 | 0.0768 | 1 | 0 |
| group_cv | face_segment_raw | face |  | task | logistic_regression | face_vs_background | 0.0582 | 0.0358 | 0.0810 | 1 | 0 |
| group_cv | face_segment_raw | face |  | task | random_forest | face_vs_background | 0.0427 | 0.0159 | 0.0686 | 1 | 0 |
| group_cv | face_valence_contrast | face |  | task | hist_gradient_boosting | face_vs_background | 0.0353 | 0.0073 | 0.0662 | 1 | 0 |
| group_cv | face_valence_contrast | face |  | task | logistic_regression | face_vs_background | 0.0472 | 0.0173 | 0.0786 | 1 | 0 |
| group_cv | face_valence_contrast | face |  | task | logistic_regression | face_demographics_vs_background_demographics | 0.0134 | 0.0020 | 0.0245 | 1 | 0 |
| group_cv | face_valence_contrast | face |  | task | random_forest | face_vs_background | 0.1153 | 0.0858 | 0.1450 | 1 | 0 |
| group_cv | face_valence_contrast | face |  | task | random_forest | face_demographics_vs_background_demographics | 0.0130 | 0.0004 | 0.0245 | 1 | 0 |
| standard_cv | face_segment_raw | face |  | task | logistic_regression | face_vs_background | 0.0223 | 0.0005 | 0.0434 | 1 | 0 |
| standard_cv | face_valence_contrast | face |  | task | hist_gradient_boosting | face_vs_background | 0.0289 | 0.0023 | 0.0537 | 1 | 0 |
| standard_cv | face_valence_contrast | face |  | task | logistic_regression | face_vs_background | 0.0622 | 0.0332 | 0.0896 | 1 | 0 |
| standard_cv | face_valence_contrast | face |  | task | logistic_regression | face_demographics_vs_background_demographics | 0.0139 | 0.0026 | 0.0255 | 1 | 0 |
| standard_cv | face_valence_contrast | face |  | task | random_forest | face_vs_background | 0.0353 | 0.0103 | 0.0608 | 1 | 0 |
| standard_cv | face_valence_contrast | face |  | task | random_forest | face_demographics_vs_background_demographics | 0.0149 | 0.0024 | 0.0262 | 1 | 0 |

## Best Row Per Feature Set

| cv_protocol | modality | cohort_name | device | task | feature_set | model | n_subjects | auroc | auprc |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| group_cv | eeg | eeg_1back_native |  | 1back | age_grade | logistic_regression | 1278 | 0.5393 | 0.3347 |
| group_cv | eeg | eeg_1back_native |  | 1back | age_only | logistic_regression | 1278 | 0.5465 | 0.3315 |
| group_cv | eeg | eeg_1back_native |  | 1back | age_sex | logistic_regression | 1278 | 0.5913 | 0.3756 |
| group_cv | eeg | eeg_1back_native |  | 1back | age_sex_grade | logistic_regression | 1278 | 0.5947 | 0.3842 |
| group_cv | eeg | eeg_1back_native |  | 1back | age_sex_grade_group | logistic_regression | 1278 | 0.5944 | 0.3801 |
| group_cv | eeg | eeg_1back_native |  | 1back | demographics | logistic_regression | 1278 | 0.5947 | 0.3842 |
| group_cv | eeg | eeg_1back_native |  | 1back | demographics_group | logistic_regression | 1278 | 0.5874 | 0.3855 |
| group_cv | eeg | eeg_1back_native |  | 1back | demographics_group_device | logistic_regression | 1278 | 0.5826 | 0.3880 |
| group_cv | eeg | eeg_1back_native |  | 1back | fnirs_device_only | random_forest | 1278 | 0.4210 | 0.2677 |
| group_cv | eeg | eeg_1back_native |  | 1back | grade_group_only | random_forest | 1278 | 0.4977 | 0.3140 |
| group_cv | eeg | eeg_1back_native |  | 1back | grade_only | hist_gradient_boosting | 1278 | 0.5284 | 0.3295 |
| group_cv | eeg | eeg_1back_native |  | 1back | group_proxy_only | logistic_regression | 1278 | 0.4499 | 0.2780 |
| group_cv | eeg | eeg_1back_native |  | 1back | no_information | no_information_prior | 1278 | 0.3859 | 0.2604 |
| group_cv | eeg | eeg_1back_native |  | 1back | qc | random_forest | 1278 | 0.4995 | 0.3086 |
| group_cv | eeg | eeg_1back_native |  | 1back | qc_demographics | logistic_regression | 1278 | 0.5790 | 0.3616 |
| group_cv | eeg | eeg_1back_native |  | 1back | sex_grade | random_forest | 1278 | 0.5873 | 0.3533 |
| group_cv | eeg | eeg_1back_native |  | 1back | sex_only | hist_gradient_boosting | 1278 | 0.5670 | 0.3672 |
| group_cv | eeg | eeg_1back_native |  | 1back | signal | logistic_regression | 1278 | 0.5183 | 0.3027 |
| group_cv | eeg | eeg_1back_native |  | 1back | signal_demographics | logistic_regression | 1278 | 0.5591 | 0.3407 |
| group_cv | eeg | eeg_1back_native |  | 1back | signal_qc | logistic_regression | 1278 | 0.5129 | 0.2998 |
| group_cv | eeg | eeg_1back_native |  | 1back | signal_qc_demographics | logistic_regression | 1278 | 0.5533 | 0.3354 |
| group_cv | eeg | eeg_oddball_native |  | oddball | age_grade | logistic_regression | 1820 | 0.5352 | 0.3658 |
| group_cv | eeg | eeg_oddball_native |  | oddball | age_only | hist_gradient_boosting | 1820 | 0.5213 | 0.3455 |
| group_cv | eeg | eeg_oddball_native |  | oddball | age_sex | random_forest | 1820 | 0.5859 | 0.3980 |
| group_cv | eeg | eeg_oddball_native |  | oddball | age_sex_grade | logistic_regression | 1820 | 0.5935 | 0.4144 |
| group_cv | eeg | eeg_oddball_native |  | oddball | age_sex_grade_group | logistic_regression | 1820 | 0.5931 | 0.4106 |
| group_cv | eeg | eeg_oddball_native |  | oddball | demographics | logistic_regression | 1820 | 0.5935 | 0.4144 |
| group_cv | eeg | eeg_oddball_native |  | oddball | demographics_group | logistic_regression | 1820 | 0.5935 | 0.4161 |
| group_cv | eeg | eeg_oddball_native |  | oddball | demographics_group_device | random_forest | 1820 | 0.5893 | 0.4063 |
| group_cv | eeg | eeg_oddball_native |  | oddball | fnirs_device_only | hist_gradient_boosting | 1820 | 0.5041 | 0.3404 |
| group_cv | eeg | eeg_oddball_native |  | oddball | grade_group_only | random_forest | 1820 | 0.4565 | 0.3173 |
| group_cv | eeg | eeg_oddball_native |  | oddball | grade_only | random_forest | 1820 | 0.5366 | 0.3654 |
| group_cv | eeg | eeg_oddball_native |  | oddball | group_proxy_only | hist_gradient_boosting | 1820 | 0.5532 | 0.3672 |
| group_cv | eeg | eeg_oddball_native |  | oddball | no_information | no_information_prior | 1820 | 0.4014 | 0.2870 |
| group_cv | eeg | eeg_oddball_native |  | oddball | qc | random_forest | 1820 | 0.4841 | 0.3234 |
| group_cv | eeg | eeg_oddball_native |  | oddball | qc_demographics | logistic_regression | 1820 | 0.5854 | 0.4044 |
| group_cv | eeg | eeg_oddball_native |  | oddball | sex_grade | random_forest | 1820 | 0.5924 | 0.4050 |
| group_cv | eeg | eeg_oddball_native |  | oddball | sex_only | random_forest | 1820 | 0.5681 | 0.3898 |
| group_cv | eeg | eeg_oddball_native |  | oddball | signal | logistic_regression | 1820 | 0.5234 | 0.3430 |
| group_cv | eeg | eeg_oddball_native |  | oddball | signal_demographics | logistic_regression | 1820 | 0.5543 | 0.3758 |
| group_cv | eeg | eeg_oddball_native |  | oddball | signal_qc | logistic_regression | 1820 | 0.5207 | 0.3421 |
| group_cv | eeg | eeg_oddball_native |  | oddball | signal_qc_demographics | logistic_regression | 1820 | 0.5514 | 0.3761 |
| group_cv | eeg | eeg_rest_native |  | rest | age_grade | logistic_regression | 1003 | 0.5212 | 0.3583 |
| group_cv | eeg | eeg_rest_native |  | rest | age_only | logistic_regression | 1003 | 0.4881 | 0.3229 |
| group_cv | eeg | eeg_rest_native |  | rest | age_sex | logistic_regression | 1003 | 0.5761 | 0.3845 |
| group_cv | eeg | eeg_rest_native |  | rest | age_sex_grade | logistic_regression | 1003 | 0.5922 | 0.4181 |
| group_cv | eeg | eeg_rest_native |  | rest | age_sex_grade_group | logistic_regression | 1003 | 0.5855 | 0.4090 |
| group_cv | eeg | eeg_rest_native |  | rest | demographics | logistic_regression | 1003 | 0.5922 | 0.4181 |
| group_cv | eeg | eeg_rest_native |  | rest | demographics_group | logistic_regression | 1003 | 0.5875 | 0.4003 |
| group_cv | eeg | eeg_rest_native |  | rest | demographics_group_device | logistic_regression | 1003 | 0.5981 | 0.4202 |
| group_cv | eeg | eeg_rest_native |  | rest | fnirs_device_only | random_forest | 1003 | 0.4938 | 0.3367 |
| group_cv | eeg | eeg_rest_native |  | rest | grade_group_only | random_forest | 1003 | 0.4367 | 0.3245 |
| group_cv | eeg | eeg_rest_native |  | rest | grade_only | random_forest | 1003 | 0.5302 | 0.3716 |
| group_cv | eeg | eeg_rest_native |  | rest | group_proxy_only | hist_gradient_boosting | 1003 | 0.5018 | 0.3310 |
| group_cv | eeg | eeg_rest_native |  | rest | no_information | no_information_prior | 1003 | 0.4199 | 0.3009 |
| group_cv | eeg | eeg_rest_native |  | rest | qc | hist_gradient_boosting | 1003 | 0.4871 | 0.3480 |
| group_cv | eeg | eeg_rest_native |  | rest | qc_demographics | random_forest | 1003 | 0.5780 | 0.4110 |
| group_cv | eeg | eeg_rest_native |  | rest | sex_grade | logistic_regression | 1003 | 0.5940 | 0.4197 |
| group_cv | eeg | eeg_rest_native |  | rest | sex_only | random_forest | 1003 | 0.5910 | 0.4061 |
| group_cv | eeg | eeg_rest_native |  | rest | signal | hist_gradient_boosting | 1003 | 0.5187 | 0.3641 |
| group_cv | eeg | eeg_rest_native |  | rest | signal_demographics | hist_gradient_boosting | 1003 | 0.5640 | 0.3949 |
| group_cv | eeg | eeg_rest_native |  | rest | signal_qc | hist_gradient_boosting | 1003 | 0.5156 | 0.3601 |
| group_cv | eeg | eeg_rest_native |  | rest | signal_qc_demographics | hist_gradient_boosting | 1003 | 0.5558 | 0.3940 |
| group_cv | face | face_segment_raw |  | task | background | logistic_regression | 3381 | 0.5686 | 0.3618 |
| group_cv | face | face_segment_raw |  | task | background_demographics | logistic_regression | 3381 | 0.6573 | 0.4287 |
| group_cv | face | face_segment_raw |  | task | demographics | logistic_regression | 3381 | 0.6602 | 0.4240 |
| group_cv | face | face_segment_raw |  | task | face | logistic_regression | 3381 | 0.6268 | 0.3994 |
| group_cv | face | face_segment_raw |  | task | face_demographics | logistic_regression | 3381 | 0.6626 | 0.4351 |
| group_cv | face | face_segment_raw |  | task | face_qc | logistic_regression | 3381 | 0.6256 | 0.3983 |
| group_cv | face | face_segment_raw |  | task | face_qc_demographics | logistic_regression | 3381 | 0.6619 | 0.4342 |
| group_cv | face | face_segment_raw |  | task | full_frame | logistic_regression | 3381 | 0.5960 | 0.3759 |
| group_cv | face | face_segment_raw |  | task | no_information | no_information_prior | 3381 | 0.4033 | 0.2654 |
| group_cv | face | face_segment_raw |  | task | qc | random_forest | 3381 | 0.5578 | 0.3449 |
| group_cv | face | face_segment_raw |  | task | qc_demographics | hist_gradient_boosting | 3381 | 0.6594 | 0.4185 |
| group_cv | face | face_valence_contrast |  | task | background | hist_gradient_boosting | 3381 | 0.5112 | 0.3210 |
| group_cv | face | face_valence_contrast |  | task | background_demographics | logistic_regression | 3381 | 0.6525 | 0.4239 |
| group_cv | face | face_valence_contrast |  | task | demographics | logistic_regression | 3381 | 0.6602 | 0.4240 |
| group_cv | face | face_valence_contrast |  | task | face | random_forest | 3381 | 0.5664 | 0.3469 |
| group_cv | face | face_valence_contrast |  | task | face_demographics | logistic_regression | 3381 | 0.6659 | 0.4276 |
| group_cv | face | face_valence_contrast |  | task | face_qc | random_forest | 3381 | 0.5526 | 0.3369 |

Showing 80 of 380 rows.
