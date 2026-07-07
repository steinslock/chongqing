# EEG v1

The first EEG milestone is a resting-state EEG baseline:

1. Index Rest BDF data and event files.
2. Extract subject-level EEG-only features.
3. Train subject-level cross-validated baselines.
4. Write metrics, predictions, splits, and a markdown report.

The scripts intentionally ignore named main BDF files and use only `*_data.bdf`/`data.bdf` plus `*_evt.bdf`/`evt.bdf`.

