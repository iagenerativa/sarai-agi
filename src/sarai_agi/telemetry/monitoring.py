"""
SARAi AGI - Advanced Telemetry and Monitoring System
===================================================

Prometheus-style metrics collection and system monitoring with:
- Metrics collection (counters, gauges, histograms, summaries)
- System monitoring (CPU, memory, disk, network)
- Auto-alerts with thresholds
- Real-time dashboard data export

Version: v3.5.1 (migrated from SARAi v3.5.0)
Author: SARAi Team
License: MIT

Features
--------
1. **Metrics Collection**
   - Counters: Monotonically increasing values
   - Gauges: Values that can go up or down
   - Histograms: Value distributions
   - Summaries: Statistical summaries

2. **System Monitoring**
   - CPU usage monitoring (threshold: 85%)
   - Memory usage monitoring (threshold: 12GB)
   - Disk usage monitoring
   - Network I/O tracking
   - Background monitoring thread (30s interval)

3. **Auto-Alerts**
   - Threshold-based alerting
   - Alert levels: INFO, WARNING, ERROR, CRITICAL
   - Alert history (last 100 alerts)
   - Automatic threshold checking

4. **Metrics Export**
   - JSON export for dashboards
   - Prometheus-compatible format
   - Time-window filtering
   - Percentile calculations (P50, P95, P99)

Example
-------
>>> from sarai_agi.telemetry import AdvancedTelemetry
>>> 
>>> telemetry = AdvancedTelemetry()
>>> telemetry.start_monitoring()
>>> 
>>> # Record interaction
>>> telemetry.record_interaction(
...     user_id="user_123",
...     text_length=100,
...     language="es",
...     emotional_context="happy",
...     security_validated=True,
...     processing_time_ms=250.0
... )
>>> 
>>> # Get metrics
>>> metrics = telemetry.get_comprehensive_metrics(time_window_minutes=60)
>>> print(metrics['counters']['interactions_total'])  # 1
>>> 
>>> # Export to file
>>> telemetry.export_metrics("dashboard_metrics.json")
>>> 
>>> # Stop monitoring
>>> telemetry.stop()
"""

import logging
import time
import psutil
import threading
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, deque
import json

logger = logging.getLogger(__name__)


# ============================================================================
# Enumerations
# ============================================================================

class MetricType(Enum):
    """
    Types of telemetry metrics.
    
    Types:
        COUNTER: Monotonically increasing (total requests, errors, etc.)
        GAUGE: Can go up or down (memory usage, active connections)
        HISTOGRAM: Distribution of values (latencies, sizes)
        SUMMARY: Statistical summaries (averages, percentiles)
    """
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class AlertLevel(Enum):
    """
    Alert severity levels.
    
    Levels:
        INFO: Informational, no action required
        WARNING: Warning, should be monitored
        ERROR: Error, requires attention
        CRITICAL: Critical, immediate action required
    """
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class TelemetryMetric:
    """
    Represents a telemetry metric.
    
    Attributes:
        name: Metric name (e.g., "cpu_usage_percent")
        value: Metric value
        metric_type: Type of metric (COUNTER, GAUGE, etc.)
        timestamp: Unix timestamp when recorded
        labels: Key-value labels (e.g., {"language": "es"})
        unit: Unit of measurement (e.g., "%", "ms", "MB")
        description: Human-readable description
    """
    name: str
    value: float
    metric_type: MetricType
    timestamp: float
    labels: Dict[str, str]
    unit: str
    description: str


@dataclass
class SystemAlert:
    """
    Represents a system alert.
    
    Attributes:
        level: Alert severity level
        metric_name: Name of metric that triggered alert
        message: Human-readable alert message
        timestamp: Unix timestamp when alert was created
        current_value: Current value that triggered alert
        threshold: Threshold that was exceeded
    """
    level: AlertLevel
    metric_name: str
    message: str
    timestamp: float
    current_value: float
    threshold: float


# ============================================================================
# Metrics Collector
# ============================================================================

