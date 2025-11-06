"""SAUL Module - Cliente gRPC para Sistema de Atención Ultra Ligero.

Módulo que conecta con el servidor SAUL gRPC y lo registra como tool
en el MCP Server.

Tools expuestos:
    - saul.respond: Respuesta rápida de texto
    - saul.respond_audio: Respuesta con audio TTS
    - saul.synthesize: Solo síntesis de voz

Versión: 3.7.0 (Feature: MCP Server)
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

# Intentar importar gRPC (graceful degradation si no está instalado)
try:
    import grpc
    # Importar stubs generados de SAUL
    # Nota: Esto asume que saul_proto está disponible
    # Si no, necesitaremos copiar los archivos .proto y regenerar
    HAS_GRPC = True
except ImportError:
    HAS_GRPC = False
    grpc = None

logger = logging.getLogger(__name__)


class SAULModule:
    """Módulo SAUL para MCP Server.

    Conecta con servidor SAUL vía gRPC y expone tools MCP.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 50051,
        timeout: float = 5.0,
        fallback_mode: bool = True
    ):
        """
        Args:
            host: Host del servidor SAUL
            port: Puerto gRPC del servidor SAUL
            timeout: Timeout en segundos para llamadas gRPC
            fallback_mode: Si True, usa respuestas mock si gRPC no disponible
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.fallback_mode = fallback_mode

        self.channel = None
        self.stub = None
        self.is_connected = False

        # Intentar conectar
        if HAS_GRPC:
            self._connect()
        else:
            logger.warning(
                "grpc not available - SAUL module running in fallback mode"
            )

    def _connect(self):
        """Conecta con el servidor SAUL gRPC."""
        try:
            # Crear canal gRPC
            target = f"{self.host}:{self.port}"
            self.channel = grpc.insecure_channel(target)

            # Verificar conexión (con timeout)
            grpc.channel_ready_future(self.channel).result(timeout=self.timeout)

            # TODO: Importar stub cuando tengamos los .proto compilados
            # from saul_proto.saul.v1 import saul_pb2_grpc
            # self.stub = saul_pb2_grpc.SAULServiceStub(self.channel)

            self.is_connected = True
            logger.info("Connected to SAUL server at %s", target)

        except grpc.FutureTimeoutError:
            logger.warning(
                "SAUL server at %s:%d not reachable (timeout=%ds) - using fallback",
                self.host, self.port, self.timeout
            )
            self.is_connected = False

        except Exception as e:
            logger.error(
                "Failed to connect to SAUL server: %s - using fallback",
                e
            )
            self.is_connected = False

    async def respond(
        self,
        query: str,
        include_audio: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """Genera respuesta SAUL (texto + opcional audio).

        Args:
            query: Query del usuario
            include_audio: Si True, incluye audio TTS
            **kwargs: Parámetros adicionales (confidence_threshold, etc.)

        Returns:
            Dict con:
                - response: Texto de respuesta
                - confidence: Score de confianza
                - template_matched: Si usó template
                - audio: Bytes de audio (si include_audio=True)
                - latency_ms: Latencia total
        """
        if self.is_connected and HAS_GRPC:
            # TODO: Implementar llamada gRPC real cuando tengamos stubs
            # return await self._respond_grpc(query, include_audio, **kwargs)
            logger.debug("gRPC call to SAUL (TODO: implement with stubs)")
            return await self._respond_fallback(query, include_audio)
        else:
            # Fallback mode
            return await self._respond_fallback(query, include_audio)

    async def _respond_fallback(
        self,
        query: str,
        include_audio: bool = False
    ) -> Dict[str, Any]:
        """Respuesta mock/fallback cuando gRPC no disponible.

        Implementa template básico similar a SAUL real.
        """
        import random
        import time

        start = time.time()

        # Template matching simple
        query_lower = query.lower()

        templates = {
            "greeting": {
                "patterns": ["hola", "hey", "buenos días", "buenas tardes"],
                "responses": [
                    "¡Hola! ¿En qué puedo ayudarte?",
                    "¡Buenas! Estoy aquí para ayudarte.",
                    "Hola. ¿Qué necesitas?",
                ]
            },
            "status": {
                "patterns": ["¿cómo estás", "qué tal", "todo bien"],
                "responses": [
                    "Todo bien por aquí. ¿Cómo puedo ayudarte?",
                    "Estoy funcionando perfectamente. ¿Y tú?",
                    "¡Genial! ¿En qué te puedo asistir?",
                ]
            },
            "thanks": {
                "patterns": ["gracias", "thanks", "muchas gracias"],
                "responses": [
                    "¡De nada! Estoy aquí para ayudarte.",
                    "¡Con gusto! Si necesitas algo más, avísame.",
                    "¡Encantado de ayudar!",
                ]
            },
            "time": {
                "patterns": ["¿qué hora", "hora es", "dime la hora"],
                "responses": [
                    "No manejo la hora directamente, pero puedo ayudarte con otras cosas.",
                    "Para la hora, te recomiendo usar un reloj. ¿Algo más?",
                ]
            },
            "default": {
                "patterns": [],
                "responses": [
                    "Entiendo tu pregunta. ¿Puedes darme más detalles?",
                    "Interesante. ¿Qué más necesitas saber?",
                    "Hmm, déjame ayudarte con eso.",
                ]
            }
        }

        # Match template
        matched_template = "default"
        for template_name, template_data in templates.items():
            if any(pattern in query_lower for pattern in template_data["patterns"]):
                matched_template = template_name
                break

        # Seleccionar respuesta
        response_text = random.choice(templates[matched_template]["responses"])

        # Simular latencia TRM (50-150ms)
        import asyncio
        await asyncio.sleep(random.uniform(0.05, 0.15))

        result = {
            "response": response_text,
            "confidence": 0.85 if matched_template != "default" else 0.50,
            "template_matched": matched_template != "default",
            "template_id": matched_template,
            "latency_ms": (time.time() - start) * 1000,
        }

        # Simular audio TTS si se pidió
        if include_audio:
            # Simular latencia TTS (50-100ms)
            await asyncio.sleep(random.uniform(0.05, 0.10))

            # Audio mock (en producción sería PCM WAV)
            audio_data = b"<MOCK_AUDIO_DATA>"
            result["audio"] = audio_data
            result["audio_size_bytes"] = len(audio_data)
            result["latency_ms"] = (time.time() - start) * 1000

        logger.debug(
            "SAUL respond (fallback): query='%s', template='%s', latency=%.1fms",
            query[:50], matched_template, result["latency_ms"]
        )

        return result

    async def synthesize(
        self,
        text: str,
        voice_model: str = "es_ES-sharvard-medium",
        speed: float = 1.0,
        **kwargs
    ) -> Dict[str, Any]:
        """Solo síntesis de voz (sin TRM).

        Args:
            text: Texto a sintetizar
            voice_model: Modelo de voz
            speed: Velocidad (0.5-2.0)
            **kwargs: Parámetros adicionales

        Returns:
            Dict con:
                - audio: Bytes de audio
                - duration: Duración en segundos
                - sample_rate: Sample rate
                - latency_ms: Latencia
        """
        import random
        import time
        import asyncio

        start = time.time()

        # Simular latencia TTS (depende de longitud de texto)
        text_length = len(text)
        latency_base = 0.05  # 50ms base
        latency_per_char = 0.002  # 2ms por caracter
        latency = latency_base + (text_length * latency_per_char)

        await asyncio.sleep(latency)

        # Audio mock
        audio_data = b"<MOCK_TTS_AUDIO>"
        duration = text_length * 0.05  # ~50ms por caracter (estimado)

        result = {
            "audio": audio_data,
            "duration": duration,
            "sample_rate": 22050,
            "format": "wav",
            "size_bytes": len(audio_data),
            "latency_ms": (time.time() - start) * 1000,
        }

        logger.debug(
            "SAUL synthesize: text_len=%d, latency=%.1fms",
            text_length, result["latency_ms"]
        )

        return result

    def get_tools(self) -> List[Tuple[str, str, callable, Dict]]:
        """Retorna tools para registrar en MCP Server.

        Returns:
            Lista de tuplas (name, description, handler, parameters_schema)
        """
        tools = [
            (
                "saul.respond",
                "Respuesta rápida de texto (< 200ms) con template matching",
                self.respond,
                {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Query del usuario"
                        },
                        "include_audio": {
                            "type": "boolean",
                            "description": "Incluir audio TTS",
                            "default": False
                        }
                    },
                    "required": ["query"]
                }
            ),
            (
                "saul.synthesize",
                "Síntesis de voz (TTS) sin template matching",
                self.synthesize,
                {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Texto a sintetizar"
                        },
                        "voice_model": {
                            "type": "string",
                            "description": "Modelo de voz",
                            "default": "es_ES-sharvard-medium"
                        },
                        "speed": {
                            "type": "number",
                            "description": "Velocidad (0.5-2.0)",
                            "default": 1.0
                        }
                    },
                    "required": ["text"]
                }
            ),
        ]

        return tools

    def __del__(self):
        """Cleanup al destruir objeto."""
        if self.channel:
            try:
                self.channel.close()
            except Exception as e:
                logger.debug("Error closing gRPC channel: %s", e)


def create_saul_module(config: Dict[str, Any] = None) -> SAULModule:
    """Factory para crear módulo SAUL desde configuración.

    Args:
        config: Dict con configuración (host, port, timeout, fallback_mode)

    Returns:
        Instancia de SAULModule
    """
    config = config or {}

    module = SAULModule(
        host=config.get("host", "localhost"),
        port=config.get("port", 50051),
        timeout=config.get("timeout", 5.0),
        fallback_mode=config.get("fallback_mode", True),
    )

    logger.info("SAUL module created: %s:%d", module.host, module.port)

    return module


__all__ = ["SAULModule", "create_saul_module"]
