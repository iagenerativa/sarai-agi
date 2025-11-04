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
        """Análisis multimodal con Qwen3-VL:4B (PLACEHOLDER)"""
        # PLACEHOLDER: Aquí integrarías con Qwen3-VL:4B para análisis real
        return {
            "topics": ["technology", "social impact", "innovation"],
            "emotions": {"interest": 0.7, "surprise": 0.3},
            "social_implications": ["digital transformation", "workplace changes"],
            "cultural_relevance": {"global": 0.8, "LATAM": 0.6}
        }
    
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
