"""
SARAi HLCS v0.2 - Ignorance Consciousness
==========================================

Consciencia de ignorancia: "Sé lo que NO sé"
- Known Unknowns (sabemos que no sabemos)
- Unknown Unknowns (ni siquiera sabemos que existen)
- Uncertainty quantification
- Confidence calibration
- Humble decision-making

"La sabiduría comienza reconociendo la propia ignorancia"

Version: 0.2.0
Author: SARAi Team
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Set
from enum import Enum

import logging
import statistics

logger = logging.getLogger(__name__)


class UncertaintyType(Enum):
    """Tipos de incertidumbre."""
    ALEATORIC = "aleatoric"  # Incertidumbre inherente (datos ruidosos)
    EPISTEMIC = "epistemic"  # Incertidumbre reducible (falta conocimiento)
    ONTOLOGICAL = "ontological"  # Incertidumbre conceptual (problema mal definido)


@dataclass
class KnownUnknown:
    """Conocimiento explícito de ignorancia."""
    domain: str  # Área de conocimiento (e.g., "RAM_prediction", "cache_behavior")
    what_we_dont_know: str  # Descripción de la ignorancia
    uncertainty_type: UncertaintyType
    confidence_in_ignorance: float  # 0.0-1.0 (qué tan seguros estamos de no saber)
    potential_impact: str  # "low", "medium", "high", "critical"
    learn_by: Optional[str] = None  # Cómo podríamos aprenderlo
    timestamp: datetime = field(default_factory=datetime.now)
    
    def __str__(self) -> str:
        return (
            f"[{self.domain}] {self.what_we_dont_know} "
            f"(impact: {self.potential_impact}, type: {self.uncertainty_type.value})"
        )


@dataclass
class UnknownUnknown:
    """Registro de descubrimiento de desconocidos inesperados."""
    discovery_trigger: str  # Qué evento reveló esta ignorancia
    new_domain: str  # Nueva área de conocimiento descubierta
    surprise_level: float  # 0.0-1.0 (qué tan inesperado fue)
    timestamp: datetime = field(default_factory=datetime.now)
    promoted_to_known: bool = False  # Si ya se convirtió en KnownUnknown
    
    def __str__(self) -> str:
        status = "✓" if self.promoted_to_known else "⚠"
        return (
            f"{status} Discovered [{self.new_domain}] via {self.discovery_trigger} "
            f"(surprise: {self.surprise_level:.2f})"
        )


@dataclass
class UncertaintyQuantification:
    """Cuantificación de incertidumbre en una decisión."""
    decision_id: str
    epistemic_uncertainty: float  # 0.0-1.0
    aleatoric_uncertainty: float  # 0.0-1.0
    total_uncertainty: float  # Combinación de ambas
    confidence_calibrated: bool  # Si la confianza está bien calibrada
    known_unknowns_count: int
    recommended_action: str  # "proceed", "gather_data", "defer_to_human"
    timestamp: datetime = field(default_factory=datetime.now)


class IgnoranceConsciousness:
    """
    HLCS v0.2 Ignorance Consciousness
    
    Mapea y cuantifica lo que NO sabemos:
    - Known Unknowns: Explícitamente identificados
    - Unknown Unknowns: Descubiertos por anomalías/sorpresas
    - Uncertainty Quantification: Epistemic + Aleatoric
    - Confidence Calibration: Adjust overconfidence bias
    
    Features:
    - Bayesian uncertainty estimation
    - Surprise detection (nuevos unknowns)
    - Humble decision-making (defer cuando incertidumbre > threshold)
    - Learning recommendations
    
    Example:
        >>> ignorance = IgnoranceConsciousness()
        >>> ignorance.register_known_unknown(
        ...     domain="cache_hit_rate",
        ...     what="Comportamiento en traffic spikes",
        ...     type=UncertaintyType.EPISTEMIC,
        ...     impact="high"
        ... )
        >>> uncertainty = ignorance.quantify_decision_uncertainty(decision_data)
        >>> print(uncertainty.recommended_action)
        "gather_data"  # Incertidumbre demasiado alta
    """
    
    def __init__(
        self,
        uncertainty_threshold: float = 0.6,
        surprise_threshold: float = 0.7,
        max_known_unknowns: int = 100,
    ):
        """
        Args:
            uncertainty_threshold: Umbral para defer decisions (0.0-1.0)
            surprise_threshold: Umbral para detectar unknown unknowns (0.0-1.0)
            max_known_unknowns: Límite de known unknowns almacenados
        """
        self.uncertainty_threshold = uncertainty_threshold
        self.surprise_threshold = surprise_threshold
        self.max_known_unknowns = max_known_unknowns
        
        # Registros de ignorancia
        self.known_unknowns: Dict[str, List[KnownUnknown]] = {}
        self.unknown_unknowns: List[UnknownUnknown] = []
        
        # Calibración de confianza
        self.confidence_calibration_history: List[Dict] = []
        self.overconfidence_bias = 0.0  # Ajuste si sobreestimamos confianza
        
        logger.info(
            "Ignorance Consciousness initialized: uncertainty_threshold=%.2f, "
            "surprise_threshold=%.2f",
            uncertainty_threshold, surprise_threshold
        )
    
    def register_known_unknown(
        self,
        domain: str,
        what_we_dont_know: str,
        uncertainty_type: UncertaintyType,
        potential_impact: str,
        confidence_in_ignorance: float = 0.8,
        learn_by: Optional[str] = None,
    ) -> KnownUnknown:
        """
        Registra un known unknown explícitamente.
        
        Args:
            domain: Área de conocimiento (e.g., "RAM_usage", "cache_behavior")
            what_we_dont_know: Descripción de lo que no sabemos
            uncertainty_type: Tipo de incertidumbre
            potential_impact: "low", "medium", "high", "critical"
            confidence_in_ignorance: Qué tan seguros estamos de no saber (0.0-1.0)
            learn_by: Cómo podríamos aprender esto
        
        Returns:
            KnownUnknown registrado
        """
        known_unknown = KnownUnknown(
            domain=domain,
            what_we_dont_know=what_we_dont_know,
            uncertainty_type=uncertainty_type,
            confidence_in_ignorance=confidence_in_ignorance,
            potential_impact=potential_impact,
            learn_by=learn_by,
        )
        
        # Almacenar por dominio
        if domain not in self.known_unknowns:
            self.known_unknowns[domain] = []
        
        self.known_unknowns[domain].append(known_unknown)
        
        # Mantener límite
        if len(self.known_unknowns[domain]) > self.max_known_unknowns:
            # Remover los más antiguos con menor impacto
            self.known_unknowns[domain] = sorted(
                self.known_unknowns[domain],
                key=lambda ku: (
                    {"low": 0, "medium": 1, "high": 2, "critical": 3}[ku.potential_impact],
                    ku.timestamp
                ),
                reverse=True
            )[:self.max_known_unknowns]
        
        logger.info("Registered known unknown: %s", known_unknown)
        
        return known_unknown
    
    def detect_unknown_unknown(
        self,
        anomaly_data: Dict,
        existing_domains: Set[str],
    ) -> Optional[UnknownUnknown]:
        """
        Detecta unknown unknowns por sorpresas/anomalías.
        
        Args:
            anomaly_data: Datos de anomalía detectada
                         Debe incluir: {"type", "severity", "domain", "surprise_score"}
            existing_domains: Dominios conocidos actualmente
        
        Returns:
            UnknownUnknown si se detecta algo inesperado, None si no
        """
        anomaly_domain = anomaly_data.get("domain", "unknown")
        surprise_score = anomaly_data.get("surprise_score", 0.0)
        
        # Detectar si es un dominio nuevo o altamente sorprendente
        is_new_domain = anomaly_domain not in existing_domains
        is_highly_surprising = surprise_score >= self.surprise_threshold
        
        if not (is_new_domain or is_highly_surprising):
            return None
        
        # Registrar unknown unknown
        unknown_unknown = UnknownUnknown(
            discovery_trigger=anomaly_data.get("type", "unknown_anomaly"),
            new_domain=anomaly_domain,
            surprise_level=surprise_score,
        )
        
        self.unknown_unknowns.append(unknown_unknown)
        
        logger.warning("Unknown unknown detected: %s", unknown_unknown)
        
        # Auto-promoción a known unknown si es crítico
        if anomaly_data.get("severity") in ["high", "critical"]:
            self._promote_to_known_unknown(unknown_unknown, anomaly_data)
        
        return unknown_unknown
    
    def _promote_to_known_unknown(
        self, unknown: UnknownUnknown, anomaly_data: Dict
    ) -> None:
        """Promociona un unknown unknown a known unknown."""
        self.register_known_unknown(
            domain=unknown.new_domain,
            what_we_dont_know=f"Discovered via {unknown.discovery_trigger}",
            uncertainty_type=UncertaintyType.EPISTEMIC,  # Asumimos que es reducible
            potential_impact=anomaly_data.get("severity", "high"),
            confidence_in_ignorance=unknown.surprise_level,
            learn_by="Collect more samples in this domain",
        )
        
        unknown.promoted_to_known = True
        
        logger.info("Promoted unknown unknown to known: %s", unknown.new_domain)
    
    def quantify_decision_uncertainty(
        self,
        decision_data: Dict,
    ) -> UncertaintyQuantification:
        """
        Cuantifica incertidumbre en una decisión.
        
        Args:
            decision_data: Datos de decisión
                          Debe incluir: {"decision_id", "domain", "samples", 
                                        "variance", "model_confidence"}
        
        Returns:
            UncertaintyQuantification con recomendación
        """
        decision_id = decision_data.get("decision_id", "unknown")
        domain = decision_data.get("domain", "general")
        
        # Calcular epistemic uncertainty (reducible con más conocimiento)
        epistemic = self._calculate_epistemic_uncertainty(decision_data, domain)
        
        # Calcular aleatoric uncertainty (inherente a los datos)
        aleatoric = self._calculate_aleatoric_uncertainty(decision_data)
        
        # Combinar incertidumbres (independientes, usar norma)
        total_uncertainty = (epistemic**2 + aleatoric**2) ** 0.5
        
        # Calibrar confianza
        calibrated, is_calibrated = self._calibrate_confidence(
            decision_data.get("model_confidence", 0.5), total_uncertainty
        )
        
        # Contar known unknowns relevantes
        known_unknowns_count = len(self.known_unknowns.get(domain, []))
        
        # Recomendar acción
        recommended_action = self._recommend_action(
            total_uncertainty, known_unknowns_count, decision_data
        )
        
        quantification = UncertaintyQuantification(
            decision_id=decision_id,
            epistemic_uncertainty=epistemic,
            aleatoric_uncertainty=aleatoric,
            total_uncertainty=total_uncertainty,
            confidence_calibrated=is_calibrated,
            known_unknowns_count=known_unknowns_count,
            recommended_action=recommended_action,
        )
        
        logger.info(
            "Decision uncertainty: id=%s, total=%.3f, epistemic=%.3f, aleatoric=%.3f, "
            "action=%s",
            decision_id, total_uncertainty, epistemic, aleatoric, recommended_action
        )
        
        return quantification
    
    def _calculate_epistemic_uncertainty(
        self, decision_data: Dict, domain: str
    ) -> float:
        """
        Calcula incertidumbre epistémica (falta de conocimiento).
        
        Factores:
        - Número de muestras (más muestras = menos incertidumbre)
        - Known unknowns en el dominio
        - Historial de calibración
        """
        samples = decision_data.get("samples", 1)
        
        # Factor 1: Sample size (decae con raíz cuadrada)
        sample_uncertainty = 1.0 / (1.0 + (samples ** 0.5))
        
        # Factor 2: Known unknowns
        known_unknowns_list = self.known_unknowns.get(domain, [])
        critical_unknowns = sum(
            1 for ku in known_unknowns_list if ku.potential_impact == "critical"
        )
        high_unknowns = sum(
            1 for ku in known_unknowns_list if ku.potential_impact == "high"
        )
        
        known_unknowns_penalty = min(
            (critical_unknowns * 0.3 + high_unknowns * 0.15), 0.5
        )
        
        # Factor 3: Overconfidence bias
        bias_penalty = abs(self.overconfidence_bias) * 0.2
        
        # Combinar factores
        epistemic = min(
            sample_uncertainty + known_unknowns_penalty + bias_penalty, 1.0
        )
        
        return epistemic
    
    def _calculate_aleatoric_uncertainty(self, decision_data: Dict) -> float:
        """
        Calcula incertidumbre aleatórica (inherente a datos).
        
        Basado en varianza observada.
        """
        variance = decision_data.get("variance", 0.0)
        
        # Normalizar varianza a [0, 1]
        # Asumimos que varianza > 0.25 es alta incertidumbre
        aleatoric = min(variance / 0.25, 1.0)
        
        return aleatoric
    
    def _calibrate_confidence(
        self, model_confidence: float, total_uncertainty: float
    ) -> tuple[float, bool]:
        """
        Calibra confianza del modelo ajustando por overconfidence bias.
        
        Returns:
            (calibrated_confidence, is_well_calibrated)
        """
        # Ajustar confianza por bias histórico
        calibrated = model_confidence - self.overconfidence_bias
        calibrated = max(0.0, min(calibrated, 1.0))
        
        # Verificar si está bien calibrada
        # Bien calibrada si confianza + incertidumbre ≈ 1.0
        expected_total = calibrated + total_uncertainty
        is_well_calibrated = 0.8 <= expected_total <= 1.2
        
        # Actualizar bias si no está calibrado
        if not is_well_calibrated:
            # Si confianza + incertidumbre > 1.0 → estamos sobreestimando confianza
            if expected_total > 1.0:
                self.overconfidence_bias += 0.05
            else:
                self.overconfidence_bias -= 0.05
            
            # Clamp bias
            self.overconfidence_bias = max(-0.3, min(self.overconfidence_bias, 0.3))
        
        # Registrar para historial
        self.confidence_calibration_history.append({
            "timestamp": datetime.now().isoformat(),
            "model_confidence": model_confidence,
            "total_uncertainty": total_uncertainty,
            "calibrated_confidence": calibrated,
            "is_calibrated": is_well_calibrated,
            "bias": self.overconfidence_bias,
        })
        
        # Mantener solo últimos 100 registros
        if len(self.confidence_calibration_history) > 100:
            self.confidence_calibration_history = \
                self.confidence_calibration_history[-100:]
        
        return calibrated, is_well_calibrated
    
    def _recommend_action(
        self,
        total_uncertainty: float,
        known_unknowns_count: int,
        decision_data: Dict,
    ) -> str:
        """
        Recomienda acción basada en incertidumbre.
        
        Returns:
            "proceed" | "gather_data" | "defer_to_human"
        """
        # Criterio 1: Incertidumbre total
        if total_uncertainty >= self.uncertainty_threshold:
            # Criterio 2: ¿Podemos reducirla?
            if known_unknowns_count > 0:
                return "gather_data"  # Hay conocimiento que podemos adquirir
            else:
                return "defer_to_human"  # Incertidumbre irreducible
        
        # Criterio 3: Known unknowns críticos
        domain = decision_data.get("domain", "general")
        critical_unknowns = sum(
            1 for ku in self.known_unknowns.get(domain, [])
            if ku.potential_impact == "critical"
        )
        
        if critical_unknowns > 0:
            return "gather_data"
        
        # Safe to proceed
        return "proceed"
    
    def get_ignorance_summary(self) -> Dict:
        """Obtiene resumen del estado de ignorancia."""
        # Estadísticas de known unknowns
        total_known_unknowns = sum(len(kus) for kus in self.known_unknowns.values())
        
        by_impact = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        by_type = {ut.value: 0 for ut in UncertaintyType}
        
        for domain_unknowns in self.known_unknowns.values():
            for ku in domain_unknowns:
                by_impact[ku.potential_impact] += 1
                by_type[ku.uncertainty_type.value] += 1
        
        # Unknown unknowns
        total_unknown_unknowns = len(self.unknown_unknowns)
        promoted_count = sum(1 for uu in self.unknown_unknowns if uu.promoted_to_known)
        
        # Calibración
        recent_calibration = self.confidence_calibration_history[-10:] \
            if self.confidence_calibration_history else []
        
        calibration_rate = sum(
            1 for cal in recent_calibration if cal["is_calibrated"]
        ) / len(recent_calibration) if recent_calibration else 0.0
        
        return {
            "known_unknowns": {
                "total": total_known_unknowns,
                "by_impact": by_impact,
                "by_type": by_type,
                "domains": list(self.known_unknowns.keys()),
            },
            "unknown_unknowns": {
                "total": total_unknown_unknowns,
                "promoted_to_known": promoted_count,
                "pending": total_unknown_unknowns - promoted_count,
            },
            "confidence_calibration": {
                "current_bias": self.overconfidence_bias,
                "calibration_rate": calibration_rate,
                "history_size": len(self.confidence_calibration_history),
            },
            "thresholds": {
                "uncertainty": self.uncertainty_threshold,
                "surprise": self.surprise_threshold,
            },
        }
    
    def get_learning_recommendations(self) -> List[Dict]:
        """
        Genera recomendaciones de aprendizaje basadas en ignorancia.
        
        Returns:
            Lista de recomendaciones ordenadas por prioridad
        """
        recommendations = []
        
        # Prioridad 1: Critical known unknowns
        for domain, unknowns in self.known_unknowns.items():
            critical = [ku for ku in unknowns if ku.potential_impact == "critical"]
            
            for ku in critical:
                recommendations.append({
                    "priority": "critical",
                    "domain": domain,
                    "what_to_learn": ku.what_we_dont_know,
                    "how_to_learn": ku.learn_by or "Investigate manually",
                    "uncertainty_type": ku.uncertainty_type.value,
                })
        
        # Prioridad 2: High impact epistemic unknowns (reducibles)
        for domain, unknowns in self.known_unknowns.items():
            high_epistemic = [
                ku for ku in unknowns
                if ku.potential_impact == "high"
                and ku.uncertainty_type == UncertaintyType.EPISTEMIC
            ]
            
            for ku in high_epistemic:
                recommendations.append({
                    "priority": "high",
                    "domain": domain,
                    "what_to_learn": ku.what_we_dont_know,
                    "how_to_learn": ku.learn_by or "Collect more data",
                    "uncertainty_type": ku.uncertainty_type.value,
                })
        
        # Prioridad 3: Unknown unknowns no promovidos
        for uu in self.unknown_unknowns:
            if not uu.promoted_to_known and uu.surprise_level >= self.surprise_threshold:
                recommendations.append({
                    "priority": "medium",
                    "domain": uu.new_domain,
                    "what_to_learn": f"Explore new domain: {uu.new_domain}",
                    "how_to_learn": "Monitor and collect samples",
                    "uncertainty_type": "unknown",
                })
        
        # Ordenar por prioridad
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        recommendations.sort(key=lambda r: priority_order.get(r["priority"], 99))
        
        return recommendations


# Exports
__all__ = [
    "IgnoranceConsciousness",
    "KnownUnknown",
    "UnknownUnknown",
    "UncertaintyQuantification",
    "UncertaintyType",
]
