"""
SARAi AGI - RAG Agent (Retrieval-Augmented Generation)

Agente de búsqueda web con síntesis LLM.
Migrado desde SARAi_v2 v2.10 con adaptaciones para arquitectura modular.

Características:
- Pipeline de 6 pasos con garantías Sentinel
- Cache persistente (web_cache)
- Auditoría inmutable (web_audit)
- Síntesis con modelo expert (context-aware short/long)
- Fallback a respuestas Sentinel si fallo total

Activación:
- Cuando classifier detecta scores['web_query'] > 0.7
- O cuando MCP enruta al nodo 'execute_rag'
- Safe Mode NO activo

Garantías:
- ✅ 0% regresión (no afecta queries normales)
- ✅ Integridad logs 100% (SHA-256)
- ✅ Autoprotección (Safe Mode trigger si fallo persistente)
- ✅ Latencia P50 RAG: ≤30s

Uso:
    from sarai_agi.agents.rag import execute_rag
    from sarai_agi.model.pool import ModelPool
    
    pool = ModelPool()
    state = {
        "input": "¿Cómo está el clima en Tokio?",
        "scores": {"web_query": 0.9}
    }
    
    result_state = execute_rag(state, pool)
    print(result_state["response"])
"""

import logging
from datetime import datetime
from typing import Dict

# Imports de componentes internos
try:
    from sarai_agi.security.resilience import activate_safe_mode, is_safe_mode
except ImportError:
    import os

    def is_safe_mode() -> bool:
        return os.getenv("SARAI_SAFE_MODE", "false").lower() == "true"

    def activate_safe_mode(reason: str):
        logging.warning(f"Safe Mode trigger (fallback): {reason}")
        os.environ["SARAI_SAFE_MODE"] = "true"

from sarai_agi.memory.web_audit import get_web_audit_logger
from sarai_agi.memory.web_cache import cached_search

logger = logging.getLogger(__name__)


# Respuestas predefinidas de Sentinel (fallback sin búsqueda)
SENTINEL_RESPONSES = {
    "web_search_disabled": (
        "Lo siento, la búsqueda web está temporalmente deshabilitada "
        "debido a que el sistema está en Modo Seguro. "
        "Esto es una medida de protección automática para garantizar "
        "la integridad de mis respuestas. Por favor, intenta de nuevo más tarde "
        "o pregunta algo que pueda responder con mi conocimiento interno."
    ),
    "web_search_failed": (
        "No pude acceder a información actualizada en este momento. "
        "Puedo intentar responder basándome en mi conocimiento interno, "
        "pero ten en cuenta que podría no estar completamente actualizado. "
        "¿Quieres que continúe con esa limitación?"
    ),
    "synthesis_failed": (
        "Encontré información relevante pero tuve problemas al procesarla. "
        "Por seguridad, prefiero no ofrecer una respuesta que podría ser incorrecta. "
        "¿Podrías reformular tu pregunta de manera más específica?"
    ),
    "model_unavailable": (
        "No puedo procesar esta consulta en este momento porque "
        "el modelo de síntesis no está disponible. "
        "Por favor, intenta de nuevo más tarde."
    )
}


def sentinel_response(reason: str) -> Dict:
    """
    Retorna una respuesta Sentinel predefinida
    
    Filosofía SARAi: "Prefiere el silencio selectivo sobre la mentira"
    
    Args:
        reason: Razón del Sentinel (clave en SENTINEL_RESPONSES)
    
    Returns:
        State dict con response, sentinel_triggered, etc.
    """
    response = SENTINEL_RESPONSES.get(
        reason,
        "Lo siento, no puedo procesar esta consulta en este momento por razones de seguridad."
    )

    return {
        "response": response,
        "sentinel_triggered": True,
        "sentinel_reason": reason,
        "timestamp": datetime.now().isoformat()
    }


