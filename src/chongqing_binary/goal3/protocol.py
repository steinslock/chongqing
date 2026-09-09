"""Goal 3 evaluation protocol: nested splits, cross-fitting, and stacking.

The outer splits are the project's fixed files. Everything below outer-train is
built here, and the three-level structure is deliberate: the stopping subset
makes every training decision, and inner-val makes none, so the inner-OOF scores
that train the meta model are honest. See `reports/goal3_method_design.md`,
section 8.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Sequence

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold, StratifiedShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .config import add_clean_demographics, cv_subjects, load_goal_config, project_path

DEMO_NUMERIC = ["age_clean"]
DEMO_CATEGORICAL = ["sex_clean", "grade_clean"]
THRESHOLD_GRID = [0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8]


def stable_seed(seed: int, *parts: str) -> int:
    payload = "|".join([str(seed), *parts])
    return int(hashlib.sha1(payload.encode("utf-8")).hexdigest()[:8], 16)


# --------------------------------------------------------------------------- #
# Cohort
# --------------------------------------------------------------------------- #
def load_cohort(config: dict[str, Any]) -> pd.DataFrame:
    """The Goal 2.8 Oddball cohort with demographics and traditional features.

    Membership comes from the Goal 2.8 index rather than being re-derived, so
    every Goal 3 comparison sits on exactly the subjects Goal 2.8 measured.
    """
    label_col = config["run"]["label_column"]
    split = add_clean_demographics(cv_subjects(config), config)
    index = pd.read_csv(project_path(config["paths"]["goal2_8_erp_index"]), dtype={"L_id": str})
    cohort_ids = set(index.loc[index["status"] == "ok", "L_id"].astype(str))

    signal = pd.read_csv(project_path(config["paths"]["goal2_8_signal_features"]), dtype={"L_id": str})
    signal_cols = [c for c in signal.columns if c.startswith("signal_")]
    qc = pd.read_csv(project_path(config["paths"]["goal2_8_qc_features"]), dtype={"L_id": str})
    qc_cols = [c for c in qc.columns if c.startswith("qc_") and
               pd.api.types.is_numeric_dtype(qc[c])]

    frame = split[split["L_id"].isin(cohort_ids)].copy()
    frame = frame.merge(signal[["L_id", *signal_cols]], on="L_id", how="inner")
    frame = frame.merge(qc[["L_id", *qc_cols]], on="L_id", how="left")
    frame = frame.sort_values("L_id").reset_index(drop=True)
    frame["label"] = frame[label_col].astype(int)
    assert int(frame["is_locked_test"].sum()) == 0, "pilot holdout must not appear in Goal 3"
    return frame


# --------------------------------------------------------------------------- #
# Splits
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class OuterFold:
    protocol: str
    index: int
    train_ids: tuple[str, ...]
    val_ids: tuple[str, ...]


@dataclass(frozen=True)
class InnerSplit:
    index: int
    fit_ids: tuple[str, ...]
    stopping_ids: tuple[str, ...]
    val_ids: tuple[str, ...]


def outer_folds(config: dict[str, Any], protocol: str, cohort: pd.DataFrame) -> list[OuterFold]:
    settings = config["protocol"]["cv_protocols"][protocol]
    split = pd.read_csv(project_path(settings["split_file"]), dtype={"L_id": str})
    fold_column = settings["fold_column"]
    split = split[split["split_group"].astype(str) == config["run"]["split_group"]]
    folds = split[["L_id", fold_column]].dropna()
    folds = folds[folds["L_id"].isin(set(cohort["L_id"]))]
    out: list[OuterFold] = []
    for value in sorted(folds[fold_column].unique(), key=lambda v: int(float(v))):
        mask = folds[fold_column] == value
        val = tuple(sorted(folds.loc[mask, "L_id"]))
        train = tuple(sorted(folds.loc[~mask, "L_id"]))
        assert not (set(train) & set(val)), "outer train and validation must be disjoint"
        out.append(OuterFold(protocol, int(float(value)), train, val))
    return out


def build_inner_splits(train_ids: Sequence[str], labels: dict[str, int], n_folds: int,
                       stopping_fraction: float, seed: int) -> list[InnerSplit]:
    """Three-fold inner CV, each fold carving its own stopping subset.

    `stopping_ids` receive every training decision (early stopping, model-family
    selection); `val_ids` receive none, so their predictions are honest
    out-of-fold scores. Making one set do both jobs is the leak this structure
    exists to prevent.
    """
    ids = np.asarray(sorted(train_ids))
    y = np.array([labels[i] for i in ids], dtype=int)
    outer = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=seed)
    splits: list[InnerSplit] = []
    for index, (pool_idx, val_idx) in enumerate(outer.split(ids, y)):
        pool_ids, pool_y = ids[pool_idx], y[pool_idx]
        carve = StratifiedShuffleSplit(n_splits=1, test_size=stopping_fraction,
                                       random_state=seed + index + 1)
        fit_idx, stop_idx = next(carve.split(pool_ids, pool_y))
        splits.append(InnerSplit(
            index=index,
            fit_ids=tuple(pool_ids[fit_idx]),
            stopping_ids=tuple(pool_ids[stop_idx]),
            val_ids=tuple(ids[val_idx]),
        ))
    for split in splits:
        assert not (set(split.fit_ids) & set(split.stopping_ids))
        assert not (set(split.fit_ids) & set(split.val_ids))
        assert not (set(split.stopping_ids) & set(split.val_ids))
    covered = set().union(*[set(s.val_ids) for s in splits])
    assert covered == set(ids), "every outer-train subject needs exactly one inner-OOF score"
    return splits


# --------------------------------------------------------------------------- #
# Tabular cross-fitting
# --------------------------------------------------------------------------- #
def _pipeline(model_name: str, numeric: list[str], categorical: list[str], seed: int,
              n_jobs: int = 4) -> Pipeline:
    """The project's Goal 2.7/2.8 pipeline, unchanged, so comparators match."""
    transformers = []
    if numeric:
        transformers.append(("num", Pipeline([
            ("imputer", SimpleImputer(strategy="median", keep_empty_features=True)),
            ("scaler", StandardScaler()),
        ]), numeric))
    if categorical:
        transformers.append(("cat", Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent", keep_empty_features=True)),
            ("onehot", OneHotEncoder(handle_unknown="ignore", min_frequency=5, sparse_output=False)),
        ]), categorical))
    preprocess = ColumnTransformer(transformers=transformers, sparse_threshold=0.0)
    if model_name == "logistic_regression":
        model: Any = LogisticRegression(class_weight="balanced", max_iter=2000, random_state=seed)
    elif model_name == "random_forest":
        model = RandomForestClassifier(n_estimators=120, min_samples_leaf=5,
                                       class_weight="balanced_subsample", n_jobs=n_jobs,
                                       random_state=seed)
    elif model_name == "hist_gradient_boosting":
        model = HistGradientBoostingClassifier(max_iter=80, learning_rate=0.05,
                                               max_leaf_nodes=15, l2_regularization=0.01,
                                               random_state=seed)
    else:
        raise ValueError(f"unsupported model {model_name!r}")
    return Pipeline([("preprocess", preprocess), ("model", model)])


