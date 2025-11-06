"""
Monitoring module for SARAi v3.7.

Real-time monitoring components:
- silence_gap_monitor.py: Detects uncomfortable silences
"""

from .silence_gap_monitor import SilenceGapMonitor, SilenceEvent, SilenceType

__all__ = [
    'SilenceGapMonitor',
    'SilenceEvent',
    'SilenceType',
]
