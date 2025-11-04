"""
Tests for Advanced Telemetry and Monitoring System
=================================================

Test Coverage:
- Metrics collection (counters, gauges)
- Metric summaries (min, max, mean, percentiles)
- System monitoring (CPU, memory, disk)
- Alert generation (threshold-based)
- Background monitoring thread
- Metrics export (JSON)
- Integration scenarios
"""

import pytest
import time
import json
import tempfile
import os
from unittest.mock import patch, MagicMock

from sarai_agi.telemetry import (
    AdvancedTelemetry,
    MetricsCollector,
    SystemMonitor,
    MetricType,
    AlertLevel,
    TelemetryMetric,
    SystemAlert,
    create_advanced_telemetry
)


# ============================================================================
# Metrics Collector Tests
# ============================================================================

class TestMetricsCollector:
    """Test suite for metrics collection."""
    
    def test_record_metric(self):
        """Test basic metric recording."""
        collector = MetricsCollector()
        
        collector.record_metric(
            name="test_metric",
            value=42.5,
            labels={"env": "test"},
            unit="ms",
            description="Test metric"
        )
        
        assert "test_metric" in collector.metrics
        assert len(collector.metrics["test_metric"]) == 1
        
        metric = collector.metrics["test_metric"][0]
        assert metric.value == 42.5
        assert metric.labels == {"env": "test"}
        assert metric.unit == "ms"
    
    def test_increment_counter(self):
        """Test counter incrementation."""
        collector = MetricsCollector()
        
        # Initial value
        assert collector.counters["interactions_total"] == 0
        
        # Increment
        collector.increment_counter("interactions_total")
        assert collector.counters["interactions_total"] == 1
        
        # Increment by amount
        collector.increment_counter("interactions_total", 5.0)
        assert collector.counters["interactions_total"] == 6.0
    
    def test_gauge_update(self):
        """Test gauge value updates."""
        collector = MetricsCollector()
        
        # Record gauge (can go up or down)
        collector.record_metric("memory_usage_mb", 1000.0)
        assert collector.gauges["memory_usage_mb"] == 1000.0
        
        collector.record_metric("memory_usage_mb", 800.0)
        assert collector.gauges["memory_usage_mb"] == 800.0  # Can decrease
    
    def test_metric_summary_statistics(self):
        """Test metric summary with statistical aggregations."""
        collector = MetricsCollector()
        
        # Record multiple values
        values = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0]
        for val in values:
            collector.record_metric("latency_ms", val)
        
        summary = collector.get_metric_summary("latency_ms", time_window_minutes=60)
        
        assert summary["count"] == 10
        assert summary["min"] == 10.0
        assert summary["max"] == 100.0
        assert summary["mean"] == 55.0  # (10+...+100)/10
        assert summary["p50"] == pytest.approx(50.0, abs=10.0)  # Median
        assert summary["p95"] >= 90.0  # 95th percentile
        assert summary["p99"] >= 95.0  # 99th percentile
    
    def test_metric_time_window_filtering(self):
        """Test time window filtering in metric summaries."""
        collector = MetricsCollector()
        
        # Record old metric (older than 1 minute)
        old_timestamp = time.time() - 120  # 2 minutes ago
        old_metric = TelemetryMetric(
            name="old_metric",
            value=999.0,
            metric_type=MetricType.GAUGE,
            timestamp=old_timestamp,
            labels={},
            unit="",
            description=""
        )
        collector.metrics["test_metric"].append(old_metric)
        
        # Record recent metric
        collector.record_metric("test_metric", 42.0)
        
        # Summary with 1-minute window should exclude old metric
        summary = collector.get_metric_summary("test_metric", time_window_minutes=1)
        
        assert summary["count"] == 1  # Only recent metric
        assert summary["mean"] == 42.0
    
    def test_thread_safety(self):
        """Test thread-safe metric recording."""
        import threading
        
        collector = MetricsCollector()
        
        def record_metrics():
            for i in range(100):
                collector.record_metric("concurrent_metric", float(i))
                collector.increment_counter("interactions_total")
        
        # Run 5 threads concurrently
        threads = [threading.Thread(target=record_metrics) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Should have 500 metrics total (5 threads * 100)
        assert len(collector.metrics["concurrent_metric"]) == 500
        assert collector.counters["interactions_total"] == 500


# ============================================================================
# System Monitor Tests
# ============================================================================

class TestSystemMonitor:
    """Test suite for system monitoring."""
    
    def test_start_stop_monitoring(self):
        """Test monitoring start/stop."""
        collector = MetricsCollector()
        monitor = SystemMonitor(collector)
        
        assert not monitor.monitoring
        
        monitor.start_monitoring()
        assert monitor.monitoring
        assert monitor.monitor_thread is not None
        assert monitor.monitor_thread.is_alive()
        
        monitor.stop_monitoring()
        assert not monitor.monitoring
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_collect_system_metrics(self, mock_disk, mock_memory, mock_cpu):
        """Test system metrics collection."""
        # Mock system values
        mock_cpu.return_value = 45.0
        mock_memory.return_value = MagicMock(used=5368709120)  # 5GB in bytes
        mock_disk.return_value = MagicMock(percent=60.0)
        
        collector = MetricsCollector()
        monitor = SystemMonitor(collector)
        
        monitor._collect_system_metrics()
        
        # Verify metrics were recorded
        assert collector.gauges["cpu_usage_percent"] == 45.0
        assert collector.gauges["memory_usage_mb"] == pytest.approx(5120.0, abs=10.0)  # ~5GB
        assert "disk_usage_percent" in collector.metrics
    
    @patch('psutil.cpu_percent')
    def test_alert_on_high_cpu(self, mock_cpu):
        """Test alert generation on high CPU usage."""
        mock_cpu.return_value = 90.0  # Above 85% threshold
        
        collector = MetricsCollector()
        monitor = SystemMonitor(collector)
        
        # Collect metrics and check thresholds
        monitor._collect_system_metrics()
        monitor._check_thresholds()
        
        # Should generate alert
        assert len(monitor.alerts) >= 1
        alert = monitor.alerts[-1]
        assert alert.level == AlertLevel.WARNING
        assert alert.metric_name == "cpu_usage_percent"
        assert alert.current_value == 90.0
        assert alert.threshold == 85.0
    
    @patch('psutil.virtual_memory')
    def test_alert_on_high_memory(self, mock_memory):
        """Test alert generation on high memory usage."""
        # 15GB in bytes (above 12GB threshold)
        mock_memory.return_value = MagicMock(used=16106127360)
        
        collector = MetricsCollector()
        monitor = SystemMonitor(collector)
        
        monitor._collect_system_metrics()
        monitor._check_thresholds()
        
        # Should generate alert
        memory_alerts = [
            a for a in monitor.alerts
            if a.metric_name == "memory_usage_mb"
        ]
        assert len(memory_alerts) >= 1
        assert memory_alerts[-1].current_value > 12000
    
    def test_alert_history_limit(self):
        """Test that alert history is limited to 100 alerts."""
        collector = MetricsCollector()
        monitor = SystemMonitor(collector)
        
        # Create 150 alerts
        for i in range(150):
            monitor._create_alert(
                AlertLevel.WARNING,
                "test_metric",
                float(i),
                50.0
            )
        
        # Should keep only last 100
        assert len(monitor.alerts) == 100


# ============================================================================
# Advanced Telemetry Tests
# ============================================================================

class TestAdvancedTelemetry:
    """Test suite for main telemetry system."""
    
    def test_initialization(self):
        """Test telemetry system initialization."""
        telemetry = AdvancedTelemetry()
        
        assert telemetry.metrics_collector is not None
        assert telemetry.system_monitor is not None
        assert telemetry.start_time > 0
    
    def test_record_interaction(self):
        """Test interaction recording."""
        telemetry = AdvancedTelemetry()
        
        telemetry.record_interaction(
            user_id="user_123",
            text_length=150,
            language="es",
            emotional_context="happy",
            security_validated=True,
            processing_time_ms=250.0
        )
        
        # Check counters
        assert telemetry.metrics_collector.counters["interactions_total"] == 1
        assert telemetry.metrics_collector.counters["security_threats_total"] == 0
        
        # Check metrics recorded
        assert "interaction_processing_time_ms" in telemetry.metrics_collector.metrics
        assert "interaction_text_length" in telemetry.metrics_collector.metrics
    
    def test_record_interaction_with_security_threat(self):
        """Test interaction recording with security threat."""
        telemetry = AdvancedTelemetry()
        
        telemetry.record_interaction(
            user_id="user_456",
            text_length=100,
            language="en",
            emotional_context="neutral",
            security_validated=False,  # Security threat
            processing_time_ms=150.0
        )
        
        assert telemetry.metrics_collector.counters["interactions_total"] == 1
        assert telemetry.metrics_collector.counters["security_threats_total"] == 1
    
    def test_record_cache_operations(self):
        """Test cache hit/miss recording."""
        telemetry = AdvancedTelemetry()
        
        telemetry.record_cache_hit()
        telemetry.record_cache_hit()
        telemetry.record_cache_miss()
        
        assert telemetry.metrics_collector.counters["cache_hits_total"] == 2
        assert telemetry.metrics_collector.counters["cache_misses_total"] == 1
    
    def test_record_error(self):
        """Test error recording."""
        telemetry = AdvancedTelemetry()
        
        telemetry.record_error()
        telemetry.record_error()
        
        assert telemetry.metrics_collector.counters["errors_total"] == 2
    
    def test_get_comprehensive_metrics(self):
        """Test comprehensive metrics retrieval."""
        telemetry = AdvancedTelemetry()
        
        # Record some interactions
        for i in range(5):
            telemetry.record_interaction(
                user_id=f"user_{i}",
                text_length=100 + i * 10,
                language="es",
                emotional_context="neutral",
                security_validated=True,
                processing_time_ms=200.0 + i * 10
            )
        
        metrics = telemetry.get_comprehensive_metrics(time_window_minutes=60)
        
        # Check structure
        assert "uptime_hours" in metrics
        assert "counters" in metrics
        assert "gauges" in metrics
        assert "processing_time_summary" in metrics
        assert "alerts_count" in metrics
        assert "recent_alerts" in metrics
        
        # Check values
        assert metrics["counters"]["interactions_total"] == 5
        assert metrics["processing_time_summary"]["count"] == 5
    
    def test_export_metrics(self):
        """Test metrics export to JSON file."""
        telemetry = AdvancedTelemetry()
        
        # Record some data
        telemetry.record_interaction(
            user_id="test_user",
            text_length=100,
            language="es",
            emotional_context="happy",
            security_validated=True,
            processing_time_ms=250.0
        )
        
        # Export to temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_filename = f.name
        
        try:
            success = telemetry.export_metrics(temp_filename)
            
            assert success
            assert os.path.exists(temp_filename)
            
            # Verify JSON content
            with open(temp_filename, 'r') as f:
                data = json.load(f)
            
            assert "uptime_hours" in data
            assert "counters" in data
            assert data["counters"]["interactions_total"] == 1
            
        finally:
            # Cleanup
            if os.path.exists(temp_filename):
                os.remove(temp_filename)
    
    def test_monitoring_lifecycle(self):
        """Test monitoring start/stop lifecycle."""
        telemetry = AdvancedTelemetry()
        
        assert not telemetry.system_monitor.monitoring
        
        telemetry.start_monitoring()
        assert telemetry.system_monitor.monitoring
        
        telemetry.stop()
        assert not telemetry.system_monitor.monitoring


# ============================================================================
# Factory Function Tests
# ============================================================================

class TestFactoryFunction:
    """Test suite for factory function."""
    
    def test_create_advanced_telemetry(self):
        """Test factory function."""
        telemetry = create_advanced_telemetry()
        
        assert isinstance(telemetry, AdvancedTelemetry)
        assert isinstance(telemetry.metrics_collector, MetricsCollector)
        assert isinstance(telemetry.system_monitor, SystemMonitor)


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration test scenarios."""
    
    def test_full_telemetry_pipeline(self):
        """Test complete telemetry pipeline."""
        telemetry = create_advanced_telemetry()
        telemetry.start_monitoring()
        
        try:
            # Simulate 10 interactions
            for i in range(10):
                telemetry.record_interaction(
                    user_id=f"user_{i % 3}",
                    text_length=100 + i * 10,
                    language="es" if i % 2 == 0 else "en",
                    emotional_context="happy" if i % 2 == 0 else "neutral",
                    security_validated=(i % 5 != 0),  # 20% threats
                    processing_time_ms=200.0 + i * 20
                )
            
            # Record cache operations
            telemetry.record_cache_hit()
            telemetry.record_cache_hit()
            telemetry.record_cache_miss()
            
            # Record errors
            telemetry.record_error()
            
            # Get metrics
            metrics = telemetry.get_comprehensive_metrics()
            
            assert metrics["counters"]["interactions_total"] == 10
            assert metrics["counters"]["security_threats_total"] == 2  # 20% of 10
            assert metrics["counters"]["cache_hits_total"] == 2
            assert metrics["counters"]["cache_misses_total"] == 1
            assert metrics["counters"]["errors_total"] == 1
            
        finally:
            telemetry.stop()
    
    def test_concurrent_interactions(self):
        """Test concurrent interaction recording."""
        import threading
        
        telemetry = AdvancedTelemetry()
        
        def record_interactions():
            for i in range(20):
                telemetry.record_interaction(
                    user_id="concurrent_user",
                    text_length=100,
                    language="es",
                    emotional_context="neutral",
                    security_validated=True,
                    processing_time_ms=250.0
                )
        
        # Run 3 threads concurrently
        threads = [threading.Thread(target=record_interactions) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Should have 60 interactions total
        metrics = telemetry.get_comprehensive_metrics()
        assert metrics["counters"]["interactions_total"] == 60
    
    @patch('psutil.cpu_percent')
    def test_monitoring_with_alerts(self, mock_cpu):
        """Test monitoring loop generates alerts correctly."""
        # Simulate high CPU
        mock_cpu.return_value = 92.0
        
        telemetry = AdvancedTelemetry()
        telemetry.start_monitoring()
        
        try:
            # Wait for monitoring loop to run (30s interval, give it 2s grace)
            time.sleep(2)
            
            # Should have collected CPU metric
            assert "cpu_usage_percent" in telemetry.metrics_collector.metrics
            
        finally:
            telemetry.stop()