@dataclass
class CrossFitResult:
    inner_oof: pd.Series          # index L_id, over outer-train
    outer_scores: pd.Series       # index L_id, over outer-val
    chosen_model: str
    selection_scores: dict[str, float]


def crossfit_tabular(frame: pd.DataFrame, numeric: list[str], categorical: list[str],
                     outer: OuterFold, inner: Sequence[InnerSplit], candidates: Sequence[str],
                     seed: int, n_jobs: int = 4) -> CrossFitResult:
    """Cross-fit one tabular feature block through the same inner folds as the deep model.

    Model-family selection reads the stopping subsets, exactly as the deep
    model's early stopping does, so inner-val stays untouched and the inner-OOF
    scores remain usable as stacking inputs. Every fit uses `fit_ids` only, so
    the deep and tabular scores are built from identical subjects.
    """
    indexed = frame.set_index("L_id")
    y = indexed["label"]

    selection: dict[str, float] = {}
    for name in candidates:
        scores = []
        for split in inner:
            model = _pipeline(name, numeric, categorical, stable_seed(seed, name, str(split.index)), n_jobs)
            model.fit(indexed.loc[list(split.fit_ids)], y.loc[list(split.fit_ids)])
            probs = model.predict_proba(indexed.loc[list(split.stopping_ids)])[:, 1]
            truth = y.loc[list(split.stopping_ids)]
            if truth.nunique() > 1:
                scores.append(roc_auc_score(truth, probs))
        selection[name] = float(np.mean(scores)) if scores else float("nan")
    chosen = max(selection, key=lambda k: (selection[k] if np.isfinite(selection[k]) else -np.inf))

    inner_oof = pd.Series(index=list(outer.train_ids), dtype=float)
    outer_accumulator = np.zeros(len(outer.val_ids), dtype=float)
    for split in inner:
        model = _pipeline(chosen, numeric, categorical, stable_seed(seed, chosen, "final", str(split.index)), n_jobs)
        model.fit(indexed.loc[list(split.fit_ids)], y.loc[list(split.fit_ids)])
        inner_oof.loc[list(split.val_ids)] = model.predict_proba(indexed.loc[list(split.val_ids)])[:, 1]
        outer_accumulator += model.predict_proba(indexed.loc[list(outer.val_ids)])[:, 1]
    outer_scores = pd.Series(outer_accumulator / len(inner), index=list(outer.val_ids))
    assert inner_oof.notna().all(), "every outer-train subject needs an inner-OOF score"
    return CrossFitResult(inner_oof, outer_scores, chosen, selection)


