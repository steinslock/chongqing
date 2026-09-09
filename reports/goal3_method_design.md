# Goal 3 Method Design and Pre-Registration

Written 2026-09-09, **before any model was trained**, in the same spirit as
`reports/goal2_10_eye_method_design.md`. Everything below — the representations,
the architectures, the splits, the decision rule, the positive controls and the
numbered predictions — is fixed at the time of writing. Any later change is
recorded as an amendment with its date and its reason, and an amendment made
after seeing a label-related result is disclosed as such.

## 1. Status

```
CONDITIONAL_GO_FOR_GOAL3_EEG_REPRESENTATION_BENCHMARK
issued 2026-09-09
```

Scope is **EEG Oddball only**. fNIRS, Face, eye tracking, behaviour and
multimodal fusion keep the Goal 2.8 gate and are not touched.

## 2. Why this stage exists

Goal 2.8 rebuilt the Oddball from raw BDF with both conditions and measured 321
hand-crafted ERP and spectral features against the label. Over 72 required EEG
increments, none was positive and 43 were significantly negative. That is a
result about **features**, not about the recording.

Three things are true at once, and Goal 3 exists in the gap between them:

- the measurement is good. The target-minus-standard difference wave over 1820
  subjects peaks at Pz at **+6.43 uV** in 0.28-0.55 s with **Cohen d = 1.08**,
  positive in **88.7 percent** of subjects, parietal maximum, Fz negative at
  -2.48 uV. This is a textbook P3b and it is not in dispute;
- the hand-crafted representation of that recording carries no increment over
  age, sex and grade;
- **the correctly recovered Oddball has never been given a deep model under a
  protocol this project would accept.** The v1 EEGNet and InceptionTime runs
  reached 0.528 and 0.515 on Oddball, but they read a cache built with a
  hardcoded `event_codes: ["22"]`, so the standard condition was absent
  entirely, and they used a different split, a different stopping rule and a
  window-level rather than subject-level protocol. They are historical
  reference. They are not evidence about Goal 3 and are never compared against
  a Goal 3 number statistically.

So the question Goal 3 asks is narrow and answerable:

> In the correctly recovered Oddball target and standard trials, is there a
> learnable spatio-temporal pattern that the hand-crafted features did not
> capture, and does it carry information independent of age, sex and grade?

## 3. The three questions

**Q1. Does EEG carry a reproducible label signal on unseen subjects?**
Deep EEG must beat chance on held-out subjects under both CV protocols. Beating
chance is necessary and nowhere near sufficient, because demographics alone
reaches 0.598-0.604 in this cohort.

**Q2. Is the deep representation better than the Goal 2.8 hand-crafted one?**
Identical subjects, identical folds, identical protocol. This is the question of
whether deep learning is *necessary*, and it is answered symmetrically: see
section 9, both representations pass through the same stacking so they enter the
comparison with the same dimensionality.

**Q3. Does EEG add anything over `age + sex + grade`?**
`Demo + EEG` against `Demo`. **This decides go/no-go.**

## 4. Data, and the measurement gate

Goal 2.8 epoched correctly and then kept only the condition averages, so the
single trials do not exist on disk. Goal 3 rebuilds them from raw BDF with
`configs/goal2_8/eeg.yaml` **unchanged**: linked-mastoid A1/A2 reference, 0.1-40
Hz FIR, resample to 250 Hz, epoch -0.2 to 0.8 s, baseline -0.2 to 0 s, 150 uV
peak-to-peak rejection with Fp1/Fp2 excluded from the rejection decision,
`min_trials` 20 standard and 5 target. No filter, reference, window or rejection
setting is re-opened. If one ever were, the reason would have to be stated, shown
not to depend on any label result, and the Goal 2.8 version kept as reference.

