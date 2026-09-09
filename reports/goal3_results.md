# Goal 3 Results

Machine-generated from `results/goal3/`. The design, the decision rule and the
predictions recorded before any model was trained are in
`reports/goal3_method_design.md`; the reading of these numbers is in
`reports/goal3_final_report.md`.

Every row is the seed-averaged result over three seeds, on the same 1820 subjects
and the same fixed folds as Goal 2.8, with inner-CV thresholds.

## Confirmatory Test

EEGNet, condition-aware, no per-subject normalisation: `p_Demo + p_EEG` against
`p_Demo`, under both CV protocols. One pre-declared test, no multiplicity
correction.

| cv_protocol   | model                                   |   auroc_diff |   auroc_diff_ci_low |   auroc_diff_ci_high |   comparator_auroc |   comparator_above_chance |   folds_positive |   both_protocols_positive | verdict               |
|:--------------|:----------------------------------------|-------------:|--------------------:|---------------------:|-------------------:|--------------------------:|-----------------:|--------------------------:|:----------------------|
| group_cv      | eegnet__condition_aware__mean_std__none |      -0.0031 |             -0.0150 |               0.0094 |             0.5909 |                         1 |                3 |                         0 | NO_INDEPENDENT_SIGNAL |
| standard_cv   | eegnet__condition_aware__mean_std__none |       0.0016 |             -0.0059 |               0.0084 |             0.6023 |                         1 |                4 |                         0 | NO_INDEPENDENT_SIGNAL |

## Exploratory Family

Twelve configurations x two protocols, closed and enumerated before the run.
Benjamini-Hochberg at 0.05 across the family, on two-sided paired bootstrap
p-values, in addition to every confirmatory requirement.

| cv_protocol   | model                                          |   auroc_diff |   auroc_diff_ci_low |   auroc_diff_ci_high |   comparator_auroc |   comparator_above_chance |   folds_positive |   both_protocols_positive |   p_two_sided |   fdr_significant | verdict               |
|:--------------|:-----------------------------------------------|-------------:|--------------------:|---------------------:|-------------------:|--------------------------:|-----------------:|--------------------------:|--------------:|------------------:|:----------------------|
| group_cv      | conformer__condition_aware__mean_std__none     |      -0.0078 |             -0.0188 |               0.0034 |             0.5909 |                         1 |                0 |                         0 |        0.1760 |                 0 | NO_INDEPENDENT_SIGNAL |
| group_cv      | conformer__difference_wave__mean_std__none     |      -0.0066 |             -0.0177 |               0.0039 |             0.5909 |                         1 |                3 |                         0 |        0.2160 |                 0 | NO_INDEPENDENT_SIGNAL |
| group_cv      | conformer__standard_only__mean_std__none       |      -0.0071 |             -0.0187 |               0.0029 |             0.5909 |                         1 |                1 |                         0 |        0.1860 |                 0 | NO_INDEPENDENT_SIGNAL |
| group_cv      | conformer__target_only__mean_std__none         |      -0.0076 |             -0.0176 |               0.0026 |             0.5909 |                         1 |                2 |                         0 |        0.1620 |                 0 | NO_INDEPENDENT_SIGNAL |
| group_cv      | eegnet__condition_aware__attention__none       |      -0.0035 |             -0.0149 |               0.0077 |             0.5909 |                         1 |                4 |                         0 |        0.5580 |                 0 | NO_INDEPENDENT_SIGNAL |
| group_cv      | eegnet__difference_wave__mean_std__none        |      -0.0061 |             -0.0173 |               0.0054 |             0.5909 |                         1 |                3 |                         0 |        0.2980 |                 0 | NO_INDEPENDENT_SIGNAL |
| group_cv      | eegnet__standard_only__mean_std__none          |      -0.0056 |             -0.0160 |               0.0050 |             0.5909 |                         1 |                3 |                         0 |        0.2920 |                 0 | NO_INDEPENDENT_SIGNAL |
| group_cv      | eegnet__target_only__mean_std__none            |      -0.0057 |             -0.0174 |               0.0049 |             0.5909 |                         1 |                2 |                         0 |        0.3140 |                 0 | NO_INDEPENDENT_SIGNAL |
| group_cv      | inceptiontime__condition_aware__mean_std__none |      -0.0068 |             -0.0180 |               0.0046 |             0.5909 |                         1 |                2 |                         0 |        0.2660 |                 0 | NO_INDEPENDENT_SIGNAL |
| group_cv      | inceptiontime__difference_wave__mean_std__none |      -0.0064 |             -0.0167 |               0.0046 |             0.5909 |                         1 |                3 |                         0 |        0.2660 |                 0 | NO_INDEPENDENT_SIGNAL |
| group_cv      | inceptiontime__standard_only__mean_std__none   |      -0.0071 |             -0.0175 |               0.0041 |             0.5909 |                         1 |                1 |                         0 |        0.2140 |                 0 | NO_INDEPENDENT_SIGNAL |
| group_cv      | inceptiontime__target_only__mean_std__none     |      -0.0062 |             -0.0166 |               0.0055 |             0.5909 |                         1 |                4 |                         0 |        0.2580 |                 0 | NO_INDEPENDENT_SIGNAL |
| standard_cv   | conformer__condition_aware__mean_std__none     |       0.0017 |             -0.0046 |               0.0081 |             0.6023 |                         1 |                2 |                         0 |        0.5480 |                 0 | NO_INDEPENDENT_SIGNAL |
| standard_cv   | conformer__difference_wave__mean_std__none     |       0.0019 |             -0.0046 |               0.0083 |             0.6023 |                         1 |                3 |                         0 |        0.5820 |                 0 | NO_INDEPENDENT_SIGNAL |
| standard_cv   | conformer__standard_only__mean_std__none       |       0.0025 |             -0.0034 |               0.0089 |             0.6023 |                         1 |                3 |                         0 |        0.4260 |                 0 | NO_INDEPENDENT_SIGNAL |
| standard_cv   | conformer__target_only__mean_std__none         |       0.0019 |             -0.0048 |               0.0090 |             0.6023 |                         1 |                4 |                         0 |        0.6080 |                 0 | NO_INDEPENDENT_SIGNAL |
| standard_cv   | eegnet__condition_aware__attention__none       |       0.0045 |             -0.0026 |               0.0124 |             0.6023 |                         1 |                5 |                         0 |        0.2400 |                 0 | NO_INDEPENDENT_SIGNAL |
| standard_cv   | eegnet__difference_wave__mean_std__none        |       0.0007 |             -0.0064 |               0.0074 |             0.6023 |                         1 |                1 |                         0 |        0.8520 |                 0 | NO_INDEPENDENT_SIGNAL |
| standard_cv   | eegnet__standard_only__mean_std__none          |       0.0021 |             -0.0050 |               0.0096 |             0.6023 |                         1 |                4 |                         0 |        0.5920 |                 0 | NO_INDEPENDENT_SIGNAL |
| standard_cv   | eegnet__target_only__mean_std__none            |       0.0029 |             -0.0039 |               0.0095 |             0.6023 |                         1 |                4 |                         0 |        0.4420 |                 0 | NO_INDEPENDENT_SIGNAL |
| standard_cv   | inceptiontime__condition_aware__mean_std__none |       0.0017 |             -0.0048 |               0.0089 |             0.6023 |                         1 |                3 |                         0 |        0.5780 |                 0 | NO_INDEPENDENT_SIGNAL |
| standard_cv   | inceptiontime__difference_wave__mean_std__none |       0.0009 |             -0.0053 |               0.0069 |             0.6023 |                         1 |                4 |                         0 |        0.7640 |                 0 | NO_INDEPENDENT_SIGNAL |
| standard_cv   | inceptiontime__standard_only__mean_std__none   |       0.0028 |             -0.0038 |               0.0093 |             0.6023 |                         1 |                5 |                         0 |        0.3920 |                 0 | NO_INDEPENDENT_SIGNAL |
| standard_cv   | inceptiontime__target_only__mean_std__none     |       0.0007 |             -0.0053 |               0.0071 |             0.6023 |                         1 |                3 |                         0 |        0.8200 |                 0 | NO_INDEPENDENT_SIGNAL |