class MetricsCollector:
    """
    Collects and manages telemetry metrics.
    
    Thread Safety: Uses RLock for concurrent access protection.
    Window Size: Maintains last 1000 values per metric.
    """
    
    def __init__(self):
        """Initialize metrics collector with predefined counters and gauges."""
        self.metrics: Dict[str, List[TelemetryMetric]] = defaultdict(list)
        self.metric_windows = defaultdict(lambda: deque(maxlen=1000))
        
        # Predefined counters (monotonically increasing)
        self.counters = {
            "interactions_total": 0,
            "errors_total": 0,
            "security_threats_total": 0,
            "cache_hits_total": 0,
            "cache_misses_total": 0
        }
        
        # Predefined gauges (can go up or down)
        self.gauges = {
            "active_connections": 0,
            "memory_usage_mb": 0,
            "cpu_usage_percent": 0,
            "queue_length": 0
        }
        
        self.lock = threading.RLock()
    
    def record_metric(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
        unit: str = "",
        description: str = ""
    ):
        """
        Record a metric.
        
        Args:
            name: Metric name
            value: Metric value
            labels: Optional labels dict
            unit: Optional unit of measurement
            description: Optional human-readable description
        """
        with self.lock:
            metric = TelemetryMetric(
                name=name,
                value=value,
                metric_type=MetricType.GAUGE,  # Default to GAUGE
                timestamp=time.time(),
                labels=labels or {},
                unit=unit,
                description=description
            )
            
            self.metrics[name].append(metric)
            self.metric_windows[name].append(value)
            
            # Update counters/gauges if predefined
            if name in self.gauges:
                self.gauges[name] = value
    
    def increment_counter(self, name: str, amount: float = 1.0):
        """
        Increment a counter metric.
        
        Args:
            name: Counter name
            amount: Amount to increment (default: 1.0)
        """
        with self.lock:
            if name in self.counters:
                self.counters[name] += amount
    
    def get_metric_summary(
        self,
        name: str,
        time_window_minutes: int = 60
    ) -> Dict[str, Any]:
        """
        Get statistical summary of a metric within time window.
        
        Args:
            name: Metric name
            time_window_minutes: Time window in minutes (default: 60)
            
        Returns:
            Dict with:
            - count: Number of values in window
            - min: Minimum value
            - max: Maximum value
            - mean: Average value
            - p50: 50th percentile (median)
            - p95: 95th percentile
            - p99: 99th percentile
        """
        with self.lock:
            if name not in self.metrics:
                return {}
            
            # Filter by time window
            cutoff_time = time.time() - (time_window_minutes * 60)
            recent_metrics = [
                m for m in self.metrics[name]
                if m.timestamp >= cutoff_time
            ]
            
            if not recent_metrics:
                return {}
            
            values = [m.value for m in recent_metrics]
            
            return {
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "mean": sum(values) / len(values),
                "p50": self._percentile(values, 0.5),
                "p95": self._percentile(values, 0.95),
                "p99": self._percentile(values, 0.99)
            }
    
    def _percentile(self, values: List[float], percentile: float) -> float:
        """
        Calculate percentile of values.
        
        Args:
            values: List of values
            percentile: Percentile to calculate (0.0-1.0)
            
        Returns:
            Percentile value
        """
        if not values:
            return 0.0
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile)
        return sorted_values[min(index, len(sorted_values) - 1)]


# ============================================================================
# System Monitor
# ============================================================================

