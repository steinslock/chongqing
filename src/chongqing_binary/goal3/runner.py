"""Goal 3 orchestration.

One job is (cv_protocol, configuration, seed). It runs the five fixed outer
folds; inside each, three inner models produce honest inner-OOF scores and their
mean produces the outer-validation score. The tabular comparators are
cross-fitted through the *same* inner splits so every score in a comparison is
built from identical subjects.

Output is the project's canonical long OOF format, so `goal2_7.runner`'s pooled
metrics, bootstrap intervals and paired increment tests apply unchanged and the
numbers are directly comparable with Goal 2.8.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import pandas as pd

from .config import ensure_output, load_goal_config, project_path
from .data import load_trial_store
from .models import ModelSpec
from .protocol import (
    DEMO_CATEGORICAL,
    DEMO_NUMERIC,
    CrossFitResult,
    InnerSplit,
    OuterFold,
    build_inner_splits,
    crossfit_tabular,
    load_cohort,
    outer_folds,
    select_threshold,
    stable_seed,
    stack,
)
from .train import (TrainConfig, build_difference_waves, candidate_devices, embed, predict,
                    train_with_device_fallback)

COHORT_NAME = "eeg_oddball_goal3"
TABULAR_CANDIDATES = ("logistic_regression", "random_forest", "hist_gradient_boosting")


@dataclass(frozen=True)
class Configuration:
    """One declared model configuration. Its `arm` is fixed before any run."""

    encoder: str
    representation: str
    pooling: str = "mean_std"
    normalisation: str = "none"
    arm: str = "exploratory"     # confirmatory | exploratory | ablation | control

    @property
    def config_id(self) -> str:
        return f"{self.encoder}__{self.representation}__{self.pooling}__{self.normalisation}"

    @property
    def spec(self) -> ModelSpec:
        return ModelSpec(encoder=self.encoder, representation=self.representation, pooling=self.pooling)


def declared_configurations() -> list[Configuration]:
    """The closed set from `reports/goal3_method_design.md`, sections 12 and 13."""
    out = [Configuration("eegnet", "condition_aware", arm="confirmatory")]
    for encoder in ("inceptiontime", "conformer"):
        for representation in ("target_only", "standard_only", "condition_aware", "difference_wave"):
            out.append(Configuration(encoder, representation))
    for representation in ("target_only", "standard_only", "difference_wave"):
        out.append(Configuration("eegnet", representation))
    out.append(Configuration("eegnet", "condition_aware", pooling="attention"))
    out.append(Configuration("eegnet", "condition_aware", normalisation="robust_z", arm="ablation"))
    return out


# --------------------------------------------------------------------------- #
# Cross-fitted tabular comparators, shared across configurations
# --------------------------------------------------------------------------- #
def tabular_scores(config: dict[str, Any], cohort: pd.DataFrame, protocol: str,
                   seed: int, n_jobs: int = 4) -> dict[str, Any]:
    """Cross-fit demographics and the Goal 2.8 traditional block once per (protocol, seed).

    Both pass through the same stacking as the deep score, so Q2 compares two
    scalars rather than one scalar against a 321-column block. This project has
    measured that the asymmetry would otherwise decide the comparison on
    dimensionality.
    """
    labels = dict(zip(cohort["L_id"], cohort["label"]))
    signal_columns = [c for c in cohort.columns if c.startswith("signal_")]
    folds = outer_folds(config, protocol, cohort)
    payload: dict[str, Any] = {"protocol": protocol, "seed": seed, "folds": {}}
    for fold in folds:
        inner = build_inner_splits(
            fold.train_ids, labels, int(config["protocol"]["inner_cv_folds"]),
            float(config["protocol"]["stopping_fraction"]),
            stable_seed(seed, protocol, str(fold.index)),
        )
        demo = crossfit_tabular(cohort, DEMO_NUMERIC, DEMO_CATEGORICAL, fold, inner,
                                TABULAR_CANDIDATES, stable_seed(seed, "demo", protocol, str(fold.index)), n_jobs)
        trad = crossfit_tabular(cohort, signal_columns, [], fold, inner,
                                TABULAR_CANDIDATES, stable_seed(seed, "trad", protocol, str(fold.index)), n_jobs)
        payload["folds"][str(fold.index)] = {
            "demo_inner": demo.inner_oof.to_dict(), "demo_outer": demo.outer_scores.to_dict(),
            "demo_model": demo.chosen_model, "demo_selection": demo.selection_scores,
            "trad_inner": trad.inner_oof.to_dict(), "trad_outer": trad.outer_scores.to_dict(),
            "trad_model": trad.chosen_model, "trad_selection": trad.selection_scores,
        }
    return payload


def tabular_path(config: dict[str, Any], protocol: str, seed: int) -> Path:
    return project_path(config["paths"]["artifacts_dir"]) / "crossfit" / f"tabular_{protocol}_seed{seed}.json"


# --------------------------------------------------------------------------- #
# One deep job
# --------------------------------------------------------------------------- #
def _rows(base: dict[str, Any], feature_set: str, scores: pd.Series, labels: dict[str, int],
          fold_index: int, threshold: float) -> list[dict[str, Any]]:
    return [
        {**base, "feature_set": feature_set, "outer_fold": fold_index, "L_id": l_id,
         "label": int(labels[l_id]), "probability": float(value),
         "fold_specific_threshold": float(threshold)}
        for l_id, value in scores.items()
    ]


def run_deep_job(config: dict[str, Any], configuration: Configuration, protocol: str, seed: int,
                 label_column: str = "label", n_jobs: int = 4,
                 devices: Sequence[str] | None = None,
                 dump_embeddings: bool = False, cohort: pd.DataFrame | None = None,
                 use_tabular: bool = True, min_free_mb: int | None = None) -> dict[str, Any]:
    """Five outer folds for one configuration and seed. Returns OOF rows and diagnostics."""
    cohort = load_cohort(config) if cohort is None else cohort
    labels = dict(zip(cohort["L_id"], cohort[label_column].astype(int)))
    store = load_trial_store(project_path(config["paths"]["trial_cache_dir"]), config["run"]["task"],
                              exclude_channels=config["deep"]["input_channels_excluded"])
    train_cfg = TrainConfig(**config["deep"]["train"], normalisation=configuration.normalisation)
    waves = (build_difference_waves(store, cohort["L_id"].tolist())
             if configuration.representation == "difference_wave" else None)

    # A control label such as sex must not be stacked against demographics,
    # which contains sex. Controls run the EEG score alone.
    free_mb = int(min_free_mb if min_free_mb is not None else config["deep"]["min_free_mb"])
    tab_path = tabular_path(config, protocol, seed)
    tabular = json.loads(tab_path.read_text()) if use_tabular and tab_path.exists() else None

    predictions: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []
    embeddings: list[pd.DataFrame] = []
    base = {
        "cv_protocol": protocol, "cohort_name": COHORT_NAME, "modality": "eeg", "device": "",
        "task": config["run"]["task"], "model": configuration.config_id, "seed": seed,
    }

    for fold in outer_folds(config, protocol, cohort):
        inner = build_inner_splits(
            fold.train_ids, labels, int(config["protocol"]["inner_cv_folds"]),
            float(config["protocol"]["stopping_fraction"]),
            stable_seed(seed, protocol, str(fold.index)),
        )
        eeg_inner = pd.Series(index=list(fold.train_ids), dtype=float)
        eeg_outer = np.zeros(len(fold.val_ids), dtype=float)
        for split in inner:
            # Queried per training, not once per job: the host's GPUs are shared
            # and a job that started while they were full would otherwise stay
            # on CPU for its whole 15-training run.
            trained = train_with_device_fallback(
                devices or candidate_devices(min_free_mb=free_mb),
                store, configuration.spec, train_cfg, labels,
                split.fit_ids, split.stopping_ids,
                seed=stable_seed(seed, configuration.config_id, protocol, str(fold.index), str(split.index)),
                difference_waves=waves,
            )
            eeg_inner.loc[list(split.val_ids)] = predict(
                trained, store, split.val_ids,
                seed=stable_seed(seed, "innerval", configuration.config_id, str(fold.index), str(split.index)))
            eeg_outer += predict(
                trained, store, fold.val_ids,
                seed=stable_seed(seed, "outerval", configuration.config_id, str(fold.index), str(split.index)))
            diagnostics.append({
                **base, "outer_fold": fold.index, "inner_fold": split.index,
                "best_epoch": trained.best_epoch, "stopping_auroc": trained.best_score,
                # Not `device`: that column names the acquisition device across
                # this project and is empty for EEG.
                "compute_device": trained.device, "epochs_run": len(trained.history),
                "n_fit": len(split.fit_ids), "n_stopping": len(split.stopping_ids),
                "n_inner_val": len(split.val_ids),
            })
            if dump_embeddings and split.index == 0:
                # One inner model per outer fold is enough for the group probe:
                # the question is whether site is encoded at all, not how
                # precisely the bagged score encodes it.
                matrix = embed(trained, store, fold.val_ids,
                               seed=stable_seed(seed, "embed", configuration.config_id, str(fold.index)))
                frame = pd.DataFrame(matrix, columns=[f"emb_{i}" for i in range(matrix.shape[1])])
                frame.insert(0, "outer_fold", fold.index)
                frame.insert(0, "L_id", list(fold.val_ids))
                embeddings.append(frame)
        eeg_outer_scores = pd.Series(eeg_outer / len(inner), index=list(fold.val_ids))

        y_train = pd.Series({l: labels[l] for l in fold.train_ids})
        eeg_threshold = select_threshold(y_train.loc[eeg_inner.index].to_numpy(), eeg_inner.to_numpy())
        predictions += _rows(base, "eeg_deep", eeg_outer_scores, labels, fold.index, eeg_threshold)

        if tabular is None:
            continue
        block = tabular["folds"][str(fold.index)]
        demo_inner = pd.Series(block["demo_inner"]).loc[list(fold.train_ids)]
        demo_outer = pd.Series(block["demo_outer"]).loc[list(fold.val_ids)]
        trad_inner = pd.Series(block["trad_inner"]).loc[list(fold.train_ids)]
        trad_outer = pd.Series(block["trad_outer"]).loc[list(fold.val_ids)]

        for name, inner_scores, outer_scores in [
            ("demographics", demo_inner, demo_outer),
            ("eeg_traditional", trad_inner, trad_outer),
        ]:
            threshold = select_threshold(y_train.loc[inner_scores.index].to_numpy(), inner_scores.to_numpy())
            predictions += _rows(base, name, outer_scores, labels, fold.index, threshold)

        for name, component_inner, component_outer in [
            ("demographics_eeg_deep", eeg_inner, eeg_outer_scores),
            ("demographics_eeg_traditional", trad_inner, trad_outer),
        ]:
            result = stack(
                {"demo": demo_inner, "other": component_inner},
                {"demo": demo_outer, "other": component_outer},
                y_train, seed=stable_seed(seed, "meta", name, protocol, str(fold.index)),
            )
            threshold = select_threshold(y_train.loc[result.inner_oof.index].to_numpy(),
                                         result.inner_oof.to_numpy())
            predictions += _rows(base, name, result.outer_scores, labels, fold.index, threshold)
            diagnostics.append({
                **base, "outer_fold": fold.index, "inner_fold": -1,
                "meta_feature_set": name, **{f"meta_coef_{k}": v for k, v in result.coefficients.items()},
                "demo_model": block["demo_model"], "trad_model": block["trad_model"],
            })

    return {
        "predictions": pd.DataFrame(predictions),
        "diagnostics": pd.DataFrame(diagnostics),
        "configuration": asdict(configuration),
        "protocol": protocol,
        "seed": seed,
        "label_column": label_column,
        "embeddings": pd.concat(embeddings, ignore_index=True) if embeddings else pd.DataFrame(),
    }


def job_output_path(config: dict[str, Any], configuration: Configuration, protocol: str,
                    seed: int, label_column: str) -> Path:
    suffix = "" if label_column == "label" else f"__{label_column}"
    return (project_path(config["paths"]["results_dir"]) / "jobs"
            / f"{configuration.config_id}__{protocol}__seed{seed}{suffix}.csv")


def write_job(config: dict[str, Any], result: dict[str, Any], path: Path) -> None:
    ensure_output(path, config)
    result["predictions"].to_csv(path, index=False)
    result["diagnostics"].to_csv(path.with_suffix(".diagnostics.csv"), index=False)
    if not result["embeddings"].empty:
        result["embeddings"].to_csv(path.with_suffix(".embeddings.csv"), index=False)
