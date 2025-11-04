"""
SARAi AGI - Security and Resilience System
==========================================

Advanced security and resilience system with:
- Malicious input detection (SQL injection, XSS, script injection, etc.)
- Automatic fallback on system overload
- Input sanitization
- DOS attack prevention
- System resilience monitoring

Version: v3.5.1 (migrated from SARAi v3.5.0)
Author: SARAi Team
License: MIT

Features
--------
1. **Malicious Input Detection**
   - SQL injection patterns (UNION, SELECT, DROP, etc.)
   - XSS attacks (<script>, javascript:, event handlers)
   - Script injection (__import__, eval, exec, os.system)
   - Buffer overflow (excessive repetition)
   - DOS attacks (rate limiting per IP)

2. **Automatic Fallback**
   - CPU usage monitoring (threshold: 90%)
   - Memory usage monitoring (threshold: 85%)
   - Latency monitoring (threshold: 5000ms)
   - Error rate monitoring (threshold: 10%)
   - Auto-recovery after configurable duration

3. **Input Sanitization**
   - HTML tag removal
   - Special character escaping
   - Safe text output for processing

4. **Resilience Metrics**
   - CPU and memory usage
   - Active requests tracking
   - Average latency calculation
   - Error rate tracking
   - Fallback status monitoring

Example
-------
>>> from sarai_agi.security import SecurityResilienceSystem
>>> 
>>> system = SecurityResilienceSystem()
>>> 
>>> # Safe interaction
>>> result = system.process_secure_interaction(
...     text="Hola, ¿cómo estás?",
...     language="es"
... )
>>> print(result['success'])  # True
>>> 
>>> # Malicious interaction (SQL injection)
>>> result = system.process_secure_interaction(
...     text="SELECT * FROM users WHERE 1=1; DROP TABLE users;",
...     language="es",
...     user_ip="192.168.1.100"
... )
>>> print(result['blocked'])  # True
>>> print(result['threats_count'])  # >=1
"""

import logging
import re
import time
import psutil
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
from collections import deque
import threading
import os

logger = logging.getLogger(__name__)


# ============================================================================
# Enumerations
# ============================================================================

class SecurityLevel(Enum):
    """
    Security severity levels.
    
    Levels:
        LOW: Informational, no immediate action required
        MEDIUM: Warning, should be logged and monitored
        HIGH: Serious threat, may require blocking
        CRITICAL: Immediate threat, must be blocked
    """
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AttackType(Enum):
    """
    Types of attacks that can be detected.
    
    Types:
        INJECTION: SQL injection attempts
        XSS: Cross-site scripting attacks
        INJECTION_SCRIPT: Script injection (Python code execution)
        BUFFER_OVERFLOW: Excessively long inputs
        DOS_ATTACK: Denial of service (rate limiting)
        EXPLOIT: Code exploitation attempts
        ABUSE: Malicious abuse patterns
    """
    INJECTION = "sql_injection"
    XSS = "cross_site_scripting"
    INJECTION_SCRIPT = "script_injection"
    BUFFER_OVERFLOW = "buffer_overflow"
    DOS_ATTACK = "denial_of_service"
    EXPLOIT = "code_exploit"
    ABUSE = "abuse_malicious"


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class SecurityThreat:
    """
    Represents a detected security threat.
    
    Attributes:
        attack_type: Type of attack detected
        severity: Severity level (LOW/MEDIUM/HIGH/CRITICAL)
        confidence: Detection confidence (0.0-1.0)
        description: Human-readable description
        detected_pattern: Regex pattern that triggered detection
        timestamp: Unix timestamp of detection
    """
    attack_type: AttackType
    severity: SecurityLevel
    confidence: float
    description: str
    detected_pattern: str
    timestamp: float


