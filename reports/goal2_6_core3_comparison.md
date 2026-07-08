# Goal 2.6 Core3 Same-Cohort Comparison

Protocol: fixed `split_group == cv` only; subject-level OOF predictions; 3-fold inner CV for hyperparameters and thresholds; baseline-exposed pilot holdout excluded throughout.

Core3 uses the intersection of subjects with EEG Rest, one available fNIRS task/device, and Face self-introduction features. Every modality is compared on the same subject cohort.

## Core3 Performance

| modality | device | task | feature_set | model | n_subjects | auroc | auprc | balanced_accuracy | macro_f1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fnirs | yiruid | vft | modality | random_forest | 661 | 0.5845 | 0.4330 | 0.5765 | 0.5776 |
| fnirs | yiruid | vft | modality_demographics | random_forest | 661 | 0.5788 | 0.4332 | 0.5782 | 0.5785 |
| eeg |  | rest | demographics | logistic_regression | 661 | 0.5754 | 0.3942 | 0.5691 | 0.5521 |
| face |  | self_intro | demographics | logistic_regression | 661 | 0.5754 | 0.3942 | 0.5691 | 0.5521 |
| fnirs | yiruid | vft | demographics | logistic_regression | 661 | 0.5754 | 0.3942 | 0.5691 | 0.5521 |
| face |  | self_intro | modality_demographics | logistic_regression | 661 | 0.5703 | 0.4254 | 0.5426 | 0.5221 |
| face |  | self_intro | modality | logistic_regression | 661 | 0.5670 | 0.4229 | 0.5394 | 0.5201 |
| eeg |  | rest | demographics | random_forest | 661 | 0.5593 | 0.3764 | 0.5581 | 0.4657 |
| fnirs | yiruid | vft | demographics | random_forest | 661 | 0.5593 | 0.3764 | 0.5581 | 0.4657 |
| eeg |  | rest | demographics | hist_gradient_boosting | 661 | 0.5574 | 0.3752 | 0.5471 | 0.3992 |
| face |  | self_intro | demographics | hist_gradient_boosting | 661 | 0.5574 | 0.3752 | 0.5471 | 0.3992 |
| fnirs | yiruid | vft | demographics | hist_gradient_boosting | 661 | 0.5574 | 0.3752 | 0.5471 | 0.3992 |
| face |  | self_intro | modality | hist_gradient_boosting | 661 | 0.5568 | 0.4193 | 0.5351 | 0.5283 |
| fnirs | yiruid | vft | modality | hist_gradient_boosting | 661 | 0.5551 | 0.3960 | 0.5510 | 0.5448 |
| fnirs | yiruid | vft | modality_demographics | hist_gradient_boosting | 661 | 0.5551 | 0.3960 | 0.5510 | 0.5448 |
| eeg |  | rest | modality_demographics | logistic_regression | 661 | 0.5533 | 0.3825 | 0.5169 | 0.4272 |
| face |  | self_intro | modality_demographics | hist_gradient_boosting | 661 | 0.5456 | 0.4002 | 0.5314 | 0.5238 |
| fnirs | yiruid | vft | modality_demographics | logistic_regression | 661 | 0.5335 | 0.3780 | 0.5229 | 0.5065 |
| fnirs | yiruid | vft | modality | logistic_regression | 661 | 0.5299 | 0.3811 | 0.5185 | 0.4867 |
| eeg |  | rest | modality | logistic_regression | 661 | 0.5143 | 0.3575 | 0.4972 | 0.4151 |
| eeg |  | rest | modality_demographics | random_forest | 661 | 0.5133 | 0.3617 | 0.4897 | 0.3299 |
| eeg |  | rest | modality | random_forest | 661 | 0.5015 | 0.3571 | 0.4935 | 0.3189 |
| eeg |  | rest | modality_demographics | hist_gradient_boosting | 661 | 0.4979 | 0.3457 | 0.4896 | 0.2698 |
| eeg |  | rest | modality | hist_gradient_boosting | 661 | 0.4937 | 0.3401 | 0.4888 | 0.3798 |

## Core3 Subject Counts

| cohort_name | modality | device | task | feature_set | n_subjects | feature_count | numeric_count | categorical_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| core3_same_cohort | eeg |  | rest | demographics | 661 | 4 | 1 | 3 |
| core3_same_cohort | eeg |  | rest | modality | 661 | 217 | 217 | 0 |
| core3_same_cohort | eeg |  | rest | modality_demographics | 661 | 221 | 218 | 3 |
| core3_same_cohort | fnirs | yiruid | vft | demographics | 661 | 4 | 1 | 3 |
| core3_same_cohort | fnirs | yiruid | vft | modality | 661 | 289 | 289 | 0 |
| core3_same_cohort | fnirs | yiruid | vft | modality_demographics | 661 | 293 | 290 | 3 |
| core3_same_cohort | face |  | self_intro | demographics | 661 | 4 | 1 | 3 |
| core3_same_cohort | face |  | self_intro | modality | 661 | 1024 | 1024 | 0 |
| core3_same_cohort | face |  | self_intro | modality_demographics | 661 | 1028 | 1025 | 3 |
