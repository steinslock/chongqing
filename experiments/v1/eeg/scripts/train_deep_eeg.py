#!/usr/bin/env python3
"""Train EEGNet or InceptionTime on cached EEG windows with subject-level CV."""

from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold
from torch import nn
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler

from _paths import V1_ROOT

SEED = 20260703
WINDOW_DIR = V1_ROOT / "eeg" / "artifacts" / "deep" / "windows"
RESULT_DIR = V1_ROOT / "eeg" / "artifacts" / "deep" / "results"
REPORT_DIR = V1_ROOT / "eeg" / "reports"


class WindowDataset(Dataset):
    def __init__(self, x: np.ndarray, labels_by_source: np.ndarray, indices: np.ndarray) -> None:
        self.x = x
        self.labels_by_source = labels_by_source.astype(np.float32)
        self.indices = indices.astype(np.int64)

    def __len__(self) -> int:
        return len(self.indices)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor, int]:
        row_idx = int(self.indices[idx])
        sample = torch.from_numpy(np.array(self.x[row_idx], dtype=np.float32, copy=True))
        label = torch.tensor(self.labels_by_source[row_idx], dtype=torch.float32)
        return sample, label, row_idx


class EEGNet(nn.Module):
    def __init__(self, n_channels: int, n_times: int, dropout: float = 0.5) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(1, 8, kernel_size=(1, 64), padding=(0, 32), bias=False),
            nn.BatchNorm2d(8),
            nn.Conv2d(8, 16, kernel_size=(n_channels, 1), groups=8, bias=False),
            nn.BatchNorm2d(16),
            nn.ELU(),
            nn.AvgPool2d(kernel_size=(1, 4)),
            nn.Dropout(dropout),
            nn.Conv2d(16, 16, kernel_size=(1, 16), padding=(0, 8), groups=16, bias=False),
            nn.Conv2d(16, 16, kernel_size=(1, 1), bias=False),
            nn.BatchNorm2d(16),
            nn.ELU(),
            nn.AvgPool2d(kernel_size=(1, 8)),
            nn.Dropout(dropout),
        )
        with torch.no_grad():
            dummy = torch.zeros(1, 1, n_channels, n_times)
            flat = self.net(dummy).flatten(1).shape[1]
        self.classifier = nn.Linear(flat, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x.unsqueeze(1)
        return self.classifier(self.net(x).flatten(1)).squeeze(1)


class InceptionBlock(nn.Module):
    def __init__(self, in_ch: int, out_ch: int) -> None:
        super().__init__()
        branch = out_ch // 4
        self.bottleneck = nn.Conv1d(in_ch, branch, kernel_size=1, bias=False)
        self.conv9 = nn.Conv1d(branch, branch, kernel_size=9, padding=4, bias=False)
        self.conv19 = nn.Conv1d(branch, branch, kernel_size=19, padding=9, bias=False)
        self.conv39 = nn.Conv1d(branch, branch, kernel_size=39, padding=19, bias=False)
        self.pool = nn.Sequential(nn.MaxPool1d(kernel_size=3, stride=1, padding=1), nn.Conv1d(in_ch, branch, kernel_size=1, bias=False))
        self.bn = nn.BatchNorm1d(branch * 4)
        self.act = nn.ReLU()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z = self.bottleneck(x)
        out = torch.cat([self.conv9(z), self.conv19(z), self.conv39(z), self.pool(x)], dim=1)
        return self.act(self.bn(out))


class InceptionTime1D(nn.Module):
    def __init__(self, n_channels: int, n_times: int, hidden: int = 64, depth: int = 4) -> None:
        super().__init__()
        blocks = []
        in_ch = n_channels
        for _ in range(depth):
            blocks.append(InceptionBlock(in_ch, hidden))
            in_ch = hidden
        self.features = nn.Sequential(*blocks)
        self.pool = nn.AdaptiveAvgPool1d(1)
        self.classifier = nn.Linear(hidden, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z = self.features(x)
        return self.classifier(self.pool(z).squeeze(-1)).squeeze(1)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", choices=["rest", "oddball", "1back"], required=True)
    parser.add_argument("--model", choices=["eegnet", "inceptiontime"], required=True)
    parser.add_argument("--windows-dir", type=Path, default=WINDOW_DIR)
    parser.add_argument("--out-dir", type=Path, default=RESULT_DIR)
    parser.add_argument("--report-dir", type=Path, default=REPORT_DIR)
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--epochs", type=int, default=80)
    parser.add_argument("--patience", type=int, default=12)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--max-windows-per-subject", type=int, default=24)
    parser.add_argument("--limit-subjects", type=int, default=None)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--num-workers", type=int, default=2)
    return parser.parse_args()


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def load_data(args: argparse.Namespace) -> tuple[np.ndarray, pd.DataFrame]:
    x_path = args.windows_dir / f"X_{args.task}.npy"
    meta_path = args.windows_dir / f"metadata_{args.task}.csv"
    if not x_path.exists() or not meta_path.exists():
        raise FileNotFoundError(f"Missing cached windows for {args.task}. Run cache_deep_windows.py first.")
    x = np.load(x_path, mmap_mode="r")
    meta = pd.read_csv(meta_path, dtype={"L_id": str})
    if len(meta) != x.shape[0]:
        raise RuntimeError(f"Metadata/window row mismatch: {len(meta)} vs {x.shape[0]}")
    if args.limit_subjects is not None:
        keep_subjects = sorted(meta["L_id"].unique())[: args.limit_subjects]
        mask = meta["L_id"].isin(keep_subjects).to_numpy()
        meta = meta.loc[mask].reset_index(drop=False).rename(columns={"index": "source_index"})
    else:
        meta = meta.reset_index(drop=False).rename(columns={"index": "source_index"})
    meta["label"] = meta["label"].astype(int)
    return x, meta


def subject_table(meta: pd.DataFrame) -> pd.DataFrame:
    subjects = meta.groupby("L_id", as_index=False)["label"].first()
    if subjects["label"].nunique() < 2:
        raise RuntimeError("Need both classes for deep CV.")
    return subjects


def build_model(model_name: str, n_channels: int, n_times: int) -> nn.Module:
    if model_name == "eegnet":
        return EEGNet(n_channels=n_channels, n_times=n_times)
    if model_name == "inceptiontime":
        return InceptionTime1D(n_channels=n_channels, n_times=n_times)
    raise ValueError(model_name)


def make_train_indices(meta: pd.DataFrame, train_lids: set[str], max_per_subject: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    selected = []
    for _, group in meta[meta["L_id"].isin(train_lids)].groupby("L_id"):
        idx = group.index.to_numpy()
        if len(idx) > max_per_subject:
            idx = rng.choice(idx, size=max_per_subject, replace=False)
        selected.extend(idx.tolist())
    return np.asarray(selected, dtype=np.int64)


def subject_scores(meta_part: pd.DataFrame, scores: np.ndarray) -> pd.DataFrame:
    df = meta_part[["L_id", "label"]].copy()
    df["y_score_window"] = scores
    grouped = df.groupby("L_id")
    return grouped.agg(
        y_true=("label", "first"),
        y_score_mean=("y_score_window", "mean"),
        y_score_median=("y_score_window", "median"),
        n_windows=("y_score_window", "size"),
    ).reset_index()


def choose_threshold(y_true: np.ndarray, y_score: np.ndarray) -> float:
    precision, recall, thresholds = precision_recall_curve(y_true, y_score)
    if len(thresholds) == 0:
        return 0.5
    f1 = 2 * precision[:-1] * recall[:-1] / np.maximum(precision[:-1] + recall[:-1], 1e-12)
    return float(thresholds[int(np.nanargmax(f1))])


def metric_row(model: str, task: str, fold: int | str, y_true: np.ndarray, y_score: np.ndarray, threshold: float) -> dict[str, object]:
    y_pred = (y_score >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    return {
        "task": task,
        "model": model,
        "fold": fold,
        "n_subjects": int(len(y_true)),
        "threshold": threshold,
        "auroc": float(roc_auc_score(y_true, y_score)),
        "auprc": float(average_precision_score(y_true, y_score)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "sensitivity": float(tp / (tp + fn)) if (tp + fn) else np.nan,
        "specificity": float(tn / (tn + fp)) if (tn + fp) else np.nan,
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "brier": float(brier_score_loss(y_true, y_score)),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
    }


def train_one_fold(
    x: np.ndarray,
    meta: pd.DataFrame,
    subjects: pd.DataFrame,
    train_subject_idx: np.ndarray,
    test_subject_idx: np.ndarray,
    fold: int,
    args: argparse.Namespace,
    device: torch.device,
) -> tuple[list[dict[str, object]], pd.DataFrame, list[dict[str, object]]]:
    train_lids = set(subjects.iloc[train_subject_idx]["L_id"])
    test_lids = set(subjects.iloc[test_subject_idx]["L_id"])
    if train_lids & test_lids:
        raise RuntimeError("Subject leakage detected.")
    train_indices = make_train_indices(meta, train_lids, args.max_windows_per_subject, args.seed + fold)
    test_meta = meta[meta["L_id"].isin(test_lids)].copy()
    test_indices = test_meta.index.to_numpy(dtype=np.int64)
    train_y = meta.loc[train_indices, "label"].to_numpy(dtype=np.float32)
    class_counts = np.bincount(train_y.astype(int), minlength=2)
    weights = np.asarray([1.0 / max(class_counts[int(y)], 1) for y in train_y], dtype=np.float64)
    sampler = WeightedRandomSampler(weights=weights, num_samples=len(weights), replacement=True)
    labels_by_source = np.full(x.shape[0], np.nan, dtype=np.float32)
    labels_by_source[meta["source_index"].to_numpy(dtype=np.int64)] = meta["label"].to_numpy(dtype=np.float32)
    train_ds = WindowDataset(x, labels_by_source, meta.loc[train_indices, "source_index"].to_numpy(dtype=np.int64))
    test_ds = WindowDataset(x, labels_by_source, test_meta["source_index"].to_numpy(dtype=np.int64))
    train_loader = DataLoader(train_ds, batch_size=args.batch_size, sampler=sampler, num_workers=args.num_workers, pin_memory=True)
    test_loader = DataLoader(test_ds, batch_size=args.batch_size, shuffle=False, num_workers=args.num_workers, pin_memory=True)
    n_channels, n_times = x.shape[1], x.shape[2]
    model = build_model(args.model, n_channels, n_times).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    pos_weight = torch.tensor([class_counts[0] / max(class_counts[1], 1)], dtype=torch.float32, device=device)
    loss_fn = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    scaler = torch.amp.GradScaler("cuda", enabled=device.type == "cuda")
    best_loss = math.inf
    best_state = None
    stale = 0
    logs = []
    for epoch in range(1, args.epochs + 1):
        model.train()
        losses = []
        for xb, yb, _ in train_loader:
            xb = xb.to(device, non_blocking=True)
            yb = yb.to(device, non_blocking=True)
            optimizer.zero_grad(set_to_none=True)
            with torch.amp.autocast(device_type=device.type, enabled=device.type == "cuda"):
                logits = model(xb)
                loss = loss_fn(logits, yb)
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
            losses.append(float(loss.detach().cpu()))
        train_loss = float(np.mean(losses)) if losses else math.inf
        logs.append({"fold": fold, "epoch": epoch, "train_loss": train_loss})
        if train_loss < best_loss - 1e-4:
            best_loss = train_loss
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
            stale = 0
        else:
            stale += 1
        if stale >= args.patience:
            break
    if best_state is not None:
        model.load_state_dict(best_state)
    ckpt_dir = args.out_dir / args.task / args.model / "checkpoints"
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    torch.save({"model_state": model.state_dict(), "args": vars(args), "fold": fold}, ckpt_dir / f"fold_{fold}.pt")
    model.eval()
    scores = []
    source_indices = []
    with torch.no_grad():
        for xb, _, idx in test_loader:
            xb = xb.to(device, non_blocking=True)
            logits = model(xb)
            scores.extend(torch.sigmoid(logits).detach().cpu().numpy().tolist())
            source_indices.extend(idx.numpy().tolist())
    pred_window = pd.DataFrame({"source_index": source_indices, "y_score_window": scores})
    test_meta_source = test_meta[["source_index", "L_id", "label", "window_in_subject", "event_code"]].merge(pred_window, on="source_index", how="inner")
    subj = subject_scores(test_meta_source, test_meta_source["y_score_window"].to_numpy())
    train_meta = meta[meta["L_id"].isin(train_lids)].copy()
    # Approximate threshold on train subjects using the model's sampled train windows.
    train_eval_ds = WindowDataset(x, labels_by_source, train_meta["source_index"].to_numpy(dtype=np.int64))
    train_loader_eval = DataLoader(train_eval_ds, batch_size=args.batch_size, shuffle=False, num_workers=args.num_workers)
    train_scores = []
    with torch.no_grad():
        for xb, _, _ in train_loader_eval:
            xb = xb.to(device)
            train_scores.extend(torch.sigmoid(model(xb)).detach().cpu().numpy().tolist())
    train_subj = subject_scores(train_meta, np.asarray(train_scores, dtype=float))
    threshold = choose_threshold(train_subj["y_true"].to_numpy(dtype=int), train_subj["y_score_mean"].to_numpy(dtype=float))
    metrics = [
        metric_row(args.model, args.task, fold, subj["y_true"].to_numpy(dtype=int), subj["y_score_mean"].to_numpy(dtype=float), threshold)
    ]
    subj["task"] = args.task
    subj["model"] = args.model
    subj["fold"] = fold
    subj["threshold"] = threshold
    return metrics, subj, logs


def write_report(path: Path, metrics: pd.DataFrame, args: argparse.Namespace) -> None:
    overall = metrics[metrics["fold"].astype(str) == "overall_oof"].copy()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        f.write(f"# Deep EEG Baseline: {args.task} {args.model}\n\n")
        f.write(f"- Task: `{args.task}`\n")
        f.write(f"- Model: `{args.model}`\n")
        f.write(f"- CV folds: {args.folds}\n")
        f.write(f"- Max epochs: {args.epochs}; patience: {args.patience}\n")
        f.write(f"- Window cap per train subject per epoch: {args.max_windows_per_subject}\n\n")
        if not overall.empty:
            f.write("## Overall OOF Metrics\n\n")
            f.write(overall.to_markdown(index=False, floatfmt=".4f"))
            f.write("\n")


def main() -> None:
    args = parse_args()
    set_seed(args.seed)
    device = torch.device(args.device if torch.cuda.is_available() and args.device.startswith("cuda") else "cpu")
    x, meta = load_data(args)
    subjects = subject_table(meta)
    if args.limit_subjects is not None:
        min_count = int(subjects["label"].value_counts().min())
        args.folds = min(args.folds, max(2, min_count))
    cv = StratifiedKFold(n_splits=args.folds, shuffle=True, random_state=args.seed)
    metrics_rows = []
    subject_predictions = []
    split_rows = []
    logs = []
    for fold, (train_idx, test_idx) in enumerate(cv.split(subjects["L_id"], subjects["label"]), start=1):
        for row in subjects.iloc[train_idx].itertuples(index=False):
            split_rows.append(
                {
                    "task": args.task,
                    "model": args.model,
                    "fold": fold,
                    "split": "train",
                    "L_id": row.L_id,
                    "label": int(row.label),
                }
            )
        for row in subjects.iloc[test_idx].itertuples(index=False):
            split_rows.append(
                {
                    "task": args.task,
                    "model": args.model,
                    "fold": fold,
                    "split": "test",
                    "L_id": row.L_id,
                    "label": int(row.label),
                }
            )
        fold_metrics, fold_subjects, fold_logs = train_one_fold(x, meta, subjects, train_idx, test_idx, fold, args, device)
        metrics_rows.extend(fold_metrics)
        subject_predictions.append(fold_subjects)
        logs.extend(fold_logs)
    pred_df = pd.concat(subject_predictions, ignore_index=True)
    thresholds = pred_df.groupby("fold")["threshold"].first().to_numpy(dtype=float)
    metrics_rows.append(
        metric_row(
            args.model,
            args.task,
            "overall_oof",
            pred_df["y_true"].to_numpy(dtype=int),
            pred_df["y_score_mean"].to_numpy(dtype=float),
            float(np.median(thresholds)),
        )
    )
    out_dir = args.out_dir / args.task / args.model
    out_dir.mkdir(parents=True, exist_ok=True)
    metrics = pd.DataFrame(metrics_rows)
    metrics_path = out_dir / "metrics.csv"
    pred_path = out_dir / "subject_predictions.csv"
    log_path = out_dir / "train_log.csv"
    split_path = out_dir / "cv_splits.csv"
    report_path = args.report_dir / f"eeg_deep_{args.task}_{args.model}_report.md"
    metrics.to_csv(metrics_path, index=False)
    pred_df.to_csv(pred_path, index=False)
    pd.DataFrame(logs).to_csv(log_path, index=False)
    pd.DataFrame(split_rows).to_csv(split_path, index=False)
    write_report(report_path, metrics, args)
    print(
        json.dumps(
            {
                "task": args.task,
                "model": args.model,
                "device": str(device),
                "subjects": len(subjects),
                "windows": len(meta),
                "metrics": str(metrics_path),
                "splits": str(split_path),
                "report": str(report_path),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
