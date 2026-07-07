# Deep EEG Baseline: 1back inceptiontime

- Task: `1back`
- Model: `inceptiontime`
- CV folds: 5
- Max epochs: 80; patience: 12
- Window cap per train subject per epoch: 24

## Overall OOF Metrics

| task   | model         | fold        |   n_subjects |   threshold |   auroc |   auprc |   balanced_accuracy |   sensitivity |   specificity |     f1 |   brier |   tn |   fp |   fn |   tp |
|:-------|:--------------|:------------|-------------:|------------:|--------:|--------:|--------------------:|--------------:|--------------:|-------:|--------:|-----:|-----:|-----:|-----:|
| 1back  | inceptiontime | overall_oof |         1694 |      0.7379 |  0.5265 |  0.3311 |              0.5077 |        0.0537 |        0.9616 | 0.0943 |  0.2540 | 1128 |   45 |  493 |   28 |
