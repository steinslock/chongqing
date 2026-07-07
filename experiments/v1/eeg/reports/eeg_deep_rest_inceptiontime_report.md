# Deep EEG Baseline: rest inceptiontime

- Task: `rest`
- Model: `inceptiontime`
- CV folds: 5
- Max epochs: 80; patience: 12
- Window cap per train subject per epoch: 24

## Overall OOF Metrics

| task   | model         | fold        |   n_subjects |   threshold |   auroc |   auprc |   balanced_accuracy |   sensitivity |   specificity |     f1 |   brier |   tn |   fp |   fn |   tp |
|:-------|:--------------|:------------|-------------:|------------:|--------:|--------:|--------------------:|--------------:|--------------:|-------:|--------:|-----:|-----:|-----:|-----:|
| rest   | inceptiontime | overall_oof |         1284 |      0.5025 |  0.5106 |  0.3460 |              0.4940 |        0.2694 |        0.7187 | 0.2972 |  0.3027 |  608 |  238 |  320 |  118 |
