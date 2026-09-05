# Chongqing Project Migration

This repository can be unpacked at any absolute path. Project-internal paths
are resolved relative to the directory containing this file. The raw dataset is
not included in the migration archive.

## Restore on a new server

1. Verify and extract the archive (the archive and checksum file must be in the
   same directory):

   ```bash
   sha256sum -c chongqing_migration_20260827.tar.zst.sha256
   tar --use-compress-program=zstd -xf chongqing_migration_20260827.tar.zst
   cd chongqing
   ```

2. Point the project at the raw dataset on the new server. The value must be an
   absolute path:

   ```bash
   export CHONGQING_RAW_DATA_DIR=/absolute/path/to/datasets_qiangmin/chongqing
   test -d "$CHONGQING_RAW_DATA_DIR"
   ```

   Add the export to the job script or shell profile used for this project.
   Every active config loader and the legacy v1 EEG entry points honor the same
   variable. The configured raw path remains protected as a read-only input.

3. Rebuild a Python environment. Virtual environments are intentionally not
   copied because their executables and activation scripts contain host paths.
   Two exact package snapshots are included under `migration/`:

   - `avmoe-requirements.lock.txt`: Python 3.9.25, PyTorch 1.13.0 + CUDA 11.7;
     this is the environment named by the current project instructions.
   - `chongqing-v1-requirements.lock.txt`: Python 3.11.5, PyTorch 2.5.1 +
     CUDA 12.1, including MNE and the broader raw-data toolchain.

   Install the PyTorch build that matches the new server's NVIDIA driver from
   the official PyTorch package index, then install the remaining pinned
   packages. The lock files are exact environment records; CUDA-specific
   packages may need the matching PyTorch index rather than the default PyPI
   index.

4. Verify the restored files and code:

   ```bash
   sha256sum -c migration/MIGRATION_FILES.sha256
   PYTHONPATH=src python -m unittest discover -s tests
   PYTHONPATH=src python - <<'PY'
   from chongqing_binary.config import load_config

   config = load_config("configs/default.yaml")
   print("project_root:", config.project_root)
   print("raw_data_dir:", config.paths["raw_data_dir"])
   print("subject_manifest:", config.paths["subject_manifest"])
   PY
   ```

5. Resume from Goal 2.8. Do not start Goal 3, Goal 4, Goal 5, deep training, or
   multimodal fusion until the Goal 2.8 remediation and decision gate is
   complete.

## Archive scope

Included: the complete `chongqing/` project tree, `.git`, untracked status
reports, Git-ignored local features, EEG window arrays, predictions,
checkpoints, and sensitive local face contact sheets.

Excluded because they are outside the project tree: the 1.5 TB raw dataset,
Qwen2.5-Omni 3B/7B model directories, Hugging Face/torchvision caches, Conda or
venv directories, and pip caches. The small project-local YuNet detector is
included so the current face audit remains reproducible.

Historical reports and manifests intentionally retain the absolute paths that
were recorded when they were produced. They are provenance, not active path
configuration.

The archive is not encrypted. Store it only on a trusted, access-controlled
drive because it contains subject IDs, derived clinical information, and local
face audit images.
