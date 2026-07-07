"""Environment version recording utilities."""

from __future__ import annotations

import importlib.metadata
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import ProjectConfig


KEY_DEPENDENCIES = [
    "numpy",
    "pandas",
    "scipy",
    "scikit-learn",
    "mne",
    "pyyaml",
    "joblib",
    "torch",
    "torchvision",
    "torchaudio",
    "lightgbm",
    "matplotlib",
    "seaborn",
    "tqdm",
    "einops",
]


def collect_environment() -> dict[str, Any]:
    info: dict[str, Any] = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "python": {
            "version": sys.version.replace("\n", " "),
            "executable": sys.executable,
            "platform": platform.platform(),
        },
        "dependencies": {name: _version(name) for name in KEY_DEPENDENCIES},
        "cuda": {"available": None, "torch_cuda_version": None, "device_count": None},
    }
    try:
        import torch

        info["cuda"] = {
            "available": bool(torch.cuda.is_available()),
            "torch_cuda_version": torch.version.cuda,
            "device_count": int(torch.cuda.device_count()),
        }
        info["pytorch"] = {"version": torch.__version__}
    except Exception as exc:  # pragma: no cover - defensive environment capture
        info["pytorch"] = {"version": _version("torch"), "error": str(exc)}
    return info


def write_environment_report(config: ProjectConfig) -> tuple[Path, Path]:
    info = collect_environment()
    json_path = config.output_path("artifacts_dir", "environment_versions.json")
    md_path = config.output_path("reports_dir", "environment_versions.md")
    json_path.write_text(json.dumps(info, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    md_path.write_text(_to_markdown(info), encoding="utf-8")
    return json_path, md_path


def _version(package_name: str) -> str | None:
    try:
        return importlib.metadata.version(package_name)
    except importlib.metadata.PackageNotFoundError:
        return None


def _to_markdown(info: dict[str, Any]) -> str:
    deps = info["dependencies"]
    lines = [
        "# Environment Versions",
        "",
        f"Generated UTC: `{info['generated_at_utc']}`",
        "",
        "## Python",
        "",
        f"- Executable: `{info['python']['executable']}`",
        f"- Version: `{info['python']['version']}`",
        f"- Platform: `{info['python']['platform']}`",
        "",
        "## CUDA / PyTorch",
        "",
        f"- PyTorch: `{info.get('pytorch', {}).get('version')}`",
        f"- CUDA available: `{info['cuda']['available']}`",
        f"- Torch CUDA version: `{info['cuda']['torch_cuda_version']}`",
        f"- CUDA device count: `{info['cuda']['device_count']}`",
        "",
        "## Key Dependencies",
        "",
        "| Package | Version |",
        "|---|---:|",
    ]
    for name in KEY_DEPENDENCIES:
        lines.append(f"| `{name}` | `{deps.get(name)}` |")
    lines.append("")
    return "\n".join(lines)

