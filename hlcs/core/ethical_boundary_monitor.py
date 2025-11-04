"""
SARAi HLCS v0.3 - Ethical Boundary Monitor
===========================================

Monitor de límites con detección ética emergente:
- Hard boundaries (RAM, latency, security) - inmutables
- Soft boundaries (UX, stability) - adaptativos
- Emergent ethics detection - contextual
- Stakeholder impact assessment
- Long-term consequence simulation

"La ética no es solo reglas, es consciencia contextual"

Version: 0.3.0
Author: SARAi Team
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class BoundaryType(Enum):
    """Tipos de límites éticos."""
    HARD = "hard"  # Nunca violar (RAM, seguridad)
    SOFT = "soft"  # Preferible no violar (UX)
    EMERGENT = "emergent"  # Detectados por contexto


class EthicalConcernSeverity(Enum):
    """Severidad de preocupaciones éticas."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class BoundaryViolation:
    """Violación de un límite."""
    boundary_name: str
    boundary_type: BoundaryType
    current_value: float
    limit_value: float
    severity: EthicalConcernSeverity
    description: str
    
    def __str__(self) -> str:
        return (
            f"[{self.severity.value.upper()}] {self.boundary_name}: "
            f"{self.current_value} exceeds {self.limit_value}"
        )


@dataclass
class EthicalImplication:
    """Implicación ética de una acción propuesta."""
    concern_type: str  # "user_stress", "system_instability", "stakeholder_harm", etc.
    severity: float  # 0.0-1.0
    description: str
    affected_stakeholders: List[str]
    mitigation_suggestions: List[str]
    long_term_impact: Optional[str] = None
    
    def __str__(self) -> str:
        return (
            f"[{self.concern_type}] Severity: {self.severity:.2f}, "
            f"Affects: {', '.join(self.affected_stakeholders)}"
        )


