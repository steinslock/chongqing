# Migration Environment Snapshot

Captured on 2026-08-27 in Asia/Tokyo for the Chongqing migration archive.

## Source state

- Project root on source host: `/data4/qiangminc/code/chongqing`
- Git commit: `fd07ba1570b993c7008a321673e14e7988832899`
- Branch: `main`
- Remote: `https://github.com/steinslock/chongqing.git`
- Original untracked state before migration work:
  `reports/status_2026-08-23/` (`artifact.json`, `report.html`,
  `source_notes.md`)
- The migration portability changes are intentionally left as working-tree
  changes in the archive; no Git commit was created.

## Hardware

- GPUs: 2 x NVIDIA RTX A6000, 49140 MiB each
- NVIDIA driver: 535.129.03
- Archive compressor: Zstandard CLI 1.5.5

## Tested Python environments

### avmoe

- Python: 3.9.25
- PyTorch: 1.13.0+cu117
- PyTorch CUDA runtime: 11.7
- CUDA available: true
- Exact packages: `migration/avmoe-requirements.lock.txt`

### chongqing_v1

- Python: 3.11.5
- PyTorch: 2.5.1+cu121
- PyTorch CUDA runtime: 12.1
- CUDA available: true
- Exact packages: `migration/chongqing-v1-requirements.lock.txt`

Both environments passed the complete 107-test suite before portability edits.
Post-edit source-tree results and the external relocated-archive verification
procedure are recorded in `migration/verification.md`.
