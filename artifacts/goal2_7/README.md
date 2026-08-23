# Goal 2.7 Artifact Release

Compact EEG/fNIRS features, Face QC, event inventories, timing audits, detector
metadata, and run/release manifests are part of the formal release.

The following remain local:

- Face frozen-embedding CSVs and `.part.csv` restart checkpoints because they are
  large and reproducible from the frozen encoder config;
- Face contact sheets because they contain identifiable source-video frames;
- uncompressed OOF CSVs, whose deterministic gzip archives are published under
  `results/goal2_7/`.

Aggregate Face detection rates, blocked counts, fallback counts, and audit
limitations remain available in `reports/goal2_7_face_detection_audit.md` and
`results/goal2_7/face_strict_control_summary.csv`.
