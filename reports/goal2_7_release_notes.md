# Goal 2.7 Formal Release Notes

Release date: 2026-08-23

Goal 2.7 is the formal lightweight multimodal evidence baseline. Standard fixed
CV and Group-aware fixed CV are co-primary, all preprocessing/model/PCA/threshold
selection is nested inside outer-train, and independent increments use paired
subject bootstrap.

## Decision

- EEG: `BLOCKED_BY_INVALID_TASK_SEMANTICS + NO_CLEAR_SIGNAL`.
- fNIRS: `BLOCKED_BY_INVALID_TASK_SEMANTICS + NO_CLEAR_SIGNAL`.
- Face: `SHORTCUT_DOMINATED`.
- No modality reached `INDEPENDENT_SIGNAL_SUPPORTED`.

The next recommended stage is Goal 2.8, an event-semantics and shortcut-remediation
decision gate. Goal 3/4/5 deep training is not authorized by this release.

## Release contents

The GitHub release includes:

- Goal 2.7 source, scripts, frozen configs, and protocol tests;
- event/timing/detection audits and final technical reports;
- compact EEG/fNIRS features and Face QC;
- all metric, CI, paired, demographics, Core3, shortcut, PCA, threshold, and
  exclusion tables;
- complete Standard/Group OOF predictions as deterministic `.csv.gz` archives;
- a SHA-256 release manifest.

Large Face embeddings, restart checkpoints, uncompressed OOF CSVs, and identifiable
Face contact sheets remain local. This is a publication constraint, not an
analytical exclusion; aggregate audit evidence and hashes remain in the release.

## Verification

- Full test discovery: 107 tests passed during formalization.
- Goal 2.7 protocol tests: 47 tests passed during formalization.
- Standard OOF rows: 1,528,167.
- Group-aware OOF rows: 1,528,167.
- Bootstrap CI rows: 36,720, all using 1000 resamples.
- Paired comparison rows: 618, all using 1000 resamples.

See `reports/goal2_7_final_report.md` for interpretation and
`artifacts/goal2_7/release_manifest.json` for exact file hashes and disposition.
