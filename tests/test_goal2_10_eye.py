"""Tests for the Goal 2.10 eye-tracking readiness layer."""

from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from chongqing_binary.eye import aoi as eye_aoi
from chongqing_binary.eye import events as eye_events
from chongqing_binary.eye import features as eye_features
from chongqing_binary.eye import drift as eye_drift
from chongqing_binary.eye import index as eye_index
from chongqing_binary.eye import qc as eye_qc
from chongqing_binary.eye import validity as eye_validity
from chongqing_binary.eye.spec import load_eye_spec
from chongqing_binary.eye.stimuli import FaceStimulusBox, TargetTrack, saccade_trials


class SpecTests(unittest.TestCase):
    def setUp(self) -> None:
        self.spec = load_eye_spec()

    def test_spec_records_the_paradigm_document_and_its_scope(self) -> None:
        # Until 2026-09-09 附件/ held no eye paradigm and this test asserted the
        # opposite, so that decoded stimulus media could not be passed off as
        # protocol documentation. The hospital then supplied
        # 重医眼动范式及参数.docx and the guard has to move rather than go away:
        # the risk is now that a reader takes the document's SECOND table, a
        # gaze-contingent battery belonging to a device with no data here, for a
        # description of these recordings.
        self.assertTrue(self.spec.attachment_available)
        self.assertEqual(self.spec.raw["attachment_path"], "附件/重医眼动范式及参数.docx")
        scope = self.spec.raw["document_scope"]
        self.assertEqual(sorted(scope["applies_to"]), ["qixin_120", "qixin_500", "tobii"])
        self.assertTrue(scope["second_table_is_a_different_device"])
        self.assertEqual(scope["absent_device"]["name"], "集思鸣智")

    def test_viewing_geometry_is_consistent_with_the_decoded_stimulus(self) -> None:
        # The document gives the saccade targets in degrees and the decoded
        # video gives them in screen widths, so the geometry is overdetermined
        # and solving it is also a check on both. It only closes under a
        # tangent mapping; a linear degrees-per-screen-width scale misses by
        # about half a percent, which is why the fit is asserted this tightly.
        geometry = self.spec.raw["viewing_geometry"]
        distance = float(geometry["viewing_distance_screen_widths"])
        amplitudes = self.spec.task("saccade").raw["trial_structure"]["amplitudes_norm"]
        degrees = self.spec.task("saccade").raw["trial_structure"]["amplitudes_deg"]
        for amplitude, expected in zip(amplitudes, degrees):
            self.assertAlmostEqual(math.degrees(math.atan(amplitude / distance)), expected, places=2)
        self.assertAlmostEqual(
            2.0 * math.degrees(math.atan(0.5 / distance)), float(geometry["screen_width_deg"]), places=1
        )

    def test_pursuit_frequencies_are_whole_cycles_of_the_motion_window(self) -> None:
        # spec_version 1 read these off an FFT of the whole 21 s block, which
        # includes 1 s of stationary target, and so quoted every one of them
        # low by 21/20. Each is an exact cycle count over the 20 s of motion
        # the document states; asserting that is what stops the window
        # ambiguity coming back.
        blocks = self.spec.task("smooth_pursuit").raw["pursuit_blocks"]
        motion_s = float(blocks["motion_duration_ms"]) / 1000.0
        self.assertEqual(blocks["block_duration_ms"], blocks["motion_duration_ms"] + blocks["settling_ms"])
        for condition in blocks["conditions"].values():
            for axis in ("x", "y"):
                cycles = condition[f"{axis}_cycles"]
                self.assertEqual(cycles, round(cycles))
                self.assertAlmostEqual(condition[f"{axis}_frequency_hz"], cycles / motion_s, places=6)

    def test_free_viewing_sequence_is_balanced(self) -> None:
        sequence = self.spec.free_viewing_sequence
        self.assertEqual(len(sequence), 36)
        valences = [item.valence for item in sequence]
        sexes = [item.sex for item in sequence]
        for valence in ("happy", "sad", "neutral"):
            self.assertEqual(valences.count(valence), 12)
        self.assertEqual(sexes.count("male"), 18)
        self.assertEqual(sexes.count("female"), 18)

    def test_presentation_order_is_fixed_and_confounded_with_index(self) -> None:
        orders = [item.order for item in self.spec.free_viewing_sequence]
        self.assertEqual(orders, list(range(1, 37)))

    def test_expected_segments_differ_by_device(self) -> None:
        task = self.spec.task("free_viewing")
        self.assertEqual(task.expected_media_segments("qixin_120"), 110)
        self.assertEqual(task.expected_media_segments("qixin_500"), 109)
        self.assertEqual(task.expected_media_segments("tobii"), 109)

    def test_sixty_hz_device_forbids_velocity_features(self) -> None:
        self.assertFalse(self.spec.device("tobii").velocity_features_permitted)
        self.assertTrue(self.spec.device("qixin_500").velocity_features_permitted)

    def test_known_defects_are_recorded(self) -> None:
        for defect in ("qixin_annotation_empty", "duplicate_recordings", "manifest_undercounts_eye"):
            self.assertIn(defect, self.spec.known_defects)


