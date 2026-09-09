# Goal 2.10 re-audit against the hospital paradigm document

**Document**: `附件/重医眼动范式及参数.docx`, received 2026-09-09, after Goal 2.10
had been extracted, modelled and reported.
**Question**: does the paradigm this project reverse-engineered match the one
that was actually run, and does anything in the document change the result?

**Answer**: the recovered paradigm is confirmed on every quantity the document
states. One documentation error is corrected, one previously invisible
methodological defect is exposed and now fixable, one unit system is unlocked,
and one device is revealed to be missing from the dataset. The Goal 2.10
result — 0 of 576 increments over demographics — is unchanged.

Goal 2.10 was specified without any attachment. `configs/goal2_10/eye_paradigm_spec.yaml`
carried a provenance warning saying so, and every value in it was recovered from
two recorded sources: the archived stimulus media and the per-subject
presentation timelines. This document is the first external check on that
recovery, and it is a strong one because it was written before the analysis and
without reference to it.

---

## 1. Scope: the document describes two different paradigms

The document contains two tables. Only the first describes this dataset.

The header states 七鑫易维与Tobii设备实验范式、呈现参数完全一致，集思鸣智为设备自带范式.
Table 1 sits under （1）七鑫易维、Tobii设备 and matches these recordings. Table 2
sits immediately above the heading （二）集思鸣智, whose section is otherwise
empty, and describes a gaze-contingent battery of five tasks: 前扫视, 反扫视,
记忆引导扫视, 双步扫视, 平滑追踪, with an 800 ms held central fixation gate,
targets at 8° in four directions, 2000 ms timeouts, an 800 ms inter-trial
interval, and pursuit as a 5°/s linear ramp in one of eight directions.

Table 2 is the 集思鸣智 device's built-in battery, not this dataset. Four
independent facts settle it:

1. It contradicts Table 1 on the same task names. 前扫视 there is gaze-contingent
   at 8° in four directions; here it is a fixed 1.5 s cross then a 1.0 s target,
   horizontal only, at 6° and 12°.
2. Gaze-contingent gating is impossible with these stimuli. They are pre-rendered
   60 fps MP4s of fixed length; an MP4 cannot wait for the subject's gaze.
3. 记忆引导扫视 and 双步扫视 have no stimulus file, no task directory and no
   timeline name anywhere in either 七鑫易维 project or the Tobii export. The
   七鑫易维 projects contain exactly three task directories: 平滑追随, 扫视,
   自由观看.
4. There is no 集思鸣智 directory under `眼动/` at all.

**Action for the study team, not for the analysis**: a third eye-tracking device
is named in the study's own paradigm document and none of its recordings are in
this dataset. It is worth asking whether that cohort exists and was meant to be
delivered. Its paradigm differs enough that its features could not be pooled
with these three in any case, so this is a coverage question, not a re-analysis
question.

---

## 2. What the document confirms

Every quantity Table 1 states matches what was recovered. Nothing had to be
revised to make them agree.

### Free viewing

| Document | Recovered | Source of the recovery |
|---|---|---|
| 中央白色十字 1 s | 1000 ms | recorded timeline |
| 情绪面孔刺激 4 s | 4000 ms | recorded timeline |
| 间隔（黑色背景）1 s | 1000 ms | recorded timeline |
| 中性 12 / 正性 12 / 负性 12 | 12 / 12 / 12 | stimulus filenames |
| 男女性别分布平衡 | 18 / 18, fully crossed | stimulus filenames |
| 每次屏幕中央呈现单张情绪表情 | single centred face | stimulus media |

The last row matters more than its size suggests. `design_note` in the
specification argued that because one face is on screen at a time there is no
competing stimulus, therefore no within-trial attentional-bias score, therefore
the only available contrast is between trials. That was a judgement call made
from the stimulus files. It is now a documented fact.

### Saccade

| Document | Recovered |
|---|---|
| 中央白色十字 1.5 s | onsets every 150 frames from frame 90 at 60 fps = 1.500 s |
| 外周刺激物 1 s | 60 frames = 1.000 s |
| 水平方向左侧或右侧 | y fixed at 0.5, five distinct x levels |
| 6° 或 12° | two amplitudes, 0.1396 and 0.2823 screen widths |
| 每个位置出现两次，共8个试次 | each of four positions exactly twice, 8 trials |

The trial count is worth dwelling on. An earlier bug had `saccade_trials()`
firing on sub-pixel noise and returning 12 spurious trials of zero amplitude; a
later one dropped the 8th trial at the video boundary. Both were fixed by
reasoning about the stimulus, before this document existed. The document
independently states 8. The formal blocks are 1200 frames at 60 fps = 20.000 s,
which is exactly 8 × (1.5 + 1.0) s with nothing left over.

