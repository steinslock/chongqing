#!/usr/bin/env python3
"""Audit eye-tracking coverage, paradigm conformance, QC and label-free validity.

This is the Goal 2.10 entry point that runs before any feature extraction. It
answers four questions and writes them down:

1. How many subjects does the eye modality actually cover, keyed on `A_id`?
2. Does the recorded data match `configs/goal2_10/eye_paradigm_spec.yaml`?
3. What is the acquisition quality, per device?
4. Do the label-free validity checks pass, so that a later null result would be
   about the data rather than about the parse?

No labels enter any check. Cohort tables report label prevalence only as a
description of who is in the cohort.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from chongqing_binary.eye import aoi as eye_aoi
from chongqing_binary.eye.index import redact_record_name
from chongqing_binary.eye import drift as eye_drift
from chongqing_binary.eye import qc as eye_qc
from chongqing_binary.eye import qixin as qixin_io
from chongqing_binary.eye import stimuli as eye_stimuli
from chongqing_binary.eye import tobii as tobii_io
from chongqing_binary.eye import validity as eye_validity
from chongqing_binary.eye.index import attach_subjects, coverage_by_unit, discover_recordings, resolve_duplicates
from chongqing_binary.eye.spec import load_eye_spec
from chongqing_binary.readiness import (
    ensure_output_path,
    environment_snapshot,
    raw_data_dir,
    read_csv,
    write_csv,
    write_json,
)

STIMULUS_DIR = "artifacts/goal2_10/stimuli"
ARTIFACT_DIR = "artifacts/goal2_10/readiness"
REPORT_PATH = "reports/eye_readiness_audit.md"

_WORKER: dict[str, Any] = {}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split-file", default="artifacts/splits/subject_splits_v1.csv")
    parser.add_argument("--n-workers", type=int, default=16)
    parser.add_argument("--limit-per-unit", type=int, default=0, help="0 audits every recording")
    parser.add_argument(
        "--render-only",
        action="store_true",
        help="rebuild the report from the saved summary without re-reading raw files",
    )
    return parser.parse_args()


# Thresholds for the readiness verdict. Each is a property of the paradigm or
# of physiology, not of the labels, so a unit that fails one has a parsing or
# acquisition problem rather than an absent effect.
VERDICT_THRESHOLDS = {
    "timeline_complete_rate": 0.90,
    "valid_sample_fraction": 0.70,
    "on_face_over_chance": 5.0,
    "pro_corr_x": 0.30,
    "anti_corr_x_max": 0.0,
    "pursuit_corr_x": 0.50,
    "aoi_eyes_minus_mouth": 0.0,
}


def main() -> None:
    args = parse_args()
    if args.render_only:
        summary = json.loads((ROOT / ARTIFACT_DIR / "eye_readiness_summary.json").read_text(encoding="utf-8"))
        summary["verdict"] = _verdict(summary)
        write_json(f"{ARTIFACT_DIR}/eye_readiness_summary.json", summary)
        ensure_output_path(REPORT_PATH).write_text(render_report(summary), encoding="utf-8")
        print(json.dumps({"rendered": REPORT_PATH}))
        return
    spec = load_eye_spec()
    raw_root = raw_data_dir()

    products = eye_stimuli.build_stimulus_products(spec, raw_root, ROOT / STIMULUS_DIR, ROOT)

    rows = discover_recordings(spec, raw_root)
    asdata = {
        name: qixin_io.load_asdata(raw_root / device.asdata)
        for name, device in spec.devices.items()
        if device.asdata
    }
    rows = qixin_io.annotate_recordings(rows, spec, asdata)
    rows = _attach_timelines(rows, spec, asdata)
    split = {row["A_id"]: row for row in read_csv(args.split_file)}
    rows = attach_subjects(rows, split)
    kept, discarded = resolve_duplicates(rows)

    selected = _select(kept, args.limit_per_unit)
    audited = _audit_recordings(selected, spec, args.n_workers)
    by_path = {row["path"]: row for row in audited}
    kept = [{**row, **by_path.get(row["path"], {})} for row in kept]

    write_csv(f"{ARTIFACT_DIR}/recordings.csv", [_publishable(row) for row in kept])
    write_csv(f"{ARTIFACT_DIR}/discarded_recordings.csv", [_publishable(row) for row in discarded])

    summary = {
        "stage": "Goal 2.10 eye readiness",
        "spec_path": str(spec.path.relative_to(ROOT)),
        "attachment_available": spec.attachment_available,
        "labels_used": False,
        "raw_data_dir": str(raw_root),
        "recordings_discovered": len(rows),
        "recordings_kept": len(kept),
        "recordings_audited": len(audited),
        "coverage": _coverage_summary(kept, split),
        "duplicates": _duplicate_summary(discarded),
        "conformance": _conformance_summary(kept),
        "quality": _quality_summary(kept),
        "validity": _validity_summary(kept),
        "device_site": _device_site_summary(kept),
        "stimulus_products": products["summary"],
        "manifest_reconciliation": _manifest_reconciliation(kept, split),
        "environment": environment_snapshot(),
    }
    summary["verdict"] = _verdict(summary)
    write_json(f"{ARTIFACT_DIR}/eye_readiness_summary.json", summary)
    write_csv(f"{ARTIFACT_DIR}/coverage_by_unit.csv", _coverage_rows(kept, split))
    ensure_output_path(REPORT_PATH).write_text(render_report(summary), encoding="utf-8")
    print(json.dumps({key: summary[key] for key in ("recordings_discovered", "recordings_kept", "recordings_audited")}))


def _attach_timelines(rows, spec, asdata) -> list[dict[str, Any]]:
    """Carry each 七鑫易维 recording's media timeline on its row.

    The worker processes need the timeline but not the whole project file, which
    would otherwise be pickled once per task.
    """

    out = []
    for row in rows:
        new = dict(row)
        index = asdata.get(str(row.get("device", "")))
        task = str(row.get("task") or "")
        if index is not None and task:
            record = index.get(spec.task(task).qixin_dir, str(row.get("record_name", "")))
            if record is not None:
                new["_timeline"] = [
                    (segment.media, float(segment.start_ms), float(segment.end_ms)) for segment in record.timeline
                ]
        out.append(new)
    return out


def _publishable(row: Mapping[str, Any]) -> dict[str, Any]:
    """Drop the working fields the worker needed but the artifact should not carry."""

    return {key: value for key, value in row.items() if not key.startswith("_")}


def _select(rows: Sequence[Mapping[str, Any]], limit: int) -> list[dict[str, Any]]:
    if limit <= 0:
        return [dict(row) for row in rows]
    seen: Counter[tuple[str, str]] = Counter()
    out: list[dict[str, Any]] = []
    for row in rows:
        key = (str(row["device"]), str(row["task"]))
        if seen[key] >= limit:
            continue
        seen[key] += 1
        out.append(dict(row))
    return out


def _worker_init() -> None:
    spec = load_eye_spec()
    stimulus_dir = raw_data_dir() / spec.device("qixin_120").root / spec.task("free_viewing").qixin_dir
    boxes = eye_stimuli.face_stimulus_boxes(spec, stimulus_dir)
    aois = {item.media: item for item in eye_aoi.build_stimulus_aois(spec, stimulus_dir, ROOT)}
    tracks = {}
    for name in ("prosaccade_formal", "antisaccade_formal", "pursuit"):
        payload = np.load(ROOT / STIMULUS_DIR / f"target_{name}.npz")
        tracks[name] = eye_stimuli.TargetTrack(
            media=str(payload["media"]), fps=float(payload["fps"]), x=payload["x"], y=payload["y"]
        )
    _WORKER.update(
        {
            "spec": spec,
            "boxes": {box.media: box for box in boxes},
            "aois": aois,
            "tracks": tracks,
            "drift_config": spec.task("free_viewing").raw["drift_correction"],
        }
    )


def _audit_recordings(rows: Sequence[Mapping[str, Any]], spec, n_workers: int) -> list[dict[str, Any]]:
    payloads = [dict(row) for row in rows]
    if n_workers <= 1:
        _worker_init()
        return [audit_one(row) for row in payloads]
    with ProcessPoolExecutor(max_workers=n_workers, initializer=_worker_init) as pool:
        return list(pool.map(audit_one, payloads, chunksize=4))


def audit_one(row: Mapping[str, Any]) -> dict[str, Any]:
    """QC and validity for one recording. Reads each raw file exactly once."""

    spec = _WORKER["spec"]
    boxes = _WORKER["boxes"]
    tracks = _WORKER["tracks"]
    device = str(row["device"])
    task = str(row["task"])
    out: dict[str, Any] = {"path": row["path"]}

    try:
        if spec.device(device).kind == "qixin":
            record = _record_stub(row)
            out.update(eye_qc.qixin_qc(spec, row, record))
            trace = eye_validity.qixin_trace(
                str(row["path"]), float(row.get("vendor_duration") or 0) or None
            )
            segments = [(media, start, end) for media, start, end in row.get("_timeline", [])]
        else:
            recording = tobii_io.read_tobii_recording(row["path"])
            out.update(eye_qc.tobii_qc(spec, row))
            trace = eye_validity.tobii_trace(recording, spec.screen)
            segments = [
                (segment.media, segment.start_ms, segment.end_ms) for segment in recording.stimulus_segments()
            ]
    except Exception as error:  # noqa: BLE001 - a broken file must be recorded, not fatal
        out["audit_error"] = f"{type(error).__name__}: {error}"
        return out

    out.update(
        _validity_for(task, trace, segments, boxes, tracks, _WORKER["aois"], _WORKER["drift_config"])
    )
    return out


def _record_stub(row: Mapping[str, Any]):
    """Rebuild the minimal QixinRecord the QC function needs from row fields."""

    timeline = tuple(
        qixin_io.MediaSegment(media=media, index=index, start_ms=int(start), end_ms=int(end))
        for index, (media, start, end) in enumerate(row.get("_timeline", []))
    )
    if not timeline and not row.get("asdata_found"):
        return None
    return qixin_io.QixinRecord(
        experiment="",
        record_name=str(row.get("record_name", "")),
        timeline=timeline,
        qc={key: row.get(f"vendor_{key}") for key in qixin_io.RECORD_QC_FIELDS},
    )


def _validity_for(task, trace, segments, boxes, tracks, aois, drift_config) -> dict[str, Any]:
    if task == "free_viewing":
        drift = eye_drift.estimate_drift(trace, segments, drift_config)
        raw = eye_validity.free_viewing_aoi_shares(trace, segments, aois)
        corrected = eye_validity.free_viewing_aoi_shares(trace, segments, aois, drift)
        return {
            **eye_validity.free_viewing_on_face(trace, segments, boxes, drift),
            **{f"raw_{key}": value for key, value in raw.items() if key.startswith("aoi_")},
            **corrected,
            **drift.as_qc(),
        }

    named = {media: (start, end) for media, start, end in segments}
    out: dict[str, Any] = {}
    if task == "smooth_pursuit" and "平滑追随" in named:
        start, end = named["平滑追随"]
        result = eye_validity.target_following(trace, tracks["pursuit"], start, end)
        out.update({f"pursuit_{key}": value for key, value in result.items()})
    if task == "saccade":
        for media, track_name, anti in (
            ("前扫视-正式", "prosaccade_formal", False),
            ("反扫视-正式", "antisaccade_formal", True),
        ):
            prefix = "anti" if anti else "pro"
            if media not in named:
                continue
            start, end = named[media]
            follow = eye_validity.target_following(trace, tracks[track_name], start, end)
            direction = eye_validity.saccade_direction_agreement(trace, tracks[track_name], start, end, anti)
            out.update({f"{prefix}_{key}": value for key, value in follow.items()})
            out.update({f"{prefix}_{key}": value for key, value in direction.items()})
    return out


def _coverage_rows(rows, split) -> list[dict[str, Any]]:
    out = []
    for (device, task), counts in sorted(coverage_by_unit(rows).items()):
        subjects = {str(row["a_id"]) for row in rows if row["device"] == device and row["task"] == task}
        cv_subjects = [
            split[a_id]
            for a_id in subjects
            if a_id in split and split[a_id]["split_group"] == "cv"
        ]
        labels = [int(item["primary_label_nonhealthy"]) for item in cv_subjects if item["primary_label_nonhealthy"] in {"0", "1"}]
        out.append(
            {
                "device": device,
                "task": task,
                "recordings": counts["recordings"],
                "in_manifest": counts["in_manifest"],
                "cv_subjects": counts["cv"],
                "cv_positive_rate": round(sum(labels) / len(labels), 4) if labels else "",
                "cv_with_eeg": sum(1 for item in cv_subjects if item["has_EEG"] == "1"),
                "cv_with_fnirs": sum(1 for item in cv_subjects if item["has_fNIRS"] == "1"),
                "cv_with_face": sum(1 for item in cv_subjects if item["has_face"] == "1"),
            }
        )
    return out


def _coverage_summary(rows, split) -> dict[str, Any]:
    subjects = {str(row["a_id"]) for row in rows}
    in_manifest = {a_id for a_id in subjects if a_id in split}
    cv = {a_id for a_id in in_manifest if split[a_id]["split_group"] == "cv"}
    per_device = {}
    for device in sorted({str(row["device"]) for row in rows}):
        device_subjects = {str(row["a_id"]) for row in rows if row["device"] == device}
        per_device[device] = {
            "subjects": len(device_subjects),
            "cv": len(device_subjects & cv),
        }
    all_three = {
        device: {str(row["a_id"]) for row in rows if row["device"] == device}
        for device in per_device
    }
    overlaps = {}
    names = sorted(all_three)
    for i, left in enumerate(names):
        for right in names[i + 1 :]:
            overlaps[f"{left}&{right}"] = len(all_three[left] & all_three[right])
    return {
        "unique_subjects": len(subjects),
        "in_manifest": len(in_manifest),
        "cv_subjects": len(cv),
        "per_device": per_device,
        "device_overlap": overlaps,
    }


def _duplicate_summary(discarded) -> dict[str, Any]:
    reasons = Counter(str(row.get("discard_reason", "")) for row in discarded)
    per_unit = Counter(
        (str(row["device"]), str(row.get("task", "")))
        for row in discarded
        if row.get("discard_reason") == "duplicate_take"
    )
    return {
        "reasons": dict(reasons),
        "duplicate_takes_per_unit": {f"{device}/{task}": count for (device, task), count in sorted(per_unit.items())},
        "missing_a_id_examples": [
            redact_record_name(row["record_name"])
            for row in discarded
            if row.get("discard_reason") == "missing_a_id"
        ][:20],
    }


def _conformance_summary(rows) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for device in sorted({str(row["device"]) for row in rows}):
        for task in sorted({str(row["task"]) for row in rows}):
            group = [row for row in rows if row["device"] == device and row["task"] == task and row.get("qc_read_ok")]
            if not group:
                continue
            complete = [int(row.get("timeline_complete", 0) or 0) for row in group]
            entry: dict[str, Any] = {
                "n": len(group),
                "timeline_complete": sum(complete),
                "timeline_complete_rate": round(sum(complete) / len(complete), 4),
                "observed_segment_counts": dict(Counter(int(row.get("n_media_segments", 0) or 0) for row in group).most_common(5)),
                "expected_segments": group[0].get("expected_media_segments", ""),
            }
            if task == "free_viewing":
                errors = [float(row["face_duration_error_ms"]) for row in group if row.get("face_duration_error_ms") is not None]
                if errors:
                    entry["face_duration_error_ms_median"] = round(float(np.median(errors)), 2)
                    entry["face_duration_error_ms_max_abs"] = round(float(np.max(np.abs(errors))), 2)
            out[f"{device}/{task}"] = entry
    return out


def _quality_summary(rows) -> dict[str, Any]:
    fields = [
        "valid_sample_fraction",
        "sampling_rate_hz",
        "clock_scale",
        "n_gaps",
        "longest_gap_ms",
        "pupil_mean_mm",
        "average_calibration_accuracy_deg",
        "duration_agreement",
    ]
    out: dict[str, Any] = {}
    for device in sorted({str(row["device"]) for row in rows}):
        attempted = [row for row in rows if row["device"] == device and "qc_read_ok" in row]
        group = [row for row in attempted if row.get("qc_read_ok")]
        entry: dict[str, Any] = {
            "n": len(group),
            "attempted": len(attempted),
            "read_failures": len(attempted) - len(group),
            "read_failure_examples": [str(row.get("qc_error") or row.get("audit_error")) for row in attempted if not row.get("qc_read_ok")][:5],
        }
        for field in fields:
            values = [row[field] for row in group if isinstance(row.get(field), (int, float)) and row[field] == row[field]]
            if values:
                entry[field] = {
                    "n": len(values),
                    "median": round(float(np.median(values)), 6),
                    "q1": round(float(np.percentile(values, 25)), 6),
                    "q3": round(float(np.percentile(values, 75)), 6),
                }
        below_50 = [row for row in group if isinstance(row.get("valid_sample_fraction"), float) and row["valid_sample_fraction"] < 0.5]
        entry["valid_below_0.5"] = len(below_50)
        out[device] = entry
    return out


def _validity_summary(rows) -> dict[str, Any]:
    checks = {
        "free_viewing": [
            "on_face_fraction",
            "on_face_over_chance",
            "chance_fraction",
            "aoi_eyes_share",
            "aoi_mouth_share",
            "aoi_face_other_share",
            "aoi_off_face_share",
            "aoi_eyes_minus_mouth",
            "raw_aoi_eyes_minus_mouth",
            "drift_dx",
            "drift_dy",
            "drift_n_crosses",
        ],
        "saccade": ["pro_corr_x", "anti_corr_x", "pro_direction_correct_rate", "anti_direction_correct_rate", "pro_n_trials_scored", "anti_n_trials_scored"],
        "smooth_pursuit": ["pursuit_corr_x", "pursuit_corr_y"],
    }
    out: dict[str, Any] = {}
    for device in sorted({str(row["device"]) for row in rows}):
        for task, fields in checks.items():
            group = [row for row in rows if row["device"] == device and row["task"] == task]
            if not group:
                continue
            entry = {}
            for field in fields:
                entry[field] = eye_validity.summarize([row.get(field, float("nan")) for row in group if isinstance(row.get(field), (int, float))])
            out[f"{device}/{task}"] = entry
    return out


def _device_site_summary(rows) -> dict[str, dict[str, int]]:
    table: dict[str, dict[str, int]] = defaultdict(dict)
    seen: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        a_id = str(row.get("a_id") or "")
        if not a_id or str(row.get("split_group")) != "cv":
            continue
        seen[a_id[:3]].add(f"{row['device']}|{a_id}")
    for prefix, entries in seen.items():
        counter: Counter[str] = Counter()
        for entry in entries:
            counter[entry.split("|", 1)[0]] += 1
        table[prefix] = dict(sorted(counter.items()))
    return dict(sorted(table.items()))


def _manifest_reconciliation(rows, split) -> dict[str, Any]:
    subjects = {str(row["a_id"]) for row in rows if str(row.get("a_id") or "")}
    manifest_direct = {row["A_id"] for row in split.values() if row.get("has_eye_direct") == "1"}
    manifest_mapped = {row["A_id"] for row in split.values() if row.get("has_eye_name_mapped") == "1"}
    return {
        "a_id_join_subjects": len(subjects),
        "manifest_has_eye_direct": len(manifest_direct),
        "manifest_has_eye_name_mapped": len(manifest_mapped),
        "found_but_not_flagged_direct": len(subjects - manifest_direct),
        "flagged_direct_but_not_found": len(manifest_direct - subjects),
        "flagged_name_mapped_but_not_found": len(manifest_mapped - subjects),
        "note": (
            "has_eye_direct is computed by chongqing_binary.audit._extract_l_ids, which greps paths for "
            "L\\d+. Eye paths carry A_id only, so the column undercounts. Eye cohorts must join on A_id."
        ),
    }


def _verdict(summary: Mapping[str, Any]) -> dict[str, Any]:
    """Pass or fail each unit against the thresholds, with the reasons."""

    out: dict[str, Any] = {}
    for unit, conformance in summary["conformance"].items():
        device, _, task = unit.partition("/")
        quality = summary["quality"].get(device, {})
        validity = summary["validity"].get(unit, {})
        checks: dict[str, Any] = {}

        checks["timeline_complete"] = {
            "value": conformance["timeline_complete_rate"],
            "threshold": VERDICT_THRESHOLDS["timeline_complete_rate"],
            "pass": conformance["timeline_complete_rate"] >= VERDICT_THRESHOLDS["timeline_complete_rate"],
        }
        valid = (quality.get("valid_sample_fraction") or {}).get("median")
        checks["valid_sample_fraction"] = {
            "value": valid,
            "threshold": VERDICT_THRESHOLDS["valid_sample_fraction"],
            "pass": valid is not None and valid >= VERDICT_THRESHOLDS["valid_sample_fraction"],
        }
        if task == "free_viewing":
            value = (validity.get("on_face_over_chance") or {}).get("median")
            checks["on_face_over_chance"] = {
                "value": value,
                "threshold": VERDICT_THRESHOLDS["on_face_over_chance"],
                "pass": value is not None and value >= VERDICT_THRESHOLDS["on_face_over_chance"],
            }
            gap = (validity.get("aoi_eyes_minus_mouth") or {}).get("median")
            checks["eyes_above_mouth"] = {
                "value": gap,
                "threshold": VERDICT_THRESHOLDS["aoi_eyes_minus_mouth"],
                "pass": gap is not None and gap > VERDICT_THRESHOLDS["aoi_eyes_minus_mouth"],
            }
        if task == "saccade":
            pro = (validity.get("pro_corr_x") or {}).get("median")
            anti = (validity.get("anti_corr_x") or {}).get("median")
            checks["pro_corr_x"] = {
                "value": pro,
                "threshold": VERDICT_THRESHOLDS["pro_corr_x"],
                "pass": pro is not None and pro >= VERDICT_THRESHOLDS["pro_corr_x"],
            }
            checks["anti_corr_x_negative"] = {
                "value": anti,
                "threshold": VERDICT_THRESHOLDS["anti_corr_x_max"],
                "pass": anti is not None and anti < VERDICT_THRESHOLDS["anti_corr_x_max"],
            }
        if task == "smooth_pursuit":
            value = (validity.get("pursuit_corr_x") or {}).get("median")
            checks["pursuit_corr_x"] = {
                "value": value,
                "threshold": VERDICT_THRESHOLDS["pursuit_corr_x"],
                "pass": value is not None and value >= VERDICT_THRESHOLDS["pursuit_corr_x"],
            }
        failed = [name for name, check in checks.items() if not check["pass"]]
        out[unit] = {
            "checks": checks,
            "failed": failed,
            "verdict": "READY" if not failed else "REVIEW",
        }
    return out


def _fmt(value: Any, digits: int = 3) -> str:
    if isinstance(value, float):
        return "n/a" if value != value else f"{value:.{digits}f}"
    return str(value)


def _stat(entry: Mapping[str, Any] | None, digits: int = 3) -> str:
    if not entry or entry.get("n", 0) == 0:
        return "n/a"
    return f"{_fmt(entry['median'], digits)} [{_fmt(entry['q1'], digits)}, {_fmt(entry['q3'], digits)}]"


def render_report(summary: Mapping[str, Any]) -> str:
    coverage = summary["coverage"]
    lines: list[str] = []
    lines.append("# Eye-Tracking Readiness Audit (Goal 2.10)")
    lines.append("")
    lines.append("Stage: readiness only. No features, no models, no labels in any check.")
    lines.append("")
    lines.append(
        f"Specification: `{summary['spec_path']}` "
        f"(paradigm document available: {summary['attachment_available']}; "
        "recovered independently from stimulus media and recorded timelines)."
    )
    lines.append("")

    verdict = summary.get("verdict", {})
    if verdict:
        ready = sum(1 for entry in verdict.values() if entry["verdict"] == "READY")
        lines.append("## Verdict")
        lines.append("")
        lines.append(f"{ready} of {len(verdict)} `device x task` units pass every readiness check.")
        lines.append("")
        lines.append("| unit | verdict | failed checks |")
        lines.append("|---|---|---|")
        for unit, entry in verdict.items():
            failed = ", ".join(entry["failed"]) if entry["failed"] else "-"
            lines.append(f"| `{unit}` | **{entry['verdict']}** | {failed} |")
        lines.append("")
        lines.append(
            "Every threshold is fixed by the paradigm or by physiology, so a failure means a parsing or "
            "acquisition problem, not an absent effect. Thresholds: "
            + ", ".join(f"{key} {value}" for key, value in VERDICT_THRESHOLDS.items())
            + "."
        )
        lines.append("")

    lines.append("## Coverage")
    lines.append("")
    lines.append(
        f"{summary['recordings_discovered']} recordings on disk, {summary['recordings_kept']} kept after "
        f"deduplication, covering **{coverage['unique_subjects']} unique subjects**, "
        f"{coverage['in_manifest']} in the manifest and **{coverage['cv_subjects']} in the development split**."
    )
    lines.append("")
    lines.append("| device | subjects | CV subjects |")
    lines.append("|---|---|---|")
    for device, counts in coverage["per_device"].items():
        lines.append(f"| `{device}` | {counts['subjects']} | {counts['cv']} |")
    lines.append("")
    lines.append("Subjects shared between devices: " + ", ".join(f"{key} {value}" for key, value in coverage["device_overlap"].items()) + ".")
    lines.append("")

    reconciliation = summary["manifest_reconciliation"]
    lines.append("### Manifest reconciliation")
    lines.append("")
    lines.append(
        f"Joining on `A_id` finds {reconciliation['a_id_join_subjects']} subjects against the manifest's "
        f"`has_eye_direct` = {reconciliation['manifest_has_eye_direct']} and "
        f"`has_eye_name_mapped` = {reconciliation['manifest_has_eye_name_mapped']}. "
        f"{reconciliation['found_but_not_flagged_direct']} subjects have a recording that `has_eye_direct` does not flag; "
        f"{reconciliation['flagged_direct_but_not_found']} are flagged with no recording found."
    )
    lines.append("")
    lines.append(reconciliation["note"])
    lines.append("")

    lines.append("## Paradigm conformance")
    lines.append("")
    lines.append("| unit | n | expected segments | complete | rate | observed counts |")
    lines.append("|---|---|---|---|---|---|")
    for unit, entry in summary["conformance"].items():
        observed = ", ".join(f"{key}x{value}" for key, value in entry["observed_segment_counts"].items())
        lines.append(
            f"| `{unit}` | {entry['n']} | {entry['expected_segments']} | {entry['timeline_complete']} | "
            f"{entry['timeline_complete_rate']:.3f} | {observed} |"
        )
    lines.append("")
    for unit, entry in summary["conformance"].items():
        if "face_duration_error_ms_median" in entry:
            lines.append(
                f"- `{unit}` face presentation error against the specified 4000 ms: median "
                f"{entry['face_duration_error_ms_median']} ms, largest absolute "
                f"{entry['face_duration_error_ms_max_abs']} ms."
            )
    lines.append("")

    lines.append("## Acquisition quality")
    lines.append("")
    lines.append("| device | read ok | read failures | valid sample fraction | sampling rate Hz | clock scale | long gaps | pupil mm | valid < 0.5 |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for device, entry in summary["quality"].items():
        lines.append(
            f"| `{device}` | {entry['n']} | {entry['read_failures']} | {_stat(entry.get('valid_sample_fraction'))} | "
            f"{_stat(entry.get('sampling_rate_hz'), 1)} | {_stat(entry.get('clock_scale'), 5)} | {_stat(entry.get('n_gaps'), 1)} | "
            f"{_stat(entry.get('pupil_mean_mm'), 2)} | {entry['valid_below_0.5']} |"
        )
    lines.append("")
    lines.append("Values are median [Q1, Q3] across recordings.")
    lines.append("")

    lines.append("## Label-free validity")
    lines.append("")
    lines.append("| unit | check | median [Q1, Q3] |")
    lines.append("|---|---|---|")
    for unit, entry in summary["validity"].items():
        for check, stat in entry.items():
            if stat.get("n", 0):
                lines.append(f"| `{unit}` | {check} | {_stat(stat)} |")
    lines.append("")

    geometry = summary["stimulus_products"].get("aoi_geometry")
    if geometry:
        lines.append("## Stimulus regions")
        lines.append("")
        lines.append(
            f"{geometry['n']} stimuli, detector `{geometry['detector']}`, lowest detection score "
            f"{geometry['detector_score_min']:.3f}. Eye and mouth bands disjoint: {geometry['disjoint']}; "
            f"both inside the visible face: {geometry['inside_face']}. Median screen-area share: eyes "
            f"{geometry['eyes_area_share_median']:.4f}, mouth {geometry['mouth_area_share_median']:.4f}, "
            f"face {geometry['face_area_share_median']:.4f}."
        )
        lines.append("")

    lines.append("## Device and acquisition site")
    lines.append("")
    devices = sorted({device for counts in summary["device_site"].values() for device in counts})
    lines.append("| A_id prefix | " + " | ".join(f"`{device}`" for device in devices) + " |")
    lines.append("|---" * (len(devices) + 1) + "|")
    for prefix, counts in summary["device_site"].items():
        lines.append(f"| {prefix} | " + " | ".join(str(counts.get(device, 0)) for device in devices) + " |")
    lines.append("")
    lines.append(
        "CV subjects only. A prefix served by a single device means device and acquisition site cannot be "
        "separated there, exactly as for the two fNIRS devices."
    )
    lines.append("")

    lines.append("## Deduplication")
    lines.append("")
    duplicates = summary["duplicates"]
    lines.append("Discard reasons: " + ", ".join(f"{key} {value}" for key, value in duplicates["reasons"].items()) + ".")
    lines.append("")
    lines.append("Duplicate takes per unit: " + ", ".join(f"{key} {value}" for key, value in duplicates["duplicate_takes_per_unit"].items()) + ".")
    lines.append("")
    lines.append(
        "The kept take is the one with a complete presentation timeline, then the most media segments, then the "
        "longest recording, then the latest. Every component comes from the recording, never from the label."
    )
    lines.append("")

    lines.append("## Stimulus-side products")
    lines.append("")
    products = summary["stimulus_products"]
    faces = products["face_boxes"]
    lines.append(
        f"{faces['n']} free-viewing face stimuli, median face box covering {faces['area_fraction_median']:.4f} of the "
        f"screen, x in [{faces['x_range'][0]:.3f}, {faces['x_range'][1]:.3f}], "
        f"y in [{faces['y_range'][0]:.3f}, {faces['y_range'][1]:.3f}]."
    )
    lines.append("")
    lines.append("| video | frames | fps | duration ms | target x | trials |")
    lines.append("|---|---|---|---|---|---|")
    for name, entry in products["targets"].items():
        levels = entry["unique_x"]
        # A step paradigm holds a handful of positions; a pursuit target sweeps
        # through hundreds, so listing them would say nothing.
        if len(levels) <= 8:
            positions = ", ".join(f"{value:g}" for value in levels)
            trials = str(entry.get("n_saccade_trials", ""))
        else:
            positions = f"continuous, {len(levels)} distinct in [{min(levels):g}, {max(levels):g}]"
            trials = "-"
        lines.append(
            f"| {name} | {entry['n_frames']} | {entry['fps']:.0f} | {entry['duration_ms']:.0f} | "
            f"{positions} | {trials} |"
        )
    lines.append("")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