## All Paired Increments

| cv_protocol   | model                                          | comparison                                            |   n_subjects |   auroc_diff |   auroc_diff_ci_low |   auroc_diff_ci_high |   fold_direction_consistency |   comparator_auroc |   comparator_above_chance |
|:--------------|:-----------------------------------------------|:------------------------------------------------------|-------------:|-------------:|--------------------:|---------------------:|-----------------------------:|-------------------:|--------------------------:|
| group_cv      | eegnet__condition_aware__mean_std__none        | demographics_eeg_deep_vs_demographics                 |         1820 |      -0.0031 |             -0.0150 |               0.0094 |                            3 |             0.5909 |                         1 |
| group_cv      | eegnet__condition_aware__attention__none       | demographics_eeg_deep_vs_demographics                 |         1820 |      -0.0035 |             -0.0149 |               0.0077 |                            4 |             0.5909 |                         1 |
| group_cv      | eegnet__condition_aware__mean_std__robust_z    | demographics_eeg_deep_vs_demographics                 |         1820 |      -0.0046 |             -0.0158 |               0.0056 |                            1 |             0.5909 |                         1 |
| group_cv      | eegnet__standard_only__mean_std__none          | demographics_eeg_deep_vs_demographics                 |         1820 |      -0.0056 |             -0.0160 |               0.0050 |                            3 |             0.5909 |                         1 |
| group_cv      | eegnet__target_only__mean_std__none            | demographics_eeg_deep_vs_demographics                 |         1820 |      -0.0057 |             -0.0174 |               0.0049 |                            2 |             0.5909 |                         1 |
| group_cv      | eegnet__difference_wave__mean_std__none        | demographics_eeg_deep_vs_demographics                 |         1820 |      -0.0061 |             -0.0173 |               0.0054 |                            3 |             0.5909 |                         1 |
| group_cv      | inceptiontime__target_only__mean_std__none     | demographics_eeg_deep_vs_demographics                 |         1820 |      -0.0062 |             -0.0166 |               0.0055 |                            4 |             0.5909 |                         1 |
| group_cv      | inceptiontime__difference_wave__mean_std__none | demographics_eeg_deep_vs_demographics                 |         1820 |      -0.0064 |             -0.0167 |               0.0046 |                            3 |             0.5909 |                         1 |
| group_cv      | conformer__difference_wave__mean_std__none     | demographics_eeg_deep_vs_demographics                 |         1820 |      -0.0066 |             -0.0177 |               0.0039 |                            3 |             0.5909 |                         1 |
| group_cv      | inceptiontime__condition_aware__mean_std__none | demographics_eeg_deep_vs_demographics                 |         1820 |      -0.0068 |             -0.0180 |               0.0046 |                            2 |             0.5909 |                         1 |
| group_cv      | inceptiontime__standard_only__mean_std__none   | demographics_eeg_deep_vs_demographics                 |         1820 |      -0.0071 |             -0.0175 |               0.0041 |                            1 |             0.5909 |                         1 |
| group_cv      | conformer__standard_only__mean_std__none       | demographics_eeg_deep_vs_demographics                 |         1820 |      -0.0071 |             -0.0187 |               0.0029 |                            1 |             0.5909 |                         1 |
| group_cv      | conformer__target_only__mean_std__none         | demographics_eeg_deep_vs_demographics                 |         1820 |      -0.0076 |             -0.0176 |               0.0026 |                            2 |             0.5909 |                         1 |
| group_cv      | conformer__condition_aware__mean_std__none     | demographics_eeg_deep_vs_demographics                 |         1820 |      -0.0078 |             -0.0188 |               0.0034 |                            0 |             0.5909 |                         1 |
| standard_cv   | eegnet__condition_aware__attention__none       | demographics_eeg_deep_vs_demographics                 |         1820 |       0.0045 |             -0.0026 |               0.0124 |                            5 |             0.6023 |                         1 |
| standard_cv   | eegnet__condition_aware__mean_std__robust_z    | demographics_eeg_deep_vs_demographics                 |         1820 |       0.0038 |             -0.0030 |               0.0112 |                            5 |             0.6023 |                         1 |
| standard_cv   | eegnet__target_only__mean_std__none            | demographics_eeg_deep_vs_demographics                 |         1820 |       0.0029 |             -0.0039 |               0.0095 |                            4 |             0.6023 |                         1 |
| standard_cv   | inceptiontime__standard_only__mean_std__none   | demographics_eeg_deep_vs_demographics                 |         1820 |       0.0028 |             -0.0038 |               0.0093 |                            5 |             0.6023 |                         1 |
| standard_cv   | conformer__standard_only__mean_std__none       | demographics_eeg_deep_vs_demographics                 |         1820 |       0.0025 |             -0.0034 |               0.0089 |                            3 |             0.6023 |                         1 |
| standard_cv   | eegnet__standard_only__mean_std__none          | demographics_eeg_deep_vs_demographics                 |         1820 |       0.0021 |             -0.0050 |               0.0096 |                            4 |             0.6023 |                         1 |
| standard_cv   | conformer__difference_wave__mean_std__none     | demographics_eeg_deep_vs_demographics                 |         1820 |       0.0019 |             -0.0046 |               0.0083 |                            3 |             0.6023 |                         1 |
| standard_cv   | conformer__target_only__mean_std__none         | demographics_eeg_deep_vs_demographics                 |         1820 |       0.0019 |             -0.0048 |               0.0090 |                            4 |             0.6023 |                         1 |
| standard_cv   | inceptiontime__condition_aware__mean_std__none | demographics_eeg_deep_vs_demographics                 |         1820 |       0.0017 |             -0.0048 |               0.0089 |                            3 |             0.6023 |                         1 |
| standard_cv   | conformer__condition_aware__mean_std__none     | demographics_eeg_deep_vs_demographics                 |         1820 |       0.0017 |             -0.0046 |               0.0081 |                            2 |             0.6023 |                         1 |
| standard_cv   | eegnet__condition_aware__mean_std__none        | demographics_eeg_deep_vs_demographics                 |         1820 |       0.0016 |             -0.0059 |               0.0084 |                            4 |             0.6023 |                         1 |
| standard_cv   | inceptiontime__difference_wave__mean_std__none | demographics_eeg_deep_vs_demographics                 |         1820 |       0.0009 |             -0.0053 |               0.0069 |                            4 |             0.6023 |                         1 |
| standard_cv   | inceptiontime__target_only__mean_std__none     | demographics_eeg_deep_vs_demographics                 |         1820 |       0.0007 |             -0.0053 |               0.0071 |                            3 |             0.6023 |                         1 |
| standard_cv   | eegnet__difference_wave__mean_std__none        | demographics_eeg_deep_vs_demographics                 |         1820 |       0.0007 |             -0.0064 |               0.0074 |                            1 |             0.6023 |                         1 |
| group_cv      | eegnet__condition_aware__mean_std__none        | demographics_eeg_deep_vs_demographics_eeg_traditional |         1820 |       0.0024 |             -0.0042 |               0.0090 |                            3 |             0.5854 |                         1 |
| group_cv      | eegnet__condition_aware__attention__none       | demographics_eeg_deep_vs_demographics_eeg_traditional |         1820 |       0.0021 |             -0.0038 |               0.0083 |                            3 |             0.5854 |                         1 |
| group_cv      | eegnet__condition_aware__mean_std__robust_z    | demographics_eeg_deep_vs_demographics_eeg_traditional |         1820 |       0.0009 |             -0.0048 |               0.0066 |                            3 |             0.5854 |                         1 |
| group_cv      | eegnet__standard_only__mean_std__none          | demographics_eeg_deep_vs_demographics_eeg_traditional |         1820 |      -0.0000 |             -0.0052 |               0.0053 |                            2 |             0.5854 |                         1 |
| group_cv      | eegnet__target_only__mean_std__none            | demographics_eeg_deep_vs_demographics_eeg_traditional |         1820 |      -0.0001 |             -0.0052 |               0.0049 |                            3 |             0.5854 |                         1 |
| group_cv      | eegnet__difference_wave__mean_std__none        | demographics_eeg_deep_vs_demographics_eeg_traditional |         1820 |      -0.0005 |             -0.0071 |               0.0057 |                            2 |             0.5854 |                         1 |
| group_cv      | inceptiontime__target_only__mean_std__none     | demographics_eeg_deep_vs_demographics_eeg_traditional |         1820 |      -0.0006 |             -0.0059 |               0.0056 |                            4 |             0.5854 |                         1 |
| group_cv      | inceptiontime__difference_wave__mean_std__none | demographics_eeg_deep_vs_demographics_eeg_traditional |         1820 |      -0.0008 |             -0.0073 |               0.0045 |                            1 |             0.5854 |                         1 |
| group_cv      | conformer__difference_wave__mean_std__none     | demographics_eeg_deep_vs_demographics_eeg_traditional |         1820 |      -0.0011 |             -0.0073 |               0.0049 |                            3 |             0.5854 |                         1 |
| group_cv      | inceptiontime__condition_aware__mean_std__none | demographics_eeg_deep_vs_demographics_eeg_traditional |         1820 |      -0.0013 |             -0.0064 |               0.0043 |                            3 |             0.5854 |                         1 |
| group_cv      | inceptiontime__standard_only__mean_std__none   | demographics_eeg_deep_vs_demographics_eeg_traditional |         1820 |      -0.0015 |             -0.0068 |               0.0045 |                            2 |             0.5854 |                         1 |
| group_cv      | conformer__standard_only__mean_std__none       | demographics_eeg_deep_vs_demographics_eeg_traditional |         1820 |      -0.0015 |             -0.0072 |               0.0040 |                            3 |             0.5854 |                         1 |
| group_cv      | conformer__target_only__mean_std__none         | demographics_eeg_deep_vs_demographics_eeg_traditional |         1820 |      -0.0020 |             -0.0077 |               0.0031 |                            2 |             0.5854 |                         1 |
| group_cv      | conformer__condition_aware__mean_std__none     | demographics_eeg_deep_vs_demographics_eeg_traditional |         1820 |      -0.0023 |             -0.0076 |               0.0031 |                            2 |             0.5854 |                         1 |
| standard_cv   | eegnet__condition_aware__attention__none       | demographics_eeg_deep_vs_demographics_eeg_traditional |         1820 |       0.0033 |             -0.0027 |               0.0096 |                            4 |             0.6034 |                         1 |
| standard_cv   | eegnet__condition_aware__mean_std__robust_z    | demographics_eeg_deep_vs_demographics_eeg_traditional |         1820 |       0.0027 |             -0.0036 |               0.0089 |                            4 |             0.6034 |                         1 |
| standard_cv   | eegnet__target_only__mean_std__none            | demographics_eeg_deep_vs_demographics_eeg_traditional |         1820 |       0.0017 |             -0.0042 |               0.0075 |                            3 |             0.6034 |                         1 |
| standard_cv   | inceptiontime__standard_only__mean_std__none   | demographics_eeg_deep_vs_demographics_eeg_traditional |         1820 |       0.0016 |             -0.0043 |               0.0076 |                            4 |             0.6034 |                         1 |
| standard_cv   | conformer__standard_only__mean_std__none       | demographics_eeg_deep_vs_demographics_eeg_traditional |         1820 |       0.0013 |             -0.0046 |               0.0075 |                            4 |             0.6034 |                         1 |
| standard_cv   | eegnet__standard_only__mean_std__none          | demographics_eeg_deep_vs_demographics_eeg_traditional |         1820 |       0.0009 |             -0.0047 |               0.0068 |                            3 |             0.6034 |                         1 |
| standard_cv   | conformer__difference_wave__mean_std__none     | demographics_eeg_deep_vs_demographics_eeg_traditional |         1820 |       0.0008 |             -0.0059 |               0.0078 |                            4 |             0.6034 |                         1 |
| standard_cv   | conformer__target_only__mean_std__none         | demographics_eeg_deep_vs_demographics_eeg_traditional |         1820 |       0.0007 |             -0.0050 |               0.0065 |                            3 |             0.6034 |                         1 |
| standard_cv   | inceptiontime__condition_aware__mean_std__none | demographics_eeg_deep_vs_demographics_eeg_traditional |         1820 |       0.0006 |             -0.0056 |               0.0069 |                            3 |             0.6034 |                         1 |
| standard_cv   | conformer__condition_aware__mean_std__none     | demographics_eeg_deep_vs_demographics_eeg_traditional |         1820 |       0.0005 |             -0.0051 |               0.0066 |                            3 |             0.6034 |                         1 |
| standard_cv   | eegnet__condition_aware__mean_std__none        | demographics_eeg_deep_vs_demographics_eeg_traditional |         1820 |       0.0005 |             -0.0052 |               0.0063 |                            4 |             0.6034 |                         1 |
| standard_cv   | inceptiontime__difference_wave__mean_std__none | demographics_eeg_deep_vs_demographics_eeg_traditional |         1820 |      -0.0003 |             -0.0066 |               0.0060 |                            3 |             0.6034 |                         1 |
| standard_cv   | inceptiontime__target_only__mean_std__none     | demographics_eeg_deep_vs_demographics_eeg_traditional |         1820 |      -0.0005 |             -0.0063 |               0.0056 |                            3 |             0.6034 |                         1 |
| standard_cv   | eegnet__difference_wave__mean_std__none        | demographics_eeg_deep_vs_demographics_eeg_traditional |         1820 |      -0.0005 |             -0.0064 |               0.0061 |                            4 |             0.6034 |                         1 |
| group_cv      | conformer__condition_aware__mean_std__none     | demographics_eeg_traditional_vs_demographics          |         1820 |      -0.0056 |             -0.0165 |               0.0065 |                            2 |             0.5909 |                         1 |
| group_cv      | conformer__difference_wave__mean_std__none     | demographics_eeg_traditional_vs_demographics          |         1820 |      -0.0056 |             -0.0170 |               0.0063 |                            2 |             0.5909 |                         1 |
| group_cv      | conformer__standard_only__mean_std__none       | demographics_eeg_traditional_vs_demographics          |         1820 |      -0.0056 |             -0.0175 |               0.0065 |                            2 |             0.5909 |                         1 |
| group_cv      | conformer__target_only__mean_std__none         | demographics_eeg_traditional_vs_demographics          |         1820 |      -0.0056 |             -0.0175 |               0.0061 |                            2 |             0.5909 |                         1 |
| group_cv      | eegnet__condition_aware__attention__none       | demographics_eeg_traditional_vs_demographics          |         1820 |      -0.0056 |             -0.0171 |               0.0057 |                            2 |             0.5909 |                         1 |
| group_cv      | eegnet__condition_aware__mean_std__none        | demographics_eeg_traditional_vs_demographics          |         1820 |      -0.0056 |             -0.0185 |               0.0060 |                            2 |             0.5909 |                         1 |
| group_cv      | eegnet__condition_aware__mean_std__robust_z    | demographics_eeg_traditional_vs_demographics          |         1820 |      -0.0056 |             -0.0170 |               0.0057 |                            2 |             0.5909 |                         1 |
| group_cv      | eegnet__difference_wave__mean_std__none        | demographics_eeg_traditional_vs_demographics          |         1820 |      -0.0056 |             -0.0177 |               0.0059 |                            2 |             0.5909 |                         1 |
| group_cv      | eegnet__standard_only__mean_std__none          | demographics_eeg_traditional_vs_demographics          |         1820 |      -0.0056 |             -0.0181 |               0.0061 |                            2 |             0.5909 |                         1 |
| group_cv      | eegnet__target_only__mean_std__none            | demographics_eeg_traditional_vs_demographics          |         1820 |      -0.0056 |             -0.0176 |               0.0057 |                            2 |             0.5909 |                         1 |
| group_cv      | inceptiontime__condition_aware__mean_std__none | demographics_eeg_traditional_vs_demographics          |         1820 |      -0.0056 |             -0.0167 |               0.0061 |                            2 |             0.5909 |                         1 |
| group_cv      | inceptiontime__difference_wave__mean_std__none | demographics_eeg_traditional_vs_demographics          |         1820 |      -0.0056 |             -0.0180 |               0.0056 |                            2 |             0.5909 |                         1 |
| group_cv      | inceptiontime__standard_only__mean_std__none   | demographics_eeg_traditional_vs_demographics          |         1820 |      -0.0056 |             -0.0175 |               0.0059 |                            2 |             0.5909 |                         1 |
| group_cv      | inceptiontime__target_only__mean_std__none     | demographics_eeg_traditional_vs_demographics          |         1820 |      -0.0056 |             -0.0170 |               0.0054 |                            2 |             0.5909 |                         1 |
| standard_cv   | conformer__condition_aware__mean_std__none     | demographics_eeg_traditional_vs_demographics          |         1820 |       0.0012 |             -0.0072 |               0.0097 |                            1 |             0.6023 |                         1 |
| standard_cv   | conformer__difference_wave__mean_std__none     | demographics_eeg_traditional_vs_demographics          |         1820 |       0.0012 |             -0.0075 |               0.0105 |                            1 |             0.6023 |                         1 |
| standard_cv   | conformer__standard_only__mean_std__none       | demographics_eeg_traditional_vs_demographics          |         1820 |       0.0012 |             -0.0069 |               0.0095 |                            1 |             0.6023 |                         1 |
| standard_cv   | conformer__target_only__mean_std__none         | demographics_eeg_traditional_vs_demographics          |         1820 |       0.0012 |             -0.0074 |               0.0094 |                            1 |             0.6023 |                         1 |
| standard_cv   | eegnet__condition_aware__attention__none       | demographics_eeg_traditional_vs_demographics          |         1820 |       0.0012 |             -0.0074 |               0.0097 |                            1 |             0.6023 |                         1 |
| standard_cv   | eegnet__condition_aware__mean_std__none        | demographics_eeg_traditional_vs_demographics          |         1820 |       0.0012 |             -0.0067 |               0.0093 |                            1 |             0.6023 |                         1 |
| standard_cv   | eegnet__condition_aware__mean_std__robust_z    | demographics_eeg_traditional_vs_demographics          |         1820 |       0.0012 |             -0.0072 |               0.0098 |                            1 |             0.6023 |                         1 |
| standard_cv   | eegnet__difference_wave__mean_std__none        | demographics_eeg_traditional_vs_demographics          |         1820 |       0.0012 |             -0.0082 |               0.0098 |                            1 |             0.6023 |                         1 |
| standard_cv   | eegnet__standard_only__mean_std__none          | demographics_eeg_traditional_vs_demographics          |         1820 |       0.0012 |             -0.0071 |               0.0097 |                            1 |             0.6023 |                         1 |
| standard_cv   | eegnet__target_only__mean_std__none            | demographics_eeg_traditional_vs_demographics          |         1820 |       0.0012 |             -0.0078 |               0.0098 |                            1 |             0.6023 |                         1 |
| standard_cv   | inceptiontime__condition_aware__mean_std__none | demographics_eeg_traditional_vs_demographics          |         1820 |       0.0012 |             -0.0079 |               0.0099 |                            1 |             0.6023 |                         1 |
| standard_cv   | inceptiontime__difference_wave__mean_std__none | demographics_eeg_traditional_vs_demographics          |         1820 |       0.0012 |             -0.0072 |               0.0091 |                            1 |             0.6023 |                         1 |
| standard_cv   | inceptiontime__standard_only__mean_std__none   | demographics_eeg_traditional_vs_demographics          |         1820 |       0.0012 |             -0.0074 |               0.0093 |                            1 |             0.6023 |                         1 |
| standard_cv   | inceptiontime__target_only__mean_std__none     | demographics_eeg_traditional_vs_demographics          |         1820 |       0.0012 |             -0.0065 |               0.0099 |                            1 |             0.6023 |                         1 |
| group_cv      | inceptiontime__target_only__mean_std__none     | eeg_deep_vs_demographics                              |         1820 |      -0.0329 |             -0.0691 |               0.0010 |                            0 |             0.5909 |                         1 |
| group_cv      | eegnet__condition_aware__mean_std__none        | eeg_deep_vs_demographics                              |         1820 |      -0.0434 |             -0.0734 |              -0.0089 |                            0 |             0.5909 |                         1 |
| group_cv      | inceptiontime__standard_only__mean_std__none   | eeg_deep_vs_demographics                              |         1820 |      -0.0498 |             -0.0858 |              -0.0160 |                            0 |             0.5909 |                         1 |
| group_cv      | eegnet__condition_aware__attention__none       | eeg_deep_vs_demographics                              |         1820 |      -0.0527 |             -0.0894 |              -0.0170 |                            0 |             0.5909 |                         1 |
| group_cv      | conformer__target_only__mean_std__none         | eeg_deep_vs_demographics                              |         1820 |      -0.0546 |             -0.0941 |              -0.0159 |                            0 |             0.5909 |                         1 |
| group_cv      | eegnet__target_only__mean_std__none            | eeg_deep_vs_demographics                              |         1820 |      -0.0557 |             -0.0914 |              -0.0198 |                            0 |             0.5909 |                         1 |