**The gate is numerical identity, not a qualitative check.** Averaging the new
trial cache by condition must reproduce `artifacts/goal2_8/eeg/oddball_erp.npz`
element-wise, over exactly the same subject set, to a tolerance of 1e-10 V. The
tolerance is set at that value because Goal 2.8 stored the averages as float32
and the observed residual on a six-subject pilot was 5.5e-12 V, which is the
float32 representation limit for signals of this size and four orders of
magnitude below the tolerance, which is itself five orders below the 6.4 uV
effect being measured.

The second layer is the paradigm effect recomputed from the trials themselves:
parietal maximum, Fz negative, Pz P3b with Cohen d above 0.8 and above 80
percent of subjects positive.

A failure at either layer stops Goal 3. It is not worked around. This is the
same rule that Goal 2.7 violated on EEG and fNIRS, and the reason those
conclusions had to be withdrawn.

## 5. Cohort

Exactly the Goal 2.8 Oddball cohort, taken from its own index file rather than
re-derived, so the comparison is exact by construction and cannot drift:

| | |
|---|---|
| subjects | 1820, all `split_group == cv` |
| pilot holdout | 0 rows, excluded throughout |
| label prevalence | 0.335 |
| age | 14.75 mean, 10-20 |
| sex | 1179 female, 640 male, 1 missing |
| grade levels | 10 |
| acquisition site prefixes | 10 |
| trials | 237,774; 108.7 standard and 21.9 target per subject on average |
| Standard CV folds | 357 / 367 / 368 / 363 / 365 |
| Group CV folds | 457 / 430 / 399 / 255 / 279 |

Every model in Goal 3 — EEG, demographics, traditional features, and every
combination — is fitted and evaluated on these same 1820 subjects and these same
folds. The full-development-cohort demographics reference of 0.643-0.671 is a
different cohort and is never compared against a Goal 3 number.

The exact-cohort demographics comparator is above chance under both protocols
(Standard 0.598-0.604, Group 0.580-0.593), so the Goal 2.9 rule that a credited
increment must beat an above-chance comparator is satisfiable here. It is still
checked and reported per row.

## 6. How the Oddball enters the model

Four representations, each answering a stated question. They are not four
attempts at the same thing.

**A. Target-only.** Does the response to the rare stimulus itself carry label
information? This is the closest setting to the old v1 cache and is the
historical connection.

**B. Standard-only.** The control that decides how A is read. If B performs like
A, then whatever is there is not deviance processing but general EEG individual
difference, and no claim about oddball or P3b may be made from it.

**C. Condition-aware target + standard.** *The primary representation.* One
shared encoder embeds every trial; a condition embedding is added so the encoder
knows which condition a trial belongs to; the subject representation is
`[pool(target), pool(standard), pool(target) - pool(standard)]`. The model
therefore has access to the *relation* between a person's target and standard
responses, not merely to general EEG appearance.

**D. Difference-wave deep control.** Subject-level `ERP_target - ERP_standard`,
one 32 x 250 image per subject, into the same architectures. Low noise, no
trial-level variability. If the single-trial models do not beat D, then whatever
they achieve does not come from trial-level variability, and the extra machinery
is not earning its place.

## 7. Architectures

Three, each with a different inductive bias, each answering a representation
question. This is deliberately not an architecture search: no model is added
after results are seen, and if two of them agree closely no fourth is
introduced to break the tie.

| model | inductive bias | question it answers |
|---|---|---|
| **EEGNet** | temporal convolution then depthwise spatial filters, the learned analogue of CSP/ICA | the standard compact EEG deep baseline, and the rebuilt historical link |
| **InceptionTime-1D** | multi-scale temporal convolution, channels mixed at the input | is the information mainly in temporal shape? |
| **compact EEG-Conformer** | convolutional tokeniser then a small self-attention stack over time | long-range temporal dependence, which neither of the other two has |

Subject pooling is `mean + std` by default for all three. Attention pooling is
declared as **one** variant on the primary architecture only. No MIL model is
built before simple aggregation has been shown to be insufficient.

