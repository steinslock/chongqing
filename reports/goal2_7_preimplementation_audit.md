# Goal 2.7 Preimplementation Audit

Date: 2026-07-09

Project root: `/home/qiangminc/codes/data4_qiangminc/code/chongqing`

Raw data root: `/home/qiangminc/codes/data4_qiangminc/datasets_qiangmin/chongqing`

This audit was written before Goal 2.7 code changes. It records the current Goal 2.6 implementation issues, the affected outputs that must be rerun, which features can be reused, which features must be regenerated, and where task-event semantics are supported or still missing.

## Required Context Read

The Goal 2.7 request file, project instructions, protocol documents, Goal 2.5 reports, Goal 2.6 reports/results, split files, group files, and Goal 2.6 code were inspected before implementation. The current worktree was clean before this report was added.

Key protocol constraints carried into Goal 2.7:

- Raw files remain read-only.
- Pilot/locked holdout subjects must not enter Goal 2.7.
- Standard fixed CV must use `artifacts/splits/subject_splits_v1.csv`, `split_group == cv`, and `cv_fold`.
- Group-aware fixed CV must use `artifacts/splits/subject_splits_group_robustness_v1.csv`, `split_group == cv`, and `robustness_fold`.
- Protocol A and Protocol B are co-primary; the same predefined models and feature sets must be used in both.
- Inner CV, PCA dimension selection, hyperparameter selection, and threshold selection must use only the outer-train subjects.

## Goal 2.6 Issue Inventory

