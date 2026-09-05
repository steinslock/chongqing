# Chongqing project status report source notes

Generated: 2026-08-23T21:19:39+09:00

## Report job

- Question: What is the current state of the Chongqing project for a reader with no prior context?
- Audience: product stakeholders.
- Delivery mode: portable HTML.
- Scope: local project files and generated evidence available through 2026-08-23.
- Decision-useful answer: experimental engineering is complete through Goal 2.7, but no modality has established stable independent signal; Goal 2.8 remediation and governance cleanup should precede deep modeling.

## Executive structure mapping

- Title: `重庆多模态二分类项目：现状汇报`.
- Executive Summary: retained as the first visible section after the title.
- Key findings with visual evidence: project stage table, coverage chart, modality decision table, and model-evidence narrative.
- Recommended next steps: Goal 2.8 decision gate section.
- Further questions: four owner decisions.
- Caveats and assumptions: final visible section.

## Source precedence

1. Goal 2.7 generated results, final report, and run manifest control the current experimental state.
2. `PROGRESS.md` controls the chronological work log.
3. Git history/status controls what is committed versus only present in the working tree.
4. `AGENTS.md` and `PROJECT_SPEC.md` are retained as evidence of stale governance documentation, not as the controlling current-stage source.

## Chart map

| Report segment | Analytical question | Family/type | Fields | Supported claim | Palette policy | Delivery |
| --- | --- | --- | --- | --- | --- | --- |
| Data coverage | How many subjects are represented in each audited or strict-valid Goal 2.7 stream? | Comparison / horizontalBar | `stream`, `subjects`, `modality`, `validity_note` | Data coverage is substantial, but task semantics and cohort alignment are the limiting issues. | Single-root preferred with neutral scaffolding; no redundant color grouping. | Native artifact chart in portable HTML |

## Visual and table QA notes

- The coverage chart uses 10 categories, more than the four-category minimum for a category comparison.
- It is explicitly labeled as coverage rather than performance and notes that streams use different cohorts.
- Long labels use a horizontal bar form.
- The project-stage and modality tables are used because their purpose is exact status lookup, not magnitude comparison.
- No time-series chart is used because the project evidence has milestone timestamps rather than enough repeated temporal observations for an honest trend.
- No cross-modality AUROC ranking chart is used because the underlying cohorts and feature families differ.

## Verification

- Full unit-test discovery rerun on 2026-08-23: 105 tests passed.
- Current Git base: `main` at `780b940`, aligned with `origin/main` and committed through Goal 2.6.
- Before creating this report, the workspace contained one modified tracked file and 22 untracked Goal 2.7 entries.
- The latest inspected project artifact timestamp was 2026-07-10T00:06:36+09:00.
- Portable delivery validation and exact-payload structural verification passed. Browser QA is `structural_only` because no compatible Chromium headless-shell was installed; the report retains its semantic chart table fallback.
