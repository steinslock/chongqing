# Goal 3 Final Report

Date: 2026-09-10

Goal 3 asked whether the correctly recovered EEG Oddball contains a learnable
spatio-temporal pattern that the Goal 2.8 hand-crafted features missed, and
whether that pattern carries information independent of age, sex and grade.

The design, the decision rule, the enumerated model family and seven numbered
predictions were written down before any model was trained, in
`reports/goal3_method_design.md`. The tables are in `reports/goal3_results.md`
and the machine-readable outputs in `results/goal3/`.

**Result: no independent EEG signal, from the strongest position this project
has been able to put a null in.**

## 1. What was run

One environment, one cohort, one protocol.

| | |
|---|---|
| cohort | the Goal 2.8 Oddball cohort, taken from its index file: **1820 subjects**, 0 pilot-holdout rows |
| trials | 237,774 single trials re-derived from raw BDF, 21.9 target and 108.7 standard per subject |
| model input | 30 channels (see the amendment in section 7), 250 samples, -0.2 to 0.8 s |
| architectures | EEGNet, InceptionTime-1D, compact EEG-Conformer |
| representations | target-only, standard-only, condition-aware, difference-wave |
| configurations | 14: 1 confirmatory, 12 exploratory, 1 ablation |
| runs | 14 x 2 protocols x 3 seeds = 84 jobs, 15 trainings each, **1260 trained models** |
| outputs | 1,019,200 subject-level OOF predictions, 1120 pooled metric rows, 560 paired comparisons |

## 2. The measurement gate

Goal 2.8 kept only the condition averages, so the trials had to be rebuilt. The
gate was not "does the P3b still look right" but **numerical identity**:
averaging the new trial cache by condition must reproduce
`artifacts/goal2_8/eeg/oddball_erp.npz`.

| check | result |
|---|---|
| subject sets identical | 1820 of 1820 |
| worst relative difference | **1.10 float32 epsilons** |
| mismatches above tolerance | **0** |
| Pz target-minus-standard, 0.28-0.55 s | +6.426 uV (Goal 2.8: +6.40) |
| Cohen d at Pz | 1.079 (Goal 2.8: 1.08) |
| subjects positive at Pz | 88.7% (Goal 2.8: 88.1%) |
| peak channel / Fz | Pz / -2.483 uV |

These are the Goal 2.8 epochs, not a re-derivation that resembles them.

## 3. The positive controls, which are what make this null worth reading

Given Goal 2.8, a null was the likely outcome. A null is only informative if the
same pipeline can be shown to learn from these trials; otherwise "EEG carries no
disease information" and "this pipeline learns nothing" are the same
observation. Same architecture, same aggregation, same splits, same protocol,
different target:

| control | Standard CV | Group CV |
|---|---|---|
| **PC1** target vs standard, trial level, held-out subjects | **0.8243** | **0.8229** |
| **PC2** sex, subject level | **0.7734** | **0.7672** |
| **PC3** age (median split), subject level | **0.8209** | **0.8029** |
| the disease label, best configuration | 0.5451 | 0.5580 |

PC1 was the hard gate at 0.70 and all ten folds cleared it (0.802 to 0.842) on
34,000 to 59,000 held-out trials.

PC2 and PC3 answer the question the design left open: **subject-level
aggregation is not the weak link.** Mean-and-std pooling over eight trials per
condition extracts enough subject-level information to reach 0.77 for sex and
0.82 for age on the very same subjects and folds where the disease label reaches
0.55. Whatever limits the disease result, it is not the encoder, not the
pooling, not the splits, and not the trials.

## 4. Question 1: does EEG carry a label signal at all?

Yes, weakly. Sixteen of the twenty-eight configuration-by-protocol rows have an
AUROC interval excluding 0.5. The whole range is **0.4825 to 0.5580**.

For scale, in the same 1820 subjects: age+sex+grade reaches **0.5909** under
Group CV and **0.6023** under Standard CV, and `eeg_deep vs demographics` runs
from -0.033 to -0.108, averaging **-0.072**.

So there is something, and it is much less than a three-item questionnaire.

## 5. Question 2: is the deep representation better than the hand-crafted one?

**No credited evidence, and the way this nearly went wrong is the most
instructive part of the stage.**

Under **Group CV**, 7 of 14 configurations beat `eeg_traditional` with intervals
excluding zero, up to +0.0647. Read alone, that is "deep learning extracts
Oddball information the 321 hand-crafted features do not".

But `eeg_traditional` sits at **0.4933 under Group CV — below chance**. Every one
of those seven wins is a win over a broken comparator, which is a statement
about the traditional features rather than about the deep representation.

Under **Standard CV**, where the traditional block is above chance at 0.5191,
**0 of 14** intervals exclude zero and the largest difference is +0.0259,
CI [-0.0029, +0.0554].

