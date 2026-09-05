#!/usr/bin/env python3
"""Index EEG BDF files for Chongqing v1 baselines.

This script reads only directory names and BDF headers. It never writes inside
the raw dataset and intentionally does not record named main BDF files.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path

from _paths import DATA_ROOT, V1_ROOT

TASKS = {
    "rest": {"dir": "1_rest-1334", "stem": "eeg_rest", "task_label": "rest"},
    "oddball": {"dir": "2_Oldball-2358", "stem": "eeg_oddball", "task_label": "oddball"},
    "nback": {"dir": "4_1BACK-1810", "stem": "eeg_1back", "task_label": "1back"},
}


@dataclass
class BdfHeader:
    status: str
    n_channels: int | None = None
    n_records: int | None = None
    record_duration_sec: float | None = None
    sampling_rate_hz: float | None = None
    duration_sec: float | None = None
    labels: list[str] | None = None
    error: str = ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", choices=sorted(TASKS), default="rest")
    parser.add_argument("--limit", type=int, default=None, help="Limit subjects for smoke tests.")
    parser.add_argument("--data-root", type=Path, default=DATA_ROOT)
    parser.add_argument("--out-dir", type=Path, default=V1_ROOT / "eeg" / "artifacts" / "index")
    return parser.parse_args()


def parse_l_id(path: Path) -> str:
    match = re.search(r"L\d+", path.name, flags=re.IGNORECASE)
    return match.group(0).upper() if match else ""


def choose_role_file(subject_dir: Path, role: str) -> Path | None:
    candidates = sorted(subject_dir.glob("*.bdf"))
    role = role.lower()
    if role == "data":
        exact = [p for p in candidates if p.name.lower() == "data.bdf"]
        suffixed = [p for p in candidates if p.name.lower().endswith("_data.bdf")]
    elif role == "evt":
        exact = [p for p in candidates if p.name.lower() == "evt.bdf"]
        suffixed = [p for p in candidates if p.name.lower().endswith("_evt.bdf")]
    else:
        raise ValueError(role)
    matches = suffixed or exact
    return matches[0] if matches else None


def read_bdf_header(path: Path | None) -> BdfHeader:
    if path is None:
        return BdfHeader(status="missing", error="file_not_found")
    try:
        with path.open("rb") as f:
            fixed = f.read(256)
            if len(fixed) < 256:
                return BdfHeader(status="bad_header", error="header_too_short")
            n_channels = int(fixed[252:256].decode("ascii", errors="ignore").strip() or 0)
            n_records = int(float(fixed[236:244].decode("ascii", errors="ignore").strip() or 0))
            record_duration = float(fixed[244:252].decode("ascii", errors="ignore").strip() or 0)
            labels = [f.read(16).decode("ascii", errors="ignore").strip() for _ in range(n_channels)]
            # Skip transducer, physical dimension/min/max, digital min/max, and prefilter fields.
            f.seek(256 + 16 * n_channels + 80 * n_channels + 8 * n_channels * 5 + 80 * n_channels)
            samples_per_record = [
                int(f.read(8).decode("ascii", errors="ignore").strip() or 0)
                for _ in range(n_channels)
            ]
        sampling_rate = None
        if record_duration > 0 and samples_per_record:
            sampling_rate = samples_per_record[0] / record_duration
        duration = n_records * record_duration if n_records >= 0 and record_duration > 0 else None
        return BdfHeader(
            status="ok",
            n_channels=n_channels,
            n_records=n_records,
            record_duration_sec=record_duration,
            sampling_rate_hz=sampling_rate,
            duration_sec=duration,
            labels=labels,
        )
    except Exception as exc:  # noqa: BLE001 - keep QA robust across malformed BDF files.
        return BdfHeader(status="read_error", error=repr(exc))


def safe_path(path: Path | None) -> str:
    return str(path) if path is not None else ""


def make_row(task: str, subject_dir: Path) -> dict[str, object]:
    data_file = choose_role_file(subject_dir, "data")
    evt_file = choose_role_file(subject_dir, "evt")
    data_header = read_bdf_header(data_file)
    evt_header = read_bdf_header(evt_file)
    l_id = parse_l_id(subject_dir)
    qc_issues = []
    if not l_id:
        qc_issues.append("missing_l_id")
    if data_file is None:
        qc_issues.append("missing_data_bdf")
    if evt_file is None:
        qc_issues.append("missing_evt_bdf")
    if data_header.status != "ok":
        qc_issues.append(f"data_header_{data_header.status}")
    if data_header.n_channels is not None and data_header.n_channels < 16:
        qc_issues.append("low_channel_count")
    if data_header.duration_sec is not None and data_header.duration_sec < 60:
        qc_issues.append("short_duration_lt_60s")
    status = "ok" if not qc_issues else "warn"
    if data_file is None or data_header.status != "ok":
        status = "fail"
    return {
        "task": TASKS[task]["task_label"],
        "task_dir": TASKS[task]["dir"],
        "subject_dir": subject_dir.name,
        "L_id": l_id,
        "data_file": safe_path(data_file),
        "evt_file": safe_path(evt_file),
        "data_file_size_bytes": data_file.stat().st_size if data_file else "",
        "evt_file_size_bytes": evt_file.stat().st_size if evt_file else "",
        "data_header_status": data_header.status,
        "evt_header_status": evt_header.status,
        "n_channels": data_header.n_channels if data_header.n_channels is not None else "",
        "sampling_rate_hz": data_header.sampling_rate_hz if data_header.sampling_rate_hz is not None else "",
        "n_records": data_header.n_records if data_header.n_records is not None else "",
        "record_duration_sec": data_header.record_duration_sec if data_header.record_duration_sec is not None else "",
        "duration_sec": data_header.duration_sec if data_header.duration_sec is not None else "",
        "channel_labels": "|".join(data_header.labels or []),
        "qc_status": status,
        "qc_issues": "|".join(qc_issues),
    }


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "task",
        "task_dir",
        "subject_dir",
        "L_id",
        "data_file",
        "evt_file",
        "data_file_size_bytes",
        "evt_file_size_bytes",
        "data_header_status",
        "evt_header_status",
        "n_channels",
        "sampling_rate_hz",
        "n_records",
        "record_duration_sec",
        "duration_sec",
        "channel_labels",
        "qc_status",
        "qc_issues",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_report(path: Path, rows: list[dict[str, object]], args: argparse.Namespace) -> None:
    status_counts: dict[str, int] = {}
    issue_counts: dict[str, int] = {}
    for row in rows:
        status_counts[str(row["qc_status"])] = status_counts.get(str(row["qc_status"]), 0) + 1
        for issue in str(row["qc_issues"]).split("|"):
            if issue:
                issue_counts[issue] = issue_counts.get(issue, 0) + 1
    duplicate_l = sorted(
        lid for lid in {str(r["L_id"]) for r in rows if r["L_id"]}
        if sum(1 for r in rows if r["L_id"] == lid) > 1
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        f.write(f"# EEG {args.task} File Index QA\n\n")
        f.write(f"- Data root: `{args.data_root}`\n")
        f.write(f"- Task directory: `{TASKS[args.task]['dir']}`\n")
        f.write(f"- Subject directories indexed: {len(rows)}\n")
        f.write(f"- QC status counts: `{json.dumps(status_counts, ensure_ascii=False)}`\n")
        f.write(f"- QC issue counts: `{json.dumps(issue_counts, ensure_ascii=False)}`\n")
        f.write(f"- Duplicate L_id count: {len(duplicate_l)}\n")
        f.write("- Named main BDF paths are intentionally not recorded.\n")


def main() -> None:
    args = parse_args()
    task_root = args.data_root / "脑电" / TASKS[args.task]["dir"]
    if not task_root.exists():
        raise FileNotFoundError(task_root)
    subject_dirs = sorted([p for p in task_root.iterdir() if p.is_dir()])
    if args.limit is not None:
        subject_dirs = subject_dirs[: args.limit]
    rows = [make_row(args.task, subject_dir) for subject_dir in subject_dirs]
    stem = TASKS[args.task]["stem"]
    csv_path = args.out_dir / f"{stem}_file_index.csv"
    report_path = args.out_dir / f"{stem}_file_index_qa.md"
    write_csv(csv_path, rows)
    write_report(report_path, rows, args)
    print(json.dumps({"rows": len(rows), "csv": str(csv_path), "report": str(report_path)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
