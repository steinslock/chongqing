"""Goal 2.9 behavioural feature and matrix tests."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from chongqing_binary.goal2_9.behaviour import (
    derive_nback_conditions,
    doors_features,
    nback_features,
    oddball_features,
)
from chongqing_binary.goal2_9.behaviour_io import (
    TRIAL_COLUMNS,
    _normalise_code,
    parse_eprime_frames,
    psychopy_trial_files,
    read_eprime_trials,
    read_psychopy_trials,
)
from chongqing_binary.goal2_9.config import load_goal_config
from chongqing_binary.goal2_9.report import credit_increments, unit_decision
from chongqing_binary.paradigm import load_paradigm_spec

BEHAVIOUR_DIR = PROJECT_ROOT / "artifacts" / "goal2_9" / "behaviour"


def _trials(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=TRIAL_COLUMNS)


class ParadigmSpecBehaviourTests(unittest.TestCase):
    def setUp(self) -> None:
        self.spec = load_paradigm_spec()

    def test_every_behaviour_unit_names_its_source(self) -> None:
        for device, task in self.spec.behaviour_units():
            bspec = self.spec.behaviour(device, task)
            self.assertTrue(str(bspec.raw.get("source", "")).strip(),
                            f"{device}/{task} behaviour has no source")

    def test_bikom_oddball_is_marked_unusable(self) -> None:
        """That build never collected the keypress, in the vendor's own run too."""
        bspec = self.spec.behaviour("bikom", "oddball")
        self.assertFalse(bspec.usable)
        self.assertEqual(bspec.unusable_reason, "response_never_collected")
        self.assertIn("bikom_oddball_behaviour", self.spec.known_gaps)

    def test_yiruid_doors_is_sensitivity_only(self) -> None:
        """Its response window closes 0.5 s after the doors appear."""
        bspec = self.spec.behaviour("yiruid", "doors")
        self.assertTrue(bspec.sensitivity_only)
        self.assertEqual(bspec.timing_confidence, "low")
        self.assertEqual(bspec.raw["defect"], "response_window_misaligned_with_stimulus")
        self.assertLess(bspec.response_window_sec, float(bspec.raw["door_visible_to_sec"]))

    def test_doors_feedback_code_1_is_loss_on_both_devices(self) -> None:
        """stim/1.png is a red "-1"; an earlier revision had this reversed."""
        for device in ("yiruid", "bikom"):
            mapping = self.spec.behaviour(device, "doors").mapping("feedback_map")
            self.assertEqual(mapping.get("1") or mapping.get("1.jpg"), "loss", device)
            self.assertEqual(mapping.get("2") or mapping.get("2.jpg"), "win", device)
        task = self.spec.fnirs("yiruid", "doors")
        self.assertEqual({str(k): v for k, v in task.raw["feedback_code_map"].items()},
                         {"1": "loss", "2": "win"})

    def test_protocol_pdf_doors_description_is_an_antipattern(self) -> None:
        """The PDF describes 3 x 20 trials with +50/-25; the run was 6 x 10 with +2/-1."""
        self.assertIn("protocol_pdf_doors_description", self.spec.antipatterns)
        self.assertEqual(self.spec.fnirs("yiruid", "doors").raw["task_blocks"], 6)
        self.assertEqual(self.spec.fnirs("yiruid", "doors").raw["trials_per_block"], 10)

    def test_1back_condition_is_recoverable_on_the_fnirs_side(self) -> None:
        """EEG 1BACK match/non-match is unrecoverable; the fNIRS logs have it."""
        self.assertFalse(self.spec.known_gaps["eeg_1back_match_nonmatch"]["recoverable"])
        for device in ("yiruid", "bikom"):
            mapping = self.spec.behaviour(device, "1back").mapping("condition_map")
            self.assertEqual(mapping["1"], "non_match")
            self.assertEqual(mapping["2"], "match")


