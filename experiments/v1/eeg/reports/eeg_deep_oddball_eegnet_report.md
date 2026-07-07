# Deep EEG Baseline: oddball eegnet

- Task: `oddball`
- Model: `eegnet`
- CV folds: 5
- Max epochs: 80; patience: 12
- Window cap per train subject per epoch: 24

## Overall OOF Metrics

| task    | model   | fold        |   n_subjects |   threshold |   auroc |   auprc |   balanced_accuracy |   sensitivity |   specificity |     f1 |   brier |   tn |   fp |   fn |   tp |
|:--------|:--------|:------------|-------------:|------------:|--------:|--------:|--------------------:|--------------:|--------------:|-------:|--------:|-----:|-----:|-----:|-----:|
| oddball | eegnet  | overall_oof |         2285 |      0.4860 |  0.5281 |  0.3559 |              0.5212 |        0.5914 |        0.4510 | 0.4413 |  0.2539 |  685 |  834 |  313 |  453 |
