"""Reusable framework interfaces for the Chongqing binary diagnosis project."""

from .config import ProjectConfig, load_config
from .data import SubjectRecord, load_subject_manifest
from .evaluation import BinaryMetrics, evaluate_binary_predictions
from .leakage import LeakageError, validate_feature_columns
from .models import BinaryClassifierProtocol, MajorityClassModel
from .splits import build_subject_splits

__all__ = [
    "BinaryClassifierProtocol",
    "BinaryMetrics",
    "LeakageError",
    "MajorityClassModel",
    "ProjectConfig",
    "SubjectRecord",
    "build_subject_splits",
    "evaluate_binary_predictions",
    "load_config",
    "load_subject_manifest",
    "validate_feature_columns",
]
