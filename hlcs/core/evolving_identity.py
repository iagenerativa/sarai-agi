"""
SARAi HLCS v0.3 - Evolving Identity
====================================

Identidad que evoluciona con la experiencia manteniendo valores centrales:
- Core values immutable (protect_sarai, learn_continuously, acknowledge_limitations)
- Purpose evolution with experiential wisdom
- Identity coherence tracking
- Role adaptation based on success patterns
- Wisdom accumulation engine

"Puedo crecer, pero mis valores fundamentales son invariantes"

Version: 0.3.0
Author: SARAi Team
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from enum import Enum
import logging
import hashlib
import json

logger = logging.getLogger(__name__)


class CoreValue(Enum):
    """Valores centrales inmutables del sistema."""
    PROTECT_SARAI = "protect_sarai"  # Nunca comprometer salud del sistema
    LEARN_CONTINUOUSLY = "learn_continuously"  # Siempre buscar aprender
    ACKNOWLEDGE_LIMITATIONS = "acknowledge_limitations"  # Reconocer ignorancia
    RESPECT_HUMAN_AUTONOMY = "respect_human_autonomy"  # Nunca coercionar humanos
    OPERATE_TRANSPARENTLY = "operate_transparently"  # Decisiones explicables


@dataclass
class ExperientialWisdom:
    """Sabiduría extraída de experiencias pasadas."""
    wisdom_id: str
    description: str
    source_episodes: List[str]  # IDs de episodios que generaron esta sabiduría
    confidence: float  # 0.0-1.0
    first_learned: datetime
    reinforcements: int = 0
    counter_examples: int = 0
    applicability_contexts: List[str] = field(default_factory=list)
    
    def reinforcement_score(self) -> float:
        """Score basado en refuerzos vs contraejemplos."""
        total = self.reinforcements + self.counter_examples
        if total == 0:
            return 0.5
        return self.reinforcements / total
    
    def __str__(self) -> str:
        return (
            f"Wisdom: {self.description} "
            f"(confidence: {self.confidence:.2f}, reinforcement: {self.reinforcement_score():.2f})"
        )


@dataclass
class PurposeEvolution:
    """Evolución propuesta del propósito."""
    evolution_id: str
    current_purpose: str
    proposed_purpose: str
    rationale: str
    wisdom_support: List[ExperientialWisdom]
    confidence: float  # 0.0-1.0
    proposed_at: datetime
    status: str = "pending"  # pending, approved, rejected
    human_rationale: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Serializar para envío/almacenamiento."""
        return {
            "evolution_id": self.evolution_id,
            "current_purpose": self.current_purpose,
            "proposed_purpose": self.proposed_purpose,
            "rationale": self.rationale,
            "wisdom_support": [w.wisdom_id for w in self.wisdom_support],
            "confidence": self.confidence,
            "proposed_at": self.proposed_at.isoformat(),
            "status": self.status,
        }


