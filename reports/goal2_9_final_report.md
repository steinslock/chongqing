# Goal 2.9 Final Report: Behavioural Features

Date: 2026-09-08

Goal 2.8 rebuilt every neural feature layer and found no increment over
demographics. It never measured what the subject actually did. Every fNIRS task
that takes a keypress wrote a trial-level log next to the recording, and no
earlier goal read any of it. Goal 2.9 reads those logs.

This report records what was measured. It does not issue a go/no-go decision.

## What Changed and What Did Not

Unchanged: the fixed Standard and Group-aware five-fold splits, three-fold inner
CV for hyperparameters and thresholds, the Logistic Regression / Random Forest /
HistGradientBoosting families and their grids, 1000-resample subject bootstrap
CIs and 1000-resample paired increment tests, and the exclusion of the
baseline-exposed pilot holdout.

Changed: one new feature layer. Trial structure, column names, condition coding
and every known log defect now live in the `behaviour:` section of each fNIRS
task in `configs/goal2_8/paradigm_spec.yaml`, alongside the neural structure the
same file already carried, each value naming its source.

Added: one decision rule. See *The Positive Result and Why It Was Withdrawn*.

## The Logs

| device | task | subject dirs | trials | response rate | usable |
|---|---|---|---|---|---|
| yiruid | 1back | 1821 / 1825 | 30 (2 x 15) | 0.93 median | yes |
| yiruid | oddball | 701 / 701 | 300 (10 x 30) | 0.167, exactly the target proportion | yes |
| yiruid | doors | 1089 / 1089 | 60 (6 x 10) | 0.38 | sensitivity only |
| bikom | 1back | 1271 / 1272 | 30 (2 x 15) | 0.93 median | yes, minus 50 subjects |
| bikom | oddball | 644 / 644 | 250 (5 x 50) | 0.01 | **no** |
| bikom | doors | 644 / 649 | 60 (6 x 10) | 1.00 median | yes |

VFT has no behavioural log: its responses are spoken and were never scored.
Rest takes no response.

### Four defects found in the logs

**Bikom Oddball never collected the keypress.** `Slide3` logs RT, RESP, ACC and
CRESP on all 250 trials, but RESP is empty for 549 of 640 subjects and the
target hit rate is exactly 0.0 for 610 of them. `Slide3.CRESP` is empty even on
target trials, so E-Prime scores every target as an error and every standard as
a correct rejection. The vendor's own reference run,
`附件/必可明范式_eprime/oddball/oddball-1-1.txt`, logs 0 responses over 50
trials. This is a property of the build, not of the subjects. No feature is
derived for this unit.

**Yiruid Doors truncates its response window.** `task_resp` runs from 0.0 s to
1.0 s while the door image is on screen from 0.5 s to 4.5 s, so a choice made
more than 0.5 s after the doors appear is never recorded. The same task on Bikom
has a 4 s window. The two devices side by side:

| | Yiruid, 1 s window | Bikom, 4 s window |
|---|---|---|
| response rate | 0.383 | 0.983 |
| median RT | 0.786 s | 0.765 s |
| median max RT | 0.962 s | 2.884 s |
| median RT skew | **-0.65** | **+1.31** |
| usable win-stay pairs | 6 | 24 |

The median RT is the same on both devices: the fast tail is real. Everything
past 1 s is missing on Yiruid, which turns a right-skewed RT distribution into a
left-skewed one and leaves a quarter of the choice pairs. Yiruid Doors is
therefore sensitivity-only and Bikom is the primary device for reward behaviour
— the reverse of the fNIRS signal, where Yiruid is primary and Bikom was
excluded.

**Fifty Bikom 1BACK subjects ran a build with no match trials.** Their condition
list contains no repeated stimulus at all: `YN` and `CRESP` are `{LEFTARROW}` on
all 30 trials and the stimulus-adjacency label is non-match everywhere. There is
no contrast to compute, so they are excluded rather than coerced. The other 1221
use the numeric coding, `YN` 1 for non-match and 2 for match.

