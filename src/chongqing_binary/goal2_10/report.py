"""Goal 2.10 reports.

The decision rule is unchanged from Goal 2.8 and Goal 2.9: a unit is credited
with independent signal only when an increment **over demographics** has a
paired bootstrap AUROC interval excluding zero under **both** CV protocols, and
the demographics baseline it beat is itself above chance. Wins over QC are
controls and are counted separately.

Goal 2.10 adds two demographic increments the earlier goals did not have, for
the absolute and contrast halves of the free-viewing feature block. They are
separated because their measurement properties differ by an order of magnitude:
53 of 75 absolute features clear split-half 0.5 on all three devices, and 0 of
46 contrasts do. A null on the contrast block is therefore evidence about the
paradigm rather than about attentional bias as a construct, and the report says
so rather than leaving the reader to infer it.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from ..goal2_8.report import DEMOGRAPHIC_INCREMENTS, SHORTCUT_CONTROLS, _markdown, best_rows
from ..goal2_9.report import COMPARATOR_CHANCE_AUROC, _decide, credit_increments
from .config import ensure_output, load_goal_config, project_path

# The two halves of the free-viewing block, tested separately.
EYE_DEMOGRAPHIC_INCREMENTS = DEMOGRAPHIC_INCREMENTS + [
    ("signal_absolute", "demographics"),
    ("signal_absolute_demographics", "demographics"),
    ("signal_contrast", "demographics"),
    ("signal_contrast_demographics", "demographics"),
]

EYE_CONTROLS = SHORTCUT_CONTROLS + [
    ("signal_absolute_demographics", "signal_contrast_demographics"),
]

EYE_REQUIRED_INCREMENTS = EYE_DEMOGRAPHIC_INCREMENTS + EYE_CONTROLS
EYE_DEMOGRAPHIC_COMPARISONS = {f"{a}_vs_{b}" for a, b in EYE_DEMOGRAPHIC_INCREMENTS}

# Any credited increment from a cohort this small must be verified by label
# permutation before it is reported. Every Goal 2.10 cohort is below it.
PERMUTATION_REQUIRED_BELOW_N = 500


def eye_unit_decision(required: pd.DataFrame) -> pd.DataFrame:
    """Decide each unit against the eye-specific set of demographic increments.

    Goal 2.9's version reads a module-level list that predates the absolute and
    contrast blocks, which would file `signal_absolute_demographics vs
    demographics` as a control. Counting an increment over demographics as a
    control, or a control as an increment, is the conflation this project
    already corrected once in the Goal 2.8 report.
    """

    if required.empty or "significant_positive" not in required.columns:
        return pd.DataFrame()
    frame = required.copy()
    frame["unit"] = frame["device"].astype(str) + "_" + frame["task"].astype(str)
    rows = [_decide_eye(group, "unit", str(unit)) for unit, group in frame.groupby("unit")]
    rows.append(_decide_eye(frame, "unit", "eye_all_units"))
    return pd.DataFrame(rows)


def _decide_eye(group: pd.DataFrame, name_field: str, name: str) -> dict[str, Any]:
    """`_decide` with the eye comparison set, and the two kinds kept apart."""

    demo = group[group["comparison"].isin(EYE_DEMOGRAPHIC_COMPARISONS)]
    control = group[~group["comparison"].isin(EYE_DEMOGRAPHIC_COMPARISONS)]
    credited = (
        "significant_positive_credited" if "significant_positive_credited" in demo.columns else "significant_positive"
    )
    per_protocol = {protocol: int(sub[credited].sum()) for protocol, sub in demo.groupby("cv_protocol")}
    both = all(per_protocol.get(protocol, 0) > 0 for protocol in ("standard_cv", "group_cv"))
    raw_positive = int(demo["significant_positive"].sum()) if "significant_positive" in demo else 0
    return {
        name_field: name,
        "demographic_increment_rows": int(len(demo)),
        "positive_over_demographics_standard_cv": per_protocol.get("standard_cv", 0),
        "positive_over_demographics_group_cv": per_protocol.get("group_cv", 0),
        "uncredited_positive_comparator_at_chance": raw_positive - int(demo[credited].sum()),
        "negative_over_demographics": int(demo["significant_negative"].sum())
        if "significant_negative" in demo
        else 0,
        "positive_on_controls": int(control["significant_positive"].sum()) if len(control) else 0,
        "decision": "INDEPENDENT_SIGNAL_SUPPORTED" if both else "NO_INDEPENDENT_SIGNAL",
    }


def _load(config: dict[str, Any], key: str) -> pd.DataFrame:
    path = project_path(config["outputs"][key])
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def eye_required_increment_table(paired: pd.DataFrame) -> pd.DataFrame:
    """The Goal 2.8 table, widened to the eye-specific comparisons."""

    if paired.empty:
        return pd.DataFrame()
    wanted = {f"{a}_vs_{b}" for a, b in EYE_REQUIRED_INCREMENTS}
    frame = paired.copy()
    if "comparison" not in frame.columns:
        frame["comparison"] = frame["feature_set_a"].astype(str) + "_vs_" + frame["feature_set_b"].astype(str)
    frame = frame[frame["comparison"].isin(wanted)].copy()
    if frame.empty:
        return frame
    low = next((column for column in frame.columns if column.startswith("auroc") and column.endswith("ci_low")), None)
    high = next((column for column in frame.columns if column.startswith("auroc") and column.endswith("ci_high")), None)
    diff = next(
        (column for column in frame.columns if column.startswith("auroc") and "diff" in column and "ci" not in column),
        None,
    )
    if low and high:
        frame["significant_positive"] = (frame[low] > 0).astype(int)
        frame["significant_negative"] = (frame[high] < 0).astype(int)
    keep = [
        column
        for column in [
            "cv_protocol", "cohort_name", "modality", "device", "task", "model",
            "comparison", diff, low, high, "significant_positive", "significant_negative",
        ]
        if column and column in frame.columns
    ]
    return frame[keep].sort_values([column for column in ["cv_protocol", "modality", "cohort_name"] if column in keep])


def _reliability_note(config: dict[str, Any]) -> dict[str, Any]:
    path = project_path(config["paths"]["results_dir"]) / "free_viewing_reliability_summary.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def build_reports(config_path: str | Path = "configs/goal2_10/models.yaml") -> dict[str, Any]:
    config = load_goal_config(config_path)
    pooled = _load(config, "all_pooled_metrics")
    paired = _load(config, "paired_comparisons")

    required = credit_increments(eye_required_increment_table(paired), pooled)
    decision = eye_unit_decision(required)
    best = best_rows(pooled)
    reliability = _reliability_note(config)

    reports_dir = Path(ensure_output("reports/.keep", config)).parent
    results_dir = Path(ensure_output(config["outputs"]["all_pooled_metrics"], config)).parent
    required.to_csv(results_dir / "required_increments.csv", index=False)
    decision.to_csv(results_dir / "unit_decision.csv", index=False)

    demo_rows = (
        required[required["comparison"].isin(EYE_DEMOGRAPHIC_COMPARISONS)]
        if "comparison" in required.columns
        else pd.DataFrame()
    )
    control_rows = (
        required[~required["comparison"].isin(EYE_DEMOGRAPHIC_COMPARISONS)]
        if "comparison" in required.columns
        else pd.DataFrame()
    )
    # Credit is only ever counted over demographics. A win on a control is a
    # control, and mixing the two counts is the conflation the Goal 2.8 report
    # had to correct.
    positive = demo_rows[demo_rows["significant_positive"] == 1] if len(demo_rows) else pd.DataFrame()
    n_positive = int(demo_rows.get("significant_positive", pd.Series(dtype=int)).sum())
    n_credited = int(demo_rows.get("significant_positive_credited", pd.Series(dtype=int)).sum())
    n_negative = int(demo_rows.get("significant_negative", pd.Series(dtype=int)).sum())
    n_control_positive = int(control_rows.get("significant_positive", pd.Series(dtype=int)).sum())
    n_control_credited = int(control_rows.get("significant_positive_credited", pd.Series(dtype=int)).sum())
    cohort_sizes = _cohort_sizes(pooled)

    lines = [
        "# Goal 2.10 Results",
        "",
        "Goal 2.10 adds the eye-tracking modality, the last objective modality no earlier",
        "goal used. The protocol is unchanged from Goal 2.7, 2.8 and 2.9: the same fixed",
        "folds, the same inner-CV selection, the same model families and grids, the same",
        "1000-resample bootstrap, the same pilot-holdout exclusion, and the Goal 2.9 rule",
        "that a credited increment must beat a comparator that is itself above chance.",
        "Only the features are new.",
        "",
        "## Read the free-viewing result with its measurement properties",
        "",
    ]
    if reliability:
        absolute = reliability.get("absolute", {})
        contrast = reliability.get("contrast", {})
        lines += [
            f"Free viewing carries {reliability.get('n_features', 0)} features in two blocks that",
            "differ by an order of magnitude in reliability, measured by odd-even split half",
            "on 249 to 322 subjects per device:",
            "",
            f"- **absolute** per-valence measures: {absolute.get('n', 0)} features, median"
            f" Spearman-Brown {absolute.get('median_sb', float('nan')):.3f},"
            f" {absolute.get('reliable_all_devices', 0)} above 0.5 on all three devices;",
            f"- **contrast** valence differences: {contrast.get('n', 0)} features, median"
            f" {contrast.get('median_sb', float('nan')):.3f},"
            f" **{contrast.get('reliable_all_devices', 0)}** above 0.5 on all three devices,"
            f" the best reaching {contrast.get('best_sb', float('nan')):.3f}.",
            "",
            "Each contrast is a difference of two means estimated from 12 trials each, which",
            "is the difference-score reliability collapse the attentional-bias literature",
            "reports, replicated here on three devices independently. The two blocks are",
            "therefore separate feature sets, and **a null on the contrast block is evidence",
            "about this paradigm, not about attentional bias as a construct.**",
            "",
        ]

    lines += [
        "## Unit Decision",
        "",
        _markdown(decision),
        "",
        "A unit is credited with independent signal only when an increment **over",
        "demographics** has a paired bootstrap AUROC interval excluding zero under **both**",
        "CV protocols **and** the demographics baseline it beat is itself above chance.",
        "Wins over QC show the features carry more than acquisition quality, which is a",
        "control rather than evidence of anything a questionnaire does not already supply.",
        "",
        "## Required Increments",
        "",
        f"Increments over demographics: **{len(demo_rows)}** rows.",
        f"Intervals excluding zero on the positive side: **{n_positive}**.",
        f"Of those, credited (comparator above chance): **{n_credited}**.",
        f"Negative and significant: **{n_negative}**.",
        "",
        f"Controls are counted separately: **{len(control_rows)}** rows, **{n_control_positive}** positive,",
        f"**{n_control_credited}** of them over an above-chance comparator. A win on a control is not",
        "an increment and is never credited as one.",
        "",
    ]
    if n_credited:
        lines += [
            f"Every Goal 2.10 cohort holds fewer than {PERMUTATION_REQUIRED_BELOW_N} subjects"
            f" ({cohort_sizes}), so each credited increment must be verified by label",
            "permutation on its own cohort before it is reported. That verification is not",
            "in this file.",
            "",
        ]
    lines += [
        _markdown(positive if not positive.empty else required, limit=40),
        "",
        "## Best Row Per Feature Set",
        "",
        _markdown(best, limit=120),
    ]
    report_path = reports_dir / "goal2_10_results.md"
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    manifest = {
        "pooled_rows": int(len(pooled)),
        "paired_rows": int(len(paired)),
        "required_rows": int(len(required)),
        "demographic_increment_rows": int(len(demo_rows)),
        "demographic_significant_positive": n_positive,
        "demographic_significant_positive_credited": n_credited,
        "demographic_significant_negative": n_negative,
        "control_rows": int(len(control_rows)),
        "control_significant_positive": n_control_positive,
        "control_significant_positive_credited": n_control_credited,
        "comparator_chance_auroc": COMPARATOR_CHANCE_AUROC,
        "permutation_required_below_n": PERMUTATION_REQUIRED_BELOW_N,
        "reliability": reliability,
        "report": str(report_path),
    }
    (results_dir / "report_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return manifest


def _cohort_sizes(pooled: pd.DataFrame) -> str:
    if pooled.empty or "n_subjects" not in pooled.columns:
        return "sizes unavailable"
    sizes = pooled.groupby("cohort_name")["n_subjects"].max()
    return f"{int(sizes.min())} to {int(sizes.max())}"


__all__ = [
    "EYE_DEMOGRAPHIC_INCREMENTS",
    "build_reports",
    "eye_required_increment_table",
    "eye_unit_decision",
]