| Issue | Evidence location | Current behavior | Goal 2.7 action |
|---|---|---|---|
| Missing key independent-increment paired comparisons | `src/chongqing_binary/goal2_6/runner.py::_paired_comparisons` | Existing pair list does not cover all required `modality+demographics vs demographics` and `modality+QC+demographics vs QC+demographics` contrasts. | Replace/extend paired comparison engine; require same subject, same outer fold, same model, same CV protocol; add paired bootstrap AUROC/AUPRC differences and fold-direction checks. |
| Pooled threshold-dependent metrics use one median threshold | `src/chongqing_binary/goal2_6/runner.py::_pooled_metrics`, `::_bootstrap_table` | For `inner_cv`, pooled metrics use `float(group["threshold"].median())` rather than each subject's outer-fold threshold. | Store fold-specific threshold per subject; compute pooled threshold-dependent metrics from row-level fold-threshold predictions. |
| Group-aware CV is supplemental only | `src/chongqing_binary/goal2_6/runner.py::_group_robustness_table` | Only a small robustness summary is produced; no full OOF, no CIs, no paired comparisons. | Run full model pipeline under both Standard CV and Group CV; output separate OOF tables and shared metrics/CI/comparison tables with `cv_protocol`. |
| Face PCA mixes visual embeddings with demographics/QC/metadata | `src/chongqing_binary/goal2_6/runner.py::_build_pipeline` | For face models, PCA is applied after a single preprocessor over all numeric/categorical features. | Add branch-separated preprocessing: visual embedding impute/scale/PCA; nonvisual numeric/categorical bypass visual PCA and are concatenated before the classifier. |
| Face failed detection uses center crop as face | `src/chongqing_binary/goal2_6/face.py::_process_video`, `::_center_crop` | If no face is detected, a center crop is embedded as face. | Re-extract strict face features; invalid face frames are excluded from face-only embeddings. |
| Face failed detection can leave full face in background | `src/chongqing_binary/goal2_6/face.py::_process_video` | Background for failed face frames is `frame.copy()`. | Re-extract strict background using only frames with detected face boxes; create black-mask main and blur-mask sensitivity features. |
| Face sampling too low for Goal 2.7 | `configs/goal2_6/face.yaml` | `sample_frames: 8`. | Increase to at least 16 fixed sampled frames per video for strict Goal 2.7 extraction. |
| Face detector is Haar-only fallback | `src/chongqing_binary/goal2_6/face.py::_load_haar_detector`; `configs/goal2_6/face.yaml` | OpenCV Haar is the configured detector; current environment check found no InsightFace, RetinaFace, MTCNN, MediaPipe, or facenet-pytorch. OpenCV `FaceDetectorYN_create` exists, but no local YuNet/SCRFD/RetinaFace checkpoint was found. | Prefer OpenCV YuNet if a checkpoint is available or can be provisioned reproducibly; otherwise record Haar as fallback/control and expose detector/fallback status in QC/reporting. |
| EEG Oddball all windows are named target | `src/chongqing_binary/goal2_6/eeg.py::_erp_features` | `windows_by_condition = {"target": windows}` for Oddball. | Do not call this full Oddball ERP. If only code 22 is available, rename as `oddball_target_only_proxy`; formal target/non-target features are blocked unless event semantics are confirmed. |
| EEG 1BACK condition difference uses unconfirmed code semantics | `src/chongqing_binary/goal2_6/eeg.py::_erp_features` | `signal_erp_19_minus_18_*` is built from codes 18 and 19 without confirmed condition meaning. | Remove/block condition-difference features unless task semantics are confirmed. Keep task-generic features separately as `1back_generic_signal`. |
| fNIRS task segmentation falls back to arbitrary 20/60/20 blocks | `src/chongqing_binary/goal2_6/fnirs.py::_segments`; `configs/goal2_6/fnirs.yaml` | If no nonzero marker exists, the code splits each recording into first 20%, middle 60%, and last 20%. | Remove this from formal task-response features. Use marker-confirmed or protocol-confirmed timing only; otherwise mark `segment_blocked` and use whole-recording features separately. |
| Bikom CSV reader has fixed 2000-row cap | `src/chongqing_binary/goal2_6/fnirs.py::_process_bikom`, `::_read_bikom_data`; `configs/goal2_6/fnirs.yaml` | `bikom_max_rows: 2000` is passed as `nrows`. | Read complete Bikom files; record raw rows, used rows, and whether previous 2000-row cap would truncate rows/markers. |
| Main demographics baseline includes grade group | `src/chongqing_binary/goal2_6/io.py::demographic_columns`; `src/chongqing_binary/goal2_6/runner.py::_standard_feature_sets` | Main demographics includes `age_clean`, `sex_clean`, `grade_clean`, and `grade_group_clean`. | Redefine main demographics as age + sex + grade. Run grade-group and group-proxy sensitivity sets separately. |
| No `QC+demographics` baseline for key increments | `src/chongqing_binary/goal2_6/runner.py::_standard_feature_sets`, `::_face_datasets`, `::build_core3_datasets` | Feature sets include `qc`, `signal_qc`, `signal_demographics`, `signal_qc_demographics`, but not a universal `qc_demographics`. | Add `qc_demographics` for EEG/fNIRS/Face and Core3. |
| Core3 name overstates cohort scope | `src/chongqing_binary/goal2_6/runner.py::build_core3_datasets`; `results/goal2_6/core3_same_cohort_summary.csv` | `core3_same_cohort` actually represents EEG Rest + Yiruid VFT + Face self-intro intersection, reported at 661 subjects. | Rename to `core3_rest_yiruidvft_selfintro_intersection`; optionally build Cohort B if coverage is sufficient. |
| HGB fallback search space is too small | `configs/goal2_6/models.yaml` | HGB uses a single very small candidate in Goal 2.6. | Expand to 3-12 predefined HGB candidates with reasonable `max_iter`, `learning_rate`, `max_leaf_nodes`, and `l2_regularization`. |

## Results That Must Be Rerun

The following Goal 2.6 outputs are directly affected by protocol or feature-definition changes and must not be reused as final Goal 2.7 evidence:

- OOF predictions: threshold fields, feature-set definitions, Face feature semantics, and group-aware protocol scope change.
- Pooled metrics and fold metrics: threshold-dependent pooled metrics need fold-specific thresholds.
- Bootstrap CIs: threshold-dependent bootstrap calculations must use fold-specific thresholds, and Protocol B must be included.
- Paired comparisons: required independent-increment contrasts are missing.
- PCA diagnostics: old PCA mixed visual and nonvisual branches.
- Group robustness summary: must be replaced by full group-aware OOF/metrics/CI.
- Core3 summary: old name and feature sets are incomplete.
- Face reports/results: strict face/background definitions and PCA branch separation require rerun.
- fNIRS task-response interpretations: fallback segmentation and Bikom row cap require rerun or blocking.
- EEG Oddball/1BACK task-condition interpretations: event semantics are not adequately supported by current cache alone.