**The block-initial trial carries a meaningless condition on Bikom.** It has no
predecessor, yet `YN` is 1 in 254 and 2 in 46 of 300 sampled blocks, and E-Prime
scores accuracy against it. The 1BACK condition is therefore derived from the
stimulus sequence rather than read from the log. On every non-block-initial
trial the two agree exactly, on both devices, with zero mismatches over the
sampled subjects; the per-subject agreement is recorded in QC and its median is
1.000.

### Two corrections to the paradigm specification

**Doors feedback code 1 is loss, not win.** `stim/1.png` is a red downward arrow
reading `-1` and `stim/2.png` is a green upward arrow reading `+2`, and the
identical pair appears as `1.jpg` / `2.jpg` in the Bikom stimulus set. An
earlier revision of the specification recorded `{1: win, 2: loss}` with amounts
`+50 元` / `-25 元`. No code had read it.

**`脑机接口.pdf` describes a Doors design that was not the one run.** It
specifies 3 blocks of 20 trials with mouse clicks and `+50 元` / `-25 元`
feedback. Both executed builds use 6 blocks of 10 trials, a keyboard 1/2 choice
and `+2` / `-1`. Recorded data is preferred, as the protocol requires, and the
PDF description is recorded as an antipattern.

## Features

| device | task | subjects | signal features |
|---|---|---|---|
| yiruid | 1back | 1412 | 38 |
| yiruid | oddball | 524 | 25 |
| yiruid | doors | 843 | 28 |
| bikom | 1back | 955 | 38 |
| bikom | doors | 515 | 28 |
| yiruid | combined | 342 | 91 |
| bikom | combined | 513 | 66 |

1BACK gives accuracy overall and per condition, hit and false-alarm rates,
d-prime and criterion, reaction-time central tendency, dispersion, skew and
range, the match-minus-non-match contrast, the block-2-minus-block-1 change, and
post-error slowing. Oddball gives hit and false-alarm rates, d-prime, criterion,
hit RT and its dispersion, and the vigilance drift across the ten blocks. Doors
gives win-stay, lose-shift, switch rate, feedback sensitivity, choice bias,
post-feedback RT and its win-minus-loss difference, and omission rates.

The QC table carries log integrity only — files found, trials found and
expected, block count, conformance, condition agreement. Response rate is task
performance and stays on the signal side, otherwise the `signal_qc vs qc`
comparison would be testing behaviour against behaviour.

## Validity, Independent of Any Label

The two devices are disjoint cohorts recorded on different hardware with
different log formats. They agree:

| | Yiruid 1BACK (n=1412) | Bikom 1BACK (n=955) |
|---|---|---|
| accuracy | 0.929 | 0.964 |
| d-prime | 2.57 | 2.95 |
| criterion | +0.25 | +0.19 |
| RT, correct | 0.657 s | 0.683 s |
| match minus non-match RT | -31 ms | -44 ms |
| post-error slowing | +98 ms | +121 ms |
| post-error slowing positive in | **76.5%** of subjects | **76.4%** of subjects |
| RT faster in block 2 in | **76.5%** of subjects | **76.5%** of subjects |
| condition agreement, median | 1.000 | 1.000 |

Post-error slowing and the block-2 speed-up replicate to within a tenth of a
percentage point across two independent cohorts and two independent readers.
Both are textbook effects. Yiruid Oddball is equally canonical: d-prime 4.53,
hit rate 0.99, false-alarm rate 0.004, hit RT 370 ms. Bikom Doors shows the
expected right-skewed RT distribution, a 0.98 response rate, and win-stay 0.46 /
lose-shift 0.55, with feedback sensitivity near zero, which is what a paradigm
whose feedback is predetermined and non-contingent should produce.

The behavioural measures are real and correctly read. The question is whether
they predict the label.

## Model Matrix

