"""Selector de cuantización dinámica para SARAi_AGI.

La lógica proviene del módulo ``model_pool_v35_dynamic`` del repositorio
histórico. Se mantuvieron las heurísticas clave (historial de éxito,
complejidad de la tarea, longitud del prompt y memoria disponible), pero
se expusieron mediante una API independiente para facilitar su reutilización
junto a la nueva arquitectura de ``SARAi_AGI``.

El objetivo es que otros componentes (por ejemplo el gestor de modelos)
puedan decidir de forma determinista la cuantización óptima antes de
invocar al modelo, manteniendo el consumo de memoria dentro de límites
seguros sin degradar la calidad de respuesta.
"""

from __future__ import annotations

import logging
import math
import statistics
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

from ..configuration import get_section, load_settings

logger = logging.getLogger(__name__)


# ========== CONSTANTES ==========

QUANTIZATION_BENCHMARKS: Dict[str, Dict[str, float]] = {
    "IQ3_XXS": {"latency_ms": 1800, "quality": 0.78},
    "Q4_K_M": {"latency_ms": 2100, "quality": 0.92},
    "Q5_K_M": {"latency_ms": 2400, "quality": 0.96},
}


@dataclass
class QuantizationMetadata:
    """Metadatos devueltos junto a la decisión de cuantización."""

    confidence: float
    ram_required_mb: float
    estimated_latency_ms: float
    rationale: str
    timestamp: float = field(default_factory=time.time)
    additional: Dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> Dict[str, Any]:
        payload = {
            "confidence": self.confidence,
            "ram_required_mb": self.ram_required_mb,
            "estimated_latency_ms": self.estimated_latency_ms,
            "rationale": self.rationale,
            "timestamp": self.timestamp,
        }
        payload.update(self.additional)
        return payload


class QuantizationLevel(str, Enum):
    """Niveles de cuantización disponibles."""

    IQ3_XXS = "IQ3_XXS"
    Q4_K_M = "Q4_K_M"
    Q5_K_M = "Q5_K_M"


@dataclass
class QuantizationDecision:
    """Respuesta de :class:`DynamicQuantizationSelector`."""

    level: QuantizationLevel
    metadata: QuantizationMetadata


class DynamicQuantizationSelector:
    """Seleccionador heurístico de cuantización.

    La implementación sigue las mismas ideas del repositorio original, pero
    se exponen algunos puntos de extensión para tests (p. ej. inyectar
    métricas de RAM disponibles o historial de uso).
    """

    def __init__(
        self,
        min_ram_free_gb: float = 1.5,
        force_quality_threshold: float = 0.9,
        history_window: int = 200,
    ) -> None:
        self.min_ram_free_gb = max(0.5, min_ram_free_gb)
        self.force_quality_threshold = max(0.0, min(force_quality_threshold, 1.0))
        self.history_window = max(1, history_window)

        # Historial de uso por nivel.
        self.usage_history: Dict[QuantizationLevel, Dict[str, float]] = {
            QuantizationLevel.IQ3_XXS: {"count": 0, "success_rate": 0.0},
            QuantizationLevel.Q4_K_M: {"count": 0, "success_rate": 0.0},
            QuantizationLevel.Q5_K_M: {"count": 0, "success_rate": 0.0},
        }

        self.latency_history: Dict[QuantizationLevel, list[float]] = {
            QuantizationLevel.IQ3_XXS: [],
            QuantizationLevel.Q4_K_M: [],
            QuantizationLevel.Q5_K_M: [],
        }

    # ------------------------------------------------------------------
    # Entrada principal
    # ------------------------------------------------------------------

    def select_quantization(
        self,
        prompt: str,
        task_complexity: float,
        quality_request: Optional[float] = None,
        ram_available_gb: Optional[float] = None,
        safety_override: bool = False,
    ) -> QuantizationDecision:
        """Obtiene el nivel sugerido de cuantización.

        Args:
            prompt: Texto completo recibido.
            task_complexity: Complejidad estimada (0-1) calculada por TRM.
            quality_request: Nivel de calidad solicitado explícitamente.
            ram_available_gb: RAM libre detectada (usado para evitar OOM).
            safety_override: Si ``True`` fuerza el modo seguro (Q4 o Q5).
        """

        tokens_estimated = max(1, len(prompt) // 4)
        quality_request = quality_request if quality_request is not None else task_complexity

        # Auto-detect RAM if not provided and psutil available
        if ram_available_gb is None:
            if HAS_PSUTIL:
                try:
                    mem = psutil.virtual_memory()
                    ram_available_gb = mem.available / (1024**3)
                except Exception as exc:
                    logger.debug("RAM detection failed: %s", exc)
                    ram_available_gb = self.min_ram_free_gb
            else:
                ram_available_gb = self.min_ram_free_gb

        ram_factor = self._compute_ram_factor(ram_available_gb)
        history_factor = self._compute_history_factor()
        complexity_factor = max(0.0, min(1.0, task_complexity))

        weights = {
            "tokens": 0.35,
            "complexity": 0.35,
            "history": 0.20,
            "ram": 0.10,
        }

        score = (
            weights["tokens"] * self._normalise_tokens(tokens_estimated) +
            weights["complexity"] * complexity_factor +
            weights["history"] * history_factor +
            weights["ram"] * ram_factor
        )

        rationale_parts = [
            f"tokens_norm={self._normalise_tokens(tokens_estimated):.2f}",
            f"complexity={complexity_factor:.2f}",
            f"history={history_factor:.2f}",
            f"ram_factor={ram_factor:.2f}",
            f"score={score:.2f}",
        ]

        if safety_override:
            level = QuantizationLevel.Q4_K_M
            rationale_parts.append("safety_override=True")
        elif quality_request >= self.force_quality_threshold:
            level = QuantizationLevel.Q5_K_M
            rationale_parts.append("force_quality=True")
        elif score < 0.45:
            level = QuantizationLevel.IQ3_XXS
        elif score < 0.7:
            level = QuantizationLevel.Q4_K_M
        else:
            level = QuantizationLevel.Q5_K_M

        latency_est = QUANTIZATION_BENCHMARKS[level.value]["latency_ms"]
        metadata = QuantizationMetadata(
            confidence=min(0.99, 0.5 + score / 2),
            ram_required_mb=self._ram_by_level(level),
            estimated_latency_ms=latency_est,
            rationale="; ".join(rationale_parts),
        )
        metadata.additional.update({
            "tokens_estimated": tokens_estimated,
            "quality_request": quality_request,
            "ram_available_gb": ram_available_gb,
        })

        logger.debug("Selector quantization → level=%s metadata=%s", level, metadata.to_payload())
        return QuantizationDecision(level=level, metadata=metadata)

    # ------------------------------------------------------------------
    # Métodos auxiliares
    # ------------------------------------------------------------------

    def update_usage_history(
        self,
        level: QuantizationLevel,
        success: bool,
        latency_ms: Optional[float] = None,
    ) -> None:
        """Actualiza el historial de éxito tras una inferencia."""

        stats = self.usage_history[level]
        stats["count"] += 1

        alpha = 0.1
        current = float(stats.get("success_rate", 0.0))
        stats["success_rate"] = (1 - alpha) * current + alpha * (1.0 if success else 0.0)

        if latency_ms is not None:
            history = self.latency_history[level]
            history.append(latency_ms)
            if len(history) > self.history_window:
                history.pop(0)

    def get_usage_stats(self) -> Dict[str, Dict[str, float]]:
        total = sum(float(hist.get("count", 0)) for hist in self.usage_history.values())
        result: Dict[str, Dict[str, float]] = {}
        for level, hist in self.usage_history.items():
            count = float(hist.get("count", 0))
            success = float(hist.get("success_rate", 0.0))
            result[level.value] = {
                "count": count,
                "success_rate": success,
                "percentage": count / total if total else 0.0,
            }
        return result

    # -- Factores -------------------------------------------------------

    def _normalise_tokens(self, tokens: int) -> float:
        return min(1.0, math.log(tokens + 1, 10))

    def _compute_history_factor(self) -> float:
        counts = [hist.get("count", 0) for hist in self.usage_history.values()]
        if not any(counts):
            return 0.5

        success_rates = []
        for hist in self.usage_history.values():
            count = hist.get("count", 0)
            success = hist.get("success_rate", 0)
            if count <= 0:
                continue
            success_rates.append(success / count)

        if not success_rates:
            return 0.5

        return statistics.mean(success_rates)

    def _compute_ram_factor(self, ram_available_gb: float) -> float:
        if ram_available_gb >= self.min_ram_free_gb + 1:
            return 1.0
        if ram_available_gb <= 0.5:
            return 0.0
        return (ram_available_gb - 0.5) / (self.min_ram_free_gb + 0.5)

    def _ram_by_level(self, level: QuantizationLevel) -> float:
        if level == QuantizationLevel.IQ3_XXS:
            return 450.0
        if level == QuantizationLevel.Q4_K_M:
            return 760.0
        return 980.0


# ========== FACTORÍA ==========


def create_dynamic_quantization_selector(
    min_ram_free_gb: float = 1.5,
    force_quality_threshold: float = 0.9,
) -> DynamicQuantizationSelector:
    settings = load_settings()
    quant_cfg = get_section(settings, "quantization", default={
        "min_ram_free_gb": min_ram_free_gb,
        "force_quality_threshold": force_quality_threshold,
    })

    # Aceptamos alias en español.
    quant_cfg.setdefault("min_ram_free_gb", quant_cfg.get("min_ram_libre_gb", min_ram_free_gb))
    quant_cfg.setdefault("force_quality_threshold", quant_cfg.get("umbral_calidad", force_quality_threshold))

    return DynamicQuantizationSelector(
        min_ram_free_gb=float(quant_cfg.get("min_ram_free_gb", min_ram_free_gb)),
        force_quality_threshold=float(quant_cfg.get("force_quality_threshold", force_quality_threshold)),
    )


def load_quantization_config(settings: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Carga la sección de cuantización desde el archivo YAML.

    Args:
        settings: Diccionario pre-cargado. Si no se entrega se llamará a
            :func:`load_settings`.
    """

    base = settings if settings is not None else load_settings()
    section = get_section(base, "quantization", default={})

    if not section:
        # Intentar lectura de alias en español.
        section = base.get("quantizacion", {}) if isinstance(base, dict) else {}

    return {
        "min_ram_free_gb": float(section.get("min_ram_free_gb", 1.5)),
        "force_quality_threshold": float(section.get("force_quality_threshold", 0.9)),
        "enable_dynamic_quantization": bool(section.get("enable_dynamic_quantization", True)),
    }


__all__ = [
    "QuantizationLevel",
    "QuantizationMetadata",
    "QuantizationDecision",
    "DynamicQuantizationSelector",
    "create_dynamic_quantization_selector",
    "load_quantization_config",
]