### Smooth pursuit

The document states three trajectories, each 20 s, each repeated twice:
水平正弦波 0.4 Hz, 慢速 Lissajous 0.2 Hz, 快速 Lissajous 0.4 Hz.

This confirms the single most consequential thing recovered about this task.
`spec_version` 1 had already established, from the decoded video alone, that the
136 s recording is not one continuous sweep but six blocks of three conditions
repeated twice, and that the fast condition runs at exactly twice the frequency
of the slow one at identical amplitude. The whole `fast minus slow` contrast was
built on that. The document confirms it: 0.4 / 0.2 = 2, by design.

An earlier revision of the specification had called this task continuous. That
error was caught by reading the stimulus. Had it not been, the document would
have caught it now.

### Design intent

The document cites a source paper for each task. Two are worth recording.

The free-viewing paper is an alexithymia HD-tDCS eye-tracking study whose
outcome measure is **dwell time on eye versus mouth regions of emotional faces**.
The eyes/mouth AOI decomposition in this analysis was chosen independently, from
the depression literature, and it turns out to be the same contrast the paradigm
designers were reproducing. The AOI choice is aligned with intent, not merely
defensible.

The pursuit paper is Benson et al. 2012, whose clinical target is
**schizophrenia**, not depression. This battery was imported from a different
clinical question. That is not a defect, but it belongs in the interpretation of
the pursuit null: the task was selected for its power to separate a different
disorder.

---

## 3. What the document corrects

### 3.1 Pursuit frequencies were quoted 4.8% low

`spec_version` 1 listed 0.381 Hz (horizontal), 0.143/0.190 Hz (slow) and
0.286/0.381 Hz (fast). Every one of those is low by the factor 21/20.

The cause: the frequencies were obtained by FFT over the whole 21 s block, and
each block opens with 1.0 s of stationary target before the motion starts. Each
value is an exact integer number of cycles over the block — 8, 3, 4, 6, 8 — and
dividing those counts by the document's 20 s of motion returns the document's
figures exactly:

| Condition | spec v1 | × 21 s | cycles | ÷ 20 s | document |
|---|---|---|---|---|---|
| horizontal x | 0.381 | 8.001 | 8 | **0.400** | 0.4 Hz |
| slow x | 0.143 | 3.003 | 3 | **0.150** | — |
| slow y | 0.190 | 3.990 | 4 | **0.200** | 0.2 Hz |
| fast x | 0.286 | 6.006 | 6 | **0.300** | — |
| fast y | 0.381 | 8.001 | 8 | **0.400** | 0.4 Hz |

The single frequency the document quotes per trajectory is the y component; the
Lissajous ratio is 3:4 on both. The block timing also reconciles exactly:
6 × 21 + 5 × 2 = 136 s, the observed recording length, while 6 × 20 + 5 × 2 = 130.
The 21 s block is 1.0 s of settling plus the document's 20.0 s of motion.

**No feature was affected.** `_pursuit_block` takes the target from the decoded
track and reads only `blocks` from this mapping; nothing computes anything from
the frequency numbers. The error was in the description, not in the extraction.
Corrected in `spec_version` 2, with the cycle counts recorded alongside so the
window ambiguity cannot recur.

### 3.2 A visual angle can now be computed

Both the specification and `events.py` stated that viewing distance was never
recorded, therefore no visual angle could be computed, therefore all thresholds
had to stay in screen fractions. That was true and is now false.

The document gives the saccade eccentricities in degrees; the decoded video
gives them in screen widths. Two equations, one unknown, overdetermined, so the
fit is also a test:

| Eccentricity | Decoded (screen widths) | Document | Solved viewing distance |
|---|---|---|---|
| small | 0.1396 | 6° | 1.3282 screen widths |
| large | 0.2823 | 12° | 1.3281 screen widths |

Agreement to four significant figures, and only under a tangent mapping: a
linear degrees-per-screen-width scale fits the same two points at 5.967° and
12.067°. The paradigm was authored with proper tangent geometry and the video
decode is exact. The screen subtends 41.26° × 23.91°.

This fixes the ratio of viewing distance to screen width, which is all a visual
angle needs. The physical screen size and the distance in cm remain unrecorded
and are still not asserted.

**It confirms a guess.** The I-DT dispersion threshold of 0.025 screen widths was
chosen as "about one degree at a nominal 60 cm on a 53 cm-wide display", with
the nominal geometry flagged in the specification as an assumption. Measured
against the document it is **1.078° horizontally**. The choice was right; it is
now verified rather than assumed.