class NbackConditionTests(unittest.TestCase):
    def test_block_initial_is_labelled_and_repeats_are_matches(self) -> None:
        trials = _trials([
            {"block": 0, "trial": i, "stimulus": s, "response": "", "rt_sec": float("nan"),
             "condition": "", "onset_sec": 0.0, "logged_correct": 1.0, "feedback": ""}
            for i, s in enumerate(["a", "b", "b", "c"])
        ])
        labels = list(derive_nback_conditions(trials)["derived_condition"])
        self.assertEqual(labels, ["block_initial", "non_match", "match", "non_match"])

    def test_each_block_gets_its_own_block_initial(self) -> None:
        """A block boundary breaks the 1-back chain; the last trial of the
        previous block is not the predecessor of the next block's first."""
        rows = []
        for block, stimuli in enumerate((["a", "a"], ["a", "b"])):
            for i, s in enumerate(stimuli):
                rows.append({"block": block, "trial": i, "stimulus": s, "response": "",
                             "rt_sec": float("nan"), "condition": "", "onset_sec": 0.0,
                             "logged_correct": 1.0, "feedback": ""})
        labels = list(derive_nback_conditions(_trials(rows))["derived_condition"])
        self.assertEqual(labels, ["block_initial", "match", "block_initial", "non_match"])


class NbackFeatureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.spec = load_paradigm_spec()
        self.bspec = self.spec.behaviour("yiruid", "1back")

    def _frame(self) -> pd.DataFrame:
        # a b b c c a : block-initial, non-match, match, non-match, match, non-match
        stimuli = ["a", "b", "b", "c", "c", "a"]
        responses = ["", "1", "2", "1", "1", "1"]   # one miss on the second match
        rts = [float("nan"), 0.5, 0.6, 0.5, 0.9, 0.7]
        return _trials([
            {"block": 0, "trial": i, "stimulus": s, "response": r, "rt_sec": t,
             "condition": "", "onset_sec": float(i), "logged_correct": float("nan"), "feedback": ""}
            for i, (s, r, t) in enumerate(zip(stimuli, responses, rts))
        ])

    def test_accuracy_and_signal_detection(self) -> None:
        features, qc = nback_features(self._frame(), self.bspec)
        self.assertEqual(qc["qc_trials_used"], 5)
        self.assertEqual(features["signal_n_match"], 2)
        self.assertEqual(features["signal_n_non_match"], 3)
        self.assertAlmostEqual(features["signal_accuracy"], 4 / 5)
        self.assertAlmostEqual(features["signal_hit_rate"], 0.5)
        self.assertAlmostEqual(features["signal_false_alarm_rate"], 0.0)
        self.assertGreater(features["signal_dprime"], 0.0)

    def test_post_error_slowing_is_positive_when_errors_are_followed_by_slow_trials(self) -> None:
        features, _ = nback_features(self._frame(), self.bspec)
        # The error is trial 4 (0.9 s); the trial after it is 0.7 s, and the
        # trials after correct ones are 0.6 and 0.5 s.
        self.assertGreater(features["signal_post_error_slowing_sec"], 0.0)

    def test_block_slope_is_omitted_for_a_two_block_task(self) -> None:
        """With two blocks the slope is the last-minus-first difference again."""
        rows = []
        for block in (0, 1):
            for i, s in enumerate(["a", "b", "b"]):
                rows.append({"block": block, "trial": i, "stimulus": s,
                             "response": "1" if s == "b" and i == 1 else "2",
                             "rt_sec": 0.5, "condition": "", "onset_sec": 0.0,
                             "logged_correct": float("nan"), "feedback": ""})
        features, _ = nback_features(_trials(rows), self.bspec)
        self.assertIn("signal_accuracy_last_minus_first_block", features)
        self.assertNotIn("signal_accuracy_block_slope", features)

    def test_condition_agreement_is_reported_against_the_logged_column(self) -> None:
        frame = self._frame()
        frame["condition"] = ["", "non_match", "match", "non_match", "match", "non_match"]
        _, qc = nback_features(frame, self.bspec)
        self.assertEqual(qc["qc_condition_agreement"], 1.0)
        self.assertEqual(qc["qc_condition_comparable_trials"], 5)


class OddballFeatureTests(unittest.TestCase):
    def test_hit_and_false_alarm_rates(self) -> None:
        spec = load_paradigm_spec()
        rows = []
        for i in range(10):
            target = i in (2, 7)
            responded = i in (2, 5)   # one hit, one miss, one false alarm
            rows.append({"block": 0, "trial": i, "stimulus": "target" if target else "standard",
                         "response": "1" if responded else "", "rt_sec": 0.3 if responded else float("nan"),
                         "condition": "", "onset_sec": float(i), "logged_correct": float("nan"),
                         "feedback": ""})
        features, qc = oddball_features(_trials(rows), spec.behaviour("yiruid", "oddball"))
        self.assertEqual(qc["qc_n_targets"], 2)
        self.assertEqual(qc["qc_n_standards"], 8)
        self.assertAlmostEqual(features["signal_hit_rate"], 0.5)
        self.assertAlmostEqual(features["signal_false_alarm_rate"], 0.125)
        self.assertAlmostEqual(features["signal_miss_rate"], 0.5)


class DoorsFeatureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.bspec = load_paradigm_spec().behaviour("bikom", "doors")

    def test_win_stay_and_lose_shift(self) -> None:
        # choice/feedback: 1/win 1/loss 2/win 2/loss 1/win
        # lag-1 pairs: after win stay (1->1), after loss shift (1->2),
        #              after win stay (2->2), after loss shift (2->1)
        rows = [
            {"block": 0, "trial": i, "stimulus": "", "response": c, "rt_sec": 1.0,
             "condition": "", "onset_sec": float(i), "logged_correct": float("nan"), "feedback": f}
            for i, (c, f) in enumerate([("1", "win"), ("1", "loss"), ("2", "win"),
                                        ("2", "loss"), ("1", "win")])
        ]
        features, qc = doors_features(_trials(rows), self.bspec)
        self.assertEqual(qc["qc_n_win"], 3)
        self.assertEqual(qc["qc_n_loss"], 2)
        self.assertAlmostEqual(features["signal_win_stay_rate"], 1.0)
        self.assertAlmostEqual(features["signal_lose_shift_rate"], 1.0)
        self.assertAlmostEqual(features["signal_feedback_sensitivity"], 1.0)
        self.assertAlmostEqual(features["signal_switch_rate"], 0.5)

    def test_lag1_pairs_do_not_cross_a_block_boundary(self) -> None:
        rows = []
        for block in (0, 1):
            for i, (choice, fb) in enumerate([("1", "win"), ("1", "win")]):
                rows.append({"block": block, "trial": i, "stimulus": "", "response": choice,
                             "rt_sec": 1.0, "condition": "", "onset_sec": 0.0,
                             "logged_correct": float("nan"), "feedback": fb})
        features, _ = doors_features(_trials(rows), self.bspec)
        # Two blocks of two trials give one within-block pair each, not three.
        self.assertEqual(features["signal_n_win_stay_pairs"], 2.0)

    def test_omissions_do_not_produce_a_choice_pair(self) -> None:
        rows = [
            {"block": 0, "trial": i, "stimulus": "", "response": c, "rt_sec": 1.0 if c else float("nan"),
             "condition": "", "onset_sec": float(i), "logged_correct": float("nan"), "feedback": f}
            for i, (c, f) in enumerate([("1", "win"), ("", "loss"), ("2", "win")])
        ]
        features, _ = doors_features(_trials(rows), self.bspec)
        self.assertAlmostEqual(features["signal_omission_rate"], 1 / 3)
        self.assertNotIn("signal_win_stay_rate", features)