## Feature Reuse Plan

Reusable with Goal 2.7 relabeling/auditing:

- Standard split file `artifacts/splits/subject_splits_v1.csv` for Protocol A.
- Group robustness split file `artifacts/splits/subject_splits_group_robustness_v1.csv` for Protocol B.
- Group proxy files under `artifacts/groups/`.
- Goal 2.6 EEG Rest cached-window traditional features can seed Goal 2.7 Rest signal features because Rest has no task-event condition semantics.
- EEG Oddball cached windows can only be reused as an explicitly named `oddball_target_only_proxy` if no target/non-target raw reconstruction is validated.
- EEG 1BACK cached windows can seed generic signal features after condition-difference columns are removed/blocked.
- fNIRS Rest whole-recording features can be reused or regenerated with Goal 2.7 metadata because no task-response segmentation is required.
- Existing demographics, label, split, and QC metadata can be reused after feature-set separation is repaired.

Must be regenerated or transformed before Goal 2.7 final outputs:

- Strict Face embeddings for face crop, black-mask background, blur-mask background, full frame, and two-video aggregates.
- Face QC with detector name, checkpoint/source, threshold, detection rate, effective valid face frames, blocked flag/reason, fallback flag, multi-face rate, and audio-not-used flag.
- Face contact sheets for at least 200 label-independent videos.
- fNIRS Bikom features using full-file reads, not a 2000-row cap.
- fNIRS task-response features only where marker/protocol timing is confirmed; otherwise blocked rows and whole-recording features.
- EEG Oddball target/non-target ERP features only if event code semantics and raw reconstruction are confirmed.
- EEG 1BACK condition-difference features only if code semantics are confirmed.
- Model outputs, metrics, bootstrap CIs, paired comparisons, threshold diagnostics, PCA diagnostics, demographics decomposition, protocol deltas, and reports.

## Current EEG Event Evidence

Sources inspected:

- `experiments/v1/eeg/scripts/cache_deep_windows.py`
- `experiments/v1/eeg/artifacts/deep/windows/metadata_rest.csv`
- `experiments/v1/eeg/artifacts/deep/windows/metadata_oddball.csv`
- `experiments/v1/eeg/artifacts/deep/windows/metadata_1back.csv`
- `experiments/v1/eeg/reports/eeg_deep_baseline_report.md`
- Raw EEG directories under `脑电/1_rest-1334`, `脑电/2_Oldball-2358`, and `脑电/4_1BACK-1810`

Evidence found before implementation:

- Rest cache: 67,332 windows from 1,284 subjects, no event code, 5.0 s windows.
- Oddball cache: 52,193 windows from 2,285 subjects, all `event_code == 22`, 250 samples per window, relative window approximately -0.2 to 0.8 s around the event.
- 1BACK cache: 24,780 windows from 1,694 subjects, event counts `18: 22,845` and `19: 1,935`, 500 samples per window, relative window approximately -0.2 to 1.8 s around the event.
- `cache_deep_windows.py` predefines Oddball event code `22` and 1BACK event codes `18`, `19`, but does not prove target/non-target or task-condition semantics.

Evidence not yet found:

- A reliable project-local mapping proving Oddball code 22 is target or non-target, or proving that non-target codes are absent/present in raw events.
- A reliable project-local mapping proving 1BACK codes 18 and 19 correspond to named task conditions or response/stimulus categories.
- A documented baseline interval beyond the cached epoch windows.

Initial Goal 2.7 event status:

- Rest: event-free and usable.
- Oddball: formal target/non-target ERP is blocked unless raw BDF/EVT audit proves semantics and reconstructability; cached code-22-only features may be retained only as `oddball_target_only_proxy`.
- 1BACK: condition differences are blocked unless semantics are confirmed; generic signal features may proceed separately.

## Current fNIRS Timing Evidence