Hyperparameters are **fixed and declared in advance**, from each architecture's
source defaults, and are not selected against any disease-label criterion. Their
trainability — learning rate, schedule, epoch budget — is confirmed once on the
label-free condition-decoding control of section 10 and then frozen. Tuning on a
label-free paradigm quantity is the same standard this project already applies
to validity checks before modelling.

## 8. Splits, and the leak this design exists to avoid

The unit is the subject. The outer splits are the project's fixed files and are
not regenerated. Both protocols are co-primary and neither may inform the other.

The important structure is **inside** outer-train, and it is three levels deep,
not two:

```
outer fold (fixed split file)
├── outer-train  ~1456 subjects
│   └── inner 3-fold, subject-level, stratified, fixed seed
│       ├── inner-fit-pool  2/3 of outer-train  (~971)
│       │   ├── fit subset       80%  (~777)  -> gradient updates
│       │   └── stopping subset  20%  (~194)  -> early stopping, and nothing else
│       └── inner-val      1/3 of outer-train  (~485)
│                                              -> honest inner-OOF, and nothing else
└── outer-val   ~364 subjects  -> mean of the 3 inner models; never touched
```

The reason for the third level is a leak that the obvious two-level design
contains. If early stopping is monitored on the same inner-val fold that
produces the inner-OOF prediction, then that prediction is read at an epoch
chosen to be good on exactly those subjects. The inner-OOF `p_EEG` is then
optimistically biased, the meta model of section 9 learns its weight on an
inflated column, and at outer-validation time it meets an honest one. Train and
test would come from different distributions and the increment would be
distorted in a direction that is not predictable in advance.

So: **the stopping subset makes every training decision; inner-val makes none.**
Inner-val exists only to produce out-of-fold scores, and the threshold selected
from them.

The cost is that each inner model fits on about 53 percent of outer-train
instead of 67 percent. That is the correct price.

Outer-validation prediction is the **mean of the three inner models**, not a
separately trained full-outer-train model. This is not a convenience: it is what
makes the meta model's training and test inputs come from one generating
process. It also means one training pass produces both.

Nothing anywhere is selected, stopped, thresholded or ranked on outer-val, and
the pilot holdout appears nowhere.

## 9. Subject-level learning, and the increment test

**Subject balance.** Labels are subject-level. Every training epoch draws a fixed
quota of target trials and a fixed quota of standard trials from every subject,
with replacement where a subject has too few, so neither the number of trials a
subject contributed nor the 22:109 condition ratio weights that subject.
Inference averages the subject score over repeated fixed-size draws. Trial count
and rejection rate are recorded and their correlation with the label is
reported, because a subject who moved more has fewer trials and a noisier score.

**The increment test is cross-fitted probability stacking, not concatenation.**
This project has measured that bolting uninformative columns onto demographics
costs 0.008 to 0.055 AUROC, so `[embedding, age, sex, grade]` versus
`[age, sex, grade]` cannot cleanly separate "EEG adds nothing" from "EEG diluted
the demographics". In the stacking design, if EEG is noise the second-stage
logistic regression gives it a weight near zero and `Demo + EEG` collapses onto
`Demo` instead of falling below it.

Within each outer fold:

1. the three inner models produce one honest inner-OOF `p_EEG` per outer-train
   subject, and their mean produces `p_EEG` on outer-val;
2. a demographics model is cross-fitted through the **same** inner folds,
   producing `p_Demo` the same way, so the two columns are comparable objects;
3. the Goal 2.8 traditional 321-feature block is cross-fitted through the same
   inner folds, producing `p_Trad`, so Q2 compares two scalars rather than one
   scalar against a 321-column block;
4. a logistic regression on the inner-OOF `[p_Demo, p_EEG]` is the meta model;
   the threshold comes from the inner-OOF meta scores;
5. outer-val receives `p_Demo`, `p_EEG`, `p_Trad`, `p_Demo+EEG`, `p_Demo+Trad`.

