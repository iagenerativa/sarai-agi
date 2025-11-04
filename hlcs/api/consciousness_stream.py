"""
SARAi HLCS v0.2 - Consciousness Stream API
===========================================

API real-time para transmitir eventos de consciencia:
- Server-Sent Events (SSE) stream
- Multi-layer consciousness events
- Filterable by consciousness type
- WebSocket support (future)

"Consciencia observable en tiempo real"

Version: 0.2.0
Author: SARAi Team
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import AsyncGenerator, Dict, List, Optional
from enum import Enum
import json
import asyncio
import logging

logger = logging.getLogger(__name__)


class ConsciousnessLayer(Enum):
    """Capas de consciencia transmitidas."""
    META = "meta"  # Meta-consciousness reflexiones
    IGNORANCE = "ignorance"  # Known/Unknown unknowns
    NARRATIVE = "narrative"  # Story construction events
    EPISODIC = "episodic"  # Raw episode events
    DECISION = "decision"  # Decision-making events


@dataclass
class ConsciousnessEvent:
    """Evento de consciencia transmitido."""
    event_id: str
    layer: ConsciousnessLayer
    timestamp: datetime
    event_type: str  # e.g., "self_reflection", "unknown_detected", "chapter_created"
    data: Dict
    priority: str = "normal"  # "low", "normal", "high", "critical"
    
    def to_sse(self) -> str:
        """
        Convierte evento a formato Server-Sent Events.
        
        Format:
            event: <event_type>
            data: <json_data>
            id: <event_id>
            
        """
        event_dict = asdict(self)
        event_dict["timestamp"] = self.timestamp.isoformat()
        event_dict["layer"] = self.layer.value
        
        sse_lines = [
            f"event: {self.event_type}",
            f"data: {json.dumps(event_dict)}",
            f"id: {self.event_id}",
            "",  # Empty line terminates event
        ]
        
        return "\n".join(sse_lines) + "\n"
    
    def __str__(self) -> str:
        return (
            f"[{self.layer.value.upper()}] {self.event_type} "
            f"(priority: {self.priority}, id: {self.event_id})"
        )


class ConsciousnessStreamAPI:
    """
    HLCS v0.2 Consciousness Stream API
    
    Transmite eventos de consciencia en tiempo real usando SSE:
    - Meta-consciousness reflections
    - Ignorance discoveries
    - Narrative updates
    - Episodic memories
    - Decision events
    
    Features:
    - Server-Sent Events protocol
    - Filterable by layer/priority
    - Event buffering (últimos 100 eventos)
    - Replay capability
    
    Example:
        >>> api = ConsciousnessStreamAPI()
        >>> await api.emit_event(
        ...     layer=ConsciousnessLayer.META,
        ...     event_type="self_reflection",
        ...     data={"self_doubt": 0.15, "alignment": 0.85}
        ... )
        >>> async for event_sse in api.stream_events():
        ...     print(event_sse)  # SSE format
    """
    
    def __init__(
        self,
        max_buffer_size: int = 100,
        heartbeat_interval: float = 30.0,
    ):
        """
        Args:
            max_buffer_size: Número de eventos a mantener en buffer
            heartbeat_interval: Intervalo de heartbeat en segundos (SSE keep-alive)
        """
        self.max_buffer_size = max_buffer_size
        self.heartbeat_interval = heartbeat_interval
        
        # Event buffer (circular)
        self.event_buffer: List[ConsciousnessEvent] = []
        
        # Event counter
        self.event_counter = 0
        
        # Active subscribers
        self.subscribers: List[asyncio.Queue] = []
        
        logger.info(
            "Consciousness Stream API initialized: buffer_size=%d, heartbeat=%.1fs",
            max_buffer_size, heartbeat_interval
        )
    
    async def emit_event(
        self,
        layer: ConsciousnessLayer,
        event_type: str,
        data: Dict,
        priority: str = "normal",
    ) -> ConsciousnessEvent:
        """
        Emite un evento de consciencia.
        
        Args:
            layer: Capa de consciencia
            event_type: Tipo de evento (e.g., "self_reflection")
            data: Datos del evento
            priority: Prioridad ("low", "normal", "high", "critical")
        
        Returns:
            ConsciousnessEvent emitido
        """
        # Crear evento
        self.event_counter += 1
        event = ConsciousnessEvent(
            event_id=f"event_{self.event_counter}",
            layer=layer,
            timestamp=datetime.now(),
            event_type=event_type,
            data=data,
            priority=priority,
        )
        
        # Agregar a buffer
        self.event_buffer.append(event)
        
        # Mantener límite de buffer
        if len(self.event_buffer) > self.max_buffer_size:
            self.event_buffer = self.event_buffer[-self.max_buffer_size:]
        
        # Notificar subscribers
        await self._notify_subscribers(event)
        
        logger.debug("Event emitted: %s", event)
        
        return event
    
    async def _notify_subscribers(self, event: ConsciousnessEvent) -> None:
        """Notifica evento a todos los subscribers activos."""
        # Remover subscribers cerrados
        self.subscribers = [q for q in self.subscribers if not q._closed]
        
        for queue in self.subscribers:
            try:
                await queue.put(event)
            except Exception as e:
                logger.warning("Failed to notify subscriber: %s", e)
    
    async def stream_events(
        self,
        layers: Optional[List[ConsciousnessLayer]] = None,
        priorities: Optional[List[str]] = None,
        replay_buffer: bool = False,
    ) -> AsyncGenerator[str, None]:
        """
        Stream de eventos SSE.
        
        Args:
            layers: Filtrar por capas (None = todas)
            priorities: Filtrar por prioridades (None = todas)
            replay_buffer: Si True, envía buffer existente antes de stream
        
        Yields:
            Eventos en formato SSE (strings)
        """
        # Crear queue para este subscriber
        queue: asyncio.Queue = asyncio.Queue()
        self.subscribers.append(queue)
        
        try:
            # Replay buffer si solicitado
            if replay_buffer:
                for event in self.event_buffer:
                    if self._event_matches_filters(event, layers, priorities):
                        yield event.to_sse()
            
            # Stream de eventos en tiempo real
            last_heartbeat = datetime.now()
            
            while True:
                try:
                    # Wait for event con timeout para heartbeat
                    event = await asyncio.wait_for(
                        queue.get(),
                        timeout=self.heartbeat_interval / 2
                    )
                    
                    # Filtrar evento
                    if self._event_matches_filters(event, layers, priorities):
                        yield event.to_sse()
                    
                    last_heartbeat = datetime.now()
                
                except asyncio.TimeoutError:
                    # Heartbeat (keep-alive)
                    now = datetime.now()
                    if (now - last_heartbeat).total_seconds() >= self.heartbeat_interval:
                        yield self._generate_heartbeat()
                        last_heartbeat = now
        
        finally:
            # Cleanup
            if queue in self.subscribers:
                self.subscribers.remove(queue)
    
    def _event_matches_filters(
        self,
        event: ConsciousnessEvent,
        layers: Optional[List[ConsciousnessLayer]],
        priorities: Optional[List[str]],
    ) -> bool:
        """Verifica si evento pasa filtros."""
        # Filtro por layer
        if layers and event.layer not in layers:
            return False
        
        # Filtro por priority
        if priorities and event.priority not in priorities:
            return False
        
        return True
    
    def _generate_heartbeat(self) -> str:
        """Genera heartbeat SSE."""
        return ": heartbeat\n\n"
    
    def get_recent_events(
        self,
        count: int = 10,
        layers: Optional[List[ConsciousnessLayer]] = None,
        priorities: Optional[List[str]] = None,
    ) -> List[ConsciousnessEvent]:
        """
        Obtiene eventos recientes del buffer.
        
        Args:
            count: Número de eventos a retornar
            layers: Filtrar por capas
            priorities: Filtrar por prioridades
        
        Returns:
            Lista de eventos (más recientes primero)
        """
        # Filtrar eventos
        filtered = [
            event for event in self.event_buffer
            if self._event_matches_filters(event, layers, priorities)
        ]
        
        # Retornar últimos N
        return filtered[-count:][::-1]  # Reverse para más recientes primero
    
    def get_event_stats(self) -> Dict:
        """Obtiene estadísticas de eventos."""
        # Contar por layer
        by_layer = {layer.value: 0 for layer in ConsciousnessLayer}
        for event in self.event_buffer:
            by_layer[event.layer.value] += 1
        
        # Contar por priority
        by_priority = {"low": 0, "normal": 0, "high": 0, "critical": 0}
        for event in self.event_buffer:
            by_priority[event.priority] += 1
        
        return {
            "total_events_emitted": self.event_counter,
            "buffer_size": len(self.event_buffer),
            "active_subscribers": len(self.subscribers),
            "events_by_layer": by_layer,
            "events_by_priority": by_priority,
            "buffer_time_range": {
                "oldest": self.event_buffer[0].timestamp.isoformat()
                if self.event_buffer else None,
                "newest": self.event_buffer[-1].timestamp.isoformat()
                if self.event_buffer else None,
            },
        }


# FastAPI integration helper
def create_sse_response(stream_api: ConsciousnessStreamAPI, **kwargs):
    """
    Helper para crear StreamingResponse compatible con FastAPI.
    
    Example:
        from fastapi import FastAPI
        from fastapi.responses import StreamingResponse
        
        app = FastAPI()
        stream_api = ConsciousnessStreamAPI()
        
        @app.get("/consciousness/stream")
        async def stream_consciousness():
            return StreamingResponse(
                stream_api.stream_events(replay_buffer=True),
                media_type="text/event-stream"
            )
    """
    try:
        from fastapi.responses import StreamingResponse
        
        return StreamingResponse(
            stream_api.stream_events(**kwargs),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # Disable nginx buffering
            }
        )
    except ImportError:
        logger.error("FastAPI not installed, cannot create SSE response")
        return None


# Exports
__all__ = [
    "ConsciousnessStreamAPI",
    "ConsciousnessEvent",
    "ConsciousnessLayer",
    "create_sse_response",
]
