"""Trial store and subject-balanced batching for Goal 3.

The unit of learning is the subject. A batch is a set of subjects, and each
subject contributes a fixed quota of trials per condition, drawn with
replacement where it has too few. Neither the number of trials a subject
survived artifact rejection with, nor the paradigm's 22:109 target-to-standard
ratio, therefore weights that subject in the loss.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator, Sequence

import numpy as np
import pandas as pd

TARGET = "deviant_target"
STANDARD = "standard"
CONDITIONS = (TARGET, STANDARD)


@dataclass
class TrialStore:
    """Memory-mapped single trials, indexed by subject and condition.

    `keep_channels` selects the model input channels out of the stored 32. The
    stored array always keeps all of them, because it must stay identical to the
    Goal 2.8 epochs; the selection is a modelling choice applied on read.
    """

    trials: np.memmap
    channels: list[str]
    times: np.ndarray
    rows: dict[str, dict[str, np.ndarray]]
    keep_channels: np.ndarray | None = None
    all_channels: list[str] = field(default_factory=list)

    @property
    def n_channels(self) -> int:
        return len(self.channels)

    def take(self, rows: np.ndarray) -> np.ndarray:
        """Trial data for the given rows, restricted to the model input channels."""
        block = np.asarray(self.trials[rows])
        return block if self.keep_channels is None else block[:, self.keep_channels]

    @property
    def n_times(self) -> int:
        return int(self.trials.shape[2])

    @property
    def subjects(self) -> list[str]:
        return sorted(self.rows)

    def counts(self) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {"L_id": l_id, **{c: len(self.rows[l_id].get(c, ())) for c in CONDITIONS}}
                for l_id in self.subjects
            ]
        )

    def evoked(self, l_id: str, condition: str) -> np.ndarray:
        return self.take(self.rows[l_id][condition]).mean(axis=0, dtype=np.float64)

    def difference_wave(self, l_id: str) -> np.ndarray:
        return (self.evoked(l_id, TARGET) - self.evoked(l_id, STANDARD)).astype(np.float32)


def load_trial_store(cache_dir: str | Path, task: str = "oddball",
                     exclude_channels: Sequence[str] = ()) -> TrialStore:
    """Open the trial cache, optionally dropping channels from the model input.

    Goal 2.8 excluded Fp1 and Fp2 from the artifact-rejection decision because
    blinks dominate them, so the 150 uV peak-to-peak bound that holds for every
    other channel does not hold for those two: measured over all 237,774 trials,
    every other channel stays under 144.5 uV while Fp2 reaches 118,990 uV. Goal
    2.8's own ERP features never read them. A network handed them unnormalised
    would have its first convolution and its batch statistics set by blink
    amplitude on two channels.
    """
    cache = Path(cache_dir)
    index = pd.read_csv(cache / f"{task}_trial_index.csv", dtype={"L_id": str, "code": str})
    trials = np.load(cache / f"{task}_trials.npy", mmap_mode="r")
    all_channels = [str(c) for c in np.load(cache / f"{task}_channels.npy")]
    times = np.load(cache / f"{task}_times.npy")
    excluded = {str(c) for c in exclude_channels}
    unknown = excluded - set(all_channels)
    if unknown:
        raise ValueError(f"cannot exclude channels that are not in the cache: {sorted(unknown)}")
    keep = np.array([i for i, c in enumerate(all_channels) if c not in excluded], dtype=np.int64)
    rows: dict[str, dict[str, np.ndarray]] = {}
    for (l_id, condition), block in index.groupby(["L_id", "condition"], sort=False):
        rows.setdefault(str(l_id), {})[str(condition)] = block["row"].to_numpy(dtype=np.int64)
    return TrialStore(trials=trials, channels=[all_channels[i] for i in keep], times=times,
                      rows=rows, keep_channels=(None if len(keep) == len(all_channels) else keep),
                      all_channels=all_channels)


class SubjectSampler:
    """Draws a fixed trial quota per subject per condition.

    `rng` is owned by the caller so a training run is reproducible from its seed
    alone. Sampling is with replacement only where a subject has fewer trials
    than the quota, which the paradigm makes common for targets.
    """

    def __init__(self, store: TrialStore, conditions: Sequence[str], quota: int) -> None:
        self.store = store
        self.conditions = tuple(conditions)
        self.quota = int(quota)

    def draw(self, subjects: Sequence[str], rng: np.random.Generator) -> dict[str, np.ndarray]:
        out: dict[str, np.ndarray] = {}
        for condition in self.conditions:
            picks = np.empty((len(subjects), self.quota), dtype=np.int64)
            for i, l_id in enumerate(subjects):
                available = self.store.rows[l_id][condition]
                replace = len(available) < self.quota
                picks[i] = rng.choice(available, size=self.quota, replace=replace)
            out[condition] = picks
        return out

    def gather(self, picks: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
        """Fetch trial data for one draw, shaped (n_subjects, quota, C, T)."""
        out: dict[str, np.ndarray] = {}
        for condition, rows in picks.items():
            flat = rows.reshape(-1)
            order = np.argsort(flat, kind="stable")
            fetched = np.empty((flat.size, self.store.n_channels, self.store.n_times), dtype=np.float32)
            # A memmap read is far cheaper in ascending row order than in the
            # random order the sampler produces.
            fetched[order] = self.store.take(flat[order])
            out[condition] = fetched.reshape(rows.shape[0], rows.shape[1],
                                             self.store.n_channels, self.store.n_times)
        return out


def subject_batches(subjects: Sequence[str], batch_size: int, rng: np.random.Generator,
                    shuffle: bool = True) -> Iterator[list[str]]:
    order = np.arange(len(subjects))
    if shuffle:
        rng.shuffle(order)
    for start in range(0, len(order), batch_size):
        picked = order[start:start + batch_size]
        if len(picked) < 2 and shuffle:
            continue  # a one-subject batch makes batch norm meaningless
        yield [subjects[i] for i in picked]


def to_microvolts(batch: np.ndarray) -> np.ndarray:
    """Volts to microvolts. A unit choice, fixed and label-independent.

    The raw epochs are around 1e-5 V. Batch normalisation would absorb that, but
    keeping inputs at O(10) avoids relying on it for numerical conditioning.
    """
    return batch * 1e6


def normalise_batch(batch: dict[str, np.ndarray], mode: str) -> dict[str, np.ndarray]:
    """Per-subject amplitude normalisation, the declared Goal 3 ablation.

    `none` is the primary setting: it preserves true ERP amplitude, which is what
    the Goal 2.8 hand-crafted features saw. `robust_z` removes per-subject
    per-channel scale, which is where an amplifier or impedance signature would
    live.

    Statistics are pooled **across conditions** within a subject. Normalising
    each condition separately would rescale target and standard by different
    factors and destroy the very target-minus-standard relation the
    condition-aware representation exists to model.
    """
    if mode == "none":
        return {k: to_microvolts(v) for k, v in batch.items()}
    if mode != "robust_z":
        raise ValueError(f"unknown normalisation {mode!r}")
    conditions = list(batch)
    stacked = np.concatenate([batch[c] for c in conditions], axis=1)  # (S, sum K, C, T)
    median = np.median(stacked, axis=(1, 3), keepdims=True)
    scale = np.maximum(np.median(np.abs(stacked - median), axis=(1, 3), keepdims=True) * 1.4826, 1e-12)
    return {c: ((batch[c] - median) / scale).astype(np.float32) for c in conditions}