class ReaderTests(unittest.TestCase):
    def test_psychopy_response_codes_are_normalised(self) -> None:
        """PsychoPy writes 1 in one file and 1.0 in its sibling."""
        self.assertEqual(_normalise_code("1.0"), "1")
        self.assertEqual(_normalise_code("2"), "2")
        self.assertEqual(_normalise_code(""), "")
        self.assertEqual(_normalise_code("{LEFTARROW}"), "{LEFTARROW}")

    def test_psychopy_sibling_csvs_are_not_mistaken_for_the_trial_file(self) -> None:
        """A glob that catches _task_loop.csv silently reads the wrong file."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "L1_O_beh_11h13.csv").touch()
            (root / "L1_O_beh__oddball_2025-10-23_11h13_task_loop.csv").touch()
            (root / "L1_O_beh_2025-10-23_11h13_all_loop.csv").touch()
            self.assertEqual([p.name for p in psychopy_trial_files(root)],
                             ["L1_O_beh_11h13.csv"])

    def test_psychopy_trials_map_codes_through_the_specification(self) -> None:
        spec = load_paradigm_spec()
        bspec = spec.behaviour("yiruid", "doors")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "trials.csv"
            path.write_text(
                "feedback,task_resp.keys,task_resp.rt,all_loop.thisN,task_loop.thisN,task.started\n"
                "1,1,0.5,0,0,30.0\n"
                "2,2,0.6,0,1,36.0\n"
                ",,,,,\n",
                encoding="utf-8")
            frame = read_psychopy_trials(path, bspec)
        self.assertEqual(list(frame["feedback"]), ["loss", "win"])
        self.assertEqual(list(frame["response"]), ["1", "2"])

    def test_eprime_log_is_parsed_from_utf16(self) -> None:
        spec = load_paradigm_spec()
        bspec = spec.behaviour("bikom", "doors")
        text = "\r\n".join([
            "*** Header Start ***", "Subject: 1", "*** Header End ***",
            "*** LogFrame Start ***", "Procedure: blocke", "pic3: 2.jpg",
            "List2.Cycle: 1", "List2.Sample: 1",
            "ImageDisplay9.OnsetTime: 74055", "ImageDisplay9.RT: 2964",
            "ImageDisplay9.RESP: 1", "*** LogFrame End ***",
            "*** LogFrame Start ***", "Procedure: blocke", "pic3: 1.jpg",
            "List2.Cycle: 1", "List2.Sample: 2",
            "ImageDisplay9.OnsetTime: 80055", "ImageDisplay9.RT: 0",
            "ImageDisplay9.RESP: ", "*** LogFrame End ***",
        ])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "log.txt"
            path.write_bytes(text.encode("utf-16"))
            header, frames = parse_eprime_frames(path)
            frame = read_eprime_trials(path, bspec)
        self.assertEqual(header["Subject"], "1")
        self.assertEqual(len(frames), 2)
        self.assertEqual(list(frame["feedback"]), ["win", "loss"])
        self.assertAlmostEqual(frame.loc[0, "rt_sec"], 2.964)
        self.assertAlmostEqual(frame.loc[0, "onset_sec"], 74.055)
        # A non-response logs RT 0; that is not a 0 ms reaction time.
        self.assertTrue(pd.isna(frame.loc[1, "rt_sec"]))


class FeatureTableTests(unittest.TestCase):
    """Checks against the extracted tables, skipped when they are absent."""

    def setUp(self) -> None:
        if not BEHAVIOUR_DIR.exists():
            self.skipTest("behavioural features not extracted")
        self.paths = sorted(BEHAVIOUR_DIR.glob("*_signal_features.csv"))
        if not self.paths:
            self.skipTest("behavioural features not extracted")

    def test_tables_hold_no_pilot_holdout_subject(self) -> None:
        for path in self.paths + sorted(BEHAVIOUR_DIR.glob("*_qc_features.csv")):
            frame = pd.read_csv(path, dtype={"L_id": str})
            self.assertTrue((frame["split_group"] == "cv").all(), path.name)
            self.assertEqual(int(pd.to_numeric(frame["is_locked_test"], errors="coerce")
                                 .fillna(0).sum()), 0, path.name)

    def test_qc_tables_carry_no_task_performance(self) -> None:
        """`signal_qc vs qc` only tests anything if QC is not itself behaviour."""
        forbidden = ("qc_response_rate", "qc_accuracy", "qc_dprime", "qc_rt")
        for path in sorted(BEHAVIOUR_DIR.glob("*_qc_features.csv")):
            columns = pd.read_csv(path, nrows=0).columns
            for name in columns:
                self.assertFalse(name.startswith(forbidden), f"{path.name}:{name}")

    def test_bikom_oddball_has_no_feature_table(self) -> None:
        self.assertFalse((BEHAVIOUR_DIR / "bikom_oddball_signal_features.csv").exists())


class IncrementCreditTests(unittest.TestCase):
    """A win over a comparator that is itself at chance is not an increment."""

    def _required(self, comparator_auroc: float) -> tuple[pd.DataFrame, pd.DataFrame]:
        required = pd.DataFrame([
            {"cv_protocol": protocol, "cohort_name": "c", "modality": "behaviour",
             "device": "yiruid", "task": "combined", "model": "random_forest",
             "comparison": "signal_vs_demographics", "auroc_diff": 0.08,
             "auroc_diff_ci_low": 0.01, "auroc_diff_ci_high": 0.16,
             "significant_positive": 1, "significant_negative": 0}
            for protocol in ("standard_cv", "group_cv")
        ])
        pooled = pd.DataFrame([
            {"cv_protocol": protocol, "cohort_name": "c", "model": "random_forest",
             "feature_set": "demographics", "threshold_type": "inner_cv",
             "auroc": comparator_auroc}
            for protocol in ("standard_cv", "group_cv")
        ])
        return required, pooled

    def test_credit_is_withheld_when_the_comparator_is_below_chance(self) -> None:
        required, pooled = self._required(0.47)
        credited = credit_increments(required, pooled)
        self.assertEqual(int(credited["significant_positive"].sum()), 2)
        self.assertEqual(int(credited["significant_positive_credited"].sum()), 0)
        decision = unit_decision(credited)
        self.assertEqual(decision.loc[0, "decision"], "NO_INDEPENDENT_SIGNAL")
        self.assertEqual(int(decision.loc[0, "uncredited_positive_comparator_at_chance"]), 2)

    def test_credit_is_given_when_the_comparator_is_above_chance(self) -> None:
        required, pooled = self._required(0.62)
        credited = credit_increments(required, pooled)
        self.assertEqual(int(credited["significant_positive_credited"].sum()), 2)
        decision = unit_decision(credited)
        self.assertEqual(decision.loc[0, "decision"], "INDEPENDENT_SIGNAL_SUPPORTED")

    def test_one_protocol_alone_is_not_enough(self) -> None:
        required, pooled = self._required(0.62)
        required.loc[required["cv_protocol"] == "group_cv", "auroc_diff_ci_low"] = -0.01
        required.loc[required["cv_protocol"] == "group_cv", "significant_positive"] = 0
        decision = unit_decision(credit_increments(required, pooled))
        self.assertEqual(decision.loc[0, "decision"], "NO_INDEPENDENT_SIGNAL")


class ResultsTests(unittest.TestCase):
    """Checks against the produced results, skipped when they are absent."""

    def setUp(self) -> None:
        self.path = PROJECT_ROOT / "results" / "goal2_9" / "required_increments.csv"
        if not self.path.exists():
            self.skipTest("Goal 2.9 matrix not run")
        self.required = pd.read_csv(self.path)

    def test_no_credited_increment_over_demographics(self) -> None:
        """Every interval that excluded zero beat a comparator at chance."""
        self.assertEqual(int(self.required["significant_positive_credited"].sum()), 0)

    def test_uncredited_positives_all_come_from_the_combined_yiruid_cohort(self) -> None:
        positive = self.required[self.required["significant_positive"] == 1]
        self.assertTrue((positive["comparator_auroc"] < 0.5).all())
        self.assertEqual(set(positive["task"]), {"combined"})
        self.assertEqual(set(positive["device"]), {"yiruid"})


class MatrixConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = load_goal_config("configs/goal2_9/models.yaml")

    def test_inherits_goal2_7_grids_and_bootstrap(self) -> None:
        goal2_7 = load_goal_config("configs/goal2_7/models.yaml")
        self.assertEqual(self.config["models"]["tabular"], goal2_7["models"]["tabular"])
        self.assertEqual(self.config["hyperparameters"], goal2_7["hyperparameters"])
        bootstrap = load_goal_config("configs/goal2_7/bootstrap.yaml")["bootstrap"]
        for key in ("n_resamples", "paired_n_resamples", "ci", "seed", "paired_seed"):
            self.assertEqual(self.config["bootstrap"][key], bootstrap[key], key)

    def test_every_output_stays_inside_goal2_9(self) -> None:
        """An inherited key pointing at results/goal2_7 once slipped through."""
        for key, value in self.config["outputs"].items():
            self.assertIn("goal2_9", str(value), key)

    def test_split_files_are_the_frozen_ones(self) -> None:
        self.assertEqual(self.config["paths"]["split_file"],
                         "artifacts/splits/subject_splits_v1.csv")
        self.assertEqual(self.config["paths"]["group_split_file"],
                         "artifacts/splits/subject_splits_group_robustness_v1.csv")

    def test_bikom_oddball_is_not_a_unit(self) -> None:
        units = {(u["device"], u["task"]) for u in self.config["goal2_9"]["units"]}
        self.assertNotIn(("bikom", "oddball"), units)
        self.assertIn(("bikom", "doors"), units)
        self.assertIn(("yiruid", "oddball"), units)


if __name__ == "__main__":
    unittest.main()
