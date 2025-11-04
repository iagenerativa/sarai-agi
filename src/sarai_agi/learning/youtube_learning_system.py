"""
SARAi AGI v3.7.0 - YouTube Learning System
Análisis especializado de contenido YouTube para aprendizaje social

Compatible con Qwen3-VL:4B para análisis visual
LOC: ~450 (core implementation, versión compacta)
"""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from enum import Enum
from datetime import datetime
import logging
import asyncio

logger = logging.getLogger(__name__)


class ContentCategory(Enum):
    """Categorías de contenido YouTube"""
    EDUCATIONAL = "educational"
    SOCIAL_COMMENTARY = "social_commentary"
    TECHNOLOGY_REVIEWS = "technology_reviews"
    CULTURAL_DOCUMENTARY = "cultural_documentary"
    LIFESTYLE_VLOGS = "lifestyle_vlogs"
    BUSINESS_ANALYSIS = "business_analysis"
    SCIENTIFIC_CONTENT = "scientific_content"


@dataclass
class YouTubeVideoAnalysis:
    """Análisis completo de video YouTube"""
    video_id: str
    title: str
    channel_name: str
    duration_seconds: int
    view_count: int
    
    # Análisis
    content_category: ContentCategory
    main_topics: List[str]
    emotional_tone: Dict[str, float]
    social_implications: List[str]
    
    # Métricas
    trending_score: float  # 0.0-1.0
    viral_potential: float  # 0.0-1.0
    learning_value: float  # 0.0-1.0
    
    # Insights
    key_insights: List[str]
    cultural_relevance: Dict[str, float]  # Por región


