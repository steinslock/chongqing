"""Goal 2.9: subject-level behavioural features from the paradigm trial logs.

Goal 2.8 rebuilt every neural feature layer and found no increment over
demographics. The keypresses those same paradigms recorded were never used.
This package reads them.
"""

from .behaviour import extract_behaviour_features

__all__ = ["extract_behaviour_features"]
