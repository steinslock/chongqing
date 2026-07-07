# Deep EEG Baseline: 1back eegnet

- Task: `1back`
- Model: `eegnet`
- CV folds: 5
- Max epochs: 80; patience: 12
- Window cap per train subject per epoch: 24

## Overall OOF Metrics

| task   | model   | fold        |   n_subjects |   threshold |   auroc |   auprc |   balanced_accuracy |   sensitivity |   specificity |     f1 |   brier |   tn |   fp |   fn |   tp |
|:-------|:--------|:------------|-------------:|------------:|--------:|--------:|--------------------:|--------------:|--------------:|-------:|--------:|-----:|-----:|-----:|-----:|
| 1back  | eegnet  | overall_oof |         1694 |      0.3366 |  0.5337 |  0.3396 |              0.5197 |        0.5662 |        0.4731 | 0.4114 |  0.2314 |  555 |  618 |  226 |  295 |
