# Experiments

This directory contains versioned experiment workspaces.

## Layout

- `v1/`: prior single-modality baseline workspace, currently focused on EEG Rest/Oddball/1BACK baselines.
- `v2/`: reserved for future multimodal or stronger model work.

## Policy

- Keep version-specific scripts, reports, artifacts, and checkpoints under their experiment version.
- Use project-root `configs/`, `src/`, `scripts/`, and `tests/` for shared reproducible interfaces.
- Do not write raw data into experiment folders.

