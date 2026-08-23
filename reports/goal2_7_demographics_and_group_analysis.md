# Goal 2.7 Demographics and Group Analysis

Main demographics is age + sex + grade. `grade_group` and group proxy variables are reported only in sensitivity/decomposition sets.

## Top Demographic Decomposition Rows

| cv_protocol | cohort_name | modality | task | feature_set | model | n_subjects | auroc | auprc |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| standard_cv | face_self_intro_native | face | self_intro | demographics_group | logistic_regression | 3572 | 0.7083 | 0.4955 |
| standard_cv | face_self_intro_native | face | self_intro | demographics_group_device | logistic_regression | 3572 | 0.7073 | 0.4969 |
| standard_cv | face_task_native | face | task | demographics_group | logistic_regression | 3567 | 0.7070 | 0.4928 |
| standard_cv | face_task_native | face | task | demographics_group_device | logistic_regression | 3567 | 0.7066 | 0.4916 |
| standard_cv | face_self_intro_native | face | self_intro | demographics_group_device | hist_gradient_boosting | 3572 | 0.7058 | 0.4780 |
| standard_cv | face_task_native | face | task | demographics_group_device | hist_gradient_boosting | 3567 | 0.7057 | 0.4791 |
| standard_cv | face_task_native | face | task | demographics_group | hist_gradient_boosting | 3567 | 0.7054 | 0.4779 |
| standard_cv | face_self_intro_native | face | self_intro | demographics_group_device | random_forest | 3572 | 0.7052 | 0.4821 |
| standard_cv | face_self_intro_native | face | self_intro | demographics_group | hist_gradient_boosting | 3572 | 0.7052 | 0.4798 |
| standard_cv | face_self_intro_native | face | self_intro | demographics_group | random_forest | 3572 | 0.7051 | 0.4843 |
| standard_cv | face_task_native | face | task | demographics_group | random_forest | 3567 | 0.7035 | 0.4817 |
| standard_cv | face_task_native | face | task | demographics_group_device | random_forest | 3567 | 0.7035 | 0.4826 |
| group_cv | face_self_intro_native | face | self_intro | demographics_group_device | logistic_regression | 3572 | 0.6775 | 0.4413 |
| standard_cv | face_self_intro_native | face | self_intro | group_proxy_only | logistic_regression | 3572 | 0.6768 | 0.4653 |
| standard_cv | face_task_native | face | task | group_proxy_only | logistic_regression | 3567 | 0.6768 | 0.4652 |
| standard_cv | face_self_intro_native | face | self_intro | group_proxy_only | random_forest | 3572 | 0.6762 | 0.4629 |
| standard_cv | face_task_native | face | task | group_proxy_only | random_forest | 3567 | 0.6755 | 0.4598 |
| standard_cv | face_self_intro_native | face | self_intro | group_proxy_only | hist_gradient_boosting | 3572 | 0.6734 | 0.4482 |
| standard_cv | face_self_intro_native | face | self_intro | age_sex_grade | random_forest | 3572 | 0.6728 | 0.4259 |
| standard_cv | face_self_intro_native | face | self_intro | demographics | random_forest | 3572 | 0.6728 | 0.4259 |
| standard_cv | face_task_native | face | task | group_proxy_only | hist_gradient_boosting | 3567 | 0.6728 | 0.4477 |
| group_cv | face_task_native | face | task | demographics_group_device | logistic_regression | 3567 | 0.6725 | 0.4325 |
| standard_cv | face_self_intro_native | face | self_intro | age_sex_grade_group | random_forest | 3572 | 0.6720 | 0.4238 |
| standard_cv | face_two_video_native | face | two_video | demographics | random_forest | 3567 | 0.6719 | 0.4215 |
| standard_cv | face_task_native | face | task | demographics | random_forest | 3567 | 0.6716 | 0.4213 |
| standard_cv | face_task_native | face | task | age_sex_grade | random_forest | 3567 | 0.6716 | 0.4213 |
| standard_cv | face_task_native | face | task | age_sex_grade_group | random_forest | 3567 | 0.6712 | 0.4238 |
| group_cv | face_self_intro_native | face | self_intro | demographics_group | logistic_regression | 3572 | 0.6710 | 0.4410 |
| standard_cv | face_self_intro_native | face | self_intro | sex_grade | hist_gradient_boosting | 3572 | 0.6709 | 0.4202 |
| standard_cv | face_task_native | face | task | age_sex_grade_group | hist_gradient_boosting | 3567 | 0.6706 | 0.4206 |
| standard_cv | face_self_intro_native | face | self_intro | age_sex_grade | hist_gradient_boosting | 3572 | 0.6705 | 0.4189 |
| standard_cv | face_self_intro_native | face | self_intro | demographics | hist_gradient_boosting | 3572 | 0.6705 | 0.4189 |
| standard_cv | face_self_intro_native | face | self_intro | age_sex_grade | logistic_regression | 3572 | 0.6704 | 0.4306 |
| standard_cv | face_self_intro_native | face | self_intro | demographics | logistic_regression | 3572 | 0.6704 | 0.4306 |
| standard_cv | face_self_intro_native | face | self_intro | sex_grade | random_forest | 3572 | 0.6703 | 0.4206 |
| standard_cv | face_self_intro_native | face | self_intro | age_sex_grade_group | hist_gradient_boosting | 3572 | 0.6702 | 0.4198 |
| standard_cv | face_self_intro_native | face | self_intro | age_sex_grade_group | logistic_regression | 3572 | 0.6702 | 0.4305 |
| standard_cv | face_task_native | face | task | sex_grade | random_forest | 3567 | 0.6702 | 0.4179 |
| standard_cv | face_task_native | face | task | demographics | hist_gradient_boosting | 3567 | 0.6700 | 0.4238 |
| standard_cv | face_task_native | face | task | age_sex_grade | hist_gradient_boosting | 3567 | 0.6700 | 0.4238 |