Embedding-level concatenation is also run and reported, as the auxiliary
evidence the earlier stages used, but it does not decide anything.

**Seeds.** Three per configuration. The paired bootstrap resamples subjects and
is blind to the instability of the fit, which is much larger for a deep model
than for the sklearn families. The primary score is the seed-averaged one and
the between-seed spread is reported next to it. A finding that appears in one
seed and not the others is not a finding.

## 10. Positive controls: the reason a null here would mean anything

Given Goal 2.8, the most likely outcome of Goal 3 is a null. A null is only
informative if the same pipeline can be shown to learn *something* from these
trials. Otherwise "EEG carries no disease information" is indistinguishable from
"our deep pipeline learns nothing".

This is the deep-model form of the rule Goal 2.10 established: a null on a
quantity the instrument cannot measure is evidence about the instrument, not
about the construct.

Same architecture, same aggregation, same splits, same protocol, different
target:

- **PC1, trial level: target versus standard.** The paradigm effect is d = 1.08
  at Pz alone, so a multivariate model must find it easily. Trained and tested on
  disjoint subjects. **This is a hard gate: below 0.70 AUROC, Goal 3 stops and
  the pipeline is debugged, and no label result may be reported.**
- **PC2, subject level: sex.** Reported, not gated.
- **PC3, subject level: age**, median-split for AUROC comparability and Spearman
  of the score with age.

PC2 and PC3 are deliberately not hard gates: making them gates would stop the
goal on a literature prior about how decodable sex is from a 1 s ERP epoch,
which is not something this dataset owes us. They are instead the calibration of
how much *subject-level* information this aggregation can extract at all. If PC1
is high while PC2 and PC3 sit at chance, the weak link is subject aggregation
rather than the trials, and that is itself a result worth reporting.

## 11. Shortcut probes, reported with the result and not in an appendix

Goal 2.7 established that the `A_id`-prefix acquisition-group proxy alone
reaches about 0.68 AUROC under Standard CV. A deep model looking at raw
microvolts can learn an amplifier, impedance or environment signature that is
site-specific, and since site is collinear with much else in this dataset, that
would look like signal.

- **Group decoding probe.** The EEG subject embedding is used to predict the
  acquisition group. Reported as balanced accuracy against its chance level and
  as one-vs-rest AUROC. This is a diagnostic, not a control feature set.
- **Amplitude ablation.** The primary setting applies **no** per-subject
  normalisation, which preserves true P3b amplitude and matches what the
  traditional features saw. The declared ablation applies per-subject per-channel
  robust z-scoring. A result that exists only unnormalised, and only under
  Standard CV, is amplitude/site shortcut and cannot support a go.
- Group-aware CV is co-primary throughout, as in every earlier stage.

## 12. Decision rule

Unchanged from the standing protocol, with one addition made necessary by
running more than one architecture.

**Confirmatory arm — one test, declared now.**

> EEGNet, condition-aware representation, no per-subject normalisation,
> seed-averaged, under **both** CV protocols:
> `p_Demo + p_EEG` versus `p_Demo`.

`INDEPENDENT_SIGNAL_SUPPORTED` requires all of: the paired subject-bootstrap
AUROC interval excludes zero; at least 4 of 5 folds positive; positive under
Group CV as well as Standard CV; the comparator above chance in that cohort and
protocol; and no dominant shortcut explanation surviving section 11. No
multiplicity correction is applied to this single pre-declared test.

**Exploratory arm — keeps the right to discover something.**

The other architectures and representations are not decoration and are not
barred from producing a finding; a design that can only confirm and never
discover would be unable to see a signal that only one inductive bias picks up.
The exploratory family is **enumerated in advance** in section 13 and is closed:
nothing is added to it later.

An exploratory row is credited as `EXPLORATORY_SIGNAL_REQUIRES_REPLICATION` when
it satisfies every confirmatory requirement above **and**, in addition:

