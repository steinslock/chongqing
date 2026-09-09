"""Goal 3 encoders and subject-level heads.

Three encoders with different inductive biases, one shared subject head. The
encoders are declared in `reports/goal3_method_design.md` and no fourth is added
after results are seen. Hyperparameters are the source defaults and are not
tuned against the disease label.
"""

from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import nn


# --------------------------------------------------------------------------- #
# Encoders: (n_trials, C, T) -> (n_trials, embedding_dim)
# --------------------------------------------------------------------------- #
class EEGNetEncoder(nn.Module):
    """EEGNet-8,2. Temporal convolution, then depthwise spatial filters.

    The depthwise spatial stage is the learned analogue of a CSP/ICA spatial
    filter, which is the inductive bias this model contributes.
    """

    def __init__(self, n_channels: int, n_times: int, f1: int = 8, depth: int = 2,
                 kernel: int = 64, dropout: float = 0.25) -> None:
        super().__init__()
        f2 = f1 * depth
        self.net = nn.Sequential(
            nn.Conv2d(1, f1, (1, kernel), padding=(0, kernel // 2), bias=False),
            nn.BatchNorm2d(f1),
            nn.Conv2d(f1, f2, (n_channels, 1), groups=f1, bias=False),
            nn.BatchNorm2d(f2),
            nn.ELU(),
            nn.AvgPool2d((1, 4)),
            nn.Dropout(dropout),
            nn.Conv2d(f2, f2, (1, 16), padding=(0, 8), groups=f2, bias=False),
            nn.Conv2d(f2, f2, (1, 1), bias=False),
            nn.BatchNorm2d(f2),
            nn.ELU(),
            nn.AvgPool2d((1, 8)),
            nn.Dropout(dropout),
        )
        with torch.no_grad():
            self.embedding_dim = int(self.net(torch.zeros(1, 1, n_channels, n_times)).flatten(1).shape[1])

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x.unsqueeze(1)).flatten(1)


class _InceptionBlock(nn.Module):
    def __init__(self, in_ch: int, out_ch: int) -> None:
        super().__init__()
        branch = out_ch // 4
        self.bottleneck = nn.Conv1d(in_ch, branch, 1, bias=False)
        self.conv9 = nn.Conv1d(branch, branch, 9, padding=4, bias=False)
        self.conv19 = nn.Conv1d(branch, branch, 19, padding=9, bias=False)
        self.conv39 = nn.Conv1d(branch, branch, 39, padding=19, bias=False)
        self.pool = nn.Sequential(nn.MaxPool1d(3, stride=1, padding=1),
                                  nn.Conv1d(in_ch, branch, 1, bias=False))
        self.bn = nn.BatchNorm1d(branch * 4)
        self.act = nn.ReLU()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z = self.bottleneck(x)
        out = torch.cat([self.conv9(z), self.conv19(z), self.conv39(z), self.pool(x)], dim=1)
        return self.act(self.bn(out))


class InceptionTimeEncoder(nn.Module):
    """InceptionTime-1D. Multi-scale temporal convolution, channels mixed at input.

    Identical in structure to the v1 model, so the historical baseline is rebuilt
    rather than approximated. Its bias is temporal shape at several scales, with
    no dedicated spatial stage.
    """

    def __init__(self, n_channels: int, n_times: int, hidden: int = 64, depth: int = 4) -> None:
        super().__init__()
        blocks: list[nn.Module] = []
        in_ch = n_channels
        for _ in range(depth):
            blocks.append(_InceptionBlock(in_ch, hidden))
            in_ch = hidden
        self.features = nn.Sequential(*blocks)
        self.pool = nn.AdaptiveAvgPool1d(1)
        self.embedding_dim = hidden

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.pool(self.features(x)).squeeze(-1)


class ConformerEncoder(nn.Module):
    """Compact EEG-Conformer: convolutional tokeniser then self-attention over time.

    Depth 3 rather than the paper's 6, because 1456 training subjects is small.
    Its bias is long-range temporal dependence, which neither other encoder has.
    """

    def __init__(self, n_channels: int, n_times: int, d_model: int = 40, depth: int = 3,
                 heads: int = 4, dropout: float = 0.25) -> None:
        super().__init__()
        self.tokeniser = nn.Sequential(
            nn.Conv2d(1, d_model, (1, 25), padding=(0, 12), bias=False),
            nn.Conv2d(d_model, d_model, (n_channels, 1), bias=False),
            nn.BatchNorm2d(d_model),
            nn.ELU(),
            nn.AvgPool2d((1, 15), stride=(1, 5)),
            nn.Dropout(dropout),
        )
        layer = nn.TransformerEncoderLayer(
            d_model=d_model, nhead=heads, dim_feedforward=d_model * 2,
            dropout=dropout, activation="gelu", batch_first=True, norm_first=True,
        )
        self.transformer = nn.TransformerEncoder(layer, num_layers=depth)
        self.norm = nn.LayerNorm(d_model)
        self.embedding_dim = d_model
        with torch.no_grad():
            self.n_tokens = int(self.tokeniser(torch.zeros(1, 1, n_channels, n_times)).shape[-1])
        self.position = nn.Parameter(torch.zeros(1, self.n_tokens, d_model))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        tokens = self.tokeniser(x.unsqueeze(1)).squeeze(2).transpose(1, 2)
        tokens = self.transformer(tokens + self.position)
        return self.norm(tokens).mean(dim=1)


ENCODERS = {
    "eegnet": EEGNetEncoder,
    "inceptiontime": InceptionTimeEncoder,
    "conformer": ConformerEncoder,
}


# --------------------------------------------------------------------------- #
# Subject-level pooling and head
# --------------------------------------------------------------------------- #
class MeanStdPooling(nn.Module):
    """The simple, stable default. Two statistics per embedding dimension."""

    multiplier = 2

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x is (n_subjects, n_trials, d). The quota guarantees n_trials > 1 for
        # every trial-level representation; the difference wave bypasses pooling.
        return torch.cat([x.mean(dim=1), x.std(dim=1)], dim=1)


class AttentionPooling(nn.Module):
    """Gated attention over trials. The one declared alternative to mean+std."""

    multiplier = 1

    def __init__(self, dim: int, hidden: int = 64) -> None:
        super().__init__()
        self.value = nn.Linear(dim, hidden)
        self.gate = nn.Linear(dim, hidden)
        self.score = nn.Linear(hidden, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        weights = self.score(torch.tanh(self.value(x)) * torch.sigmoid(self.gate(x)))
        return (torch.softmax(weights, dim=1) * x).sum(dim=1)


@dataclass(frozen=True)
class ModelSpec:
    encoder: str
    representation: str          # target_only | standard_only | condition_aware | difference_wave
    pooling: str = "mean_std"    # mean_std | attention
    dropout: float = 0.25
    head_hidden: int = 64


class SubjectModel(nn.Module):
    """Shared trial encoder, per-condition pooling, subject-level head.

    For `condition_aware` the subject vector is
    `[pool(target), pool(standard), pool(target) - pool(standard)]`, so the head
    sees the relation between a person's two responses and not only their
    general EEG appearance. Separate pooling is what makes the model
    condition-aware; a condition embedding added after a shared encoder would be
    a constant shift that the separate pooling already absorbs.
    """

    def __init__(self, spec: ModelSpec, n_channels: int, n_times: int) -> None:
        super().__init__()
        self.spec = spec
        encoder_cls = ENCODERS[spec.encoder]
        kwargs = {"dropout": spec.dropout} if spec.encoder in {"eegnet", "conformer"} else {}
        self.encoder = encoder_cls(n_channels=n_channels, n_times=n_times, **kwargs)
        dim = self.encoder.embedding_dim

        if spec.pooling == "mean_std":
            self.pool: nn.Module = MeanStdPooling()
            pooled = dim * MeanStdPooling.multiplier
        elif spec.pooling == "attention":
            self.pool = AttentionPooling(dim)
            pooled = dim
        else:
            raise ValueError(f"unknown pooling {spec.pooling!r}")

        if spec.representation == "condition_aware":
            subject_dim = pooled * 3
        elif spec.representation == "difference_wave":
            subject_dim = dim
        else:
            subject_dim = pooled

        self.head = nn.Sequential(
            nn.Linear(subject_dim, spec.head_hidden),
            nn.BatchNorm1d(spec.head_hidden),
            nn.ELU(),
            nn.Dropout(spec.dropout),
            nn.Linear(spec.head_hidden, 1),
        )
        self.subject_dim = subject_dim

    def embed(self, batch: dict[str, torch.Tensor]) -> torch.Tensor:
        """Subject-level representation. `batch` maps condition -> (S, K, C, T)."""
        if self.spec.representation == "difference_wave":
            # One subject-level image per subject, so there is nothing to pool.
            data = next(iter(batch.values()))
            return self.encoder(data.reshape(data.shape[0], data.shape[2], data.shape[3]))
        pooled: dict[str, torch.Tensor] = {}
        for condition, data in batch.items():
            n_subjects, n_trials = data.shape[0], data.shape[1]
            flat = data.reshape(n_subjects * n_trials, data.shape[2], data.shape[3])
            embedded = self.encoder(flat).reshape(n_subjects, n_trials, -1)
            pooled[condition] = self.pool(embedded)
        if self.spec.representation == "condition_aware":
            from .data import STANDARD, TARGET
            target, standard = pooled[TARGET], pooled[STANDARD]
            return torch.cat([target, standard, target - standard], dim=1)
        return next(iter(pooled.values()))

    def forward(self, batch: dict[str, torch.Tensor]) -> torch.Tensor:
        return self.head(self.embed(batch)).squeeze(1)


class TrialModel(nn.Module):
    """Trial-level classifier, used only by positive control PC1."""

    def __init__(self, encoder: str, n_channels: int, n_times: int, dropout: float = 0.25) -> None:
        super().__init__()
        encoder_cls = ENCODERS[encoder]
        kwargs = {"dropout": dropout} if encoder in {"eegnet", "conformer"} else {}
        self.encoder = encoder_cls(n_channels=n_channels, n_times=n_times, **kwargs)
        self.head = nn.Linear(self.encoder.embedding_dim, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.head(self.encoder(x)).squeeze(1)
