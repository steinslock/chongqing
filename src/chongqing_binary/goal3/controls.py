"""Goal 3 positive controls and shortcut probes.

Section 10 of the method design: a null on the disease label is only informative
if the same pipeline can be shown to learn something from these trials.
Otherwise "EEG carries no disease information" and "this pipeline learns
nothing" are the same observation. PC1 is a hard gate; PC2 and PC3 calibrate how
much subject-level information the aggregation can extract at all.

Section 11: the acquisition-group probe asks whether the learned representation
encodes the recording site, which is a shortcut risk whatever it does for the
label.
"""

from __future__ import annotations

from typing import Any, Sequence

import numpy as np
import pandas as pd
import torch
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from torch import nn

from .config import load_goal_config, project_path
from .data import STANDARD, TARGET, TrialStore, load_trial_store, normalise_batch
from .models import TrialModel
from .protocol import build_inner_splits, load_cohort, outer_folds, stable_seed
from .train import candidate_devices, _is_device_failure


# --------------------------------------------------------------------------- #
# PC1: target versus standard, at the trial level
# --------------------------------------------------------------------------- #
def _trial_table(store: TrialStore, subjects: Sequence[str]) -> tuple[np.ndarray, np.ndarray]:
    """Row indices and condition labels, sorted by row.

    Sorted, because a memmap read in ascending order is far cheaper than a
    random one, and because keeping rows sorted lets a batch be selected by
    sorted index without any relabelling bookkeeping.
    """
    rows, labels = [], []
    for l_id in subjects:
        for condition, value in ((TARGET, 1), (STANDARD, 0)):
            picks = store.rows[l_id][condition]
            rows.append(picks)
            labels.append(np.full(len(picks), value, dtype=np.int64))
    row_array = np.concatenate(rows)
    label_array = np.concatenate(labels)
    order = np.argsort(row_array, kind="stable")
    return row_array[order], label_array[order]


