"""Módulo de clasificación de intenciones (TRM Classifier)."""

from .trm import (
    TRMClassifier,
    TRMClassifierSimulated,
    create_trm_classifier,
)

__all__ = [
    "TRMClassifier",
    "TRMClassifierSimulated",
    "create_trm_classifier",
]
