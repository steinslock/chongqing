"""Goal 3 training: one deep model, fitted honestly inside one inner fold.

The split structure is the point of this module. Early stopping reads the
`stopping` subset and nothing else; the `inner-val` subjects are never seen
during fitting, so the predictions this module returns for them are honest
out-of-fold scores that the cross-fitted stacking can safely consume. See
`reports/goal3_method_design.md`, section 8.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Sequence

import numpy as np
import torch
from sklearn.metrics import roc_auc_score
from torch import nn

from .data import STANDARD, TARGET, SubjectSampler, TrialStore, normalise_batch, subject_batches
from .models import ModelSpec, SubjectModel

REPRESENTATION_CONDITIONS = {
    "target_only": (TARGET,),
    "standard_only": (STANDARD,),
    "condition_aware": (TARGET, STANDARD),
    "difference_wave": (TARGET,),  # a synthetic single "trial" per subject
}


@dataclass(frozen=True)
class TrainConfig:
    """Fixed, pre-declared. Not tuned against the disease label."""

    trial_quota: int = 8
    batch_subjects: int = 16
    max_epochs: int = 80
    patience: int = 15
    learning_rate: float = 1e-3
    weight_decay: float = 1e-4
    normalisation: str = "none"
    eval_draws_stopping: int = 2
    eval_draws_final: int = 8
    min_epochs: int = 5
    # Subjects per forward pass at inference. This is the peak-memory setting,
    # not a modelling one: at 64 it pushes 64 x quota x conditions trials through
    # the encoder at once, four times the training batch, and it decided how
    # large a free GPU sliver had to be before a run could use one. Lowering it
    # changes no prediction.
    predict_chunk_subjects: int = 16


@dataclass
class TrainedModel:
    model: SubjectModel
    spec: ModelSpec
    config: TrainConfig
    device: str
    best_epoch: int
    best_score: float
    history: list[dict[str, float]] = field(default_factory=list)
    difference_waves: dict[str, np.ndarray] | None = None


def _difference_wave_batch(waves: dict[str, np.ndarray], subjects: Sequence[str]) -> dict[str, np.ndarray]:
    stacked = np.stack([waves[l_id] for l_id in subjects])[:, None]
    return {TARGET: stacked}


def _make_batch(store: TrialStore, spec: ModelSpec, sampler: SubjectSampler | None,
                waves: dict[str, np.ndarray] | None, subjects: Sequence[str],
                rng: np.random.Generator, normalisation: str,
                device: str) -> dict[str, torch.Tensor]:
    if spec.representation == "difference_wave":
        raw = _difference_wave_batch(waves or {}, subjects)
    else:
        assert sampler is not None
        raw = sampler.gather(sampler.draw(subjects, rng))
    normalised = normalise_batch(raw, normalisation)
    return {k: torch.from_numpy(np.ascontiguousarray(v)).to(device) for k, v in normalised.items()}


@torch.no_grad()
def predict(trained: TrainedModel, store: TrialStore, subjects: Sequence[str],
            seed: int, n_draws: int | None = None) -> np.ndarray:
    """Subject probabilities, averaged over repeated fixed-size trial draws.

    Averaging over draws is what makes a subject's score independent of which
    trials happened to be sampled, and it is the inference-time counterpart of
    the fixed quota used in training.
    """
    model, spec, cfg = trained.model, trained.spec, trained.config
    model.eval()
    draws = n_draws if n_draws is not None else cfg.eval_draws_final
    if spec.representation == "difference_wave":
        draws = 1
    sampler = (None if spec.representation == "difference_wave"
               else SubjectSampler(store, REPRESENTATION_CONDITIONS[spec.representation], cfg.trial_quota))
    rng = np.random.default_rng(seed)
    total = np.zeros(len(subjects), dtype=np.float64)
    for _ in range(draws):
        acc = []
        for start in range(0, len(subjects), cfg.predict_chunk_subjects):
            chunk = list(subjects[start:start + cfg.predict_chunk_subjects])
            batch = _make_batch(store, spec, sampler, trained.difference_waves, chunk,
                                rng, cfg.normalisation, trained.device)
            acc.append(torch.sigmoid(model(batch)).float().cpu().numpy())
        total += np.concatenate(acc)
    return total / draws


@torch.no_grad()
def embed(trained: TrainedModel, store: TrialStore, subjects: Sequence[str],
          seed: int, n_draws: int | None = None) -> np.ndarray:
    """Subject-level representations, averaged over draws like `predict`.

    Used by the acquisition-group probe: a representation that decodes the
    recording site is a shortcut risk regardless of what it does for the label.
    """
    model, spec, cfg = trained.model, trained.spec, trained.config
    model.eval()
    draws = 1 if spec.representation == "difference_wave" else (n_draws or cfg.eval_draws_final)
    sampler = (None if spec.representation == "difference_wave"
               else SubjectSampler(store, REPRESENTATION_CONDITIONS[spec.representation], cfg.trial_quota))
    rng = np.random.default_rng(seed)
    total: np.ndarray | None = None
    for _ in range(draws):
        acc = []
        for start in range(0, len(subjects), cfg.predict_chunk_subjects):
            chunk = list(subjects[start:start + cfg.predict_chunk_subjects])
            batch = _make_batch(store, spec, sampler, trained.difference_waves, chunk,
                                rng, cfg.normalisation, trained.device)
            acc.append(model.embed(batch).float().cpu().numpy())
        stacked = np.concatenate(acc, axis=0)
        total = stacked if total is None else total + stacked
    return total / draws


def train_subject_model(store: TrialStore, spec: ModelSpec, cfg: TrainConfig,
                        labels: dict[str, int], fit_ids: Sequence[str],
                        stopping_ids: Sequence[str], seed: int, device: str,
                        difference_waves: dict[str, np.ndarray] | None = None) -> TrainedModel:
    """Fit one model. `stopping_ids` drives early stopping and nothing else."""
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)

    model = SubjectModel(spec, store.n_channels, store.n_times).to(device)
    optimiser = torch.optim.AdamW(model.parameters(), lr=cfg.learning_rate,
                                  weight_decay=cfg.weight_decay)
    y_fit = np.array([labels[l] for l in fit_ids], dtype=np.float32)
    n_pos = float(max(y_fit.sum(), 1.0))
    pos_weight = torch.tensor([(len(y_fit) - n_pos) / n_pos], device=device)
    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)

    sampler = (None if spec.representation == "difference_wave"
               else SubjectSampler(store, REPRESENTATION_CONDITIONS[spec.representation], cfg.trial_quota))
    label_of = {l: labels[l] for l in list(fit_ids) + list(stopping_ids)}
    y_stop = np.array([label_of[l] for l in stopping_ids], dtype=int)

    best_state: dict[str, torch.Tensor] | None = None
    best_score, best_epoch, stale = -np.inf, -1, 0
    history: list[dict[str, float]] = []
    fit_list = list(fit_ids)

    for epoch in range(cfg.max_epochs):
        model.train()
        losses: list[float] = []
        for chunk in subject_batches(fit_list, cfg.batch_subjects, rng):
            batch = _make_batch(store, spec, sampler, difference_waves, chunk, rng,
                                cfg.normalisation, device)
            target = torch.tensor([float(label_of[l]) for l in chunk], device=device)
            optimiser.zero_grad(set_to_none=True)
            loss = criterion(model(batch), target)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
            optimiser.step()
            losses.append(float(loss.detach()))

        probe = TrainedModel(model, spec, cfg, device, epoch, float("nan"),
                             difference_waves=difference_waves)
        scores = predict(probe, store, stopping_ids, seed=seed + 10_000 + epoch,
                         n_draws=cfg.eval_draws_stopping)
        score = float(roc_auc_score(y_stop, scores)) if len(set(y_stop.tolist())) > 1 else float("nan")
        history.append({"epoch": epoch, "train_loss": float(np.mean(losses)), "stopping_auroc": score})

        if np.isfinite(score) and score > best_score:
            best_score, best_epoch, stale = score, epoch, 0
            best_state = copy.deepcopy(model.state_dict())
        else:
            stale += 1
            if epoch + 1 >= cfg.min_epochs and stale >= cfg.patience:
                break

    if best_state is not None:
        model.load_state_dict(best_state)
    return TrainedModel(model, spec, cfg, device, best_epoch, best_score, history, difference_waves)


def build_difference_waves(store: TrialStore, subjects: Sequence[str]) -> dict[str, np.ndarray]:
    """Subject-level `ERP_target - ERP_standard`, the representation D control."""
    return {l_id: store.difference_wave(l_id) for l_id in subjects}


def candidate_devices(min_free_mb: int = 1500, preferred: str | None = None) -> list[str]:
    """GPUs with room, emptiest first, then CPU.

    The host's eight L40S are shared with other users and their free memory
    changes between the moment it is read and the moment a tensor is allocated,
    so device choice is a list to try rather than a single answer. This affects
    wall time only, never a fit.
    """
    if preferred:
        return [preferred] if preferred == "cpu" else [preferred, "cpu"]
    if not torch.cuda.is_available():
        return ["cpu"]
    free_by_device: list[tuple[int, int]] = []
    for index in range(torch.cuda.device_count()):
        try:
            free, _ = torch.cuda.mem_get_info(index)
        except Exception:  # noqa: BLE001
            continue
        free_mb = int(free // (1024 * 1024))
        if free_mb >= min_free_mb:
            free_by_device.append((free_mb, index))
    free_by_device.sort(reverse=True)
    return [f"cuda:{index}" for _, index in free_by_device] + ["cpu"]


# A CUDA device that cannot be allocated on does not always say "out of
# memory". On this shared host, once the free memory threshold was lowered far
# enough to use other users' leftovers, the failure arrived as
# `CUBLAS_STATUS_ALLOC_FAILED when calling cublasCreate(handle)`: cuBLAS could
# not obtain its workspace. Matching only the phrase "out of memory" let those
# escape the fallback and kill six jobs.
_DEVICE_FAILURE_MARKERS = (
    "out of memory",
    "cublas_status_alloc_failed",
    "cublas_status_execution_failed",
    "cublas_status_not_initialized",
    "cudnn_status_alloc_failed",
    "cudnn_status_not_initialized",
    # cuDNN reports a failed host allocation under its own name rather than as
    # an alloc-failed status, which is how the last conformer job died.
    "host_allocation_failed",
    "allocation failed",
    "cudnn error",
    "no kernel image is available",
    "cuda error",
)

# A CUDA context that has failed once in a process usually keeps failing, so the
# process stops offering GPUs rather than retrying them on every training.
_CUDA_DISABLED = False


def _is_device_failure(exc: BaseException) -> bool:
    if isinstance(exc, torch.cuda.OutOfMemoryError):
        return True
    text = str(exc).lower()
    return any(marker in text for marker in _DEVICE_FAILURE_MARKERS)


def train_with_device_fallback(devices: Sequence[str], *args, **kwargs) -> TrainedModel:
    """Run `train_subject_model`, moving on when a GPU cannot take the model.

    A shared GPU can fill between the free-memory read and the first allocation,
    which is what happened on the first Goal 3 benchmark run, and it can also
    refuse a cuBLAS handle while reporting free memory, which is what killed six
    jobs later. Both are device failures, and both fall back rather than raise;
    anything else is a real error and propagates.
    """
    global _CUDA_DISABLED

    candidates = ["cpu"] if _CUDA_DISABLED else list(devices)
    if "cpu" not in candidates:
        candidates.append("cpu")
    last: BaseException | None = None
    for device in candidates:
        try:
            return train_subject_model(*args, device=device, **kwargs)
        except (RuntimeError, torch.cuda.OutOfMemoryError) as exc:  # noqa: PERF203
            if device == "cpu" or not _is_device_failure(exc):
                raise
            last = exc
            _CUDA_DISABLED = True
            try:
                torch.cuda.empty_cache()
            except Exception:  # noqa: BLE001
                pass
    raise RuntimeError(f"no device could fit the model; last error: {last}")