---

## 4. What the document exposes: axis anisotropy

This is the substantive finding of the re-audit, and it was invisible before the
document arrived — not overlooked, but unfixable, because there was no way to
convert between the axes without the geometry.

Gaze and target x are normalised by screen width and y by screen height. The
aspect ratio is 0.5625 and no code rescales one onto the other. Any
two-dimensional distance therefore adds two different units.

The clearest illustration is in the pursuit stimulus itself. The Lissajous
amplitudes are recorded as x = 0.298, y = 0.400, which makes the vertical
excursion look the larger of the two. In degrees they are 12.65° and 9.62°: the
vertical excursion is the *smaller*. The normalised representation inverts the
ratio.

**Affected**

- `scanpath` and `bcea`, 2 of the 9 free-viewing trial measures and 2 of the 7
  contrast measures. A bcea in these units is a product of screen widths and
  screen heights, not an area in deg².
- The two-dimensional pursuit `rmse`.
- `_catch_up`, whose eye and target speeds are the `hypot` of both axes, and
  whose 0.35 threshold is therefore expressed in the mixed metric.
- The I-DT criterion. The detector applies the same 0.025 to each axis
  independently, so the vertical criterion is 0.607° — 1.8× stricter than the
  horizontal. A fixation drifting vertically is cut into more pieces than the
  same drift horizontally.

**Not affected** — checked, not assumed

- Every AOI quantity, including the eyes-versus-mouth contrast that is the
  headline validity result. `build_stimulus_aois` works in pixels, the
  interocular scaling is a pixel distance, and the region tests are per axis.
- The fixation-cross drift correction, a per-axis median.
- `position_gain_x/y`, `corr_x/y`, `rmse_x`, all single axis.
- `_velocity_gain`, computed on x alone.

**Effect on the Goal 2.10 result: none.**

It distorts the metric of five features; it does not confound them. Every
recording used the same 1920×1080 stimulus, so the distortion is identical for
every subject on every device. It cannot align with acquisition site the way the
vertical gaze offset did — that is the failure mode that mattered here, and this
is not an instance of it. It cannot have manufactured the null, and it cannot
have hidden a signal that the many unaffected features would not also carry.
**0 of 576 stands.**

The correction is worth making because it changes what the numbers *mean*, not
because it changes the decision.

---

## 5. What the document makes newly possible

1. **Report in degrees.** Fixation dispersion, saccade amplitude and gain,
   scanpath length, bcea, pursuit velocity in deg/s. This is what makes the
   numbers comparable to the literature the paradigm was drawn from, and it is
   what a reviewer will expect.
2. **Fix the anisotropy.** Multiply y by 0.5625 before any `hypot`. Small change,
   and now well-defined.
3. **Weight trials by CFAPS norms.** The document names the stimulus set as
   《中国面部情感图片系统》(CFAPS) outright, where `spec_version` 1 could only infer
   "CFAPS-style" from the filename codes. CFAPS ships per-image normed valence
   and arousal ratings. This analysis currently weights every sad face equally.
   Obtaining that norm table would allow trials to be weighted or covaried by
   rated intensity. Whether that helps is an open question — it does not address
   the reliability collapse, which is driven by having only 12 trials per
   valence, and it would add an analytic degree of freedom that must be
   pre-registered rather than tried.

---

## 6. Verdict

The reverse-engineered paradigm was correct. Every timing, count, balance and
structural claim in `configs/goal2_10/eye_paradigm_spec.yaml` is confirmed by a
document written independently of it, including the two that had been fixed
mid-analysis after producing implausible results — the 8 saccade trials and the
blocked structure of the pursuit task.

The document corrects one descriptive error that reached no feature, unlocks a
unit system that was previously unavailable, exposes one real metric defect that
cannot have affected the conclusion, and reveals that a third device's cohort is
named in the study protocol but absent from the delivered data.

**The Goal 2.10 conclusion is unchanged: 0 of 576 increments over demographics
credited, all twelve device × task units `NO_INDEPENDENT_SIGNAL`.** The
reliability finding that governs its interpretation is also unchanged and is now
better grounded: the document confirms 12 trials per valence, which is the
reason the valence contrast has no measurable reliability, and therefore the
reason a null on it is evidence about this paradigm rather than about
attentional bias as a construct.

No re-extraction is required to defend the result. A re-extraction with the
anisotropy fixed and features reported in degrees would improve the write-up and
is worth doing before any external submission; it is not worth doing to check
the answer.