@dataclass
class SystemResilienceMetrics:
    """
    System resilience metrics.
    
    Attributes:
        cpu_usage: Current CPU usage percentage
        memory_usage: Current memory usage percentage
        active_requests: Number of active requests in buffer
        avg_latency_ms: Average request latency in milliseconds
        error_rate: Error rate (0.0-1.0)
        fallback_active: Whether fallback mode is active
        uptime_hours: Hours since fallback activation (0 if not active)
    """
    cpu_usage: float
    memory_usage: float
    active_requests: int
    avg_latency_ms: float
    error_rate: float
    fallback_active: bool
    uptime_hours: float


# ============================================================================
# Malicious Input Detector
# ============================================================================

class MaliciousInputDetector:
    """
    Detects malicious patterns in user input.
    
    Supports detection of:
    - SQL injection (UNION, SELECT, DROP, etc.)
    - XSS attacks (<script>, javascript:, event handlers)
    - Script injection (Python code execution)
    - Buffer overflow (excessive length/repetition)
    - DOS attacks (rate limiting per IP)
    """
    
    def __init__(self):
        """Initialize detector with attack patterns."""
        # SQL injection patterns
        self.sql_patterns = [
            r"(\bUNION\b|\bSELECT\b|\bINSERT\b|\bUPDATE\b|\bDELETE\b|\bDROP\b).*\bFROM\b",
            r"';.*--",
            r"1=1",
            r"\bOR\b.*=.*"
        ]
        
        # XSS patterns
        self.xss_patterns = [
            r"<script[^>]*>.*</script>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe",
            r"<object"
        ]
        
        # Script injection patterns
        self.script_injection_patterns = [
            r"__import__",
            r"eval\(",
            r"exec\(",
            r"os\.system",
            r"subprocess\."
        ]
        
        # Buffer overflow patterns
        self.buffer_overflow_patterns = [
            r"A{100,}",  # Excessive repetition
            r".{10000,}"  # Very long strings
        ]
        
        # IP request tracking for DOS detection
        self.ip_requests: Dict[str, deque] = {}
        self.dos_threshold = 100  # requests per minute
    
    def detect_malicious_input(
        self,
        text: str,
        user_ip: Optional[str] = None
    ) -> List[SecurityThreat]:
        """
        Detect malicious patterns in input text.
        
        Args:
            text: Input text to analyze
            user_ip: Optional user IP for DOS detection
            
        Returns:
            List of detected SecurityThreat objects
        """
        threats = []
        
        # Check SQL injection
        for pattern in self.sql_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                threats.append(SecurityThreat(
                    attack_type=AttackType.INJECTION,
                    severity=SecurityLevel.HIGH,
                    confidence=0.85,
                    description="Possible SQL injection detected",
                    detected_pattern=pattern,
                    timestamp=time.time()
                ))
        
        # Check XSS
        for pattern in self.xss_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                threats.append(SecurityThreat(
                    attack_type=AttackType.XSS,
                    severity=SecurityLevel.HIGH,
                    confidence=0.9,
                    description="Possible XSS attack detected",
                    detected_pattern=pattern,
                    timestamp=time.time()
                ))
        
        # Check script injection
        for pattern in self.script_injection_patterns:
            if re.search(pattern, text):
                threats.append(SecurityThreat(
                    attack_type=AttackType.INJECTION_SCRIPT,
                    severity=SecurityLevel.CRITICAL,
                    confidence=0.95,
                    description="Script injection detected",
                    detected_pattern=pattern,
                    timestamp=time.time()
                ))
        
        # Check buffer overflow
        for pattern in self.buffer_overflow_patterns:
            if re.search(pattern, text):
                threats.append(SecurityThreat(
                    attack_type=AttackType.BUFFER_OVERFLOW,
                    severity=SecurityLevel.MEDIUM,
                    confidence=0.7,
                    description="Possible buffer overflow",
                    detected_pattern=pattern,
                    timestamp=time.time()
                ))
        
        # Check DOS attack (rate limiting)
        if user_ip:
            if user_ip not in self.ip_requests:
                self.ip_requests[user_ip] = deque(maxlen=100)
            
            self.ip_requests[user_ip].append(time.time())
            
            # Count requests in last minute
            recent = [
                ts for ts in self.ip_requests[user_ip]
                if time.time() - ts < 60
            ]
            
            if len(recent) > self.dos_threshold:
                threats.append(SecurityThreat(
                    attack_type=AttackType.DOS_ATTACK,
                    severity=SecurityLevel.CRITICAL,
                    confidence=1.0,
                    description=f"DOS attack: {len(recent)} requests/min",
                    detected_pattern="rate_limit_exceeded",
                    timestamp=time.time()
                ))
        
        return threats
    
    def sanitize_input(self, text: str) -> str:
        """
        Sanitize input by removing/escaping dangerous patterns.
        
        Args:
            text: Input text to sanitize
            
        Returns:
            Sanitized text safe for processing
        """
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Escape SQL special characters
        text = text.replace("'", "''")
        text = text.replace('"', '""')
        
        return text