class IndexTests(unittest.TestCase):
    def test_a_id_extraction(self) -> None:
        self.assertEqual(eye_index.extract_a_id("A02062_<name>_251105161924"), "A02062")
        self.assertEqual(eye_index.extract_a_id("眼动-tobbi E16284<name>_free"), "E16284")
        self.assertIsNone(eye_index.extract_a_id("User1_251028130305"))

    def test_recordings_without_a_id_are_discarded_not_kept(self) -> None:
        rows = [
            {"device": "qixin_120", "task": "free_viewing", "a_id": None, "record_name": "User1_x", "path": "/p1"},
            {"device": "qixin_120", "task": "free_viewing", "a_id": "A02062", "record_name": "r", "path": "/p2"},
        ]
        kept, discarded = eye_index.resolve_duplicates(rows)
        self.assertEqual([row["path"] for row in kept], ["/p2"])
        self.assertEqual(discarded[0]["discard_reason"], "missing_a_id")

    def test_duplicate_take_with_complete_timeline_wins(self) -> None:
        rows = [
            {
                "device": "qixin_120", "task": "free_viewing", "a_id": "A02062", "path": "/short",
                "timeline_complete": 0, "n_media_segments": 12, "record_duration_ms": 900000, "recorded_at": "251015095814",
            },
            {
                "device": "qixin_120", "task": "free_viewing", "a_id": "A02062", "path": "/full",
                "timeline_complete": 1, "n_media_segments": 110, "record_duration_ms": 243567, "recorded_at": "251015100119",
            },
        ]
        kept, discarded = eye_index.resolve_duplicates(rows)
        self.assertEqual(kept[0]["path"], "/full")
        self.assertEqual(kept[0]["n_takes"], 2)
        self.assertEqual(discarded[0]["discard_reason"], "duplicate_take")
        self.assertEqual(discarded[0]["kept_path"], "/full")

    def test_subjects_join_on_a_id_not_name(self) -> None:
        split = {"A02062": {"L_id": "L9", "split_group": "cv", "cv_fold": "3"}}
        rows = eye_index.attach_subjects(
            [{"device": "qixin_120", "task": "free_viewing", "a_id": "A02062", "record_name": "A02062_<name>_1"}], split
        )
        self.assertEqual(rows[0]["L_id"], "L9")
        self.assertEqual(rows[0]["split_group"], "cv")
        self.assertEqual(rows[0]["group_prefix3"], "A02")


class StimulusTests(unittest.TestCase):
    def _formal_track(self) -> TargetTrack:
        # 8 trials: centre 1.5 s, target 1.0 s, repeating with a 2.5 s period.
        x = np.full(1200, 0.5)
        targets = [0.6396, 0.3604, 0.2177, 0.7823, 0.3604, 0.7823, 0.6396, 0.2177]
        for trial, position in enumerate(targets):
            start = 90 + trial * 150
            x[start : start + 60] = position
        return TargetTrack(media="t", fps=60.0, x=x, y=np.full(1200, 0.5))

    def test_saccade_trials_recovered_exactly(self) -> None:
        trials = saccade_trials(self._formal_track())
        self.assertEqual(len(trials), 8)
        self.assertAlmostEqual(trials[0]["onset_ms"], 1500.0, places=6)
        self.assertAlmostEqual(trials[1]["onset_ms"], 4000.0, places=6)
        self.assertEqual([trial["direction"] for trial in trials], [1, -1, -1, 1, -1, 1, 1, -1])

    def test_subpixel_wobble_does_not_create_trials(self) -> None:
        # The decoded centroid moves by a fraction of a pixel between frames.
        # A naive difference-based detector turns that into spurious trials.
        track = self._formal_track()
        rng = np.random.default_rng(0)
        noisy = TargetTrack(
            media="t", fps=60.0, x=track.x + rng.normal(0, 2e-5, track.x.size), y=track.y
        )
        self.assertEqual(len(saccade_trials(noisy)), 8)


