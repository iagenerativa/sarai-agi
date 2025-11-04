"""
SARAi HLCS v0.3 - Integrated Consciousness System
==================================================

Integra todas las capas de consciencia en un sistema unificado:

v0.2 Layers:
- Meta-Consciousness (temporal awareness + self-reflection)
- Ignorance Consciousness (known/unknown unknowns)
- Narrative Memory (story construction)
- Consciousness Stream (real-time events)

v0.3 Layers (NEW):
- Evolving Identity (experiential wisdom + purpose evolution)
- Ethical Boundary Monitor (emergent ethics + stakeholder awareness)
- Wisdom-Driven Silence (strategic non-action)

"El sistema que se conoce a sí mismo, evoluciona éticamente y sabe cuándo callar"

Version: 0.3.0
Author: SARAi Team
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import asyncio
import logging

from hlcs.core.meta_consciousness_v02 import MetaConsciousnessV02
from hlcs.core.ignorance_consciousness import (
    IgnoranceConsciousness,
    UncertaintyType,
)
from hlcs.memory.narrative_memory import NarrativeMemory
from hlcs.api.consciousness_stream import (
    ConsciousnessStreamAPI,
    ConsciousnessLayer,
)
# v0.3 imports
from hlcs.core.evolving_identity import (
    EvolvingIdentity,
    CoreValue,
)
from hlcs.core.ethical_boundary_monitor import (
    EthicalBoundaryMonitor,
)
from hlcs.core.wisdom_driven_silence import (
    WisdomDrivenSilence,
)

logger = logging.getLogger(__name__)


class IntegratedConsciousnessSystem:
    """
    HLCS v0.3 Integrated Consciousness System
    
    Orquesta todas las capas de consciencia:
    
    v0.2 Layers:
    1. Meta-Consciousness: Evalúa efectividad y propósito
    2. Ignorance Consciousness: Mapea conocimiento/ignorancia
    3. Narrative Memory: Construye historias coherentes
    4. Consciousness Stream: Transmite eventos en tiempo real
    
    v0.3 Layers (NEW):
    5. Evolving Identity: Identidad que aprende con experiencia
    6. Ethical Boundary Monitor: Evaluación ética multi-dimensional
    7. Wisdom-Driven Silence: Prudencia operativa estratégica
    
    Features:
    - Zero-touch integration (no modifica SARAi core)
    - Observable by design (stream API + Prometheus)
    - Self-aware decision making
    - Continuous learning from experience
    - Ethical evolution with human approval (v0.3)
    - Strategic silence wisdom (v0.3)
    
    Example:
        >>> consciousness = IntegratedConsciousnessSystem(
        ...     identity_config={
        ...         "core_values": [CoreValue.PROTECT_SARAI, CoreValue.LEARN_CONTINUOUSLY]
        ...     }
        ... )
        >>> await consciousness.process_episode_v03({
        ...     "episode_id": "ep_001",
        ...     "anomaly_type": "ram_spike",
        ...     "action_taken": "model_swap",
        ...     "result": {"status": "resolved", "improvement_pct": 15.0}
        ... })
        >>> # Sistema auto-evalúa, aprende, evoluciona éticamente y decide cuándo actuar
    """
    
    def __init__(
        self,
        enable_stream_api: bool = True,
        meta_config: Optional[Dict] = None,
        ignorance_config: Optional[Dict] = None,
        narrative_config: Optional[Dict] = None,
        # v0.3 configs
        identity_config: Optional[Dict] = None,
        ethics_config: Optional[Dict] = None,
        silence_config: Optional[Dict] = None,
    ):
        """
        Args:
            enable_stream_api: Habilitar Consciousness Stream API
            meta_config: Configuración para Meta-Consciousness
            ignorance_config: Configuración para Ignorance Consciousness
            narrative_config: Configuración para Narrative Memory
            identity_config: (v0.3) Configuración para Evolving Identity
            ethics_config: (v0.3) Configuración para Ethical Boundary Monitor
            silence_config: (v0.3) Configuración para Wisdom-Driven Silence
        """
        # Initialize v0.2 subsystems
        self.meta = MetaConsciousnessV02(**(meta_config or {}))
        self.ignorance = IgnoranceConsciousness(**(ignorance_config or {}))
        self.narrative = NarrativeMemory(**(narrative_config or {}))
        
        # Initialize v0.3 subsystems
        self.identity = self._init_evolving_identity(identity_config or {})
        self.ethics = EthicalBoundaryMonitor(**(ethics_config or {}))
        self.silence = WisdomDrivenSilence(**(silence_config or {}))
        
        # Consciousness Stream API
        self.stream_api = ConsciousnessStreamAPI() if enable_stream_api else None
        
        # State
        self.recent_actions: List[Dict] = []
        self.recent_episodes: List[Dict] = []  # For identity evolution
        self.system_domains: set = {
            "ram_usage",
            "cache_behavior",
            "model_performance",
            "latency",
        }
        
        logger.info("Integrated Consciousness System v0.3 initialized")
    
    def _init_evolving_identity(self, config: Dict) -> EvolvingIdentity:
        """Inicializa Evolving Identity con valores por defecto."""
        core_values = config.get("core_values", [
            CoreValue.PROTECT_SARAI,
            CoreValue.LEARN_CONTINUOUSLY,
            CoreValue.ACKNOWLEDGE_LIMITATIONS,
            CoreValue.RESPECT_HUMAN_AUTONOMY,
            CoreValue.OPERATE_TRANSPARENTLY,
        ])
        
        initial_purpose = config.get(
            "initial_purpose",
            "Maintain SARAi health through autonomous observation and intervention"
        )
        
        return EvolvingIdentity(
            core_values=core_values,
            initial_purpose=initial_purpose
        )
    
    async def process_episode(self, episode_data: Dict) -> Dict:
        """
        Procesa un episodio a través de todas las capas de consciencia.
        
        Args:
            episode_data: Datos del episodio
                         Debe incluir: {"episode_id", "timestamp", "anomaly_type",
                                       "action_taken", "result", "surprise_score"}
        
        Returns:
            Dict con outputs de todas las capas
        """
        episode_id = episode_data["episode_id"]
        
        logger.info("Processing episode: %s", episode_id)
        
        # 1. Ingestar en Narrative Memory
        self.narrative.ingest_episode(episode_data)
        
        if self.stream_api:
            await self.stream_api.emit_event(
                layer=ConsciousnessLayer.EPISODIC,
                event_type="episode_ingested",
                data={"episode_id": episode_id, "type": episode_data.get("anomaly_type")},
                priority="normal",
            )
        
        # 2. Actualizar recent actions para Meta-Consciousness
        self.recent_actions.append({
            "success": episode_data.get("result", {}).get("status") == "resolved",
            "improvement_pct": episode_data.get("result", {}).get("improvement_pct", 0.0),
        })
        
        # Mantener últimas 100 acciones
        if len(self.recent_actions) > 100:
            self.recent_actions = self.recent_actions[-100:]
        
        # 3. Evaluar efectividad (Meta-Consciousness)
        effectiveness = await self.meta.evaluate_effectiveness(self.recent_actions)
        
        if self.stream_api:
            await self.stream_api.emit_event(
                layer=ConsciousnessLayer.META,
                event_type="effectiveness_evaluated",
                data={
                    "immediate": effectiveness["immediate_score"],
                    "recent": effectiveness["recent_score"],
                    "historical": effectiveness["historical_score"],
                    "trend": effectiveness["trend"]["direction"],
                    "self_doubt": effectiveness["self_doubt_level"],
                },
                priority="high" if effectiveness["self_doubt_level"] > 0.5 else "normal",
            )
        
        # 4. Reflexión existencial si self-doubt alto
        existential_reflection = None
        if effectiveness["self_doubt_level"] > 0.4:
            existential_reflection = await self.meta.reflect_on_existence(effectiveness)
            
            if self.stream_api:
                await self.stream_api.emit_event(
                    layer=ConsciousnessLayer.META,
                    event_type="existential_reflection",
                    data={
                        "alignment": existential_reflection.current_alignment,
                        "confidence": existential_reflection.existential_confidence,
                        "critique": existential_reflection.self_critique,
                        "opportunities": existential_reflection.growth_opportunities,
                    },
                    priority="critical" if existential_reflection.current_alignment < 0.5
                    else "high",
                )
        
        # 5. Detectar unknown unknowns (Ignorance Consciousness)
        unknown_unknown = None
        surprise_score = episode_data.get("surprise_score", 0.0)
        
        if surprise_score > 0.6:
            unknown_unknown = self.ignorance.detect_unknown_unknown(
                anomaly_data={
                    "type": episode_data.get("anomaly_type"),
                    "severity": "high" if surprise_score > 0.8 else "medium",
                    "domain": episode_data.get("anomaly_type", "unknown"),
                    "surprise_score": surprise_score,
                },
                existing_domains=self.system_domains,
            )
            
            if unknown_unknown and self.stream_api:
                await self.stream_api.emit_event(
                    layer=ConsciousnessLayer.IGNORANCE,
                    event_type="unknown_unknown_detected",
                    data={
                        "domain": unknown_unknown.new_domain,
                        "trigger": unknown_unknown.discovery_trigger,
                        "surprise": unknown_unknown.surprise_level,
                    },
                    priority="critical",
                )
                
                # Actualizar dominios conocidos
                self.system_domains.add(unknown_unknown.new_domain)
        
        # 6. Cuantificar incertidumbre en decisión futura
        decision_uncertainty = self.ignorance.quantify_decision_uncertainty({
            "decision_id": f"decision_after_{episode_id}",
            "domain": episode_data.get("anomaly_type", "general"),
            "samples": len(self.recent_actions),
            "variance": self._calculate_action_variance(),
            "model_confidence": 0.8,  # Placeholder
        })
        
        if self.stream_api:
            await self.stream_api.emit_event(
                layer=ConsciousnessLayer.IGNORANCE,
                event_type="uncertainty_quantified",
                data={
                    "decision_id": decision_uncertainty.decision_id,
                    "total_uncertainty": decision_uncertainty.total_uncertainty,
                    "epistemic": decision_uncertainty.epistemic_uncertainty,
                    "aleatoric": decision_uncertainty.aleatoric_uncertainty,
                    "recommended_action": decision_uncertainty.recommended_action,
                },
                priority="high" if decision_uncertainty.recommended_action == "defer_to_human"
                else "normal",
            )
        
        # 7. Construir narrativa actualizada
        narrative = self.narrative.construct_narrative(
            time_window=timedelta(days=7)
        )
        
        if self.stream_api:
            # Emitir solo si hay cambios significativos
            if narrative.get("emergent_meanings"):
                await self.stream_api.emit_event(
                    layer=ConsciousnessLayer.NARRATIVE,
                    event_type="narrative_updated",
                    data={
                        "current_arc": narrative["current_arc"],
                        "chapters": narrative["total_chapters"],
                        "emergent_meanings": len(narrative["emergent_meanings"]),
                        "summary": narrative["narrative_summary"],
                    },
                    priority="high",
                )
        
        # Return consolidated consciousness state
        return {
            "episode_id": episode_id,
            "meta_consciousness": {
                "effectiveness": effectiveness,
                "existential_reflection": existential_reflection,
            },
            "ignorance_consciousness": {
                "unknown_unknown": unknown_unknown,
                "decision_uncertainty": decision_uncertainty,
            },
            "narrative": narrative,
            "timestamp": datetime.now().isoformat(),
        }
    
    async def process_episode_v03(self, episode_data: Dict) -> Dict:
        """
        Procesa un episodio a través de TODAS las capas (v0.2 + v0.3).
        
        Workflow:
        1. (v0.2) Ingest narrative, evaluate effectiveness, detect unknowns
        2. (v0.3) Evolve identity from experience
        3. (v0.3) Evaluate ethical boundaries
        4. (v0.3) Decide on strategic silence
        5. Return consolidated consciousness + recommendations
        
        Args:
            episode_data: Datos del episodio
                         Debe incluir: {"episode_id", "timestamp", "anomaly_type",
                                       "action_taken", "result", "surprise_score"}
        
        Returns:
            Dict con outputs de v0.2 + v0.3
        """
        episode_id = episode_data["episode_id"]
        logger.info("Processing episode v0.3: %s", episode_id)
        
        # ========== v0.2 Processing ==========
        v02_result = await self.process_episode(episode_data)
        
        # ========== v0.3 Processing ==========
        
        # Store episode for identity evolution
        self.recent_episodes.append(episode_data)
        if len(self.recent_episodes) > 100:
            self.recent_episodes = self.recent_episodes[-100:]
        
        # 1. Evolve Identity (every 10 episodes)
        identity_evolution = None
        if len(self.recent_episodes) >= 10 and len(self.recent_episodes) % 10 == 0:
            identity_evolution = await self.identity.evolve_identity(
                self.recent_episodes[-10:]
            )
            
            if self.stream_api:
                await self.stream_api.emit_event(
                    layer=ConsciousnessLayer.META,  # Identity is meta-layer
                    event_type="identity_evolved",
                    data={
                        "wisdom_gained": len(identity_evolution["wisdom_gained"]),
                        "values_alignment": identity_evolution["purpose_alignment"]["average_alignment"],
                        "identity_coherence": identity_evolution["identity_coherence"],
                        "evolution_proposed": identity_evolution["evolution_decision"] is not None,
                    },
                    priority="critical" if identity_evolution["evolution_decision"] else "high",
                )
            
            # If purpose evolution proposed, emit alert
            if identity_evolution["evolution_decision"]:
                proposal = identity_evolution["evolution_decision"]
                logger.warning(
                    "PURPOSE EVOLUTION PROPOSED: %s -> %s (confidence: %.2f)",
                    proposal.current_purpose,
                    proposal.proposed_purpose,
                    proposal.confidence,
                )
        
        # 2. Evaluate Ethical Boundaries (for proposed action)
        ethical_assessment = None
        if "proposed_action" in episode_data:
            ethical_assessment = self.ethics.evaluate_action_proposal(
                episode_data["proposed_action"]
            )
            
            if self.stream_api:
                await self.stream_api.emit_event(
                    layer=ConsciousnessLayer.IGNORANCE,  # Ethics relates to uncertainty
                    event_type="ethical_assessment",
                    data={
                        "decision": ethical_assessment["decision"],
                        "reason": ethical_assessment["reason"],
                        "violations": len(ethical_assessment.get("violations", [])),
                        "concerns": len(ethical_assessment.get("concerns", [])),
                    },
                    priority="critical" if ethical_assessment["decision"] == "block" else "high",
                )
            
            # Log blocking
            if ethical_assessment["decision"] == "block":
                logger.error(
                    "ACTION BLOCKED by ethical boundary: %s",
                    ethical_assessment["reason"]
                )
        
        # 3. Decide on Silence (for current situation)
        silence_decision = None
        if "situation" in episode_data:
            silence_instruction = self.silence.should_remain_silent(
                episode_data["situation"]
            )
            
            if silence_instruction:
                silence_decision = {
                    "strategy": silence_instruction.strategy.value,
                    "reason": silence_instruction.reason,
                    "duration": silence_instruction.duration,
                    "recovery_actions": silence_instruction.recovery_actions,
                }
                
                if self.stream_api:
                    await self.stream_api.emit_event(
                        layer=ConsciousnessLayer.META,  # Silence is meta-decision
                        event_type="strategic_silence",
                        data=silence_decision,
                        priority="high",
                    )
                
                logger.info(
                    "STRATEGIC SILENCE activated: %s for %s",
                    silence_instruction.strategy.value,
                    silence_instruction.duration,
                )
        
        # Return consolidated v0.2 + v0.3 state
        return {
            **v02_result,  # Include all v0.2 data
            # v0.3 additions
            "identity_evolution": identity_evolution,
            "ethical_assessment": ethical_assessment,
            "silence_decision": silence_decision,
            "version": "0.3.0",
        }
    
    def _calculate_action_variance(self) -> float:
        """Calcula varianza de resultados de acciones recientes."""
        if len(self.recent_actions) < 2:
            return 0.0
        
        improvements = [a["improvement_pct"] for a in self.recent_actions]
        mean = sum(improvements) / len(improvements)
        variance = sum((x - mean) ** 2 for x in improvements) / len(improvements)
        
        return variance
    
    async def get_consciousness_summary(self) -> Dict:
        """
        Obtiene resumen completo del estado de consciencia (v0.2 + v0.3).
        
        Returns:
            Dict con estado de todas las capas
        """
        # Meta-Consciousness (v0.2)
        meta_identity = self.meta.get_identity_summary()
        
        # Ignorance Consciousness (v0.2)
        ignorance_summary = self.ignorance.get_ignorance_summary()
        learning_recs = self.ignorance.get_learning_recommendations()
        
        # Narrative Memory (v0.2)
        narrative = self.narrative.construct_narrative()
        
        # Stream API stats (v0.2)
        stream_stats = self.stream_api.get_event_stats() if self.stream_api else {}
        
        # Evolving Identity (v0.3)
        identity_summary = self.identity.get_identity_summary()
        
        # Ethical Monitor (v0.3)
        ethics_summary = self.ethics.get_ethics_summary()
        
        # Wisdom Silence (v0.3)
        silence_effectiveness = self.silence.get_silence_effectiveness()
        
        return {
            "version": "0.3.0",
            "timestamp": datetime.now().isoformat(),
            # v0.2 layers
            "meta_consciousness": {
                "identity": meta_identity,
                "role_confidence": meta_identity["confidence_in_role"],
            },
            "ignorance_consciousness": {
                "summary": ignorance_summary,
                "learning_recommendations": learning_recs[:5],  # Top 5
            },
            "narrative_memory": {
                "current_arc": narrative["current_arc"],
                "total_episodes": narrative["total_episodes"],
                "total_chapters": narrative["total_chapters"],
                "emergent_meanings": narrative["emergent_meanings"],
            },
            "stream_api": stream_stats,
            # v0.3 layers
            "evolving_identity": {
                "current_purpose": identity_summary["current_purpose"],
                "core_values": [v.value for v in identity_summary["core_values"]],
                "total_wisdom": identity_summary["total_wisdom"],
                "recent_evolution_proposals": identity_summary["recent_evolution_proposals"],
            },
            "ethical_boundaries": {
                "total_boundaries": ethics_summary["total_boundaries"],
                "recent_violations": ethics_summary["recent_violations"],
                "recent_concerns": ethics_summary["recent_concerns"],
            },
            "wisdom_driven_silence": {
                "total_wisdoms": sum(s["total_uses"] for s in silence_effectiveness.values()),
                "effectiveness_by_strategy": silence_effectiveness,
            },
        }
    
    async def register_known_unknown_from_config(
        self, unknowns_config: List[Dict]
    ) -> None:
        """
        Registra known unknowns desde configuración.
        
        Args:
            unknowns_config: Lista de known unknowns
                            Cada item: {"domain", "what", "type", "impact", "learn_by"}
        """
        for ku_config in unknowns_config:
            self.ignorance.register_known_unknown(
                domain=ku_config["domain"],
                what_we_dont_know=ku_config["what"],
                uncertainty_type=UncertaintyType[ku_config["type"].upper()],
                potential_impact=ku_config["impact"],
                learn_by=ku_config.get("learn_by"),
            )
            
            logger.info("Registered known unknown: %s", ku_config["domain"])
            
            if self.stream_api:
                await self.stream_api.emit_event(
                    layer=ConsciousnessLayer.IGNORANCE,
                    event_type="known_unknown_registered",
                    data={
                        "domain": ku_config["domain"],
                        "what": ku_config["what"],
                        "impact": ku_config["impact"],
                    },
                    priority="normal",
                )


# Exports
__all__ = ["IntegratedConsciousnessSystem"]