def _balanced_epoch_indices(y: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """One epoch sees every target trial and an equal number of standards.

    The paradigm presents standards about five times as often, and an unbalanced
    epoch would let the model score well by always answering "standard".
    """
    positive = np.flatnonzero(y == 1)
    negative = np.flatnonzero(y == 0)
    drawn = rng.choice(negative, size=min(len(positive), len(negative)), replace=False)
    order = np.concatenate([positive, drawn])
    rng.shuffle(order)
    return order


def _trial_scores(model: nn.Module, store: TrialStore, rows: np.ndarray, device: str,
                  chunk: int = 1024) -> np.ndarray:
    model.eval()
    out = []
    with torch.no_grad():
        for start in range(0, len(rows), chunk):
            picks = rows[start:start + chunk]
            data = normalise_batch({TARGET: store.take(picks)[None]}, "none")[TARGET][0]
            x = torch.from_numpy(np.ascontiguousarray(data)).to(device)
            out.append(torch.sigmoid(model(x)).float().cpu().numpy())
    return np.concatenate(out)


def run_condition_decoding(config: dict[str, Any], encoder: str = "eegnet", seed: int = 0,
                           max_epochs: int = 12, batch_size: int = 256,
                           devices: Sequence[str] | None = None) -> pd.DataFrame:
    """PC1. Trained and tested on disjoint subjects, over the fixed outer folds.

    This is the hard gate. The target-minus-standard effect is d = 1.08 at Pz
    alone, so a multivariate trial classifier that cannot find it means the
    pipeline is broken and no label result may be reported.
    """
    cohort = load_cohort(config)
    store = load_trial_store(project_path(config["paths"]["trial_cache_dir"]), config["run"]["task"],
                              exclude_channels=config["deep"]["input_channels_excluded"])
    labels = dict(zip(cohort["L_id"], cohort["label"]))
    rows: list[dict[str, Any]] = []

    for protocol in config["protocol"]["cv_protocols"]:
        for fold in outer_folds(config, protocol, cohort):
            inner = build_inner_splits(fold.train_ids, labels, 3,
                                       float(config["protocol"]["stopping_fraction"]),
                                       stable_seed(seed, protocol, str(fold.index)))[0]
            fit_rows, fit_y = _trial_table(store, inner.fit_ids)
            stop_rows, stop_y = _trial_table(store, inner.stopping_ids)
            val_rows, val_y = _trial_table(store, fold.val_ids)

            device, model, optimiser = None, None, None
            for candidate in (devices or candidate_devices()):
                try:
                    torch.manual_seed(stable_seed(seed, encoder, protocol, str(fold.index)))
                    model = TrialModel(encoder, store.n_channels, store.n_times).to(candidate)
                    optimiser = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
                    device = candidate
                    break
                except (RuntimeError, torch.cuda.OutOfMemoryError) as exc:  # noqa: PERF203
                    if not _is_device_failure(exc):
                        raise
                    torch.cuda.empty_cache()
            assert device is not None and model is not None and optimiser is not None
            criterion = nn.BCEWithLogitsLoss()
            rng = np.random.default_rng(stable_seed(seed, "pc1", protocol, str(fold.index)))

            best, best_state = -np.inf, None
            for epoch in range(max_epochs):
                model.train()
                order = _balanced_epoch_indices(fit_y, rng)
                for start in range(0, len(order), batch_size):
                    picks = np.sort(order[start:start + batch_size])
                    data = normalise_batch({TARGET: store.take(fit_rows[picks])[None]}, "none")[TARGET][0]
                    x = torch.from_numpy(np.ascontiguousarray(data)).to(device)
                    y_batch = torch.from_numpy(fit_y[picks].astype(np.float32)).to(device)
                    optimiser.zero_grad(set_to_none=True)
                    criterion(model(x), y_batch).backward()
                    optimiser.step()
                value = float(roc_auc_score(stop_y, _trial_scores(model, store, stop_rows, device)))
                print(f"[pc1] {protocol} fold {fold.index} epoch {epoch}: stopping AUROC {value:.4f}",
                      flush=True)
                if value > best:
                    best = value
                    best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
            if best_state is not None:
                model.load_state_dict(best_state)
            row = {
                "control": "pc1_target_vs_standard", "encoder": encoder, "cv_protocol": protocol,
                "outer_fold": fold.index, "n_train_subjects": len(inner.fit_ids),
                "n_val_subjects": len(fold.val_ids), "n_val_trials": int(len(val_rows)),
                "stopping_auroc": best, "seed": seed, "compute_device": device,
                "auroc": float(roc_auc_score(val_y, _trial_scores(model, store, val_rows, device))),
            }
            rows.append(row)
            print(f"[pc1] {protocol} fold {fold.index}: val AUROC {row['auroc']:.4f} "
                  f"(stopping {best:.4f}, {row['n_val_trials']} trials, {device})", flush=True)
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# Shortcut probe: does the representation encode the acquisition site?
# --------------------------------------------------------------------------- #
def run_group_probe(config: dict[str, Any], embeddings: pd.DataFrame, cohort: pd.DataFrame,
                    seed: int = 0, min_group_size: int = 30) -> pd.DataFrame:
    """Decode the acquisition group from out-of-fold EEG embeddings.

    The embeddings are already out of fold, so a cross-validated classifier on
    top of them measures how much site information the representation carries.
    """
    # An interrupted `write_job` can leave a short embeddings file behind: the
    # predictions are written first, so a kill between the two writes truncates
    # only this one. A partial file would silently change the probe's cohort.
    expected = int(cohort["L_id"].nunique())
    if int(embeddings["L_id"].nunique()) != expected:
        raise ValueError(
            f"incomplete embeddings: {embeddings['L_id'].nunique()} subjects, expected {expected}")

    groups = cohort[["L_id", "A_id"]].copy()
    groups["group"] = groups["A_id"].astype(str).str[:2]
    counts = groups["group"].value_counts()
    keep = set(counts[counts >= min_group_size].index)
    merged = embeddings.merge(groups[groups["group"].isin(keep)], on="L_id", how="inner")
    if merged.empty:
        return pd.DataFrame()
    feature_cols = [c for c in merged.columns if c.startswith("emb_")]
    x = merged[feature_cols].to_numpy(dtype=float)
    y = merged["group"].to_numpy()

    model = Pipeline([("scale", StandardScaler()),
                      ("model", LogisticRegression(max_iter=2000, class_weight="balanced",
                                                   random_state=seed))])
    folds = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)
    predicted = np.empty(len(y), dtype=object)
    for train_idx, test_idx in folds.split(x, y):
        model.fit(x[train_idx], y[train_idx])
        predicted[test_idx] = model.predict(x[test_idx])
    chance = float(pd.Series(y).value_counts(normalize=True).max())
    return pd.DataFrame([{
        "probe": "acquisition_group_decoding",
        "n_subjects": len(y),
        "n_groups": int(pd.Series(y).nunique()),
        "balanced_accuracy": float(balanced_accuracy_score(y, list(predicted))),
        "chance_balanced_accuracy": 1.0 / float(pd.Series(y).nunique()),
        "majority_class_share": chance,
        "embedding_dim": len(feature_cols),
    }])