The rule that caught this is the Goal 2.9 requirement that a credited increment
beat an above-chance comparator. It was written for demographics comparators;
Goal 3 extended it to every comparison (amendment 3, section 7) from the
structure of the comparison and before these numbers existed. Without that
extension this report would have claimed a deep-versus-traditional win in seven
configurations, which would have been this project's **third** instance of the
same error after Goal 2.9 withdrew eight rows and Goal 2.10 withdrew eighteen.

## 6. Question 3: does EEG add anything over age, sex and grade? The decision

**Confirmatory test**, declared in advance as the single test that decides:
EEGNet, condition-aware, no per-subject normalisation, seed-averaged,
`p_Demo + p_EEG` against `p_Demo`.

| protocol | increment | 95% CI | comparator | above chance | folds positive | p |
|---|---|---|---|---|---|---|
| Standard CV | +0.0016 | [-0.0059, +0.0084] | 0.6023 | yes | 4/5 | 0.634 |
| Group CV | -0.0031 | [-0.0150, +0.0094] | 0.5909 | yes | 3/5 | 0.626 |

**Exploratory family**, 12 configurations x 2 protocols, enumerated and closed
before the run: **0 of 24 intervals exclude zero**, 0 survive Benjamini-Hochberg
at 0.05. The largest point estimate in the entire family is +0.0045 (p = 0.240).

**Amplitude ablation.** Per-subject robust z-scoring gives -0.0046 and +0.0038,
both intervals containing zero. The result does not depend on whether
subject-level amplitude is preserved, so it is not an artefact of the primary
normalisation choice in either direction.

**Verdict: `NO_INDEPENDENT_SIGNAL`** on 26 of 26 decision rows; the two ablation
rows return no verdict by design.

## 7. Three things this stage had to fix, and what they cost

All three were recorded as dated amendments in the method design before the
matrix was read, and all three rest on quantities measured without a label.

**Amendment 1: the model reads 30 channels, not 32.** Goal 2.8 deliberately
excluded Fp1 and Fp2 from its artifact-rejection decision because blinks
dominate them. The consequence it never had to face is that its 150 uV
peak-to-peak bound constrains every channel *except* those two: over all 237,774
trials, every other channel stays below **144.5 uV** while Fp1 reaches 10,673 uV
and Fp2 reaches **118,990 uV**, and all fifty highest-amplitude subjects peak on
one of them. Goal 2.8's ERP features read only parietal channels and were
insulated; a network handed the raw array unnormalised would have had its first
convolution and its batch statistics set by blink amplitude on two channels.

**Amendment 2: the identity gate is relative, not absolute.** The design
declared an absolute tolerance of 1e-10 V from a six-subject pilot. On all 3640
subject-condition pairs the absolute residual spans 1.3e-13 to 2.4e-10 while the
*relative* residual stays between 3.4e-8 and 1.3e-7, one float32 epsilon. The
absolute bound was measuring amplitude, not identity, and its worst offender was
simply the subject with the largest blinks.

**Amendment 3: the above-chance comparator rule applies to every comparison.**
Section 5 above is what it bought.

## 8. Shortcut probes

**The representation encodes the recording site.** Decoding the acquisition
group from out-of-fold EEG embeddings gives balanced accuracy 0.537 to 0.584
against a 0.10 chance level under Group CV — 5.4 to 5.8 times chance — and 0.148
to 0.152 under Standard CV. Prediction 7 holds.

The asymmetry has a mechanism. Under Group CV the model is tested on sites it
never trained on, and an out-of-distribution site displaces the embedding
systematically in a site-specific direction; under Standard CV every site is in
training and the encoder maps them together. This is precisely why Group CV is
co-primary, and it is also why the Group-CV Q2 result in section 5 deserved the
scepticism it got.

**Trial count cannot manufacture signal.** Target count, standard count and
rejection rate have univariate label AUROCs of 0.4989, 0.5058 and 0.4955
(all p > 0.2), so the subject-balanced sampling had nothing to protect against
in the first place.

## 9. Two methodological results worth carrying forward

**The deep EEG score is seed-unstable at a scale that dwarfs the effect being
tested.** Between-seed AUROC standard deviation for `eeg_deep` averages **0.0249
under Group CV with a maximum of 0.0527**, against increments of ±0.005. One
configuration ranges from 0.4775 to 0.5760 across three seeds of the same fit.
The paired subject bootstrap is blind to this — it resamples subjects, not fits —
exactly as the protocol warns. Seed-averaging is not a nicety here; a single-seed
deep result on this cohort is not interpretable.

The stacked score `demographics_eeg_deep` is far more stable (std 0.0035 to
0.0043), because the meta model gives a noisy component a small weight.

