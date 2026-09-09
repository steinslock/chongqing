# Goal 2.10 Results

Goal 2.10 adds the eye-tracking modality, the last objective modality no earlier
goal used. The protocol is unchanged from Goal 2.7, 2.8 and 2.9: the same fixed
folds, the same inner-CV selection, the same model families and grids, the same
1000-resample bootstrap, the same pilot-holdout exclusion, and the Goal 2.9 rule
that a credited increment must beat a comparator that is itself above chance.
Only the features are new.

## Read the free-viewing result with its measurement properties

Free viewing carries 121 features in two blocks that
differ by an order of magnitude in reliability, measured by odd-even split half
on 249 to 322 subjects per device:

- **absolute** per-valence measures: 75 features, median Spearman-Brown 0.698, 53 above 0.5 on all three devices;
- **contrast** valence differences: 46 features, median -0.051, **0** above 0.5 on all three devices, the best reaching 0.326.

Each contrast is a difference of two means estimated from 12 trials each, which
is the difference-score reliability collapse the attentional-bias literature
reports, replicated here on three devices independently. The two blocks are
therefore separate feature sets, and **a null on the contrast block is evidence
about this paradigm, not about attentional bias as a construct.**

## Unit Decision

| unit | demographic_increment_rows | positive_over_demographics_standard_cv | positive_over_demographics_group_cv | uncredited_positive_comparator_at_chance | negative_over_demographics | positive_on_controls | decision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| qixin_120_combined | 48 | 0 | 0 | 3 | 11 | 4 | NO_INDEPENDENT_SIGNAL |
| qixin_120_free_viewing | 48 | 0 | 0 | 0 | 24 | 0 | NO_INDEPENDENT_SIGNAL |
| qixin_120_saccade | 48 | 0 | 0 | 9 | 1 | 0 | NO_INDEPENDENT_SIGNAL |
| qixin_120_smooth_pursuit | 48 | 0 | 0 | 6 | 2 | 5 | NO_INDEPENDENT_SIGNAL |
| qixin_500_combined | 48 | 0 | 0 | 0 | 8 | 0 | NO_INDEPENDENT_SIGNAL |
| qixin_500_free_viewing | 48 | 0 | 0 | 0 | 11 | 0 | NO_INDEPENDENT_SIGNAL |
| qixin_500_saccade | 48 | 0 | 0 | 0 | 20 | 0 | NO_INDEPENDENT_SIGNAL |
| qixin_500_smooth_pursuit | 48 | 0 | 0 | 0 | 25 | 0 | NO_INDEPENDENT_SIGNAL |
| tobii_combined | 48 | 0 | 0 | 0 | 20 | 0 | NO_INDEPENDENT_SIGNAL |
| tobii_free_viewing | 48 | 0 | 0 | 0 | 22 | 0 | NO_INDEPENDENT_SIGNAL |
| tobii_saccade | 48 | 0 | 0 | 0 | 5 | 0 | NO_INDEPENDENT_SIGNAL |
| tobii_smooth_pursuit | 48 | 0 | 0 | 0 | 3 | 0 | NO_INDEPENDENT_SIGNAL |
| eye_all_units | 576 | 0 | 0 | 18 | 152 | 9 | NO_INDEPENDENT_SIGNAL |

A unit is credited with independent signal only when an increment **over
demographics** has a paired bootstrap AUROC interval excluding zero under **both**
CV protocols **and** the demographics baseline it beat is itself above chance.
Wins over QC show the features carry more than acquisition quality, which is a
control rather than evidence of anything a questionnaire does not already supply.

## Required Increments

Increments over demographics: **576** rows.
Intervals excluding zero on the positive side: **18**.
Of those, credited (comparator above chance): **0**.
Negative and significant: **152**.

Controls are counted separately: **72** rows, **9** positive,
**1** of them over an above-chance comparator. A win on a control is not
an increment and is never credited as one.

