"""
SARAi AGI - Security Module
===========================

Security and resilience system with threat detection and auto-fallback.

Components:
- SecurityResilienceSystem: Main security integration
- MaliciousInputDetector: Threat detection (SQL injection, XSS, etc.)
- AutomaticFallbackSystem: System overload protection
- SecurityLevel, AttackType: Enums for security classification
- SecurityThreat, SystemResilienceMetrics: Data structures

Example:
    >>> from sarai_agi.security import SecurityResilienceSystem
    >>> 
    >>> system = SecurityResilienceSystem()
    >>> result = system.process_secure_interaction(
    ...     text="Hola, ¿cómo estás?",
    ...     language="es"
    ... )
    >>> print(result['success'])  # True
"""

from .resilience import (
    SecurityResilienceSystem,
    MaliciousInputDetector,
    AutomaticFallbackSystem,
    SecurityLevel,
    AttackType,
    SecurityThreat,
    SystemResilienceMetrics,
    create_security_resilience_system
)

__all__ = [
    "SecurityResilienceSystem",
    "MaliciousInputDetector",
    "AutomaticFallbackSystem",
    "SecurityLevel",
    "AttackType",
    "SecurityThreat",
    "SystemResilienceMetrics",
    "create_security_resilience_system"
]
