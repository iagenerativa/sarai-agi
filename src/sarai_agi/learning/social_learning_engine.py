"""
SARAi AGI v3.7.0 - Social Learning Engine
Análisis de contenido social y cultural con emotional adaptation

Compatible con EmotionalContextEngine (16 emociones × 8 culturas)
LOC: ~550 (core implementation)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from enum import Enum
from datetime import datetime
import logging
import asyncio

logger = logging.getLogger(__name__)


class LearningDomain(Enum):
    """Dominios de aprendizaje social y contextual"""
    TECHNOLOGY_TRENDS = "tech_trends"
    SOCIAL_BEHAVIOR = "social_behavior"
    CULTURAL_PATTERNS = "cultural_patterns"
    ECONOMIC_CHANGES = "economic_changes"
    POLITICAL_DYNAMICS = "political_dynamics"
    SCIENTIFIC_PROGRESS = "scientific_progress"
    LIFESTYLE_TRENDS = "lifestyle_trends"
    ARTISTIC_EXPRESSION = "artistic_expression"


@dataclass
class LearningInsight:
    """Insight aprendido del análisis multimodal"""
    domain: LearningDomain
    insight: str
    confidence: float  # 0.0-1.0
    cultural_relevance: List[str]  # Regiones donde aplica
    evidence: List[Dict[str, Any]]  # Evidencia multimodal
    timestamp: datetime = field(default_factory=datetime.now)
    source_count: int = 1
    emotional_context: Optional[Dict[str, float]] = None


class SocialLearningEngine:
    """
    Motor de aprendizaje social y contextual
    Integra con Qwen3-VL:4B y EmotionalContextEngine
    
    Features:
    - 16 emociones × 8 culturas (integración con EmotionalContextEngine)
    - Patrones de comportamiento social automáticos
    - Adaptación cultural por región (LATAM, EU, ASIA, etc.)
    - Insights de lifestyle y cambios sociales
    - Continuous learning 24/7
    """
    
    def __init__(self, pipeline_dependencies, config: Dict[str, Any]):
        """
        Inicializa con integración a sistemas existentes
        
        Args:
            pipeline_dependencies: PipelineDependencies con emotional_context, etc.
            config: Configuración social learning
        """
        # Componentes existentes
        self.emotional_engine = getattr(pipeline_dependencies, 'emotional_context', None)
        self.model_pool = getattr(pipeline_dependencies, 'model_pool', None)
        
        # Configuración
        self.config = config.get("social_learning", {})
        self.enabled = self.config.get("enabled", True)
        self.continuous_learning = self.config.get("continuous_learning", False)
        self.learning_cycle_interval = self.config.get("learning_cycle_interval_minutes", 5)
        
        # Knowledge base (en memoria, TODO: persistir en RAG)
        self.knowledge_base: Dict[LearningDomain, List[LearningInsight]] = {
            domain: [] for domain in LearningDomain
        }
        
        # Cultural patterns por región
        self.cultural_patterns: Dict[str, Dict[str, Any]] = {}
        
        # Regiones culturales soportadas (integra con EmotionalContextEngine)
        self.cultural_regions = self.config.get("cultural_adaptation", {}).get(
            "regions",
            ["LATAM", "NA", "EU", "ASIA", "AFRICA", "OCEANIA", "ME", "SS"]
        )
        
        logger.info(f"SocialLearningEngine initialized: continuous={self.continuous_learning}, "
                   f"regions={len(self.cultural_regions)}")
    
    async def analyze_content_for_insights(
        self,
        content: Dict[str, Any],
        target_domains: List[LearningDomain] = None
    ) -> List[LearningInsight]:
        """
        Analiza contenido multimodal para extraer insights
        
        Args:
            content: Dict con keys: text, visual_frames, audio_transcript, metadata
            target_domains: Dominios específicos a analizar (None = todos)
        
        Returns:
            Lista de insights aprendidos
        """
        if not self.enabled:
            logger.debug("Social learning disabled, skipping analysis")
            return []
        
        if target_domains is None:
            target_domains = list(LearningDomain)
        
        logger.info(f"Analyzing content for {len(target_domains)} domains...")
        
        insights = []
        
        # Análisis emocional (usa EmotionalContextEngine si disponible)
        emotional_context = None
        if self.emotional_engine:
            try:
                emotional_context = await self._analyze_emotional_context(content)
            except Exception as e:
                logger.warning(f"Emotional analysis failed: {e}")
        
        # Análisis por dominio
        for domain in target_domains:
            try:
                domain_insights = await self._analyze_domain_specific(content, domain, emotional_context)
                if domain_insights:
                    insights.extend(domain_insights)
            except Exception as e:
                logger.error(f"Domain analysis failed for {domain.value}: {e}")
        
        # Actualizar knowledge base
        if insights:
            await self._update_knowledge_base(content.get("id", "unknown"), insights)
        
        logger.info(f"Generated {len(insights)} insights from content")
        return insights
    
    async def _analyze_emotional_context(self, content: Dict[str, Any]) -> Dict[str, float]:
        """Analiza contexto emocional usando EmotionalContextEngine (STRICT MODE)"""
        text_content = content.get("text", "")
        
        if not text_content:
            return {}
        
        # ⚠️ STRICT MODE: Si no hay EmotionalContextEngine, retornar vacío (no mock)
        if self.emotional_engine is None:
            logger.warning(
                "STRICT MODE: EmotionalContextEngine not available - returning empty emotions"
            )
            return {}
        
        try:
            # ✅ INTEGRACIÓN REAL: Usar EmotionalContextEngine.analyze_emotional_context()
            user_id = content.get("user_id", "social_learning_anonymous")
            language = content.get("language", "es")
            
            emotional_response = self.emotional_engine.analyze_emotional_context(
                text=text_content,
                user_id=user_id,
                language=language
            )
            
            # Convertir EmotionalResponse a dict con scores (0.0-1.0)
            # EmotionalResponse tiene: detected_emotion, confidence, empathy_level, etc.
            emotion_name = emotional_response.detected_emotion.value
            confidence = emotional_response.confidence
            empathy = emotional_response.empathy_level
            
            # Construir dict de emociones compatible con el sistema
            # Mapear la emoción detectada a score basado en confidence
            emotions = {
                "joy": 0.0,
                "trust": 0.0,
                "fear": 0.0,
                "surprise": 0.0,
                "sadness": 0.0,
                "disgust": 0.0,
                "anger": 0.0,
                "anticipation": 0.0
            }
            
            # Mapear emociones de EmotionalContext a emociones básicas
            emotion_mapping = {
                "excited": {"joy": 0.8, "anticipation": 0.6},
                "frustrated": {"anger": 0.7, "sadness": 0.5},
                "urgent": {"anticipation": 0.8, "fear": 0.3},
                "confused": {"fear": 0.5, "surprise": 0.4},
                "appreciative": {"joy": 0.7, "trust": 0.8},
                "complaining": {"anger": 0.6, "disgust": 0.4},
                "playful": {"joy": 0.8, "surprise": 0.3},
                "friendly": {"joy": 0.6, "trust": 0.7},
                "doubtful": {"fear": 0.4, "surprise": 0.5},
                "empathetic": {"trust": 0.9, "sadness": 0.3},
                "assertive": {"trust": 0.6, "anticipation": 0.5},
                "formal": {"trust": 0.5},
                "informal": {"joy": 0.4, "trust": 0.4},
                "ironic": {"surprise": 0.6, "joy": 0.3},
                "neutral": {"trust": 0.3}
            }
            
            # Aplicar mapping basado en emoción detectada
            if emotion_name in emotion_mapping:
                for basic_emotion, score in emotion_mapping[emotion_name].items():
                    emotions[basic_emotion] = score * confidence
            
            # Ajustar por empathy level (emociones positivas aumentan con alta empatía)
            if empathy > 0.7:
                emotions["trust"] = min(1.0, emotions["trust"] + 0.2)
                emotions["joy"] = min(1.0, emotions["joy"] + 0.1)
            
            logger.info(
                f"✅ REAL EmotionalContext analysis: {emotion_name} "
                f"(confidence={confidence:.2f}, empathy={empathy:.2f})"
            )
            
            return emotions
            
        except Exception as e:
            # ⚠️ STRICT MODE: Log error y retornar vacío (no mock)
            logger.error(
                f"STRICT MODE: EmotionalContextEngine failed ({e}) - returning empty emotions"
            )
            return {}
    
    async def _analyze_domain_specific(
        self,
        content: Dict[str, Any],
        domain: LearningDomain,
        emotional_context: Optional[Dict[str, float]]
    ) -> List[LearningInsight]:
        """Análisis específico por dominio de aprendizaje"""
        insights = []
        
        if domain == LearningDomain.SOCIAL_BEHAVIOR:
            insight = await self._analyze_social_behavior(content, emotional_context)
            if insight:
                insights.append(insight)
        
        elif domain == LearningDomain.TECHNOLOGY_TRENDS:
            insight = await self._analyze_technology_trends(content, emotional_context)
            if insight:
                insights.append(insight)
        
        elif domain == LearningDomain.CULTURAL_PATTERNS:
            insight = await self._analyze_cultural_patterns(content, emotional_context)
            if insight:
                insights.append(insight)
        
        elif domain == LearningDomain.LIFESTYLE_TRENDS:
            insight = await self._analyze_lifestyle_trends(content, emotional_context)
            if insight:
                insights.append(insight)
        
        # TODO: Implementar otros dominios (economic, political, scientific, artistic)
        
        return insights
    
    async def _analyze_social_behavior(
        self,
        content: Dict[str, Any],
        emotional_context: Optional[Dict[str, float]]
    ) -> Optional[LearningInsight]:
        """Analiza comportamientos sociales del contenido"""
        try:
            text = content.get("text", "")
            metadata = content.get("metadata", {})
            
            # Detectar patrones sociales (PLACEHOLDER: NLP real)
            social_keywords = ["family", "friends", "community", "social", "relationship"]
            has_social_content = any(keyword in text.lower() for keyword in social_keywords)
            
            if not has_social_content:
                return None
            
            # Determinar relevancia cultural
            cultural_relevance = []
            if "family" in text.lower():
                cultural_relevance.extend(["LATAM", "ASIA", "ME"])  # Culturas familiares
            if "community" in text.lower():
                cultural_relevance.extend(["AFRICA", "LATAM"])
            
            if not cultural_relevance:
                cultural_relevance = ["global"]
            
            # Crear insight
            insight = LearningInsight(
                domain=LearningDomain.SOCIAL_BEHAVIOR,
                insight=f"Social pattern detected: {text[:100]}...",
                confidence=0.75,
                cultural_relevance=list(set(cultural_relevance)),
                evidence=[{"type": "text", "content": text[:200]}],
                emotional_context=emotional_context
            )
            
            logger.debug(f"Social behavior insight: confidence={insight.confidence:.2f}, "
                        f"regions={len(insight.cultural_relevance)}")
            return insight
        
        except Exception as e:
            logger.error(f"Social behavior analysis failed: {e}")
            return None
    
    async def _analyze_technology_trends(
        self,
        content: Dict[str, Any],
        emotional_context: Optional[Dict[str, float]]
    ) -> Optional[LearningInsight]:
        """Analiza tendencias tecnológicas"""
        try:
            text = content.get("text", "")
            
            # Detectar contenido tech
            tech_keywords = ["AI", "technology", "software", "hardware", "cloud", "IoT"]
            has_tech_content = any(keyword in text for keyword in tech_keywords)
            
            if not has_tech_content:
                return None
            
            insight = LearningInsight(
                domain=LearningDomain.TECHNOLOGY_TRENDS,
                insight=f"Technology trend: {text[:100]}...",
                confidence=0.80,
                cultural_relevance=["global"],  # Tech es generalmente global
                evidence=[{"type": "text", "content": text[:200]}],
                emotional_context=emotional_context
            )
            
            return insight
        
        except Exception as e:
            logger.error(f"Technology trends analysis failed: {e}")
            return None
    
    async def _analyze_cultural_patterns(
        self,
        content: Dict[str, Any],
        emotional_context: Optional[Dict[str, float]]
    ) -> Optional[LearningInsight]:
        """Analiza patrones culturales"""
        try:
            text = content.get("text", "")
            
            # Detectar contenido cultural
            cultural_keywords = ["culture", "tradition", "heritage", "customs", "values"]
            has_cultural_content = any(keyword in text.lower() for keyword in cultural_keywords)
            
            if not has_cultural_content:
                return None
            
            # Detectar región cultural específica (PLACEHOLDER: análisis más sofisticado)
            region_mapping = {
                "latino": "LATAM",
                "asian": "ASIA",
                "european": "EU",
                "african": "AFRICA",
                "american": "NA"
            }
            
            detected_regions = []
            for keyword, region in region_mapping.items():
                if keyword in text.lower():
                    detected_regions.append(region)
            
            if not detected_regions:
                detected_regions = ["global"]
            
            insight = LearningInsight(
                domain=LearningDomain.CULTURAL_PATTERNS,
                insight=f"Cultural pattern: {text[:100]}...",
                confidence=0.70,
                cultural_relevance=detected_regions,
                evidence=[{"type": "text", "content": text[:200]}],
                emotional_context=emotional_context
            )
            
            return insight
        
        except Exception as e:
            logger.error(f"Cultural patterns analysis failed: {e}")
            return None
    
    async def _analyze_lifestyle_trends(
        self,
        content: Dict[str, Any],
        emotional_context: Optional[Dict[str, float]]
    ) -> Optional[LearningInsight]:
        """Analiza tendencias de lifestyle"""
        try:
            text = content.get("text", "")
            
            # Detectar lifestyle content
            lifestyle_keywords = ["fashion", "health", "wellness", "travel", "food", "fitness"]
            has_lifestyle_content = any(keyword in text.lower() for keyword in lifestyle_keywords)
            
            if not has_lifestyle_content:
                return None
            
            insight = LearningInsight(
                domain=LearningDomain.LIFESTYLE_TRENDS,
                insight=f"Lifestyle trend: {text[:100]}...",
                confidence=0.65,
                cultural_relevance=["global"],
                evidence=[{"type": "text", "content": text[:200]}],
                emotional_context=emotional_context
            )
            
            return insight
        
        except Exception as e:
            logger.error(f"Lifestyle trends analysis failed: {e}")
            return None
    
    async def _update_knowledge_base(self, content_id: str, insights: List[LearningInsight]):
        """Actualiza knowledge base con nuevos insights"""
        for insight in insights:
            domain = insight.domain
            
            # Agregar a knowledge base
            self.knowledge_base[domain].append(insight)
            
            # Mantener solo los últimos 100 insights por dominio
            if len(self.knowledge_base[domain]) > 100:
                self.knowledge_base[domain] = self.knowledge_base[domain][-100:]
        
        # Actualizar cultural patterns
        await self._update_cultural_patterns(insights)
        
        logger.debug(f"Knowledge base updated: {len(insights)} new insights")
    
    async def _update_cultural_patterns(self, insights: List[LearningInsight]):
        """Actualiza patrones culturales basado en insights"""
        for insight in insights:
            for region in insight.cultural_relevance:
                if region not in self.cultural_patterns:
                    self.cultural_patterns[region] = {
                        "pattern_count": 0,
                        "avg_confidence": 0.0,
                        "domains": set()
                    }
                
                # Actualizar estadísticas
                pattern = self.cultural_patterns[region]
                pattern["pattern_count"] += 1
                pattern["domains"].add(insight.domain.value)
                
                # Actualizar confidence promedio
                old_avg = pattern["avg_confidence"]
                count = pattern["pattern_count"]
                pattern["avg_confidence"] = ((old_avg * (count - 1)) + insight.confidence) / count
    
    async def get_contextual_response(
        self,
        query: str,
        user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Obtiene respuesta enriquecida con contexto social aprendido
        
        Args:
            query: Consulta del usuario
            user_context: Contexto del usuario (región, cultura, etc.)
        
        Returns:
            Dict con respuesta + insights sociales relevantes
        """
        user_region = user_context.get("region", "global")
        
        # Buscar insights relevantes para la consulta
        relevant_insights = []
        for domain, insights in self.knowledge_base.items():
            for insight in insights:
                # Filtrar por región cultural del usuario
                if user_region in insight.cultural_relevance or "global" in insight.cultural_relevance:
                    # PLACEHOLDER: Aquí iría análisis semántico real
                    # Por ahora, simplemente agregar todos los insights recientes
                    relevant_insights.append(insight)
        
        # Ordenar por confidence y recencia
        relevant_insights.sort(key=lambda x: (x.confidence, x.timestamp), reverse=True)
        
        # Tomar top 5 insights
        top_insights = relevant_insights[:5]
        
        return {
            "query": query,
            "user_region": user_region,
            "relevant_insights": [
                {
                    "domain": i.domain.value,
                    "insight": i.insight,
                    "confidence": i.confidence,
                    "cultural_relevance": i.cultural_relevance
                }
                for i in top_insights
            ],
            "cultural_adaptation": self.cultural_patterns.get(user_region, {})
        }
    
    async def continuous_learning_loop(self):
        """Bucle de aprendizaje continuo (24/7)"""
        if not self.continuous_learning:
            logger.info("Continuous learning disabled")
            return
        
        logger.info(f"Starting continuous learning loop: interval={self.learning_cycle_interval}min")
        
        while self.continuous_learning:
            try:
                # PLACEHOLDER: Aquí integrarías con descubrimiento de contenido trending
                # Por ahora, simplemente sleep
                logger.debug("Continuous learning cycle (placeholder)")
                
                await asyncio.sleep(self.learning_cycle_interval * 60)
            
            except Exception as e:
                logger.error(f"Continuous learning loop error: {e}")
                await asyncio.sleep(60)  # Wait 1 min on error


# Configuración por defecto
DEFAULT_SOCIAL_LEARNING_CONFIG = {
    "social_learning": {
        "enabled": True,
        "continuous_learning": False,  # Manual por defecto
        "learning_cycle_interval_minutes": 5,
        "max_content_per_batch": 10,
        "insight_confidence_threshold": 0.7,
        "cultural_adaptation": {
            "enabled": True,
            "regions": ["LATAM", "NA", "EU", "ASIA", "AFRICA", "OCEANIA", "ME", "SS"],
            "adaptation_strategy": "progressive",
            "cultural_weight": 0.3
        }
    }
}
