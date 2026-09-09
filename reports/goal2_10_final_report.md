# Goal 2.10: The Eye-Tracking Feature Layer

Date: 2026-09-09
Status: measurement complete. No go/no-go decision is issued here; that remains
open, as it has since Goal 2.8.

Goal 2.10 adds eye tracking, the last objective modality no earlier goal used.
It changes nothing else: the same fixed Standard and Group-aware folds, the same
three-fold inner CV, the same three model families and grids, the same
1000-resample subject bootstrap and paired tests, the same pilot-holdout
exclusion, and the Goal 2.9 rule that a credited increment must beat a
comparator that is itself above chance.

Before any of it was modelled, the literature it would rest on was reviewed and
a method was written down together with its predictions, in
`reports/goal2_10_eye_method_design.md`. This report records what happened.

## Result

**Over the 576 increments over demographics, 0 are credited.** Eighteen
intervals excluded zero on the positive side; every one of them beat a
demographics baseline that was itself below chance. 152 were significantly
negative. All twelve `device x task` units return `NO_INDEPENDENT_SIGNAL`.

Eye tracking is the fifth feature layer to return no increment over
demographics, after EEG, fNIRS, Face and behaviour.

The eighteen uncredited positives share a signature that is worth stating,
because it is the same one Goal 2.9 had to withdraw a result over. All eighteen
are Group CV, all eighteen are `qixin_120` cohorts, and their comparator AUROC
runs 0.435 to 0.467. The demographics baseline in that device's cohorts is
0.555 to 0.563 under Standard CV and falls to 0.435 to 0.462 under Group CV,
while `qixin_500` holds 0.657 to 0.678 and 0.643 to 0.659 across the two
protocols. A baseline that collapses under one protocol manufactures a positive
difference that the paired interval then certifies with a tight bound. The rule
that a comparator must be above chance blocked every one of them, without
touching any comparison where the baseline was working.

## What the modality is, as recovered

At the time this analysis was run, `附件/` held paradigm scripts for EEG, fNIRS
and Face and nothing at all for eye tracking, so
`configs/goal2_10/eye_paradigm_spec.yaml` was recovered from two recorded
sources that agree with each other: the archived stimulus media and the
recorded presentation timelines.

> **Added 2026-09-09.** The hospital subsequently supplied
> `附件/重医眼动范式及参数.docx`. It confirms the recovery on every quantity it
> states — all three trial structures, the 12/12/12 valence balance, the 8
> saccade trials, and the three pursuit trajectories with fast at exactly twice
> slow — including the two that had been corrected mid-analysis after producing
> implausible results. It also corrects one descriptive error that reached no
> feature, supplies the viewing geometry that lets every measure be expressed
> in degrees, and exposes one metric defect that cannot have affected this
> result. **The conclusion below is unchanged.** See
> `reports/goal2_10_paradigm_document_review.md`.

Three devices recorded the same three tasks on near-disjoint cohorts: Tobii Pro
Nano at 60 Hz, 七鑫易维 at 120 Hz and 七鑫易维 F500 at 500 Hz. Only two subjects
appear under more than one, and each device owns a distinct set of `A_id` site
prefixes, so device and acquisition site cannot be separated. Units are
`device x task` and raw features are never merged across devices, exactly as
for the two fNIRS devices.

- **自由观看**: 36 trials of fixation cross 1.0 s, one CFAPS-style greyscale
  face 4.0 s, blank 1.0 s. Valence and sex fully crossed, 12 happy, 12 sad, 12
  neutral, 18 male, 18 female. Presentation order is fixed and identical for
  every subject.
- **扫视**: prosaccade instruction, 10 s practice, 20 s formal, then the same
  for antisaccade. Each formal block holds exactly **8 trials**, first onset
  1500 ms, period 2500 ms, target on 1000 ms, four leftward and four rightward,
  four small and four large.
- **平滑追随**: six 21 s sinusoidal blocks separated by 2 s gaps, three
  conditions repeated twice: horizontal at 0.381 Hz, a 3:4 Lissajous at
  0.143/0.190 Hz, and the same Lissajous at exactly double those frequencies
  and the same amplitude.

Coverage is far larger than the manifest records. `has_eye_direct` counts 281
subjects because `chongqing_binary.audit._extract_l_ids` greps paths for `L\d+`
and no eye path carries one; they carry `A_id`. Joining on `A_id` finds 1187
subjects, **919 of them in the development split**, across 3481 recordings.

## Four defects found, none of which announced itself

