"""Loader for the Goal 2.10 eye-tracking paradigm specification.

Recovered before any paradigm document existed, from the stimulus media and the
recorded timelines; `附件/重医眼动范式及参数.docx` arrived 2026-09-09 and confirms
it. Its second table belongs to a device with no data here — see `document_scope`.
Historical note, kept because it explains the structure below: `附件/`
holds no eye-tracking paradigm script. Every value is recovered from the
archived stimulus media or from the recorded presentation timeline, and each
carries a `source` naming which. The readiness audit validates the
specification against the recorded data rather than the other way round.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SPEC_PATH = "configs/goal2_10/eye_paradigm_spec.yaml"

VALENCES = ("happy", "neutral", "sad")


def project_path(path: str | Path) -> Path:
    value = Path(path).expanduser()
    if not value.is_absolute():
        value = PROJECT_ROOT / value
    return value


@dataclass(frozen=True)
class EyeDeviceSpec:
    """One eye-tracking device and what its sampling rate permits."""

    name: str
    label: str
    root: str
    sampling_rate_hz: int
    raw: dict[str, Any] = field(repr=False, default_factory=dict)

    @property
    def kind(self) -> str:
        return "tobii" if self.name == "tobii" else "qixin"

    @property
    def asdata(self) -> str | None:
        value = self.raw.get("asdata")
        return None if value is None else str(value)

    @property
    def velocity_features_permitted(self) -> bool:
        return bool(self.raw.get("velocity_features_permitted", False))

    @property
    def provides_per_sample_event_type(self) -> bool:
        return bool(self.raw.get("provides_per_sample_event_type", False))


@dataclass(frozen=True)
class EyeTaskSpec:
    """Structure of one eye-tracking task."""

    name: str
    label: str
    qixin_dir: str
    raw: dict[str, Any] = field(repr=False, default_factory=dict)

    @property
    def primary(self) -> bool:
        return bool(self.raw.get("primary", False))

    @property
    def tobii_suffixes(self) -> tuple[str, ...]:
        value = self.raw.get("tobii_filename_suffix")
        if isinstance(value, list):
            return tuple(str(item) for item in value)
        return (str(value),)

    @property
    def tobii_timeline_name(self) -> str:
        return str(self.raw.get("tobii_timeline_name", self.label))

    def expected_media_segments(self, device: str) -> int | None:
        """Media segments the recorded timeline should hold on this device."""
        specific = {
            "qixin_500": "media_segments_expected_qixin_f500",
            "tobii": "media_segments_expected_tobii",
        }.get(device)
        if specific and specific in self.raw:
            return int(self.raw[specific])
        for key in ("media_segments_expected_qixin", "media_segments_expected"):
            if key in self.raw:
                return int(self.raw[key])
        return None

    @property
    def analysed_blocks(self) -> list[dict[str, Any]]:
        return [block for block in self.raw.get("blocks", []) if block.get("analysed")]

    @property
    def device_restriction(self) -> dict[str, Any]:
        return dict(self.raw.get("device_restriction", {}))


@dataclass(frozen=True)
class FreeViewingStimulus:
    """One face stimulus in the free-viewing sequence."""

    media: str
    order: int
    code: str
    valence: str
    sex: str


@dataclass(frozen=True)
class EyeParadigmSpec:
    """The whole eye-tracking specification."""

    path: Path
    devices: dict[str, EyeDeviceSpec]
    tasks: dict[str, EyeTaskSpec]
    raw: dict[str, Any] = field(repr=False, default_factory=dict)

    @property
    def attachment_available(self) -> bool:
        return bool(self.raw.get("attachment_available", False))

    @property
    def screen(self) -> tuple[int, int]:
        screen = self.raw.get("screen", {})
        return int(screen.get("width_px", 1920)), int(screen.get("height_px", 1080))

    def device(self, name: str) -> EyeDeviceSpec:
        return self.devices[name]

    def task(self, name: str) -> EyeTaskSpec:
        return self.tasks[name]

    def task_for_qixin_dir(self, directory: str) -> str | None:
        for name, task in self.tasks.items():
            if task.qixin_dir == directory:
                return name
        return None

    def task_for_tobii_suffix(self, suffix: str) -> str | None:
        for name, task in self.tasks.items():
            if suffix in task.tobii_suffixes:
                return name
        return None

    @property
    def free_viewing_sequence(self) -> list[FreeViewingStimulus]:
        """The fixed 36-face presentation sequence, decoded from filenames."""
        stimulus_set = self.tasks["free_viewing"].raw["stimulus_set"]
        codes = stimulus_set["valence_codes"]
        out: list[FreeViewingStimulus] = []
        for media in stimulus_set["order"]:
            order_text, _, remainder = str(media).partition("-")
            code = "".join(ch for ch in remainder if ch.isalpha())
            meta = codes[code]
            out.append(
                FreeViewingStimulus(
                    media=str(media),
                    order=int(order_text),
                    code=code,
                    valence=str(meta["valence"]),
                    sex=str(meta["sex"]),
                )
            )
        return out

    @property
    def known_defects(self) -> dict[str, str]:
        return {str(item["id"]): str(item.get("description", "")) for item in self.raw.get("known_defects", [])}

    @property
    def validity_checks(self) -> list[dict[str, Any]]:
        return list(self.raw.get("label_free_validity_checks", []))


def load_eye_spec(path: str | Path = DEFAULT_SPEC_PATH) -> EyeParadigmSpec:
    spec_path = project_path(path)
    data = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Eye paradigm specification must be a mapping: {spec_path}")

    devices = {
        name: EyeDeviceSpec(
            name=name,
            label=str(block.get("label", name)),
            root=str(block["root"]),
            sampling_rate_hz=int(block["sampling_rate_hz"]),
            raw=block,
        )
        for name, block in data["devices"].items()
    }
    tasks = {
        name: EyeTaskSpec(
            name=name,
            label=str(block.get("label", name)),
            qixin_dir=str(block["qixin_dir"]),
            raw=block,
        )
        for name, block in data["tasks"].items()
    }
    return EyeParadigmSpec(path=spec_path, devices=devices, tasks=tasks, raw=data)
