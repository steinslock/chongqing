"""Goal 2.8 Face segmentation tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from chongqing_binary.goal2_8.config import load_goal_config
from chongqing_binary.goal2_8.face import _expand, _largest_box, _sample_times
from chongqing_binary.goal2_8.face_segments import _to_seconds
from chongqing_binary.paradigm import load_paradigm_spec


class WebLogTimestampTests(unittest.TestCase):
    def test_parses_h_m_s_ms(self) -> None:
        self.assertAlmostEqual(_to_seconds("3:29:29:98"), 3 * 3600 + 29 * 60 + 29 + 0.098)

    def test_rejects_malformed(self) -> None:
        for bad in (None, "", "3:29:29", "not a time", "a:b:c:d"):
            self.assertIsNone(_to_seconds(bad))


class InteriorSamplingTests(unittest.TestCase):
    """Frames come from the segment interior so alignment error cannot leak in."""

    def test_stays_inside_the_segment(self) -> None:
        times = _sample_times(100.0, 200.0, 16, 0.8)
        self.assertEqual(len(times), 16)
        self.assertGreaterEqual(min(times), 110.0)
        self.assertLessEqual(max(times), 190.0)

    def test_margin_scales_with_interior_fraction(self) -> None:
        wide = _sample_times(0.0, 100.0, 8, 1.0)
        narrow = _sample_times(0.0, 100.0, 8, 0.5)
        self.assertLess(min(wide), min(narrow))
        self.assertGreater(max(wide), max(narrow))

    def test_degenerate_segment_does_not_invert(self) -> None:
        times = _sample_times(50.0, 50.5, 4, 0.8)
        self.assertTrue(all(50.0 <= t <= 50.5 for t in times))


class DetectionHelperTests(unittest.TestCase):
    def test_largest_box_selected(self) -> None:
        faces = [[10, 10, 20, 20], [0, 0, 50, 50]]
        self.assertEqual(_largest_box(faces), (0, 0, 50, 50))

    def test_no_detection_returns_none(self) -> None:
        self.assertIsNone(_largest_box(None))
        self.assertIsNone(_largest_box([]))

    def test_expand_stays_within_frame(self) -> None:
        x, y, w, h = _expand((5, 5, 20, 20), 100, 100, scale=3.0)
        self.assertGreaterEqual(x, 0)
        self.assertGreaterEqual(y, 0)
        self.assertLessEqual(x + w, 100)
        self.assertLessEqual(y + h, 100)


class FaceConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = load_goal_config("configs/goal2_8/face.yaml")["face"]
        self.spec = load_paradigm_spec()

    def test_yunet_required_and_haar_is_a_failure(self) -> None:
        """Goal 2.7 silently fell back to Haar on 99 percent of videos."""
        self.assertEqual(self.config["detector"]["preferred"], "opencv_yunet")
        self.assertTrue(self.config["detector"]["fallback_is_qc_failure"])

    def test_yunet_checkpoint_exists(self) -> None:
        from chongqing_binary.goal2_8.config import project_path

        self.assertTrue(project_path(self.config["detector"]["checkpoint"]).exists())

    def test_contrast_pairs_are_within_subject(self) -> None:
        pairs = self.spec.face["task"]["primary_contrast"]["pairs"]
        order = self.spec.face["task"]["movie_order"]
        self.assertTrue(pairs)
        for minuend, subtrahend in pairs:
            self.assertIn(minuend, order)
            self.assertIn(subtrahend, order)
            self.assertNotEqual(minuend, subtrahend)

    def test_frames_sampled_per_segment_not_per_session(self) -> None:
        self.assertGreaterEqual(int(self.config["frames_per_segment"]), 8)
        self.assertLess(float(self.config["segment_interior_fraction"]), 1.0)


if __name__ == "__main__":
    unittest.main()
