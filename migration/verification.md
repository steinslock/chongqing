# Migration Verification

## Source-tree checks

Run on 2026-08-27 with
`CHONGQING_RAW_DATA_DIR=/data4/qiangminc/datasets_qiangmin/chongqing`:

- Python AST parsing for `src/`, `scripts/`, `tests/`, and legacy v1 EEG
  scripts: passed.
- `git diff --check`: passed.
- Active project, readiness, Goal 2.6, and Goal 2.7 config loaders resolve the
  raw-data environment override and preserve the read-only guard: passed.
- All six legacy v1 EEG entry points import and show `--help` from a relocated
  path-compatible root: passed under the `chongqing_v1` environment.
- `avmoe` environment: 109 tests passed in 19.342 seconds.
- `chongqing_v1` environment: 109 tests passed in 21.062 seconds. The existing
  pandas fragmentation performance warning was emitted and is non-fatal.

## File integrity

`migration/MIGRATION_FILES.sha256` covers every regular file in the archived
project tree except the checksum list itself. Run it from the extracted project
root with `sha256sum -c migration/MIGRATION_FILES.sha256`.

The archive is additionally tested with `zstd -t`, checked for a single
`chongqing/` top-level directory, extracted under a differently named temporary
parent directory, and subjected to the complete test suite. Results of this
post-archive exercise are written to the companion file
`chongqing_migration_20260827.verification.txt` beside the archive.
