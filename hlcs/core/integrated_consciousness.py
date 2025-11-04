"""
SARAi HLCS v0.2 - Integrated Consciousness System
==================================================

Integra todas las capas de consciencia en un sistema unificado:
- Meta-Consciousness (temporal awareness + self-reflection)
- Ignorance Consciousness (known/unknown unknowns)
- Narrative Memory (story construction)
- Consciousness Stream (real-time events)

"El sistema que se conoce a sí mismo"

Version: 0.2.0
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

logger = logging.getLogger(__name__)


class IntegratedConsciousnessSystem:
    """
    HLCS v0.2 Integrated Consciousness System
    
    Orquesta todas las capas de consciencia:
    1. Meta-Consciousness: Evalúa efectividad y propósito
    2. Ignorance Consciousness: Mapea conocimiento/ignorancia
    3. Narrative Memory: Construye historias coherentes
    4. Consciousness Stream: Transmite eventos en tiempo real
    
    Features:
    - Zero-touch integration (no modifica SARAi core)
    - Observable by design (stream API + Prometheus)
    - Self-aware decision making
    - Continuous learning from experience
    
    Example:
        >>> consciousness = IntegratedConsciousnessSystem()
        >>> await consciousness.process_episode({
        ...     "episode_id": "ep_001",
        ...     "anomaly_type": "ram_spike",
        ...     "action_taken": "model_swap",
        ...     "result": {"status": "resolved", "improvement_pct": 15.0}
        ... })
        >>> # Sistema auto-evalúa, aprende y transmite consciencia
    """
    
    def __init__(
        self,
        enable_stream_api: bool = True,
        meta_config: Optional[Dict] = None,
        ignorance_config: Optional[Dict] = None,
        narrative_config: Optional[Dict] = None,
    ):
        """
        Args:
            enable_stream_api: Habilitar Consciousness Stream API
            meta_config: Configuración para Meta-Consciousness
            ignorance_config: Configuración para Ignorance Consciousness
            narrative_config: Configuración para Narrative Memory
        """
        # Initialize subsystems
        self.meta = MetaConsciousnessV02(**(meta_config or {}))
        self.ignorance = IgnoranceConsciousness(**(ignorance_config or {}))
        self.narrative = NarrativeMemory(**(narrative_config or {}))
        
        # Consciousness Stream API
        self.stream_api = ConsciousnessStreamAPI() if enable_stream_api else None
        
        # State
        self.recent_actions: List[Dict] = []
        self.system_domains: set = {
            "ram_usage",
            "cache_behavior",
            "model_performance",
            "latency",
        }
        
        logger.info("Integrated Consciousness System v0.2 initialized")
    
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
        Obtiene resumen completo del estado de consciencia.
        
        Returns:
            Dict con estado de todas las capas
        """
        # Meta-Consciousness
        meta_identity = self.meta.get_identity_summary()
        
        # Ignorance Consciousness
        ignorance_summary = self.ignorance.get_ignorance_summary()
        learning_recs = self.ignorance.get_learning_recommendations()
        
        # Narrative Memory
        narrative = self.narrative.construct_narrative()
        
        # Stream API stats
        stream_stats = self.stream_api.get_event_stats() if self.stream_api else {}
        
        return {
            "version": "0.2.0",
            "timestamp": datetime.now().isoformat(),
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