| cv_protocol | cohort_name | modality | device | task | model | comparison | auroc_diff | auroc_diff_ci_low | auroc_diff_ci_high | significant_positive | significant_negative | feature_set_b | comparator_auroc | comparator_above_chance | significant_positive_credited |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| group_cv | eye_qixin_120_combined_native | eye | qixin_120 | combined | hist_gradient_boosting | signal_qc_demographics_vs_qc_demographics | 0.0848 | 0.0133 | 0.1676 | 1 | 0 | qc_demographics | 0.4604 | 0 | 0 |
| group_cv | eye_qixin_120_combined_native | eye | qixin_120 | combined | hist_gradient_boosting | signal_absolute_vs_demographics | 0.1082 | 0.0195 | 0.1977 | 1 | 0 | demographics | 0.4554 | 0 | 0 |
| group_cv | eye_qixin_120_combined_native | eye | qixin_120 | combined | hist_gradient_boosting | signal_absolute_demographics_vs_demographics | 0.1135 | 0.0191 | 0.2000 | 1 | 0 | demographics | 0.4554 | 0 | 0 |
| group_cv | eye_qixin_120_saccade_native | eye | qixin_120 | saccade | hist_gradient_boosting | signal_vs_demographics | 0.1280 | 0.0318 | 0.2185 | 1 | 0 | demographics | 0.4361 | 0 | 0 |
| group_cv | eye_qixin_120_saccade_native | eye | qixin_120 | saccade | hist_gradient_boosting | signal_demographics_vs_demographics | 0.1417 | 0.0481 | 0.2382 | 1 | 0 | demographics | 0.4361 | 0 | 0 |
| group_cv | eye_qixin_120_saccade_native | eye | qixin_120 | saccade | hist_gradient_boosting | signal_qc_demographics_vs_demographics | 0.1006 | 0.0043 | 0.1874 | 1 | 0 | demographics | 0.4361 | 0 | 0 |
| group_cv | eye_qixin_120_saccade_native | eye | qixin_120 | saccade | hist_gradient_boosting | signal_absolute_vs_demographics | 0.1054 | 0.0124 | 0.1891 | 1 | 0 | demographics | 0.4361 | 0 | 0 |
| group_cv | eye_qixin_120_saccade_native | eye | qixin_120 | saccade | hist_gradient_boosting | signal_absolute_demographics_vs_demographics | 0.0991 | 0.0013 | 0.1807 | 1 | 0 | demographics | 0.4361 | 0 | 0 |
| group_cv | eye_qixin_120_saccade_native | eye | qixin_120 | saccade | hist_gradient_boosting | signal_contrast_demographics_vs_demographics | 0.0748 | 0.0026 | 0.1522 | 1 | 0 | demographics | 0.4361 | 0 | 0 |
| group_cv | eye_qixin_120_saccade_native | eye | qixin_120 | saccade | random_forest | signal_vs_demographics | 0.1066 | 0.0197 | 0.2020 | 1 | 0 | demographics | 0.4671 | 0 | 0 |
| group_cv | eye_qixin_120_saccade_native | eye | qixin_120 | saccade | random_forest | signal_demographics_vs_demographics | 0.0890 | 0.0047 | 0.1755 | 1 | 0 | demographics | 0.4671 | 0 | 0 |
| group_cv | eye_qixin_120_saccade_native | eye | qixin_120 | saccade | random_forest | signal_qc_demographics_vs_demographics | 0.0954 | 0.0043 | 0.1857 | 1 | 0 | demographics | 0.4671 | 0 | 0 |
| group_cv | eye_qixin_120_smooth_pursuit_native | eye | qixin_120 | smooth_pursuit | hist_gradient_boosting | signal_vs_demographics | 0.0931 | 0.0046 | 0.1780 | 1 | 0 | demographics | 0.4350 | 0 | 0 |
| group_cv | eye_qixin_120_smooth_pursuit_native | eye | qixin_120 | smooth_pursuit | hist_gradient_boosting | signal_demographics_vs_demographics | 0.1024 | 0.0183 | 0.1917 | 1 | 0 | demographics | 0.4350 | 0 | 0 |
| group_cv | eye_qixin_120_smooth_pursuit_native | eye | qixin_120 | smooth_pursuit | hist_gradient_boosting | signal_qc_demographics_vs_demographics | 0.0945 | 0.0053 | 0.1776 | 1 | 0 | demographics | 0.4350 | 0 | 0 |
| group_cv | eye_qixin_120_smooth_pursuit_native | eye | qixin_120 | smooth_pursuit | hist_gradient_boosting | signal_absolute_vs_demographics | 0.1129 | 0.0240 | 0.2049 | 1 | 0 | demographics | 0.4350 | 0 | 0 |
| group_cv | eye_qixin_120_smooth_pursuit_native | eye | qixin_120 | smooth_pursuit | hist_gradient_boosting | signal_absolute_demographics_vs_demographics | 0.1060 | 0.0167 | 0.1962 | 1 | 0 | demographics | 0.4350 | 0 | 0 |
| group_cv | eye_qixin_120_smooth_pursuit_native | eye | qixin_120 | smooth_pursuit | random_forest | signal_absolute_demographics_vs_demographics | 0.0946 | 0.0095 | 0.1748 | 1 | 0 | demographics | 0.4503 | 0 | 0 |

