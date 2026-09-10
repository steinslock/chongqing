# The Increment Criteria, and What They Cost

Date: 2026-09-10

This document answers two questions asked directly: **what conditions does an
increment over demographics have to satisfy**, and **how many increments would
be credited if most of those conditions were dropped**.

It is a record, not a decision. No stage's conclusion changes here.

## 1. Why there is a list at all

The rule was not designed up front. Each clause was added after a specific
result turned out to be an artefact, and each is traceable to the stage that
found it. That is a reasonable way to build a rule, and it is also how a rule
quietly becomes strict enough to hide a real effect. Writing the clauses out in
one place, with their provenance and their cost, is the only way to judge
whether that has happened.

## 2. The criteria

| # | criterion | added by | what it was catching |
|---|---|---|---|
| 1 | the paired subject-bootstrap AUROC interval excludes zero on the positive side | Goal 2.7 | ordinary sampling noise |
| 2 | at least 4 of 5 outer folds positive | Goal 2.7 | an effect carried by one fold |
| 3 | positive under **both** CV protocols | Goal 2.7 | site/acquisition shortcuts, which Group CV removes by holding out whole sites |
| 4 | no dominant shortcut explanation from the control battery | Goal 2.7 | background, group proxy, device, QC and metadata channels |
| 5 | the comparator is itself **above chance** in that cohort and protocol | Goal 2.9 | beating a demographics baseline that had collapsed below 0.5 |
| 6 | label permutation for any credited increment from a cohort under ~500 subjects | Goal 2.9 | fit instability the subject bootstrap cannot see |
| 7 | seed-averaged over three seeds | Goal 3 | deep-model fit variance |
| 8 | FDR control across the exploratory family | Goal 3 | multiplicity over a 12-configuration family |
| 9 | criterion 5 applies to **every** paired comparison, not only increments over demographics | Goal 3 | the same collapsed-comparator mechanism in `deep vs traditional` |

Criteria 1 to 5 apply to every stage. Criteria 6 to 9 apply where their
precondition holds: 6 only to small cohorts, 7 and 8 only to deep stages, 9 to
any comparison that is not against demographics.

Note what criterion 4 is not: it is a reading of the control battery by a human,
not a threshold. Nothing has ever been rejected by it alone.

## 3. The relaxed re-check

Criteria 2, 3, 6, 7, 8 and 9 were dropped, leaving criterion 1 (interval
excludes zero) and criterion 5 (comparator above chance). Every
`modality + demographics` against `demographics` comparison from Goal 2.7
through Goal 3 was re-scored: **878 rows across five stages and five
modalities.** `scripts/recheck_increments_relaxed.py` reproduces it and
`results/increment_recheck/` holds the tables.

| modality | rows | L1 interval excludes zero | **L2 + comparator above chance** | L3 + at least 4/5 folds |
|---|---|---|---|---|
| **EEG** | 302 | 35 | **35** | 20 |
| **Face** | 66 | 12 | **12** | 10 |
| eye tracking | 288 | 11 | **0** | 0 |
| behaviour | 84 | 3 | **0** | 0 |
| fNIRS | 138 | 0 | **0** | 0 |

| stage | rows | L1 | **L2** | L3 |
|---|---|---|---|---|
| Goal 2.7 | 162 | 12 | **12** | 10 |
| Goal 2.8 | 120 | 0 | **0** | 0 |
| Goal 2.9 | 84 | 3 | **0** | 0 |
| Goal 2.10 | 288 | 11 | **0** | 0 |
| Goal 3 | 224 | 35 | **35** | 20 |

fNIRS returns nothing even at L1: not one of its 138 increment intervals
excludes zero. Eye tracking's 11 and behaviour's 3 fall only at criterion 5,
which is the clause both stages were originally withdrawn under; they are the
same rows.

## 4. What the two survivors are

### Face, 12 rows, all from Goal 2.7

| comparison | rows | interval excludes zero |
|---|---|---|
| `face + demographics` vs demographics | 18 | **0** |
| `face + QC + demographics` vs demographics | 18 | **10** |
| `core-3 intersection + demographics` vs demographics | 6 | 2 |

Pure Face plus demographics never beats demographics, in any protocol, with any
model. Ten of the twelve require the **QC block** to be added as well —
resolution, frame rate, duration, codec — which is acquisition metadata and the
channel Goal 2.7 named when it called Face `SHORTCUT_DOMINATED`. The remaining
two are the three-modality intersection cohort on the self-introduction clip.

These features are also **superseded**. Goal 2.7 sampled 16 frames uniformly
across an approximately 11-minute multi-phase session that it had not segmented.
Goal 2.8 segmented it with `附件/网页数据.xlsx` and recomputed on the same
subjects: **0 of 120** intervals exclude zero, at L1.

### EEG, 35 rows, all from Goal 3

All thirty-five are single-seed rows. Their distribution:

| seed | protocol | deep model | traditional 321 features |
|---|---|---|---|
| 2 | Group CV | 14 of 14 | **14 of 14** |
| 0 | Standard CV | 6 | 0 |
| 0 | Group CV | 1 | 0 |

Twenty-eight of the thirty-five sit in one cell, Group CV seed 2, where every
deep configuration **and** the hand-crafted feature block are credited at once.
In that cell the demographics comparator is 0.5574 against 0.5814 and 0.6013 in
the other two seeds, while the EEG score itself is at its weakest of the three
(0.5075) and `Demo + EEG` is flat at 0.584 across all three seeds. The
comparator is cross-fitted through seed-dependent inner splits, so it varies;
in this stage it varied by 0.044.

This is recorded as an observation about those rows, not as a new criterion.
Criterion 5 does not catch it, because 0.5574 is above chance.

## 5. Comparability, which is a real limit on reading the table above

**Goal 2.7, 2.8, 2.9 and 2.10 each ran one seed. Goal 3 ran three.** Dropping
criterion 7 therefore gives EEG three independent draws that no other modality
was given, and 302 of the 878 rows are Goal 3's. EEG's 35 and Face's 12 are not
on the same denominator.

Two ways to level it, neither done here:

- run the classical stages at three seeds as well, which is cheap for the
  sklearn families and would make the comparison fair;
- or read only Goal 3's seed-averaged rows, which give 0 of 28.

## 6. What this does and does not show

Relaxing six of the nine criteria produced no new modality. It surfaced two
groups of rows, and both have a stated character: Face's require an acquisition
metadata block and come from a feature layer that was rebuilt and returned
nothing, and EEG's are concentrated in one seed where the comparator moved.

That is not an argument that the criteria are all necessary. Criteria 2, 3 and 5
each did real work here; 6, 8 and 9 removed nothing in this particular re-check,
and 7 removed everything EEG had. A future stage is entitled to ask the same
question again.

The one place in this project where an objective modality demonstrably carries
information that the recording setting cannot explain is **Face against
background** in Goal 2.8: 8 of 12 intervals positive, the strongest at +0.1153
[0.0858, 0.1450] under Group CV on the within-subject valence contrast, a
representation in which the background control itself sits at chance because
identity, room, camera and site cancel within subject. That signal is real and
it does not beat age, sex and grade.

## 7. Reproducing this

```
python scripts/recheck_increments_relaxed.py
```

Outputs land in `results/increment_recheck/`:
`all_increments_with_comparators.csv`, `ladder_by_modality.csv`,
`ladder_by_goal.csv`, `credited_under_relaxed_rule.csv`.