- survives Benjamini-Hochberg FDR control at 0.05 across the whole enumerated
  exploratory family, using two-sided p-values derived from the paired bootstrap
  difference distribution;
- passes label permutation on that exact configuration, following the precedent
  of `scripts/verify_goal2_9_positive.py`.

That verdict is deliberately **not** a go. It is a discovery that needs
independent replication, and it is reported as one.

**Anything positive under Standard CV and absent under Group CV is
`shortcut-sensitive / non-robust` and cannot support either verdict.**

## 13. The enumerated exploratory family

Fixed at the time of writing; closed.

Architectures `{InceptionTime-1D, EEG-Conformer}` x representations
`{target-only, standard-only, condition-aware, difference-wave}`, plus EEGNet on
`{target-only, standard-only, difference-wave}`, plus the EEGNet condition-aware
attention-pooling variant, under both CV protocols, on the increment
`p_Demo + p_EEG` versus `p_Demo`. That is 8 + 3 + 1 = 12 configurations x 2
protocols = **24 exploratory increment tests**.

The amplitude ablation, the embedding-level concatenation, Q1 and Q2 are
reported but are not increment tests over demographics and are not part of this
family.

## 14. Predictions recorded before running

Scored explicitly in the final report, whether or not they hold.

1. **PC1 (target vs standard, trial level) reaches at least 0.85 AUROC.**
   A single channel already separates the conditions at d = 1.08.
2. **PC2 (sex) lands between 0.60 and 0.75**, PC3 (age, median split) likewise.
3. **EEG alone reaches 0.50 to 0.56** on the disease label under both protocols,
   that is, above chance but far below demographics at 0.58-0.60.
4. **The confirmatory increment interval includes zero**: no independent EEG
   signal over age, sex and grade.
5. **Deep does not beat traditional** once both are cross-fitted to a single
   score: the Q2 interval includes zero. If deep *does* win, the most likely
   reason is dimensionality rather than representation, which is exactly what
   the symmetric stacking is there to rule out.
6. **Standard-only performs like target-only**, so no deviance-processing claim
   will be available regardless of the label outcome.
7. **The acquisition group is decodable from the EEG embedding well above
   chance.** Site structure is in these recordings; the question is only whether
   the label result depends on it.

I expect to be right about 4. The design's job is to make me falsifiable if I am
not: the positive controls prevent a broken pipeline from masquerading as a
null, the symmetric stacking prevents dilution from masquerading as absence, and
the exploratory arm prevents a single architecture choice from hiding a real
effect.

## 15. What would change the conclusion

- PC1 below 0.70: the pipeline is wrong; no label conclusion is reported at all.
- Confirmatory increment positive under both protocols, comparator above chance,
  group probe not dominant, ablation stable, permutation clean: that is a go, and
  I will have been wrong about prediction 4.
- Exploratory rows positive only under Standard CV, or only unnormalised, or
  only in one seed: shortcut-sensitive, reported as such, no go.
- Everything null with PC1 high: the strongest form of this null, because the
  instrument is demonstrably able to learn from these trials.

## 16. Amendments

Both were made on 2026-09-09, after the trial cache was built and verified but
**before any model was trained**, and both rest on quantities measured without
consulting any label. They are recorded here rather than folded silently into
the design.

### Amendment 1: the deep model reads 30 channels, not 32

Fp1 and Fp2 are excluded from the model input. The cache still holds all 32 and
is byte-for-byte the Goal 2.8 measurement; this is a model-input choice.

Goal 2.8 set `reject_exclude_channels: [Fp1, Fp2]` deliberately, because blinks
dominate the frontopolar channels and a shared threshold rejected 65 percent of
1BACK epochs. The consequence, which Goal 2.8 never had to face, is that its
150 uV peak-to-peak bound constrains every channel *except* those two. Measured
over all 237,774 trials:

| | max abs amplitude |
|---|---|
| every channel except Fp1/Fp2 | **144.5 uV** |
| Fp1 | 10,673 uV |
| Fp2 | **118,990 uV** |

