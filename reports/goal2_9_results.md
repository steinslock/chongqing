# Goal 2.9 Results

Goal 2.9 adds one feature layer that no earlier goal used: the trial-level
keypresses the paradigms recorded. The protocol is unchanged from Goal 2.7 and
Goal 2.8 - the same fixed folds, the same inner-CV selection, the same model
families and grids, the same 1000-resample bootstrap, the same pilot-holdout
exclusion. Only the features are new.

## Unit Decision

| unit | demographic_increment_rows | positive_over_demographics_standard_cv | positive_over_demographics_group_cv | uncredited_positive_comparator_at_chance | negative_over_demographics | positive_over_qc_controls | decision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| bikom_1back | 24 | 0 | 0 | 0 | 9 | 0 | NO_INDEPENDENT_SIGNAL |
| bikom_combined | 24 | 0 | 0 | 0 | 0 | 0 | NO_INDEPENDENT_SIGNAL |
| bikom_doors | 24 | 0 | 0 | 0 | 0 | 0 | NO_INDEPENDENT_SIGNAL |
| yiruid_1back | 24 | 0 | 0 | 0 | 3 | 0 | NO_INDEPENDENT_SIGNAL |
| yiruid_combined | 24 | 0 | 0 | 8 | 0 | 0 | NO_INDEPENDENT_SIGNAL |
| yiruid_doors | 24 | 0 | 0 | 0 | 7 | 0 | NO_INDEPENDENT_SIGNAL |
| yiruid_oddball | 24 | 0 | 0 | 0 | 6 | 0 | NO_INDEPENDENT_SIGNAL |
| behaviour_overall | 168 | 0 | 0 | 8 | 25 | 0 | NO_INDEPENDENT_SIGNAL |

A unit is credited with independent signal only when an increment **over
demographics** has a paired bootstrap AUROC interval excluding zero under **both**
CV protocols **and** the demographics baseline it beat is itself above chance.
Beating the QC baseline shows the features carry more than log completeness,
which is a control, not evidence of anything a questionnaire does not already
supply.

## Required Increments

Increments over demographics: **168** rows.
Intervals excluding zero on the positive side: **8** of 168.
Of those, credited (comparator above chance): **0**.
Negative and significant: **25**.

| cv_protocol | cohort_name | modality | device | task | model | comparison | auroc_diff | auroc_diff_ci_low | auroc_diff_ci_high | significant_positive | significant_negative | feature_set_b | comparator_auroc | comparator_above_chance | significant_positive_credited |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| group_cv | behaviour_yiruid_combined_native | behaviour | yiruid | combined | logistic_regression | signal_qc_demographics_vs_qc_demographics | 0.0731 | 0.0073 | 0.1402 | 1 | 0 | qc_demographics | 0.4446 | 0 | 0 |
| group_cv | behaviour_yiruid_combined_native | behaviour | yiruid | combined | random_forest | signal_vs_demographics | 0.0846 | 0.0061 | 0.1697 | 1 | 0 | demographics | 0.4292 | 0 | 0 |
| standard_cv | behaviour_yiruid_combined_native | behaviour | yiruid | combined | hist_gradient_boosting | signal_vs_demographics | 0.0889 | 0.0111 | 0.1761 | 1 | 0 | demographics | 0.4963 | 0 | 0 |
| standard_cv | behaviour_yiruid_combined_native | behaviour | yiruid | combined | hist_gradient_boosting | signal_demographics_vs_demographics | 0.0848 | 0.0021 | 0.1618 | 1 | 0 | demographics | 0.4963 | 0 | 0 |
| standard_cv | behaviour_yiruid_combined_native | behaviour | yiruid | combined | hist_gradient_boosting | signal_qc_demographics_vs_qc_demographics | 0.0848 | 0.0093 | 0.1612 | 1 | 0 | qc_demographics | 0.4963 | 0 | 0 |
| standard_cv | behaviour_yiruid_combined_native | behaviour | yiruid | combined | hist_gradient_boosting | signal_qc_demographics_vs_demographics | 0.0848 | 0.0051 | 0.1661 | 1 | 0 | demographics | 0.4963 | 0 | 0 |
| standard_cv | behaviour_yiruid_combined_native | behaviour | yiruid | combined | random_forest | signal_vs_demographics | 0.0882 | 0.0075 | 0.1689 | 1 | 0 | demographics | 0.4719 | 0 | 0 |
| standard_cv | behaviour_yiruid_combined_native | behaviour | yiruid | combined | random_forest | signal_demographics_vs_demographics | 0.0791 | 0.0010 | 0.1590 | 1 | 0 | demographics | 0.4719 | 0 | 0 |

