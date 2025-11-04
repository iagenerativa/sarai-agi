"""Pipeline paralela y secuencial para SARAi_AGI.

La implementación original en ``SARAi_v2`` contenía integración directa
con todos los subsistemas (clasificador TRM, MCP, ModelPool, etc.). Durante
la migración a **SARAi_AGI** se busca mantener la estructura general de la
canalización, pero desacoplada mediante dependencias explícitas para poder
probarla de forma aislada.

El módulo ofrece:

* :class:`PipelineDependencies`: describe las funciones necesarias para que
  la pipeline opere (clasificador, MCP, generador de respuestas, etc.).
* :class:`ParallelPipeline`: ejecuta el flujo con posibilidad de paralelizar
  etapas CPU-bound utilizando un ``ThreadPoolExecutor`` configurable.
* :func:`create_parallel_pipeline`: factoría que construye la pipeline
  utilizando la configuración leída desde ``config/default_settings.yaml``.
* :func:`get_parallel_pipeline`: acceso perezoso a una instancia global útil
  para entornos donde no existe un contenedor de dependencias.

La API externa se mantiene simple: ``await pipeline.run(state)`` donde
``state`` es un diccionario mutable que contiene al menos la clave
``"input"`` con el texto original. La función retorna un nuevo diccionario
que incluye la respuesta generada y metadatos de telemetría.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, Optional, Tuple, Union

from ..configuration import get_section, load_settings

logger = logging.getLogger(__name__)

# -- Tipos -----------------------------------------------------------------

ClassifierCallable = Callable[[Dict[str, Any]], Dict[str, float]]
WeightingCallable = Callable[[Dict[str, Any]], Dict[str, float]]
ResponseGeneratorCallable = Callable[[Dict[str, Any], str], Union[str, Awaitable[str]]]
EmotionDetectorCallable = Callable[[bytes], Optional[Dict[str, Any]]]
PrefetchCallable = Callable[[Dict[str, Any]], Optional[str]]
RouterCallable = Callable[[Dict[str, Any]], str]


@dataclass
class PipelineDependencies:
    """Dependencias necesarias para ejecutar la pipeline.

    Todos los campos son funciones que pueden ser implementadas por los
    módulos que se migren posteriormente. Se diseñan como ``callable`` en
    lugar de clases concretas para permitir tests unitarios sencillos.
    """

    trm_classifier: ClassifierCallable
    mcp_weighter: WeightingCallable
    response_generator: ResponseGeneratorCallable
    emotion_detector: Optional[EmotionDetectorCallable] = None
    prefetch_model: Optional[PrefetchCallable] = None
    router: Optional[RouterCallable] = None


@dataclass
class PipelineMetrics:
    """Pequeña estructura para exponer información de telemetría."""

    classify_ms: float = 0.0
    weights_ms: float = 0.0
    routing_ms: float = 0.0
    generation_ms: float = 0.0
    emotion_ms: float = 0.0
    response_latency_ms: float = 0.0
    streaming_chunks: int = 0
    last_agent: Optional[str] = None
    prefetch_target: Optional[str] = None
    additional: Dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> Dict[str, Any]:
        """Serializa las métricas a un diccionario simple."""

        payload = {
            "classify_ms": self.classify_ms,
            "weights_ms": self.weights_ms,
            "routing_ms": self.routing_ms,
            "generation_ms": self.generation_ms,
            "emotion_ms": self.emotion_ms,
            "response_latency_ms": self.response_latency_ms,
            "streaming_chunks": self.streaming_chunks,
            "last_agent": self.last_agent,
            "prefetch_target": self.prefetch_target,
        }
        payload.update(self.additional)
        return payload


class ParallelPipeline:
    """Implementación principal del flujo de orquestación.

    Args:
        dependencies: Instancia de :class:`PipelineDependencies` con las
            funciones necesarias para ejecutar la canalización.
        config: Configuración opcional que sobrescribe los valores por
            defecto cargados desde ``config/default_settings.yaml``.
    """

    def __init__(
        self,
        dependencies: PipelineDependencies,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.dependencies = dependencies

        settings = load_settings()
        pipeline_config = get_section(settings, "pipeline", default={
            "enable_parallelization": True,
            "min_input_length": 20,
            "max_workers": None,
        })
        if config:
            pipeline_config.update(config)

        self.enable_parallel = bool(pipeline_config.get("enable_parallelization", True))
        self.min_input_length = int(pipeline_config.get("min_input_length", 0) or 0)

        max_workers_cfg = pipeline_config.get("max_workers")
        if max_workers_cfg is None:
            # Dejamos al sistema escoger un número razonable dejando al menos
            # un núcleo libre para otras tareas (como telemetría).
            cpu_count = os.cpu_count() or 4
            max_workers = max(1, cpu_count - 1)
        else:
            max_workers = int(max_workers_cfg)

        self.executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="sarai-pipeline"
        )
        self.metrics = PipelineMetrics()

    # ------------------------------------------------------------------
    # Métodos públicos
    # ------------------------------------------------------------------

    async def run(self, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta la pipeline y devuelve un nuevo estado enriquecido."""

        state: Dict[str, Any] = dict(initial_state)
        text_input = str(state.get("input", ""))
        run_parallel = self._should_run_parallel(text_input)
        loop = asyncio.get_running_loop()

        # Tareas opcionales que podemos lanzar por adelantado.
        emotion_task: Optional[asyncio.Future] = None
        prefetch_task: Optional[asyncio.Future] = None
        emotion_start: Optional[float] = None
        emotion_result: Optional[Dict[str, Any]] = None
        prefetch_result: Optional[str] = None

        start_global = time.perf_counter()

        if run_parallel:
            emotion_start = time.perf_counter()
            emotion_task = loop.create_task(self._run_in_executor(self._detect_emotion, state.copy()))

        classify_start = time.perf_counter()
        scores = await self._run_in_executor(self._classify_intent, state)
        self.metrics.classify_ms = _elapsed_ms(classify_start)
        state.update(scores)

        weights_start = time.perf_counter()
        weights = await self._run_in_executor(self._compute_weights, state)
        self.metrics.weights_ms = _elapsed_ms(weights_start)
        state.update(weights)

        if run_parallel:
            prefetch_task = loop.create_task(self._run_in_executor(self._prefetch_model, state.copy()))

        if not run_parallel:
            emotion_start = time.perf_counter()
            emotion_result = await self._run_in_executor(self._detect_emotion, state.copy())
            self.metrics.emotion_ms = _elapsed_ms(emotion_start)
        else:
            emotion_result = await emotion_task if emotion_task else None
            if emotion_start is not None and emotion_task is not None:
                self.metrics.emotion_ms = _elapsed_ms(emotion_start)

        if emotion_result:
            state["emotion"] = emotion_result

        if not run_parallel:
            prefetch_result = await self._run_in_executor(self._prefetch_model, state.copy())
        else:
            prefetch_result = await prefetch_task if prefetch_task else None
        self.metrics.prefetch_target = prefetch_result

        routing_start = time.perf_counter()
        agent_key = await self._run_in_executor(self._route_to_agent, state)
        self.metrics.routing_ms = _elapsed_ms(routing_start)

        response, metadata = await self._generate_with_streaming(state, agent_key)
        self.metrics.response_latency_ms = _elapsed_ms(start_global)
        state["response"] = response

        metadata_container = state.setdefault("metadata", {})
        if not isinstance(metadata_container, dict):
            metadata_container = {}
            state["metadata"] = metadata_container

        metadata_container.update({
            "agent": agent_key,
            "pipeline_metrics": self.metrics.to_payload(),
            **metadata,
        })

        return state

    async def shutdown(self) -> None:
        """Cierra el executor asociado."""

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self.executor.shutdown)

    # ------------------------------------------------------------------
    # Etapas internas
    # ------------------------------------------------------------------

    def _should_run_parallel(self, text_input: str) -> bool:
        if not self.enable_parallel:
            return False
        return len(text_input) >= self.min_input_length

    def _classify_intent(self, state: Dict[str, Any]) -> Dict[str, float]:
        try:
            result = self.dependencies.trm_classifier(state)
            if not isinstance(result, dict):
                raise TypeError("El clasificador debe devolver un dict")
            return result
        except Exception as exc:  # pragma: no cover - registro defensivo
            logger.exception("Fallo en el clasificador TRM: %s", exc)
            return {"hard": 0.5, "soft": 0.5}

    def _compute_weights(self, state: Dict[str, Any]) -> Dict[str, float]:
        try:
            result = self.dependencies.mcp_weighter(state)
            if not isinstance(result, dict):
                raise TypeError("El MCP debe devolver un dict")
            alpha = float(result.get("alpha", 0.5))
            beta = float(result.get("beta", max(0.0, 1.0 - alpha)))
            total = alpha + beta
            if total == 0:
                return {"alpha": 0.5, "beta": 0.5}
            return {"alpha": alpha / total, "beta": beta / total}
        except Exception as exc:  # pragma: no cover - registro defensivo
            logger.exception("Fallo en el MCP: %s", exc)
            return {"alpha": 0.5, "beta": 0.5}

    def _detect_emotion(self, state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        detector = self.dependencies.emotion_detector
        audio_bytes = state.get("audio_input")
        if not detector or audio_bytes is None:
            return None
        try:
            return detector(audio_bytes)
        except Exception as exc:  # pragma: no cover
            logger.warning("Detector de emoción falló: %s", exc)
            return None

    def _prefetch_model(self, state: Dict[str, Any]) -> Optional[str]:
        prefetcher = self.dependencies.prefetch_model
        if not prefetcher:
            # Heurística mínima basada en la longitud del input: retornamos el
            # nombre del modelo con propósito informativo para los tests.
            length = len(str(state.get("input", "")))
            if length > 400:
                return "expert_long"
            if length > 150:
                return "expert_short"
            return "tiny"
        try:
            return prefetcher(state)
        except Exception as exc:  # pragma: no cover
            logger.debug("Prefetch falló: %s", exc)
            return None

    def _route_to_agent(self, state: Dict[str, Any]) -> str:
        router = self.dependencies.router
        if router:
            try:
                return router(state)
            except Exception as exc:  # pragma: no cover
                logger.warning("Router personalizado falló: %s", exc)
        # Ruta por defecto sencilla.
        alpha = float(state.get("alpha", 0.5))
        beta = float(state.get("beta", 0.5))
        if alpha >= 0.7:
            return "expert"
        if beta >= 0.7:
            return "empathy"
        return "balanced"

    async def _generate_with_streaming(self, state: Dict[str, Any], agent_key: str) -> Tuple[str, Dict[str, Any]]:
        start = time.perf_counter()
        try:
            result = self.dependencies.response_generator(state, agent_key)
            if asyncio.iscoroutine(result):
                response = await result
            else:
                response = result
        except Exception as exc:  # pragma: no cover - registro defensivo
            logger.exception("Generador de respuestas falló: %s", exc)
            errors_container = state.setdefault("errors", [])
            if not isinstance(errors_container, list):
                errors_container = []
                state["errors"] = errors_container
            errors_container.append({
                "stage": "generation",
                "reason": str(exc),
            })
            response = ""
        duration = _elapsed_ms(start)
        self.metrics.generation_ms = duration
        self.metrics.streaming_chunks = 1
        self.metrics.last_agent = agent_key
        return response, {"generation_ms": duration}

    async def _run_in_executor(self, func: Callable[..., Any], *args: Any) -> Any:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self.executor, lambda: func(*args))