class ClockAlignmentTests(unittest.TestCase):
    def _samples(self, n: int, span_ms: float) -> "pd.DataFrame":
        import pandas as pd

        micro = np.linspace(0.0, span_ms * 1000.0, n)
        return pd.DataFrame({"timestampUs": micro, "time_ms": micro / 1000.0})

    def test_f500_drift_is_removed(self) -> None:
        from chongqing_binary.eye import qixin as qixin_io

        # 136 s of samples whose own clock runs 0.4 percent long.
        samples = self._samples(68000, 136544.0)
        aligned = qixin_io.aligned_time_ms(samples, 136000.0)
        self.assertAlmostEqual(float(aligned[-1]), 136000.0, places=3)
        self.assertAlmostEqual(qixin_io.clock_scale(samples, 136000.0), 136000.0 / 136544.0, places=9)

    def test_missing_duration_leaves_the_clock_alone(self) -> None:
        from chongqing_binary.eye import qixin as qixin_io

        samples = self._samples(1000, 5000.0)
        self.assertAlmostEqual(float(qixin_io.aligned_time_ms(samples, None)[-1]), 5000.0, places=6)


class ValidityTests(unittest.TestCase):
    def _box(self) -> FaceStimulusBox:
        return FaceStimulusBox(
            media="1-NEF15", valence="neutral", sex="female", order=1,
            x0=0.4, y0=0.3, x1=0.6, y1=0.7, image_width=1920, image_height=1080,
        )

    def test_on_face_dwell_exceeds_chance_when_gaze_is_on_the_face(self) -> None:
        time_ms = np.arange(0, 4000, 10, dtype=float)
        trace = eye_validity.GazeTrace(
            time_ms,
            np.full(time_ms.size, 0.5),
            np.full(time_ms.size, 0.5),
            np.ones(time_ms.size, dtype=bool),
        )
        result = eye_validity.free_viewing_on_face(trace, [("1-NEF15", 0.0, 4000.0)], {"1-NEF15": self._box()})
        self.assertEqual(result["on_face_fraction"], 1.0)
        self.assertGreater(result["on_face_over_chance"], 10.0)

    def test_antisaccade_scoring_rewards_looking_away(self) -> None:
        track = StimulusTests()._formal_track()
        time_ms = np.arange(0, 20000, 10, dtype=float)
        x = np.full(time_ms.size, 0.5)
        for trial in saccade_trials(track):
            window = (time_ms >= trial["onset_ms"] + 200) & (time_ms <= trial["offset_ms"])
            x[window] = 0.5 - trial["direction"] * 0.25  # mirrored, i.e. correct antisaccade
        trace = eye_validity.GazeTrace(time_ms, x, np.full(time_ms.size, 0.5), np.ones(time_ms.size, dtype=bool))
        correct = eye_validity.saccade_direction_agreement(trace, track, 0.0, 20000.0, antisaccade=True)
        wrong = eye_validity.saccade_direction_agreement(trace, track, 0.0, 20000.0, antisaccade=False)
        self.assertEqual(correct["n_trials_scored"], 8)
        # The recorded block ends a few tens of ms before the video does; the
        # final trial must be clamped, not dropped.
        short = eye_validity.saccade_direction_agreement(trace, track, 0.0, 19980.0, antisaccade=True)
        self.assertEqual(short["n_trials_scored"], 8)
        self.assertEqual(correct["direction_correct_rate"], 1.0)
        self.assertEqual(wrong["direction_correct_rate"], 0.0)


class AoiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.spec = load_eye_spec()
        self.config = self.spec.task("free_viewing").raw["aoi"]

    def test_aoi_config_is_marked_an_analysis_choice(self) -> None:
        # The rest of this specification is recovered fact; these are not, and
        # the distinction has to survive being read by someone else.
        self.assertEqual(self.config["source"], "analysis_choice")

    def test_haar_fallback_is_a_failure_here(self) -> None:
        self.assertTrue(self.config["detector_fallback_is_qc_failure"])
        self.assertEqual(self.config["detector"], "opencv_yunet")

    def test_regions_are_disjoint_and_exhaustive(self) -> None:
        aoi = eye_aoi.StimulusAoi(
            media="m", valence="sad", sex="male", order=1,
            face=eye_aoi.Rect(0.40, 0.30, 0.60, 0.70),
            eyes=eye_aoi.Rect(0.43, 0.36, 0.57, 0.47),
            mouth=eye_aoi.Rect(0.44, 0.52, 0.56, 0.61),
            detector="opencv_yunet", detector_score=0.9, interocular_distance=0.07,
        )
        x = np.array([0.50, 0.50, 0.50, 0.10])
        y = np.array([0.42, 0.56, 0.33, 0.10])  # eyes, mouth, face_other, off_face
        shares = aoi.shares(x, y)
        self.assertAlmostEqual(sum(shares.values()), 1.0, places=9)
        self.assertEqual(shares["eyes"], 0.25)
        self.assertEqual(shares["mouth"], 0.25)
        self.assertEqual(shares["face_other"], 0.25)
        self.assertEqual(shares["off_face"], 0.25)
        self.assertFalse(aoi.eyes.overlaps(aoi.mouth))


class DriftTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = load_eye_spec().task("free_viewing").raw["drift_correction"]

    def _trace_with_offset(self, dx: float, dy: float, n_crosses: int) -> tuple[Any, list]:
        time_ms = np.arange(0, n_crosses * 1000, 10, dtype=float)
        trace = eye_validity.GazeTrace(
            time_ms,
            np.full(time_ms.size, 0.5 + dx),
            np.full(time_ms.size, 0.5 + dy),
            np.ones(time_ms.size, dtype=bool),
        )
        segments = [("中央十字", float(i * 1000), float(i * 1000 + 990)) for i in range(n_crosses)]
        return trace, segments

    def test_offset_is_recovered(self) -> None:
        trace, segments = self._trace_with_offset(0.01, 0.06, 36)
        estimate = eye_drift.estimate_drift(trace, segments, self.config)
        self.assertTrue(estimate.usable)
        self.assertEqual(estimate.n_crosses, 36)
        self.assertAlmostEqual(estimate.dx, 0.01, places=9)
        self.assertAlmostEqual(estimate.dy, 0.06, places=9)
        x, y = estimate.apply(np.array([0.51]), np.array([0.56]))
        self.assertAlmostEqual(float(x[0]), 0.50, places=9)
        self.assertAlmostEqual(float(y[0]), 0.50, places=9)

    def test_too_few_crosses_leaves_gaze_untouched(self) -> None:
        trace, segments = self._trace_with_offset(0.01, 0.06, 3)
        estimate = eye_drift.estimate_drift(trace, segments, self.config)
        self.assertFalse(estimate.usable)
        x, y = estimate.apply(np.array([0.51]), np.array([0.56]))
        self.assertEqual(float(x[0]), 0.51)
        self.assertEqual(float(y[0]), 0.56)
        self.assertEqual(estimate.as_qc()["drift_applied"], 0)

    def test_correction_flips_the_eye_mouth_contrast(self) -> None:
        # A downward offset the size of the measured one moves gaze from the
        # eye band into the mouth band. This is the device-level bias that
        # would otherwise enter a model as a site shortcut.
        aoi = eye_aoi.StimulusAoi(
            media="m", valence="sad", sex="male", order=1,
            face=eye_aoi.Rect(0.40, 0.30, 0.60, 0.70),
            eyes=eye_aoi.Rect(0.43, 0.37, 0.57, 0.47),
            mouth=eye_aoi.Rect(0.44, 0.52, 0.56, 0.61),
            detector="opencv_yunet", detector_score=0.9, interocular_distance=0.07,
        )
        looked_at = 0.42
        offset = 0.14
        x = np.full(100, 0.50)
        y = np.full(100, looked_at + offset)
        raw = aoi.shares(x, y)
        self.assertGreater(raw["mouth"], raw["eyes"])
        corrected = aoi.shares(*eye_drift.DriftEstimate(0.0, offset, 36, 0.0, 0.0, True).apply(x, y))
        self.assertGreater(corrected["eyes"], corrected["mouth"])