**Cross-fitted stacking removes the dilution artefact, and the difference is
visible.** Goal 2.8 recorded **78 significantly negative** increments over
demographics out of 216. Goal 3 records **0 positive and 0 negative** out of 56,
with the whole range from -0.0078 to +0.0045. EEG did not become less harmful;
the increment test stopped punishing an uninformative block. Goal 2.8's negatives
were the pipeline paying for columns it could not ignore, and this project had to
add a paragraph to its protocol explaining that a negative increment means
absence rather than damage. With one scalar per component that paragraph is no
longer needed: an uninformative component receives a near-zero weight and
`Demo + EEG` collapses onto `Demo`.

Any future increment test in this project should use this design.

## 10. The predictions, scored

| # | prediction | outcome |
|---|---|---|
| 1 | PC1 reaches at least 0.85 | **missed**: 0.8236. The prediction conflated the subject-averaged effect size (d = 1.08) with single-trial separability, which is necessarily lower |
| 2 | PC2 and PC3 land between 0.60 and 0.75 | **exceeded**: sex 0.767-0.773, age 0.803-0.821 |
| 3 | EEG alone reaches 0.50 to 0.56 | **held**, slightly wider: 0.4825 to 0.5580 |
| 4 | the confirmatory increment interval includes zero | **held** under both protocols |
| 5 | deep does not beat traditional once both are cross-fitted | **held**, and only because amendment 3 was applied |
| 6 | standard-only performs like target-only | **held**: EEGNet 0.5156/0.5327 against 0.5353/0.5370. No deviance-processing claim is available |
| 7 | the acquisition group is decodable from the embedding | **held**: 5.4 to 5.8 times chance |

Six of seven held. The one that missed was a reasoning error on my part, not a
surprise in the data, and it is recorded as such.

## 11. What this null does and does not say

**It says**: in 1820 subjects, the single-trial spatio-temporal structure of a
correctly recovered auditory Oddball carries no information about this
health/non-health label beyond age, sex and grade, under either CV protocol,
across three inductive biases, four representations and three seeds, whether or
not subject amplitude is preserved.

**It is the strongest form of null this project has produced**, because for the
first time the instrument's capacity was measured on the same pipeline: age at
0.82 and sex at 0.77 against the disease label at 0.55, on the same subjects and
folds. Goal 2.10 established that a null on an unmeasurable quantity is evidence
about the instrument; Goal 3 is the converse, a null on a demonstrably capable
instrument.

**It does not say** that EEG is uninformative about psychiatric state in
general. It says it about this label, this paradigm, this cohort and this 1 s
epoch. Specific limits worth stating:

- The label is a school-screening health/non-health cut in which age, sex and
  grade already reach 0.64 to 0.67 on the full development cohort. A signal has
  to clear a demographically loaded baseline to be credited.
- Only Oddball was modelled. Rest and 1BACK are out of scope by design, and the
  standard-only control shows this paradigm's contribution is not specific to
  deviance processing anyway.
- The seed instability in section 9 sets a floor on what could have been
  detected: an effect smaller than about 0.02 AUROC would not be separable from
  fit noise at three seeds, whatever the bootstrap says.

## 12. Recommendation

Goal 3 answers its three questions and stops. It does not lift the Goal 2.8 gate
on Goal 4, Goal 5 or multimodal fusion, and nothing here argues for lifting it:
the modality with the largest label signal in this dataset is still
demographics, and the one objective modality that beat *background* (Face,
Goal 2.8) still did not beat demographics.

If EEG work continues, the two questions worth money are not architectural.
They are whether a label with a sharper clinical definition behaves differently
in this cohort, and whether a paradigm with a larger individual-difference
component than a 1 s Oddball epoch would help. Neither is a Goal 3 question.

## 13. Reproducibility

Single environment `chongqing_v1`; `source activate.local.sh`.

```
python scripts/build_eeg_goal3_trials.py --n-jobs 64
python scripts/verify_goal3_trial_cache.py
python scripts/run_goal3_tabular.py --workers 6
python scripts/run_goal3_controls.py --stage pc1
python scripts/run_goal3_controls.py --stage subject
python scripts/run_goal3.py --workers 10 --cache-dir /dev/shm/goal3_eeg
python scripts/run_goal3_controls.py --stage group
python scripts/summarize_goal3.py
python -m unittest discover -s tests
```

All 84 job files carry 9100 rows, no truncation, no missing configuration. All
predictions are `split_group == cv` with zero pilot-holdout subjects, and the
split files are unchanged.

One embeddings dump, `eegnet__condition_aware__mean_std__none__standard_cv__seed1`,
was lost to a write interrupted by a scheduler restart. Its prediction and
diagnostic files are intact and complete; only the group probe is affected, and
it runs on the remaining five. The file was not regenerated, because doing so
would have meant overwriting a completed matrix job and the regenerated run
could have landed on a different device.

The trial cache is 7.6 GB and stays local. `results/goal3/` holds the OOF
predictions, pooled metrics, bootstrap intervals, paired comparisons, p-values,
seed spread, controls and the decision table.
