# Face Shortcut Audit Plan

Goal 5 must treat video background, device, codec, resolution, frame rate, and quality as possible shortcuts. All clips from the same `L_id` and source video inherit the same global fold.

## Required Future Experiments

1. face crop only
2. aligned face crop
3. full frame
4. background blurred
5. background masked
6. face masked background-only
7. QC-only
8. codec/resolution/fps-only
9. demographics-only
10. Face+demographics
11. self-introduction video only
12. task video only
13. two-video fusion

## Interpretation Rules

- Background-only or codec-only performance near face-crop performance indicates shortcut risk.
- Full-frame performance that exceeds face-crop while background-masked drops suggests background or acquisition-batch leakage.
- Stable face-crop/aligned-crop signal with weak background-only/QC-only baselines is stronger evidence for face dynamics.
- Two-video fusion should aggregate subject-level predictions only after both videos are processed within the same fold.