Every one was found by asking whether a result matched something already known,
not by an error message.

1. **Tobii `Recording timestamp` is in microseconds** while `Recording
   duration` is in milliseconds.
2. **The 七鑫易维 sample clock is not the presentation clock.** On F500 the
   samples span about 0.4 percent longer than the recorded `duration`, a 300 to
   400 ms drift by the end of a 136 s block. Uncorrected, the pursuit
   gaze-target correlation reads 0.64 to 0.72; mapped onto the presentation
   clock it reads 0.935, and the residual lag falls to the ordinary
   physiological 100 to 150 ms.
3. **All three trackers report gaze below the true fixation point**, by a
   device-dependent amount: +0.015 of screen height on Tobii, +0.056 at 120 Hz,
   +0.052 on F500. The eye and mouth bands are each about 0.10 of screen height,
   so uncorrected the eye-minus-mouth contrast reads -0.103 and -0.145 on the
   two 七鑫易维 devices against +0.245 on Tobii: the universal rule that people
   look at eyes more than mouths reverses. Since device is collinear with site,
   that would have entered a model as a site shortcut wearing the clothes of a
   behavioural finding. The paradigm supplies its own correction, a 1 s fixation
   cross before every trial; after it the three devices read +0.362, +0.339 and
   +0.269 and the between-device spread falls from 0.390 to 0.093.
4. **Catch-up saccades cannot be counted with a dispersion detector.** During
   pursuit the eye moves smoothly, so I-DT merely chops that motion at its
   threshold and the resulting rate tracks eye speed. That version reported the
   highest rate in the slowest condition, the reverse of what catch-up saccades
   do, which is how it was found. Replaced by a velocity-residual detector:
   1.23, 1.26 and 1.84 Hz across horizontal, slow and fast, with `fast minus
   slow` positive in 92 percent of subjects.

The third is the one worth carrying forward. The Step 1 face-box check passed
with the offset in place, at 18 times its area share on every device, because
the face box is symmetric about screen centre. **A coarse validity check that
passes is not evidence that the coordinate frame is right.**

## Label-free validity, which all of it passes

Nothing here reads a label. Each expectation is fixed by physiology or by the
paradigm, so a failure would mean a parsing problem rather than an absent
effect. Median over all recordings:

| check | tobii | qixin_120 | qixin_500 |
|---|---|---|---|
| dwell inside the stimulus face box, over its 0.053 area share | 18.6x | 18.3x | 18.4x |
| eye-region dwell minus mouth-region dwell | +0.362 | +0.339 | +0.269 |
| prosaccade gaze-target correlation | 0.822 | 0.771 | 0.756 |
| antisaccade gaze-target correlation | -0.614 | -0.552 | -0.531 |
| pursuit gaze-target correlation | 0.971 | 0.942 | 0.935 |
| prosaccade latency (ms) | 177 | 235 | 261 |
| antisaccade latency (ms) | 278 | 348 | 351 |
| antisaccade minus prosaccade latency (ms) | +100 | +107 | +86 |
| prosaccade saccade gain | 1.007 | 1.015 | 1.019 |
| antisaccade corrected-error rate | 1.000 | 1.000 | 1.000 |

Three of these deserve comment.

The **inhibition cost** replicates within 21 ms across three devices while
absolute latency differs by 84 ms between them. Absolute latency is not
comparable across these devices; the within-subject contrast is. That is the
reason the contrast exists.

**Mouth dwell is highest for happy faces** on all three devices, 0.231, 0.242
and 0.262, against 0.121, 0.124 and 0.144 for neutral. The smile is the
diagnostic feature of a happy expression, so this is an expected effect
recovered independently three times, and it validates the whole
valence-to-region chain.

**Pursuit degrades with target speed** in the right direction on every measure:
`fast minus slow` gives RMSE +0.014 positive in 83 percent of subjects, smooth
fraction -0.055, catch-up rate +0.53 Hz positive in 92 percent.

## The measurement result that decides how to read the null

Free viewing carries 121 features in two blocks whose reliability differs by an
order of magnitude. Odd-even split half, Spearman-Brown corrected, on 249 to
322 subjects per device:

| block | features | median | above 0.5 on all three devices |
|---|---|---|---|
| absolute per-valence measures | 75 | 0.698 | **53** |
| valence contrasts | 46 | -0.051 | **0** |

