"""Shared utilities for Goal 2.5 modality readiness audits."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
L_ID_RE = re.compile(r"(?<![A-Za-z0-9])L\d+(?![A-Za-z0-9])", re.IGNORECASE)


def read_yaml(path: str | Path) -> dict[str, Any]:
    path = resolve_project_path(path)
    try:
        import yaml  # type: ignore

        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
        if not isinstance(data, dict):
            raise ValueError(f"YAML root must be a mapping: {path}")
        return data
    except ModuleNotFoundError:
        return _read_simple_yaml(path)


def _read_simple_yaml(path: Path) -> dict[str, Any]:
    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any] | list[Any]]] = [(-1, root)]
    lines = path.read_text(encoding="utf-8").splitlines()
    for line_no, raw in enumerate(lines):
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        text = line.strip()
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if text.startswith("- "):
            if not isinstance(parent, list):
                raise ValueError(f"Unsupported YAML list placement in {path}: {raw}")
            parent.append(_parse_scalar(text[2:].strip()))
            continue
        if ":" not in text:
            raise ValueError(f"Unsupported YAML line in {path}: {raw}")
        key, value = text.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value:
            parsed: Any = _parse_scalar(value)
        else:
            parsed = [] if _next_significant_is_list(lines, line_no, indent) else {}
        if isinstance(parent, dict):
            parent[key] = parsed
        else:
            raise ValueError(f"Unsupported YAML mapping placement in {path}: {raw}")
        if isinstance(parsed, (dict, list)):
            stack.append((indent, parsed))
    return root


def _next_significant_is_list(lines: Sequence[str], current_line_no: int, current_indent: int) -> bool:
    for raw in lines[current_line_no + 1 :]:
        stripped = raw.split("#", 1)[0].rstrip()
        if not stripped.strip():
            continue
        indent = len(stripped) - len(stripped.lstrip(" "))
        return indent > current_indent and stripped.strip().startswith("- ")
    return False


def _parse_scalar(value: str) -> Any:
    if value in {"null", "Null", "NULL", "~"}:
        return None
    if value in {"true", "True", "TRUE"}:
        return True
    if value in {"false", "False", "FALSE"}:
        return False
    if (value.startswith("'") and value.endswith("'")) or (value.startswith('"') and value.endswith('"')):
        return value[1:-1]
    try:
        if "." not in value:
            return int(value)
        return float(value)
    except ValueError:
        return value


def resolve_project_path(path: str | Path) -> Path:
    value = Path(path)
    if not value.is_absolute():
        value = PROJECT_ROOT / value
    return value.resolve()


def load_readiness_config(path: str | Path | None = None) -> dict[str, Any]:
    cfg_path = resolve_project_path(path or PROJECT_ROOT / "configs" / "readiness" / "default.yaml")
    data = read_yaml(cfg_path)
    inherited = data.pop("extends", None)
    if inherited:
        parent_path = Path(inherited)
        if not parent_path.is_absolute():
            parent_path = cfg_path.parent / parent_path
        data = _deep_merge(read_yaml(parent_path), data)
    parent = data.get("project_config")
    if parent:
        data = _deep_merge(read_yaml(parent), data)
    data["_config_path"] = str(cfg_path)
    return data


def _deep_merge(base: dict[str, Any], override: Mapping[str, Any]) -> dict[str, Any]:
    result = dict(base)
    for key, value in override.items():
        if isinstance(value, Mapping) and isinstance(result.get(key), Mapping):
            result[key] = _deep_merge(dict(result[key]), value)
        else:
            result[key] = value
    return result


def readonly_roots(config: Mapping[str, Any] | None = None) -> list[Path]:
    if config is None:
        config = load_readiness_config(None)
    values = list(config.get("readonly_inputs", []))
    if not values:
        values = [
            "/home/qiangminc/codes/data4_qiangminc/datasets_qiangmin/chongqing",
            "inputs/derived_reports/chongqing_binary_diagnosis_report",
        ]
    return [resolve_project_path(str(value)) for value in values]


def ensure_output_path(path: str | Path, config: Mapping[str, Any] | None = None) -> Path:
    target = resolve_project_path(path)
    for root in readonly_roots(config):
        if target == root or target.is_relative_to(root):
            raise PermissionError(f"Refusing to write under read-only input: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


def read_csv(path: str | Path) -> list[dict[str, str]]:
    with resolve_project_path(path).open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: str | Path, rows: Sequence[Mapping[str, Any]], fieldnames: Sequence[str] | None = None) -> Path:
    target = ensure_output_path(path)
    if fieldnames is None:
        fieldnames = union_fieldnames(rows)
    with target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _cell(row.get(key, "")) for key in fieldnames})
    return target


def union_fieldnames(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    seen: list[str] = []
    for row in rows:
        for key in row:
            if key not in seen:
                seen.append(str(key))
    return seen


def write_json(path: str | Path, data: Any) -> Path:
    target = ensure_output_path(path)
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target


def _cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        if value != value:
            return ""
        return f"{value:.8g}"
    return str(value)


def split_rows(config: Mapping[str, Any] | None = None) -> list[dict[str, str]]:
    config = config or load_readiness_config(None)
    return read_csv(config.get("paths", {}).get("split_file", "artifacts/splits/subject_splits_v1.csv"))


def split_by_l_id(config: Mapping[str, Any] | None = None) -> dict[str, dict[str, str]]:
    return {row["L_id"]: row for row in split_rows(config)}


def manifest_rows(config: Mapping[str, Any] | None = None) -> list[dict[str, str]]:
    config = config or load_readiness_config(None)
    manifest = config.get("paths", {}).get(
        "subject_manifest",
        "inputs/derived_reports/chongqing_binary_diagnosis_report/data/subject_manifest.csv",
    )
    return read_csv(manifest)


def base_subject_fields(row: Mapping[str, str]) -> dict[str, str]:
    keys = [
        "A_id",
        "L_id",
        "primary_label_nonhealthy",
        "sensitivity_label_clear_diagnosis",
        "sensitivity_label_mdd_highrisk",
        "sex",
        "age",
        "age_bin",
        "grade",
        "grade_group",
        "has_EEG",
        "has_fNIRS",
        "has_face",
        "has_eye_direct",
        "has_eye_name_mapped",
        "split_group",
        "split_role",
        "is_locked_test",
        "cv_fold",
        "fnirs_device",
    ]
    return {key: row.get(key, "") for key in keys}


def extract_l_ids(text: str) -> list[str]:
    return [match.group(0).upper() for match in L_ID_RE.finditer(text)]


def stable_hash(value: str) -> int:
    return int(hashlib.sha1(value.encode("utf-8")).hexdigest(), 16)


def sha1_short(value: str | Path) -> str:
    return hashlib.sha1(str(value).encode("utf-8")).hexdigest()[:12]


def path_hash(path: str | Path) -> str:
    return sha1_short(Path(path).resolve())


def stable_subject_sample(rows: Sequence[Mapping[str, str]], limit_per_class: int, seed: int = 0) -> list[dict[str, str]]:
    eligible = [
        dict(row)
        for row in rows
        if row.get("split_group") == "cv" and row.get("primary_label_nonhealthy") in {"0", "1"}
    ]
    selected: list[dict[str, str]] = []
    for label in ("0", "1"):
        group = [row for row in eligible if row.get("primary_label_nonhealthy") == label]
        group.sort(key=lambda row: stable_hash(f"{seed}:{row.get('L_id','')}"))
        selected.extend(group[:limit_per_class])
    selected.sort(key=lambda row: row.get("L_id", ""))
    return selected


def require_cv_only(rows: Sequence[Mapping[str, str]]) -> None:
    leaks = [row.get("L_id", "") for row in rows if row.get("split_group") != "cv"]
    if leaks:
        raise ValueError(f"Smoke rows must come from CV pool only; examples: {leaks[:5]}")


def count_true(rows: Iterable[Mapping[str, Any]], column: str) -> int:
    return sum(1 for row in rows if str(row.get(column, "")) in {"1", "true", "True"})


def value_counts(rows: Iterable[Mapping[str, Any]], column: str) -> dict[str, int]:
    return dict(Counter(str(row.get(column, "") or "[missing]") for row in rows))


def raw_data_dir(config: Mapping[str, Any] | None = None) -> Path:
    config = config or load_readiness_config(None)
    return resolve_project_path(
        config.get("paths", {}).get(
            "raw_data_dir",
            "/home/qiangminc/codes/data4_qiangminc/datasets_qiangmin/chongqing",
        )
    )


def environment_snapshot() -> dict[str, Any]:
    snap: dict[str, Any] = {
        "python": sys.version.replace("\n", " "),
        "executable": sys.executable,
        "platform": platform.platform(),
        "packages": {},
        "cuda": {},
    }
    for module in ["yaml", "numpy", "pandas", "scipy", "sklearn", "torch", "torchvision", "cv2"]:
        snap["packages"][module] = _module_version(module)
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=index,name,memory.total,memory.used,utilization.gpu", "--format=csv,noheader"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
        snap["cuda"]["nvidia_smi"] = result.stdout.strip().splitlines()
    except Exception as exc:  # pragma: no cover
        snap["cuda"]["nvidia_smi_error"] = str(exc)
    try:
        import torch  # type: ignore

        snap["cuda"]["torch_cuda_available"] = bool(torch.cuda.is_available())
        snap["cuda"]["torch_cuda_version"] = getattr(torch.version, "cuda", None)
        snap["cuda"]["torch_device_count"] = int(torch.cuda.device_count())
    except Exception as exc:
        snap["cuda"]["torch_error"] = str(exc)
    return snap


def _module_version(module: str) -> str | None:
    try:
        imported = __import__(module)
        return str(getattr(imported, "__version__", "installed"))
    except Exception:
        return None


def text_table(counts: Mapping[str, Any]) -> str:
    lines = ["| metric | value |", "|---|---:|"]
    for key, value in counts.items():
        lines.append(f"| `{key}` | {value} |")
    return "\n".join(lines)


def project_file_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with resolve_project_path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def raw_tree_fingerprint(root: str | Path, max_files: int = 200000) -> dict[str, Any]:
    root = Path(root).resolve()
    count = 0
    size = 0
    latest_mtime = 0.0
    digest = hashlib.sha256()
    for dirpath, _, filenames in os.walk(root):
        for name in sorted(filenames):
            path = Path(dirpath) / name
            try:
                stat = path.stat()
            except OSError:
                continue
            rel = path.relative_to(root).as_posix()
            count += 1
            size += stat.st_size
            latest_mtime = max(latest_mtime, stat.st_mtime)
            if count <= max_files:
                digest.update(f"{rel}|{stat.st_size}|{int(stat.st_mtime)}\n".encode("utf-8", "ignore"))
    return {
        "root": str(root),
        "file_count": count,
        "total_size_bytes": size,
        "latest_mtime": latest_mtime,
        "metadata_sha256_prefix": digest.hexdigest()[:16],
    }
