"""Small manifest-only smoke test pipeline."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from .config import ProjectConfig
from .data import (
    balanced_smoke_sample,
    deterministic_stratified_split,
    feature_matrix,
    label_vector,
    load_subject_manifest,
)
from .evaluation import evaluate_binary_predictions
from .leakage import validate_feature_columns
from .models import MajorityClassModel


def run_smoke_test(config: ProjectConfig) -> dict[str, Any]:
    """Run a tiny non-clinical, subject-level wiring check."""

    feature_columns = config.smoke_feature_columns
    validate_feature_columns(
        feature_columns,
        exact=config.forbidden_feature_exact,
        patterns=config.forbidden_feature_patterns,
    )

    records = load_subject_manifest(config=config)
    sample = balanced_smoke_sample(records, config.label_column, config.smoke_limit)
    train, test = deterministic_stratified_split(sample, config.label_column, config.smoke_test_fraction)

    x_train = feature_matrix(train, feature_columns)
    y_train = label_vector(train, config.label_column)
    x_test = feature_matrix(test, feature_columns)
    y_test = label_vector(test, config.label_column)

    model = MajorityClassModel().fit(x_train, y_train)
    scores = model.predict_proba(x_test)
    metrics = evaluate_binary_predictions(y_test, scores).to_dict()

    payload = {
        "purpose": "Goal0 manifest-only smoke test; not a full model training run.",
        "label_column": config.label_column,
        "feature_columns": feature_columns,
        "n_sample": len(sample),
        "n_train": len(train),
        "n_test": len(test),
        "model": "MajorityClassModel",
        "metrics": metrics,
    }

    metrics_path = config.output_path("artifacts_dir", "smoke", "smoke_metrics.json")
    predictions_path = config.output_path("results_dir", "smoke", "smoke_predictions.csv")
    metrics_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    _write_predictions(predictions_path, test, y_test, scores)
    payload["metrics_path"] = str(metrics_path)
    payload["predictions_path"] = str(predictions_path)
    return payload


def _write_predictions(path: Path, records: list[Any], y_true: list[int], scores: list[float]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["L_id", "y_true", "y_score"])
        writer.writeheader()
        for record, truth, score in zip(records, y_true, scores):
            writer.writerow({"L_id": record.l_id, "y_true": truth, "y_score": f"{score:.8f}"})

