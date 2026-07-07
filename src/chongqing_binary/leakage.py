"""Feature leakage guards for clinical scale and diagnosis fields."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Sequence


class LeakageError(ValueError):
    """Raised when a forbidden feature column is requested."""


@dataclass(frozen=True)
class LeakageFinding:
    column: str
    reason: str


def find_forbidden_feature_columns(
    columns: Iterable[str],
    exact: Sequence[str] | None = None,
    patterns: Sequence[str] | None = None,
) -> list[LeakageFinding]:
    exact_set = {value.strip().lower() for value in (exact or [])}
    compiled = [re.compile(pattern) for pattern in (patterns or [])]
    findings: list[LeakageFinding] = []
    for column in columns:
        normalized = column.strip().lower()
        if normalized in exact_set:
            findings.append(LeakageFinding(column=column, reason="exact forbidden field"))
            continue
        for pattern in compiled:
            if pattern.search(column):
                findings.append(LeakageFinding(column=column, reason=f"pattern: {pattern.pattern}"))
                break
    return findings


def validate_feature_columns(
    columns: Iterable[str],
    exact: Sequence[str] | None = None,
    patterns: Sequence[str] | None = None,
) -> None:
    findings = find_forbidden_feature_columns(columns, exact=exact, patterns=patterns)
    if findings:
        detail = "; ".join(f"{finding.column} ({finding.reason})" for finding in findings)
        raise LeakageError(f"Forbidden feature columns detected: {detail}")

