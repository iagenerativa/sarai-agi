"""
SARAi HLCS - Episode Data Model
================================

Representa un episodio de aprendizaje:
- Problema detectado (anomalía)
- Acción tomada
- Resultado obtenido
- Embedding vectorial para FAISS

Version: 0.1.0
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

import hashlib
import json


class EpisodeStatus(Enum):
    """Estado del episodio."""
    OPEN = "open"                    # Problema detectado, sin acción
    ACTION_PROPOSED = "proposed"      # Acción propuesta, no aplicada
    ACTION_APPLIED = "applied"        # Acción aplicada, esperando resultado
    RESOLVED = "resolved"             # Problema resuelto exitosamente
    FAILED = "failed"                 # Acción empeoró el problema
    ROLLED_BACK = "rolled_back"       # Acción revertida
    CONTRAPRODUCTIVE = "contraproductive"  # Marcado como no repetir


class AnomalyType(Enum):
    """Tipo de anomalía detectada."""
    LATENCY_SPIKE = "latency_spike"
    RAM_PRESSURE = "ram_pressure"
    CACHE_MISS_STORM = "cache_miss_storm"
    FALLBACK_RATE_HIGH = "fallback_rate_high"
    ERROR_RATE_HIGH = "error_rate_high"
    RESPONSE_QUALITY_LOW = "response_quality_low"
    UNKNOWN = "unknown"


@dataclass
class Anomaly:
    """Anomalía detectada por SelfMonitor."""
    type: AnomalyType
    severity: float  # 0.0-1.0
    metric_name: str
    current_value: float
    expected_value: float
    threshold: float
    context: Dict = field(default_factory=dict)
    
    def __str__(self) -> str:
        return (
            f"{self.type.value}: {self.metric_name}={self.current_value:.2f} "
            f"(expected={self.expected_value:.2f}, threshold={self.threshold:.2f}, "
            f"severity={self.severity:.2f})"
        )


@dataclass
class Action:
    """Acción propuesta por Autocorrector."""
    name: str  # e.g., "increase_cache_ttl"
    target_component: str  # e.g., "rag.web_cache"
    config_fragment: Dict
    reason: str
    confidence: float = 0.0  # 0.0-1.0 (v0.2+ con meta-reasoner)
    estimated_impact: Optional[Dict] = None  # {"latency": -0.3, "ram": 0.1}
    
    def to_api_payload(self) -> Dict:
        """Convierte a payload para PUT /config/live."""
        return {
            "action": self.name,
            "config_fragment": self.config_fragment,
            "reason": self.reason,
            "hlcs_episode_id": "",  # Se rellena al aplicar
        }
    
    def __str__(self) -> str:
        return f"{self.name} on {self.target_component} (confidence={self.confidence:.2f})"


@dataclass
class Result:
    """Resultado de aplicar una acción."""
    success: bool
    metrics_before: Dict[str, float]
    metrics_after: Dict[str, float]
    improvement_pct: Dict[str, float] = field(default_factory=dict)
    error: Optional[str] = None
    
    def is_improvement(self, threshold_pct: float = 5.0) -> bool:
        """Verifica si hay mejora significativa (>threshold_pct%)."""
        for metric, improvement in self.improvement_pct.items():
            if improvement < -threshold_pct:  # Empeoró >5%
                return False
        return True
    
    def __str__(self) -> str:
        if self.success:
            improvements = ", ".join(
                f"{k}={v:+.1f}%" for k, v in self.improvement_pct.items()
            )
            return f"Success: {improvements}"
        else:
            return f"Failed: {self.error}"


@dataclass
class Episode:
    """
    Episodio completo de aprendizaje.
    
    Representa un ciclo:
    1. Anomalía detectada
    2. Acción propuesta
    3. Acción aplicada (opcional)
    4. Resultado evaluado
    
    Se almacena en NarrativeMemory con embedding FAISS.
    """
    
    # Metadata
    id: str
    timestamp: datetime
    status: EpisodeStatus
    
    # Content
    anomaly: Anomaly
    action: Optional[Action] = None
    result: Optional[Result] = None
    
    # Memory
    embedding: Optional[List[float]] = None  # Vector FAISS
    similar_episodes: List[str] = field(default_factory=list)  # IDs de episodios similares
    
    # Rollback info
    config_hash_before: Optional[str] = None
    config_hash_after: Optional[str] = None
    rolled_back: bool = False
    
    # Metadata adicional
    tags: List[str] = field(default_factory=list)
    notes: str = ""
    
    @classmethod
    def create_from_anomaly(cls, anomaly: Anomaly) -> "Episode":
        """Crea episodio nuevo desde anomalía."""
        episode_id = cls._generate_id(anomaly)
        return cls(
            id=episode_id,
            timestamp=datetime.now(),
            status=EpisodeStatus.OPEN,
            anomaly=anomaly,
            tags=[anomaly.type.value],
        )
    
    @staticmethod
    def _generate_id(anomaly: Anomaly) -> str:
        """Genera ID único para episodio."""
        timestamp = datetime.now().isoformat()
        content = f"{timestamp}_{anomaly.type.value}_{anomaly.metric_name}"
        hash_obj = hashlib.sha256(content.encode())
        return f"ep_{hash_obj.hexdigest()[:16]}"
    
    def propose_action(self, action: Action) -> None:
        """Registra acción propuesta."""
        self.action = action
        self.status = EpisodeStatus.ACTION_PROPOSED
    
    def apply_action(self, config_hash: str) -> None:
        """Marca acción como aplicada."""
        self.config_hash_after = config_hash
        self.status = EpisodeStatus.ACTION_APPLIED
    
    def close_with_result(self, result: Result) -> None:
        """Cierra episodio con resultado."""
        self.result = result
        
        if not result.success:
            self.status = EpisodeStatus.FAILED
        elif result.is_improvement():
            self.status = EpisodeStatus.RESOLVED
        else:
            self.status = EpisodeStatus.CONTRAPRODUCTIVE
    
    def mark_rolled_back(self) -> None:
        """Marca episodio como revertido."""
        self.rolled_back = True
        self.status = EpisodeStatus.ROLLED_BACK
    
    def to_dict(self) -> Dict:
        """Serializa a dict para storage."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status.value,
            "anomaly": {
                "type": self.anomaly.type.value,
                "severity": self.anomaly.severity,
                "metric_name": self.anomaly.metric_name,
                "current_value": self.anomaly.current_value,
                "expected_value": self.anomaly.expected_value,
                "threshold": self.anomaly.threshold,
                "context": self.anomaly.context,
            },
            "action": {
                "name": self.action.name,
                "target_component": self.action.target_component,
                "config_fragment": self.action.config_fragment,
                "reason": self.action.reason,
                "confidence": self.action.confidence,
            } if self.action else None,
            "result": {
                "success": self.result.success,
                "metrics_before": self.result.metrics_before,
                "metrics_after": self.result.metrics_after,
                "improvement_pct": self.result.improvement_pct,
                "error": self.result.error,
            } if self.result else None,
            "config_hash_before": self.config_hash_before,
            "config_hash_after": self.config_hash_after,
            "rolled_back": self.rolled_back,
            "tags": self.tags,
            "notes": self.notes,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Episode":
        """Deserializa desde dict."""
        anomaly = Anomaly(
            type=AnomalyType(data["anomaly"]["type"]),
            severity=data["anomaly"]["severity"],
            metric_name=data["anomaly"]["metric_name"],
            current_value=data["anomaly"]["current_value"],
            expected_value=data["anomaly"]["expected_value"],
            threshold=data["anomaly"]["threshold"],
            context=data["anomaly"].get("context", {}),
        )
        
        action = None
        if data.get("action"):
            action = Action(
                name=data["action"]["name"],
                target_component=data["action"]["target_component"],
                config_fragment=data["action"]["config_fragment"],
                reason=data["action"]["reason"],
                confidence=data["action"].get("confidence", 0.0),
            )
        
        result = None
        if data.get("result"):
            result = Result(
                success=data["result"]["success"],
                metrics_before=data["result"]["metrics_before"],
                metrics_after=data["result"]["metrics_after"],
                improvement_pct=data["result"].get("improvement_pct", {}),
                error=data["result"].get("error"),
            )
        
        return cls(
            id=data["id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            status=EpisodeStatus(data["status"]),
            anomaly=anomaly,
            action=action,
            result=result,
            config_hash_before=data.get("config_hash_before"),
            config_hash_after=data.get("config_hash_after"),
            rolled_back=data.get("rolled_back", False),
            tags=data.get("tags", []),
            notes=data.get("notes", ""),
        )
    
    def to_narrative_text(self) -> str:
        """Genera texto narrativo para embedding."""
        parts = [
            f"Problem: {self.anomaly}",
        ]
        
        if self.action:
            parts.append(f"Action: {self.action}")
        
        if self.result:
            parts.append(f"Result: {self.result}")
        
        if self.tags:
            parts.append(f"Tags: {', '.join(self.tags)}")
        
        return " | ".join(parts)
    
    def __str__(self) -> str:
        return f"Episode {self.id} [{self.status.value}]: {self.anomaly.type.value}"


# Exports
__all__ = [
    "Episode",
    "Anomaly",
    "Action",
    "Result",
    "EpisodeStatus",
    "AnomalyType",
]
