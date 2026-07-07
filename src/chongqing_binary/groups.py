"""Site/batch/device proxy audit for Goal 2.5."""

from __future__ import annotations

from collections import Counter, defaultdict
from statistics import mean
from typing import Any, Mapping

from .readiness import ensure_output_path, split_rows, text_table, write_csv


def group_code(row: Mapping[str, str]) -> str:
    a_id = row.get("A_id", "")
    if len(a_id) >= 3:
        return f"A_prefix3_{a_id[:3]}"
    if a_id:
        return f"A_prefix_{a_id[0]}"
    return "A_missing"


def build_subject_groups(config: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
    rows = []
    for row in split_rows(config):
        out = dict(row)
        out["group_code"] = group_code(row)
        out["group_family"] = (row.get("A_id", "")[:1] or "missing")
        out["group_prefix2"] = (row.get("A_id", "")[:2] or "missing")
        out["group_prefix3"] = (row.get("A_id", "")[:3] or "missing")
        rows.append(out)
    return rows


def summarize_groups(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["group_code"]].append(row)
    summaries = []
    for code, items in sorted(grouped.items()):
        labels = [int(row["primary_label_nonhealthy"]) for row in items if row.get("primary_label_nonhealthy") in {"0", "1"}]
        ages = []
        for row in items:
            try:
                ages.append(float(row.get("age", "")))
            except ValueError:
                pass
        folds = sorted(set(row.get("cv_fold", "") for row in items if row.get("cv_fold", "")))
        summaries.append(
            {
                "group_code": code,
                "n_subjects": len(items),
                "n_positive": sum(labels),
                "positive_rate": (sum(labels) / len(labels)) if labels else "",
                "age_mean": mean(ages) if ages else "",
                "sex_counts": _counts(items, "sex"),
                "grade_group_counts": _counts(items, "grade_group"),
                "eeg_flag": sum(1 for row in items if row.get("has_EEG") == "1"),
                "fnirs_flag": sum(1 for row in items if row.get("has_fNIRS") == "1"),
                "face_flag": sum(1 for row in items if row.get("has_face") == "1"),
                "fnirs_device_counts": _counts(items, "fnirs_device"),
                "cv_folds_present": "|".join(folds),
                "n_cv_folds_present": len(folds),
                "locked_test_count": sum(1 for row in items if row.get("split_group") == "locked_test"),
                "shortcut_risk": "high" if len(labels) >= 20 and _extreme_rate(labels) else "review",
            }
        )
    return summaries


def _counts(rows: list[dict[str, Any]], column: str) -> str:
    counter = Counter(str(row.get(column, "") or "[missing]") for row in rows)
    return "|".join(f"{key}:{value}" for key, value in sorted(counter.items()))


def _extreme_rate(labels: list[int]) -> bool:
    rate = sum(labels) / len(labels)
    return rate <= 0.15 or rate >= 0.85


def build_group_robustness_split(rows: list[dict[str, Any]], seed: int = 20260707) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[row["group_code"]].append(row)
    fold_loads = [{"n": 0, "pos": 0} for _ in range(5)]
    group_items = []
    for code, items in groups.items():
        labels = [int(row["primary_label_nonhealthy"]) for row in items if row.get("primary_label_nonhealthy") in {"0", "1"}]
        group_items.append((code, len(items), sum(labels), items))
    group_items.sort(key=lambda item: (-item[1], item[0]))
    assignment: dict[str, int] = {}
    for code, n, pos, _ in group_items:
        best = min(range(5), key=lambda fold: (fold_loads[fold]["n"], abs((fold_loads[fold]["pos"] + pos) - (fold_loads[fold]["n"] + n) * 0.30)))
        assignment[code] = best
        fold_loads[best]["n"] += n
        fold_loads[best]["pos"] += pos
    out = []
    for row in rows:
        new = dict(row)
        new["robustness_split_note"] = "group_proxy_fold_for_robustness_only_not_replacement"
        new["robustness_fold"] = "" if row.get("split_group") == "locked_test" else str(assignment[row["group_code"]])
        out.append(new)
    return out


def write_group_outputs(config: Mapping[str, Any] | None = None) -> dict[str, Any]:
    rows = build_subject_groups(config)
    summaries = summarize_groups(rows)
    write_csv("artifacts/groups/subject_groups.csv", rows)
    write_csv("artifacts/groups/group_summary.csv", summaries)
    write_csv("artifacts/splits/subject_splits_group_robustness_v1.csv", build_group_robustness_split(rows))
    report = group_report(rows, summaries)
    ensure_output_path("reports/site_batch_confound_audit.md").write_text(report, encoding="utf-8")
    return {"rows": rows, "summaries": summaries}


def group_report(rows: list[dict[str, Any]], summaries: list[dict[str, Any]]) -> str:
    stats = {
        "subjects": len(rows),
        "a_prefix3_groups": len(summaries),
        "groups_n_ge_20": sum(1 for row in summaries if int(row["n_subjects"]) >= 20),
        "groups_high_shortcut_risk": sum(1 for row in summaries if row["shortcut_risk"] == "high"),
    }
    lines = [
        "# Goal 2.5 Site/Batch/Device Confound Audit",
        "",
        "A direct clinical site or school identifier is not present in the canonical manifest. The most stable available grouping proxy is the anonymized `A_id` prefix. Goal 2.5 writes `group_code = first three characters of A_id` as a batch/site-proxy for audit and robustness only.",
        "",
        "## Summary",
        "",
        text_table(stats),
        "",
        "## Interpretation",
        "",
        "- `A_id` prefix is reliable as a stable anonymized grouping key, but its real-world meaning is not confirmed.",
        "- fNIRS device is an explicit device confound and is retained in `subject_groups.csv` and cohort outputs.",
        "- Face codec/resolution/fps are audited in Face video tables and should be tested as shortcut-only features before formal Face modeling.",
        "- `subject_splits_group_robustness_v1.csv` is generated only for robustness analysis. It does not replace `subject_splits_v1.csv` and must not be used for model selection based on performance.",
        "",
        "## Attempted Variables",
        "",
        "- Manifest: `A_id`, demographics, modality flags, fNIRS device.",
        "- Raw directories: EEG task naming, fNIRS device/task directories, Face video metadata.",
        "- Direct school/site/camera fields were not found in the canonical manifest.",
    ]
    return "\n".join(lines) + "\n"