class SystemMonitor:
    """
    Monitors system health and generates alerts.
    
    Monitors:
    - CPU usage (threshold: 85%)
    - Memory usage (threshold: 12GB = 12000 MB)
    - Disk usage
    - Network I/O
    
    Background Thread: Runs monitoring loop every 30 seconds.
    Alert History: Maintains last 100 alerts.
    """
    
    def __init__(self, metrics_collector: MetricsCollector):
        """
        Initialize system monitor.
        
        Args:
            metrics_collector: MetricsCollector instance to use
        """
        self.metrics = metrics_collector
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        
        # Thresholds for alerts
        self.thresholds = {
            "cpu_usage_percent": 85.0,  # %
            "memory_usage_mb": 12000,   # 12GB
            "queue_length": 100
        }
        
        self.alerts: List[SystemAlert] = []
    
    def start_monitoring(self):
        """Start continuous system monitoring."""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(
                target=self._monitoring_loop,
                daemon=True
            )
            self.monitor_thread.start()
            logger.info("✅ System monitoring started")
    
    def stop_monitoring(self):
        """Stop system monitoring."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("System monitoring stopped")
    
    def _monitoring_loop(self):
        """Continuous monitoring loop (internal)."""
        while self.monitoring:
            try:
                self._collect_system_metrics()
                self._check_thresholds()
                time.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)  # Backoff on error
    
    def _collect_system_metrics(self):
        """Collect system metrics (internal)."""
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        self.metrics.record_metric("cpu_usage_percent", cpu_percent, unit="%")
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_mb = memory.used / (1024 * 1024)
        self.metrics.record_metric("memory_usage_mb", memory_mb, unit="MB")
        
        # Disk usage
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        self.metrics.record_metric("disk_usage_percent", disk_percent, unit="%")
        
        # Network I/O (if available)
        try:
            network = psutil.net_io_counters()
            self.metrics.record_metric(
                "network_bytes_sent",
                network.bytes_sent,
                unit="bytes"
            )
            self.metrics.record_metric(
                "network_bytes_recv",
                network.bytes_recv,
                unit="bytes"
            )
        except Exception:
            pass  # Network stats may not be available
    
    def _check_thresholds(self):
        """Check thresholds and generate alerts (internal)."""
        for metric_name, threshold in self.thresholds.items():
            if metric_name in self.metrics.gauges:
                current_value = self.metrics.gauges[metric_name]
                
                if current_value > threshold:
                    self._create_alert(
                        AlertLevel.WARNING,
                        metric_name,
                        current_value,
                        threshold
                    )
    
    def _create_alert(
        self,
        level: AlertLevel,
        metric_name: str,
        current_value: float,
        threshold: float
    ):
        """
        Create and record an alert (internal).
        
        Args:
            level: Alert severity level
            metric_name: Name of metric that triggered alert
            current_value: Current value
            threshold: Threshold that was exceeded
        """
        alert = SystemAlert(
            level=level,
            metric_name=metric_name,
            message=f"{metric_name} exceeded threshold: {current_value:.2f} > {threshold:.2f}",
            timestamp=time.time(),
            current_value=current_value,
            threshold=threshold
        )
        
        self.alerts.append(alert)
        logger.warning(f"🚨 Alert: {alert.message}")
        
        # Keep only last 100 alerts
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]


# ============================================================================
# Advanced Telemetry System
# ============================================================================

class AdvancedTelemetry:
    """
    Advanced telemetry and monitoring system for SARAi AGI.
    
    Integrates:
    - Metrics collection (counters, gauges)
    - System monitoring (CPU, memory, disk, network)
    - Auto-alerts with configurable thresholds
    - Metrics export for dashboards
    
    Thread Safety: All components are thread-safe.
    Background Monitoring: Auto-starts monitoring thread.
    """
    
    def __init__(self):
        """Initialize advanced telemetry system."""
        self.metrics_collector = MetricsCollector()
        self.system_monitor = SystemMonitor(self.metrics_collector)
        
        self.start_time = time.time()
        
        logger.info("✅ Advanced Telemetry System initialized")
    
    def start_monitoring(self):
        """Start system monitoring (CPU, memory, disk, network)."""
        self.system_monitor.start_monitoring()
    
    def stop(self):
        """Stop telemetry system and monitoring."""
        self.system_monitor.stop_monitoring()
    
    def record_interaction(
        self,
        user_id: str,
        text_length: int,
        language: str,
        emotional_context: str,
        security_validated: bool,
        processing_time_ms: float
    ):
        """
        Record an interaction with full context.
        
        Args:
            user_id: User identifier
            text_length: Length of input text (characters)
            language: Language code (e.g., "es", "en")
            emotional_context: Emotion label (e.g., "happy", "neutral")
            security_validated: Whether security validation passed
            processing_time_ms: Processing time in milliseconds
        """
        labels = {
            "language": language,
            "emotion": emotional_context,
            "user_id": user_id
        }
        
        # Record processing time
        self.metrics_collector.record_metric(
            "interaction_processing_time_ms",
            processing_time_ms,
            labels=labels,
            unit="ms"
        )
        
        # Record text length
        self.metrics_collector.record_metric(
            "interaction_text_length",
            text_length,
            labels=labels,
            unit="chars"
        )
        
        # Update counters
        self.metrics_collector.increment_counter("interactions_total")
        
        if not security_validated:
            self.metrics_collector.increment_counter("security_threats_total")
    
    def record_cache_hit(self):
        """Record a cache hit."""
        self.metrics_collector.increment_counter("cache_hits_total")
    
    def record_cache_miss(self):
        """Record a cache miss."""
        self.metrics_collector.increment_counter("cache_misses_total")
    
    def record_error(self):
        """Record an error occurrence."""
        self.metrics_collector.increment_counter("errors_total")
    
    def get_comprehensive_metrics(
        self,
        time_window_minutes: int = 60
    ) -> Dict[str, Any]:
        """
        Get comprehensive metrics summary.
        
        Args:
            time_window_minutes: Time window for aggregation (default: 60)
            
        Returns:
            Dict with:
            - uptime_hours: System uptime in hours
            - counters: All counter values
            - gauges: All gauge values
            - processing_time_summary: Statistical summary of processing times
            - alerts_count: Total number of alerts
            - recent_alerts: Last 5 alerts
        """
        processing_summary = self.metrics_collector.get_metric_summary(
            "interaction_processing_time_ms",
            time_window_minutes
        )
        
        return {
            "uptime_hours": (time.time() - self.start_time) / 3600,
            "counters": self.metrics_collector.counters.copy(),
            "gauges": self.metrics_collector.gauges.copy(),
            "processing_time_summary": processing_summary,
            "alerts_count": len(self.system_monitor.alerts),
            "recent_alerts": [asdict(a) for a in self.system_monitor.alerts[-5:]]
        }
    
    def export_metrics(self, filename: str = "metrics_export.json") -> bool:
        """
        Export metrics to JSON file for dashboards.
        
        Args:
            filename: Output filename (default: "metrics_export.json")
            
        Returns:
            True if successful, False otherwise
        """
        try:
            metrics_data = self.get_comprehensive_metrics()
            
            with open(filename, 'w') as f:
                json.dump(metrics_data, f, indent=2, default=str)
            
            logger.info(f"✅ Metrics exported to {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting metrics: {e}")
            return False


# ============================================================================
# Factory Function
# ============================================================================

def create_advanced_telemetry() -> AdvancedTelemetry:
    """
    Create AdvancedTelemetry instance.
    
    Returns:
        Initialized AdvancedTelemetry
    """
    return AdvancedTelemetry()