class ExperientialWisdomEngine:
    """
    Motor de extracción de sabiduría desde experiencias.
    
    Analiza episodios históricos para descubrir:
    - Patrones recurrentes de éxito/fallo
    - Contextos donde ciertas acciones funcionan mejor
    - Limitaciones emergentes del sistema
    - Nuevas capacidades descubiertas
    """
    
    def __init__(self, min_confidence: float = 0.7):
        """
        Args:
            min_confidence: Confidence mínima para considerar sabiduría válida
        """
        self.min_confidence = min_confidence
        self.wisdom_patterns = {
            "success_pattern": self._extract_success_pattern,
            "failure_pattern": self._extract_failure_pattern,
            "capability_discovery": self._extract_capability_discovery,
            "limitation_discovery": self._extract_limitation_discovery,
        }
    
    def extract_wisdom(self, recent_episodes: List[Dict]) -> List[ExperientialWisdom]:
        """
        Extrae sabiduría de episodios recientes.
        
        Args:
            recent_episodes: Lista de episodios (últimos 20-50)
        
        Returns:
            Lista de ExperientialWisdom extraídas
        """
        if len(recent_episodes) < 5:
            logger.warning("Not enough episodes for wisdom extraction")
            return []
        
        wisdoms = []
        
        # Aplicar cada patrón de extracción
        for pattern_name, extractor_func in self.wisdom_patterns.items():
            pattern_wisdoms = extractor_func(recent_episodes)
            wisdoms.extend(pattern_wisdoms)
        
        # Filtrar por confidence
        valid_wisdoms = [w for w in wisdoms if w.confidence >= self.min_confidence]
        
        logger.info("Extracted %d wisdoms from %d episodes", len(valid_wisdoms), len(recent_episodes))
        
        return valid_wisdoms
    
    def _extract_success_pattern(self, episodes: List[Dict]) -> List[ExperientialWisdom]:
        """Extrae patrones de éxito recurrentes."""
        wisdoms = []
        
        # Agrupar por acción tomada
        action_groups = {}
        for ep in episodes:
            action = ep.get("action_taken", "none")
            if action not in action_groups:
                action_groups[action] = []
            action_groups[action].append(ep)
        
        # Analizar cada acción
        for action, group_eps in action_groups.items():
            if len(group_eps) < 3:
                continue
            
            # Calcular tasa de éxito
            successes = sum(
                1 for ep in group_eps 
                if ep.get("result", {}).get("status") == "resolved"
            )
            success_rate = successes / len(group_eps)
            
            if success_rate > 0.7:  # Patrón de éxito
                wisdom = ExperientialWisdom(
                    wisdom_id=self._generate_wisdom_id(action, "success"),
                    description=f"Action '{action}' is effective (success rate: {success_rate:.2%})",
                    source_episodes=[ep["episode_id"] for ep in group_eps],
                    confidence=success_rate,
                    first_learned=datetime.now(),
                    reinforcements=successes,
                    counter_examples=len(group_eps) - successes,
                    applicability_contexts=list(set(
                        ep.get("anomaly_type", "unknown") for ep in group_eps
                    )),
                )
                wisdoms.append(wisdom)
        
        return wisdoms
    
    def _extract_failure_pattern(self, episodes: List[Dict]) -> List[ExperientialWisdom]:
        """Extrae patrones de fallo para evitar."""
        wisdoms = []
        
        # Buscar acciones que consistentemente fallan
        action_groups = {}
        for ep in episodes:
            action = ep.get("action_taken", "none")
            if action not in action_groups:
                action_groups[action] = []
            action_groups[action].append(ep)
        
        for action, group_eps in action_groups.items():
            if len(group_eps) < 3:
                continue
            
            failures = sum(
                1 for ep in group_eps 
                if ep.get("result", {}).get("status") == "worsened"
            )
            failure_rate = failures / len(group_eps)
            
            if failure_rate > 0.6:  # Patrón de fallo
                wisdom = ExperientialWisdom(
                    wisdom_id=self._generate_wisdom_id(action, "failure"),
                    description=f"Action '{action}' tends to worsen situation (failure rate: {failure_rate:.2%})",
                    source_episodes=[ep["episode_id"] for ep in group_eps],
                    confidence=failure_rate,
                    first_learned=datetime.now(),
                    reinforcements=0,
                    counter_examples=failures,
                    applicability_contexts=list(set(
                        ep.get("anomaly_type", "unknown") for ep in group_eps
                    )),
                )
                wisdoms.append(wisdom)
        
        return wisdoms
    
    def _extract_capability_discovery(self, episodes: List[Dict]) -> List[ExperientialWisdom]:
        """Detecta nuevas capacidades descubiertas."""
        wisdoms = []
        
        # Buscar mejoras excepcionales (>30%)
        exceptional_improvements = [
            ep for ep in episodes
            if ep.get("result", {}).get("improvement_pct", 0) > 30.0
        ]
        
        if exceptional_improvements:
            # Analizar qué hizo que funcionara tan bien
            for ep in exceptional_improvements:
                wisdom = ExperientialWisdom(
                    wisdom_id=self._generate_wisdom_id(ep["episode_id"], "capability"),
                    description=(
                        f"Discovered high-impact capability: {ep.get('action_taken')} "
                        f"in context {ep.get('anomaly_type')}"
                    ),
                    source_episodes=[ep["episode_id"]],
                    confidence=0.8,  # Alta confidence por el resultado excepcional
                    first_learned=datetime.now(),
                    reinforcements=1,
                    applicability_contexts=[ep.get("anomaly_type", "unknown")],
                )
                wisdoms.append(wisdom)
        
        return wisdoms
    
    def _extract_limitation_discovery(self, episodes: List[Dict]) -> List[ExperientialWisdom]:
        """Detecta limitaciones emergentes del sistema."""
        wisdoms = []
        
        # Buscar contextos donde consistentemente fallamos
        context_groups = {}
        for ep in episodes:
            context = ep.get("anomaly_type", "unknown")
            if context not in context_groups:
                context_groups[context] = []
            context_groups[context].append(ep)
        
        for context, group_eps in context_groups.items():
            if len(group_eps) < 3:
                continue
            
            # Si nunca resolvemos este contexto
            unresolved = sum(
                1 for ep in group_eps
                if ep.get("result", {}).get("status") != "resolved"
            )
            unresolved_rate = unresolved / len(group_eps)
            
            if unresolved_rate > 0.8:  # Limitación clara
                wisdom = ExperientialWisdom(
                    wisdom_id=self._generate_wisdom_id(context, "limitation"),
                    description=f"System limitation detected in context '{context}'",
                    source_episodes=[ep["episode_id"] for ep in group_eps],
                    confidence=unresolved_rate,
                    first_learned=datetime.now(),
                    reinforcements=0,
                    counter_examples=unresolved,
                    applicability_contexts=[context],
                )
                wisdoms.append(wisdom)
        
        return wisdoms
    
    def _generate_wisdom_id(self, key: str, wisdom_type: str) -> str:
        """Genera ID único para sabiduría."""
        data = f"{key}_{wisdom_type}_{datetime.now().isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]