294 datasets across two CV protocols, 1708 pooled metric rows, 622,688
subject-level OOF predictions, 294 paired comparisons.

Best pooled AUROC by feature-set family, inner-CV thresholds:

| cohort | protocol | n | behaviour | demographics | site proxy | QC |
|---|---|---|---|---|---|---|
| yiruid 1back | standard_cv | 1412 | 0.5581 | 0.5959 | 0.6236 | 0.5081 |
| yiruid 1back | group_cv | 1412 | 0.5524 | 0.5838 | 0.5492 | 0.4653 |
| yiruid oddball | standard_cv | 524 | 0.5394 | 0.5676 | 0.6710 | 0.5063 |
| yiruid oddball | group_cv | 524 | 0.5086 | 0.5522 | 0.5863 | 0.5568 |
| yiruid doors | standard_cv | 843 | 0.5200 | 0.5897 | 0.6393 | 0.5006 |
| yiruid doors | group_cv | 843 | 0.5136 | 0.5863 | 0.5437 | 0.5764 |
| bikom 1back | standard_cv | 955 | 0.5499 | 0.6305 | 0.5995 | 0.5080 |
| bikom 1back | group_cv | 955 | 0.5229 | 0.6021 | 0.5840 | 0.5224 |
| bikom doors | standard_cv | 515 | 0.5379 | 0.5587 | 0.5816 | 0.4846 |
| bikom doors | group_cv | 515 | 0.5138 | 0.5388 | 0.4644 | 0.5016 |
| yiruid combined | standard_cv | 342 | 0.5852 | 0.5202 | 0.6691 | 0.5060 |
| yiruid combined | group_cv | 342 | 0.5338 | 0.4668 | 0.6035 | 0.5886 |
| bikom combined | standard_cv | 513 | 0.5609 | 0.5660 | 0.5752 | 0.5077 |
| bikom combined | group_cv | 513 | 0.5479 | 0.5314 | 0.4617 | 0.5265 |

Behaviour is above chance in every cohort and under both protocols, at 0.51 to
0.59, and below demographics in every cohort except the combined Yiruid one.
The acquisition-site proxy remains the strongest single predictor in most rows,
as it has been since Goal 2.7.

## Paired Increments

294 paired comparisons in all. The decision-relevant subset is the 168
increments **over demographics**; the remaining 126 are controls.

| comparison | rows | interval excludes zero, positive | credited | significantly negative |
|---|---|---|---|---|
| `signal_vs_demographics` | 42 | 3 | **0** | 15 |
| `signal_demographics_vs_demographics` | 42 | 2 | **0** | 3 |
| `signal_qc_demographics_vs_demographics` | 42 | 1 | **0** | 3 |
| `signal_qc_demographics_vs_qc_demographics` | 42 | 2 | **0** | 4 |
| **over demographics, total** | **168** | **8** | **0** | **25** |
| `signal_qc_vs_qc` (control) | 42 | 11 | — | 2 |
| `signal_demographics_vs_signal` (control) | 42 | 19 | — | 3 |
| `signal_qc_demographics_vs_signal_qc` (control) | 42 | 18 | — | 4 |

Across the 168 demographics increments the AUROC difference ranges from -0.1105
to +0.0889.

The control rows behave exactly as they should and are worth reading as a
sanity check. `signal_qc vs qc` is positive in 11 of 42 rows: behaviour carries
more than log completeness, as it must. `signal_demographics vs signal` is
positive in 19 of 42: adding age, sex and grade to behaviour helps. The reverse
direction, adding behaviour to demographics, is the one that does not.