class EventTests(unittest.TestCase):
    def test_blink_does_not_merge_or_inflate_fixations(self) -> None:
        time_ms = np.arange(0, 1100, 10.0)
        x = np.where(time_ms < 500, 0.4, np.where(time_ms < 520, np.nan, 0.6))
        y = np.full_like(time_ms, 0.5)
        events = eye_events.detect_fixations(time_ms, x, y, dispersion=0.025, min_duration_ms=80, max_gap_ms=75)
        self.assertEqual(events.count, 2)
        # The first fixation must end at its last sample with gaze, not at the
        # sample that broke the window.
        self.assertAlmostEqual(events.fixations[0].end_ms, 490.0, places=6)
        self.assertAlmostEqual(events.scanpath_length(), 0.2, places=6)

    def test_dispersion_threshold_is_not_a_visual_angle(self) -> None:
        config = load_eye_spec().task("free_viewing").raw["events"]
        self.assertIn("dispersion_screen_fraction", config)
        self.assertNotIn("dispersion_degrees", config)
        self.assertEqual(config["algorithm"], "I-DT")

    def test_short_dwell_is_not_a_fixation(self) -> None:
        time_ms = np.arange(0, 60, 10.0)
        events = eye_events.detect_fixations(
            time_ms, np.full(6, 0.5), np.full(6, 0.5), dispersion=0.025, min_duration_ms=80, max_gap_ms=75
        )
        self.assertEqual(events.count, 0)


class FeatureTests(unittest.TestCase):
    def _trials(self) -> "pd.DataFrame":
        import pandas as pd

        rows = []
        for trial in range(1, 37):
            valence = ("happy", "neutral", "sad")[trial % 3]
            for window in ("early", "late"):
                rows.append(
                    {
                        "trial": trial, "media": f"m{trial}", "valence": valence,
                        "stimulus_sex": "male", "window": window, "n_samples": 100,
                        "valid_fraction": 1.0, "n_fixations": 8.0 + (valence == "sad"),
                        "mean_fixation_ms": 200.0, "scanpath": 0.3, "bcea": 0.01,
                        "pupil_delta": 0.1 if valence == "sad" else 0.0,
                        "eyes_share": 0.5, "mouth_share": 0.2,
                        "face_other_share": 0.25, "off_face_share": 0.05,
                        "first_fixation_ms": 60.0, "first_fixation_on_eyes": 1.0,
                    }
                )
        return pd.DataFrame(rows)

    def test_contrasts_are_differences_of_the_absolute_features(self) -> None:
        features = eye_features.free_viewing_subject_features(self._trials())
        sad = features["signal_late_sad_n_fixations"]
        neutral = features["signal_late_neutral_n_fixations"]
        self.assertAlmostEqual(
            features["signal_contrast_late_sad_minus_neutral_n_fixations"], sad - neutral, places=9
        )
        self.assertAlmostEqual(features["signal_contrast_late_sad_minus_neutral_pupil_delta"], 0.1, places=9)

    def test_absolute_features_are_kept_beside_the_contrasts(self) -> None:
        # Difference scores are the part of this literature whose reliability
        # collapses, so the absolute measures must not be dropped for them.
        features = eye_features.free_viewing_subject_features(self._trials())
        for valence in ("happy", "neutral", "sad"):
            self.assertIn(f"signal_late_{valence}_eyes_share", features)
        self.assertIn("signal_contrast_late_sad_minus_neutral_eyes_share", features)

    def test_trial_index_trend_is_reported(self) -> None:
        # Presentation order is fixed, so trial index and valence are
        # confounded by design and the trend has to be visible.
        features = eye_features.free_viewing_subject_features(self._trials())
        self.assertIn("signal_trend_eyes_share", features)

    def test_split_half_needs_enough_subjects(self) -> None:
        import pandas as pd

        odd = pd.DataFrame({"signal_a": np.linspace(0, 1, 10)})
        even = pd.DataFrame({"signal_a": np.linspace(0, 1, 10)})
        result = eye_features.split_half_reliability(odd, even, ["signal_a"], min_subjects=20)
        self.assertTrue(np.isnan(result.loc[0, "spearman_brown"]))
        bigger = pd.DataFrame({"signal_a": np.linspace(0, 1, 40)})
        result = eye_features.split_half_reliability(bigger, bigger, ["signal_a"], min_subjects=20)
        self.assertAlmostEqual(result.loc[0, "spearman_brown"], 1.0, places=6)