def execute_rag(state: Dict, model_pool) -> Dict:
    """
    Ejecuta pipeline RAG completo con garantías Sentinel
    
    Pipeline (6 pasos):
    1. GARANTÍA SENTINEL: Verificar Safe Mode
    2. BÚSQUEDA CACHEADA: cached_search() con SearXNG
    3. AUDITORÍA PRE: log_web_query() con SHA-256
    4. SÍNTESIS PROMPT: Prompt engineering con snippets
    5. LLM GENERATION: Expert (short/long según contexto)
    6. AUDITORÍA POST: log_web_query() con response
    
    Args:
        state: State dict con 'input', 'scores', etc.
        model_pool: ModelPool para acceso a modelos expert
    
    Returns:
        state actualizado con 'response' y 'rag_metadata'
    """
    query = state.get("input", "")

    if not query:
        logger.error("RAG Agent: input vacío")
        sentinel = sentinel_response("synthesis_failed")
        state.update(sentinel)
        return state

    # ====== PASO 1: GARANTÍA SENTINEL ======
    if is_safe_mode():
        logger.warning("RAG Agent: Safe Mode activo, búsqueda bloqueada")
        sentinel = sentinel_response("web_search_disabled")
        state.update(sentinel)
        return state

    # ====== PASO 2: BÚSQUEDA CACHEADA ======
    try:
        logger.info(f"RAG Agent: Buscando '{query[:60]}...'")
        search_results = cached_search(query)

        if search_results is None:
            # SearXNG no disponible o timeout
            logger.warning("RAG Agent: Búsqueda falló (SearXNG no disponible)")

            # ====== PASO 3A: AUDITORÍA (error) ======
            audit_logger = get_web_audit_logger()
            audit_logger.log_web_query(
                query=query,
                search_results=None,
                error="searxng_unavailable"
            )

            sentinel = sentinel_response("web_search_failed")
            state.update(sentinel)
            return state

        if len(search_results.get("snippets", [])) == 0:
            # SearXNG retornó 0 resultados
            logger.warning(f"RAG Agent: 0 snippets para '{query[:60]}...'")

            # ====== PASO 3B: AUDITORÍA (0 snippets) ======
            audit_logger = get_web_audit_logger()
            audit_logger.log_web_query(
                query=query,
                search_results=search_results,
                error="zero_snippets"
            )

            sentinel = sentinel_response("web_search_failed")
            state.update(sentinel)
            return state

    except Exception as e:
        logger.error(f"RAG Agent: Error en búsqueda: {e}")

        # Auditar error
        audit_logger = get_web_audit_logger()
        audit_logger.log_web_query(
            query=query,
            search_results=None,
            error=str(e)
        )

        # Trigger Safe Mode si error persistente
        activate_safe_mode(f"rag_search_exception: {e}")

        sentinel = sentinel_response("web_search_failed")
        state.update(sentinel)
        return state

    # ====== PASO 3C: AUDITORÍA PRE-SÍNTESIS ======
    logger.info(f"RAG Agent: {len(search_results['snippets'])} snippets obtenidos")

    # ====== PASO 4: SÍNTESIS PROMPT ======
    try:
        # Construir prompt con snippets
        prompt_parts = [
            "Eres SARAi, una IA que sintetiza información verificable de fuentes web.",
            "Usando ÚNICAMENTE los siguientes extractos, responde a la pregunta del usuario.",
            "REGLAS CRÍTICAS:",
            "- Cita la fuente (URL) cuando uses un extracto",
            "- Si los extractos no contienen la respuesta, "
            "di 'No encontré información concluyente'",
            "- NO inventes información que no esté en los extractos",
            "- Sé conciso y directo",
            "",
            f"PREGUNTA DEL USUARIO: {query}",
            "",
            "EXTRACTOS VERIFICADOS:"
        ]

        for i, snippet in enumerate(search_results["snippets"], 1):
            prompt_parts.append(f"\n[Fuente {i}] {snippet.get('title', 'Sin título')}")
            prompt_parts.append(f"URL: {snippet.get('url', 'N/A')}")
            prompt_parts.append(f"Contenido: {snippet.get('content', 'Sin contenido')}")
            prompt_parts.append("---")

        prompt_parts.append("\nRESPUESTA (citando fuentes cuando sea posible):")
        prompt = "\n".join(prompt_parts)

        # Decidir modelo (short vs long)
        # Si el prompt es muy grande (muchos snippets), usar expert_long
        # Threshold: ~400 chars por snippet * 5 snippets = ~2000 chars → usar long
        prompt_length = len(prompt)
        model_name = "expert_long" if prompt_length > 1500 else "expert_short"

        logger.info(f"RAG Agent: Sintetizando con {model_name} (prompt: {prompt_length} chars)...")

    except Exception as e:
        logger.error(f"RAG Agent: Error construyendo prompt: {e}")

        audit_logger = get_web_audit_logger()
        audit_logger.log_web_query(
            query=query,
            search_results=search_results,
            error=f"prompt_build_error: {e}"
        )

        sentinel = sentinel_response("synthesis_failed")
        state.update(sentinel)
        return state

    # ====== PASO 5: LLM GENERATION ======
    try:
        # Obtener modelo del pool (carga bajo demanda)
        llm = model_pool.get(model_name)

        if llm is None:
            logger.error(f"RAG Agent: Modelo {model_name} no disponible")

            audit_logger = get_web_audit_logger()
            audit_logger.log_web_query(
                query=query,
                search_results=search_results,
                error=f"model_unavailable: {model_name}"
            )

            sentinel = sentinel_response("model_unavailable")
            state.update(sentinel)
            return state

        # Generar respuesta
        response = llm.generate(prompt)

        logger.info(f"RAG Agent: Respuesta generada ({len(response)} chars)")

    except Exception as e:
        logger.error(f"RAG Agent: Error en generación LLM: {e}")

        audit_logger = get_web_audit_logger()
        audit_logger.log_web_query(
            query=query,
            search_results=search_results,
            error=f"llm_generation_error: {e}"
        )

        sentinel = sentinel_response("synthesis_failed")
        state.update(sentinel)
        return state

    # ====== PASO 6: AUDITORÍA POST-SÍNTESIS ======
    try:
        audit_logger = get_web_audit_logger()
        audit_logger.log_web_query(
            query=query,
            search_results=search_results,
            response=response,
            llm_model=model_name
        )

        logger.info("RAG Agent: Pipeline completado exitosamente")

    except Exception as e:
        logger.error(f"RAG Agent: Error en auditoría final: {e}")
        # No bloquear respuesta por error de auditoría

    # ====== ACTUALIZAR STATE ======
    state.update({
        "response": response,
        "sentinel_triggered": False,
        "rag_metadata": {
            "source": search_results.get("source"),
            "snippets_count": len(search_results["snippets"]),
            "llm_model": model_name,
            "prompt_length": prompt_length
        }
    })

    return state


def create_rag_node(model_pool):
    """
    Factory function para crear nodo RAG compatible con LangGraph
    
    Args:
        model_pool: ModelPool instance
    
    Returns:
        Función nodo que recibe state y retorna state actualizado
    """
    def rag_node(state: Dict) -> Dict:
        return execute_rag(state, model_pool)

    return rag_node
