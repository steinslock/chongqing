"""Full-content fNIRS readers for Goal 2.8.

Goal 2.7 probed Yiruid `.nirs` files with `scipy.io.whosmat`, which returns
variable names and shapes but no contents, and therefore recorded the
wavelengths as `unknown_from_header_probe`. Every file in fact carries
`SD.Lambda`, source and detector counts, 3D optode positions and a measurement
list, which is everything the modified Beer-Lambert law needs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

# Extinction coefficients in cm^-1 / (moles/liter), from the Wray et al. (1988)
# tabulation used by HOMER2's GetExtinctions for 690 nm and 830 nm.
EXTINCTION: dict[int, dict[str, float]] = {
    690: {"HbO": 276.0, "HbR": 2051.96},
    830: {"HbO": 974.0, "HbR": 693.04},
    695: {"HbO": 300.16, "HbR": 1841.05},
}


@dataclass
class YiruidRecording:
    """One Yiruid `.nirs` file, read in full."""

    path: Path
    raw_intensity: np.ndarray          # (n_samples, n_measurements)
    time: np.ndarray                   # (n_samples,)
    measurement_list: np.ndarray       # (n_measurements, 4): src, det, unused, wavelength index
    wavelengths_nm: list[float]
    source_positions: np.ndarray
    detector_positions: np.ndarray
    spatial_unit: str
    marker_samples: np.ndarray = field(default_factory=lambda: np.array([], dtype=int))

    @property
    def sfreq_hz(self) -> float:
        diffs = np.diff(self.time)
        diffs = diffs[np.isfinite(diffs) & (diffs > 0)]
        return float(1.0 / np.median(diffs)) if diffs.size else float("nan")

    @property
    def duration_sec(self) -> float:
        return float(self.time[-1] - self.time[0]) if self.time.size else float("nan")

    @property
    def marker_onsets_sec(self) -> list[float]:
        return [float(self.time[i]) for i in self.marker_samples if 0 <= i < self.time.size]

    @property
    def n_channels(self) -> int:
        """Source-detector pairs, i.e. measurements divided by wavelengths."""
        return int(self.measurement_list.shape[0] // max(1, len(self.wavelengths_nm)))

    def channel_pairs(self) -> list[tuple[int, int]]:
        """(source, detector) for each channel, in first-wavelength order."""
        first = np.flatnonzero(self.measurement_list[:, 3] == 1)
        return [(int(self.measurement_list[i, 0]), int(self.measurement_list[i, 1])) for i in first]

    def source_detector_distances_mm(self) -> np.ndarray:
        pairs = self.channel_pairs()
        out = np.empty(len(pairs), dtype=float)
        for index, (src, det) in enumerate(pairs):
            out[index] = float(np.linalg.norm(
                self.source_positions[src - 1] - self.detector_positions[det - 1]))
        return out


def read_yiruid_nirs(path: str | Path) -> YiruidRecording:
    """Read a Yiruid `.nirs` file including its SD structure."""
    from scipy.io import loadmat

    path = Path(path)
    mat = loadmat(path)
    raw = np.asarray(mat["d"], dtype=float)
    time = np.asarray(mat["t"], dtype=float).reshape(-1)
    ml = np.asarray(mat.get("ml", mat.get("SD")), dtype=float)

    sd = mat["SD"][0, 0]
    lambdas = [float(x) for x in np.ravel(sd["Lambda"])]
    src_pos = np.asarray(sd["SrcPos"], dtype=float)
    det_pos = np.asarray(sd["DetPos"], dtype=float)
    meas = np.asarray(sd["MeasList"], dtype=float)
    unit_raw = sd["SpatialUnit"] if "SpatialUnit" in (sd.dtype.names or ()) else np.array(["mm"])
    unit = str(np.ravel(unit_raw)[0]) if np.size(unit_raw) else "mm"

    stim = mat.get("s")
    if stim is not None and np.size(stim):
        markers = np.flatnonzero(np.asarray(stim).reshape(-1) != 0).astype(int)
    else:
        markers = np.array([], dtype=int)

    return YiruidRecording(
        path=path, raw_intensity=raw, time=time, measurement_list=meas,
        wavelengths_nm=lambdas, source_positions=src_pos, detector_positions=det_pos,
        spatial_unit=unit, marker_samples=markers,
    )


def differential_pathlength_factor(wavelength_nm: float, age_years: float) -> float:
    """Age- and wavelength-dependent DPF (Scholkmann & Wolf, 2013)."""
    age = float(np.clip(age_years if np.isfinite(age_years) else 13.0, 1.0, 50.0))
    lam = float(wavelength_nm)
    return (223.3
            + 0.05624 * age ** 0.8493
            - 5.723e-7 * lam ** 3
            + 0.001245 * lam ** 2
            - 0.9025 * lam)


def optical_density(raw_intensity: np.ndarray, baseline_samples: int = 100) -> np.ndarray:
    """Convert raw intensity to optical density relative to a baseline mean."""
    intensity = np.maximum(np.asarray(raw_intensity, dtype=float), 1e-9)
    n = max(1, min(int(baseline_samples), intensity.shape[0]))
    baseline = np.nanmean(intensity[:n], axis=0)
    baseline = np.where(np.isfinite(baseline) & (baseline > 0), baseline, np.nanmedian(intensity, axis=0))
    return -np.log(intensity / np.maximum(baseline, 1e-9))


def modified_beer_lambert(od: np.ndarray, measurement_list: np.ndarray,
                          wavelengths_nm: list[float], distances_mm: np.ndarray,
                          age_years: float) -> tuple[np.ndarray, np.ndarray]:
    """Convert optical density to HbO and HbR concentrations.

    Returns two arrays of shape (n_samples, n_channels) in micromolar. Requires
    exactly two wavelengths, which every recording in this dataset has.
    """
    if len(wavelengths_nm) != 2:
        raise ValueError(f"MBLL needs exactly two wavelengths, got {wavelengths_nm}")
    w1, w2 = (int(round(w)) for w in wavelengths_nm)
    for wavelength in (w1, w2):
        if wavelength not in EXTINCTION:
            raise ValueError(f"No extinction coefficients tabulated for {wavelength} nm")

    ext = np.array([
        [EXTINCTION[w1]["HbO"], EXTINCTION[w1]["HbR"]],
        [EXTINCTION[w2]["HbO"], EXTINCTION[w2]["HbR"]],
    ], dtype=float)
    inverse = np.linalg.pinv(ext)

    idx1 = np.flatnonzero(measurement_list[:, 3] == 1)
    idx2 = np.flatnonzero(measurement_list[:, 3] == 2)
    n_channels = min(idx1.size, idx2.size, distances_mm.size)

    dpf = np.array([differential_pathlength_factor(w1, age_years),
                    differential_pathlength_factor(w2, age_years)], dtype=float)
    # Path length in cm, because the extinction table is per cm.
    path_cm = (distances_mm[:n_channels] / 10.0)[None, :] * dpf[:, None]

    attenuation = np.stack([od[:, idx1[:n_channels]], od[:, idx2[:n_channels]]], axis=0)
    normalised = attenuation / np.maximum(path_cm[:, None, :], 1e-9)
    hb = np.einsum("ij,jsc->isc", inverse, normalised)
    # moles/liter -> micromolar
    return hb[0] * 1e6, hb[1] * 1e6


def read_bikom_csv(path: str | Path) -> dict[str, Any]:
    """Read one Bikom vendor CSV, keeping the Mark labels intact.

    Goal 2.7 collapsed the Mark column to a 0/1 indicator, which discarded the
    ST/A0/A1/B0/B1/ED labels that encode block on and off.
    """
    path = Path(path)
    lines = path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
    header_index = next((i for i, line in enumerate(lines) if line.startswith("Probe1(")), None)
    if header_index is None:
        raise ValueError(f"No Probe1 data header found in {path}")

    # Some exports pad every line with trailing commas, so "0.1" arrives as
    # "0.1,,,,,,,...". Drop trailing empty fields before joining, while keeping
    # genuinely comma-separated values such as "695,830".
    meta: dict[str, str] = {}
    for line in lines[:header_index]:
        parts = line.rstrip().split(",")
        if len(parts) >= 2 and parts[0]:
            fields = parts[1:]
            while fields and not fields[-1].strip():
                fields.pop()
            meta[parts[0].strip()] = ",".join(f.strip() for f in fields)

    header = [h.strip() for h in lines[header_index].split(",")]
    rows = [line.rstrip("\n").split(",") for line in lines[header_index + 1:] if line.strip()]
    channel_idx = [i for i, h in enumerate(header) if h.startswith("CH")]

    values = np.full((len(rows), len(channel_idx)), np.nan, dtype=float)
    for r, row in enumerate(rows):
        for c, i in enumerate(channel_idx):
            if i < len(row):
                try:
                    values[r, c] = float(row[i])
                except ValueError:
                    pass

    def column(name: str) -> list[str]:
        if name not in header:
            return []
        i = header.index(name)
        return [row[i].strip() if i < len(row) else "" for row in rows]

    time_raw = column("Time")
    time = np.array([float(x) if x else np.nan for x in time_raw]) if time_raw else np.arange(len(rows), dtype=float)
    marks = [(i, m) for i, m in enumerate(column("Mark")) if m not in ("", "0")]

    try:
        period = float(meta.get("Sampling Period[s]", "") or 0.1)
    except ValueError:
        period = 0.1
    return {
        "path": str(path), "meta": meta, "values": values,
        "channel_names": [header[i] for i in channel_idx],
        "time": time, "sampling_period_sec": period,
        "sfreq_hz": 1.0 / period if period else float("nan"),
        "marks": [{"sample": i, "label": m, "onset_sec": i * period} for i, m in marks],
        "mark_labels": [m for _, m in marks],
        "duration_sec": len(rows) * period,
    }
