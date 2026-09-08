# Goal 2.7 Superseded Notice

Date: 2026-09-07

Goal 2.7's three modality conclusions are **superseded**. This notice records
what was concluded, what the raw data actually shows, and where in the code the
error originated. Goal 2.7's own files are left unchanged so it stays
reproducible; this is a separate document.

## Superseded conclusions

| Modality | Goal 2.7 status | Now |
|---|---|---|
| EEG | `BLOCKED_BY_INVALID_TASK_SEMANTICS + NO_CLEAR_SIGNAL` | `SUPERSEDED` |
| fNIRS | `BLOCKED_BY_INVALID_TASK_SEMANTICS + NO_CLEAR_SIGNAL` | `SUPERSEDED` |
| Face | `SHORTCUT_DOMINATED` | `SUPERSEDED` |

A superseded conclusion is not evidence and must not be cited as a constraint on
new work.

## 1. EEG Oddball: the standard condition exists in the raw data

Goal 2.7 recorded that the Oddball cache contained only event code `22`,
described it as `oddball_target_only_proxy`, and blocked target/non-target ERP.

The raw `*_evt.bdf` files contain **both** codes. Across 313 sampled subjects,
every one had both, with median 123 of code `11` and 25 of code `22`, five
blocks, 1.001 s inter-stimulus interval and 31 s inter-block gaps.

The paradigm fixes the meaning: `附件/oddball_device_lastrun.py` maps
`frequency_500hz.wav` to trigger `11` and `frequency_1000hz.wav` to trigger
`22`, and `task_block.xlsx` is 25 trials of 500 Hz with no expected response
against 5 trials of 1000 Hz requiring a keypress. `附件/脑机接口.pdf` states the
same: respond to the deviant, not to the standard.

Root cause: `experiments/v1/eeg/scripts/cache_deep_windows.py` line 78 hardcodes
`"event_codes": ["22"]`. Goal 2.6 and Goal 2.7 read that cache and attributed a
cache filter to the data. `scripts/audit_goal2_7_events.py` could not have
caught it, because `audit_eeg` reads only the cached metadata CSV and never
opens a BDF.

Consequence: target/standard ERP and the target-minus-standard difference wave,
the actual P300 effect, were never tested.

## 2. EEG 1BACK: codes 18 and 19 are positional, not conditional

Goal 2.7 blocked 1BACK condition differences because codes `18`/`19` were
"not semantically confirmed".

Across 399 sampled subjects, code `19` appears exactly twice per subject and
code `18` about 23 times. Event timelines show `19` at the first stimulus of
each of the two blocks, with 2.00 s SOA and a 5.0 s inter-block gap. So `19`
marks the block-initial stimulus, the one trial with no 1-back predecessor, and
`18` marks every later stimulus. They were never a condition contrast, so
blocking that contrast was correct but for the wrong reason.

Two further facts were not recorded by Goal 2.7:

- Codes `66`/`77` encode response correct/incorrect but **lag by one trial**:
  `附件/nback_animal_marker_lastrun.py` emits them at Begin Routine from the
  previous trial's `task_resp.corr`.
- Block 2 is systematically truncated. Block 1 always carries 15 stimuli; block
  2 carries 3 to 11, mode 10. No subject has the full 30.

EEG 1BACK match/non-match remains genuinely unrecoverable, because the EEG-side
condition files and per-subject logs are not in the dataset. The fNIRS side does
have them.

## 3. fNIRS: wavelengths, geometry and timing are all recorded

Goal 2.7 forbade naming Yiruid signals HbO/HbR "without wavelength and geometry
confirmation", and blocked all fNIRS task-response features for want of
confirmed timing.

Every Yiruid `.nirs` file is a standard HOMER2 MATLAB file carrying
`SD.Lambda = [690, 830]` nm, `nSrcs` and `nDets` of 16, 3D optode positions in
millimetres, a 53-pair by 2-wavelength measurement list, a 20 Hz time vector,
and a stimulus matrix with exact marker samples.
`附件/前额叶_20260106093254/` supplies the matching `yrd-53` montage and
per-channel MNI cortical projections. Everything needed for the modified
Beer-Lambert law is present.

