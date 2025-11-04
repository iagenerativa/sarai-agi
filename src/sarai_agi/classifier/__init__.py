"""Módulo de clasificación de intenciones (TRM Classifier)."""

from .trm import (
    HAS_TORCH,
    TRMClassifierSimulated,
    create_trm_classifier,
)

__all__ = [
    "TRMClassifierSimulated",
    "create_trm_classifier",
    "HAS_TORCH",
]

# Import TRMClassifier only if torch is available
if HAS_TORCH:
    from .trm import TRMClassifier
    __all__.append("TRMClassifier")
else:
    # Provide a dummy class for type hints
    TRMClassifier = None  # type: ignore