Showing 90 of 140 rows.

## Pooled AUROC By Feature Set

| cv_protocol   | model                                          | feature_set                  |   n_subjects |   auroc |   auprc |
|:--------------|:-----------------------------------------------|:-----------------------------|-------------:|--------:|--------:|
| group_cv      | conformer__condition_aware__mean_std__none     | demographics                 |         1820 |  0.5909 |  0.4124 |
| group_cv      | conformer__condition_aware__mean_std__none     | demographics_eeg_deep        |         1820 |  0.5831 |  0.4125 |
| group_cv      | conformer__condition_aware__mean_std__none     | demographics_eeg_traditional |         1820 |  0.5854 |  0.4121 |
| group_cv      | conformer__condition_aware__mean_std__none     | eeg_deep                     |         1820 |  0.4866 |  0.3227 |
| group_cv      | conformer__condition_aware__mean_std__none     | eeg_traditional              |         1820 |  0.4933 |  0.3277 |
| group_cv      | conformer__difference_wave__mean_std__none     | demographics                 |         1820 |  0.5909 |  0.4124 |
| group_cv      | conformer__difference_wave__mean_std__none     | demographics_eeg_deep        |         1820 |  0.5843 |  0.4088 |
| group_cv      | conformer__difference_wave__mean_std__none     | demographics_eeg_traditional |         1820 |  0.5854 |  0.4121 |
| group_cv      | conformer__difference_wave__mean_std__none     | eeg_deep                     |         1820 |  0.4825 |  0.3311 |
| group_cv      | conformer__difference_wave__mean_std__none     | eeg_traditional              |         1820 |  0.4933 |  0.3277 |
| group_cv      | conformer__standard_only__mean_std__none       | demographics                 |         1820 |  0.5909 |  0.4124 |
| group_cv      | conformer__standard_only__mean_std__none       | demographics_eeg_deep        |         1820 |  0.5838 |  0.4106 |
| group_cv      | conformer__standard_only__mean_std__none       | demographics_eeg_traditional |         1820 |  0.5854 |  0.4121 |
| group_cv      | conformer__standard_only__mean_std__none       | eeg_deep                     |         1820 |  0.4982 |  0.3356 |
| group_cv      | conformer__standard_only__mean_std__none       | eeg_traditional              |         1820 |  0.4933 |  0.3277 |
| group_cv      | conformer__target_only__mean_std__none         | demographics                 |         1820 |  0.5909 |  0.4124 |
| group_cv      | conformer__target_only__mean_std__none         | demographics_eeg_deep        |         1820 |  0.5833 |  0.4136 |
| group_cv      | conformer__target_only__mean_std__none         | demographics_eeg_traditional |         1820 |  0.5854 |  0.4121 |
| group_cv      | conformer__target_only__mean_std__none         | eeg_deep                     |         1820 |  0.5363 |  0.3501 |
| group_cv      | conformer__target_only__mean_std__none         | eeg_traditional              |         1820 |  0.4933 |  0.3277 |
| group_cv      | eegnet__condition_aware__attention__none       | demographics                 |         1820 |  0.5909 |  0.4124 |
| group_cv      | eegnet__condition_aware__attention__none       | demographics_eeg_deep        |         1820 |  0.5874 |  0.4168 |
| group_cv      | eegnet__condition_aware__attention__none       | demographics_eeg_traditional |         1820 |  0.5854 |  0.4121 |
| group_cv      | eegnet__condition_aware__attention__none       | eeg_deep                     |         1820 |  0.5382 |  0.3756 |
| group_cv      | eegnet__condition_aware__attention__none       | eeg_traditional              |         1820 |  0.4933 |  0.3277 |
| group_cv      | eegnet__condition_aware__mean_std__none        | demographics                 |         1820 |  0.5909 |  0.4124 |
| group_cv      | eegnet__condition_aware__mean_std__none        | demographics_eeg_deep        |         1820 |  0.5878 |  0.4196 |
| group_cv      | eegnet__condition_aware__mean_std__none        | demographics_eeg_traditional |         1820 |  0.5854 |  0.4121 |
| group_cv      | eegnet__condition_aware__mean_std__none        | eeg_deep                     |         1820 |  0.5475 |  0.3818 |
| group_cv      | eegnet__condition_aware__mean_std__none        | eeg_traditional              |         1820 |  0.4933 |  0.3277 |
| group_cv      | eegnet__condition_aware__mean_std__robust_z    | demographics                 |         1820 |  0.5909 |  0.4124 |
| group_cv      | eegnet__condition_aware__mean_std__robust_z    | demographics_eeg_deep        |         1820 |  0.5863 |  0.4094 |
| group_cv      | eegnet__condition_aware__mean_std__robust_z    | demographics_eeg_traditional |         1820 |  0.5854 |  0.4121 |
| group_cv      | eegnet__condition_aware__mean_std__robust_z    | eeg_deep                     |         1820 |  0.5301 |  0.3691 |
| group_cv      | eegnet__condition_aware__mean_std__robust_z    | eeg_traditional              |         1820 |  0.4933 |  0.3277 |
| group_cv      | eegnet__difference_wave__mean_std__none        | demographics                 |         1820 |  0.5909 |  0.4124 |
| group_cv      | eegnet__difference_wave__mean_std__none        | demographics_eeg_deep        |         1820 |  0.5848 |  0.4108 |
| group_cv      | eegnet__difference_wave__mean_std__none        | demographics_eeg_traditional |         1820 |  0.5854 |  0.4121 |
| group_cv      | eegnet__difference_wave__mean_std__none        | eeg_deep                     |         1820 |  0.5122 |  0.3419 |
| group_cv      | eegnet__difference_wave__mean_std__none        | eeg_traditional              |         1820 |  0.4933 |  0.3277 |
| group_cv      | eegnet__standard_only__mean_std__none          | demographics                 |         1820 |  0.5909 |  0.4124 |
| group_cv      | eegnet__standard_only__mean_std__none          | demographics_eeg_deep        |         1820 |  0.5854 |  0.4152 |
| group_cv      | eegnet__standard_only__mean_std__none          | demographics_eeg_traditional |         1820 |  0.5854 |  0.4121 |
| group_cv      | eegnet__standard_only__mean_std__none          | eeg_deep                     |         1820 |  0.5156 |  0.3445 |
| group_cv      | eegnet__standard_only__mean_std__none          | eeg_traditional              |         1820 |  0.4933 |  0.3277 |
| group_cv      | eegnet__target_only__mean_std__none            | demographics                 |         1820 |  0.5909 |  0.4124 |
| group_cv      | eegnet__target_only__mean_std__none            | demographics_eeg_deep        |         1820 |  0.5852 |  0.4160 |
| group_cv      | eegnet__target_only__mean_std__none            | demographics_eeg_traditional |         1820 |  0.5854 |  0.4121 |
| group_cv      | eegnet__target_only__mean_std__none            | eeg_deep                     |         1820 |  0.5353 |  0.3624 |
| group_cv      | eegnet__target_only__mean_std__none            | eeg_traditional              |         1820 |  0.4933 |  0.3277 |
| group_cv      | inceptiontime__condition_aware__mean_std__none | demographics                 |         1820 |  0.5909 |  0.4124 |
| group_cv      | inceptiontime__condition_aware__mean_std__none | demographics_eeg_deep        |         1820 |  0.5841 |  0.4162 |
| group_cv      | inceptiontime__condition_aware__mean_std__none | demographics_eeg_traditional |         1820 |  0.5854 |  0.4121 |
| group_cv      | inceptiontime__condition_aware__mean_std__none | eeg_deep                     |         1820 |  0.4949 |  0.3295 |
| group_cv      | inceptiontime__condition_aware__mean_std__none | eeg_traditional              |         1820 |  0.4933 |  0.3277 |
| group_cv      | inceptiontime__difference_wave__mean_std__none | demographics                 |         1820 |  0.5909 |  0.4124 |
| group_cv      | inceptiontime__difference_wave__mean_std__none | demographics_eeg_deep        |         1820 |  0.5846 |  0.4071 |
| group_cv      | inceptiontime__difference_wave__mean_std__none | demographics_eeg_traditional |         1820 |  0.5854 |  0.4121 |
| group_cv      | inceptiontime__difference_wave__mean_std__none | eeg_deep                     |         1820 |  0.4835 |  0.3165 |
| group_cv      | inceptiontime__difference_wave__mean_std__none | eeg_traditional              |         1820 |  0.4933 |  0.3277 |
| group_cv      | inceptiontime__standard_only__mean_std__none   | demographics                 |         1820 |  0.5909 |  0.4124 |
| group_cv      | inceptiontime__standard_only__mean_std__none   | demographics_eeg_deep        |         1820 |  0.5839 |  0.4058 |
| group_cv      | inceptiontime__standard_only__mean_std__none   | demographics_eeg_traditional |         1820 |  0.5854 |  0.4121 |
| group_cv      | inceptiontime__standard_only__mean_std__none   | eeg_deep                     |         1820 |  0.5411 |  0.3645 |
| group_cv      | inceptiontime__standard_only__mean_std__none   | eeg_traditional              |         1820 |  0.4933 |  0.3277 |
| group_cv      | inceptiontime__target_only__mean_std__none     | demographics                 |         1820 |  0.5909 |  0.4124 |
| group_cv      | inceptiontime__target_only__mean_std__none     | demographics_eeg_deep        |         1820 |  0.5848 |  0.4144 |
| group_cv      | inceptiontime__target_only__mean_std__none     | demographics_eeg_traditional |         1820 |  0.5854 |  0.4121 |
| group_cv      | inceptiontime__target_only__mean_std__none     | eeg_deep                     |         1820 |  0.5580 |  0.3717 |
| group_cv      | inceptiontime__target_only__mean_std__none     | eeg_traditional              |         1820 |  0.4933 |  0.3277 |
| standard_cv   | conformer__condition_aware__mean_std__none     | demographics                 |         1820 |  0.6023 |  0.4158 |
| standard_cv   | conformer__condition_aware__mean_std__none     | demographics_eeg_deep        |         1820 |  0.6039 |  0.4216 |
| standard_cv   | conformer__condition_aware__mean_std__none     | demographics_eeg_traditional |         1820 |  0.6034 |  0.4137 |
| standard_cv   | conformer__condition_aware__mean_std__none     | eeg_deep                     |         1820 |  0.5196 |  0.3570 |
| standard_cv   | conformer__condition_aware__mean_std__none     | eeg_traditional              |         1820 |  0.5191 |  0.3483 |
| standard_cv   | conformer__difference_wave__mean_std__none     | demographics                 |         1820 |  0.6023 |  0.4158 |
| standard_cv   | conformer__difference_wave__mean_std__none     | demographics_eeg_deep        |         1820 |  0.6042 |  0.4172 |
| standard_cv   | conformer__difference_wave__mean_std__none     | demographics_eeg_traditional |         1820 |  0.6034 |  0.4137 |
| standard_cv   | conformer__difference_wave__mean_std__none     | eeg_deep                     |         1820 |  0.5017 |  0.3363 |
| standard_cv   | conformer__difference_wave__mean_std__none     | eeg_traditional              |         1820 |  0.5191 |  0.3483 |
| standard_cv   | conformer__standard_only__mean_std__none       | demographics                 |         1820 |  0.6023 |  0.4158 |
| standard_cv   | conformer__standard_only__mean_std__none       | demographics_eeg_deep        |         1820 |  0.6048 |  0.4209 |
| standard_cv   | conformer__standard_only__mean_std__none       | demographics_eeg_traditional |         1820 |  0.6034 |  0.4137 |
| standard_cv   | conformer__standard_only__mean_std__none       | eeg_deep                     |         1820 |  0.5388 |  0.3666 |
| standard_cv   | conformer__standard_only__mean_std__none       | eeg_traditional              |         1820 |  0.5191 |  0.3483 |
| standard_cv   | conformer__target_only__mean_std__none         | demographics                 |         1820 |  0.6023 |  0.4158 |
| standard_cv   | conformer__target_only__mean_std__none         | demographics_eeg_deep        |         1820 |  0.6041 |  0.4223 |
| standard_cv   | conformer__target_only__mean_std__none         | demographics_eeg_traditional |         1820 |  0.6034 |  0.4137 |
| standard_cv   | conformer__target_only__mean_std__none         | eeg_deep                     |         1820 |  0.5223 |  0.3630 |
| standard_cv   | conformer__target_only__mean_std__none         | eeg_traditional              |         1820 |  0.5191 |  0.3483 |
| standard_cv   | eegnet__condition_aware__attention__none       | demographics                 |         1820 |  0.6023 |  0.4158 |
| standard_cv   | eegnet__condition_aware__attention__none       | demographics_eeg_deep        |         1820 |  0.6068 |  0.4245 |
| standard_cv   | eegnet__condition_aware__attention__none       | demographics_eeg_traditional |         1820 |  0.6034 |  0.4137 |
| standard_cv   | eegnet__condition_aware__attention__none       | eeg_deep                     |         1820 |  0.5451 |  0.3778 |
| standard_cv   | eegnet__condition_aware__attention__none       | eeg_traditional              |         1820 |  0.5191 |  0.3483 |
| standard_cv   | eegnet__condition_aware__mean_std__none        | demographics                 |         1820 |  0.6023 |  0.4158 |
| standard_cv   | eegnet__condition_aware__mean_std__none        | demographics_eeg_deep        |         1820 |  0.6039 |  0.4209 |
| standard_cv   | eegnet__condition_aware__mean_std__none        | demographics_eeg_traditional |         1820 |  0.6034 |  0.4137 |
| standard_cv   | eegnet__condition_aware__mean_std__none        | eeg_deep                     |         1820 |  0.5339 |  0.3717 |
| standard_cv   | eegnet__condition_aware__mean_std__none        | eeg_traditional              |         1820 |  0.5191 |  0.3483 |
| standard_cv   | eegnet__condition_aware__mean_std__robust_z    | demographics                 |         1820 |  0.6023 |  0.4158 |
| standard_cv   | eegnet__condition_aware__mean_std__robust_z    | demographics_eeg_deep        |         1820 |  0.6061 |  0.4212 |
| standard_cv   | eegnet__condition_aware__mean_std__robust_z    | demographics_eeg_traditional |         1820 |  0.6034 |  0.4137 |
| standard_cv   | eegnet__condition_aware__mean_std__robust_z    | eeg_deep                     |         1820 |  0.5423 |  0.3801 |
| standard_cv   | eegnet__condition_aware__mean_std__robust_z    | eeg_traditional              |         1820 |  0.5191 |  0.3483 |
| standard_cv   | eegnet__difference_wave__mean_std__none        | demographics                 |         1820 |  0.6023 |  0.4158 |
| standard_cv   | eegnet__difference_wave__mean_std__none        | demographics_eeg_deep        |         1820 |  0.6029 |  0.4196 |
| standard_cv   | eegnet__difference_wave__mean_std__none        | demographics_eeg_traditional |         1820 |  0.6034 |  0.4137 |
| standard_cv   | eegnet__difference_wave__mean_std__none        | eeg_deep                     |         1820 |  0.5228 |  0.3502 |
| standard_cv   | eegnet__difference_wave__mean_std__none        | eeg_traditional              |         1820 |  0.5191 |  0.3483 |
| standard_cv   | eegnet__standard_only__mean_std__none          | demographics                 |         1820 |  0.6023 |  0.4158 |
| standard_cv   | eegnet__standard_only__mean_std__none          | demographics_eeg_deep        |         1820 |  0.6043 |  0.4210 |
| standard_cv   | eegnet__standard_only__mean_std__none          | demographics_eeg_traditional |         1820 |  0.6034 |  0.4137 |
| standard_cv   | eegnet__standard_only__mean_std__none          | eeg_deep                     |         1820 |  0.5327 |  0.3630 |
| standard_cv   | eegnet__standard_only__mean_std__none          | eeg_traditional              |         1820 |  0.5191 |  0.3483 |
| standard_cv   | eegnet__target_only__mean_std__none            | demographics                 |         1820 |  0.6023 |  0.4158 |
| standard_cv   | eegnet__target_only__mean_std__none            | demographics_eeg_deep        |         1820 |  0.6051 |  0.4223 |
| standard_cv   | eegnet__target_only__mean_std__none            | demographics_eeg_traditional |         1820 |  0.6034 |  0.4137 |
| standard_cv   | eegnet__target_only__mean_std__none            | eeg_deep                     |         1820 |  0.5370 |  0.3635 |
| standard_cv   | eegnet__target_only__mean_std__none            | eeg_traditional              |         1820 |  0.5191 |  0.3483 |

