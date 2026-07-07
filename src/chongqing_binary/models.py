"""Model interface and smoke-only baseline models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence


class BinaryClassifierProtocol(Protocol):
    """Minimal binary classifier interface used by project scripts."""

    def fit(self, x: Sequence[Sequence[float]], y: Sequence[int]) -> "BinaryClassifierProtocol":
        ...

    def predict_proba(self, x: Sequence[Sequence[float]]) -> list[float]:
        ...


@dataclass
class MajorityClassModel:
    """Tiny smoke-test baseline that predicts the positive prior."""

    positive_prior: float = 0.5

    def fit(self, x: Sequence[Sequence[float]], y: Sequence[int]) -> "MajorityClassModel":
        if not y:
            raise ValueError("Cannot fit on empty labels.")
        self.positive_prior = sum(int(value) for value in y) / len(y)
        return self

    def predict_proba(self, x: Sequence[Sequence[float]]) -> list[float]:
        return [self.positive_prior for _ in x]