# ============================================================================
# Automatic Fallback System
# ============================================================================

class AutomaticFallbackSystem:
    """
    Automatic fallback system for handling failures and overload.
    
    Monitors:
    - CPU usage (threshold: 90%)
    - Memory usage (threshold: 85%)
    - Request latency (threshold: 5000ms)
    - Error rate (threshold: 10%)
    
    Automatically activates fallback mode when thresholds are exceeded
    and auto-recovers after configurable duration (default: 30 minutes).
    """
    
    def __init__(self):
        """Initialize fallback system with default thresholds."""
        self.fallback_active = False
        self.fallback_reason: Optional[str] = None
        self.fallback_since: Optional[float] = None
        
        # Thresholds
        self.cpu_threshold = 90.0  # %
        self.memory_threshold = 85.0  # %
        self.latency_threshold = 5000.0  # ms
        self.error_rate_threshold = 0.1  # 10%
        
        # Tracking deques
        self.recent_requests: deque = deque(maxlen=100)
        self.recent_errors: deque = deque(maxlen=100)
        self.recent_timeouts: deque = deque(maxlen=100)
        
        # Monitoring thread (daemon)
        self.monitor_thread = threading.Thread(
            target=self._monitor_system,
            daemon=True
        )
        self.monitor_thread.start()
    
    def check_fallback_conditions(self) -> Optional[str]:
        """
        Check if fallback conditions are met.
        
        Returns:
            Condition string if fallback should activate, None otherwise
        """
        # Check CPU
        cpu_usage = psutil.cpu_percent(interval=1)
        if cpu_usage > self.cpu_threshold:
            return f"high_cpu_{cpu_usage:.1f}%"
        
        # Check memory
        memory = psutil.virtual_memory()
        if memory.percent > self.memory_threshold:
            return f"high_memory_{memory.percent:.1f}%"
        
        # Check latency
        if len(self.recent_requests) >= 10:
            avg_latency = sum(self.recent_requests) / len(self.recent_requests)
            if avg_latency > self.latency_threshold:
                return f"high_latency_{avg_latency:.0f}ms"
        
        # Check error rate
        if len(self.recent_errors) >= 10:
            error_rate = len(self.recent_errors) / max(1, len(self.recent_requests))
            if error_rate > self.error_rate_threshold:
                return f"high_error_rate_{error_rate*100:.1f}%"
        
        return None
    
    def activate_fallback(self, condition: str, duration_minutes: int = 30):
        """
        Activate fallback mode.
        
        Args:
            condition: Reason for fallback activation
            duration_minutes: Auto-recovery duration (default: 30)
        """
        self.fallback_active = True
        self.fallback_reason = condition
        self.fallback_since = time.time()
        
        logger.warning(
            f"🛡️ Fallback activated: {condition} (duration: {duration_minutes}min)"
        )
        
        # Schedule auto-reset
        threading.Timer(
            duration_minutes * 60,
            self._reset_fallback
        ).start()
    
    def _reset_fallback(self):
        """Reset fallback mode (internal)."""
        self.fallback_active = False
        self.fallback_reason = None
        self.fallback_since = None
        logger.info("✅ Fallback deactivated")
    
    def record_request(
        self,
        latency: float,
        success: bool,
        timeout: bool = False
    ):
        """
        Record request result for monitoring.
        
        Args:
            latency: Request latency in milliseconds
            success: Whether request succeeded
            timeout: Whether request timed out
        """
        self.recent_requests.append(latency)
        
        if not success:
            self.recent_errors.append(time.time())
        
        if timeout:
            self.recent_timeouts.append(time.time())
    
    def _monitor_system(self):
        """Continuous system monitoring thread (internal)."""
        while True:
            try:
                condition = self.check_fallback_conditions()
                
                if condition and not self.fallback_active:
                    self.activate_fallback(condition)
                
                time.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in fallback monitor: {e}")
                time.sleep(60)  # Backoff on error
    
    def get_resilience_metrics(self) -> SystemResilienceMetrics:
        """
        Get current resilience metrics.
        
        Returns:
            SystemResilienceMetrics object with current stats
        """
        cpu_usage = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        
        avg_latency = (
            sum(self.recent_requests) / max(1, len(self.recent_requests))
        )
        error_rate = (
            len(self.recent_errors) / max(1, len(self.recent_requests))
        )
        
        uptime = (
            (time.time() - self.fallback_since) / 3600
            if self.fallback_since else 0
        )
        
        return SystemResilienceMetrics(
            cpu_usage=cpu_usage,
            memory_usage=memory.percent,
            active_requests=len(self.recent_requests),
            avg_latency_ms=avg_latency,
            error_rate=error_rate,
            fallback_active=self.fallback_active,
            uptime_hours=uptime
        )