Sources inspected:

- `src/chongqing_binary/goal2_6/fnirs.py`
- `configs/goal2_6/fnirs.yaml`
- `reports/goal2_6_fnirs_results.md`
- Raw Yiruid `.nirs` samples under `近红外/依瑞德近红外/`
- Raw Bikom CSV samples under `近红外/必可明近红外/`

Evidence found before implementation:

- Yiruid VFT sample files have 3,000 rows and typically one nonzero `s` marker with value `1.0`; `Mark_infor` appears with two values.
- Yiruid 1BACK sample files have about 3,100-3,540 rows and typically two nonzero `s` markers with value `1.0`.
- Yiruid Rest sample files have about 6,980-7,000 rows and no nonzero markers.
- Bikom VFT sample files have about 1,700 rows, about 169.9 s duration, and no nonzero `Mark` in sampled HbO files.
- Bikom 1BACK sample files have about 1,553 rows, about 155.2 s duration, and six nonzero `Mark` values in sampled HbO files.
- Bikom Rest sample files often have more than 2,000 rows; sampled files show 3,497-3,999 rows, so the Goal 2.6 2,000-row cap truncates Rest files and can miss later markers.

Evidence not yet found:

- A reliable protocol document confirming baseline, active block, and recovery durations for Yiruid VFT/1BACK.
- A reliable protocol document confirming fixed timing for Bikom VFT/1BACK.
- A subject-level rule mapping sparse marker rows to baseline/active/recovery intervals for every device/task.

Initial Goal 2.7 fNIRS status:

- Rest whole-recording features are usable.
- VFT/1BACK task-response features require marker/protocol audit before formal use.
- No 20/60/20 fallback can be used as a formal task-response result.
- Bikom must be read full-length, and row truncation must be recorded.
- Yiruid feature names must remain raw/log-intensity or OD-like, not HbO/HbR.

## Current Face Detector and Runtime Evidence

Sources inspected:

- `src/chongqing_binary/goal2_6/face.py`
- `configs/goal2_6/face.yaml`
- Python environment checks under conda environment `avmoe`
- Local model-file search for YuNet/SCRFD/RetinaFace checkpoints

Evidence found before implementation:

- Hardware: two NVIDIA RTX A6000 GPUs are present.
- Default base Python lacks `torch` and `pandas`; Goal 2.7 Python commands should use `conda run -n avmoe`.
- `avmoe` has `torch 1.13.0+cu117`, `torchvision 0.14.0+cu117`, CUDA available, and both A6000 GPUs visible.
- OpenCV version is 4.6.0 and exposes `FaceDetectorYN_create`.
- `insightface`, `retinaface`, `mtcnn`, `mediapipe`, and `facenet_pytorch` are not installed in `avmoe`.
- No local YuNet/SCRFD/RetinaFace ONNX/PTH checkpoint was found in searched project/home paths.

Initial Goal 2.7 Face status:

- Strict Face extraction should run in `avmoe` to use GPU for the frozen ResNet18 encoder.
- OpenCV YuNet is preferred if a checkpoint is available/provisioned. If not, Haar must be explicitly recorded as fallback/control and interpreted with shortcut caution.
- The encoder remains frozen; no visual fine-tuning is allowed.
- Audio must remain unused.

## Missing Data/Evidence Register

These items are not proven at preimplementation time and must be resolved by audit outputs or marked blocked:

- Oddball target/non-target code semantics.
- Oddball raw BDF/EVT reconstructability for target and non-target windows.
- 1BACK event code semantics for 18/19.
- fNIRS VFT baseline/active/recovery timing for Yiruid and Bikom.
- fNIRS 1BACK event/timing semantics for Yiruid and Bikom.
- Formal non-Haar face detector checkpoint availability.
- Whether strict Face blocked rates leave enough valid subjects in each face task.
- Whether Cohort B (EEG Oddball + Yiruid VFT + Face task) has sufficient same-subject coverage after event/strict-face validity filters.

## Implementation Gate

Coding may begin after this report. The first implementation steps must preserve the above protocol constraints and must not treat blocked event/timing semantics as formal task-response evidence.
