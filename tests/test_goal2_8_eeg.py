"""Goal 2.8 EEG pipeline tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from chongqing_binary.goal2_8.config import load_goal_config
from chongqing_binary.goal2_8.eeg_epochs import _match_role
from chongqing_binary.goal2_8.fnirs_io import (
    EXTINCTION,
    differential_pathlength_factor,
    modified_beer_lambert,
    optical_density,
)
from chongqing_binary.paradigm import load_paradigm_spec


class Goal28EegConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = load_goal_config("configs/goal2_8/eeg.yaml")
        self.eeg = self.config["eeg"]

    def test_reject_threshold_is_per_task(self) -> None:
        """A 2 s epoch cannot share a 1 s epoch's peak-to-peak threshold."""
        thresholds = self.eeg["reject_peak_to_peak_volts"]
        self.assertIsInstance(thresholds, dict)
        self.assertLess(thresholds["oddball"], thresholds["1back"])
        self.assertLess(thresholds["1back"], thresholds["rest"])

    def test_blink_channels_excluded_from_rejection(self) -> None:
        self.assertEqual(self.eeg["reject_exclude_channels"], ["Fp1", "Fp2"])

    def test_scale_converts_microvolts_to_volts(self) -> None:
        self.assertAlmostEqual(float(self.eeg["bdf_to_volts_scale"]), 1e-6)

    def test_rest_uses_continuous_windows_not_events(self) -> None:
        rest = self.eeg["rest"]
        self.assertGreater(float(rest["window_sec"]), 0)
        self.assertIn("alpha", rest["bands"])
        self.assertIn("frontal", rest["asymmetry_pairs"])


class RoleMatchingTests(unittest.TestCase):
    def test_matches_both_naming_conventions(self) -> None:
        """Bare data.bdf must match too; missing it cost 329 subjects."""
        import tempfile

        spec = load_paradigm_spec()
        patterns = spec.eeg_common["data_file_patterns"]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "L1_data.bdf").touch()
            self.assertEqual([p.name for p in _match_role(root, patterns)], ["L1_data.bdf"])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "data.bdf").touch()
            self.assertEqual([p.name for p in _match_role(root, patterns)], ["data.bdf"])

    def test_never_matches_the_identifiable_file(self) -> None:
        import tempfile

        spec = load_paradigm_spec()
        patterns = spec.eeg_common["data_file_patterns"]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "data.bdf").touch()
            (root / "张三.bdf").touch()  # participant-named copy
            names = [p.name for p in _match_role(root, patterns)]
            self.assertEqual(names, ["data.bdf"])


class MbllTests(unittest.TestCase):
    """The conversion Goal 2.7 declared impossible for want of wavelengths."""

    def test_extinction_table_covers_recorded_wavelengths(self) -> None:
        spec = load_paradigm_spec()
        for device in ("yiruid", "bikom"):
            for wavelength in spec.data["fnirs"][device]["wavelengths_nm"]:
                self.assertIn(int(round(wavelength)), EXTINCTION)

    def test_dpf_is_wavelength_and_age_dependent(self) -> None:
        young = differential_pathlength_factor(690, 10)
        old = differential_pathlength_factor(690, 40)
        self.assertGreater(old, young)
        self.assertNotAlmostEqual(differential_pathlength_factor(690, 13),
                                  differential_pathlength_factor(830, 13))
        self.assertTrue(3.0 < differential_pathlength_factor(690, 13) < 8.0)

    def test_mbll_recovers_known_concentrations(self) -> None:
        """Forward-model a known HbO/HbR pair, then invert it."""
        wavelengths = [690.0, 830.0]
        distances = np.array([30.0, 30.0])
        age = 13.0
        hbo_true, hbr_true = 2.0e-6, -1.0e-6  # molar
        ext = np.array([[EXTINCTION[690]["HbO"], EXTINCTION[690]["HbR"]],
                        [EXTINCTION[830]["HbO"], EXTINCTION[830]["HbR"]]])
        dpf = np.array([differential_pathlength_factor(w, age) for w in wavelengths])
        path_cm = (distances / 10.0)[None, :] * dpf[:, None]
        att = (ext @ np.array([hbo_true, hbr_true]))[:, None, None] * path_cm[:, None, :]
        od = np.concatenate([att[0], att[1]], axis=1)  # (1, 4): w1 ch0,ch1 then w2 ch0,ch1
        ml = np.array([[1, 1, 1, 1], [2, 2, 1, 1], [1, 1, 1, 2], [2, 2, 1, 2]], dtype=float)
        hbo, hbr = modified_beer_lambert(od, ml, wavelengths, distances, age)
        self.assertAlmostEqual(float(hbo[0, 0]), hbo_true * 1e6, places=4)
        self.assertAlmostEqual(float(hbr[0, 0]), hbr_true * 1e6, places=4)

    def test_optical_density_zero_on_constant_signal(self) -> None:
        od = optical_density(np.full((100, 4), 5000.0))
        self.assertTrue(np.allclose(od, 0.0, atol=1e-9))

    def test_mbll_rejects_wrong_wavelength_count(self) -> None:
        with self.assertRaises(ValueError):
            modified_beer_lambert(np.zeros((10, 2)), np.zeros((2, 4)), [690.0], np.array([30.0]), 13.0)


if __name__ == "__main__":
    unittest.main()
