"""Discovery, subject resolution and deduplication of eye-tracking recordings.

Eye recordings are keyed on `A_id`, not `L_id`. `chongqing_binary.audit`
greps paths for `L\\d+`, which no eye path carries, which is why the manifest
records 291 eye subjects against the 1187 that actually exist.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .spec import EyeParadigmSpec

A_ID_RE = re.compile(r"(?<![A-Za-z0-9])([A-Z]\d{5})(?![0-9])")

# A recording directory embeds the subject's personal name beside the A_id
# (`A02062_<name>_251105161924`, `C17049-<name>`). The A_id is the key and the
# name is never used, but it travels in `record_name` and `path` into any CSV,
# report or summary written from them. Anything leaving this machine goes
# through here first. The A_id and the timestamp survive, so a defect example
# still makes its point.
_PERSONAL_NAME_RE = re.compile(r"[\u4e00-\u9fff]{2,4}")


def redact_record_name(name: str) -> str:
    """Replace CJK personal-name runs in a recording name with a placeholder."""

    return _PERSONAL_NAME_RE.sub("<name>", str(name))
QIXIN_DIR_RE = re.compile(r"^(?P<a_id>[A-Z]\d{5})_(?P<name>.*)_(?P<stamp>\d{12})$")
TOBII_FILE_RE = re.compile(r"^眼动-tobbi\s*(?P<stem>.+?)_(?P<suffix>[A-Za-z]+)$")

# Directory names inside a 七鑫易维 task folder that are not subject recordings.
QIXIN_NON_SUBJECT_DIRS = {"thumb"}


@dataclass(frozen=True)
class RecordingKey:
    device: str
    task: str
    a_id: str


def extract_a_id(text: str) -> str | None:
    match = A_ID_RE.search(text)
    return match.group(1) if match else None


def discover_recordings(spec: EyeParadigmSpec, raw_root: Path) -> list[dict[str, Any]]:
    """Every eye recording on disk, one row each, before deduplication."""

    rows: list[dict[str, Any]] = []
    for device in spec.devices.values():
        root = raw_root / device.root
        if device.kind == "qixin":
            rows.extend(_discover_qixin(spec, device.name, root))
        else:
            rows.extend(_discover_tobii(spec, device.name, root))
    rows.sort(key=lambda row: (row["device"], row["task"], row["a_id"] or "", row["path"]))
    return rows


def _discover_qixin(spec: EyeParadigmSpec, device: str, root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for task_name, task in spec.tasks.items():
        task_dir = root / task.qixin_dir
        if not task_dir.is_dir():
            continue
        for entry in sorted(task_dir.iterdir()):
            if not entry.is_dir() or entry.name in QIXIN_NON_SUBJECT_DIRS:
                continue
            match = QIXIN_DIR_RE.match(entry.name)
            a_id = match.group("a_id") if match else extract_a_id(entry.name)
            rows.append(
                {
                    "device": device,
                    "task": task_name,
                    "a_id": a_id,
                    "record_name": entry.name,
                    "path": str(entry),
                    "recorded_at": match.group("stamp") if match else "",
                    "a_id_pattern": "canonical" if match else ("loose" if a_id else "missing"),
                    "size_bytes": _dir_size(entry),
                }
            )
    return rows


def _discover_tobii(spec: EyeParadigmSpec, device: str, root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not root.is_dir():
        return rows
    for path in sorted(root.rglob("*.xlsx")):
        if path.name.startswith("~$"):
            continue
        match = TOBII_FILE_RE.match(path.stem)
        suffix = match.group("suffix") if match else ""
        task_name = spec.task_for_tobii_suffix(suffix) if suffix else None
        a_id = extract_a_id(path.name)
        relative = path.relative_to(root).parts
        rows.append(
            {
                "device": device,
                "task": task_name or "",
                "a_id": a_id,
                "record_name": path.stem,
                "path": str(path),
                "recorded_at": relative[1] if len(relative) > 1 else "",
                "site_dir": relative[0] if relative else "",
                "filename_suffix": suffix,
                "a_id_pattern": "canonical" if a_id else "missing",
                "size_bytes": path.stat().st_size,
            }
        )
    return rows


def _dir_size(directory: Path) -> int:
    total = 0
    for child in directory.iterdir():
        if child.is_file():
            total += child.stat().st_size
    return total


def attach_subjects(
    rows: Sequence[Mapping[str, Any]],
    split_by_a_id: Mapping[str, Mapping[str, str]],
) -> list[dict[str, Any]]:
    """Join recordings to the fixed split on `A_id`, never on name."""

    out: list[dict[str, Any]] = []
    for row in rows:
        new = dict(row)
        subject = split_by_a_id.get(str(row.get("a_id") or ""))
        new["in_manifest"] = int(subject is not None)
        new["L_id"] = subject["L_id"] if subject else ""
        new["split_group"] = subject["split_group"] if subject else ""
        new["cv_fold"] = subject.get("cv_fold", "") if subject else ""
        new["group_prefix3"] = (str(row.get("a_id") or "")[:3]) if row.get("a_id") else ""
        out.append(new)
    return out


def duplicate_score(row: Mapping[str, Any]) -> tuple:
    """Rank competing takes of the same subject-task.

    A complete presentation timeline beats an incomplete one, then more media
    segments, then a longer recording, then the later take. Every component
    comes from the recording itself, never from the label.
    """

    return (
        int(row.get("timeline_complete", 0) or 0),
        int(row.get("n_media_segments", 0) or 0),
        float(row.get("record_duration_ms", 0) or 0),
        float(row.get("size_bytes", 0) or 0),
        str(row.get("recorded_at", "")),
    )


def resolve_duplicates(rows: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Split rows into the kept take per (device, task, A_id) and the discards.

    Rows with no `A_id` or no resolved task are never kept; they are returned as
    discards carrying the reason, so the audit can report them rather than let
    them vanish.
    """

    grouped: dict[RecordingKey, list[Mapping[str, Any]]] = {}
    discarded: list[dict[str, Any]] = []
    for row in rows:
        a_id = str(row.get("a_id") or "")
        task = str(row.get("task") or "")
        if not a_id or not task:
            reason = "missing_a_id" if not a_id else "unresolved_task"
            discarded.append({**row, "discard_reason": reason, "duplicate_rank": ""})
            continue
        grouped.setdefault(RecordingKey(str(row["device"]), task, a_id), []).append(row)

    kept: list[dict[str, Any]] = []
    for key, group in sorted(grouped.items(), key=lambda item: (item[0].device, item[0].task, item[0].a_id)):
        ordered = sorted(group, key=duplicate_score, reverse=True)
        best = dict(ordered[0])
        best["n_takes"] = len(ordered)
        best["duplicate_rank"] = 1
        kept.append(best)
        for rank, loser in enumerate(ordered[1:], start=2):
            discarded.append(
                {
                    **loser,
                    "discard_reason": "duplicate_take",
                    "duplicate_rank": rank,
                    "n_takes": len(ordered),
                    "kept_path": best["path"],
                }
            )
    return kept, discarded


def coverage_by_unit(rows: Iterable[Mapping[str, Any]]) -> dict[tuple[str, str], dict[str, int]]:
    """Subject counts per `device x task`, split by manifest and CV membership."""

    out: dict[tuple[str, str], dict[str, int]] = {}
    for row in rows:
        key = (str(row["device"]), str(row["task"]))
        bucket = out.setdefault(key, {"recordings": 0, "in_manifest": 0, "cv": 0})
        bucket["recordings"] += 1
        bucket["in_manifest"] += int(row.get("in_manifest", 0) or 0)
        bucket["cv"] += int(str(row.get("split_group", "")) == "cv")
    return out
