"""
SARAi Integrations Module

Módulo de integraciones con servicios externos.
"""

from .saul_integration import (
    SAULIntegration,
    SARAiSAULAdapter,
    create_saul_integration,
    SAUL_AVAILABLE
)

__all__ = [
    "SAULIntegration",
    "SARAiSAULAdapter",
    "create_saul_integration",
    "SAUL_AVAILABLE",
]
