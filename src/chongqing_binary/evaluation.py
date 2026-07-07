"""Subject-level binary evaluation utilities."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Sequence


@dataclass(frozen=True)
class BinaryMetrics:
    n: int
    threshold: float
    positive_rate: float
    predicted_positive_rate: float
    accuracy: float
    balanced_accuracy: float
    sensitivity: float
    specificity: float
    f1: float
    brier: float
    auroc: float | None
    tn: int
    fp: int
    fn: int
    tp: int

    def to_dict(self) -> dict[str, float | int | None]:
        return asdict(self)


def evaluate_binary_predictions(
    y_true: Sequence[int],
    y_score: Sequence[float],
    threshold: float = 0.5,
) -> BinaryMetrics:
    if len(y_true) != len(y_score):
        raise ValueError("y_true and y_score must have the same length.")
    if not y_true:
        raise ValueError("Cannot evaluate empty predictions.")

    y_pred = [1 if score >= threshold else 0 for score in y_score]
    tp = sum(1 for truth, pred in zip(y_true, y_pred) if truth == 1 and pred == 1)
    tn = sum(1 for truth, pred in zip(y_true, y_pred) if truth == 0 and pred == 0)
    fp = sum(1 for truth, pred in zip(y_true, y_pred) if truth == 0 and pred == 1)
    fn = sum(1 for truth, pred in zip(y_true, y_pred) if truth == 1 and pred == 0)

    sensitivity = _safe_div(tp, tp + fn)
    specificity = _safe_div(tn, tn + fp)
    precision = _safe_div(tp, tp + fp)
    f1 = _safe_div(2 * precision * sensitivity, precision + sensitivity)
    brier = sum((float(score) - int(truth)) ** 2 for truth, score in zip(y_true, y_score)) / len(y_true)

    return BinaryMetrics(
        n=len(y_true),
        threshold=threshold,
        positive_rate=sum(y_true) / len(y_true),
        predicted_positive_rate=sum(y_pred) / len(y_pred),
        accuracy=(tp + tn) / len(y_true),
        balanced_accuracy=(sensitivity + specificity) / 2,
        sensitivity=sensitivity,
        specificity=specificity,
        f1=f1,
        brier=brier,
        auroc=_auroc(y_true, y_score),
        tn=tn,
        fp=fp,
        fn=fn,
        tp=tp,
    )


def _safe_div(num: float, den: float) -> float:
    return num / den if den else 0.0


def _auroc(y_true: Sequence[int], y_score: Sequence[float]) -> float | None:
    positives = [(score, truth) for truth, score in zip(y_true, y_score) if truth == 1]
    negatives = [(score, truth) for truth, score in zip(y_true, y_score) if truth == 0]
    if not positives or not negatives:
        return None

    wins = 0.0
    total = len(positives) * len(negatives)
    for positive_score, _ in positives:
        for negative_score, _ in negatives:
            if positive_score > negative_score:
                wins += 1.0
            elif positive_score == negative_score:
                wins += 0.5
    return wins / total