## Best Row Per Feature Set

| cv_protocol | modality | cohort_name | device | task | feature_set | model | n_subjects | auroc | auprc |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| group_cv | eye | eye_qixin_120_combined_native | qixin_120 | combined | age_grade | random_forest | 320 | 0.4659 | 0.2994 |
| group_cv | eye | eye_qixin_120_combined_native | qixin_120 | combined | age_only | logistic_regression | 320 | 0.5254 | 0.3337 |
| group_cv | eye | eye_qixin_120_combined_native | qixin_120 | combined | age_sex | logistic_regression | 320 | 0.5619 | 0.3548 |
| group_cv | eye | eye_qixin_120_combined_native | qixin_120 | combined | age_sex_grade | logistic_regression | 320 | 0.4968 | 0.3174 |
| group_cv | eye | eye_qixin_120_combined_native | qixin_120 | combined | age_sex_grade_group | logistic_regression | 320 | 0.4935 | 0.3164 |
| group_cv | eye | eye_qixin_120_combined_native | qixin_120 | combined | demographics | logistic_regression | 320 | 0.4968 | 0.3174 |
| group_cv | eye | eye_qixin_120_combined_native | qixin_120 | combined | demographics_group | random_forest | 320 | 0.5413 | 0.3427 |
| group_cv | eye | eye_qixin_120_combined_native | qixin_120 | combined | demographics_group_device | hist_gradient_boosting | 320 | 0.5476 | 0.3852 |
| group_cv | eye | eye_qixin_120_combined_native | qixin_120 | combined | fnirs_device_only | hist_gradient_boosting | 320 | 0.5749 | 0.3964 |
| group_cv | eye | eye_qixin_120_combined_native | qixin_120 | combined | grade_group_only | logistic_regression | 320 | 0.4707 | 0.3502 |
| group_cv | eye | eye_qixin_120_combined_native | qixin_120 | combined | grade_only | random_forest | 320 | 0.4515 | 0.3017 |
| group_cv | eye | eye_qixin_120_combined_native | qixin_120 | combined | group_proxy_only | hist_gradient_boosting | 320 | 0.5682 | 0.3669 |
| group_cv | eye | eye_qixin_120_combined_native | qixin_120 | combined | no_information | no_information_prior | 320 | 0.3465 | 0.2683 |
| group_cv | eye | eye_qixin_120_combined_native | qixin_120 | combined | qc | random_forest | 320 | 0.5337 | 0.3482 |
| group_cv | eye | eye_qixin_120_combined_native | qixin_120 | combined | qc_demographics | random_forest | 320 | 0.5117 | 0.3470 |
| group_cv | eye | eye_qixin_120_combined_native | qixin_120 | combined | sex_grade | logistic_regression | 320 | 0.4758 | 0.3171 |
| group_cv | eye | eye_qixin_120_combined_native | qixin_120 | combined | sex_only | hist_gradient_boosting | 320 | 0.4897 | 0.3130 |
| group_cv | eye | eye_qixin_120_combined_native | qixin_120 | combined | signal | hist_gradient_boosting | 320 | 0.5196 | 0.3572 |
| group_cv | eye | eye_qixin_120_combined_native | qixin_120 | combined | signal_absolute | hist_gradient_boosting | 320 | 0.5636 | 0.3846 |
| group_cv | eye | eye_qixin_120_combined_native | qixin_120 | combined | signal_absolute_demographics | hist_gradient_boosting | 320 | 0.5689 | 0.3885 |
| group_cv | eye | eye_qixin_120_combined_native | qixin_120 | combined | signal_contrast | hist_gradient_boosting | 320 | 0.4567 | 0.3022 |
| group_cv | eye | eye_qixin_120_combined_native | qixin_120 | combined | signal_contrast_demographics | logistic_regression | 320 | 0.4619 | 0.3465 |
| group_cv | eye | eye_qixin_120_combined_native | qixin_120 | combined | signal_demographics | hist_gradient_boosting | 320 | 0.5304 | 0.3699 |
| group_cv | eye | eye_qixin_120_combined_native | qixin_120 | combined | signal_qc | hist_gradient_boosting | 320 | 0.5421 | 0.3836 |
| group_cv | eye | eye_qixin_120_combined_native | qixin_120 | combined | signal_qc_demographics | hist_gradient_boosting | 320 | 0.5452 | 0.3791 |
| group_cv | eye | eye_qixin_120_free_viewing_native | qixin_120 | free_viewing | age_grade | random_forest | 322 | 0.4672 | 0.3039 |
| group_cv | eye | eye_qixin_120_free_viewing_native | qixin_120 | free_viewing | age_only | logistic_regression | 322 | 0.5252 | 0.3556 |
| group_cv | eye | eye_qixin_120_free_viewing_native | qixin_120 | free_viewing | age_sex | logistic_regression | 322 | 0.5596 | 0.3764 |
| group_cv | eye | eye_qixin_120_free_viewing_native | qixin_120 | free_viewing | age_sex_grade | logistic_regression | 322 | 0.4933 | 0.3180 |
| group_cv | eye | eye_qixin_120_free_viewing_native | qixin_120 | free_viewing | age_sex_grade_group | logistic_regression | 322 | 0.4858 | 0.3116 |
| group_cv | eye | eye_qixin_120_free_viewing_native | qixin_120 | free_viewing | demographics | logistic_regression | 322 | 0.4933 | 0.3180 |
| group_cv | eye | eye_qixin_120_free_viewing_native | qixin_120 | free_viewing | demographics_group | random_forest | 322 | 0.5343 | 0.3411 |
| group_cv | eye | eye_qixin_120_free_viewing_native | qixin_120 | free_viewing | demographics_group_device | random_forest | 322 | 0.5291 | 0.3414 |
| group_cv | eye | eye_qixin_120_free_viewing_native | qixin_120 | free_viewing | fnirs_device_only | hist_gradient_boosting | 322 | 0.5708 | 0.3949 |
| group_cv | eye | eye_qixin_120_free_viewing_native | qixin_120 | free_viewing | grade_group_only | logistic_regression | 322 | 0.5000 | 0.3323 |
| group_cv | eye | eye_qixin_120_free_viewing_native | qixin_120 | free_viewing | grade_only | hist_gradient_boosting | 322 | 0.4579 | 0.3056 |
| group_cv | eye | eye_qixin_120_free_viewing_native | qixin_120 | free_viewing | group_proxy_only | hist_gradient_boosting | 322 | 0.5603 | 0.3544 |
| group_cv | eye | eye_qixin_120_free_viewing_native | qixin_120 | free_viewing | no_information | no_information_prior | 322 | 0.3498 | 0.2701 |
| group_cv | eye | eye_qixin_120_free_viewing_native | qixin_120 | free_viewing | qc | logistic_regression | 322 | 0.5042 | 0.3475 |
| group_cv | eye | eye_qixin_120_free_viewing_native | qixin_120 | free_viewing | qc_demographics | random_forest | 322 | 0.4938 | 0.3358 |
| group_cv | eye | eye_qixin_120_free_viewing_native | qixin_120 | free_viewing | sex_grade | logistic_regression | 322 | 0.4841 | 0.3167 |
| group_cv | eye | eye_qixin_120_free_viewing_native | qixin_120 | free_viewing | sex_only | logistic_regression | 322 | 0.4953 | 0.3175 |
| group_cv | eye | eye_qixin_120_free_viewing_native | qixin_120 | free_viewing | signal | hist_gradient_boosting | 322 | 0.4759 | 0.3270 |
| group_cv | eye | eye_qixin_120_free_viewing_native | qixin_120 | free_viewing | signal_absolute | logistic_regression | 322 | 0.4879 | 0.3166 |
| group_cv | eye | eye_qixin_120_free_viewing_native | qixin_120 | free_viewing | signal_absolute_demographics | logistic_regression | 322 | 0.4956 | 0.3166 |
| group_cv | eye | eye_qixin_120_free_viewing_native | qixin_120 | free_viewing | signal_contrast | logistic_regression | 322 | 0.4305 | 0.3392 |
| group_cv | eye | eye_qixin_120_free_viewing_native | qixin_120 | free_viewing | signal_contrast_demographics | logistic_regression | 322 | 0.4513 | 0.3155 |
| group_cv | eye | eye_qixin_120_free_viewing_native | qixin_120 | free_viewing | signal_demographics | hist_gradient_boosting | 322 | 0.4789 | 0.3277 |
| group_cv | eye | eye_qixin_120_free_viewing_native | qixin_120 | free_viewing | signal_qc | hist_gradient_boosting | 322 | 0.4682 | 0.3159 |
| group_cv | eye | eye_qixin_120_free_viewing_native | qixin_120 | free_viewing | signal_qc_demographics | hist_gradient_boosting | 322 | 0.4699 | 0.3169 |
| group_cv | eye | eye_qixin_120_saccade_native | qixin_120 | saccade | age_grade | logistic_regression | 322 | 0.4876 | 0.3421 |
| group_cv | eye | eye_qixin_120_saccade_native | qixin_120 | saccade | age_only | logistic_regression | 322 | 0.5349 | 0.3508 |
| group_cv | eye | eye_qixin_120_saccade_native | qixin_120 | saccade | age_sex | logistic_regression | 322 | 0.5717 | 0.3721 |
| group_cv | eye | eye_qixin_120_saccade_native | qixin_120 | saccade | age_sex_grade | logistic_regression | 322 | 0.5222 | 0.3415 |
| group_cv | eye | eye_qixin_120_saccade_native | qixin_120 | saccade | age_sex_grade_group | logistic_regression | 322 | 0.5205 | 0.3425 |
| group_cv | eye | eye_qixin_120_saccade_native | qixin_120 | saccade | demographics | logistic_regression | 322 | 0.5222 | 0.3415 |
| group_cv | eye | eye_qixin_120_saccade_native | qixin_120 | saccade | demographics_group | random_forest | 322 | 0.5462 | 0.3474 |
| group_cv | eye | eye_qixin_120_saccade_native | qixin_120 | saccade | demographics_group_device | hist_gradient_boosting | 322 | 0.5630 | 0.3920 |
| group_cv | eye | eye_qixin_120_saccade_native | qixin_120 | saccade | fnirs_device_only | hist_gradient_boosting | 322 | 0.5834 | 0.4057 |
| group_cv | eye | eye_qixin_120_saccade_native | qixin_120 | saccade | grade_group_only | logistic_regression | 322 | 0.5000 | 0.3354 |
| group_cv | eye | eye_qixin_120_saccade_native | qixin_120 | saccade | grade_only | hist_gradient_boosting | 322 | 0.4545 | 0.3048 |
| group_cv | eye | eye_qixin_120_saccade_native | qixin_120 | saccade | group_proxy_only | hist_gradient_boosting | 322 | 0.5648 | 0.3606 |
| group_cv | eye | eye_qixin_120_saccade_native | qixin_120 | saccade | no_information | no_information_prior | 322 | 0.3467 | 0.2720 |
| group_cv | eye | eye_qixin_120_saccade_native | qixin_120 | saccade | qc | logistic_regression | 322 | 0.5574 | 0.3782 |
| group_cv | eye | eye_qixin_120_saccade_native | qixin_120 | saccade | qc_demographics | logistic_regression | 322 | 0.5755 | 0.3860 |
| group_cv | eye | eye_qixin_120_saccade_native | qixin_120 | saccade | sex_grade | logistic_regression | 322 | 0.4940 | 0.3274 |
| group_cv | eye | eye_qixin_120_saccade_native | qixin_120 | saccade | sex_only | random_forest | 322 | 0.4986 | 0.3227 |
| group_cv | eye | eye_qixin_120_saccade_native | qixin_120 | saccade | signal | random_forest | 322 | 0.5738 | 0.3775 |
| group_cv | eye | eye_qixin_120_saccade_native | qixin_120 | saccade | signal_absolute | random_forest | 322 | 0.5488 | 0.3510 |
| group_cv | eye | eye_qixin_120_saccade_native | qixin_120 | saccade | signal_absolute_demographics | hist_gradient_boosting | 322 | 0.5351 | 0.3646 |
| group_cv | eye | eye_qixin_120_saccade_native | qixin_120 | saccade | signal_contrast | logistic_regression | 322 | 0.5472 | 0.3761 |
| group_cv | eye | eye_qixin_120_saccade_native | qixin_120 | saccade | signal_contrast_demographics | logistic_regression | 322 | 0.5675 | 0.3656 |
| group_cv | eye | eye_qixin_120_saccade_native | qixin_120 | saccade | signal_demographics | hist_gradient_boosting | 322 | 0.5778 | 0.3803 |
| group_cv | eye | eye_qixin_120_saccade_native | qixin_120 | saccade | signal_qc | hist_gradient_boosting | 322 | 0.5638 | 0.3695 |
| group_cv | eye | eye_qixin_120_saccade_native | qixin_120 | saccade | signal_qc_demographics | random_forest | 322 | 0.5625 | 0.3883 |
| group_cv | eye | eye_qixin_120_smooth_pursuit_native | qixin_120 | smooth_pursuit | age_grade | random_forest | 336 | 0.4666 | 0.3081 |
| group_cv | eye | eye_qixin_120_smooth_pursuit_native | qixin_120 | smooth_pursuit | age_only | logistic_regression | 336 | 0.5263 | 0.3512 |
| group_cv | eye | eye_qixin_120_smooth_pursuit_native | qixin_120 | smooth_pursuit | age_sex | logistic_regression | 336 | 0.5701 | 0.3651 |
| group_cv | eye | eye_qixin_120_smooth_pursuit_native | qixin_120 | smooth_pursuit | age_sex_grade | logistic_regression | 336 | 0.5018 | 0.3186 |
| group_cv | eye | eye_qixin_120_smooth_pursuit_native | qixin_120 | smooth_pursuit | age_sex_grade_group | logistic_regression | 336 | 0.4954 | 0.3155 |
| group_cv | eye | eye_qixin_120_smooth_pursuit_native | qixin_120 | smooth_pursuit | demographics | logistic_regression | 336 | 0.5018 | 0.3186 |
| group_cv | eye | eye_qixin_120_smooth_pursuit_native | qixin_120 | smooth_pursuit | demographics_group | hist_gradient_boosting | 336 | 0.5451 | 0.3646 |
| group_cv | eye | eye_qixin_120_smooth_pursuit_native | qixin_120 | smooth_pursuit | demographics_group_device | hist_gradient_boosting | 336 | 0.5449 | 0.3704 |
| group_cv | eye | eye_qixin_120_smooth_pursuit_native | qixin_120 | smooth_pursuit | fnirs_device_only | hist_gradient_boosting | 336 | 0.5748 | 0.4021 |
| group_cv | eye | eye_qixin_120_smooth_pursuit_native | qixin_120 | smooth_pursuit | grade_group_only | logistic_regression | 336 | 0.4795 | 0.3303 |
| group_cv | eye | eye_qixin_120_smooth_pursuit_native | qixin_120 | smooth_pursuit | grade_only | logistic_regression | 336 | 0.4665 | 0.3370 |
| group_cv | eye | eye_qixin_120_smooth_pursuit_native | qixin_120 | smooth_pursuit | group_proxy_only | hist_gradient_boosting | 336 | 0.5591 | 0.3597 |
| group_cv | eye | eye_qixin_120_smooth_pursuit_native | qixin_120 | smooth_pursuit | no_information | no_information_prior | 336 | 0.3559 | 0.2753 |
| group_cv | eye | eye_qixin_120_smooth_pursuit_native | qixin_120 | smooth_pursuit | qc | logistic_regression | 336 | 0.5294 | 0.3593 |
| group_cv | eye | eye_qixin_120_smooth_pursuit_native | qixin_120 | smooth_pursuit | qc_demographics | logistic_regression | 336 | 0.5209 | 0.3291 |
| group_cv | eye | eye_qixin_120_smooth_pursuit_native | qixin_120 | smooth_pursuit | sex_grade | logistic_regression | 336 | 0.4935 | 0.3169 |
| group_cv | eye | eye_qixin_120_smooth_pursuit_native | qixin_120 | smooth_pursuit | sex_only | logistic_regression | 336 | 0.5169 | 0.3490 |
| group_cv | eye | eye_qixin_120_smooth_pursuit_native | qixin_120 | smooth_pursuit | signal | logistic_regression | 336 | 0.5617 | 0.3800 |
| group_cv | eye | eye_qixin_120_smooth_pursuit_native | qixin_120 | smooth_pursuit | signal_absolute | logistic_regression | 336 | 0.5613 | 0.3862 |
| group_cv | eye | eye_qixin_120_smooth_pursuit_native | qixin_120 | smooth_pursuit | signal_absolute_demographics | logistic_regression | 336 | 0.5587 | 0.3761 |
| group_cv | eye | eye_qixin_120_smooth_pursuit_native | qixin_120 | smooth_pursuit | signal_contrast | random_forest | 336 | 0.4995 | 0.3277 |
| group_cv | eye | eye_qixin_120_smooth_pursuit_native | qixin_120 | smooth_pursuit | signal_contrast_demographics | logistic_regression | 336 | 0.4580 | 0.2983 |
| group_cv | eye | eye_qixin_120_smooth_pursuit_native | qixin_120 | smooth_pursuit | signal_demographics | logistic_regression | 336 | 0.5518 | 0.3768 |
| group_cv | eye | eye_qixin_120_smooth_pursuit_native | qixin_120 | smooth_pursuit | signal_qc | logistic_regression | 336 | 0.5721 | 0.3736 |
| group_cv | eye | eye_qixin_120_smooth_pursuit_native | qixin_120 | smooth_pursuit | signal_qc_demographics | logistic_regression | 336 | 0.5629 | 0.3675 |
| group_cv | eye | eye_qixin_500_combined_native | qixin_500 | combined | age_grade | logistic_regression | 301 | 0.5466 | 0.3927 |
| group_cv | eye | eye_qixin_500_combined_native | qixin_500 | combined | age_only | hist_gradient_boosting | 301 | 0.5027 | 0.3638 |
| group_cv | eye | eye_qixin_500_combined_native | qixin_500 | combined | age_sex | logistic_regression | 301 | 0.6311 | 0.4544 |
| group_cv | eye | eye_qixin_500_combined_native | qixin_500 | combined | age_sex_grade | logistic_regression | 301 | 0.6673 | 0.4951 |
| group_cv | eye | eye_qixin_500_combined_native | qixin_500 | combined | age_sex_grade_group | logistic_regression | 301 | 0.6680 | 0.4955 |
| group_cv | eye | eye_qixin_500_combined_native | qixin_500 | combined | demographics | logistic_regression | 301 | 0.6673 | 0.4951 |
| group_cv | eye | eye_qixin_500_combined_native | qixin_500 | combined | demographics_group | logistic_regression | 301 | 0.6727 | 0.4985 |
| group_cv | eye | eye_qixin_500_combined_native | qixin_500 | combined | demographics_group_device | random_forest | 301 | 0.6533 | 0.5044 |
| group_cv | eye | eye_qixin_500_combined_native | qixin_500 | combined | fnirs_device_only | logistic_regression | 301 | 0.4130 | 0.3166 |
| group_cv | eye | eye_qixin_500_combined_native | qixin_500 | combined | grade_group_only | random_forest | 301 | 0.4961 | 0.3697 |
| group_cv | eye | eye_qixin_500_combined_native | qixin_500 | combined | grade_only | random_forest | 301 | 0.5650 | 0.4064 |
| group_cv | eye | eye_qixin_500_combined_native | qixin_500 | combined | group_proxy_only | logistic_regression | 301 | 0.5410 | 0.3984 |
| group_cv | eye | eye_qixin_500_combined_native | qixin_500 | combined | no_information | no_information_prior | 301 | 0.4193 | 0.3219 |
| group_cv | eye | eye_qixin_500_combined_native | qixin_500 | combined | qc | random_forest | 301 | 0.5552 | 0.4064 |
| group_cv | eye | eye_qixin_500_combined_native | qixin_500 | combined | qc_demographics | logistic_regression | 301 | 0.6222 | 0.4638 |
| group_cv | eye | eye_qixin_500_combined_native | qixin_500 | combined | sex_grade | hist_gradient_boosting | 301 | 0.6640 | 0.4865 |
| group_cv | eye | eye_qixin_500_combined_native | qixin_500 | combined | sex_only | logistic_regression | 301 | 0.6362 | 0.4626 |
| group_cv | eye | eye_qixin_500_combined_native | qixin_500 | combined | signal | logistic_regression | 301 | 0.6200 | 0.4670 |
| group_cv | eye | eye_qixin_500_combined_native | qixin_500 | combined | signal_absolute | logistic_regression | 301 | 0.5856 | 0.4413 |
| group_cv | eye | eye_qixin_500_combined_native | qixin_500 | combined | signal_absolute_demographics | logistic_regression | 301 | 0.6090 | 0.4643 |

Showing 120 of 600 rows.