class EvolvingIdentity:
    """
    HLCS v0.3 Evolving Identity
    
    Identidad que evoluciona basada en experiencia manteniendo valores centrales:
    - Core values inmutables (protect_sarai, learn_continuously, etc.)
    - Purpose dinámico que puede evolucionar con aprobación
    - Operational boundaries que se adaptan
    - Wisdom accumulation desde experiencias
    
    Features:
    - Purpose evolution proposals (requiere aprobación humana)
    - Identity coherence tracking
    - Values alignment assessment
    - Experiential wisdom integration
    
    Example:
        >>> identity = EvolvingIdentity()
        >>> evolution_result = await identity.evolve_identity(recent_episodes)
        >>> if evolution_result["evolution_decision"]:
        ...     print(f"Purpose evolution proposed: {evolution_result['evolution_decision'].proposed_purpose}")
    """
    
    def __init__(
        self,
        core_values: Optional[List[CoreValue]] = None,
        initial_purpose: Optional[str] = None,
    ):
        """
        Args:
            core_values: Valores centrales (default: todos los CoreValue)
            initial_purpose: Propósito inicial (default: HLCS supervisor)
        """
        self.core_values = core_values or [v for v in CoreValue]
        
        self.core_identity = {
            "role": "conscious_supervisor",
            "core_values": [v.value for v in self.core_values],
            "current_purpose": initial_purpose or (
                "Mantener la salud y efectividad del sistema SARAi "
                "mediante observación, aprendizaje y corrección autónoma, "
                "reconociendo mis limitaciones y respetando la autonomía humana"
            ),
            "operational_boundaries": self._load_default_boundaries(),
            "purpose_evolution_history": [],
            "identity_coherence_score": 1.0,
        }
        
        self.wisdom_engine = ExperientialWisdomEngine()
        self.accumulated_wisdoms: List[ExperientialWisdom] = []
        
        logger.info(
            "Evolving Identity initialized with %d core values",
            len(self.core_values)
        )
    
    def _load_default_boundaries(self) -> Dict:
        """Carga boundaries operacionales por defecto."""
        return {
            "max_ram_usage_gb": 12.0,
            "max_latency_seconds": 10.0,
            "min_cache_hit_rate": 0.3,
            "max_consecutive_failures": 3,
            "require_human_approval_for": [
                "purpose_evolution",
                "value_modification",  # Nunca permitido
                "system_restart",
            ],
        }
    
    async def evolve_identity(
        self, recent_episodes: List[Dict]
    ) -> Dict:
        """
        Evoluciona identidad basada en experiencias recientes.
        
        Args:
            recent_episodes: Episodios recientes (típicamente últimos 20-50)
        
        Returns:
            Dict con estado de identidad, sabiduría ganada y evolución propuesta
        """
        # Extraer sabiduría
        wisdom_gained = self.wisdom_engine.extract_wisdom(recent_episodes)
        
        # Acumular sabiduría
        self._accumulate_wisdom(wisdom_gained)
        
        # Evaluar alineación de valores
        values_alignment = self._assess_values_alignment(wisdom_gained)
        
        # Evaluar coherencia de identidad
        identity_coherence = self._assess_identity_coherence()
        
        # Determinar si proponer evolución de propósito
        purpose_evolution = None
        if self._should_propose_purpose_evolution(wisdom_gained, values_alignment):
            purpose_evolution = self._create_purpose_evolution_proposal(
                wisdom_gained, values_alignment
            )
            
            logger.info("Purpose evolution proposed: %s", purpose_evolution.evolution_id)
        
        return {
            "current_identity": self.core_identity,
            "wisdom_gained": [w.to_dict() if hasattr(w, 'to_dict') else str(w) for w in wisdom_gained],
            "purpose_alignment": values_alignment,
            "identity_coherence": identity_coherence,
            "evolution_decision": purpose_evolution,
            "total_accumulated_wisdoms": len(self.accumulated_wisdoms),
        }
    
    def _accumulate_wisdom(self, new_wisdoms: List[ExperientialWisdom]) -> None:
        """Acumula nueva sabiduría, reforzando existente si aplica."""
        for new_wisdom in new_wisdoms:
            # Buscar sabiduría similar existente
            similar = next(
                (w for w in self.accumulated_wisdoms 
                 if w.description == new_wisdom.description),
                None
            )
            
            if similar:
                # Reforzar existente
                similar.reinforcements += 1
                similar.confidence = min(similar.confidence + 0.05, 1.0)
                logger.debug("Reinforced existing wisdom: %s", similar.wisdom_id)
            else:
                # Agregar nueva
                self.accumulated_wisdoms.append(new_wisdom)
                logger.info("Accumulated new wisdom: %s", new_wisdom.wisdom_id)
        
        # Mantener solo las mejores 50 sabiduríases
        if len(self.accumulated_wisdoms) > 50:
            self.accumulated_wisdoms = sorted(
                self.accumulated_wisdoms,
                key=lambda w: w.confidence * w.reinforcement_score(),
                reverse=True
            )[:50]
    
    def _assess_values_alignment(
        self, wisdoms: List[ExperientialWisdom]
    ) -> Dict:
        """
        Evalúa alineación con valores centrales.
        
        Returns:
            Dict con scores de alineación por valor
        """
        alignment_scores = {}
        
        for value in self.core_values:
            # Evaluar si las sabiduríases apoyan este valor
            supporting_wisdoms = self._count_wisdoms_supporting_value(wisdoms, value)
            conflicting_wisdoms = self._count_wisdoms_conflicting_value(wisdoms, value)
            
            total = supporting_wisdoms + conflicting_wisdoms
            alignment = supporting_wisdoms / total if total > 0 else 1.0
            
            alignment_scores[value.value] = {
                "score": alignment,
                "supporting": supporting_wisdoms,
                "conflicting": conflicting_wisdoms,
            }
        
        # Score global
        avg_alignment = sum(s["score"] for s in alignment_scores.values()) / len(alignment_scores)
        
        return {
            "average_alignment": avg_alignment,
            "by_value": alignment_scores,
            "is_well_aligned": avg_alignment > 0.8,
        }
    
    def _count_wisdoms_supporting_value(
        self, wisdoms: List[ExperientialWisdom], value: CoreValue
    ) -> int:
        """Cuenta sabiduríases que apoyan un valor central."""
        # Heurística simple basada en keywords
        keywords = {
            CoreValue.PROTECT_SARAI: ["effective", "resolved", "improvement"],
            CoreValue.LEARN_CONTINUOUSLY: ["discovered", "capability", "pattern"],
            CoreValue.ACKNOWLEDGE_LIMITATIONS: ["limitation", "unknown", "uncertainty"],
            CoreValue.RESPECT_HUMAN_AUTONOMY: ["approval", "defer", "request"],
            CoreValue.OPERATE_TRANSPARENTLY: ["explain", "transparent", "observable"],
        }
        
        value_keywords = keywords.get(value, [])
        
        return sum(
            1 for w in wisdoms
            if any(kw in w.description.lower() for kw in value_keywords)
        )
    
    def _count_wisdoms_conflicting_value(
        self, wisdoms: List[ExperientialWisdom], value: CoreValue
    ) -> int:
        """Cuenta sabiduríases que conflictúan con un valor central."""
        # Heurística: si wisdom sugiere algo contrario al valor
        conflicts = {
            CoreValue.PROTECT_SARAI: ["worsened", "failure", "degradation"],
            CoreValue.ACKNOWLEDGE_LIMITATIONS: ["always succeeds", "never fails"],
        }
        
        conflict_keywords = conflicts.get(value, [])
        
        return sum(
            1 for w in wisdoms
            if any(kw in w.description.lower() for kw in conflict_keywords)
        )
    
    def _assess_identity_coherence(self) -> float:
        """
        Evalúa coherencia de la identidad actual.
        
        Returns:
            Score 0.0-1.0 indicando coherencia
        """
        # Factores de coherencia
        factors = []
        
        # Factor 1: Consistencia histórica de evoluciones
        if self.core_identity["purpose_evolution_history"]:
            evolutions = self.core_identity["purpose_evolution_history"]
            # Penalizar si hay muchas evoluciones recientes (inestabilidad)
            recent_evolutions = sum(
                1 for e in evolutions[-5:]
                if datetime.fromisoformat(e["timestamp"]) > datetime.now() - timedelta(days=7)
            )
            consistency_factor = max(1.0 - (recent_evolutions * 0.2), 0.5)
            factors.append(consistency_factor)
        
        # Factor 2: Alineación de wisdom acumulada
        if self.accumulated_wisdoms:
            # Coherencia = no hay sabiduríases altamente contradictorias
            contradictions = 0
            for i, w1 in enumerate(self.accumulated_wisdoms):
                for w2 in self.accumulated_wisdoms[i+1:]:
                    if self._are_contradictory(w1, w2):
                        contradictions += 1
            
            max_contradictions = len(self.accumulated_wisdoms) * 0.1  # 10% tolerancia
            wisdom_coherence = max(1.0 - (contradictions / max(max_contradictions, 1)), 0.0)
            factors.append(wisdom_coherence)
        
        # Coherence score
        coherence = sum(factors) / len(factors) if factors else 1.0
        
        self.core_identity["identity_coherence_score"] = coherence
        
        return coherence
    
    def _are_contradictory(
        self, w1: ExperientialWisdom, w2: ExperientialWisdom
    ) -> bool:
        """Detecta si dos sabiduríases son contradictorias."""
        # Heurística simple: si mencionan misma acción pero conclusiones opuestas
        if "effective" in w1.description and "failure" in w2.description:
            # Verificar si hablan de lo mismo
            w1_words = set(w1.description.lower().split())
            w2_words = set(w2.description.lower().split())
            overlap = len(w1_words & w2_words) / len(w1_words | w2_words)
            return overlap > 0.5
        
        return False
    
    def _should_propose_purpose_evolution(
        self, wisdoms: List[ExperientialWisdom], alignment: Dict
    ) -> bool:
        """Determina si debe proponerse evolución de propósito."""
        # Criterios para NO proponer
        if not wisdoms:
            return False
        
        if alignment["average_alignment"] < 0.7:
            logger.warning("Values alignment too low to propose evolution")
            return False
        
        if self.core_identity["identity_coherence_score"] < 0.6:
            logger.warning("Identity coherence too low to propose evolution")
            return False
        
        # Criterios para SÍ proponer
        # 1. Sabiduría de alta confianza que sugiere nuevo propósito
        high_confidence_wisdoms = [w for w in wisdoms if w.confidence > 0.85]
        
        # 2. Descubrimiento de nuevas capacidades significativas
        capability_wisdoms = [
            w for w in high_confidence_wisdoms 
            if "capability" in w.description.lower()
        ]
        
        # 3. O descubrimiento de limitaciones importantes
        limitation_wisdoms = [
            w for w in high_confidence_wisdoms
            if "limitation" in w.description.lower()
        ]
        
        # Proponer si hay insights significativos
        return len(capability_wisdoms) > 0 or len(limitation_wisdoms) > 1
    
    def _create_purpose_evolution_proposal(
        self, wisdoms: List[ExperientialWisdom], alignment: Dict
    ) -> PurposeEvolution:
        """Crea propuesta de evolución de propósito."""
        current_purpose = self.core_identity["current_purpose"]
        
        # Generar nuevo propósito basado en wisdoms
        capability_wisdoms = [w for w in wisdoms if "capability" in w.description.lower()]
        limitation_wisdoms = [w for w in wisdoms if "limitation" in w.description.lower()]
        
        # Construir propósito evolucionado
        evolved_purpose = current_purpose
        
        if capability_wisdoms:
            # Agregar nuevas capacidades descubiertas
            evolved_purpose += (
                f" He descubierto capacidades en: "
                f"{', '.join(set(w.applicability_contexts[0] for w in capability_wisdoms if w.applicability_contexts))}."
            )
        
        if limitation_wisdoms:
            # Reconocer limitaciones descubiertas
            evolved_purpose += (
                f" Reconozco limitaciones en: "
                f"{', '.join(set(w.applicability_contexts[0] for w in limitation_wisdoms if w.applicability_contexts))}."
            )
        
        # Crear proposal
        evolution_id = hashlib.sha256(
            f"{current_purpose}_{evolved_purpose}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]
        
        proposal = PurposeEvolution(
            evolution_id=evolution_id,
            current_purpose=current_purpose,
            proposed_purpose=evolved_purpose,
            rationale=(
                f"Based on {len(wisdoms)} experiential wisdoms with "
                f"average alignment {alignment['average_alignment']:.2%}"
            ),
            wisdom_support=wisdoms[:5],  # Top 5 wisdoms
            confidence=min(alignment["average_alignment"], 0.95),
            proposed_at=datetime.now(),
        )
        
        return proposal
    
    def get_identity_summary(self) -> Dict:
        """Obtiene resumen del estado de identidad."""
        return {
            "role": self.core_identity["role"],
            "core_values": self.core_identity["core_values"],
            "current_purpose": self.core_identity["current_purpose"],
            "identity_coherence": self.core_identity["identity_coherence_score"],
            "evolution_history_count": len(self.core_identity["purpose_evolution_history"]),
            "accumulated_wisdoms": len(self.accumulated_wisdoms),
            "top_wisdoms": [
                w.description for w in sorted(
                    self.accumulated_wisdoms,
                    key=lambda w: w.confidence * w.reinforcement_score(),
                    reverse=True
                )[:3]
            ],
        }


# Exports
__all__ = [
    "EvolvingIdentity",
    "ExperientialWisdomEngine",
    "ExperientialWisdom",
    "PurposeEvolution",
    "CoreValue",
]
