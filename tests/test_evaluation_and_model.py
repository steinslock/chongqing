from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from chongqing_binary.evaluation import evaluate_binary_predictions
from chongqing_binary.models import MajorityClassModel


class EvaluationAndModelTests(unittest.TestCase):
    def test_majority_model_predicts_training_prior(self) -> None:
        model = MajorityClassModel().fit([[0.0], [1.0], [1.0], [0.0]], [0, 1, 1, 1])
        self.assertAlmostEqual(model.positive_prior, 0.75)
        self.assertEqual(model.predict_proba([[0.0], [1.0]]), [0.75, 0.75])

    def test_binary_metrics(self) -> None:
        metrics = evaluate_binary_predictions([0, 0, 1, 1], [0.1, 0.6, 0.8, 0.4], threshold=0.5)
        self.assertEqual(metrics.n, 4)
        self.assertEqual(metrics.tn, 1)
        self.assertEqual(metrics.fp, 1)
        self.assertEqual(metrics.fn, 1)
        self.assertEqual(metrics.tp, 1)
        self.assertAlmostEqual(metrics.balanced_accuracy, 0.5)
        self.assertIsNotNone(metrics.auroc)


if __name__ == "__main__":
    unittest.main()

