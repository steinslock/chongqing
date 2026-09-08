"""Readers for the trial-level behavioural logs the paradigms wrote.

Every task that takes a keypress left a per-subject trial log next to the fNIRS
recording, and Goal 2.8 used none of it. Two formats exist: PsychoPy trial CSVs
on the Yiruid side and E-Prime `Block_Trial` text logs on the Bikom side. Both
are reduced here to one tidy table so the feature code sees a single shape.

Column names, block structure and the known defects come from
`configs/goal2_8/paradigm_spec.yaml` through `paradigm.spec.BehaviourTaskSpec`.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

import pandas as pd

from ..paradigm.spec import BehaviourTaskSpec

TRIAL_COLUMNS = [
    "block", "trial", "onset_sec", "stimulus", "condition",
    "response", "rt_sec", "logged_correct", "feedback",
]

# PsychoPy writes several sibling CSVs per subject; only the wide one carries
# trial rows with timestamps. Two file-naming conventions coexist, so the rule
# is negative: anything that is not one of these siblings.
PSYCHOPY_SIBLING_SUFFIXES = (
    "_task_loop.csv", "_all_loop.csv", "_stim_loop.csv", "_rep.csv",
)


def _empty_trials() -> pd.DataFrame:
    return pd.DataFrame(columns=TRIAL_COLUMNS)


def _to_float(value: Any) -> float:
    text = str(value or "").strip()
    if not text:
        return float("nan")
    try:
        return float(text)
    except ValueError:
        return float("nan")


# -- file discovery --------------------------------------------------------

def psychopy_trial_files(subject_dir: Path) -> list[Path]:
    """Wide PsychoPy trial CSVs in one subject directory, oldest name first."""
    return sorted(
        path for path in subject_dir.glob("*.csv")
        if not path.name.endswith(PSYCHOPY_SIBLING_SUFFIXES)
    )


def eprime_trial_files(subject_dir: Path, glob: str) -> list[Path]:
    return sorted(subject_dir.glob(glob))


def collect_subject_dirs(root: Path, glob: str = "*") -> dict[str, Path]:
    """Map `L_id` to its behavioural directory under `root`."""
    from ..goal2_8.fnirs import _extract_l_id

    out: dict[str, Path] = {}
    if not root.exists():
        return out
    for path in sorted(root.glob(glob)):
        if not path.is_dir():
            continue
        l_id = _extract_l_id(path.name)
        if l_id and l_id not in out:
            out[l_id] = path
    return out


# -- PsychoPy --------------------------------------------------------------

def read_psychopy_csv(path: Path) -> list[dict[str, str]]:
    """Read one PsychoPy CSV, tolerating the encodings seen in this dataset."""
    last: Exception | None = None
    for encoding in ("utf-8-sig", "gbk", "utf-8"):
        try:
            with path.open("r", encoding=encoding, newline="") as handle:
                return list(csv.DictReader(handle))
        except UnicodeDecodeError as exc:  # noqa: PERF203
            last = exc
    raise ValueError(f"unreadable PsychoPy CSV: {path}") from last


def read_psychopy_trials(path: Path, bspec: BehaviourTaskSpec) -> pd.DataFrame:
    """Tidy trial table from a PsychoPy wide CSV."""
    rows = read_psychopy_csv(path)
    if not rows:
        return _empty_trials()

    trial_marker = bspec.column("trial_row_column")
    block_col = bspec.column("block_column")
    index_col = bspec.column("trial_index_column")
    onset_col = bspec.column("onset_column")
    stim_col = bspec.column("stimulus_column") or trial_marker
    cond_col = bspec.column("condition_column")
    resp_col = bspec.column("response_column")
    rt_col = bspec.column("rt_column")
    acc_col = bspec.column("accuracy_column")
    fb_col = bspec.column("feedback_column")
    cond_map = bspec.mapping("condition_map")
    stim_map = bspec.mapping("stimulus_map")
    fb_map = bspec.mapping("feedback_map")

    out: list[dict[str, Any]] = []
    for row in rows:
        if not str(row.get(trial_marker) or "").strip():
            continue
        raw_cond = str(row.get(cond_col) or "").strip() if cond_col else ""
        raw_fb = str(row.get(fb_col) or "").strip() if fb_col else ""
        stimulus = str(row.get(stim_col) or "").strip()
        out.append({
            "block": _to_float(row.get(block_col)),
            "trial": _to_float(row.get(index_col)),
            "onset_sec": _to_float(row.get(onset_col)),
            "stimulus": stim_map.get(stimulus, stimulus),
            "condition": cond_map.get(_normalise_code(raw_cond), ""),
            "response": _normalise_code(str(row.get(resp_col) or "").strip()),
            "rt_sec": _to_float(row.get(rt_col)),
            "logged_correct": _to_float(row.get(acc_col)) if acc_col else float("nan"),
            "feedback": fb_map.get(_normalise_code(raw_fb), ""),
        })
    return pd.DataFrame(out, columns=TRIAL_COLUMNS)


def _normalise_code(value: str) -> str:
    """`1.0` and `1` are the same response code; PsychoPy writes both."""
    text = str(value).strip()
    if not text:
        return ""
    try:
        number = float(text)
    except ValueError:
        return text
    return str(int(number)) if number.is_integer() else text


# -- E-Prime ---------------------------------------------------------------

def read_eprime_text(path: Path) -> str:
    raw = path.read_bytes()
    last: Exception | None = None
    for encoding in ("utf-16", "utf-16-le", "utf-8-sig", "gbk"):
        try:
            text = raw.decode(encoding)
        except UnicodeDecodeError as exc:  # noqa: PERF203
            last = exc
            continue
        if "LogFrame" in text:
            return text
    raise ValueError(f"unreadable E-Prime log: {path}") from last


def parse_eprime_frames(path: Path) -> tuple[dict[str, str], list[dict[str, str]]]:
    """Split an E-Prime `Block_Trial` log into its header and its LogFrames."""
    header: dict[str, str] = {}
    frames: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    in_header = False
    for line in read_eprime_text(path).splitlines():
        stripped = line.strip()
        if stripped == "*** Header Start ***":
            in_header = True
            continue
        if stripped == "*** Header End ***":
            in_header = False
            continue
        if stripped == "*** LogFrame Start ***":
            current = {}
            continue
        if stripped == "*** LogFrame End ***":
            if current is not None:
                frames.append(current)
            current = None
            continue
        if ":" not in stripped:
            continue
        key, _, value = stripped.partition(":")
        key, value = key.strip(), value.strip()
        if in_header:
            header.setdefault(key, value)
        elif current is not None:
            current[key] = value
    return header, frames


def _response_prefix(frame: dict[str, str], rt_suffix: str) -> str:
    """E-Prime names the response object per subject, so discover the prefix."""
    for key in frame:
        if key.endswith(rt_suffix):
            return key[: -len(rt_suffix)]
    return ""


def read_eprime_trials(path: Path, bspec: BehaviourTaskSpec) -> pd.DataFrame:
    """Tidy trial table from an E-Prime `Block_Trial` log."""
    _, frames = parse_eprime_frames(path)
    rt_suffix = bspec.column("rt_suffix", ".RT")
    resp_suffix = bspec.column("response_suffix", ".RESP")
    acc_suffix = bspec.column("accuracy_suffix", ".ACC")
    procedure = bspec.column("trial_procedure")
    stim_col = bspec.column("stimulus_column")
    cond_col = bspec.column("condition_column")
    fb_col = bspec.column("feedback_column")
    block_col = bspec.column("block_column")
    index_col = bspec.column("trial_index_column")
    onset_col = bspec.column("onset_column")
    cond_map = bspec.mapping("condition_map")
    fb_map = bspec.mapping("feedback_map")
    rt_scale = 1e-3 if bspec.column("rt_units") == "milliseconds" else 1.0
    onset_scale = 1e-3 if bspec.column("onset_units") == "milliseconds" else 1.0
    block_from_prefix = bspec.column("block_from") == "response_object_prefix"

    trials = [f for f in frames if any(k.endswith(rt_suffix) for k in f)]
    if procedure:
        trials = [f for f in trials if f.get("Procedure") == procedure]
    if not trials:
        return _empty_trials()

    prefix_order: list[str] = []
    out: list[dict[str, Any]] = []
    for position, frame in enumerate(trials):
        prefix = _response_prefix(frame, rt_suffix)
        if prefix and prefix not in prefix_order:
            prefix_order.append(prefix)
        if block_from_prefix:
            block = float(prefix_order.index(prefix)) if prefix else float("nan")
        else:
            block = _to_float(frame.get(block_col))
        rt = _to_float(frame.get(f"{prefix}{rt_suffix}")) * rt_scale
        response = str(frame.get(f"{prefix}{resp_suffix}") or "").strip()
        raw_cond = str(frame.get(cond_col) or "").strip() if cond_col else ""
        raw_fb = str(frame.get(fb_col) or "").strip() if fb_col else ""
        stimulus = str(frame.get(stim_col) or "").strip().replace("\\", "/")
        out.append({
            "block": block,
            "trial": _to_float(frame.get(index_col)) if index_col else float(position),
            "onset_sec": _to_float(frame.get(onset_col)) * onset_scale if onset_col else float("nan"),
            "stimulus": stimulus,
            "condition": cond_map.get(_normalise_code(raw_cond), "") if cond_map else raw_cond,
            # E-Prime writes RT 0 for a non-response; keep the empty response as
            # the single source of truth and blank the paired RT.
            "response": _normalise_code(response),
            "rt_sec": rt if response else float("nan"),
            "logged_correct": _to_float(frame.get(f"{prefix}{acc_suffix}")),
            "feedback": fb_map.get(raw_fb, "") if fb_map else raw_fb,
        })
    frame_out = pd.DataFrame(out, columns=TRIAL_COLUMNS)
    if not block_from_prefix and frame_out["block"].isna().all():
        frame_out["block"] = 0.0
    return frame_out


def read_trials(path: Path, bspec: BehaviourTaskSpec) -> pd.DataFrame:
    if bspec.log_format == "eprime_block_trial_txt":
        return read_eprime_trials(path, bspec)
    return read_psychopy_trials(path, bspec)
