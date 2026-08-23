#!/usr/bin/env python3
"""Build deterministic Goal 2.7 OOF archives and a release manifest."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import shutil
import sys
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

OOF_FILES = [
    Path("results/goal2_7/all_oof_predictions_standard_cv.csv"),
    Path("results/goal2_7/all_oof_predictions_group_cv.csv"),
]
MANIFEST_PATH = Path("artifacts/goal2_7/release_manifest.json")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_deterministic_gzip(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with source.open("rb") as source_handle, destination.open("wb") as raw_output:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw_output, compresslevel=9, mtime=0) as archive:
            shutil.copyfileobj(source_handle, archive, length=1024 * 1024)


def _goal_files() -> list[Path]:
    files: set[Path] = set()
    directory_roots = [
        Path("configs/goal2_7"),
        Path("src/chongqing_binary/goal2_7"),
        Path("artifacts/goal2_7"),
        Path("results/goal2_7"),
    ]
    for relative_root in directory_roots:
        root = PROJECT_ROOT / relative_root
        if root.exists():
            files.update(path for path in root.rglob("*") if path.is_file())
    files.update((PROJECT_ROOT / "scripts").glob("*goal2_7*.py"))
    files.update((PROJECT_ROOT / "reports").glob("goal2_7_*.md"))
    files.add(PROJECT_ROOT / "tests/test_goal2_7_protocol.py")
    for relative in ["AGENTS.md", "PROJECT_SPEC.md", "EXPERIMENT_PROTOCOL.md", "PROGRESS.md", ".gitignore", "configs/default.yaml"]:
        files.add(PROJECT_ROOT / relative)
    return sorted(
        path
        for path in files
        if path.exists()
        and path != PROJECT_ROOT / MANIFEST_PATH
        and "__pycache__" not in path.parts
        and path.suffix not in {".pyc", ".pyo"}
    )


def _disposition(path: Path) -> tuple[str, str]:
    relative = path.relative_to(PROJECT_ROOT).as_posix()
    if relative.startswith("artifacts/goal2_7/face/contact_sheets/"):
        return "local_sensitive_audit", "Identifiable source-video frames are not published."
    if relative.endswith(".part.csv"):
        return "local_intermediate", "Restart checkpoint; final output or summary is published."
    if relative.startswith("artifacts/goal2_7/face/") and "_signal_features" in relative and relative.endswith(".csv"):
        return "local_large_regenerable", "Frozen visual embeddings exceed the normal Git release budget and are reproducible from config."
    if relative in {path.as_posix() for path in OOF_FILES}:
        return "local_uncompressed", "Uncompressed CSV exceeds GitHub's per-file limit; deterministic .csv.gz archive is published."
    return "github_release", "Included in the formal Goal 2.7 release."


def build_release(create_archives: bool = True) -> dict[str, object]:
    archive_rows = []
    for relative in OOF_FILES:
        source = PROJECT_ROOT / relative
        archive = Path(f"{source}.gz")
        if not source.exists():
            if not archive.exists():
                raise FileNotFoundError(f"Missing OOF source and archive: {relative}")
        elif create_archives:
            _write_deterministic_gzip(source, archive)
        archive_rows.append(
            {
                "source": relative.as_posix(),
                "archive": archive.relative_to(PROJECT_ROOT).as_posix(),
                "source_rows": sum(1 for _ in source.open("rb")) - 1 if source.exists() else None,
                "archive_bytes": archive.stat().st_size,
                "archive_sha256": _sha256(archive),
            }
        )

    file_rows = []
    for path in _goal_files():
        disposition, reason = _disposition(path)
        file_rows.append(
            {
                "path": path.relative_to(PROJECT_ROOT).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": _sha256(path),
                "disposition": disposition,
                "reason": reason,
            }
        )

    manifest = {
        "goal": "Goal 2.7",
        "release_date": date.today().isoformat(),
        "release_policy": {
            "github_release": "Source, configs, tests, reports, compact features, metrics, manifests, and compressed OOF archives.",
            "local_only": "Large Face embeddings, .part checkpoints, uncompressed OOF CSVs, and identifiable contact sheets.",
        },
        "oof_archives": archive_rows,
        "files": file_rows,
        "counts_by_disposition": {
            disposition: sum(row["disposition"] == disposition for row in file_rows)
            for disposition in sorted({row["disposition"] for row in file_rows})
        },
    }
    output = PROJECT_ROOT / MANIFEST_PATH
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-archives", action="store_true", help="Refresh hashes without rebuilding existing .csv.gz archives.")
    args = parser.parse_args()
    manifest = build_release(create_archives=not args.skip_archives)
    print(
        json.dumps(
            {
                "manifest": str(PROJECT_ROOT / MANIFEST_PATH),
                "files": len(manifest["files"]),
                "counts_by_disposition": manifest["counts_by_disposition"],
                "oof_archives": manifest["oof_archives"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