All fifty of the highest-amplitude subjects peak on Fp1 or Fp2. Goal 2.8 was
insulated because its ERP features read only `[Pz, Cz, CP1, CP2, P3, P4]`; a
network handed the raw array unnormalised is not, and its first convolution and
batch statistics would be set by blink amplitude on two channels rather than by
brain activity on thirty.

Frontal coverage is kept through Fz, F3, F4, F7 and F8. The exclusion is applied
identically to every representation, architecture, seed and protocol, and no
label was consulted in making it.

A related observation, not acted on: after linked-mastoid referencing A1 and A2
carry the same values as each other, so two of the thirty inputs are redundant.
They are bounded and harmless, and removing them would be a further deviation
for no gain.

### Amendment 2: the identity gate is relative, not absolute

Section 4 declared an absolute tolerance of 1e-10 V from a six-subject pilot.
Measured on all 3640 subject-condition pairs, that was the wrong instrument.

Goal 2.8 stored its evoked arrays as float32, so the residual scales with the
amplitude of the recording. The relative residual `max|difference| /
max|reference|` lies between **3.4e-8 and 1.3e-7** across every pair, that is
within one float32 epsilon (1.19e-7), while the absolute residual spans 1.3e-13
to 2.4e-10 purely because one blink-contaminated recording is three orders of
magnitude larger than the rest. An absolute bound would have been a test of
amplitude rather than of identity, and the worst offender would have been the
subject with the largest blinks rather than any real disagreement.

The gate is therefore `max|difference| / max|reference| <= 4e-7`, about three
float32 epsilons. The observed maximum is **1.10 epsilons**, over 1820 of 1820
subjects, with zero mismatches.

### Amendment 3: the above-chance comparator rule applies to every comparison

Goal 2.9 introduced the rule that a credited increment must beat a comparator
that is itself above chance, and Goal 2.10 withdrew eighteen rows under it. The
rule was written for demographics comparators, and section 12 inherited it that
way.

Nothing in the argument is specific to demographics. The Q2 comparison
`p_EEG` against `p_Trad` has exactly the same failure mode: if the traditional
features fall below chance in a protocol, then "deep beats traditional" is a
statement about the traditional features rather than about the deep
representation. This project has twice been caught by the demographics form of
that mistake and should not walk into the Q2 form of it.

So `comparator_auroc` and `comparator_above_chance` are now recorded for **every**
paired comparison, not only the increments over demographics, and any claim that
one representation beats another is read against them.

The amendment was made on 2026-09-09 while the matrix was still running, from
the structure of the comparison rather than from a result. It makes the rule
stricter, never looser, and it cannot turn a null into a positive.

## 17. Gate results

Run 2026-09-09, before any model was trained.

**Identity.** 1820 of 1820 subjects, identical subject set, identical channel
names, identical time axis, zero mismatches, worst relative difference 1.10
float32 epsilons. The trials are the Goal 2.8 epochs.

**Paradigm validity, recomputed from the trials.**

| quantity | Goal 3 trials | Goal 2.8 report |
|---|---|---|
| Pz target-minus-standard, 0.28-0.55 s | **+6.426 uV** | +6.40 uV |
| Cohen d at Pz | **1.079** | 1.08 |
| subjects positive at Pz | **88.7%** | 88.1% |
| peak channel | **Pz** | parietal maximum |
| Fz | **-2.483 uV** | -2.45 uV |

Trial counts: 21.9 target per subject (5 to 29) and 108.7 standard (20 to 147),
237,774 trials over 1820 subjects.

**Both layers pass. Goal 3 proceeds to the positive controls.**

## 18. Compute

One environment, `chongqing_v1`. The models are small; the host's eight L40S are
heavily loaded by other users, so training takes whatever GPU memory is free and
falls back to CPU otherwise, and this affects wall time only, never a fit.
Trial cache is about 7.6 GB of float32.
