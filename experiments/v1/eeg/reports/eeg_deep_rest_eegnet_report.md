# Deep EEG Baseline: rest eegnet

- Task: `rest`
- Model: `eegnet`
- CV folds: 5
- Max epochs: 80; patience: 12
- Window cap per train subject per epoch: 24

## Overall OOF Metrics

| task   | model   | fold        |   n_subjects |   threshold |   auroc |   auprc |   balanced_accuracy |   sensitivity |   specificity |     f1 |   brier |   tn |   fp |   fn |   tp |
|:-------|:--------|:------------|-------------:|------------:|--------:|--------:|--------------------:|--------------:|--------------:|-------:|--------:|-----:|-----:|-----:|-----:|
| rest   | eegnet  | overall_oof |         1284 |      0.2380 |  0.5027 |  0.3485 |              0.4974 |        0.4132 |        0.5816 | 0.3720 |  0.2621 |  492 |  354 |  257 |  181 |