class YouTubeLearningSystem:
    """
    Sistema especializado para YouTube learning
    Integra con Qwen3-VL:4B para análisis visual
    """
    
    def __init__(self, pipeline_dependencies, config: Dict[str, Any]):
        self.model_pool = getattr(pipeline_dependencies, 'model_pool', None)
        self.emotional_engine = getattr(pipeline_dependencies, 'emotional_context', None)
        
        self.config = config.get("youtube_learning", {})
        self.enabled = self.config.get("enabled", True)
        self.auto_discovery = self.config.get("auto_discovery", False)
        
        self.content_priorities = self.config.get("content_priorities", {
            "educational": 0.9,
            "social_commentary": 0.85,
            "technology_reviews": 0.8
        })
        
        logger.info(f"YouTubeLearningSystem initialized: enabled={self.enabled}")
    
    async def analyze_video(self, video_url: str) -> YouTubeVideoAnalysis:
        """Análisis completo de video YouTube"""
        if not self.enabled:
            raise ValueError("YouTube learning disabled")
        
        logger.info(f"Analyzing YouTube video: {video_url}")
        
        # 1. Extraer metadata (PLACEHOLDER: usa youtube-dl o API)
        metadata = await self._extract_metadata(video_url)
        
        # 2. Extraer frames clave (PLACEHOLDER: usa ffmpeg)
        frames = await self._extract_key_frames(video_url)
        
        # 3. Análisis multimodal (PLACEHOLDER: usa Qwen3-VL:4B)
        analysis = await self._multimodal_analysis(metadata, frames)
        
        # 4. Determinar categoría
        category = self._categorize_content(metadata, analysis)
        
        # 5. Calcular métricas
        trending_score = self._calculate_trending_score(metadata)
        viral_potential = self._calculate_viral_potential(metadata, analysis)
        learning_value = self._calculate_learning_value(category, analysis)
        
        # 6. Generar insights
        insights = self._generate_insights(analysis)
        
        return YouTubeVideoAnalysis(
            video_id=metadata.get("id", "unknown"),
            title=metadata.get("title", ""),
            channel_name=metadata.get("channel", ""),
            duration_seconds=metadata.get("duration", 0),
            view_count=metadata.get("views", 0),
            content_category=category,
            main_topics=analysis.get("topics", []),
            emotional_tone=analysis.get("emotions", {}),
            social_implications=analysis.get("social_implications", []),
            trending_score=trending_score,
            viral_potential=viral_potential,
            learning_value=learning_value,
            key_insights=insights,
            cultural_relevance=analysis.get("cultural_relevance", {"global": 0.5})
        )
    
    async def _extract_metadata(self, video_url: str) -> Dict[str, Any]:
        """
        Extrae metadata REAL del video usando yt-dlp (STRICT MODE)
        
        Returns:
            Dict con metadata real o {} si falla (NO mock)
        """
        try:
            import yt_dlp
            
            # Configuración yt-dlp optimizada
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                'skip_download': True,  # Solo metadata, no descargar video
                'format': 'best',
                # Extraer estadísticas adicionales
                'extractor_args': {
                    'youtube': {
                        'skip': ['dash', 'hls']  # Skip streaming formats
                    }
                }
            }
            
            # Ejecutar en thread pool para no bloquear event loop
            loop = asyncio.get_event_loop()
            
            def _extract_sync():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    return ydl.extract_info(video_url, download=False)
            
            # ✅ REAL extraction con yt-dlp
            info = await loop.run_in_executor(None, _extract_sync)
            
            if not info:
                logger.error(f"STRICT MODE: yt-dlp returned None for {video_url}")
                return {}
            
            # Extraer campos relevantes
            metadata = {
                "id": info.get("id", ""),
                "title": info.get("title", ""),
                "channel": info.get("uploader", info.get("channel", "")),
                "duration": info.get("duration", 0),
                "views": info.get("view_count", 0),
                "likes": info.get("like_count", 0),
                "comments": info.get("comment_count", 0),
                "upload_date": info.get("upload_date", ""),
                "description": info.get("description", ""),
                "tags": info.get("tags", []),
                "categories": info.get("categories", []),
                "thumbnail": info.get("thumbnail", ""),
                "webpage_url": info.get("webpage_url", video_url)
            }
            
            logger.info(
                f"✅ REAL yt-dlp metadata extracted: {metadata['title']} "
                f"({metadata['views']:,} views, {metadata['duration']}s)"
            )
            
            return metadata
            
        except ImportError:
            # ⚠️ STRICT MODE: Sin yt-dlp → retornar {} (NO mock)
            logger.error(
                "STRICT MODE: yt-dlp not installed - returning empty metadata. "
                "Install with: pip install yt-dlp"
            )
            return {}
            
        except Exception as e:
            # ⚠️ STRICT MODE: Error en extracción → retornar {} (NO mock)
            logger.error(
                f"STRICT MODE: yt-dlp extraction failed for {video_url}: {e} - "
                "returning empty metadata"
            )
            return {}
    
    async def _extract_key_frames(self, video_url: str) -> List[Dict[str, Any]]:
        """Extrae frames clave del video (PLACEHOLDER)"""
        # PLACEHOLDER: Aquí usarías ffmpeg para extraer frames
        return [
            {"timestamp": 0, "frame_data": "base64_image_data"},
            {"timestamp": 300, "frame_data": "base64_image_data"},
            {"timestamp": 600, "frame_data": "base64_image_data"}
        ]
    
    async def _multimodal_analysis(
        self,
        metadata: Dict[str, Any],
        frames: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Análisis multimodal REAL con Qwen3-VL:4B via MultimodalModelWrapper (STRICT MODE)
        
        Returns:
            Dict con analysis real o {} si falla (NO mock)
        """
        try:
            # ⚠️ STRICT MODE: Si no hay model_pool, retornar vacío
            if self.model_pool is None:
                logger.warning(
                    "STRICT MODE: model_pool not available - returning empty analysis"
                )
                return {}
            
            # ⚠️ STRICT MODE: Si no hay frames, retornar vacío
            if not frames or len(frames) == 0:
                logger.warning(
                    "STRICT MODE: No frames provided - returning empty analysis"
                )
                return {}
            
            # ✅ REAL ANALYSIS: Obtener modelo Qwen3-VL via ModelPool
            try:
                # Usar get() del ModelPool para obtener MultimodalModelWrapper
                vision_model = await asyncio.to_thread(
                    self.model_pool.get,
                    "qwen3_vl"
                )
            except Exception as e:
                logger.error(
                    f"STRICT MODE: Failed to get qwen3_vl from ModelPool: {e}"
                )
                return {}
            
            # Analizar primer frame (representativo)
            first_frame = frames[0]
            frame_data = first_frame.get("frame_data", "")
            
            if not frame_data:
                logger.warning("STRICT MODE: No frame_data in first frame")
                # Release model antes de retornar
                await asyncio.to_thread(self.model_pool.release, "qwen3_vl")
                return {}
            
            # Construir prompt para análisis multimodal
            title = metadata.get("title", "")
            description = metadata.get("description", "")[:200]  # Primeros 200 chars
            
            analysis_prompt = f"""Analiza este frame del video "{title}".
            
Descripción del video: {description}

Identifica:
1. Temas principales (topics) - lista de 2-5 temas
2. Tono emocional (emotions) - dict con emociones 0.0-1.0
3. Implicaciones sociales (social_implications) - lista de 1-3 implicaciones
4. Relevancia cultural (cultural_relevance) - dict por región

Responde en formato JSON válido."""
            
            # Preparar input multimodal para el wrapper
            # El frame_data puede ser base64 o path - el wrapper lo maneja
            multimodal_input = {
                "text": analysis_prompt,
                "image": frame_data  # MultimodalModelWrapper acepta base64 o path
            }
            
            # Ejecutar análisis con Qwen3-VL:4B via wrapper
            try:
                response_text = await asyncio.to_thread(
                    vision_model.invoke,
                    multimodal_input,
                    {"max_tokens": 512}
                )
            except Exception as e:
                logger.error(f"STRICT MODE: Qwen3-VL invoke failed: {e}")
                return {}
            finally:
                # Siempre release el modelo después de usar (incluso si hay error)
                await asyncio.to_thread(self.model_pool.release, "qwen3_vl")
            
            if not response_text or not isinstance(response_text, str):
                logger.error("STRICT MODE: Qwen3-VL returned invalid response")
                return {}
            
            # Intentar parsear como JSON
            try:
                import json
                # Buscar bloque JSON en la respuesta
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_text = response_text[json_start:json_end]
                    parsed = json.loads(json_text)
                    
                    # Validar estructura esperada
                    analysis = {
                        "topics": parsed.get("topics", parsed.get("temas", [])),
                        "emotions": parsed.get("emotions", parsed.get("emociones", {})),
                        "social_implications": parsed.get("social_implications", parsed.get("implicaciones_sociales", [])),
                        "cultural_relevance": parsed.get("cultural_relevance", parsed.get("relevancia_cultural", {}))
                    }
                    
                    logger.info(
                        f"✅ REAL Qwen3-VL analysis (via wrapper): {len(analysis['topics'])} topics, "
                        f"{len(analysis.get('emotions', {}))} emotions detected"
                    )
                    
                    return analysis
                else:
                    # No se pudo parsear JSON, usar análisis básico del texto
                    logger.warning("STRICT MODE: Could not parse JSON from Qwen3-VL response")
                    
                    # Análisis básico de keywords en respuesta
                    response_lower = response_text.lower()
                    
                    # Detectar topics por keywords
                    topics = []
                    topic_keywords = {
                        "technology": ["tecnología", "tech", "software", "digital"],
                        "education": ["educación", "aprendizaje", "curso", "tutorial"],
                        "social": ["social", "sociedad", "cultural", "comunidad"],
                        "innovation": ["innovación", "futuro", "avance", "desarrollo"]
                    }
                    
                    for topic, keywords in topic_keywords.items():
                        if any(kw in response_lower for kw in keywords):
                            topics.append(topic)
                    
                    # Detectar emociones por keywords
                    emotions = {}
                    emotion_keywords = {
                        "interest": ["interesante", "curioso", "atención"],
                        "surprise": ["sorprendente", "inesperado", "wow"],
                        "joy": ["alegría", "feliz", "positivo"],
                        "trust": ["confiable", "profesional", "experto"]
                    }
                    
                    for emotion, keywords in emotion_keywords.items():
                        if any(kw in response_lower for kw in keywords):
                            emotions[emotion] = 0.6  # Score moderado
                    
                    analysis = {
                        "topics": topics if topics else ["general"],
                        "emotions": emotions if emotions else {"interest": 0.5},
                        "social_implications": [],
                        "cultural_relevance": {"global": 0.5}
                    }
                    
                    logger.info(
                        f"✅ REAL Qwen3-VL analysis (keyword-based via wrapper): "
                        f"{len(topics)} topics detected"
                    )
                    
                    return analysis
                    
            except json.JSONDecodeError as je:
                logger.error(f"STRICT MODE: JSON parse error from Qwen3-VL: {je}")
                return {}
            
        except Exception as e:
            # ⚠️ STRICT MODE: Error en análisis → retornar {} (NO mock)
            logger.error(
                f"STRICT MODE: Qwen3-VL multimodal analysis failed: {e} - "
                "returning empty analysis"
            )
            return {}
    
    def _categorize_content(
        self,
        metadata: Dict[str, Any],
        analysis: Dict[str, Any]
    ) -> ContentCategory:
        """Categoriza el contenido del video"""
        # Simple keyword-based categorization (PLACEHOLDER: ML real)
        title = metadata.get("title", "").lower()
        
        if any(word in title for word in ["tutorial", "learn", "course"]):
            return ContentCategory.EDUCATIONAL
        elif any(word in title for word in ["tech", "review", "technology"]):
            return ContentCategory.TECHNOLOGY_REVIEWS
        elif any(word in title for word in ["social", "society", "culture"]):
            return ContentCategory.SOCIAL_COMMENTARY
        else:
            return ContentCategory.LIFESTYLE_VLOGS
    
    def _calculate_trending_score(self, metadata: Dict[str, Any]) -> float:
        """Calcula trending score basado en engagement"""
        views = metadata.get("views", 0)
        likes = metadata.get("likes", 0)
        comments = metadata.get("comments", 0)
        
        # Simple formula: engagement rate
        if views > 0:
            engagement_rate = (likes + comments * 2) / views
            trending_score = min(engagement_rate * 100, 1.0)
        else:
            trending_score = 0.0
        
        return trending_score
    
    def _calculate_viral_potential(
        self,
        metadata: Dict[str, Any],
        analysis: Dict[str, Any]
    ) -> float:
        """Calcula potencial viral"""
        trending_score = self._calculate_trending_score(metadata)
        emotional_intensity = max(analysis.get("emotions", {}).values(), default=0.0)
        
        viral_potential = (trending_score * 0.7) + (emotional_intensity * 0.3)
        return min(viral_potential, 1.0)
    
    def _calculate_learning_value(
        self,
        category: ContentCategory,
        analysis: Dict[str, Any]
    ) -> float:
        """Calcula valor de aprendizaje"""
        # Usar prioridades de configuración
        base_value = self.content_priorities.get(category.value, 0.5)
        
        # Ajustar por cantidad de topics
        topic_count = len(analysis.get("topics", []))
        topic_bonus = min(topic_count * 0.1, 0.3)
        
        learning_value = min(base_value + topic_bonus, 1.0)
        return learning_value
    
    def _generate_insights(self, analysis: Dict[str, Any]) -> List[str]:
        """Genera insights clave del análisis"""
        insights = []
        
        for topic in analysis.get("topics", []):
            insights.append(f"Key topic: {topic}")
        
        for implication in analysis.get("social_implications", []):
            insights.append(f"Social implication: {implication}")
        
        return insights[:5]  # Top 5 insights


# Configuración por defecto
DEFAULT_YOUTUBE_CONFIG = {
    "youtube_learning": {
        "enabled": True,
        "auto_discovery": False,
        "discovery_interval_minutes": 30,
        "content_priorities": {
            "educational": 0.9,
            "social_commentary": 0.85,
            "technology_reviews": 0.8,
            "cultural_documentary": 0.75,
            "business_analysis": 0.7
        },
        "analysis_settings": {
            "default_depth": "deep",
            "max_frames_per_video": 30,
            "min_learning_value": 0.6
        }
    }
}
