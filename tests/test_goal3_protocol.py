"""Goal 3 protocol, data and model tests.

The split tests are the important ones. Goal 3's whole design rests on the
stopping subset making every training decision while inner-val makes none, and a
regression there would reintroduce the optimistic bias in the cross-fitted
scores that the third split level exists to prevent.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import torch

from chongqing_binary.goal3.config import load_goal_config
from chongqing_binary.goal3.data import (
    CONDITIONS,
    STANDARD,
    TARGET,
    SubjectSampler,
    TrialStore,
    normalise_batch,
    subject_batches,
)
from chongqing_binary.goal3.models import ModelSpec, SubjectModel
from chongqing_binary.goal3.protocol import build_inner_splits, stack
from chongqing_binary.goal3.report import benjamini_hochberg
from chongqing_binary.goal3.runner import declared_configurations

CONFIG = "configs/goal3/common.yaml"


def _toy_store(n_subjects: int = 12, n_channels: int = 4, n_times: int = 16) -> TrialStore:
    rng = np.random.default_rng(0)
    rows: dict[str, dict[str, np.ndarray]] = {}
    blocks = []
    cursor = 0
    for i in range(n_subjects):
        l_id = f"L{i:03d}"
        rows[l_id] = {}
        # Deliberately uneven: subject 0 has fewer targets than any sane quota.
        counts = {TARGET: 2 if i == 0 else 6, STANDARD: 10 + i}
        for condition in CONDITIONS:
            n = counts[condition]
            rows[l_id][condition] = np.arange(cursor, cursor + n)
            blocks.append(rng.normal(size=(n, n_channels, n_times)).astype(np.float32))
            cursor += n
    return TrialStore(trials=np.concatenate(blocks), channels=[f"c{i}" for i in range(n_channels)],
                      times=np.linspace(-0.2, 0.8, n_times, dtype=np.float32), rows=rows)


class InnerSplitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ids = [f"L{i:03d}" for i in range(300)]
        rng = np.random.default_rng(7)
        self.labels = {l: int(v) for l, v in zip(self.ids, rng.integers(0, 2, len(self.ids)))}

    def test_three_way_disjoint_and_covering(self) -> None:
        splits = build_inner_splits(self.ids, self.labels, 3, 0.2, seed=11)
        self.assertEqual(len(splits), 3)
        covered: set[str] = set()
        for split in splits:
            fit, stop, val = set(split.fit_ids), set(split.stopping_ids), set(split.val_ids)
            self.assertFalse(fit & stop)
            self.assertFalse(fit & val)
            self.assertFalse(stop & val)
            self.assertEqual(fit | stop | val, set(self.ids))
            covered |= val
        self.assertEqual(covered, set(self.ids), "every subject needs exactly one inner-OOF score")

    def test_stopping_subset_is_carved_from_fit_pool_not_from_inner_val(self) -> None:
        """The leak guard: stopping subjects must never be inner-val subjects.

        If they were, the epoch would be chosen to be good on exactly the
        subjects whose predictions train the meta model.
        """
        for split in build_inner_splits(self.ids, self.labels, 3, 0.2, seed=3):
            self.assertFalse(set(split.stopping_ids) & set(split.val_ids))
            expected = round(0.2 * (len(split.fit_ids) + len(split.stopping_ids)))
            self.assertLessEqual(abs(len(split.stopping_ids) - expected), 1)

    def test_deterministic_for_a_seed(self) -> None:
        a = build_inner_splits(self.ids, self.labels, 3, 0.2, seed=5)
        b = build_inner_splits(self.ids, self.labels, 3, 0.2, seed=5)
        self.assertEqual([s.fit_ids for s in a], [s.fit_ids for s in b])
        self.assertEqual([s.stopping_ids for s in a], [s.stopping_ids for s in b])


class SamplerTests(unittest.TestCase):
    def test_quota_is_met_even_when_a_subject_has_too_few_trials(self) -> None:
        store = _toy_store()
        sampler = SubjectSampler(store, (TARGET, STANDARD), quota=8)
        picks = sampler.draw(store.subjects, np.random.default_rng(0))
        for condition in (TARGET, STANDARD):
            self.assertEqual(picks[condition].shape, (len(store.subjects), 8))
        # L000 has 2 target trials and still contributes exactly 8 rows, so trial
        # count cannot weight a subject.
        drawn = set(picks[TARGET][0].tolist())
        self.assertTrue(drawn.issubset(set(store.rows["L000"][TARGET].tolist())))

    def test_gather_returns_the_rows_that_were_drawn(self) -> None:
        store = _toy_store()
        sampler = SubjectSampler(store, (TARGET,), quota=4)
        rng = np.random.default_rng(1)
        picks = sampler.draw(store.subjects, rng)
        data = sampler.gather(picks)[TARGET]
        for i in range(len(store.subjects)):
            for j in range(4):
                np.testing.assert_array_equal(data[i, j], store.trials[picks[TARGET][i, j]])

    def test_batches_never_have_a_single_subject(self) -> None:
        rng = np.random.default_rng(0)
        sizes = [len(b) for b in subject_batches([f"L{i}" for i in range(17)], 8, rng)]
        self.assertNotIn(1, sizes)


class NormalisationTests(unittest.TestCase):
    def test_none_only_changes_units(self) -> None:
        batch = {TARGET: np.full((2, 3, 4, 5), 1e-5, dtype=np.float32)}
        out = normalise_batch(batch, "none")[TARGET]
        np.testing.assert_allclose(out, 10.0, rtol=1e-5)

    def test_robust_z_uses_one_scale_for_both_conditions(self) -> None:
        """Scaling conditions separately would destroy the target-minus-standard relation."""
        rng = np.random.default_rng(0)
        target = rng.normal(loc=5.0, scale=1.0, size=(1, 4, 2, 40)).astype(np.float32)
        standard = rng.normal(loc=0.0, scale=1.0, size=(1, 9, 2, 40)).astype(np.float32)
        out = normalise_batch({TARGET: target, STANDARD: standard}, "robust_z")
        # The condition means must stay apart after normalisation.
        self.assertGreater(out[TARGET].mean() - out[STANDARD].mean(), 1.0)


class ModelTests(unittest.TestCase):
    def test_every_declared_configuration_builds_and_runs(self) -> None:
        for configuration in declared_configurations():
            model = SubjectModel(configuration.spec, 32, 250)
            if configuration.representation == "condition_aware":
                batch = {TARGET: torch.randn(3, 4, 32, 250), STANDARD: torch.randn(3, 4, 32, 250)}
            elif configuration.representation == "difference_wave":
                batch = {TARGET: torch.randn(3, 1, 32, 250)}
            else:
                batch = {TARGET: torch.randn(3, 4, 32, 250)}
            self.assertEqual(model(batch).shape, (3,))

    def test_condition_aware_representation_carries_the_difference(self) -> None:
        model = SubjectModel(ModelSpec("eegnet", "condition_aware"), 8, 32).eval()
        target, standard = torch.randn(2, 4, 8, 32), torch.randn(2, 4, 8, 32)
        with torch.no_grad():
            vector = model.embed({TARGET: target, STANDARD: standard})
        third = vector.shape[1] // 3
        np.testing.assert_allclose(
            vector[:, 2 * third:].numpy(),
            (vector[:, :third] - vector[:, third:2 * third]).numpy(), rtol=1e-5, atol=1e-6)

    def test_declared_family_matches_the_preregistration(self) -> None:
        configurations = declared_configurations()
        arms = pd.Series([c.arm for c in configurations]).value_counts().to_dict()
        self.assertEqual(arms.get("confirmatory"), 1)
        self.assertEqual(arms.get("exploratory"), 12)
        self.assertEqual(arms.get("ablation"), 1)
        self.assertEqual(len({c.config_id for c in configurations}), len(configurations))


class StackingTests(unittest.TestCase):
    def test_a_noise_component_does_not_drag_the_informative_one_down(self) -> None:
        """The reason the increment test stacks probabilities instead of concatenating.

        Appending uninformative columns to demographics costs this project 0.008
        to 0.055 AUROC; a second-stage model on one scalar per component gives
        noise a near-zero weight instead.
        """
        from sklearn.metrics import roc_auc_score

        rng = np.random.default_rng(0)
        n = 600
        y = pd.Series(rng.integers(0, 2, n), index=[f"L{i}" for i in range(n)])
        informative = pd.Series(np.clip(0.5 + 0.25 * (y.to_numpy() - 0.5) * 2
                                        + rng.normal(0, 0.12, n), 0.01, 0.99), index=y.index)
        noise = pd.Series(rng.uniform(0.01, 0.99, n), index=y.index)
        result = stack({"demo": informative, "other": noise},
                       {"demo": informative, "other": noise}, y, seed=0)
        alone = roc_auc_score(y, informative)
        combined = roc_auc_score(y, result.outer_scores)
        self.assertGreater(combined, alone - 0.02)
        self.assertLess(abs(result.coefficients["other"]), abs(result.coefficients["demo"]))


class DeviceFailureTests(unittest.TestCase):
    """A GPU that refuses a model does not always say "out of memory".

    Six jobs died on `CUBLAS_STATUS_ALLOC_FAILED when calling cublasCreate`,
    which is an allocation failure whose message never contains that phrase, so
    the fallback declined to handle it and the exception propagated.
    """

    def test_allocation_failures_are_recognised(self) -> None:
        from chongqing_binary.goal3.train import _is_device_failure

        for message in [
            "CUDA error: CUBLAS_STATUS_ALLOC_FAILED when calling `cublasCreate(handle)`",
            "CUDA error: CUBLAS_STATUS_EXECUTION_FAILED when calling `cublasSgemm(...)`",
            "CUDA out of memory. Tried to allocate 2.00 GiB",
            "cuDNN error: CUDNN_STATUS_ALLOC_FAILED",
            "cuDNN error: CUDNN_STATUS_INTERNAL_ERROR_HOST_ALLOCATION_FAILED",
        ]:
            self.assertTrue(_is_device_failure(RuntimeError(message)), message)

    def test_real_errors_still_propagate(self) -> None:
        from chongqing_binary.goal3.train import _is_device_failure

        for message in [
            "mat1 and mat2 shapes cannot be multiplied (4x224 and 112x64)",
            "Expected all tensors to be on the same device",
            "index 5 is out of bounds for dimension 0 with size 3",
        ]:
            self.assertFalse(_is_device_failure(RuntimeError(message)), message)


class ComparatorRuleTests(unittest.TestCase):
    """A win over a below-chance comparator is a statement about the comparator.

    Goal 2.9 established this for demographics and Goal 2.10 withdrew eighteen
    rows under it. Goal 3 applies it to every comparison, including deep versus
    traditional.
    """

    def test_comparator_auroc_is_attached_to_every_comparison(self) -> None:
        from chongqing_binary.goal3.report import attach_comparators

        paired = pd.DataFrame([
            {"cv_protocol": "group_cv", "model": "m", "seed": "mean",
             "feature_set_a": "eeg_deep", "feature_set_b": "eeg_traditional",
             "comparison": "eeg_deep_vs_eeg_traditional", "auroc_diff": 0.06},
            {"cv_protocol": "group_cv", "model": "m", "seed": "mean",
             "feature_set_a": "demographics_eeg_deep", "feature_set_b": "demographics",
             "comparison": "demographics_eeg_deep_vs_demographics", "auroc_diff": 0.01},
        ])
        pooled = pd.DataFrame([
            {"cv_protocol": "group_cv", "model": "m", "seed": "mean",
             "feature_set": "eeg_traditional", "threshold_type": "inner_cv", "auroc": 0.4906},
            {"cv_protocol": "group_cv", "model": "m", "seed": "mean",
             "feature_set": "demographics", "threshold_type": "inner_cv", "auroc": 0.5909},
        ])
        out = attach_comparators(paired, pooled).set_index("comparison")
        self.assertAlmostEqual(out.loc["eeg_deep_vs_eeg_traditional", "comparator_auroc"], 0.4906)
        self.assertEqual(out.loc["eeg_deep_vs_eeg_traditional", "comparator_above_chance"], 0)
        self.assertEqual(out.loc["demographics_eeg_deep_vs_demographics", "comparator_above_chance"], 1)


class FdrTests(unittest.TestCase):
    def test_benjamini_hochberg_rejects_below_the_ranked_threshold(self) -> None:
        # thresholds i/n * alpha are 0.01, 0.02, 0.03, 0.04, 0.05
        p = np.array([0.001, 0.008, 0.039, 0.041, 0.9])
        np.testing.assert_array_equal(benjamini_hochberg(p, 0.05),
                                      np.array([True, True, False, False, False]))

    def test_step_up_pulls_in_smaller_p_values(self) -> None:
        """The largest passing rank rejects everything below it, not only the passers."""
        # thresholds are 0.0125, 0.025, 0.0375, 0.05; only ranks 1 and 4 pass alone
        p = np.array([0.001, 0.03, 0.04, 0.05])
        np.testing.assert_array_equal(benjamini_hochberg(p, 0.05), np.array([True, True, True, True]))

    def test_all_null_rejects_nothing(self) -> None:
        self.assertFalse(benjamini_hochberg(np.array([0.4, 0.6, 0.8]), 0.05).any())


class CrossFitConsistencyTests(unittest.TestCase):
    """The tabular comparators and the deep model must see the same inner splits.

    They are cross-fitted in separate processes and joined by `L_id`, so a drift
    in the split seeding would silently give `p_Demo` and `p_EEG` different
    training sets and make the stacking compare two different experiments.
    """

    def test_inner_splits_are_reproduced_from_the_same_seed_recipe(self) -> None:
        from chongqing_binary.goal3.protocol import stable_seed

        ids = [f"L{i:03d}" for i in range(400)]
        rng = np.random.default_rng(2)
        labels = {l: int(v) for l, v in zip(ids, rng.integers(0, 2, len(ids)))}
        recipe = stable_seed(0, "standard_cv", "3")
        a = build_inner_splits(ids, labels, 3, 0.2, recipe)
        b = build_inner_splits(ids, labels, 3, 0.2, recipe)
        self.assertEqual([s.val_ids for s in a], [s.val_ids for s in b])
        self.assertEqual([s.stopping_ids for s in a], [s.stopping_ids for s in b])

    def test_different_folds_get_different_inner_splits(self) -> None:
        from chongqing_binary.goal3.protocol import stable_seed

        ids = [f"L{i:03d}" for i in range(400)]
        labels = {l: i % 2 for i, l in enumerate(ids)}
        a = build_inner_splits(ids, labels, 3, 0.2, stable_seed(0, "standard_cv", "0"))
        b = build_inner_splits(ids, labels, 3, 0.2, stable_seed(0, "standard_cv", "1"))
        self.assertNotEqual([s.val_ids for s in a], [s.val_ids for s in b])


class ChannelSelectionTests(unittest.TestCase):
    def test_excluded_channels_are_dropped_from_the_model_input_only(self) -> None:
        store = _toy_store(n_channels=4)
        store.all_channels = ["Fp1", "Fp2", "Pz", "Cz"]
        store.channels = ["Pz", "Cz"]
        store.keep_channels = np.array([2, 3])
        rows = store.rows["L000"][STANDARD][:3]
        taken = store.take(rows)
        self.assertEqual(taken.shape[1], 2)
        np.testing.assert_array_equal(taken, np.asarray(store.trials[rows])[:, [2, 3]])
        self.assertEqual(store.n_channels, 2)
        # The stored array is untouched, because it must remain the Goal 2.8 data.
        self.assertEqual(store.trials.shape[1], 4)


class ConfigTests(unittest.TestCase):
    def test_preprocessing_is_not_redefined_by_goal3(self) -> None:
        """Goal 3 is a representation experiment; it must not re-open the measurement."""
        config = load_goal_config(CONFIG)
        self.assertNotIn("eeg", config, "Goal 3 must read EEG preprocessing from Goal 2.8")
        self.assertEqual(config["paths"]["eeg_preprocessing_config"], "configs/goal2_8/eeg.yaml")

    def test_protocol_matches_the_other_goals(self) -> None:
        config = load_goal_config(CONFIG)
        self.assertEqual(config["protocol"]["inner_cv_folds"], 3)
        self.assertEqual(config["bootstrap"]["n_resamples"], 1000)
        self.assertEqual(config["protocol"]["cv_protocols"]["standard_cv"]["fold_column"], "cv_fold")
        self.assertEqual(config["protocol"]["cv_protocols"]["group_cv"]["fold_column"], "robustness_fold")


if __name__ == "__main__":
    unittest.main()