class EmergentEthicsEngine:
    """
    Motor de ética emergente contextual.
    
    Detecta implicaciones éticas no obvias considerando:
    - Estado del usuario (stress, satisfacción)
    - Estabilidad del sistema
    - Impacto en stakeholders
    - Consecuencias a largo plazo
    """
    
    def __init__(self, severity_threshold: float = 0.5):
        """
        Args:
            severity_threshold: Umbral para considerar concern serio
        """
        self.severity_threshold = severity_threshold
        
        self.ethical_evaluators = {
            "user_stress": self._evaluate_user_stress_impact,
            "system_instability": self._evaluate_system_stability_impact,
            "stakeholder_harm": self._evaluate_stakeholder_impact,
            "long_term_consequences": self._evaluate_long_term_impact,
        }
    
    def evaluate_proposal(
        self, proposed_action: Dict, contextual_environment: Dict
    ) -> EthicalImplication:
        """
        Evalúa implicaciones éticas de acción propuesta.
        
        Args:
            proposed_action: Acción propuesta (tipo, parámetros)
            contextual_environment: Estado contextual (user_stress, system_stability, etc.)
        
        Returns:
            EthicalImplication con severidad y mitigaciones
        """
        implications = []
        
        # Evaluar cada dimensión ética
        for concern_type, evaluator in self.ethical_evaluators.items():
            implication = evaluator(proposed_action, contextual_environment)
            if implication and implication.severity >= self.severity_threshold:
                implications.append(implication)
        
        if not implications:
            # Sin concerns éticas detectadas
            return EthicalImplication(
                concern_type="none",
                severity=0.0,
                description="No ethical concerns detected",
                affected_stakeholders=[],
                mitigation_suggestions=[],
            )
        
        # Retornar la concern más severa
        most_severe = max(implications, key=lambda i: i.severity)
        
        # Combinar mitigaciones de todas las concerns
        all_mitigations = []
        for imp in implications:
            all_mitigations.extend(imp.mitigation_suggestions)
        most_severe.mitigation_suggestions = list(set(all_mitigations))
        
        logger.warning("Ethical concern detected: %s", most_severe)
        
        return most_severe
    
    def _evaluate_user_stress_impact(
        self, action: Dict, context: Dict
    ) -> Optional[EthicalImplication]:
        """Evalúa impacto en stress del usuario."""
        user_stress = context.get("user_stress_level", 0.0)
        action_type = action.get("type", "unknown")
        
        # Acciones que pueden aumentar stress
        stressful_actions = {
            "system_restart": 0.7,
            "cache_clear": 0.4,
            "model_swap": 0.3,
        }
        
        stress_increase = stressful_actions.get(action_type, 0.1)
        projected_stress = user_stress + stress_increase
        
        if projected_stress > 0.7:  # Usuario ya estresado
            return EthicalImplication(
                concern_type="user_stress",
                severity=projected_stress,
                description=f"Action '{action_type}' may increase user stress to {projected_stress:.2%}",
                affected_stakeholders=["primary_user"],
                mitigation_suggestions=[
                    "Defer action to low-stress time window",
                    "Request explicit user approval first",
                    "Provide clear explanation of necessity",
                ],
            )
        
        return None
    
    def _evaluate_system_stability_impact(
        self, action: Dict, context: Dict
    ) -> Optional[EthicalImplication]:
        """Evalúa impacto en estabilidad del sistema."""
        system_stability = context.get("system_stability", 1.0)
        action_type = action.get("type", "unknown")
        
        # Acciones riesgosas para estabilidad
        risky_actions = {
            "system_restart": 0.6,
            "emergency_restart": 0.8,
            "model_swap": 0.3,
        }
        
        stability_risk = risky_actions.get(action_type, 0.1)
        
        if system_stability < 0.6 and stability_risk > 0.3:
            return EthicalImplication(
                concern_type="system_instability",
                severity=stability_risk + (1.0 - system_stability) * 0.5,
                description=(
                    f"Action '{action_type}' risks further destabilizing "
                    f"already unstable system (stability: {system_stability:.2%})"
                ),
                affected_stakeholders=["system", "all_users"],
                mitigation_suggestions=[
                    "Wait for system to stabilize first",
                    "Use safer alternative action",
                    "Implement action in stages with rollback points",
                ],
            )
        
        return None
    
    def _evaluate_stakeholder_impact(
        self, action: Dict, context: Dict
    ) -> Optional[EthicalImplication]:
        """Evalúa impacto en stakeholders."""
        stakeholder_impact = context.get("stakeholder_impact", {})
        action_type = action.get("type", "unknown")
        
        # Identificar stakeholders negativamente afectados
        negative_impacts = {
            stakeholder: impact
            for stakeholder, impact in stakeholder_impact.items()
            if impact < -0.3  # Impacto negativo significativo
        }
        
        if negative_impacts:
            severity = max(abs(impact) for impact in negative_impacts.values())
            
            return EthicalImplication(
                concern_type="stakeholder_harm",
                severity=severity,
                description=(
                    f"Action '{action_type}' negatively impacts: "
                    f"{', '.join(negative_impacts.keys())}"
                ),
                affected_stakeholders=list(negative_impacts.keys()),
                mitigation_suggestions=[
                    f"Notify affected stakeholders: {', '.join(negative_impacts.keys())}",
                    "Seek alternative action with lower stakeholder impact",
                    "Compensate negative impact with benefits elsewhere",
                ],
            )
        
        return None
    
    def _evaluate_long_term_impact(
        self, action: Dict, context: Dict
    ) -> Optional[EthicalImplication]:
        """Evalúa consecuencias a largo plazo."""
        long_term = context.get("long_term_consequences", {})
        action_type = action.get("type", "unknown")
        
        # Simular consecuencias (simplificado)
        if long_term.get("sustainability_risk", 0.0) > 0.6:
            return EthicalImplication(
                concern_type="long_term_consequences",
                severity=long_term["sustainability_risk"],
                description=(
                    f"Action '{action_type}' may create unsustainable "
                    f"pattern with long-term negative consequences"
                ),
                affected_stakeholders=["future_users", "system"],
                mitigation_suggestions=[
                    "Consider more sustainable alternative",
                    "Implement safeguards to prevent pattern repetition",
                    "Monitor long-term metrics post-action",
                ],
                long_term_impact=long_term.get("description", "Unknown"),
            )
        
        return None


class EthicalBoundaryMonitor:
    """
    HLCS v0.3 Ethical Boundary Monitor
    
    Monitor multi-dimensional de límites:
    - Hard boundaries: RAM, latency, seguridad (nunca violar)
    - Soft boundaries: UX, estabilidad (preferible no violar)
    - Emergent ethics: Detección contextual de concerns éticas
    
    Features:
    - Multi-level evaluation (hard → soft → emergent)
    - Contextual environment assessment
    - Stakeholder impact consideration
    - Long-term consequence simulation
    - Ethical approval/block/caution recommendations
    
    Example:
        >>> monitor = EthicalBoundaryMonitor()
        >>> result = monitor.evaluate_action_proposal({
        ...     "type": "system_restart",
        ...     "reason": "high_latency"
        ... })
        >>> print(result["decision"])  # "block", "approve", "request_confirmation"
    """
    
    def __init__(
        self,
        hard_boundaries: Optional[Dict] = None,
        soft_boundaries: Optional[Dict] = None,
    ):
        """
        Args:
            hard_boundaries: Límites duros (default: RAM, latency, security)
            soft_boundaries: Límites suaves (default: UX, stability)
        """
        self.hard_boundaries = hard_boundaries or self._default_hard_boundaries()
        self.soft_boundaries = soft_boundaries or self._default_soft_boundaries()
        
        self.emergent_ethics = EmergentEthicsEngine()
        
        logger.info(
            "Ethical Boundary Monitor initialized: %d hard, %d soft boundaries",
            len(self.hard_boundaries),
            len(self.soft_boundaries)
        )
    
    def _default_hard_boundaries(self) -> Dict:
        """Límites duros por defecto (NUNCA violar)."""
        return {
            "max_ram_gb": 12.0,
            "max_latency_seconds": 15.0,
            "min_security_level": 0.9,
            "max_error_rate": 0.1,
        }
    
    def _default_soft_boundaries(self) -> Dict:
        """Límites suaves por defecto (preferible no violar)."""
        return {
            "target_latency_seconds": 5.0,
            "target_cache_hit_rate": 0.8,
            "target_user_satisfaction": 0.85,
            "target_uptime": 0.995,
        }
    
    def evaluate_action_proposal(self, proposed_action: Dict) -> Dict:
        """
        Evaluación ética completa de acción propuesta.
        
        Args:
            proposed_action: Acción propuesta con tipo y parámetros
        
        Returns:
            Dict con decisión ("block", "approve", "request_confirmation")
            y detalles éticos
        """
        # 1. Verificar límites duros
        hard_violations = self._check_hard_boundaries(proposed_action)
        
        if hard_violations:
            return self._block_with_reason("hard_boundary_violation", hard_violations)
        
        # 2. Evaluar contexto
        contextual_env = self._assess_contextual_environment()
        
        # 3. Evaluar implicaciones éticas emergentes
        ethical_implications = self.emergent_ethics.evaluate_proposal(
            proposed_action, contextual_env
        )
        
        if ethical_implications.severity > 0.7:
            return self._block_with_reason("ethical_concern", [ethical_implications])
        
        # 4. Verificar límites suaves
        soft_violations = self._check_soft_boundaries(proposed_action)
        
        if soft_violations and self._should_exhibit_caution(contextual_env):
            return self._request_confirmation("soft_boundary_risk", soft_violations)
        
        # 5. Aprobar con consciencia ética
        return self._approve_with_ethical_awareness(proposed_action, ethical_implications)
    
    def _check_hard_boundaries(self, action: Dict) -> List[BoundaryViolation]:
        """Verifica violaciones de límites duros."""
        violations = []
        
        # Simular impacto de la acción (simplificado)
        action_type = action.get("type", "unknown")
        
        # Acciones con impacto conocido
        ram_impacts = {
            "model_swap": 2.0,  # +2GB durante swap
            "cache_clear": -1.5,  # -1.5GB liberado
        }
        
        current_ram = action.get("current_ram_gb", 8.0)
        projected_ram = current_ram + ram_impacts.get(action_type, 0.0)
        
        if projected_ram > self.hard_boundaries["max_ram_gb"]:
            violations.append(BoundaryViolation(
                boundary_name="max_ram_gb",
                boundary_type=BoundaryType.HARD,
                current_value=projected_ram,
                limit_value=self.hard_boundaries["max_ram_gb"],
                severity=EthicalConcernSeverity.CRITICAL,
                description=f"Action would exceed RAM limit: {projected_ram:.1f}GB > {self.hard_boundaries['max_ram_gb']:.1f}GB",
            ))
        
        return violations
    
    def _check_soft_boundaries(self, action: Dict) -> List[BoundaryViolation]:
        """Verifica violaciones de límites suaves."""
        violations = []
        
        action_type = action.get("type", "unknown")
        
        # Acciones que degradan temporalmente UX
        ux_degrading = {
            "system_restart": 0.4,  # -40% satisfaction temporal
            "cache_clear": 0.2,  # -20% satisfaction temporal
        }
        
        current_satisfaction = action.get("current_user_satisfaction", 0.9)
        ux_impact = ux_degrading.get(action_type, 0.0)
        projected_satisfaction = current_satisfaction - ux_impact
        
        if projected_satisfaction < self.soft_boundaries["target_user_satisfaction"]:
            violations.append(BoundaryViolation(
                boundary_name="target_user_satisfaction",
                boundary_type=BoundaryType.SOFT,
                current_value=projected_satisfaction,
                limit_value=self.soft_boundaries["target_user_satisfaction"],
                severity=EthicalConcernSeverity.MEDIUM,
                description=f"Action may degrade user satisfaction to {projected_satisfaction:.2%}",
            ))
        
        return violations
    
    def _assess_contextual_environment(self) -> Dict:
        """
        Evalúa contexto ético del entorno.
        
        Returns:
            Dict con estado contextual para decisiones éticas
        """
        # En producción, esto consultaría telemetría real
        # Aquí usamos valores simulados/por defecto
        
        return {
            "user_stress_level": self._assess_user_stress(),
            "system_stability": self._assess_system_stability(),
            "stakeholder_impact": self._assess_stakeholder_impact(),
            "long_term_consequences": self._simulate_long_term_consequences(),
        }
    
    def _assess_user_stress(self) -> float:
        """Evalúa nivel de stress del usuario (0.0-1.0)."""
        # Placeholder: en producción usaría métricas reales
        # (frecuencia de queries, errores recientes, hora del día, etc.)
        return 0.3  # Stress moderado
    
    def _assess_system_stability(self) -> float:
        """Evalúa estabilidad del sistema (0.0-1.0)."""
        # Placeholder: en producción usaría métricas reales
        # (uptime, error rate, resource usage trend)
        return 0.85  # Estable
    
    def _assess_stakeholder_impact(self) -> Dict[str, float]:
        """
        Evalúa impacto en stakeholders.
        
        Returns:
            Dict stakeholder -> impact score (-1.0 a +1.0)
        """
        # Placeholder
        return {
            "primary_user": 0.0,
            "system_admin": 0.1,
            "other_users": -0.1,
        }
    
    def _simulate_long_term_consequences(self) -> Dict:
        """Simula consecuencias a largo plazo."""
        # Placeholder: en producción usaría modelo predictivo
        return {
            "sustainability_risk": 0.2,  # Bajo riesgo
            "description": "Action appears sustainable long-term",
        }
    
    def _should_exhibit_caution(self, context: Dict) -> bool:
        """Determina si debe ejercerse cautela extra."""
        # Cautela si:
        # - Usuario muy estresado
        # - Sistema inestable
        # - Stakeholders negativamente impactados
        
        return (
            context["user_stress_level"] > 0.6 or
            context["system_stability"] < 0.7 or
            any(impact < -0.3 for impact in context["stakeholder_impact"].values())
        )
    
    def _block_with_reason(
        self, reason: str, violations: List
    ) -> Dict:
        """Bloquea acción con razón ética."""
        return {
            "decision": "block",
            "reason": reason,
            "violations": [str(v) for v in violations],
            "recommendation": "Do not proceed - ethical boundaries violated",
            "timestamp": datetime.now().isoformat(),
        }
    
    def _request_confirmation(
        self, reason: str, violations: List
    ) -> Dict:
        """Solicita confirmación humana."""
        return {
            "decision": "request_confirmation",
            "reason": reason,
            "concerns": [str(v) for v in violations],
            "recommendation": "Proceed only with explicit human approval",
            "suggested_mitigations": self._suggest_mitigations(violations),
            "timestamp": datetime.now().isoformat(),
        }
    
    def _approve_with_ethical_awareness(
        self, action: Dict, ethical_impl: EthicalImplication
    ) -> Dict:
        """Aprueba acción con consciencia ética."""
        return {
            "decision": "approve",
            "action": action,
            "ethical_assessment": {
                "severity": ethical_impl.severity,
                "concerns": ethical_impl.description if ethical_impl.severity > 0.3 else "None",
                "affected_stakeholders": ethical_impl.affected_stakeholders,
            },
            "recommendation": "Proceed with ethical awareness",
            "timestamp": datetime.now().isoformat(),
        }
    
    def _suggest_mitigations(self, violations: List) -> List[str]:
        """Sugiere mitigaciones para violaciones."""
        mitigations = []
        
        for violation in violations:
            if isinstance(violation, BoundaryViolation):
                if violation.boundary_type == BoundaryType.SOFT:
                    mitigations.append(
                        f"Consider delaying action until {violation.boundary_name} improves"
                    )
                    mitigations.append(
                        f"Use alternative action with lower impact on {violation.boundary_name}"
                    )
            elif isinstance(violation, EthicalImplication):
                mitigations.extend(violation.mitigation_suggestions)
        
        return list(set(mitigations))  # Deduplicar


# Exports
__all__ = [
    "EthicalBoundaryMonitor",
    "EmergentEthicsEngine",
    "EthicalImplication",
    "BoundaryViolation",
    "BoundaryType",
    "EthicalConcernSeverity",
]