The best contrast reaches 0.326. Thirty-three of the 46 have a negative median.
The cause is arithmetic: each contrast is a difference of two means estimated
from 12 trials each, which keeps both errors and cancels the shared true
variance. This is the difference-score reliability collapse the attentional-bias
literature reports, replicated here on three devices independently.

The consequence is not a caveat, it is the interpretation:

- The two blocks entered the matrix as separate declared feature sets, because
  mixing 46 unreliable columns into 75 informative ones would have depressed the
  free-viewing result for a reason unrelated to signal. This project has already
  measured that dilution.
- **A null on the contrast block is evidence about this paradigm, not about
  attentional bias as a construct.** The valence contrast was the primary
  theoretical motivation for the entire free-viewing analysis, and it is not
  measurable at 12 trials per valence. Reporting its null as evidence against
  the construct would be wrong.

The absolute block, which is measurable, also returns nothing: 0 credited
increments.

## Controls behave as controls

- `signal_qc vs qc`: 6 of 72 positive, 8 negative, median +0.005. The eye
  features carry essentially nothing beyond acquisition quality, and the signal
  block's own median AUROC, 0.510, is indistinguishable from the QC block's
  0.508.
- `signal_demographics vs signal`: 21 of 72 positive, 2 negative, median +0.025.
  Adding demographics to eye features helps.
- Adding eye features to demographics **lowers** AUROC in 74 percent of rows,
  median -0.039. That is the dilution this project documented in the
  demographics re-verification, not damage done by the features.
- The site proxy alone reaches 0.589 under Standard CV and 0.420 under Group CV,
  which is Group CV working as designed.

## What this adds to the picture

Eye tracking arrived with the strongest prior of any layer in this project. It
was the only paradigm here with a balanced within-subject valence contrast, the
literature gives it medium meta-analytic effects where EEG and fNIRS gave
little, and every label-free validity check passes on all three devices with
textbook values. It still returns nothing over age, sex and grade.

Three things separate this null from the earlier ones.

**It is the first null where the primary construct was shown to be unmeasurable
rather than merely unrewarding.** The valence contrast fails on reliability
before it ever reaches a model. Goal 2.9's behavioural measures were valid but
uninformative; this one is partly invalid, and the report says which part.

**It is the first null with three independent devices.** EEG had one, fNIRS had
two on disjoint cohorts, Face had one. Here the same three tasks were recorded
by three trackers at three sampling rates on three near-disjoint cohorts, and
the validity checks agree while the label increments agree in returning nothing.
A parsing artefact would be unlikely to survive that.

**The decision rule earned its keep for the second time.** Eighteen intervals
excluded zero, all against a baseline below chance, all in the one device whose
demographics fit collapses under Group CV. Without the Goal 2.9 rule this would
have been reported as `qixin_120` showing independent eye-tracking signal in
three of four cohorts.

## Constraints that still hold

- The pilot holdout is baseline-exposed. This dataset cannot produce a final
  validation, and any positive finding would need an external cohort.
- Device is collinear with acquisition site for eye tracking as it is for fNIRS,
  so no cross-device pooling is possible and no device effect can be separated
  from a site effect.
- Every eye cohort holds 247 to 336 subjects, all below the 500 at which this
  protocol requires label-permutation verification of any credited increment.
  None was credited, so none was needed.
- Velocity-derived features are unavailable at 60 Hz and, as measured across
  seven smoothing windows, remain sampling-rate dependent at 120 and 500 Hz.
  Position gain is the rate-robust measure.
- Each saccade block holds 8 trials, so its error rate has a resolution of 0.125
  and is not comparable with the 40 to 100 trial batteries the literature
  reports.

## Reproducibility

Single environment `chongqing_v1`; `source activate.local.sh`.

```
python scripts/audit_eye_readiness.py --n-workers 48
python scripts/extract_eye_goal2_10_features.py --n-jobs 32
python scripts/run_goal2_10.py --n-workers 24
python scripts/summarize_goal2_10.py
python -m unittest discover -s tests
```

237 unit tests pass, 55 of them new for this stage. 600 datasets, 518,592 OOF
prediction rows, 3504 pooled metric rows, 864 paired comparisons. All feature tables and OOF predictions are CV-only with zero
pilot-holdout rows. The split files are unchanged.

Machine-readable outputs are under `results/goal2_10/`, including
`required_increments.csv`, `unit_decision.csv` and
`free_viewing_reliability_summary.csv`. The readiness audit is
`reports/eye_readiness_audit.md` and the pre-registered design is
`reports/goal2_10_eye_method_design.md`.
