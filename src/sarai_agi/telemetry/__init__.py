"""
SARAi AGI - Telemetry Module
============================

Advanced telemetry and monitoring system with Prometheus-style metrics.

Components:
- AdvancedTelemetry: Main telemetry integration
- MetricsCollector: Metrics collection and aggregation
- SystemMonitor: System health monitoring
- MetricType, AlertLevel: Enums for classification
- TelemetryMetric, SystemAlert: Data structures

Example:
    >>> from sarai_agi.telemetry import AdvancedTelemetry
    >>>
    >>> telemetry = AdvancedTelemetry()
    >>> telemetry.start_monitoring()
    >>>
    >>> telemetry.record_interaction(
    ...     user_id="user_123",
    ...     text_length=100,
    ...     language="es",
    ...     emotional_context="happy",
    ...     security_validated=True,
    ...     processing_time_ms=250.0
    ... )
    >>>
    >>> metrics = telemetry.get_comprehensive_metrics()
    >>> telemetry.export_metrics("dashboard.json")
"""

from .monitoring import (
    AdvancedTelemetry,
    AlertLevel,
    MetricsCollector,
    MetricType,
    SystemAlert,
    SystemMonitor,
    TelemetryMetric,
    create_advanced_telemetry,
)

__all__ = [
    "AdvancedTelemetry",
    "MetricsCollector",
    "SystemMonitor",
    "MetricType",
    "AlertLevel",
    "TelemetryMetric",
    "SystemAlert",
    "create_advanced_telemetry"
]