# ---------------------------------------------------------------------------
# Factorías sencillas
# ---------------------------------------------------------------------------

_GLOBAL_PIPELINE: Optional[ParallelPipeline] = None


def create_parallel_pipeline(
    dependencies: PipelineDependencies,
    config: Optional[Dict[str, Any]] = None,
) -> ParallelPipeline:
    """Crea una instancia de :class:`ParallelPipeline`."""

    return ParallelPipeline(dependencies=dependencies, config=config)


def get_parallel_pipeline(
    dependencies: PipelineDependencies,
    config: Optional[Dict[str, Any]] = None,
) -> ParallelPipeline:
    """Devuelve una instancia global (lazy singleton).

    Esta función es útil en escenarios donde todavía no contamos con un
    contenedor de dependencias formal. Se conserva por compatibilidad con
    la API histórica mientras se completa la migración.
    """

    global _GLOBAL_PIPELINE
    if _GLOBAL_PIPELINE is None:
        _GLOBAL_PIPELINE = create_parallel_pipeline(dependencies, config)
    return _GLOBAL_PIPELINE


def _elapsed_ms(start: float) -> float:
    return (time.perf_counter() - start) * 1000.0


__all__ = [
    "PipelineDependencies",
    "PipelineMetrics",
    "ParallelPipeline",
    "create_parallel_pipeline",
    "get_parallel_pipeline",
]
