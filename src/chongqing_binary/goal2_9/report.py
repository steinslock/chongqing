"""Goal 2.9 reports.

The decision rule is the Goal 2.8 one, unchanged: a unit is credited with
independent signal only when an increment **over demographics** has a paired
bootstrap AUROC interval excluding zero under **both** CV protocols. Wins over
QC are log-integrity controls and are counted separately.

Goal 2.8 decided one row per modality. Every Goal 2.9 row is the same modality,
so the decision is taken per device/task unit instead, and a modality-level row
is added on top so the result lines up with the Goal 2.8 table.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from ..goal2_8.report import (
    DEMOGRAPHIC_INCREMENTS,
    _markdown,
    best_rows,
    required_increment_table,
)
from .config import ensure_output, load_goal_config, project_path

DEMOGRAPHIC_COMPARISONS = {f"{a}_vs_{b}" for a, b in DEMOGRAPHIC_INCREMENTS}

# An increment is only meaningful when the baseline it beats is itself doing
# something. In a cohort where demographics has fallen below chance, "beats
# demographics" is a statement about the comparator, not about the signal.
COMPARATOR_CHANCE_AUROC = 0.5


def _load(config: dict[str, Any], key: str) -> pd.DataFrame:
    path = project_path(config["outputs"][key])
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def credit_increments(required: pd.DataFrame, pooled: pd.DataFrame) -> pd.DataFrame:
    """Attach the comparator's own AUROC and withhold credit when it is at chance.

    Goal 2.9's combined Yiruid cohort produced eight increments whose intervals
    excluded zero, under both protocols, with 4/5 or 5/5 consistent fold
    direction. `scripts/verify_goal2_9_positive.py` shows all eight are noise:
    shuffling the diagnoses on that exact cohort reproduces a gap that large 12
    to 18 percent of the time, and the same 342 subjects show no gap at all when
    scored by models trained on the larger per-task cohorts.

    The mechanism is that the paired bootstrap resamples subjects but not folds,
    so it measures subject sampling noise and is blind to how unstable the fit
    itself is. In a cohort this small the demographics fit is unstable enough to
    land below chance, and a below-chance comparator manufactures a positive
    difference that the interval then certifies. Requiring the comparator to be
    above chance blocks that path without touching any comparison where the
    baseline is doing its job.
    """
    frame = required.copy()
    if frame.empty:
        return frame
    frame["feature_set_b"] = frame["comparison"].astype(str).str.rsplit("_vs_", n=1).str[-1]
    if pooled.empty:
        frame["comparator_auroc"] = float("nan")
    else:
        base = pooled.copy()
        if "threshold_type" in base.columns:
            base = base[base["threshold_type"].astype(str) == "inner_cv"]
        base = base[["cv_protocol", "cohort_name", "model", "feature_set", "auroc"]].rename(
            columns={"feature_set": "feature_set_b", "auroc": "comparator_auroc"})
        frame = frame.merge(base, on=["cv_protocol", "cohort_name", "model", "feature_set_b"],
                            how="left")
    frame["comparator_above_chance"] = (frame["comparator_auroc"] > COMPARATOR_CHANCE_AUROC).astype(int)
    frame["significant_positive_credited"] = (
        frame.get("significant_positive", 0) * frame["comparator_above_chance"]).astype(int)
    return frame


def _decide(group: pd.DataFrame, name_field: str, name: str) -> dict[str, Any]:
    demo = group[group["comparison"].isin(DEMOGRAPHIC_COMPARISONS)]
    control = group[~group["comparison"].isin(DEMOGRAPHIC_COMPARISONS)]
    credited = "significant_positive_credited" if "significant_positive_credited" in demo.columns \
        else "significant_positive"
    per_protocol = {protocol: int(sub[credited].sum())
                    for protocol, sub in demo.groupby("cv_protocol")}
    both = all(per_protocol.get(p, 0) > 0 for p in ("standard_cv", "group_cv"))
    raw_positive = int(demo["significant_positive"].sum()) if "significant_positive" in demo else 0
    return {
        name_field: name,
        "demographic_increment_rows": int(len(demo)),
        "positive_over_demographics_standard_cv": per_protocol.get("standard_cv", 0),
        "positive_over_demographics_group_cv": per_protocol.get("group_cv", 0),
        "uncredited_positive_comparator_at_chance": raw_positive - int(demo[credited].sum()),
        "negative_over_demographics": int(demo["significant_negative"].sum())
        if "significant_negative" in demo else 0,
        "positive_over_qc_controls": int(control["significant_positive"].sum()),
        "decision": "INDEPENDENT_SIGNAL_SUPPORTED" if both else "NO_INDEPENDENT_SIGNAL",
    }


def unit_decision(required: pd.DataFrame) -> pd.DataFrame:
    """One decision per device/task unit, plus one for behaviour as a whole."""
    if required.empty or "significant_positive" not in required.columns:
        return pd.DataFrame()
    frame = required.copy()
    frame["unit"] = frame["device"].astype(str) + "_" + frame["task"].astype(str)
    rows = [_decide(group, "unit", unit) for unit, group in frame.groupby("unit")]
    rows.append(_decide(frame, "unit", "behaviour_overall"))
    return pd.DataFrame(rows)


def build_reports(config_path: str | Path = "configs/goal2_9/models.yaml") -> dict[str, Any]:
    config = load_goal_config(config_path)
    pooled = _load(config, "all_pooled_metrics")
    paired = _load(config, "paired_comparisons")

    required = credit_increments(required_increment_table(paired), pooled)
    decision = unit_decision(required)
    best = best_rows(pooled)

    reports_dir = Path(ensure_output("reports/.keep", config)).parent
    results_dir = Path(ensure_output(config["outputs"]["all_pooled_metrics"], config)).parent
    required.to_csv(results_dir / "required_increments.csv", index=False)
    decision.to_csv(results_dir / "unit_decision.csv", index=False)

    positive = (required[required["significant_positive"] == 1]
                if "significant_positive" in required.columns else pd.DataFrame())
    n_positive = int(required.get("significant_positive", pd.Series(dtype=int)).sum())
    n_credited = int(required.get("significant_positive_credited", pd.Series(dtype=int)).sum())
    n_negative = int(required.get("significant_negative", pd.Series(dtype=int)).sum())
    demo_rows = (required[required["comparison"].isin(DEMOGRAPHIC_COMPARISONS)]
                 if "comparison" in required.columns else pd.DataFrame())

    lines = [
        "# Goal 2.9 Results",
        "",
        "Goal 2.9 adds one feature layer that no earlier goal used: the trial-level",
        "keypresses the paradigms recorded. The protocol is unchanged from Goal 2.7 and",
        "Goal 2.8 - the same fixed folds, the same inner-CV selection, the same model",
        "families and grids, the same 1000-resample bootstrap, the same pilot-holdout",
        "exclusion. Only the features are new.",
        "",
        "## Unit Decision",
        "",
        _markdown(decision),
        "",
        "A unit is credited with independent signal only when an increment **over",
        "demographics** has a paired bootstrap AUROC interval excluding zero under **both**",
        "CV protocols **and** the demographics baseline it beat is itself above chance.",
        "Beating the QC baseline shows the features carry more than log completeness,",
        "which is a control, not evidence of anything a questionnaire does not already",
        "supply.",
        "",
        "## Required Increments",
        "",
        f"Increments over demographics: **{len(demo_rows)}** rows.",
        f"Intervals excluding zero on the positive side: **{n_positive}** of {len(required)}.",
        f"Of those, credited (comparator above chance): **{n_credited}**.",
        f"Negative and significant: **{n_negative}**.",
        "",
        _markdown(positive if not positive.empty else required, limit=40),
        "",
        "## Best Row Per Feature Set",
        "",
        _markdown(best, limit=100),
    ]
    report_path = reports_dir / "goal2_9_results.md"
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    manifest = {
        "pooled_rows": int(len(pooled)),
        "paired_rows": int(len(paired)),
        "required_rows": int(len(required)),
        "demographic_increment_rows": int(len(demo_rows)),
        "positive_required": n_positive,
        "credited_required": n_credited,
        "negative_required": n_negative,
        "decision": decision.to_dict(orient="records"),
        "report": str(report_path),
    }
    (results_dir / "report_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest
