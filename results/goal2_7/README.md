# Goal 2.7 Result Release

This directory contains the machine-readable Goal 2.7 evidence used by
`reports/goal2_7_final_report.md`.

## Published outputs

- pooled and fold metrics;
- 1000-resample subject bootstrap confidence intervals;
- 1000-resample paired independent-increment comparisons;
- demographics, shortcut, Core3, PCA, threshold, and exclusion diagnostics;
- deterministic gzip archives of the Standard and Group-aware OOF predictions.

The full OOF archives are:

- `all_oof_predictions_standard_cv.csv.gz`
- `all_oof_predictions_group_cv.csv.gz`

Pandas reads these archives directly. To restore the exact filenames expected by
the default config, run:

```bash
gzip -dk results/goal2_7/all_oof_predictions_standard_cv.csv.gz
gzip -dk results/goal2_7/all_oof_predictions_group_cv.csv.gz
```

`scripts/run_goal2_7.py --supplemental-only` also falls back to the tracked gzip
archives when the uncompressed CSVs are absent.

## Local-only outputs

The uncompressed OOF CSVs are ignored because each exceeds GitHub's 100 MB
per-file limit. They contain the same rows as the deterministic gzip archives.
Hashes, sizes, row counts, and publication disposition are recorded in
`artifacts/goal2_7/release_manifest.json`.
