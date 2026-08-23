# Goal 2.7 Protocol Comparison

Protocol A is Standard fixed CV; Protocol B is Group-aware fixed CV. They are co-primary and use the same predefined feature/model sets.

## Standard vs Group CV

| cohort_name | modality | device | task | feature_set | model | seed | auroc_standard_cv | auprc_standard_cv | balanced_accuracy_standard_cv | macro_f1_standard_cv | auroc_group_cv | auprc_group_cv | balanced_accuracy_group_cv | macro_f1_group_cv | auroc_delta_standard_minus_group |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| face_task_native | face |  | task | group_proxy_only | logistic_regression | 20260707 | 0.6768 | 0.4652 | 0.6296 | 0.6034 | 0.4518 | 0.2953 | 0.4912 | 0.4902 | 0.2249 |
| face_self_intro_native | face |  | self_intro | group_proxy_only | logistic_regression | 20260707 | 0.6768 | 0.4653 | 0.6293 | 0.6018 | 0.4525 | 0.2952 | 0.5081 | 0.5035 | 0.2243 |
| face_self_intro_native | face |  | self_intro | group_proxy_only | random_forest | 20260707 | 0.6762 | 0.4629 | 0.6306 | 0.6031 | 0.4613 | 0.2996 | 0.5082 | 0.5079 | 0.2150 |
| face_task_native | face |  | task | group_proxy_only | hist_gradient_boosting | 20260707 | 0.6728 | 0.4477 | 0.6343 | 0.6033 | 0.4604 | 0.3002 | 0.5030 | 0.5012 | 0.2124 |
| fnirs_bikom_vft_native | fnirs | bikom | vft | group_proxy_only | logistic_regression | 20260707 | 0.5900 | 0.3806 | 0.5903 | 0.5387 | 0.3912 | 0.2642 | 0.5007 | 0.2418 | 0.1989 |
| face_task_native | face |  | task | group_proxy_only | random_forest | 20260707 | 0.6755 | 0.4598 | 0.6324 | 0.6114 | 0.4879 | 0.3137 | 0.5001 | 0.4975 | 0.1876 |
| face_self_intro_native | face |  | self_intro | group_proxy_only | hist_gradient_boosting | 20260707 | 0.6734 | 0.4482 | 0.6284 | 0.5968 | 0.4889 | 0.3170 | 0.5236 | 0.5236 | 0.1845 |
| fnirs_bikom_rest_native | fnirs | bikom | rest | group_proxy_only | random_forest | 20260707 | 0.6002 | 0.3969 | 0.5862 | 0.5383 | 0.4384 | 0.2962 | 0.5922 | 0.5387 | 0.1619 |
| fnirs_bikom_1back_native | fnirs | bikom | 1back | group_proxy_only | logistic_regression | 20260707 | 0.5893 | 0.3747 | 0.5955 | 0.5436 | 0.4284 | 0.2900 | 0.5963 | 0.5446 | 0.1609 |
| fnirs_bikom_vft_native | fnirs | bikom | vft | group_proxy_only | random_forest | 20260707 | 0.5969 | 0.3885 | 0.5883 | 0.5405 | 0.4380 | 0.2963 | 0.5007 | 0.2418 | 0.1589 |
| fnirs_yiruid_vft_native | fnirs | yiruid | vft | group_proxy_only | hist_gradient_boosting | 20260707 | 0.6213 | 0.5081 | 0.6066 | 0.5756 | 0.4638 | 0.3746 | 0.4939 | 0.4362 | 0.1575 |
| eeg_oddball_native | eeg |  | oddball | group_proxy_only | logistic_regression | 20260707 | 0.6019 | 0.3881 | 0.5878 | 0.5409 | 0.4454 | 0.3048 | 0.5094 | 0.3730 | 0.1565 |
| fnirs_bikom_1back_native | fnirs | bikom | 1back | group_proxy_only | random_forest | 20260707 | 0.5958 | 0.3870 | 0.5739 | 0.5511 | 0.4439 | 0.2972 | 0.5963 | 0.5446 | 0.1519 |
| fnirs_yiruid_rest_native | fnirs | yiruid | rest | group_proxy_only | hist_gradient_boosting | 20260707 | 0.6245 | 0.5104 | 0.6053 | 0.5726 | 0.4781 | 0.3850 | 0.4477 | 0.4477 | 0.1464 |
| fnirs_yiruid_1back_native | fnirs | yiruid | 1back | group_proxy_only | logistic_regression | 20260707 | 0.6302 | 0.5119 | 0.6122 | 0.5764 | 0.4892 | 0.3787 | 0.4436 | 0.4407 | 0.1411 |
| fnirs_yiruid_rest_native | fnirs | yiruid | rest | group_proxy_only | random_forest | 20260707 | 0.6265 | 0.5107 | 0.6045 | 0.5692 | 0.4855 | 0.3705 | 0.5089 | 0.4679 | 0.1411 |
| fnirs_bikom_1back_native | fnirs | bikom | 1back | group_proxy_only | hist_gradient_boosting | 20260707 | 0.5933 | 0.3836 | 0.5937 | 0.5441 | 0.4548 | 0.3017 | 0.5963 | 0.5446 | 0.1385 |
| eeg_oddball_native | eeg |  | oddball | group_proxy_only | random_forest | 20260707 | 0.6040 | 0.3873 | 0.5893 | 0.5665 | 0.4655 | 0.3177 | 0.5075 | 0.2926 | 0.1385 |
| fnirs_yiruid_rest_native | fnirs | yiruid | rest | group_proxy_only | logistic_regression | 20260707 | 0.6278 | 0.5097 | 0.6098 | 0.5759 | 0.4952 | 0.3799 | 0.5089 | 0.4679 | 0.1326 |
| fnirs_yiruid_vft_native | fnirs | yiruid | vft | group_proxy_only | logistic_regression | 20260707 | 0.6268 | 0.5103 | 0.6123 | 0.5811 | 0.4991 | 0.3885 | 0.5181 | 0.4344 | 0.1277 |
| eeg_rest_native | eeg |  | rest | group_proxy_only | logistic_regression | 20260707 | 0.6159 | 0.4195 | 0.5853 | 0.5558 | 0.4889 | 0.3215 | 0.5056 | 0.4883 | 0.1270 |
| eeg_rest_native | eeg |  | rest | group_proxy_only | random_forest | 20260707 | 0.6173 | 0.4183 | 0.5853 | 0.5558 | 0.4975 | 0.3307 | 0.5056 | 0.4883 | 0.1198 |
| eeg_rest_native | eeg |  | rest | group_proxy_only | hist_gradient_boosting | 20260707 | 0.6188 | 0.4271 | 0.5799 | 0.5404 | 0.5093 | 0.3593 | 0.5052 | 0.4703 | 0.1095 |
| fnirs_yiruid_rest_native | fnirs | yiruid | rest | fnirs_device_only | random_forest | 20260707 | 0.5014 | 0.3873 | 0.5029 | 0.4143 | 0.3920 | 0.3412 | 0.4388 | 0.3698 | 0.1094 |
| fnirs_yiruid_1back_native | fnirs | yiruid | 1back | no_information | no_information_prior | 20260707 | 0.4948 | 0.3861 | 0.5000 | 0.3793 | 0.3870 | 0.3342 | 0.5000 | 0.3793 | 0.1078 |
| fnirs_yiruid_rest_native | fnirs | yiruid | rest | no_information | no_information_prior | 20260707 | 0.4939 | 0.3829 | 0.5000 | 0.3803 | 0.3869 | 0.3317 | 0.5000 | 0.3803 | 0.1069 |
| fnirs_yiruid_vft_native | fnirs | yiruid | vft | no_information | no_information_prior | 20260707 | 0.4922 | 0.3792 | 0.5000 | 0.3813 | 0.3901 | 0.3315 | 0.5000 | 0.3813 | 0.1022 |
| core3_rest_yiruidvft_selfintro_intersection | face |  | self_intro | group_proxy_only | hist_gradient_boosting | 20260707 | 0.6003 | 0.4100 | 0.5932 | 0.5792 | 0.4983 | 0.3666 | 0.4439 | 0.3841 | 0.1020 |
| core3_rest_yiruidvft_selfintro_intersection | eeg |  | rest | group_proxy_only | hist_gradient_boosting | 20260707 | 0.6003 | 0.4100 | 0.5932 | 0.5792 | 0.4983 | 0.3666 | 0.4439 | 0.3841 | 0.1020 |
| core3_rest_yiruidvft_selfintro_intersection | fnirs | yiruid | vft | group_proxy_only | hist_gradient_boosting | 20260707 | 0.6003 | 0.4100 | 0.5932 | 0.5792 | 0.4983 | 0.3666 | 0.4439 | 0.3841 | 0.1020 |
| core3_rest_yiruidvft_selfintro_intersection | fnirs | yiruid | vft | demographics_group_device | hist_gradient_boosting | 20260707 | 0.6141 | 0.4392 | 0.5933 | 0.5849 | 0.5137 | 0.3401 | 0.5486 | 0.4797 | 0.1003 |
| core3_rest_yiruidvft_selfintro_intersection | face |  | self_intro | demographics_group | hist_gradient_boosting | 20260707 | 0.6141 | 0.4392 | 0.5933 | 0.5849 | 0.5137 | 0.3401 | 0.5486 | 0.4797 | 0.1003 |
| core3_rest_yiruidvft_selfintro_intersection | face |  | self_intro | demographics_group_device | hist_gradient_boosting | 20260707 | 0.6141 | 0.4392 | 0.5933 | 0.5849 | 0.5137 | 0.3401 | 0.5486 | 0.4797 | 0.1003 |
| core3_rest_yiruidvft_selfintro_intersection | eeg |  | rest | demographics_group_device | hist_gradient_boosting | 20260707 | 0.6141 | 0.4392 | 0.5933 | 0.5849 | 0.5137 | 0.3401 | 0.5486 | 0.4797 | 0.1003 |
| core3_rest_yiruidvft_selfintro_intersection | fnirs | yiruid | vft | demographics_group | hist_gradient_boosting | 20260707 | 0.6141 | 0.4392 | 0.5933 | 0.5849 | 0.5137 | 0.3401 | 0.5486 | 0.4797 | 0.1003 |
| core3_rest_yiruidvft_selfintro_intersection | eeg |  | rest | demographics_group | hist_gradient_boosting | 20260707 | 0.6141 | 0.4392 | 0.5933 | 0.5849 | 0.5137 | 0.3401 | 0.5486 | 0.4797 | 0.1003 |
| face_two_video_native | face |  | two_video | no_information | no_information_prior | 20260707 | 0.4960 | 0.3014 | 0.5000 | 0.4106 | 0.3998 | 0.2599 | 0.5000 | 0.4106 | 0.0962 |
| face_task_native | face |  | task | no_information | no_information_prior | 20260707 | 0.4960 | 0.3014 | 0.5000 | 0.4106 | 0.3998 | 0.2599 | 0.5000 | 0.4106 | 0.0962 |
| face_self_intro_native | face |  | self_intro | no_information | no_information_prior | 20260707 | 0.4960 | 0.3016 | 0.5000 | 0.4106 | 0.4000 | 0.2601 | 0.5000 | 0.4106 | 0.0960 |
| face_two_video_native | face |  | two_video | background | random_forest | 20260707 | 0.6283 | 0.3979 | 0.5851 | 0.5586 | 0.5334 | 0.3339 | 0.5497 | 0.5228 | 0.0949 |
| fnirs_yiruid_1back_native | fnirs | yiruid | 1back | group_proxy_only | random_forest | 20260707 | 0.6291 | 0.5123 | 0.6110 | 0.5757 | 0.5345 | 0.4175 | 0.5124 | 0.4141 | 0.0946 |
| fnirs_bikom_rest_native | fnirs | bikom | rest | no_information | no_information_prior | 20260707 | 0.4923 | 0.3116 | 0.5000 | 0.4063 | 0.3995 | 0.2692 | 0.5000 | 0.4063 | 0.0928 |
| fnirs_bikom_vft_native | fnirs | bikom | vft | no_information | no_information_prior | 20260707 | 0.4921 | 0.3116 | 0.5000 | 0.4062 | 0.3996 | 0.2696 | 0.5000 | 0.4062 | 0.0925 |
| fnirs_yiruid_1back_native | fnirs | yiruid | 1back | demographics_group_device | hist_gradient_boosting | 20260707 | 0.6611 | 0.5458 | 0.6105 | 0.5802 | 0.5697 | 0.4403 | 0.5279 | 0.4992 | 0.0914 |
| fnirs_yiruid_1back_native | fnirs | yiruid | 1back | demographics_group | hist_gradient_boosting | 20260707 | 0.6611 | 0.5458 | 0.6105 | 0.5802 | 0.5697 | 0.4403 | 0.5279 | 0.4992 | 0.0914 |
| fnirs_bikom_1back_native | fnirs | bikom | 1back | no_information | no_information_prior | 20260707 | 0.4866 | 0.3083 | 0.5000 | 0.4063 | 0.3963 | 0.2681 | 0.5000 | 0.4063 | 0.0903 |
| fnirs_yiruid_vft_native | fnirs | yiruid | vft | group_proxy_only | random_forest | 20260707 | 0.6275 | 0.5107 | 0.6125 | 0.5817 | 0.5393 | 0.4061 | 0.5053 | 0.3965 | 0.0882 |
| eeg_oddball_native | eeg |  | oddball | no_information | no_information_prior | 20260707 | 0.4882 | 0.3276 | 0.5000 | 0.3996 | 0.4009 | 0.2863 | 0.5000 | 0.3996 | 0.0873 |
| fnirs_yiruid_vft_native | fnirs | yiruid | vft | demographics_group | hist_gradient_boosting | 20260707 | 0.6541 | 0.5395 | 0.6074 | 0.5801 | 0.5670 | 0.4342 | 0.5386 | 0.5164 | 0.0872 |
| fnirs_yiruid_vft_native | fnirs | yiruid | vft | demographics_group_device | hist_gradient_boosting | 20260707 | 0.6541 | 0.5395 | 0.6074 | 0.5801 | 0.5670 | 0.4342 | 0.5386 | 0.5164 | 0.0872 |
| fnirs_yiruid_rest_native | fnirs | yiruid | rest | demographics_group_device | hist_gradient_boosting | 20260707 | 0.6587 | 0.5419 | 0.6127 | 0.5869 | 0.5722 | 0.4286 | 0.5390 | 0.5156 | 0.0865 |
| fnirs_yiruid_rest_native | fnirs | yiruid | rest | demographics_group | hist_gradient_boosting | 20260707 | 0.6587 | 0.5419 | 0.6127 | 0.5869 | 0.5722 | 0.4286 | 0.5390 | 0.5156 | 0.0865 |
| face_two_video_native | face |  | two_video | background_blur | random_forest | 20260707 | 0.6318 | 0.4077 | 0.5965 | 0.5522 | 0.5454 | 0.3360 | 0.5540 | 0.5048 | 0.0864 |
| fnirs_yiruid_1back_native | fnirs | yiruid | 1back | demographics_group_device | random_forest | 20260707 | 0.6610 | 0.5492 | 0.6238 | 0.5956 | 0.5763 | 0.4434 | 0.5567 | 0.5188 | 0.0847 |
| eeg_rest_native | eeg |  | rest | demographics_group | hist_gradient_boosting | 20260707 | 0.6292 | 0.4343 | 0.5683 | 0.5373 | 0.5449 | 0.3675 | 0.5618 | 0.5440 | 0.0842 |
| eeg_rest_native | eeg |  | rest | demographics_group_device | hist_gradient_boosting | 20260707 | 0.6244 | 0.4399 | 0.5809 | 0.5511 | 0.5417 | 0.3710 | 0.5119 | 0.4979 | 0.0827 |
| eeg_1back_native | eeg |  | 1back | no_information | no_information_prior | 20260707 | 0.4718 | 0.2776 | 0.5000 | 0.4142 | 0.3893 | 0.2479 | 0.5000 | 0.4142 | 0.0825 |
| fnirs_yiruid_1back_native | fnirs | yiruid | 1back | demographics_group | logistic_regression | 20260707 | 0.6645 | 0.5407 | 0.6078 | 0.5882 | 0.5839 | 0.4493 | 0.5685 | 0.5502 | 0.0806 |
| fnirs_yiruid_1back_native | fnirs | yiruid | 1back | demographics_group_device | logistic_regression | 20260707 | 0.6645 | 0.5408 | 0.6078 | 0.5882 | 0.5840 | 0.4504 | 0.5690 | 0.5509 | 0.0805 |
| fnirs_yiruid_vft_native | fnirs | yiruid | vft | demographics_group | logistic_regression | 20260707 | 0.6592 | 0.5355 | 0.6144 | 0.5997 | 0.5791 | 0.4398 | 0.5526 | 0.5455 | 0.0800 |
| eeg_rest_native | eeg |  | rest | grade_group_only | random_forest | 20260707 | 0.5052 | 0.3512 | 0.5089 | 0.2995 | 0.4254 | 0.3131 | 0.4254 | 0.4151 | 0.0798 |
| fnirs_yiruid_vft_native | fnirs | yiruid | vft | demographics_group_device | logistic_regression | 20260707 | 0.6586 | 0.5370 | 0.6132 | 0.5961 | 0.5792 | 0.4396 | 0.5526 | 0.5455 | 0.0794 |
| eeg_1back_native | eeg |  | 1back | group_proxy_only | random_forest | 20260707 | 0.6034 | 0.3565 | 0.5898 | 0.5447 | 0.5291 | 0.3125 | 0.5000 | 0.2265 | 0.0743 |
| fnirs_bikom_vft_native | fnirs | bikom | vft | group_proxy_only | hist_gradient_boosting | 20260707 | 0.5983 | 0.3949 | 0.5900 | 0.5460 | 0.5241 | 0.3336 | 0.5921 | 0.5382 | 0.0742 |
| fnirs_yiruid_vft_native | fnirs | yiruid | vft | demographics_group | random_forest | 20260707 | 0.6551 | 0.5418 | 0.6162 | 0.5831 | 0.5810 | 0.4588 | 0.5402 | 0.4989 | 0.0741 |
| face_self_intro_native | face |  | self_intro | full_frame | random_forest | 20260707 | 0.6257 | 0.3922 | 0.5965 | 0.5578 | 0.5531 | 0.3593 | 0.5549 | 0.5064 | 0.0726 |
| eeg_1back_native | eeg |  | 1back | demographics_group_device | random_forest | 20260707 | 0.6299 | 0.3828 | 0.5871 | 0.5422 | 0.5575 | 0.3420 | 0.5151 | 0.4443 | 0.0724 |
| fnirs_yiruid_rest_native | fnirs | yiruid | rest | demographics_group | logistic_regression | 20260707 | 0.6616 | 0.5407 | 0.6318 | 0.6231 | 0.5895 | 0.4517 | 0.5720 | 0.5555 | 0.0721 |
| fnirs_yiruid_rest_native | fnirs | yiruid | rest | demographics_group_device | logistic_regression | 20260707 | 0.6616 | 0.5407 | 0.6318 | 0.6231 | 0.5901 | 0.4498 | 0.5844 | 0.5725 | 0.0715 |
| fnirs_yiruid_1back_native | fnirs | yiruid | 1back | demographics_group | random_forest | 20260707 | 0.6531 | 0.5432 | 0.6202 | 0.5842 | 0.5817 | 0.4503 | 0.5619 | 0.5185 | 0.0714 |
| fnirs_bikom_vft_native | fnirs | bikom | vft | signal_qc | random_forest | 20260707 | 0.5619 | 0.3568 | 0.5412 | 0.5227 | 0.4907 | 0.3202 | 0.5777 | 0.5774 | 0.0712 |
| fnirs_bikom_rest_native | fnirs | bikom | rest | group_proxy_only | logistic_regression | 20260707 | 0.5950 | 0.3891 | 0.5897 | 0.5383 | 0.5248 | 0.3312 | 0.5851 | 0.5578 | 0.0702 |
| fnirs_yiruid_rest_native | fnirs | yiruid | rest | demographics_group_device | random_forest | 20260707 | 0.6586 | 0.5431 | 0.6160 | 0.5974 | 0.5889 | 0.4590 | 0.5493 | 0.4976 | 0.0697 |
| fnirs_bikom_rest_native | fnirs | bikom | rest | group_proxy_only | hist_gradient_boosting | 20260707 | 0.5932 | 0.3885 | 0.5862 | 0.5383 | 0.5250 | 0.3332 | 0.5922 | 0.5387 | 0.0682 |
| fnirs_yiruid_rest_native | fnirs | yiruid | rest | demographics_group | random_forest | 20260707 | 0.6590 | 0.5448 | 0.6186 | 0.5973 | 0.5908 | 0.4610 | 0.5505 | 0.4980 | 0.0682 |
| fnirs_bikom_vft_native | fnirs | bikom | vft | signal_demographics | random_forest | 20260707 | 0.5647 | 0.3685 | 0.5161 | 0.5159 | 0.4971 | 0.3213 | 0.4946 | 0.4799 | 0.0676 |
| eeg_1back_native | eeg |  | 1back | group_proxy_only | hist_gradient_boosting | 20260707 | 0.6059 | 0.3560 | 0.5950 | 0.5402 | 0.5384 | 0.3304 | 0.4952 | 0.2824 | 0.0674 |
| eeg_rest_native | eeg |  | rest | grade_group_only | hist_gradient_boosting | 20260707 | 0.4923 | 0.3348 | 0.5089 | 0.2995 | 0.4260 | 0.3154 | 0.4254 | 0.4151 | 0.0663 |
| eeg_1back_native | eeg |  | 1back | demographics_group_device | hist_gradient_boosting | 20260707 | 0.6263 | 0.3885 | 0.5789 | 0.5368 | 0.5601 | 0.3535 | 0.5488 | 0.4933 | 0.0663 |
| face_task_native | face |  | task | background_blur | hist_gradient_boosting | 20260707 | 0.6233 | 0.3915 | 0.5889 | 0.5430 | 0.5572 | 0.3558 | 0.5515 | 0.4952 | 0.0661 |
