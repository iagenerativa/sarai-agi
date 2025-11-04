"""
SARAi HLCS v0.2 - Narrative Episodic Memory
============================================

Memoria narrativa que construye historias coherentes:
- Story construction from episodes
- Causal inference between events
- Emergent meaning detection
- Identity continuity
- Turning points recognition

"La memoria no es una lista de hechos, es una narrativa con sentido"

Version: 0.2.0
Author: SARAi Team
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum

import logging

logger = logging.getLogger(__name__)


class CausalRelation(Enum):
    """Tipos de relación causal entre episodios."""
    DIRECT_CAUSE = "direct_cause"  # A → B directamente
    ENABLING = "enabling"  # A permitió B
    PREVENTING = "preventing"  # A previno B
    CORRELATIONAL = "correlational"  # A y B coocurren sin causalidad clara
    UNRELATED = "unrelated"  # Sin relación aparente


class StoryArc(Enum):
    """Arcos narrativos detectados."""
    IMPROVEMENT = "improvement"  # Historia de mejora continua
    DECLINE = "decline"  # Historia de deterioro
    RECOVERY = "recovery"  # Caída seguida de recuperación
    PLATEAU = "plateau"  # Estabilidad sostenida
    VOLATILE = "volatile"  # Cambios erráticos sin patrón claro


@dataclass
class CausalEdge:
    """Conexión causal entre dos episodios."""
    from_episode_id: str
    to_episode_id: str
    relation_type: CausalRelation
    confidence: float  # 0.0-1.0
    temporal_gap: timedelta
    evidence: List[str]  # Evidencias que apoyan la causalidad
    
    def __str__(self) -> str:
        return (
            f"{self.from_episode_id} --[{self.relation_type.value}]--> "
            f"{self.to_episode_id} (confidence: {self.confidence:.2f})"
        )


@dataclass
class NarrativeChapter:
    """Capítulo de la narrativa (grupo de episodios relacionados)."""
    chapter_id: str
    title: str
    episodes: List[str]  # IDs de episodios
    story_arc: StoryArc
    start_time: datetime
    end_time: datetime
    summary: str
    key_insights: List[str]
    turning_points: List[str]  # IDs de episodios que cambiaron la narrativa
    
    def __str__(self) -> str:
        duration = self.end_time - self.start_time
        return (
            f"Chapter: {self.title} ({self.story_arc.value}, "
            f"{len(self.episodes)} episodes, {duration})"
        )


@dataclass
class EmergentMeaning:
    """Significado emergente detectado en la narrativa."""
    pattern_id: str
    description: str
    supporting_episodes: List[str]
    confidence: float  # 0.0-1.0
    first_detected: datetime
    last_reinforced: datetime
    implications: List[str]  # Qué implica este patrón para el futuro
    
    def __str__(self) -> str:
        return (
            f"Emergent: {self.description} "
            f"(confidence: {self.confidence:.2f}, {len(self.supporting_episodes)} episodes)"
        )


class NarrativeMemory:
    """
    HLCS v0.2 Narrative Episodic Memory
    
    Construye narrativas coherentes a partir de episodios:
    - Causal graph construction (episodios conectados causalmente)
    - Story arc detection (improvement, decline, recovery, plateau)
    - Emergent meaning detection (patrones no obvios)
    - Turning points identification (episodios que cambian la historia)
    - Identity continuity (coherencia narrativa en el tiempo)
    
    Features:
    - Temporal causality inference (Granger-style)
    - Multi-scale narratives (micro/macro chapters)
    - Surprise-based turning points
    - Pattern mining for emergent insights
    
    Example:
        >>> memory = NarrativeMemory()
        >>> memory.ingest_episode(episode_data)
        >>> story = memory.construct_narrative(time_window=timedelta(days=7))
        >>> print(story["current_arc"])
        StoryArc.IMPROVEMENT
        >>> print(story["emergent_meanings"])
        ["Sistema aprende más rápido con feedback humano"]
    """
    
    def __init__(
        self,
        causality_confidence_threshold: float = 0.6,
        turning_point_surprise_threshold: float = 0.7,
        max_episodes_in_memory: int = 1000,
    ):
        """
        Args:
            causality_confidence_threshold: Umbral para considerar causalidad válida
            turning_point_surprise_threshold: Umbral de sorpresa para turning points
            max_episodes_in_memory: Límite de episodios almacenados
        """
        self.causality_threshold = causality_confidence_threshold
        self.surprise_threshold = turning_point_surprise_threshold
        self.max_episodes = max_episodes_in_memory
        
        # Almacenamiento de episodios
        self.episodes: Dict[str, Dict] = {}  # episode_id -> episode_data
        
        # Grafo causal
        self.causal_edges: List[CausalEdge] = []
        
        # Narrativa
        self.chapters: List[NarrativeChapter] = []
        self.current_arc: StoryArc = StoryArc.PLATEAU
        
        # Significados emergentes
        self.emergent_meanings: List[EmergentMeaning] = []
        
        # Turning points
        self.turning_points: List[str] = []  # episode_ids
        
        logger.info(
            "Narrative Memory initialized: causality_threshold=%.2f, "
            "surprise_threshold=%.2f",
            causality_confidence_threshold, turning_point_surprise_threshold
        )
    
    def ingest_episode(self, episode_data: Dict) -> None:
        """
        Ingesta un episodio y actualiza la narrativa.
        
        Args:
            episode_data: Datos del episodio
                         Debe incluir: {"episode_id", "timestamp", "anomaly_type",
                                       "action_taken", "result", "surprise_score"}
        """
        episode_id = episode_data["episode_id"]
        
        # Almacenar episodio
        self.episodes[episode_id] = episode_data
        
        # Mantener límite
        if len(self.episodes) > self.max_episodes:
            # Remover episodios más antiguos que no sean turning points
            sorted_ids = sorted(
                self.episodes.keys(),
                key=lambda eid: self.episodes[eid]["timestamp"]
            )
            
            for eid in sorted_ids:
                if eid not in self.turning_points and len(self.episodes) > self.max_episodes:
                    del self.episodes[eid]
                if len(self.episodes) <= self.max_episodes:
                    break
        
        # Detectar causalidad con episodios recientes
        self._infer_causal_edges(episode_id)
        
        # Detectar turning points
        if episode_data.get("surprise_score", 0.0) >= self.surprise_threshold:
            self._mark_turning_point(episode_id, episode_data)
        
        # Actualizar narrativa
        self._update_narrative()
        
        logger.debug("Ingested episode: %s", episode_id)
    
    def _infer_causal_edges(self, new_episode_id: str) -> None:
        """
        Infiere conexiones causales con episodios recientes.
        
        Usa heurística Granger-style:
        - Temporal precedence (A antes que B)
        - Correlation (A y B relacionados)
        - No spuriousness (no hay C que explique ambos)
        """
        new_episode = self.episodes[new_episode_id]
        new_timestamp = new_episode["timestamp"]
        
        # Buscar episodios en ventana temporal (últimas 24h)
        window = timedelta(hours=24)
        
        for candidate_id, candidate_data in self.episodes.items():
            if candidate_id == new_episode_id:
                continue
            
            candidate_timestamp = candidate_data["timestamp"]
            
            # Temporal precedence
            if candidate_timestamp >= new_timestamp:
                continue
            
            temporal_gap = new_timestamp - candidate_timestamp
            if temporal_gap > window:
                continue
            
            # Calcular causalidad
            relation, confidence = self._estimate_causality(
                candidate_data, new_episode, temporal_gap
            )
            
            if confidence >= self.causality_threshold:
                edge = CausalEdge(
                    from_episode_id=candidate_id,
                    to_episode_id=new_episode_id,
                    relation_type=relation,
                    confidence=confidence,
                    temporal_gap=temporal_gap,
                    evidence=self._generate_causal_evidence(
                        candidate_data, new_episode
                    ),
                )
                
                self.causal_edges.append(edge)
                
                logger.debug("Causal edge detected: %s", edge)
    
    def _estimate_causality(
        self,
        cause_episode: Dict,
        effect_episode: Dict,
        temporal_gap: timedelta,
    ) -> Tuple[CausalRelation, float]:
        """
        Estima tipo y confianza de causalidad.
        
        Returns:
            (CausalRelation, confidence)
        """
        # Factor 1: Temporal proximity (más cercano = más probable)
        proximity_score = 1.0 / (1.0 + temporal_gap.total_seconds() / 3600.0)
        
        # Factor 2: Domain similarity
        cause_domain = cause_episode.get("anomaly_type", "unknown")
        effect_domain = effect_episode.get("anomaly_type", "unknown")
        
        domain_similarity = 1.0 if cause_domain == effect_domain else 0.5
        
        # Factor 3: Action-Result correlation
        cause_action = cause_episode.get("action_taken", "none")
        cause_result = cause_episode.get("result", {}).get("status", "unknown")
        effect_type = effect_episode.get("anomaly_type", "unknown")
        
        # Heurística simple: éxito en A → menos anomalías tipo B
        if cause_result == "resolved" and effect_type == cause_domain:
            action_correlation = 0.3  # Posible prevención
            relation_type = CausalRelation.PREVENTING
        elif cause_result == "worsened" and effect_type == cause_domain:
            action_correlation = 0.8  # Probable causalidad directa
            relation_type = CausalRelation.DIRECT_CAUSE
        elif cause_action != "none" and effect_type != cause_domain:
            action_correlation = 0.4  # Posible enabling
            relation_type = CausalRelation.ENABLING
        else:
            action_correlation = 0.2  # Correlación débil
            relation_type = CausalRelation.CORRELATIONAL
        
        # Confianza total
        confidence = (
            proximity_score * 0.3 +
            domain_similarity * 0.3 +
            action_correlation * 0.4
        )
        
        return relation_type, confidence
    
    def _generate_causal_evidence(
        self, cause_episode: Dict, effect_episode: Dict
    ) -> List[str]:
        """Genera evidencias textuales de causalidad."""
        evidence = []
        
        # Evidencia temporal
        temporal_gap = effect_episode["timestamp"] - cause_episode["timestamp"]
        evidence.append(f"Temporal gap: {temporal_gap}")
        
        # Evidencia de dominio
        if cause_episode.get("anomaly_type") == effect_episode.get("anomaly_type"):
            evidence.append(f"Same domain: {cause_episode['anomaly_type']}")
        
        # Evidencia de acción
        if cause_episode.get("action_taken") != "none":
            evidence.append(
                f"Action taken in cause: {cause_episode['action_taken']}"
            )
        
        # Evidencia de resultado
        cause_result = cause_episode.get("result", {}).get("status", "unknown")
        if cause_result in ["resolved", "worsened"]:
            evidence.append(f"Cause resulted in: {cause_result}")
        
        return evidence
    
    def _mark_turning_point(self, episode_id: str, episode_data: Dict) -> None:
        """Marca un episodio como turning point."""
        if episode_id not in self.turning_points:
            self.turning_points.append(episode_id)
            
            logger.info(
                "Turning point detected: %s (surprise: %.2f)",
                episode_id, episode_data.get("surprise_score", 0.0)
            )
    
    def _update_narrative(self) -> None:
        """Actualiza la narrativa global (arc, chapters, emergent meanings)."""
        if len(self.episodes) < 3:
            return  # Necesitamos al menos 3 episodios para narrativa
        
        # Detectar arc actual
        self.current_arc = self._detect_story_arc()
        
        # Construir chapters
        self._construct_chapters()
        
        # Detectar emergent meanings
        self._detect_emergent_meanings()
    
    def _detect_story_arc(self) -> StoryArc:
        """Detecta el arco narrativo actual basado en episodios recientes."""
        # Obtener últimos 10 episodios
        recent_ids = sorted(
            self.episodes.keys(),
            key=lambda eid: self.episodes[eid]["timestamp"]
        )[-10:]
        
        if not recent_ids:
            return StoryArc.PLATEAU
        
        # Calcular "success rate" en cada episodio
        success_scores = []
        for eid in recent_ids:
            ep = self.episodes[eid]
            result_status = ep.get("result", {}).get("status", "unknown")
            
            if result_status == "resolved":
                success_scores.append(1.0)
            elif result_status == "worsened":
                success_scores.append(0.0)
            else:
                success_scores.append(0.5)
        
        # Calcular tendencia (slope aproximada)
        if len(success_scores) >= 3:
            # Slope = (últimos 3 promedio) - (primeros 3 promedio)
            early_avg = sum(success_scores[:3]) / 3
            late_avg = sum(success_scores[-3:]) / 3
            slope = late_avg - early_avg
            
            # Calcular volatilidad
            variance = sum((s - sum(success_scores) / len(success_scores)) ** 2
                          for s in success_scores) / len(success_scores)
            
            # Clasificar arc
            if variance > 0.15:
                return StoryArc.VOLATILE
            elif slope > 0.15:
                return StoryArc.IMPROVEMENT
            elif slope < -0.15:
                # Detectar recovery (decline seguido de improvement)
                mid_avg = sum(success_scores[3:6]) / 3 if len(success_scores) >= 6 else late_avg
                if mid_avg < early_avg and late_avg > mid_avg:
                    return StoryArc.RECOVERY
                else:
                    return StoryArc.DECLINE
            else:
                return StoryArc.PLATEAU
        
        return StoryArc.PLATEAU
    
    def _construct_chapters(self) -> None:
        """Construye capítulos de la narrativa agrupando episodios relacionados."""
        # Agrupar por turning points y arcos
        # Simplificación: 1 chapter por cada grupo de episodios entre turning points
        
        if not self.episodes:
            return
        
        sorted_ids = sorted(
            self.episodes.keys(),
            key=lambda eid: self.episodes[eid]["timestamp"]
        )
        
        # Dividir en chapters por turning points
        chapter_groups = []
        current_group = []
        
        for eid in sorted_ids:
            current_group.append(eid)
            
            if eid in self.turning_points:
                # Finalizar chapter
                chapter_groups.append(current_group)
                current_group = []
        
        # Agregar último grupo si existe
        if current_group:
            chapter_groups.append(current_group)
        
        # Crear chapters
        self.chapters = []
        for i, group in enumerate(chapter_groups):
            if not group:
                continue
            
            start_ep = self.episodes[group[0]]
            end_ep = self.episodes[group[-1]]
            
            # Detectar arc del chapter
            chapter_arc = self._detect_chapter_arc(group)
            
            # Generar summary
            summary = self._generate_chapter_summary(group, chapter_arc)
            
            # Key insights
            insights = self._extract_chapter_insights(group)
            
            # Turning points en el chapter
            chapter_turning_points = [
                eid for eid in group if eid in self.turning_points
            ]
            
            chapter = NarrativeChapter(
                chapter_id=f"chapter_{i}",
                title=f"Chapter {i}: {chapter_arc.value.title()}",
                episodes=group,
                story_arc=chapter_arc,
                start_time=start_ep["timestamp"],
                end_time=end_ep["timestamp"],
                summary=summary,
                key_insights=insights,
                turning_points=chapter_turning_points,
            )
            
            self.chapters.append(chapter)
    
    def _detect_chapter_arc(self, episode_ids: List[str]) -> StoryArc:
        """Detecta arc de un chapter específico."""
        # Similar a _detect_story_arc pero para subset
        if len(episode_ids) < 3:
            return StoryArc.PLATEAU
        
        success_scores = []
        for eid in episode_ids:
            result_status = self.episodes[eid].get("result", {}).get("status", "unknown")
            success_scores.append(
                1.0 if result_status == "resolved"
                else 0.0 if result_status == "worsened"
                else 0.5
            )
        
        early = sum(success_scores[:len(success_scores)//3])
        late = sum(success_scores[-len(success_scores)//3:])
        
        slope = (late - early) / len(success_scores)
        
        if slope > 0.1:
            return StoryArc.IMPROVEMENT
        elif slope < -0.1:
            return StoryArc.DECLINE
        else:
            return StoryArc.PLATEAU
    
    def _generate_chapter_summary(
        self, episode_ids: List[str], arc: StoryArc
    ) -> str:
        """Genera resumen narrativo del chapter."""
        ep_count = len(episode_ids)
        
        # Contar tipos de anomalías
        anomaly_types = [
            self.episodes[eid].get("anomaly_type", "unknown")
            for eid in episode_ids
        ]
        most_common = max(set(anomaly_types), key=anomaly_types.count)
        
        # Contar resultados
        resolved = sum(
            1 for eid in episode_ids
            if self.episodes[eid].get("result", {}).get("status") == "resolved"
        )
        
        summary = (
            f"{arc.value.title()} period with {ep_count} episodes. "
            f"Most common issue: {most_common}. "
            f"Resolved: {resolved}/{ep_count}."
        )
        
        return summary
    
    def _extract_chapter_insights(self, episode_ids: List[str]) -> List[str]:
        """Extrae insights clave del chapter."""
        insights = []
        
        # Insight 1: Acción más efectiva
        actions = [
            self.episodes[eid].get("action_taken", "none")
            for eid in episode_ids
            if self.episodes[eid].get("result", {}).get("status") == "resolved"
        ]
        
        if actions:
            most_effective = max(set(actions), key=actions.count)
            insights.append(f"Most effective action: {most_effective}")
        
        # Insight 2: Patrón temporal
        timestamps = [self.episodes[eid]["timestamp"] for eid in episode_ids]
        if len(timestamps) >= 2:
            duration = timestamps[-1] - timestamps[0]
            insights.append(f"Duration: {duration}")
        
        return insights
    
    def _detect_emergent_meanings(self) -> None:
        """Detecta patrones emergentes en la narrativa."""
        # Patrón 1: "Learning effect" - mejoras aceleradas con tiempo
        if self._detect_learning_effect():
            self._register_emergent_meaning(
                pattern_id="learning_effect",
                description="Sistema demuestra aprendizaje acelerado con experiencia",
                implications=["Confiar más en acciones autónomas futuras"],
            )
        
        # Patrón 2: "Cascading failures" - fallos que generan más fallos
        if self._detect_cascading_failures():
            self._register_emergent_meaning(
                pattern_id="cascading_failures",
                description="Fallos tienden a generar fallos subsecuentes",
                implications=["Intervenir temprano para evitar cascadas"],
            )
    
    def _detect_learning_effect(self) -> bool:
        """Detecta si el sistema mejora más rápido con tiempo."""
        # Necesitamos al menos 2 chapters
        if len(self.chapters) < 2:
            return False
        
        # Comparar primeros chapters vs últimos
        early_chapters = self.chapters[:len(self.chapters)//2]
        late_chapters = self.chapters[len(self.chapters)//2:]
        
        # Calcular success rate promedio
        early_success = self._calculate_chapter_success_rate(early_chapters)
        late_success = self._calculate_chapter_success_rate(late_chapters)
        
        # Learning effect = mejora > 20%
        return late_success > early_success + 0.2
    
    def _detect_cascading_failures(self) -> bool:
        """Detecta si los fallos tienden a causar más fallos."""
        # Buscar causal edges tipo DIRECT_CAUSE entre episodios "worsened"
        cascading_count = 0
        
        for edge in self.causal_edges:
            from_ep = self.episodes.get(edge.from_episode_id)
            to_ep = self.episodes.get(edge.to_episode_id)
            
            if (from_ep and to_ep and
                edge.relation_type == CausalRelation.DIRECT_CAUSE and
                from_ep.get("result", {}).get("status") == "worsened" and
                to_ep.get("anomaly_type") != "none"):
                cascading_count += 1
        
        # Si > 30% de edges son cascading failures
        return cascading_count / max(len(self.causal_edges), 1) > 0.3
    
    def _calculate_chapter_success_rate(
        self, chapters: List[NarrativeChapter]
    ) -> float:
        """Calcula success rate promedio de chapters."""
        total_resolved = 0
        total_episodes = 0
        
        for chapter in chapters:
            for eid in chapter.episodes:
                total_episodes += 1
                if self.episodes[eid].get("result", {}).get("status") == "resolved":
                    total_resolved += 1
        
        return total_resolved / total_episodes if total_episodes > 0 else 0.0
    
    def _register_emergent_meaning(
        self, pattern_id: str, description: str, implications: List[str]
    ) -> None:
        """Registra un significado emergente."""
        # Verificar si ya existe
        existing = next(
            (em for em in self.emergent_meanings if em.pattern_id == pattern_id),
            None
        )
        
        if existing:
            # Actualizar existente
            existing.last_reinforced = datetime.now()
            existing.confidence = min(existing.confidence + 0.1, 1.0)
            existing.implications = implications
        else:
            # Crear nuevo
            supporting_episodes = list(self.episodes.keys())[-10:]  # Últimos 10
            
            emergent = EmergentMeaning(
                pattern_id=pattern_id,
                description=description,
                supporting_episodes=supporting_episodes,
                confidence=0.7,
                first_detected=datetime.now(),
                last_reinforced=datetime.now(),
                implications=implications,
            )
            
            self.emergent_meanings.append(emergent)
            
            logger.info("Emergent meaning detected: %s", emergent)
    
    def construct_narrative(
        self, time_window: Optional[timedelta] = None
    ) -> Dict:
        """
        Construye narrativa completa para una ventana temporal.
        
        Args:
            time_window: Ventana temporal (None = toda la historia)
        
        Returns:
            Dict con narrative completo: arc, chapters, emergent meanings, etc.
        """
        # Filtrar episodios por ventana
        if time_window:
            cutoff = datetime.now() - time_window
            filtered_ids = [
                eid for eid in self.episodes
                if self.episodes[eid]["timestamp"] >= cutoff
            ]
        else:
            filtered_ids = list(self.episodes.keys())
        
        # Estadísticas
        total_episodes = len(filtered_ids)
        total_causal_edges = len([
            e for e in self.causal_edges
            if e.from_episode_id in filtered_ids and e.to_episode_id in filtered_ids
        ])
        
        return {
            "current_arc": self.current_arc.value,
            "total_episodes": total_episodes,
            "total_chapters": len(self.chapters),
            "total_causal_edges": total_causal_edges,
            "turning_points_count": len([
                tp for tp in self.turning_points if tp in filtered_ids
            ]),
            "chapters": [
                {
                    "title": ch.title,
                    "arc": ch.story_arc.value,
                    "summary": ch.summary,
                    "insights": ch.key_insights,
                    "episodes_count": len(ch.episodes),
                }
                for ch in self.chapters
            ],
            "emergent_meanings": [
                {
                    "pattern": em.pattern_id,
                    "description": em.description,
                    "confidence": em.confidence,
                    "implications": em.implications,
                }
                for em in self.emergent_meanings
            ],
            "narrative_summary": self._generate_narrative_summary(),
        }
    
    def _generate_narrative_summary(self) -> str:
        """Genera resumen narrativo de toda la historia."""
        if not self.chapters:
            return "No narrative chapters available yet."
        
        # Construir historia
        summary_parts = []
        
        # Introducción
        summary_parts.append(
            f"HLCS narrative across {len(self.chapters)} chapters "
            f"and {len(self.episodes)} episodes."
        )
        
        # Arc actual
        summary_parts.append(f"Current trajectory: {self.current_arc.value}.")
        
        # Emergent meanings
        if self.emergent_meanings:
            summary_parts.append(
                f"Key insights: {', '.join(em.description for em in self.emergent_meanings)}."
            )
        
        # Turning points
        if self.turning_points:
            summary_parts.append(
                f"Critical turning points: {len(self.turning_points)} detected."
            )
        
        return " ".join(summary_parts)


# Exports
__all__ = [
    "NarrativeMemory",
    "CausalEdge",
    "CausalRelation",
    "NarrativeChapter",
    "StoryArc",
    "EmergentMeaning",
]
