"""
SARAi AGI - Sistema Integrador Principal
==========================================

Conecta todos los componentes de SARAi en un sistema cohesivo end-to-end:

TRM Classifier → MCP → Emotion → Cascade Router → Model Pool → RAG Agent → Response

Este módulo proporciona factory functions reales que reemplazan los placeholders
del sistema de pipeline, conectando todos los subsistemas de SARAi.

Arquitectura de Integración
----------------------------

1. **INPUT STAGE**
   - Input parsing y validación
   - Detección de contexto inicial

2. **CLASSIFICATION STAGE** (TRM Classifier)
   - Scores: hard, soft, web_query
   - Complejidad técnica vs emocional

3. **WEIGHTING STAGE** (MCP)
   - Alpha/Beta calculation
   - Routing weights para expert/empathy

4. **EMOTION DETECTION** (Emotional Context Engine)
   - 16 emociones detectadas
   - 8 culturas regionales
   - Niveles de empatía

5. **ROUTING STAGE** (Cascade Router)
   - Confidence-based routing
   - LFM2 → MiniCPM → Qwen-3 escalation
   - Vision/Code/RAG specialized routing

6. **EXECUTION STAGE** (Model Pool + RAG)
   - Dynamic quantization
   - RAG para web queries (score ≥0.7)
   - Response generation

7. **POST-PROCESSING** (Fluidity - pendiente)
   - Tone smoothing
   - Response enhancement

Version: v3.6.0
Author: SARAi Team
License: MIT

Example
-------
>>> from sarai_agi.core.integrator import create_integrated_pipeline
>>> import asyncio
>>>
>>> # Create fully integrated pipeline
>>> pipeline = create_integrated_pipeline()
>>>
>>> # Execute query
>>> async def main():
...     result = await pipeline.run({
...         "input": "¿Cómo funciona el aprendizaje por refuerzo?"
...     })
...     print(result["response"])
...     print(result["metadata"]["agent"])  # expert/empathy/balanced
...     print(result["metadata"]["emotion"])  # NEUTRAL/CONFUSED/etc
...     await pipeline.shutdown()
>>>
>>> asyncio.run(main())
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

# NOTE: Evitar imports de módulos que requieren torch en nivel de módulo
# Todos los imports condicionales se hacen dentro de las factory functions

from ..configuration import get_section, load_settings
from ..pipeline import PipelineDependencies, create_parallel_pipeline

logger = logging.getLogger(__name__)


# ============================================================================
# Factory Functions - Real Component Connections
# ============================================================================

def create_trm_classifier_callable(config: Optional[Dict[str, Any]] = None):
    """
    Factory para TRM Classifier con fallback graceful.

    Si torch no disponible o modelo no encontrado, devuelve
    clasificador basado en reglas simples.

    Args:
        config: Configuración opcional (path al modelo, etc.)

    Returns:
        Callable que acepta state dict y devuelve scores dict
    """
    try:
        # Import condicional dentro de la función
        from ..classifier import trm

        if not trm.HAS_TORCH:
            logger.warning("TRM Classifier: torch no disponible, usando fallback basado en reglas")
            return _create_rule_based_classifier()

        settings = load_settings()
        classifier_config = get_section(settings, "classifier", default={})

        if config:
            classifier_config.update(config)

        model_path = classifier_config.get("model_path")

        if model_path and Path(model_path).exists():
            logger.info("TRM Classifier: cargando modelo desde %s", model_path)
            classifier = trm.TRMClassifier()
            classifier.load_checkpoint(model_path)

            def trm_callable(state: Dict[str, Any]) -> Dict[str, float]:
                text = state.get("input", "")
                scores = classifier.classify(text)
                logger.debug("TRM scores: %s", scores)
                return scores

            return trm_callable
        else:
            logger.warning("TRM Classifier: modelo no encontrado en %s, usando fallback", model_path)
            return _create_rule_based_classifier()

    except Exception as exc:
        logger.exception("Error creando TRM Classifier: %s", exc)
        return _create_rule_based_classifier()


def _create_rule_based_classifier():
    """Clasificador basado en reglas como fallback."""

    def rule_based_classifier(state: Dict[str, Any]) -> Dict[str, float]:
        text = str(state.get("input", "")).lower()

        # Reglas simples basadas en keywords
        hard_keywords = ["código", "code", "python", "algoritmo", "error", "debug", "función"]
        soft_keywords = ["siento", "emoción", "ayuda", "triste", "feliz", "preocup"]
        web_keywords = ["clima", "noticias", "actualidad", "hoy", "ahora", "último"]

        hard_score = sum(1 for kw in hard_keywords if kw in text) / len(hard_keywords)
        soft_score = sum(1 for kw in soft_keywords if kw in text) / len(soft_keywords)
        web_score = sum(1 for kw in web_keywords if kw in text) / len(web_keywords)

        # Normalizar
        total = hard_score + soft_score + web_score
        if total > 0:
            hard_score /= total
            soft_score /= total
            web_score /= total
        else:
            hard_score = 0.5
            soft_score = 0.5
            web_score = 0.0

        scores = {
            "hard": min(max(hard_score, 0.0), 1.0),
            "soft": min(max(soft_score, 0.0), 1.0),
            "web_query": min(max(web_score, 0.0), 1.0),
        }

        logger.debug("Rule-based classifier scores: %s", scores)
        return scores

    return rule_based_classifier


def create_mcp_weighter_callable(config: Optional[Dict[str, Any]] = None):
    """
    Factory para MCP weighter (alpha/beta calculation).

    Usa MCPCore con modo rules-based o learned según disponibilidad.

    Args:
        config: Configuración opcional

    Returns:
        Callable que acepta state dict y devuelve weights dict
    """
    try:
        # Import condicional dentro de la función
        from ..mcp import core as mcp_module

        settings = load_settings()
        mcp_config = get_section(settings, "mcp", default={})

        if config:
            mcp_config.update(config)

        if not mcp_module.HAS_TORCH:
            logger.warning("MCP: torch no disponible, usando solo rules-based mode")

        mcp = mcp_module.MCPCore(
            mode="rules" if not mcp_module.HAS_TORCH else mcp_config.get("mode", "rules"),
            embedder=None,  # TODO: integrar embedder real
        )

        def mcp_callable(state: Dict[str, Any]) -> Dict[str, float]:
            text = state.get("input", "")
            hard_score = state.get("hard", 0.5)
            soft_score = state.get("soft", 0.5)

            alpha, beta = mcp.compute_weights(
                context=text,
                hard_score=hard_score,
                soft_score=soft_score,
            )

            weights = {"alpha": alpha, "beta": beta}
            logger.debug("MCP weights: %s", weights)
            return weights

        return mcp_callable

    except Exception as exc:
        logger.exception("Error creando MCP weighter: %s", exc)
        return _create_fallback_weighter()


def _create_fallback_weighter():
    """Weighter simple basado en scores como fallback."""

    def fallback_weighter(state: Dict[str, Any]) -> Dict[str, float]:
        hard_score = state.get("hard", 0.5)
        soft_score = state.get("soft", 0.5)

        # Alpha = confianza en hard (experto)
        # Beta = confianza en soft (empatía)
        alpha = min(max(hard_score, 0.0), 1.0)
        beta = min(max(soft_score, 0.0), 1.0)

        weights = {"alpha": alpha, "beta": beta}
        logger.debug("Fallback weighter: %s", weights)
        return weights

    return fallback_weighter


def create_emotion_detector_callable(config: Optional[Dict[str, Any]] = None):
    """
    Factory para Emotion Detector.

    Usa EmotionalContextEngine para detectar emociones y culturas.

    Args:
        config: Configuración opcional

    Returns:
        Callable que acepta audio bytes y devuelve emotion dict
    """
    try:
        # Import condicional
        from ..emotion.context_engine import EmotionalContextEngine

        engine = EmotionalContextEngine()

        def emotion_callable(audio_or_text: Any) -> Optional[Dict[str, Any]]:
            # Si es bytes, asumir audio (por ahora no procesamos audio)
            if isinstance(audio_or_text, bytes):
                logger.debug("Emotion detector: audio input detectado (no implementado aún)")
                return None

            # Si es dict con 'input', extraer texto
            if isinstance(audio_or_text, dict):
                text = audio_or_text.get("input", "")
            else:
                text = str(audio_or_text)

            if not text:
                return None

            result = engine.analyze_emotional_context(text)

            emotion_dict = {
                "emotion": result.detected_emotion.value,
                "confidence": result.confidence,
                "empathy_level": result.empathy_level,
                "cultural_context": result.cultural_context.value if result.cultural_context else "neutral",
                "voice_modulation": result.voice_modulation,
            }

            logger.debug("Emotion detected: %s (confidence=%.2f)", emotion_dict["emotion"], emotion_dict["confidence"])
            return emotion_dict

        return emotion_callable

    except Exception as exc:
        logger.exception("Error creando emotion detector: %s", exc)
        return lambda x: None


def create_router_callable(config: Optional[Dict[str, Any]] = None):
    """
    Factory para Router (Cascade + Multimodal).

    Integra ConfidenceRouter para routing inteligente entre
    expert/empathy/balanced según alpha/beta/emotion.

    Args:
        config: Configuración opcional

    Returns:
        Callable que acepta state dict y devuelve agent_key str
    """
    try:
        # Import condicional
        from ..cascade.confidence_router import ConfidenceRouter

        confidence_router = ConfidenceRouter()

        def router_callable(state: Dict[str, Any]) -> str:
            alpha = float(state.get("alpha", 0.5))
            beta = float(state.get("beta", 0.5))
            web_query = float(state.get("web_query", 0.0))

            # Priority 1: Vision queries (pendiente integración)
            # if state.get("has_image"):
            #     return "vision"

            # Priority 2: Code queries (pendiente integración)
            # if alpha >= 0.8 and "code" in state.get("input", "").lower():
            #     return "code"

            # Priority 3: RAG queries
            if web_query >= 0.7:
                logger.debug("Router: RAG agent selected (web_query=%.2f)", web_query)
                return "rag"

            # Priority 4: Expert vs Empathy routing
            if alpha >= 0.7:
                logger.debug("Router: Expert agent selected (alpha=%.2f)", alpha)
                return "expert"
            elif beta >= 0.7:
                logger.debug("Router: Empathy agent selected (beta=%.2f)", beta)
                return "empathy"
            else:
                logger.debug("Router: Balanced agent selected (alpha=%.2f, beta=%.2f)", alpha, beta)
                return "balanced"

        return router_callable

    except Exception as exc:
        logger.exception("Error creando router: %s", exc)
        return lambda state: "balanced"


def create_response_generator_callable(config: Optional[Dict[str, Any]] = None):
    """
    Factory para Response Generator.

    Integra ModelPool + RAG Agent + Cascade Router para generación
    de respuestas con routing inteligente.

    Args:
        config: Configuración opcional

    Returns:
        Callable que acepta (state, agent_key) y devuelve response str
    """
    try:
        # Imports condicionales
        from ..agents.rag import execute_rag
        from ..cascade.confidence_router import ConfidenceRouter
        from ..model.pool import ModelPool

        model_pool = ModelPool()
        confidence_router = ConfidenceRouter()

        def response_generator(state: Dict[str, Any], agent_key: str) -> str:
            text = state.get("input", "")

            # RAG Agent routing
            if agent_key == "rag":
                logger.info("Response Generator: Ejecutando RAG Agent")
                try:
                    updated_state = execute_rag(state, model_pool)
                    return str(updated_state.get("response", "Error en RAG Agent"))
                except Exception as exc:
                    logger.exception("RAG Agent falló: %s", exc)
                    # Fallback a expert agent
                    agent_key = "expert"

            # Model selection based on agent_key
            if agent_key == "expert":
                model_name = "expert_short"  # Cascade decidirá si escalar
            elif agent_key == "empathy":
                model_name = "tiny"  # LFM2 modo empatía
            else:  # balanced
                model_name = "expert_short"

            # Get model with auto-quantization
            try:
                model = model_pool.get_for_prompt(model_name, text)

                # Para expert, usar cascade routing
                if agent_key == "expert":
                    from ..model.wrapper import CascadeWrapper

                    # Verificar si el modelo es CascadeWrapper
                    if isinstance(model, CascadeWrapper):
                        response = model.invoke(text)
                    else:
                        # Fallback a invocación directa
                        response = model.invoke(text)
                else:
                    response = model.invoke(text)

                logger.info("Response generada por %s (model=%s)", agent_key, model_name)
                return str(response)

            except Exception as exc:
                logger.exception("Error generando respuesta: %s", exc)
                return f"Error generando respuesta: {exc}"

        return response_generator

    except Exception as exc:
        logger.exception("Error creando response generator: %s", exc)
        return lambda state, agent_key: f"Error: {exc}"


def create_prefetch_callable(config: Optional[Dict[str, Any]] = None):
    """
    Factory para Prefetch (predicción de modelo).

    Analiza input y predice qué modelo se usará para precargarlo.

    Args:
        config: Configuración opcional

    Returns:
        Callable que acepta state dict y devuelve model_name str
    """

    def prefetch_callable(state: Dict[str, Any]) -> Optional[str]:
        text = state.get("input", "")
        alpha = float(state.get("alpha", 0.5))
        web_query = float(state.get("web_query", 0.0))

        # Predicción simple basada en scores
        if web_query >= 0.7:
            return "expert_short"  # RAG usa expert
        elif alpha >= 0.7:
            return "expert_short"
        else:
            return "tiny"

    return prefetch_callable


# ============================================================================
# Integrated Pipeline Factory
# ============================================================================

def create_integrated_pipeline(config: Optional[Dict[str, Any]] = None):
    """
    Crea pipeline completamente integrada con todos los componentes reales.

    Esta es la función principal de integración que conecta:
    - TRM Classifier (clasificación de intenciones)
    - MCP Core (weighting alpha/beta)
    - Emotional Context Engine (detección emocional)
    - Cascade Router (routing inteligente)
    - Model Pool (gestión de modelos)
    - RAG Agent (búsquedas web)

    Args:
        config: Configuración opcional para sobrescribir defaults

    Returns:
        ParallelPipeline completamente integrada y lista para usar

    Example:
        >>> pipeline = create_integrated_pipeline()
        >>> result = await pipeline.run({"input": "¿Cómo está el clima?"})
        >>> print(result["response"])
        >>> await pipeline.shutdown()
    """
    logger.info("Creating integrated SARAi pipeline...")

    dependencies = PipelineDependencies(
        trm_classifier=create_trm_classifier_callable(config),
        mcp_weighter=create_mcp_weighter_callable(config),
        response_generator=create_response_generator_callable(config),
        emotion_detector=create_emotion_detector_callable(config),
        prefetch_model=create_prefetch_callable(config),
        router=create_router_callable(config),
    )

    pipeline = create_parallel_pipeline(dependencies=dependencies, config=config)

    logger.info("Integrated pipeline created successfully")
    return pipeline


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "create_integrated_pipeline",
    "create_trm_classifier_callable",
    "create_mcp_weighter_callable",
    "create_emotion_detector_callable",
    "create_router_callable",
    "create_response_generator_callable",
    "create_prefetch_callable",
]
