# EEG v1 Code Audit

## Main Findings

- The v1 traditional Rest baseline and deep EEG scripts do not inherit `artifacts/splits/subject_splits_v1.csv`; they generate their own `StratifiedKFold` splits and therefore are not directly comparable with the fixed-split baseline.
- The deep training script defaults to `--device cuda:0`, uses `WeightedRandomSampler` and `BCEWithLogitsLoss(pos_weight)` together, and can double-compensate class imbalance.
- Early stopping/checkpoint selection is based on training loss rather than an independent inner validation split.
- Thresholds are selected from training subject predictions in the old deep script, so threshold-dependent metrics are optimistic unless redesigned.
- Window-level datasets are split through subject IDs in the old deep script, but subjects with more accepted windows can still receive implicit larger training weight.
- Rest/Oddball/1BACK window definitions and event codes are encoded in v1 scripts, but the raw event structure still needs task-level audit before formal Goal 3.

## Comparability

Treat v1 EEG results as exploratory. Goal 3 must use the global fixed CV pool, subject-level OOF aggregation, inner validation for checkpointing/early stopping, and no pilot-holdout decisions.