# ============================================================================
# Security and Resilience System
# ============================================================================

class SecurityResilienceSystem:
    """
    Main security and resilience system for SARAi AGI.
    
    Integrates:
    - Malicious input detection
    - Automatic fallback system
    - Input sanitization
    - Threat tracking
    - Security metrics
    
    Thread Safety: Components use thread-safe data structures (deque).
    Monitor thread runs as daemon (auto-terminates with main process).
    """
    
    def __init__(self):
        """Initialize security and resilience system."""
        self.detector = MaliciousInputDetector()
        self.fallback_system = AutomaticFallbackSystem()
        
        # Tracking
        self.threats_detected: List[SecurityThreat] = []
        self.blocked_interactions = 0
        self.total_interactions = 0
        
        self._setup_logging()
    
    def validate_input_security(
        self,
        text: str,
        user_ip: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Tuple[bool, str, List[SecurityThreat]]:
        """
        Validate input security and detect threats.
        
        Args:
            text: Input text to validate
            user_ip: Optional user IP for DOS detection
            user_id: Optional user ID for tracking
            
        Returns:
            Tuple of (is_safe, reason, threats_list)
            - is_safe: True if input is safe to process
            - reason: "validated" if safe, or threat description if blocked
            - threats_list: List of all detected threats (empty if none)
        """
        self.total_interactions += 1
        
        # Detect threats
        threats = self.detector.detect_malicious_input(text, user_ip)
        
        if threats:
            self.threats_detected.extend(threats)
            
            # Determine if should block
            critical_threats = [
                t for t in threats
                if t.severity == SecurityLevel.CRITICAL
            ]
            high_threats = [
                t for t in threats
                if t.severity == SecurityLevel.HIGH
            ]
            
            # Block on CRITICAL threats
            if critical_threats:
                self.blocked_interactions += 1
                return (
                    False,
                    f"Critical threat: {critical_threats[0].description}",
                    threats
                )
            
            # Block on multiple HIGH threats
            if len(high_threats) >= 2:
                self.blocked_interactions += 1
                return (False, "Multiple high threats detected", threats)
        
        return (True, "validated", threats)
    
    def process_secure_interaction(
        self,
        text: str,
        language: str,
        emotion: Optional[str] = None,
        user_ip: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process interaction with security validation.
        
        Complete pipeline:
        1. Validate input security (threat detection)
        2. Check fallback conditions (CPU/RAM/latency)
        3. Sanitize input (remove dangerous patterns)
        4. Record metrics (latency, success)
        
        Args:
            text: Input text to process
            language: Language code (e.g., "es", "en")
            emotion: Optional emotion context
            user_ip: Optional user IP for DOS detection
            user_id: Optional user ID for tracking
            
        Returns:
            Dict with:
            - success: bool (True if processed, False if blocked)
            - blocked: bool (True if blocked by security)
            - reason: str (validation result or block reason)
            - threats_count: int (number of threats detected)
            - system_state: str ("normal" or "fallback")
            - processing_time_ms: float (total processing time)
            - sanitized_text: str (cleaned input, if success=True)
        """
        start_time = time.time()
        
        # Validate security
        is_safe, reason, threats = self.validate_input_security(
            text, user_ip, user_id
        )
        
        if not is_safe:
            return {
                'success': False,
                'blocked': True,
                'reason': reason,
                'threats_count': len(threats),
                'processing_time_ms': (time.time() - start_time) * 1000
            }
        
        # Check fallback conditions
        fallback_condition = self.fallback_system.check_fallback_conditions()
        if fallback_condition:
            self.fallback_system.activate_fallback(fallback_condition)
        
        # Sanitize input
        safe_text = self.detector.sanitize_input(text)
        
        processing_time = (time.time() - start_time) * 1000
        
        # Record request metrics
        self.fallback_system.record_request(
            latency=processing_time,
            success=True,
            timeout=False
        )
        
        return {
            'success': True,
            'security_validation': 'passed',
            'threats_count': len(threats),
            'system_state': (
                'fallback' if self.fallback_system.fallback_active
                else 'normal'
            ),
            'processing_time_ms': processing_time,
            'sanitized_text': safe_text
        }
    
    def get_security_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive security and resilience metrics.
        
        Returns:
            Dict with:
            - total_interactions: Total interactions processed
            - threats_detected: Total threats detected
            - blocked_interactions: Interactions blocked
            - block_rate: Percentage of blocked interactions
            - resilience: System resilience metrics (CPU, RAM, latency, etc.)
        """
        resilience_metrics = self.fallback_system.get_resilience_metrics()
        
        return {
            'total_interactions': self.total_interactions,
            'threats_detected': len(self.threats_detected),
            'blocked_interactions': self.blocked_interactions,
            'block_rate': (
                self.blocked_interactions / max(1, self.total_interactions)
            ),
            'resilience': {
                'cpu_usage': resilience_metrics.cpu_usage,
                'memory_usage': resilience_metrics.memory_usage,
                'avg_latency_ms': resilience_metrics.avg_latency_ms,
                'error_rate': resilience_metrics.error_rate,
                'fallback_active': resilience_metrics.fallback_active
            }
        }
    
    def _setup_logging(self):
        """Configure security logging (internal)."""
        # Create logs directory if not exists
        os.makedirs("logs", exist_ok=True)
        
        # Security log file handler
        security_handler = logging.FileHandler("logs/security.log")
        security_handler.setLevel(logging.WARNING)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        security_handler.setFormatter(formatter)
        
        logger.addHandler(security_handler)


# ============================================================================
# Factory Function
# ============================================================================

def create_security_resilience_system() -> SecurityResilienceSystem:
    """
    Create SecurityResilienceSystem instance.
    
    Returns:
        Initialized SecurityResilienceSystem
    """
    return SecurityResilienceSystem()