# --------------------------------------------------------------------------- #
# Stacking
# --------------------------------------------------------------------------- #
def _logit(p: np.ndarray) -> np.ndarray:
    clipped = np.clip(np.asarray(p, dtype=float), 1e-6, 1 - 1e-6)
    return np.log(clipped / (1.0 - clipped))


@dataclass
class StackResult:
    inner_oof: pd.Series
    outer_scores: pd.Series
    coefficients: dict[str, float]


def stack(components_inner: dict[str, pd.Series], components_outer: dict[str, pd.Series],
          y_train: pd.Series, seed: int) -> StackResult:
    """Second-stage logistic regression on cross-fitted scores.

    Each component enters as a single logit-transformed column, so an
    uninformative component receives a near-zero weight instead of diluting the
    others. That is the whole reason the increment test is built this way: this
    project has measured that appending uninformative columns to demographics
    costs 0.008 to 0.055 AUROC, which would confound "adds nothing" with
    "made it worse".
    """
    names = list(components_inner)
    train_ids = list(components_inner[names[0]].index)
    x_train = np.column_stack([_logit(components_inner[n].loc[train_ids].to_numpy()) for n in names])
    val_ids = list(components_outer[names[0]].index)
    x_val = np.column_stack([_logit(components_outer[n].loc[val_ids].to_numpy()) for n in names])

    model = LogisticRegression(class_weight="balanced", max_iter=2000, random_state=seed)
    model.fit(x_train, y_train.loc[train_ids].to_numpy())
    inner = pd.Series(model.predict_proba(x_train)[:, 1], index=train_ids)
    outer = pd.Series(model.predict_proba(x_val)[:, 1], index=val_ids)
    coefficients = {name: float(c) for name, c in zip(names, model.coef_[0])}
    coefficients["intercept"] = float(model.intercept_[0])
    return StackResult(inner, outer, coefficients)


def select_threshold(y: np.ndarray, score: np.ndarray, grid: Sequence[float] = THRESHOLD_GRID) -> float:
    """Balanced-accuracy threshold from inner-OOF scores, as in every earlier goal."""
    best, best_value = 0.5, -np.inf
    for threshold in grid:
        value = balanced_accuracy_score(y, (score >= float(threshold)).astype(int))
        if value > best_value:
            best, best_value = float(threshold), value
    return best
