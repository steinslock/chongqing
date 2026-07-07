# Deep EEG Baseline: oddball inceptiontime

- Task: `oddball`
- Model: `inceptiontime`
- CV folds: 5
- Max epochs: 80; patience: 12
- Window cap per train subject per epoch: 24

## Overall OOF Metrics

| task    | model         | fold        |   n_subjects |   threshold |   auroc |   auprc |   balanced_accuracy |   sensitivity |   specificity |     f1 |   brier |   tn |   fp |   fn |   tp |
|:--------|:--------------|:------------|-------------:|------------:|--------:|--------:|--------------------:|--------------:|--------------:|-------:|--------:|-----:|-----:|-----:|-----:|
| oddball | inceptiontime | overall_oof |         2285 |      0.8536 |  0.5148 |  0.3458 |              0.5000 |        0.0091 |        0.9908 | 0.0178 |  0.2597 | 1505 |   14 |  759 |    7 |
