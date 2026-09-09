"""Areas of interest on the free-viewing face stimuli.

The regions depend only on the stimulus images, never on a subject, so they are
computed once and cached. That also means they cannot leak: the same regions
apply to every subject in every fold.

The eye-versus-mouth contrast is the one the depression face-viewing literature
reports, most recently with 68-point landmarks. YuNet supplies five points,
which is enough to place both bands once they are scaled by the inter-ocular
distance.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import cv2
import numpy as np

from .spec import EyeParadigmSpec
from .stimuli import FaceStimulusBox, face_stimulus_boxes

# Column layout of a YuNet detection row.
_BOX = slice(0, 4)
_RIGHT_EYE = slice(4, 6)
_LEFT_EYE = slice(6, 8)
_NOSE = slice(8, 10)
_RIGHT_MOUTH = slice(10, 12)
_LEFT_MOUTH = slice(12, 14)
_SCORE = 14

REGION_ORDER = ("eyes", "mouth", "face_other", "off_face")


@dataclass(frozen=True)
class Rect:
    """A normalised screen rectangle."""

    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def area(self) -> float:
        return max(0.0, self.x1 - self.x0) * max(0.0, self.y1 - self.y0)

    def contains(self, x: np.ndarray, y: np.ndarray) -> np.ndarray:
        return (x >= self.x0) & (x <= self.x1) & (y >= self.y0) & (y <= self.y1)

    def overlaps(self, other: "Rect") -> bool:
        return not (self.x1 <= other.x0 or other.x1 <= self.x0 or self.y1 <= other.y0 or other.y1 <= self.y0)

    def inside(self, other: "Rect", tolerance: float = 1e-9) -> bool:
        return (
            self.x0 >= other.x0 - tolerance
            and self.y0 >= other.y0 - tolerance
            and self.x1 <= other.x1 + tolerance
            and self.y1 <= other.y1 + tolerance
        )


@dataclass(frozen=True)
class StimulusAoi:
    """Every region of one free-viewing stimulus, in normalised coordinates."""

    media: str
    valence: str
    sex: str
    order: int
    face: Rect
    eyes: Rect
    mouth: Rect
    detector: str
    detector_score: float
    interocular_distance: float

    def regions(self) -> dict[str, Rect]:
        return {"eyes": self.eyes, "mouth": self.mouth, "face_other": self.face}

    def assign(self, x: np.ndarray, y: np.ndarray) -> dict[str, np.ndarray]:
        """Assign each gaze sample to exactly one region, first match wins."""

        remaining = np.isfinite(x) & np.isfinite(y)
        out: dict[str, np.ndarray] = {}
        for name in ("eyes", "mouth", "face_other"):
            hit = self.regions()[name].contains(x, y) & remaining
            out[name] = hit
            remaining = remaining & ~hit
        out["off_face"] = remaining
        return out

    def shares(self, x: np.ndarray, y: np.ndarray) -> dict[str, float]:
        """Fraction of usable samples in each region; the four sum to one."""

        usable = int((np.isfinite(x) & np.isfinite(y)).sum())
        if usable == 0:
            return {name: float("nan") for name in REGION_ORDER}
        assigned = self.assign(x, y)
        return {name: float(assigned[name].sum()) / usable for name in REGION_ORDER}

    @property
    def area_shares(self) -> dict[str, float]:
        """The share of screen area each region covers, the chance baseline."""

        eyes = self.eyes.area
        mouth = self.mouth.area
        face_other = max(0.0, self.face.area - eyes - mouth)
        return {"eyes": eyes, "mouth": mouth, "face_other": face_other, "off_face": max(0.0, 1.0 - self.face.area)}


class AoiDetectionError(RuntimeError):
    """YuNet found no face in a stimulus image.

    Falling back to Haar is a recorded QC failure in this project, and here it
    would silently change the region geometry for one stimulus only, so the
    build fails instead.
    """


def _rect_from_landmarks(
    points: Sequence[tuple[float, float]],
    interocular: float,
    x_margin_iod: float,
    y_half_height_iod: float,
    width: int,
    height: int,
) -> Rect:
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    centre_y = float(np.mean(ys))
    return Rect(
        x0=(min(xs) - x_margin_iod * interocular) / width,
        y0=(centre_y - y_half_height_iod * interocular) / height,
        x1=(max(xs) + x_margin_iod * interocular) / width,
        y1=(centre_y + y_half_height_iod * interocular) / height,
    )


def build_stimulus_aois(spec: EyeParadigmSpec, stimulus_dir: Path, project_root: Path) -> list[StimulusAoi]:
    """Regions for all 36 free-viewing stimuli, from YuNet landmarks."""

    config = spec.task("free_viewing").raw["aoi"]
    checkpoint = project_root / str(config["detector_checkpoint"])
    if not checkpoint.exists():
        raise FileNotFoundError(f"YuNet checkpoint missing: {checkpoint}")
    detector = cv2.FaceDetectorYN_create(
        str(checkpoint), "", (320, 320), float(config["detector_score_threshold"]), 0.3, 5000
    )

    boxes = {box.media: box for box in face_stimulus_boxes(spec, stimulus_dir)}
    out: list[StimulusAoi] = []
    for stimulus in spec.free_viewing_sequence:
        path = stimulus_dir / f"{stimulus.media}.png"
        image = cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), cv2.IMREAD_COLOR)
        if image is None:
            raise FileNotFoundError(f"Unreadable stimulus image: {path}")
        height, width = image.shape[:2]
        detector.setInputSize((width, height))
        _, faces = detector.detect(image)
        if faces is None or len(faces) == 0:
            raise AoiDetectionError(f"YuNet found no face in {path.name}; Haar fallback is a QC failure here")
        face = max(faces, key=lambda row: row[2] * row[3])

        right_eye = tuple(float(value) for value in face[_RIGHT_EYE])
        left_eye = tuple(float(value) for value in face[_LEFT_EYE])
        interocular = float(np.hypot(left_eye[0] - right_eye[0], left_eye[1] - right_eye[1]))
        if interocular <= 0:
            raise AoiDetectionError(f"Degenerate interocular distance in {path.name}")

        eyes = _rect_from_landmarks(
            [right_eye, left_eye],
            interocular,
            float(config["eyes"]["x_margin_iod"]),
            float(config["eyes"]["y_half_height_iod"]),
            width,
            height,
        )
        mouth = _rect_from_landmarks(
            [tuple(float(value) for value in face[_RIGHT_MOUTH]), tuple(float(value) for value in face[_LEFT_MOUTH])],
            interocular,
            float(config["mouth"]["x_margin_iod"]),
            float(config["mouth"]["y_half_height_iod"]),
            width,
            height,
        )
        stimulus_box = boxes[stimulus.media]
        out.append(
            StimulusAoi(
                media=stimulus.media,
                valence=stimulus.valence,
                sex=stimulus.sex,
                order=stimulus.order,
                face=Rect(stimulus_box.x0, stimulus_box.y0, stimulus_box.x1, stimulus_box.y1),
                eyes=eyes,
                mouth=mouth,
                detector=str(config["detector"]),
                detector_score=float(face[_SCORE]),
                interocular_distance=interocular / width,
            )
        )
    return out


def check_aoi_geometry(aois: Sequence[StimulusAoi], config: Mapping[str, Any]) -> dict[str, Any]:
    """Geometry invariants the regions must satisfy before any feature uses them.

    Overlapping eye and mouth bands would double count gaze; a band spilling
    outside the visible face would count background as face.
    """

    overlapping = [aoi.media for aoi in aois if aoi.eyes.overlaps(aoi.mouth)]
    outside = [
        aoi.media
        for aoi in aois
        if not (aoi.eyes.inside(aoi.face, 0.02) and aoi.mouth.inside(aoi.face, 0.02))
    ]
    return {
        "n": len(aois),
        "disjoint": not overlapping,
        "overlapping_examples": overlapping[:10],
        "inside_face": not outside,
        "outside_examples": outside[:10],
        "detector": aois[0].detector if aois else "",
        "detector_score_min": min((aoi.detector_score for aoi in aois), default=float("nan")),
        "eyes_area_share_median": float(np.median([aoi.eyes.area for aoi in aois])) if aois else float("nan"),
        "mouth_area_share_median": float(np.median([aoi.mouth.area for aoi in aois])) if aois else float("nan"),
        "face_area_share_median": float(np.median([aoi.face.area for aoi in aois])) if aois else float("nan"),
        "requirements_met": (not overlapping) and (not outside),
    }


def serialise(aois: Sequence[StimulusAoi]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for aoi in aois:
        row = asdict(aoi)
        for name in ("face", "eyes", "mouth"):
            rect = row.pop(name)
            row.update({f"{name}_{key}": value for key, value in rect.items()})
        rows.append(row)
    return rows