class SaccadeScoringTests(unittest.TestCase):
    def test_antisaccade_error_and_correction_are_scored(self) -> None:
        from chongqing_binary.eye.trace import GazeTrace

        track = StimulusTests()._formal_track()
        config = load_eye_spec().task("saccade").raw["scoring"]
        time_ms = np.arange(0, 20000, 5.0)
        x = np.full(time_ms.size, 0.5)
        for trial in saccade_trials(track):
            # Look towards the target first (an antisaccade error), then correct.
            early = (time_ms >= trial["onset_ms"] + 200) & (time_ms < trial["onset_ms"] + 400)
            late = (time_ms >= trial["onset_ms"] + 400) & (time_ms <= trial["offset_ms"])
            x[early] = 0.5 + trial["direction"] * 0.25
            x[late] = 0.5 - trial["direction"] * 0.25
        trace = GazeTrace(time_ms, x, np.full(time_ms.size, 0.5), np.ones(time_ms.size, bool))
        results = eye_features.saccade_trials_scored(trace, track, 0.0, 20000.0, True, config)
        self.assertEqual(len(results), 8)
        self.assertTrue(all(not item.correct for item in results))
        self.assertTrue(all(item.corrected for item in results))
        block = eye_features.saccade_block_features(results, "signal_anti_", velocity_permitted=False)
        self.assertEqual(block["signal_anti_direction_error_rate"], 1.0)
        self.assertEqual(block["signal_anti_corrected_error_rate"], 1.0)
        self.assertNotIn("signal_anti_peak_velocity_median", block)

    def test_velocity_features_are_gated_on_the_device(self) -> None:
        results = [
            eye_features.SaccadeTrialResult(
                trial=0, amplitude=0.14, direction=1, latency_ms=200.0, responded=True,
                correct=True, corrected=False, correction_ms=float("nan"), gain=1.0, peak_velocity=8.0,
            )
        ]
        permitted = eye_features.saccade_block_features(results, "signal_pro_", velocity_permitted=True)
        forbidden = eye_features.saccade_block_features(results, "signal_pro_", velocity_permitted=False)
        self.assertIn("signal_pro_peak_velocity_median", permitted)
        self.assertNotIn("signal_pro_peak_velocity_median", forbidden)


class ReliabilityFindingTests(unittest.TestCase):
    def test_spec_records_that_the_valence_contrasts_are_unreliable(self) -> None:
        # Measured, not assumed. A null on the contrast block is evidence about
        # this paradigm, not about attentional bias as a construct.
        finding = load_eye_spec().task("free_viewing").raw["reliability_finding"]
        self.assertEqual(finding["source"], "measured")
        self.assertEqual(finding["contrast_reliable_on_all_devices"], 0)
        self.assertGreater(finding["absolute_reliable_on_all_devices"], 40)

    def test_a_difference_of_noisy_means_loses_its_reliability(self) -> None:
        # Why the contrasts collapse: subtracting two independently noisy
        # 12-trial means keeps both errors and cancels the shared true variance.
        rng = np.random.default_rng(0)
        n = 300
        trait = rng.normal(0, 1, n)
        noise = 1.6
        def half(seed: int) -> tuple[np.ndarray, np.ndarray]:
            gen = np.random.default_rng(seed)
            sad = trait + gen.normal(0, noise, n)
            neutral = trait + gen.normal(0, noise, n)
            return sad, sad - neutral
        abs_a, con_a = half(1)
        abs_b, con_b = half(2)
        r_abs = float(np.corrcoef(abs_a, abs_b)[0, 1])
        r_con = float(np.corrcoef(con_a, con_b)[0, 1])
        self.assertGreater(r_abs, 0.2)
        self.assertLess(r_con, r_abs)


class PursuitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.spec = load_eye_spec()
        self.task = self.spec.task("smooth_pursuit")

    def test_spec_records_the_blocked_design(self) -> None:
        # An earlier revision called this task continuous. It is six 21 s
        # sinusoidal blocks, three conditions repeated twice.
        blocks = self.task.raw["pursuit_blocks"]
        self.assertEqual(blocks["block_duration_ms"], 21000)
        self.assertEqual(blocks["gap_duration_ms"], 2000)
        self.assertEqual(sorted(blocks["conditions"]), ["horizontal", "lissajous_fast", "lissajous_slow"])
        fast = blocks["conditions"]["lissajous_fast"]
        slow = blocks["conditions"]["lissajous_slow"]
        # The contrast only isolates speed if amplitude is held constant.
        self.assertAlmostEqual(fast["x_amplitude"], slow["x_amplitude"], places=6)
        self.assertAlmostEqual(fast["x_frequency_hz"] / slow["x_frequency_hz"], 2.0, places=1)

    def test_blocks_are_recovered_from_the_decoded_track(self) -> None:
        from chongqing_binary.eye.stimuli import TargetTrack, pursuit_blocks

        fps = 60.0
        x = np.full(8160, 0.5)
        for start in (1260, 2640, 4020, 5400, 6780):
            x[start : start + 120] = np.nan
        track = TargetTrack(media="p", fps=fps, x=x, y=np.full(8160, 0.5))
        blocks = pursuit_blocks(track)
        self.assertEqual(len(blocks), 6)
        self.assertAlmostEqual(blocks[0]["duration_ms"], 21000.0, places=3)
        self.assertAlmostEqual(blocks[1]["start_ms"], 23000.0, places=3)

    def test_catch_up_uses_velocity_not_dispersion(self) -> None:
        # A dispersion detector chops smooth motion at its threshold, so its
        # rate tracks eye speed rather than saccades. That version reported the
        # highest rate in the slowest condition.
        config = self.task.raw["scoring"]
        self.assertIn("catch_up_residual_speed", config)
        self.assertNotIn("catch_up_min_amplitude", config)

    def test_a_saccade_on_top_of_pursuit_is_counted(self) -> None:
        config = self.task.raw["scoring"]
        fs = 500.0
        time_ms = np.arange(0, 10000, 1000.0 / fs)
        target = 0.5 + 0.1 * np.sin(2 * np.pi * 0.2 * time_ms / 1000.0)
        gaze = target.copy()
        # One 20 ms step of 0.05 screen widths: 2.5 widths per second.
        step = (time_ms >= 5000) & (time_ms < 5020)
        gaze[step] += np.linspace(0, 0.05, int(step.sum()))
        gaze[time_ms >= 5020] += 0.05
        flat = np.full(time_ms.size, 0.5)
        result = eye_features._catch_up(time_ms, gaze, flat, target, flat, config)
        self.assertGreaterEqual(result["catch_up_rate_hz"], 0.05)
        self.assertLess(result["smooth_fraction"], 1.0)

    def test_no_saccade_means_fully_smooth(self) -> None:
        config = self.task.raw["scoring"]
        fs = 500.0
        time_ms = np.arange(0, 10000, 1000.0 / fs)
        target = 0.5 + 0.1 * np.sin(2 * np.pi * 0.2 * time_ms / 1000.0)
        flat = np.full(time_ms.size, 0.5)
        result = eye_features._catch_up(time_ms, target, flat, target, flat, config)
        self.assertEqual(result["catch_up_rate_hz"], 0.0)
        self.assertEqual(result["smooth_fraction"], 1.0)

    def test_velocity_gain_is_declared_not_comparable_across_devices(self) -> None:
        config = self.task.raw["scoring"]
        self.assertTrue(config["velocity_gain_not_comparable_across_devices"])

    def test_savgol_gain_survives_high_rate_noise(self) -> None:
        # A plain sample difference returns about 0.21 at 500 Hz where the
        # physiological range is 0.7 to 1.0, because noise dominates the
        # derivative the faster the sampling.
        config = self.task.raw["scoring"]
        rng = np.random.default_rng(0)
        fs = 500.0
        time_ms = np.arange(0, 20000, 1000.0 / fs)
        target = 0.5 + 0.15 * np.sin(2 * np.pi * 0.3 * time_ms / 1000.0)
        gaze = 0.5 + 0.9 * 0.15 * np.sin(2 * np.pi * 0.3 * time_ms / 1000.0) + rng.normal(0, 0.001, time_ms.size)
        gain = eye_features._velocity_gain(time_ms, gaze, target, config)
        self.assertGreater(gain, 0.75)
        self.assertLess(gain, 1.05)


class QcTests(unittest.TestCase):
    def test_gap_summary_ignores_blink_length_dropouts(self) -> None:
        time_ms = np.arange(0, 2000, 10, dtype=float)
        valid = np.ones(time_ms.size, dtype=bool)
        valid[10:20] = False  # 100 ms, a blink
        short = eye_qc._gap_summary(time_ms, valid)
        self.assertEqual(short["n_gaps"], 0)
        valid[100:150] = False  # 500 ms, a tracking failure
        long = eye_qc._gap_summary(time_ms, valid)
        self.assertEqual(long["n_gaps"], 1)


if __name__ == "__main__":
    unittest.main()
