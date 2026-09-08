"""Goal 2.8 paradigm specification and conformance tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from chongqing_binary.paradigm import load_paradigm_spec
from chongqing_binary.paths import raw_data_root


class ParadigmSpecTests(unittest.TestCase):
    def setUp(self) -> None:
        self.spec = load_paradigm_spec()

    def test_spec_loads_with_required_sections(self) -> None:
        self.assertTrue(self.spec.version)
        self.assertIn("eeg_oddball_script", self.spec.sources)
        self.assertIn("face_web_log", self.spec.sources)

    def test_every_value_carrying_section_names_a_source(self) -> None:
        """Task structure must be traceable to a dataset attachment."""
        for task in self.spec.eeg_tasks():
            self.assertIn("source", self.spec.eeg(task).raw, f"eeg/{task} has no source")
        for device in self.spec.fnirs_devices():
            self.assertIn("source", self.spec.data["fnirs"][device], f"fnirs/{device} has no source")

    def test_oddball_declares_both_conditions(self) -> None:
        """The Goal 2.7 blocker claimed only code 22 existed."""
        oddball = self.spec.eeg("oddball")
        self.assertEqual(oddball.codes, ["11", "22"])
        self.assertEqual(oddball.condition_of("11"), "standard")
        self.assertEqual(oddball.condition_of("22"), "deviant_target")
        self.assertEqual(oddball.expected_total("11"), 125)
        self.assertEqual(oddball.expected_total("22"), 25)
        contrast = oddball.primary_contrast
        self.assertEqual(contrast["minuend"], "22")
        self.assertEqual(contrast["subtrahend"], "11")

    def test_1back_positional_codes_excluded_from_contrast(self) -> None:
        """19 is block-initial and 66/77/88 are not conditions."""
        one_back = self.spec.eeg("1back")
        self.assertEqual(one_back.codes_for_contrast(), ["18"])
        self.assertEqual(one_back.condition_of("19"), "block_initial_stimulus")
        self.assertEqual(one_back.event_codes["66"]["lag_trials"], 1)
        self.assertFalse(one_back.event_codes["88"]["usable"])

    def test_1back_match_nonmatch_recorded_as_unrecoverable(self) -> None:
        gap = self.spec.known_gaps["eeg_1back_match_nonmatch"]
        self.assertFalse(gap["recoverable"])

    def test_fnirs_covers_five_tasks_on_both_devices(self) -> None:
        for device in ("yiruid", "bikom"):
            self.assertEqual(
                sorted(self.spec.fnirs_tasks(device)),
                ["1back", "doors", "oddball", "rest", "vft"],
            )

    def test_yiruid_wavelengths_and_geometry_declared(self) -> None:
        """Goal 2.7 recorded these as unconfirmed."""
        vft = self.spec.fnirs("yiruid", "vft")
        self.assertEqual(vft.wavelengths_nm, [690.0, 830.0])
        self.assertEqual(vft.device_raw["n_sources"], 16)
        self.assertEqual(vft.device_raw["n_detectors"], 16)
        self.assertEqual(vft.n_channels, 53)

    def test_bikom_marker_labels_are_preserved(self) -> None:
        one_back = self.spec.fnirs("bikom", "1back")
        self.assertTrue(one_back.device_raw["marker_labels_must_be_preserved"])
        self.assertEqual(one_back.marker_labels["A0"], "block1_task_on")
        self.assertEqual(one_back.marker_labels["B1"], "block2_task_off")

    def test_bikom_vft_is_sensitivity_only(self) -> None:
        vft = self.spec.fnirs("bikom", "vft")
        self.assertEqual(vft.timing_confidence, "low")
        self.assertTrue(vft.sensitivity_only)

    def test_block_windows_expand_multiblock_from_single_marker(self) -> None:
        """Yiruid VFT emits one marker but runs four blocks back to back."""
        windows = self.spec.fnirs("yiruid", "vft").block_windows([30.0])
        self.assertEqual(len(windows), 4)
        self.assertAlmostEqual(windows[0]["task_start"], 30.0)
        self.assertAlmostEqual(windows[-1]["task_end"], 90.0)

    def test_block_windows_apply_intro_offset(self) -> None:
        windows = self.spec.fnirs("yiruid", "1back").block_windows([30.0, 92.0])
        self.assertEqual(len(windows), 2)
        self.assertAlmostEqual(windows[0]["task_start"], 32.0)
        self.assertAlmostEqual(windows[1]["task_start"], 94.0)

    def test_bikom_stim_time_header_flagged_as_antipattern(self) -> None:
        self.assertTrue(self.spec.antipatterns["bikom_stim_time_header"]["must_ignore"])
        self.assertTrue(self.spec.antipatterns["v1_oddball_cache_event_codes"]["must_ignore"])

    def test_face_movie_order_and_durations(self) -> None:
        face = self.spec.face
        self.assertEqual(face["task"]["movie_order"], ["positive", "neutral", "negative"])
        movies = self.spec.face_movies()
        self.assertAlmostEqual(movies["negative"]["stimulus_duration_sec"], 125.00)
        self.assertEqual(movies["negative"]["start_column"], "timevideostart3")


class ParadigmConformanceTests(unittest.TestCase):
    """Small live checks against the raw dataset, skipped when it is absent."""

    def setUp(self) -> None:
        self.root = raw_data_root()
        if not self.root.exists():
            self.skipTest(f"raw dataset not available at {self.root}")
        self.spec = load_paradigm_spec()

    def test_oddball_raw_events_contain_both_codes(self) -> None:
        from chongqing_binary.paradigm.conformance import check_eeg_task

        rows = check_eeg_task(self.spec, "oddball", self.root, n_subjects=3)
        checks = {row["check"]: row for row in rows}
        for code in ("11", "22"):
            key = next(k for k in checks if k.startswith(f"code_{code}_present"))
            self.assertEqual(checks[key]["status"], "pass", checks[key])

    def test_yiruid_vft_marker_matches_spec(self) -> None:
        from chongqing_binary.paradigm.conformance import check_fnirs_task

        rows = check_fnirs_task(self.spec, "yiruid", "vft", self.root, n_subjects=2)
        checks = {row["check"]: row for row in rows}
        self.assertEqual(checks["marker_count"]["status"], "pass", checks["marker_count"])
        self.assertEqual(checks["wavelengths_nm"]["status"], "pass", checks["wavelengths_nm"])


if __name__ == "__main__":
    unittest.main()
