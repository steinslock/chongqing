# Face Goal 5 Design

Goal 5 should start from frozen visual features rather than full video-model fine-tuning.

## First Formal Models

1. Frozen frame encoder + mean pooling + Logistic Regression.
2. Frozen frame encoder + MLP.
3. Frozen frame encoder + lightweight temporal aggregation using GRU, TCN, or attention pooling.

VideoMAE, MViT, TimeSformer, or full-parameter video fine-tuning are deferred until frozen-feature models show stable signal.

## Video Inputs

- Self-introduction video alone.
- Task video alone.
- Two-video subject-level fusion.
- Face crop only, aligned face crop, and full frame variants.

## Shortcut Controls

Run background blurred, background masked, face-masked background-only, QC-only, codec/resolution/fps-only, demographics-only, and Face+demographics experiments. If background-only or codec-only baselines approach face-crop performance, treat the Face signal as shortcut-contaminated.

## Protocol

- Decode and sample clips inside subject fold only.
- All clips from the same source video inherit `L_id` split and fold.
- Keep subject-level predictions with `L_id`.
- Report model performance on the same Face cohort for random, demographics-only, QC-only, signal-only, signal+QC, and signal+demographics.