Root cause: `src/chongqing_binary/fnirs/io.py` probes `.nirs` with
`scipy.io.whosmat`, which returns variable names and shapes but no contents,
and therefore hardcodes `"wavelengths": "unknown_from_header_probe"`.
`src/chongqing_binary/goal2_7/fnirs.py` loads the file but never reads `SD`, and
`scripts/audit_goal2_7_events.py` passes an explicit `variable_names` list that
excludes `SD`.

Timing is likewise confirmed. Sampled subjects are identical within each task:

| Device | Task | Duration | Markers |
|---|---|---|---|
| Yiruid | Rest | 350 s | none |
| Yiruid | VFT | 150 s | 1 at 30.0 s |
| Yiruid | 1BACK | 157 s | 2 at 30.0 and 92.0 s |
| Yiruid | Oddball | 633 s | 10, every 60 s from 30 s |
| Yiruid | Doors | 570 s | 6, every 90 s from 30 s |
| Bikom | Rest | 350 s | `ST`, `ED` |
| Bikom | VFT | 170 s | none |
| Bikom | 1BACK | 155 s | `ST`, `A0`, `A1`, `B0`, `B1`, `ED` |
| Bikom | Oddball | 630 s | `ST`, 10 `A0`/`A1` pairs, `ED` |
| Bikom | Doors | 570 s | `ST`, 6 `A0`/`A1` pairs, `ED` |

These match the paradigm scripts and `脑机接口.pdf` exactly. Two secondary
defects compounded the blocker: `goal2_7/fnirs.py` reduces the Bikom `Mark`
column to a 0/1 indicator, discarding the `A0`/`A1`/`B0`/`B1` labels that encode
block on and off; and its `_segments()` takes the task window as "first marker
to last marker", which degenerates to a single sample for VFT and swallows all
ten rest periods for Oddball.

Bikom VFT is the one genuine gap: it has no markers. Its group-mean HbO shows a
sharp change point at about 29.5 s, consistent with the same 30 s baseline used
everywhere else, but the task end is not directly evidenced. It carries
`timing_confidence: low` and may only support sensitivity analyses.

## 4. Face: the task video was never segmented

Goal 2.7 sampled 16 frames uniformly from each `面部2-任务` video and concluded
Face was shortcut-dominated.

Those videos are 680 to 820 s multi-phase sessions, not single clips.
`附件/run_video_process.py` splits each one, keyed by `A_id`, into three emotion
movies labelled positive, neutral and negative, three corpus readings with the
same labels, and 18 dialogue questions. Split points come from
`附件/网页数据.xlsx`, which covers 4574 subjects with 4422 complete rows and a
median session span of 699 s. `面部/面部任务.zip` holds the stimulus set itself,
including the three movies at 93.16 s, 86.64 s and 125.00 s, the 18 question
clips, and the `start.mp3` alignment beep; `index.js` fixes the movie order as
positive, neutral, negative.

Sampling 16 frames across an 11 minute session that mixes film watching, reading
aloud and interview yields mostly identity, appearance and room background. That
is a sufficient alternative explanation for the shortcut-dominated result, so
the result does not establish the absence of facial signal.

A secondary defect: `configs/goal2_7/face.yaml` prefers the YuNet detector, but
the run recorded Haar fallback on 3572 of 3597 self-introduction videos and 3567
of 3597 task videos. YuNet has since been verified working in the unified
environment.

## What is not superseded

The Goal 2.7 evaluation protocol stands, and so does its central negative
finding: demographics and acquisition site are strong predictors of the label.
Age plus sex plus grade reaches about 0.67 AUROC, the `A_id`-prefix group proxy
alone reaches about 0.68, their combination about 0.71, and Group-aware CV
deflates group-proxy-heavy rows. Non-healthy prevalence differs sharply by
school. Any future positive modality result must clear these controls.

## Release manifest

`artifacts/goal2_7/release_manifest.json` and
`scripts/build_goal2_7_release_manifest.py` are retired. Hash-based constraints
were abolished on 2026-09-07; see `AGENTS.md`. The manifest is kept only as a
historical file and must not be extended, regenerated, or validated against.