Showing 120 of 140 rows.

## Between-Seed Spread

The paired bootstrap resamples subjects and is blind to the instability of the fit.

| cv_protocol   | model                                          | feature_set                  |   n_seeds |   auroc_seed_mean |   auroc_seed_std |   auroc_seed_min |   auroc_seed_max |
|:--------------|:-----------------------------------------------|:-----------------------------|----------:|------------------:|-----------------:|-----------------:|-----------------:|
| group_cv      | conformer__condition_aware__mean_std__none     | demographics                 |         3 |            0.5800 |           0.0220 |           0.5574 |           0.6013 |
| group_cv      | conformer__difference_wave__mean_std__none     | demographics                 |         3 |            0.5800 |           0.0220 |           0.5574 |           0.6013 |
| group_cv      | conformer__standard_only__mean_std__none       | demographics                 |         3 |            0.5800 |           0.0220 |           0.5574 |           0.6013 |
| group_cv      | conformer__target_only__mean_std__none         | demographics                 |         3 |            0.5800 |           0.0220 |           0.5574 |           0.6013 |
| group_cv      | eegnet__condition_aware__attention__none       | demographics                 |         3 |            0.5800 |           0.0220 |           0.5574 |           0.6013 |
| group_cv      | eegnet__condition_aware__mean_std__none        | demographics                 |         3 |            0.5800 |           0.0220 |           0.5574 |           0.6013 |
| group_cv      | eegnet__condition_aware__mean_std__robust_z    | demographics                 |         3 |            0.5800 |           0.0220 |           0.5574 |           0.6013 |
| group_cv      | eegnet__difference_wave__mean_std__none        | demographics                 |         3 |            0.5800 |           0.0220 |           0.5574 |           0.6013 |
| group_cv      | eegnet__standard_only__mean_std__none          | demographics                 |         3 |            0.5800 |           0.0220 |           0.5574 |           0.6013 |
| group_cv      | eegnet__target_only__mean_std__none            | demographics                 |         3 |            0.5800 |           0.0220 |           0.5574 |           0.6013 |
| group_cv      | inceptiontime__condition_aware__mean_std__none | demographics                 |         3 |            0.5800 |           0.0220 |           0.5574 |           0.6013 |
| group_cv      | inceptiontime__difference_wave__mean_std__none | demographics                 |         3 |            0.5800 |           0.0220 |           0.5574 |           0.6013 |
| group_cv      | inceptiontime__standard_only__mean_std__none   | demographics                 |         3 |            0.5800 |           0.0220 |           0.5574 |           0.6013 |
| group_cv      | inceptiontime__target_only__mean_std__none     | demographics                 |         3 |            0.5800 |           0.0220 |           0.5574 |           0.6013 |
| standard_cv   | conformer__condition_aware__mean_std__none     | demographics                 |         3 |            0.5958 |           0.0086 |           0.5869 |           0.6040 |
| standard_cv   | conformer__difference_wave__mean_std__none     | demographics                 |         3 |            0.5958 |           0.0086 |           0.5869 |           0.6040 |
| standard_cv   | conformer__standard_only__mean_std__none       | demographics                 |         3 |            0.5958 |           0.0086 |           0.5869 |           0.6040 |
| standard_cv   | conformer__target_only__mean_std__none         | demographics                 |         3 |            0.5958 |           0.0086 |           0.5869 |           0.6040 |
| standard_cv   | eegnet__condition_aware__attention__none       | demographics                 |         3 |            0.5958 |           0.0086 |           0.5869 |           0.6040 |
| standard_cv   | eegnet__condition_aware__mean_std__none        | demographics                 |         3 |            0.5958 |           0.0086 |           0.5869 |           0.6040 |
| standard_cv   | eegnet__condition_aware__mean_std__robust_z    | demographics                 |         3 |            0.5958 |           0.0086 |           0.5869 |           0.6040 |
| standard_cv   | eegnet__difference_wave__mean_std__none        | demographics                 |         3 |            0.5958 |           0.0086 |           0.5869 |           0.6040 |
| standard_cv   | eegnet__standard_only__mean_std__none          | demographics                 |         3 |            0.5958 |           0.0086 |           0.5869 |           0.6040 |
| standard_cv   | eegnet__target_only__mean_std__none            | demographics                 |         3 |            0.5958 |           0.0086 |           0.5869 |           0.6040 |
| standard_cv   | inceptiontime__condition_aware__mean_std__none | demographics                 |         3 |            0.5958 |           0.0086 |           0.5869 |           0.6040 |
| standard_cv   | inceptiontime__difference_wave__mean_std__none | demographics                 |         3 |            0.5958 |           0.0086 |           0.5869 |           0.6040 |
| standard_cv   | inceptiontime__standard_only__mean_std__none   | demographics                 |         3 |            0.5958 |           0.0086 |           0.5869 |           0.6040 |
| standard_cv   | inceptiontime__target_only__mean_std__none     | demographics                 |         3 |            0.5958 |           0.0086 |           0.5869 |           0.6040 |
| group_cv      | conformer__condition_aware__mean_std__none     | demographics_eeg_deep        |         3 |            0.5815 |           0.0038 |           0.5778 |           0.5853 |
| group_cv      | conformer__difference_wave__mean_std__none     | demographics_eeg_deep        |         3 |            0.5832 |           0.0049 |           0.5775 |           0.5867 |
| group_cv      | conformer__standard_only__mean_std__none       | demographics_eeg_deep        |         3 |            0.5810 |           0.0013 |           0.5795 |           0.5821 |
| group_cv      | conformer__target_only__mean_std__none         | demographics_eeg_deep        |         3 |            0.5820 |           0.0039 |           0.5778 |           0.5856 |
| group_cv      | eegnet__condition_aware__attention__none       | demographics_eeg_deep        |         3 |            0.5847 |           0.0030 |           0.5826 |           0.5881 |
| group_cv      | eegnet__condition_aware__mean_std__none        | demographics_eeg_deep        |         3 |            0.5850 |           0.0033 |           0.5812 |           0.5873 |
| group_cv      | eegnet__condition_aware__mean_std__robust_z    | demographics_eeg_deep        |         3 |            0.5837 |           0.0037 |           0.5794 |           0.5864 |
| group_cv      | eegnet__difference_wave__mean_std__none        | demographics_eeg_deep        |         3 |            0.5829 |           0.0029 |           0.5801 |           0.5859 |
| group_cv      | eegnet__standard_only__mean_std__none          | demographics_eeg_deep        |         3 |            0.5832 |           0.0037 |           0.5796 |           0.5870 |
| group_cv      | eegnet__target_only__mean_std__none            | demographics_eeg_deep        |         3 |            0.5833 |           0.0037 |           0.5795 |           0.5868 |
| group_cv      | inceptiontime__condition_aware__mean_std__none | demographics_eeg_deep        |         3 |            0.5819 |           0.0043 |           0.5772 |           0.5857 |
| group_cv      | inceptiontime__difference_wave__mean_std__none | demographics_eeg_deep        |         3 |            0.5823 |           0.0040 |           0.5777 |           0.5851 |
| group_cv      | inceptiontime__standard_only__mean_std__none   | demographics_eeg_deep        |         3 |            0.5814 |           0.0030 |           0.5780 |           0.5837 |
| group_cv      | inceptiontime__target_only__mean_std__none     | demographics_eeg_deep        |         3 |            0.5815 |           0.0029 |           0.5782 |           0.5835 |
| standard_cv   | conformer__condition_aware__mean_std__none     | demographics_eeg_deep        |         3 |            0.6007 |           0.0036 |           0.5972 |           0.6044 |
| standard_cv   | conformer__difference_wave__mean_std__none     | demographics_eeg_deep        |         3 |            0.6015 |           0.0039 |           0.5973 |           0.6050 |
| standard_cv   | conformer__standard_only__mean_std__none       | demographics_eeg_deep        |         3 |            0.6014 |           0.0042 |           0.5970 |           0.6053 |
| standard_cv   | conformer__target_only__mean_std__none         | demographics_eeg_deep        |         3 |            0.6014 |           0.0031 |           0.5980 |           0.6041 |
| standard_cv   | eegnet__condition_aware__attention__none       | demographics_eeg_deep        |         3 |            0.6043 |           0.0062 |           0.5988 |           0.6110 |
| standard_cv   | eegnet__condition_aware__mean_std__none        | demographics_eeg_deep        |         3 |            0.6014 |           0.0053 |           0.5967 |           0.6072 |
| standard_cv   | eegnet__condition_aware__mean_std__robust_z    | demographics_eeg_deep        |         3 |            0.6030 |           0.0053 |           0.5998 |           0.6091 |
| standard_cv   | eegnet__difference_wave__mean_std__none        | demographics_eeg_deep        |         3 |            0.6006 |           0.0043 |           0.5958 |           0.6042 |
| standard_cv   | eegnet__standard_only__mean_std__none          | demographics_eeg_deep        |         3 |            0.6015 |           0.0044 |           0.5968 |           0.6056 |
| standard_cv   | eegnet__target_only__mean_std__none            | demographics_eeg_deep        |         3 |            0.6020 |           0.0039 |           0.5981 |           0.6058 |
| standard_cv   | inceptiontime__condition_aware__mean_std__none | demographics_eeg_deep        |         3 |            0.6014 |           0.0048 |           0.5970 |           0.6066 |
| standard_cv   | inceptiontime__difference_wave__mean_std__none | demographics_eeg_deep        |         3 |            0.6008 |           0.0042 |           0.5965 |           0.6048 |
| standard_cv   | inceptiontime__standard_only__mean_std__none   | demographics_eeg_deep        |         3 |            0.6019 |           0.0025 |           0.5991 |           0.6039 |
| standard_cv   | inceptiontime__target_only__mean_std__none     | demographics_eeg_deep        |         3 |            0.6003 |           0.0039 |           0.5966 |           0.6044 |
| group_cv      | conformer__condition_aware__mean_std__none     | demographics_eeg_traditional |         3 |            0.5830 |           0.0044 |           0.5780 |           0.5861 |
| group_cv      | conformer__difference_wave__mean_std__none     | demographics_eeg_traditional |         3 |            0.5830 |           0.0044 |           0.5780 |           0.5861 |
| group_cv      | conformer__standard_only__mean_std__none       | demographics_eeg_traditional |         3 |            0.5830 |           0.0044 |           0.5780 |           0.5861 |
| group_cv      | conformer__target_only__mean_std__none         | demographics_eeg_traditional |         3 |            0.5830 |           0.0044 |           0.5780 |           0.5861 |
| group_cv      | eegnet__condition_aware__attention__none       | demographics_eeg_traditional |         3 |            0.5830 |           0.0044 |           0.5780 |           0.5861 |
| group_cv      | eegnet__condition_aware__mean_std__none        | demographics_eeg_traditional |         3 |            0.5830 |           0.0044 |           0.5780 |           0.5861 |
| group_cv      | eegnet__condition_aware__mean_std__robust_z    | demographics_eeg_traditional |         3 |            0.5830 |           0.0044 |           0.5780 |           0.5861 |
| group_cv      | eegnet__difference_wave__mean_std__none        | demographics_eeg_traditional |         3 |            0.5830 |           0.0044 |           0.5780 |           0.5861 |
| group_cv      | eegnet__standard_only__mean_std__none          | demographics_eeg_traditional |         3 |            0.5830 |           0.0044 |           0.5780 |           0.5861 |
| group_cv      | eegnet__target_only__mean_std__none            | demographics_eeg_traditional |         3 |            0.5830 |           0.0044 |           0.5780 |           0.5861 |
| group_cv      | inceptiontime__condition_aware__mean_std__none | demographics_eeg_traditional |         3 |            0.5830 |           0.0044 |           0.5780 |           0.5861 |
| group_cv      | inceptiontime__difference_wave__mean_std__none | demographics_eeg_traditional |         3 |            0.5830 |           0.0044 |           0.5780 |           0.5861 |
| group_cv      | inceptiontime__standard_only__mean_std__none   | demographics_eeg_traditional |         3 |            0.5830 |           0.0044 |           0.5780 |           0.5861 |
| group_cv      | inceptiontime__target_only__mean_std__none     | demographics_eeg_traditional |         3 |            0.5830 |           0.0044 |           0.5780 |           0.5861 |
| standard_cv   | conformer__condition_aware__mean_std__none     | demographics_eeg_traditional |         3 |            0.6007 |           0.0052 |           0.5976 |           0.6067 |
| standard_cv   | conformer__difference_wave__mean_std__none     | demographics_eeg_traditional |         3 |            0.6007 |           0.0052 |           0.5976 |           0.6067 |
| standard_cv   | conformer__standard_only__mean_std__none       | demographics_eeg_traditional |         3 |            0.6007 |           0.0052 |           0.5976 |           0.6067 |
| standard_cv   | conformer__target_only__mean_std__none         | demographics_eeg_traditional |         3 |            0.6007 |           0.0052 |           0.5976 |           0.6067 |
| standard_cv   | eegnet__condition_aware__attention__none       | demographics_eeg_traditional |         3 |            0.6007 |           0.0052 |           0.5976 |           0.6067 |
| standard_cv   | eegnet__condition_aware__mean_std__none        | demographics_eeg_traditional |         3 |            0.6007 |           0.0052 |           0.5976 |           0.6067 |
| standard_cv   | eegnet__condition_aware__mean_std__robust_z    | demographics_eeg_traditional |         3 |            0.6007 |           0.0052 |           0.5976 |           0.6067 |
| standard_cv   | eegnet__difference_wave__mean_std__none        | demographics_eeg_traditional |         3 |            0.6007 |           0.0052 |           0.5976 |           0.6067 |
| standard_cv   | eegnet__standard_only__mean_std__none          | demographics_eeg_traditional |         3 |            0.6007 |           0.0052 |           0.5976 |           0.6067 |
| standard_cv   | eegnet__target_only__mean_std__none            | demographics_eeg_traditional |         3 |            0.6007 |           0.0052 |           0.5976 |           0.6067 |
| standard_cv   | inceptiontime__condition_aware__mean_std__none | demographics_eeg_traditional |         3 |            0.6007 |           0.0052 |           0.5976 |           0.6067 |
| standard_cv   | inceptiontime__difference_wave__mean_std__none | demographics_eeg_traditional |         3 |            0.6007 |           0.0052 |           0.5976 |           0.6067 |
| standard_cv   | inceptiontime__standard_only__mean_std__none   | demographics_eeg_traditional |         3 |            0.6007 |           0.0052 |           0.5976 |           0.6067 |
| standard_cv   | inceptiontime__target_only__mean_std__none     | demographics_eeg_traditional |         3 |            0.6007 |           0.0052 |           0.5976 |           0.6067 |
| group_cv      | conformer__condition_aware__mean_std__none     | eeg_deep                     |         3 |            0.4870 |           0.0087 |           0.4799 |           0.4967 |
| group_cv      | conformer__difference_wave__mean_std__none     | eeg_deep                     |         3 |            0.4866 |           0.0058 |           0.4805 |           0.4919 |
| group_cv      | conformer__standard_only__mean_std__none       | eeg_deep                     |         3 |            0.4908 |           0.0444 |           0.4522 |           0.5393 |
| group_cv      | conformer__target_only__mean_std__none         | eeg_deep                     |         3 |            0.5252 |           0.0259 |           0.5092 |           0.5550 |
| group_cv      | eegnet__condition_aware__attention__none       | eeg_deep                     |         3 |            0.5330 |           0.0027 |           0.5299 |           0.5349 |
| group_cv      | eegnet__condition_aware__mean_std__none        | eeg_deep                     |         3 |            0.5443 |           0.0188 |           0.5234 |           0.5597 |

Showing 90 of 140 rows.