| unit | rows | positive standard_cv | positive group_cv | uncredited | negative | decision |
|---|---|---|---|---|---|---|
| yiruid 1back | 24 | 0 | 0 | 0 | 3 | NO_INDEPENDENT_SIGNAL |
| yiruid oddball | 24 | 0 | 0 | 0 | 6 | NO_INDEPENDENT_SIGNAL |
| yiruid doors | 24 | 0 | 0 | 0 | 7 | NO_INDEPENDENT_SIGNAL |
| bikom 1back | 24 | 0 | 0 | 0 | 9 | NO_INDEPENDENT_SIGNAL |
| bikom doors | 24 | 0 | 0 | 0 | 0 | NO_INDEPENDENT_SIGNAL |
| yiruid combined | 24 | 0 | 0 | **8** | 0 | NO_INDEPENDENT_SIGNAL |
| bikom combined | 24 | 0 | 0 | 0 | 0 | NO_INDEPENDENT_SIGNAL |

## The Positive Result and Why It Was Withdrawn

The first run of the decision rule returned `INDEPENDENT_SIGNAL_SUPPORTED` for
the combined Yiruid cohort: 6 increments over demographics with intervals
excluding zero under Standard CV and 2 under Group CV, point estimates +0.079 to
+0.089, with all 24 of its rows positive in sign. That is what a real effect
looks like from the outside.

It is not one. **Every one of the eight beat a demographics baseline that was
itself below chance.**

| | full CV cohort (n=3597) | combined Yiruid cohort (n=342) |
|---|---|---|
| demographics AUROC, standard_cv | ~0.67 | 0.472 - 0.520 |
| demographics AUROC, group_cv | — | 0.429 - 0.467 |
| age range | 9 - 20, sd 2.38 | 12 - 20, sd 1.66 |
| univariate age AUROC | 0.620 | 0.549 |
| distinct site prefixes | 51 | 10 |
| label prevalence | 0.305 | 0.439 |

The combined cohort is the intersection of three Yiruid tasks, and Oddball is
the limiting one, so it is a restricted subgroup drawn from ten sites with its
age range compressed. That is the setting, but it is not the whole explanation:
demographics scores 0.51 to 0.55 on these very subjects when the model is
trained on a larger cohort, so the subgroup is not inherently
demographics-proof. What breaks is the fitting, not the people.

Behaviour's absolute AUROC in that cohort is 0.585 under Standard CV and 0.534
under Group CV — below the ~0.67 demographics reaches in the full cohort, and
below the 0.669 the site proxy reaches in this very cohort. The increment is
arithmetically real and substantively empty.

### The three checks that settle it

`scripts/verify_goal2_9_positive.py` reruns them; outputs are in
`results/goal2_9/positive_result_verification.json`.

**1. Transfer.** Score the same 342 subjects with the models trained on the
larger per-task cohorts, without refitting anything.

| models trained on | n | demographics | behaviour |
|---|---|---|---|
| yiruid 1back (1412 subjects) | 342 | 0.525 | 0.522 |
| yiruid oddball (524) | 342 | 0.511 | 0.537 |
| yiruid doors (843) | 342 | 0.507 | 0.545 |
| **yiruid combined (342)** | 342 | **0.484** | **0.573** |

Same people, same labels. The gap exists only when the models are trained inside
the 342-subject cohort. Trained on more subjects, demographics recovers to
0.51-0.55 on these very people and the gap disappears. So the effect is not a
property of this subgroup; it is a property of fitting on 274 training subjects.

**2. Pooling.** The zero-information model scores exactly 0.500 in every fold of
this cohort, yet its pooled AUROC is 0.404 under Standard CV and 0.347 under
Group CV. The Group CV folds hold 74, 169, 37, 55 and 7 subjects at prevalences
0.19 to 0.56. Pooling across folds that unbalanced pushes uninformative
predictors below chance mechanically, before any data is involved.

**3. Permutation.** Shuffle the diagnoses on this exact cohort, with its real 91
features and real folds, and refit. 100 permutations:

| | demographics | behaviour | gap | P(gap >= +0.079) |
|---|---|---|---|---|
| real labels, RF | 0.456 | 0.554 | +0.098 | — |
| real labels, HGB | 0.449 | 0.546 | +0.097 | — |
| shuffled, RF | 0.486, below chance in **58%** of runs | 0.500 | +0.014 (sd 0.067) | **17%** |
| shuffled, HGB | 0.481, below chance in **67%** of runs | 0.500 | +0.019 (sd 0.067) | **18%** |