## Best Row Per Feature Set

| cv_protocol | modality | cohort_name | device | task | feature_set | model | n_subjects | auroc | auprc |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| group_cv | behaviour | behaviour_bikom_1back_native | bikom | 1back | age_grade | logistic_regression | 955 | 0.5567 | 0.3937 |
| group_cv | behaviour | behaviour_bikom_1back_native | bikom | 1back | age_only | random_forest | 955 | 0.5295 | 0.3375 |
| group_cv | behaviour | behaviour_bikom_1back_native | bikom | 1back | age_sex | logistic_regression | 955 | 0.5886 | 0.3559 |
| group_cv | behaviour | behaviour_bikom_1back_native | bikom | 1back | age_sex_grade | logistic_regression | 955 | 0.6021 | 0.4307 |
| group_cv | behaviour | behaviour_bikom_1back_native | bikom | 1back | age_sex_grade_group | logistic_regression | 955 | 0.6027 | 0.4347 |
| group_cv | behaviour | behaviour_bikom_1back_native | bikom | 1back | demographics | logistic_regression | 955 | 0.6021 | 0.4307 |
| group_cv | behaviour | behaviour_bikom_1back_native | bikom | 1back | demographics_group | logistic_regression | 955 | 0.6188 | 0.4321 |
| group_cv | behaviour | behaviour_bikom_1back_native | bikom | 1back | demographics_group_device | hist_gradient_boosting | 955 | 0.6121 | 0.3972 |
| group_cv | behaviour | behaviour_bikom_1back_native | bikom | 1back | fnirs_device_only | logistic_regression | 955 | 0.5927 | 0.3670 |
| group_cv | behaviour | behaviour_bikom_1back_native | bikom | 1back | grade_group_only | logistic_regression | 955 | 0.5238 | 0.3387 |
| group_cv | behaviour | behaviour_bikom_1back_native | bikom | 1back | grade_only | logistic_regression | 955 | 0.5789 | 0.3878 |
| group_cv | behaviour | behaviour_bikom_1back_native | bikom | 1back | group_proxy_only | logistic_regression | 955 | 0.5840 | 0.3564 |
| group_cv | behaviour | behaviour_bikom_1back_native | bikom | 1back | no_information | no_information_prior | 955 | 0.3915 | 0.2686 |
| group_cv | behaviour | behaviour_bikom_1back_native | bikom | 1back | qc | logistic_regression | 955 | 0.5224 | 0.3369 |
| group_cv | behaviour | behaviour_bikom_1back_native | bikom | 1back | qc_demographics | logistic_regression | 955 | 0.6021 | 0.4307 |
| group_cv | behaviour | behaviour_bikom_1back_native | bikom | 1back | sex_grade | logistic_regression | 955 | 0.6015 | 0.4175 |
| group_cv | behaviour | behaviour_bikom_1back_native | bikom | 1back | sex_only | logistic_regression | 955 | 0.5981 | 0.3847 |
| group_cv | behaviour | behaviour_bikom_1back_native | bikom | 1back | signal | hist_gradient_boosting | 955 | 0.5229 | 0.3423 |
| group_cv | behaviour | behaviour_bikom_1back_native | bikom | 1back | signal_demographics | logistic_regression | 955 | 0.5892 | 0.4118 |
| group_cv | behaviour | behaviour_bikom_1back_native | bikom | 1back | signal_qc | hist_gradient_boosting | 955 | 0.5229 | 0.3423 |
| group_cv | behaviour | behaviour_bikom_1back_native | bikom | 1back | signal_qc_demographics | logistic_regression | 955 | 0.5892 | 0.4118 |
| group_cv | behaviour | behaviour_bikom_combined_native | bikom | combined | age_grade | logistic_regression | 513 | 0.4718 | 0.3528 |
| group_cv | behaviour | behaviour_bikom_combined_native | bikom | combined | age_only | random_forest | 513 | 0.4562 | 0.3311 |
| group_cv | behaviour | behaviour_bikom_combined_native | bikom | combined | age_sex | logistic_regression | 513 | 0.5222 | 0.3749 |
| group_cv | behaviour | behaviour_bikom_combined_native | bikom | combined | age_sex_grade | logistic_regression | 513 | 0.5314 | 0.3967 |
| group_cv | behaviour | behaviour_bikom_combined_native | bikom | combined | age_sex_grade_group | logistic_regression | 513 | 0.5277 | 0.3814 |
| group_cv | behaviour | behaviour_bikom_combined_native | bikom | combined | demographics | logistic_regression | 513 | 0.5314 | 0.3967 |
| group_cv | behaviour | behaviour_bikom_combined_native | bikom | combined | demographics_group | logistic_regression | 513 | 0.5309 | 0.3965 |
| group_cv | behaviour | behaviour_bikom_combined_native | bikom | combined | demographics_group_device | logistic_regression | 513 | 0.5243 | 0.3943 |
| group_cv | behaviour | behaviour_bikom_combined_native | bikom | combined | fnirs_device_only | hist_gradient_boosting | 513 | 0.5265 | 0.3847 |
| group_cv | behaviour | behaviour_bikom_combined_native | bikom | combined | grade_group_only | random_forest | 513 | 0.4913 | 0.3656 |
| group_cv | behaviour | behaviour_bikom_combined_native | bikom | combined | grade_only | hist_gradient_boosting | 513 | 0.4524 | 0.3405 |
| group_cv | behaviour | behaviour_bikom_combined_native | bikom | combined | group_proxy_only | hist_gradient_boosting | 513 | 0.4617 | 0.3577 |
| group_cv | behaviour | behaviour_bikom_combined_native | bikom | combined | no_information | no_information_prior | 513 | 0.4196 | 0.3281 |
| group_cv | behaviour | behaviour_bikom_combined_native | bikom | combined | qc | hist_gradient_boosting | 513 | 0.5265 | 0.3847 |
| group_cv | behaviour | behaviour_bikom_combined_native | bikom | combined | qc_demographics | logistic_regression | 513 | 0.5314 | 0.3967 |
| group_cv | behaviour | behaviour_bikom_combined_native | bikom | combined | sex_grade | hist_gradient_boosting | 513 | 0.5292 | 0.3841 |
| group_cv | behaviour | behaviour_bikom_combined_native | bikom | combined | sex_only | hist_gradient_boosting | 513 | 0.5445 | 0.4005 |
| group_cv | behaviour | behaviour_bikom_combined_native | bikom | combined | signal | logistic_regression | 513 | 0.5479 | 0.4058 |
| group_cv | behaviour | behaviour_bikom_combined_native | bikom | combined | signal_demographics | random_forest | 513 | 0.5596 | 0.4234 |
| group_cv | behaviour | behaviour_bikom_combined_native | bikom | combined | signal_qc | random_forest | 513 | 0.5639 | 0.4461 |
| group_cv | behaviour | behaviour_bikom_combined_native | bikom | combined | signal_qc_demographics | logistic_regression | 513 | 0.5521 | 0.4141 |
| group_cv | behaviour | behaviour_bikom_doors_native | bikom | doors | age_grade | logistic_regression | 515 | 0.4679 | 0.3495 |
| group_cv | behaviour | behaviour_bikom_doors_native | bikom | doors | age_only | random_forest | 515 | 0.4492 | 0.3266 |
| group_cv | behaviour | behaviour_bikom_doors_native | bikom | doors | age_sex | logistic_regression | 515 | 0.5261 | 0.3756 |
| group_cv | behaviour | behaviour_bikom_doors_native | bikom | doors | age_sex_grade | logistic_regression | 515 | 0.5388 | 0.4016 |
| group_cv | behaviour | behaviour_bikom_doors_native | bikom | doors | age_sex_grade_group | logistic_regression | 515 | 0.5292 | 0.3822 |
| group_cv | behaviour | behaviour_bikom_doors_native | bikom | doors | demographics | logistic_regression | 515 | 0.5388 | 0.4016 |
| group_cv | behaviour | behaviour_bikom_doors_native | bikom | doors | demographics_group | logistic_regression | 515 | 0.5271 | 0.3886 |
| group_cv | behaviour | behaviour_bikom_doors_native | bikom | doors | demographics_group_device | logistic_regression | 515 | 0.5233 | 0.3882 |
| group_cv | behaviour | behaviour_bikom_doors_native | bikom | doors | fnirs_device_only | logistic_regression | 515 | 0.5806 | 0.4175 |
| group_cv | behaviour | behaviour_bikom_doors_native | bikom | doors | grade_group_only | hist_gradient_boosting | 515 | 0.4894 | 0.3668 |
| group_cv | behaviour | behaviour_bikom_doors_native | bikom | doors | grade_only | hist_gradient_boosting | 515 | 0.4546 | 0.3404 |
| group_cv | behaviour | behaviour_bikom_doors_native | bikom | doors | group_proxy_only | hist_gradient_boosting | 515 | 0.4644 | 0.3489 |
| group_cv | behaviour | behaviour_bikom_doors_native | bikom | doors | no_information | no_information_prior | 515 | 0.4202 | 0.3269 |
| group_cv | behaviour | behaviour_bikom_doors_native | bikom | doors | qc | hist_gradient_boosting | 515 | 0.5016 | 0.3677 |
| group_cv | behaviour | behaviour_bikom_doors_native | bikom | doors | qc_demographics | logistic_regression | 515 | 0.5388 | 0.4016 |
| group_cv | behaviour | behaviour_bikom_doors_native | bikom | doors | sex_grade | hist_gradient_boosting | 515 | 0.5315 | 0.3846 |
| group_cv | behaviour | behaviour_bikom_doors_native | bikom | doors | sex_only | random_forest | 515 | 0.5464 | 0.4001 |
| group_cv | behaviour | behaviour_bikom_doors_native | bikom | doors | signal | logistic_regression | 515 | 0.5138 | 0.3921 |
| group_cv | behaviour | behaviour_bikom_doors_native | bikom | doors | signal_demographics | logistic_regression | 515 | 0.5246 | 0.4104 |
| group_cv | behaviour | behaviour_bikom_doors_native | bikom | doors | signal_qc | logistic_regression | 515 | 0.5138 | 0.3921 |
| group_cv | behaviour | behaviour_bikom_doors_native | bikom | doors | signal_qc_demographics | logistic_regression | 515 | 0.5246 | 0.4104 |
| group_cv | behaviour | behaviour_yiruid_1back_native | yiruid | 1back | age_grade | hist_gradient_boosting | 1412 | 0.5196 | 0.4045 |
| group_cv | behaviour | behaviour_yiruid_1back_native | yiruid | 1back | age_only | logistic_regression | 1412 | 0.5295 | 0.4052 |
| group_cv | behaviour | behaviour_yiruid_1back_native | yiruid | 1back | age_sex | logistic_regression | 1412 | 0.5889 | 0.4490 |
| group_cv | behaviour | behaviour_yiruid_1back_native | yiruid | 1back | age_sex_grade | logistic_regression | 1412 | 0.5838 | 0.4459 |
| group_cv | behaviour | behaviour_yiruid_1back_native | yiruid | 1back | age_sex_grade_group | logistic_regression | 1412 | 0.5823 | 0.4451 |
| group_cv | behaviour | behaviour_yiruid_1back_native | yiruid | 1back | demographics | logistic_regression | 1412 | 0.5838 | 0.4459 |
| group_cv | behaviour | behaviour_yiruid_1back_native | yiruid | 1back | demographics_group | logistic_regression | 1412 | 0.5879 | 0.4541 |
| group_cv | behaviour | behaviour_yiruid_1back_native | yiruid | 1back | demographics_group_device | random_forest | 1412 | 0.5813 | 0.4557 |
| group_cv | behaviour | behaviour_yiruid_1back_native | yiruid | 1back | fnirs_device_only | hist_gradient_boosting | 1412 | 0.5000 | 0.3931 |
| group_cv | behaviour | behaviour_yiruid_1back_native | yiruid | 1back | grade_group_only | random_forest | 1412 | 0.5030 | 0.3879 |
| group_cv | behaviour | behaviour_yiruid_1back_native | yiruid | 1back | grade_only | random_forest | 1412 | 0.5215 | 0.4096 |
| group_cv | behaviour | behaviour_yiruid_1back_native | yiruid | 1back | group_proxy_only | hist_gradient_boosting | 1412 | 0.5492 | 0.4458 |
| group_cv | behaviour | behaviour_yiruid_1back_native | yiruid | 1back | no_information | no_information_prior | 1412 | 0.3885 | 0.3381 |
| group_cv | behaviour | behaviour_yiruid_1back_native | yiruid | 1back | qc | hist_gradient_boosting | 1412 | 0.4653 | 0.3858 |
| group_cv | behaviour | behaviour_yiruid_1back_native | yiruid | 1back | qc_demographics | logistic_regression | 1412 | 0.5878 | 0.4657 |
| group_cv | behaviour | behaviour_yiruid_1back_native | yiruid | 1back | sex_grade | random_forest | 1412 | 0.5913 | 0.4575 |
| group_cv | behaviour | behaviour_yiruid_1back_native | yiruid | 1back | sex_only | random_forest | 1412 | 0.5844 | 0.4684 |
| group_cv | behaviour | behaviour_yiruid_1back_native | yiruid | 1back | signal | logistic_regression | 1412 | 0.5524 | 0.4404 |
| group_cv | behaviour | behaviour_yiruid_1back_native | yiruid | 1back | signal_demographics | logistic_regression | 1412 | 0.6019 | 0.4907 |
| group_cv | behaviour | behaviour_yiruid_1back_native | yiruid | 1back | signal_qc | logistic_regression | 1412 | 0.5523 | 0.4441 |
| group_cv | behaviour | behaviour_yiruid_1back_native | yiruid | 1back | signal_qc_demographics | logistic_regression | 1412 | 0.6016 | 0.4969 |
| group_cv | behaviour | behaviour_yiruid_combined_native | yiruid | combined | age_grade | logistic_regression | 342 | 0.4538 | 0.4251 |
| group_cv | behaviour | behaviour_yiruid_combined_native | yiruid | combined | age_only | logistic_regression | 342 | 0.4625 | 0.4234 |
| group_cv | behaviour | behaviour_yiruid_combined_native | yiruid | combined | age_sex | logistic_regression | 342 | 0.5124 | 0.4347 |
| group_cv | behaviour | behaviour_yiruid_combined_native | yiruid | combined | age_sex_grade | logistic_regression | 342 | 0.4668 | 0.4021 |
| group_cv | behaviour | behaviour_yiruid_combined_native | yiruid | combined | age_sex_grade_group | logistic_regression | 342 | 0.4583 | 0.3976 |
| group_cv | behaviour | behaviour_yiruid_combined_native | yiruid | combined | demographics | logistic_regression | 342 | 0.4668 | 0.4021 |
| group_cv | behaviour | behaviour_yiruid_combined_native | yiruid | combined | demographics_group | random_forest | 342 | 0.5019 | 0.4384 |
| group_cv | behaviour | behaviour_yiruid_combined_native | yiruid | combined | demographics_group_device | random_forest | 342 | 0.5094 | 0.4480 |
| group_cv | behaviour | behaviour_yiruid_combined_native | yiruid | combined | fnirs_device_only | random_forest | 342 | 0.6096 | 0.5010 |
| group_cv | behaviour | behaviour_yiruid_combined_native | yiruid | combined | grade_group_only | logistic_regression | 342 | 0.4459 | 0.4374 |
| group_cv | behaviour | behaviour_yiruid_combined_native | yiruid | combined | grade_only | logistic_regression | 342 | 0.4161 | 0.4065 |
| group_cv | behaviour | behaviour_yiruid_combined_native | yiruid | combined | group_proxy_only | hist_gradient_boosting | 342 | 0.6035 | 0.5201 |
| group_cv | behaviour | behaviour_yiruid_combined_native | yiruid | combined | no_information | no_information_prior | 342 | 0.3472 | 0.3748 |
| group_cv | behaviour | behaviour_yiruid_combined_native | yiruid | combined | qc | logistic_regression | 342 | 0.5886 | 0.4971 |
| group_cv | behaviour | behaviour_yiruid_combined_native | yiruid | combined | qc_demographics | logistic_regression | 342 | 0.4446 | 0.4006 |
| group_cv | behaviour | behaviour_yiruid_combined_native | yiruid | combined | sex_grade | logistic_regression | 342 | 0.4662 | 0.4131 |

Showing 100 of 294 rows.
