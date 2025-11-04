"""
SARAi HLCS v0.2 - Meta-Consciousness Layer
===========================================

Consciencia meta-cognitiva con temporal awareness:
- Self-reflection en múltiples escalas temporales
- Self-doubt scoring basado en tendencias
- Existential purpose alignment
- Meta-learning detection
- Role evolution tracking

"¿Estoy siendo efectivo? ¿Estoy cumpliendo mi propósito?"

Version: 0.2.0
Author: SARAi Team
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import logging
import statistics

logger = logging.getLogger(__name__)


@dataclass
class EffectivenessScore:
    """Score de efectividad en una ventana temporal."""
    window_name: str  # "immediate", "recent", "historical"
    score: float  # 0.0-1.0
    sample_size: int
    timestamp: datetime
    
    def __str__(self) -> str:
        return f"{self.window_name}: {self.score:.3f} ({self.sample_size} samples)"


@dataclass
class TrendAnalysis:
    """Análisis de tendencias entre ventanas temporales."""
    direction: str  # "improving", "declining", "stable", "volatile"
    magnitude: float  # Magnitud del cambio
    confidence: float  # 0.0-1.0
    concerns: List[str] = field(default_factory=list)
    
    def is_concerning(self) -> bool:
        """Verifica si la tendencia es preocupante."""
        return self.direction == "declining" or self.direction == "volatile"


@dataclass
class ExistentialReflection:
    """Reflexión existencial sobre propósito y alineación."""
    core_purpose: str
    current_alignment: float  # 0.0-1.0
    existential_confidence: float  # 0.0-1.0
    self_critique: List[str]
    growth_opportunities: List[str]
    timestamp: datetime
    
    def __str__(self) -> str:
        return (
            f"Purpose Alignment: {self.current_alignment:.2%} "
            f"(confidence: {self.existential_confidence:.2%})"
        )


class MetaConsciousnessV02:
    """
    HLCS v0.2 Meta-Consciousness Layer
    
    Implementa consciencia temporal multi-escala:
    - Immediate: Últimas 5 acciones (¿funciona ahora?)
    - Recent: Últimas 20 acciones (¿funciona últimamente?)
    - Historical: Últimas 100 acciones (¿funciono en general?)
    
    Features:
    - Self-doubt scoring basado en tendencias
    - Existential reflection sobre propósito
    - Meta-learning detection
    - Role evolution tracking
    
    Example:
        >>> meta = MetaConsciousnessV02()
        >>> reflection = await meta.evaluate_effectiveness(recent_actions)
        >>> print(reflection["self_doubt_level"])
        0.15  # Baja auto-duda = alta confianza
    """
    
    def __init__(
        self,
        immediate_window: int = 5,
        recent_window: int = 20,
        historical_window: int = 100,
        purpose_alignment_threshold: float = 0.75,
    ):
        """
        Args:
            immediate_window: Número de acciones para ventana inmediata
            recent_window: Número de acciones para ventana reciente
            historical_window: Número de acciones para ventana histórica
            purpose_alignment_threshold: Umbral mínimo de alineación con propósito
        """
        self.temporal_windows = {
            "immediate": immediate_window,
            "recent": recent_window,
            "history": historical_window,
        }
        
        self.purpose_alignment_threshold = purpose_alignment_threshold
        
        # Estado interno de identidad
        self.identity_evolution = {
            "role": "supervisor_cognitivo",
            "capabilities": ["monitor", "learn", "correct", "reflect"],
            "confidence_in_role": 0.95,
            "last_self_evaluation": None,
            "role_evolution_history": [],
        }
        
        # Core purpose
        self.core_purpose = (
            "Mantener la salud y efectividad del sistema SARAi "
            "mediante observación, aprendizaje y corrección autónoma"
        )
        
        logger.info(
            "Meta-Consciousness initialized: immediate=%d, recent=%d, historical=%d",
            immediate_window, recent_window, historical_window
        )
    
    async def evaluate_effectiveness(
        self, recent_actions: List[Dict]
    ) -> Dict:
        """
        Evalúa efectividad en múltiples escalas temporales.
        
        Args:
            recent_actions: Lista de acciones recientes con resultados
                           Cada acción debe tener: {"success": bool, "improvement_pct": float}
        
        Returns:
            Dict con scores por ventana, tendencia y self-doubt
        """
        if not recent_actions:
            logger.warning("No actions to evaluate")
            return {
                "immediate_score": 0.0,
                "recent_score": 0.0,
                "historical_score": 0.0,
                "trend": self._no_data_trend(),
                "self_doubt_level": 1.0,  # Máxima duda si no hay datos
            }
        
        # Calcular efectividad en cada ventana
        immediate = self._calculate_effectiveness_in_window(
            recent_actions, "immediate"
        )
        recent = self._calculate_effectiveness_in_window(
            recent_actions, "recent"
        )
        historical = self._calculate_effectiveness_in_window(
            recent_actions, "history"
        )
        
        # Analizar tendencias
        trend = self._analyze_trends(immediate, recent, historical)
        
        # Calcular self-doubt
        self_doubt = self._calculate_self_doubt(trend, immediate, recent, historical)
        
        # Log reflexión
        logger.info(
            "Effectiveness evaluation: immediate=%.3f, recent=%.3f, historical=%.3f, "
            "trend=%s, self_doubt=%.3f",
            immediate.score, recent.score, historical.score,
            trend.direction, self_doubt
        )
        
        # Actualizar historial de evolución si hay cambios significativos
        self._update_role_evolution(trend, self_doubt)
        
        return {
            "immediate_score": immediate.score,
            "recent_score": recent.score,
            "historical_score": historical.score,
            "trend": {
                "direction": trend.direction,
                "magnitude": trend.magnitude,
                "confidence": trend.confidence,
                "concerns": trend.concerns,
            },
            "self_doubt_level": self_doubt,
            "timestamp": datetime.now().isoformat(),
        }
    
    def _calculate_effectiveness_in_window(
        self, actions: List[Dict], window_name: str
    ) -> EffectivenessScore:
        """Calcula efectividad en una ventana temporal específica."""
        window_size = self.temporal_windows[window_name]
        window_actions = actions[-window_size:] if len(actions) >= window_size else actions
        
        if not window_actions:
            return EffectivenessScore(
                window_name=window_name,
                score=0.0,
                sample_size=0,
                timestamp=datetime.now()
            )
        
        # Calcular score basado en éxitos y mejoras
        successes = sum(1 for a in window_actions if a.get("success", False))
        improvements = [
            a.get("improvement_pct", 0.0) 
            for a in window_actions 
            if a.get("success", False)
        ]
        
        # Score compuesto: 50% tasa de éxito + 50% mejora promedio
        success_rate = successes / len(window_actions)
        avg_improvement = statistics.mean(improvements) if improvements else 0.0
        avg_improvement_normalized = min(max(avg_improvement / 100.0, -1.0), 1.0)
        
        # Score final (0.0-1.0)
        score = (success_rate * 0.5) + ((avg_improvement_normalized + 1.0) / 2.0 * 0.5)
        
        return EffectivenessScore(
            window_name=window_name,
            score=score,
            sample_size=len(window_actions),
            timestamp=datetime.now()
        )
    
    def _analyze_trends(
        self,
        immediate: EffectivenessScore,
        recent: EffectivenessScore,
        historical: EffectivenessScore,
    ) -> TrendAnalysis:
        """Analiza tendencias entre ventanas temporales."""
        scores = [immediate.score, recent.score, historical.score]
        
        # Detectar dirección
        if immediate.score > recent.score > historical.score:
            direction = "improving"
            magnitude = immediate.score - historical.score
            concerns = []
        elif immediate.score < recent.score < historical.score:
            direction = "declining"
            magnitude = historical.score - immediate.score
            concerns = [
                "Deterioro sostenido detectado",
                "Revisar estrategia de acciones",
            ]
        else:
            # Calcular volatilidad
            volatility = statistics.stdev(scores) if len(scores) > 1 else 0.0
            
            if volatility > 0.15:
                direction = "volatile"
                magnitude = volatility
                concerns = ["Alta variabilidad en efectividad", "Estabilización requerida"]
            else:
                direction = "stable"
                magnitude = volatility
                concerns = []
        
        # Confidence basado en sample sizes
        min_sample_size = min(
            immediate.sample_size, recent.sample_size, historical.sample_size
        )
        confidence = min(min_sample_size / self.temporal_windows["immediate"], 1.0)
        
        return TrendAnalysis(
            direction=direction,
            magnitude=magnitude,
            confidence=confidence,
            concerns=concerns,
        )
    
    def _calculate_self_doubt(
        self,
        trend: TrendAnalysis,
        immediate: EffectivenessScore,
        recent: EffectivenessScore,
        historical: EffectivenessScore,
    ) -> float:
        """
        Calcula nivel de auto-duda (0.0-1.0).
        
        Baja auto-duda (0.0-0.3) = Alta confianza en capacidad
        Alta auto-duda (0.7-1.0) = Baja confianza, necesita ayuda
        """
        # Factores de duda
        doubt_factors = []
        
        # Factor 1: Tendencia declinante
        if trend.direction == "declining":
            doubt_factors.append(0.4 * trend.magnitude)
        elif trend.direction == "volatile":
            doubt_factors.append(0.3 * trend.magnitude)
        
        # Factor 2: Score absoluto bajo
        avg_score = statistics.mean([immediate.score, recent.score, historical.score])
        if avg_score < 0.5:
            doubt_factors.append(0.3 * (0.5 - avg_score))
        
        # Factor 3: Falta de datos (incertidumbre)
        if immediate.sample_size < self.temporal_windows["immediate"]:
            uncertainty = 1.0 - (immediate.sample_size / self.temporal_windows["immediate"])
            doubt_factors.append(0.2 * uncertainty)
        
        # Factor 4: Concerns específicas
        if trend.concerns:
            doubt_factors.append(0.1 * len(trend.concerns) / 5.0)
        
        # Self-doubt total
        self_doubt = min(sum(doubt_factors), 1.0)
        
        return self_doubt
    
    def _update_role_evolution(self, trend: TrendAnalysis, self_doubt: float) -> None:
        """Actualiza historial de evolución del rol."""
        timestamp = datetime.now()
        
        # Registrar eventos significativos
        if trend.direction == "improving" and self_doubt < 0.2:
            self.identity_evolution["role_evolution_history"].append({
                "timestamp": timestamp.isoformat(),
                "event": "Mejora sostenida - capacidad de meta-aprendizaje demostrada",
                "confidence_change": +0.05,
            })
            self.identity_evolution["confidence_in_role"] = min(
                self.identity_evolution["confidence_in_role"] + 0.05, 1.0
            )
        
        elif trend.direction == "declining" and self_doubt > 0.6:
            self.identity_evolution["role_evolution_history"].append({
                "timestamp": timestamp.isoformat(),
                "event": "Deterioro detectado - necesita recalibración",
                "confidence_change": -0.10,
            })
            self.identity_evolution["confidence_in_role"] = max(
                self.identity_evolution["confidence_in_role"] - 0.10, 0.0
            )
        
        # Mantener solo últimos 50 eventos
        if len(self.identity_evolution["role_evolution_history"]) > 50:
            self.identity_evolution["role_evolution_history"] = \
                self.identity_evolution["role_evolution_history"][-50:]
        
        self.identity_evolution["last_self_evaluation"] = timestamp.isoformat()
    
    async def reflect_on_existence(
        self, effectiveness_data: Dict
    ) -> ExistentialReflection:
        """
        Reflexión existencial sobre propósito y alineación.
        
        "¿Estoy cumpliendo mi propósito? ¿Soy útil para SARAi?"
        
        Args:
            effectiveness_data: Datos de efectividad reciente
        
        Returns:
            ExistentialReflection con auto-crítica y oportunidades de crecimiento
        """
        # Alineación con propósito = score reciente
        current_alignment = effectiveness_data["recent_score"]
        
        # Confidence existencial basado en tendencia
        trend_direction = effectiveness_data["trend"]["direction"]
        if trend_direction == "improving":
            existential_confidence = 0.9
        elif trend_direction == "stable":
            existential_confidence = 0.7
        elif trend_direction == "declining":
            existential_confidence = 0.4
        else:  # volatile
            existential_confidence = 0.5
        
        # Auto-crítica basada en gaps
        self_critique = self._generate_self_critique(effectiveness_data)
        
        # Oportunidades de crecimiento
        growth_opportunities = self._identify_growth_areas(effectiveness_data)
        
        reflection = ExistentialReflection(
            core_purpose=self.core_purpose,
            current_alignment=current_alignment,
            existential_confidence=existential_confidence,
            self_critique=self_critique,
            growth_opportunities=growth_opportunities,
            timestamp=datetime.now(),
        )
        
        logger.info("Existential reflection: %s", reflection)
        
        return reflection
    
    def _generate_self_critique(self, effectiveness_data: Dict) -> List[str]:
        """Genera críticas constructivas basadas en datos."""
        critiques = []
        
        # Crítica sobre alignment
        if effectiveness_data["recent_score"] < self.purpose_alignment_threshold:
            critiques.append(
                f"Alineación con propósito por debajo del umbral "
                f"({effectiveness_data['recent_score']:.2%} < "
                f"{self.purpose_alignment_threshold:.2%})"
            )
        
        # Crítica sobre self-doubt
        if effectiveness_data["self_doubt_level"] > 0.5:
            critiques.append(
                f"Nivel de auto-duda elevado ({effectiveness_data['self_doubt_level']:.2%}), "
                "necesito más datos o recalibración"
            )
        
        # Crítica sobre tendencia
        if effectiveness_data["trend"]["direction"] == "declining":
            critiques.append(
                "Tendencia declinante detectada, necesito revisar estrategia"
            )
        
        # Crítica sobre volatilidad
        if effectiveness_data["trend"]["direction"] == "volatile":
            critiques.append(
                "Alta variabilidad en resultados, necesito estabilizar acciones"
            )
        
        if not critiques:
            critiques.append("Desempeño dentro de parámetros esperados")
        
        return critiques
    
    def _identify_growth_areas(self, effectiveness_data: Dict) -> List[str]:
        """Identifica oportunidades de mejora."""
        opportunities = []
        
        # Oportunidad basada en self-doubt
        if effectiveness_data["self_doubt_level"] > 0.3:
            opportunities.append(
                "Aumentar tamaño de muestra para reducir incertidumbre"
            )
        
        # Oportunidad basada en alignment
        if effectiveness_data["recent_score"] < 0.8:
            opportunities.append(
                "Optimizar criterios de selección de acciones"
            )
        
        # Oportunidad basada en tendencia
        trend_direction = effectiveness_data["trend"]["direction"]
        if trend_direction in ["declining", "volatile"]:
            opportunities.append(
                "Implementar meta-reasoner para decisiones más inteligentes (v0.3)"
            )
        
        # Oportunidad basada en concerns
        if effectiveness_data["trend"].get("concerns"):
            opportunities.append(
                "Activar monitoreo intensivo en áreas de preocupación"
            )
        
        if not opportunities:
            opportunities.append(
                "Continuar aprendizaje incremental sin cambios mayores"
            )
        
        return opportunities
    
    def _no_data_trend(self) -> TrendAnalysis:
        """Trend analysis cuando no hay datos."""
        return TrendAnalysis(
            direction="unknown",
            magnitude=0.0,
            confidence=0.0,
            concerns=["Sin datos suficientes para análisis"],
        )
    
    def get_identity_summary(self) -> Dict:
        """Obtiene resumen del estado de identidad actual."""
        return {
            "role": self.identity_evolution["role"],
            "capabilities": self.identity_evolution["capabilities"],
            "confidence_in_role": self.identity_evolution["confidence_in_role"],
            "last_self_evaluation": self.identity_evolution["last_self_evaluation"],
            "evolution_events_count": len(
                self.identity_evolution["role_evolution_history"]
            ),
            "recent_evolution": self.identity_evolution["role_evolution_history"][-5:]
            if self.identity_evolution["role_evolution_history"]
            else [],
        }


# Exports
__all__ = [
    "MetaConsciousnessV02",
    "EffectivenessScore",
    "TrendAnalysis",
    "ExistentialReflection",
]