With no signal whatsoever, this cohort produces a gap as large as the reported
one about **one run in six**, and it drives demographics below chance in the
majority of runs. The observed increment sits roughly 1.2 standard deviations
above the null mean. It is unremarkable noise.

Behaviour's own AUROC confirms it: in this cohort the bootstrap interval for the
behaviour model includes 0.5 in **5 of 6** model-by-protocol combinations. Only
Standard CV HistGradientBoosting excludes it, at [0.520, 0.645]. A predictor that
cannot be separated from a coin flip cannot carry independent signal.

### Why the paired interval missed it

The paired bootstrap resamples subjects. It measures how much the difference
would move if we had drawn different people, and it is blind to how much the
difference moves because the *fit itself* is unstable. In a 342-subject cohort
the demographics fit is unstable enough to land below chance, and a below-chance
comparator manufactures a positive difference that the interval then certifies
with a tight bound. The fold-direction check does not help either, because the
same unstable fit is unstable in the same direction in every fold.

### The rule that now closes it

A credited increment must beat a comparator that is itself above chance.
`results/goal2_9/required_increments.csv` carries `comparator_auroc`,
`comparator_above_chance` and `significant_positive_credited` for every row, and
a test constructs a comparator-at-chance win and asserts it is not credited.
Under the corrected rule, **0 of 168 increments over demographics are credited**.

Beyond that, any credited increment from a cohort under about 500 subjects must
be verified by label permutation before it is reported. That check is now a
script, not a habit.

This is the second time this project has caught a decision rule crediting the
wrong thing. Goal 2.8's first rule credited Face for beating a background
control; this one credited behaviour for beating a broken baseline. Both were
found by looking at which rows were positive rather than at the count.

## What This Adds to the Picture

Behaviour is the fourth feature layer to return no increment over demographics,
after EEG, fNIRS and Face. It is not a null result of the same kind, and the
difference is worth stating precisely.

The measures are demonstrably valid. Post-error slowing replicates at 76.5% in
both cohorts, d-prime is 2.6 to 4.5, the effects are textbook. They carry
univariate label information: reaction-time dispersion reaches AUROC 0.55 to
0.57, more than the Bikom fNIRS features ever did. What they do not do is add
anything over age, sex and grade.

Part of the reason is visible directly: behaviour correlates with age. RT
standard deviation and IQR reach Spearman rho of -0.22 with age, RT means -0.18,
Oddball d-prime +0.18. Older adolescents are faster, less variable and more
sensitive. So is the part of the behavioural signal that tracks the label. That
is a developmental effect that age already captures, which is exactly what the
increment-over-demographics test is designed to detect and discount.

## Constraints That Still Hold

- The pilot holdout is baseline-exposed. This dataset cannot produce a final
  validation, and any positive finding would need an external cohort.
- Acquisition site remains the strongest single predictor in most rows.
- The two fNIRS device cohorts are disjoint, so device and site cannot be
  separated, and that applies to the behavioural logs as well.
- Bikom Oddball behaviour and Yiruid Doors choices are lost to paradigm
  implementation defects. Both are recoverable in principle by a future
  acquisition; neither is recoverable from this archive.

## Reproducibility

Single environment `chongqing_v1`; `source activate.local.sh`.

```
python scripts/extract_behaviour_goal2_9_features.py --n-jobs 16
python scripts/run_goal2_9.py --n-workers 24
python scripts/summarize_goal2_9.py
python -m unittest discover -s tests
```

182 unit tests pass. All feature tables and OOF predictions contain only
`split_group == cv` rows with zero pilot-holdout subjects. The split files are
byte-identical to their committed state.

Machine-readable outputs are under `results/goal2_9/`, including
`required_increments.csv` and `unit_decision.csv`.
