"""SARAi MCP Protocol Server.

Servidor FastAPI que implementa el Model Context Protocol (MCP) estándar.
Orquesta módulos cognitivos (SAUL, Vision, Audio, RAG, Memory, Skills)
y los expone como tools/resources vía MCP.

Arquitectura:
    HLCS → MCP Server → Tool Registry → Módulos (SAUL, Vision, etc.)

Endpoints MCP:
    POST /tools/list       - Lista de tools disponibles
    POST /tools/call       - Ejecutar un tool
    POST /resources/list   - Lista de resources disponibles
    POST /resources/read   - Leer un resource
    GET  /health          - Health check
    GET  /metrics         - Prometheus metrics

Versión: 3.7.0 (Feature: MCP Server)
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ..configuration import get_section, load_settings

logger = logging.getLogger(__name__)

# ============================================================================
# Modelos Pydantic para MCP Protocol
# ============================================================================


class ToolDefinition(BaseModel):
    """Definición de un tool MCP."""

    name: str = Field(..., description="Nombre único del tool (ej: saul.respond)")
    description: str = Field(..., description="Descripción funcional del tool")
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="JSON Schema de parámetros esperados"
    )


class ToolCallRequest(BaseModel):
    """Request para ejecutar un tool."""

    name: str = Field(..., description="Nombre del tool a ejecutar")
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Parámetros para el tool"
    )


class ToolCallResponse(BaseModel):
    """Response de ejecución de tool."""

    success: bool = Field(..., description="Si la ejecución fue exitosa")
    result: Any = Field(default=None, description="Resultado del tool")
    error: Optional[str] = Field(default=None, description="Mensaje de error si falló")
    latency_ms: float = Field(..., description="Latencia de ejecución (ms)")


class ResourceDefinition(BaseModel):
    """Definición de un resource MCP."""

    uri: str = Field(..., description="URI único del resource (ej: memory://conversations)")
    name: str = Field(..., description="Nombre descriptivo")
    mimeType: str = Field(default="application/json", description="MIME type del contenido")


class ResourceReadRequest(BaseModel):
    """Request para leer un resource."""

    uri: str = Field(..., description="URI del resource")


class ResourceReadResponse(BaseModel):
    """Response de lectura de resource."""

    uri: str = Field(..., description="URI del resource")
    contents: Any = Field(..., description="Contenido del resource")
    mimeType: str = Field(default="application/json")


# ============================================================================
# Tool Registry - Sistema de registro dinámico
# ============================================================================


class ToolRegistry:
    """Registro de tools disponibles.

    Permite agregar módulos dinámicamente (SAUL, Vision, Audio, etc.).
    """

    def __init__(self):
        """Inicializa registry vacío."""
        self.tools: Dict[str, ToolDefinition] = {}
        self.handlers: Dict[str, callable] = {}
        logger.info("ToolRegistry initialized (empty)")

    def register_tool(
        self,
        name: str,
        description: str,
        handler: callable,
        parameters: Dict[str, Any] = None
    ):
        """Registra un tool.

        Args:
            name: Nombre único (ej: "saul.respond")
            description: Descripción funcional
            handler: Función async que ejecuta el tool
            parameters: JSON Schema de parámetros
        """
        tool = ToolDefinition(
            name=name,
            description=description,
            parameters=parameters or {}
        )

        self.tools[name] = tool
        self.handlers[name] = handler

        logger.info("Registered tool: %s", name)

    async def call_tool(self, name: str, parameters: Dict[str, Any]) -> Any:
        """Ejecuta un tool registrado.

        Args:
            name: Nombre del tool
            parameters: Parámetros para el tool

        Returns:
            Resultado del tool

        Raises:
            HTTPException: Si el tool no existe o falla
        """
        if name not in self.handlers:
            raise HTTPException(
                status_code=404,
                detail=f"Tool '{name}' not found. Available: {list(self.tools.keys())}"
            )

        handler = self.handlers[name]

        try:
            # Ejecutar handler (async)
            result = await handler(**parameters)
            return result

        except Exception as e:
            logger.error("Tool '%s' failed: %s", name, e, exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Tool execution failed: {str(e)}"
            )

    def list_tools(self) -> List[ToolDefinition]:
        """Lista todos los tools registrados."""
        return list(self.tools.values())


# ============================================================================
# Resource Registry
# ============================================================================


class ResourceRegistry:
    """Registro de resources (memoria, conocimiento, estado)."""

    def __init__(self):
        """Inicializa registry vacío."""
        self.resources: Dict[str, ResourceDefinition] = {}
        self.handlers: Dict[str, callable] = {}
        logger.info("ResourceRegistry initialized (empty)")

    def register_resource(
        self,
        uri: str,
        name: str,
        handler: callable,
        mime_type: str = "application/json"
    ):
        """Registra un resource.

        Args:
            uri: URI único (ej: "memory://conversations")
            name: Nombre descriptivo
            handler: Función async que lee el resource
            mime_type: MIME type del contenido
        """
        resource = ResourceDefinition(
            uri=uri,
            name=name,
            mimeType=mime_type
        )

        self.resources[uri] = resource
        self.handlers[uri] = handler

        logger.info("Registered resource: %s", uri)

    async def read_resource(self, uri: str) -> Any:
        """Lee un resource.

        Args:
            uri: URI del resource

        Returns:
            Contenido del resource

        Raises:
            HTTPException: Si el resource no existe o falla
        """
        if uri not in self.handlers:
            raise HTTPException(
                status_code=404,
                detail=f"Resource '{uri}' not found. Available: {list(self.resources.keys())}"
            )

        handler = self.handlers[uri]

        try:
            contents = await handler()
            return contents

        except Exception as e:
            logger.error("Resource '%s' read failed: %s", uri, e, exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Resource read failed: {str(e)}"
            )

    def list_resources(self) -> List[ResourceDefinition]:
        """Lista todos los resources registrados."""
        return list(self.resources.values())


# ============================================================================
# MCP Server
# ============================================================================


class MCPServer:
    """Servidor MCP (Model Context Protocol).

    Orquestador central que expone tools y resources vía FastAPI.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Args:
            config: Configuración del servidor (host, port, etc.)
        """
        self.config = config or {}
        self.app = FastAPI(
            title="SARAi MCP Server",
            description="Model Context Protocol Server - Orquestador de módulos cognitivos",
            version="3.7.0"
        )

        # Registries
        self.tool_registry = ToolRegistry()
        self.resource_registry = ResourceRegistry()

        # Métricas
        self.metrics = {
            "requests_total": 0,
            "requests_by_tool": {},
            "errors_total": 0,
            "uptime_start": time.time(),
        }

        # Registrar endpoints
        self._register_endpoints()

        logger.info("MCPServer initialized (config=%s)", self.config)

    def _register_endpoints(self):
        """Registra endpoints FastAPI."""

        @self.app.get("/")
        async def root():
            """Root endpoint."""
            return {
                "service": "SARAi MCP Server",
                "version": "3.7.0",
                "status": "running",
                "tools": len(self.tool_registry.tools),
                "resources": len(self.resource_registry.resources),
            }

        @self.app.get("/health")
        async def health():
            """Health check."""
            uptime = time.time() - self.metrics["uptime_start"]
            return {
                "status": "healthy",
                "uptime_seconds": uptime,
                "tools": len(self.tool_registry.tools),
                "resources": len(self.resource_registry.resources),
                "requests_total": self.metrics["requests_total"],
                "errors_total": self.metrics["errors_total"],
            }

        @self.app.get("/metrics")
        async def metrics():
            """Prometheus-style metrics."""
            uptime = time.time() - self.metrics["uptime_start"]

            lines = [
                "# HELP sarai_mcp_uptime_seconds Server uptime",
                "# TYPE sarai_mcp_uptime_seconds gauge",
                f"sarai_mcp_uptime_seconds {uptime:.1f}",
                "",
                "# HELP sarai_mcp_requests_total Total requests",
                "# TYPE sarai_mcp_requests_total counter",
                f"sarai_mcp_requests_total {self.metrics['requests_total']}",
                "",
                "# HELP sarai_mcp_errors_total Total errors",
                "# TYPE sarai_mcp_errors_total counter",
                f"sarai_mcp_errors_total {self.metrics['errors_total']}",
                "",
                "# HELP sarai_mcp_tools_registered Total tools registered",
                "# TYPE sarai_mcp_tools_registered gauge",
                f"sarai_mcp_tools_registered {len(self.tool_registry.tools)}",
                "",
                "# HELP sarai_mcp_resources_registered Total resources registered",
                "# TYPE sarai_mcp_resources_registered gauge",
                f"sarai_mcp_resources_registered {len(self.resource_registry.resources)}",
            ]

            # Requests por tool
            for tool, count in self.metrics["requests_by_tool"].items():
                lines.append(f'sarai_mcp_requests_by_tool{{tool="{tool}"}} {count}')

            return "\n".join(lines)

        @self.app.post("/tools/list")
        async def list_tools():
            """Lista todos los tools disponibles."""
            tools = self.tool_registry.list_tools()
            return {"tools": [tool.model_dump() for tool in tools]}

        @self.app.post("/tools/call")
        async def call_tool(request: ToolCallRequest):
            """Ejecuta un tool."""
            start = time.time()

            self.metrics["requests_total"] += 1
            self.metrics["requests_by_tool"][request.name] = (
                self.metrics["requests_by_tool"].get(request.name, 0) + 1
            )

            try:
                result = await self.tool_registry.call_tool(
                    request.name,
                    request.parameters
                )

                latency_ms = (time.time() - start) * 1000

                return ToolCallResponse(
                    success=True,
                    result=result,
                    latency_ms=latency_ms
                ).model_dump()

            except HTTPException as e:
                self.metrics["errors_total"] += 1
                raise e

            except Exception as e:
                self.metrics["errors_total"] += 1
                latency_ms = (time.time() - start) * 1000

                logger.error("Tool call failed: %s", e, exc_info=True)

                return ToolCallResponse(
                    success=False,
                    error=str(e),
                    latency_ms=latency_ms
                ).model_dump()

        @self.app.post("/resources/list")
        async def list_resources():
            """Lista todos los resources disponibles."""
            resources = self.resource_registry.list_resources()
            return {"resources": [res.model_dump() for res in resources]}

        @self.app.post("/resources/read")
        async def read_resource(request: ResourceReadRequest):
            """Lee un resource."""
            try:
                contents = await self.resource_registry.read_resource(request.uri)

                resource_def = self.resource_registry.resources[request.uri]

                return ResourceReadResponse(
                    uri=request.uri,
                    contents=contents,
                    mimeType=resource_def.mimeType
                ).model_dump()

            except HTTPException as e:
                raise e

            except Exception as e:
                logger.error("Resource read failed: %s", e, exc_info=True)
                raise HTTPException(
                    status_code=500,
                    detail=f"Resource read failed: {str(e)}"
                )

    def register_module(self, module):
        """Registra un módulo completo (ej: SAUL).

        El módulo debe implementar:
        - get_tools() -> List[(name, description, handler, parameters)]
        - get_resources() -> List[(uri, name, handler, mime_type)] (opcional)
        """
        # Registrar tools del módulo
        if hasattr(module, "get_tools"):
            tools = module.get_tools()
            for tool_info in tools:
                if len(tool_info) == 4:
                    name, description, handler, parameters = tool_info
                else:
                    name, description, handler = tool_info
                    parameters = {}

                self.tool_registry.register_tool(
                    name, description, handler, parameters
                )

        # Registrar resources del módulo
        if hasattr(module, "get_resources"):
            resources = module.get_resources()
            for res_info in resources:
                if len(res_info) == 4:
                    uri, name, handler, mime_type = res_info
                else:
                    uri, name, handler = res_info
                    mime_type = "application/json"

                self.resource_registry.register_resource(
                    uri, name, handler, mime_type
                )

        logger.info("Registered module: %s", module.__class__.__name__)

    def run(self, host: str = "0.0.0.0", port: int = 3000):
        """Inicia el servidor.

        Args:
            host: Host a escuchar
            port: Puerto
        """
        import uvicorn

        logger.info("Starting MCP Server on %s:%d", host, port)

        uvicorn.run(
            self.app,
            host=host,
            port=port,
            log_level="info"
        )


# ============================================================================
# Factory
# ============================================================================


def create_mcp_server(config_path: str = "config/sarai.yaml") -> MCPServer:
    """Crea servidor MCP desde configuración.

    Args:
        config_path: Ruta al archivo YAML de configuración

    Returns:
        Instancia de MCPServer configurada
    """
    settings = load_settings(config_path)
    mcp_config = get_section(settings, "mcp_server", {})

    server = MCPServer(config=mcp_config)

    logger.info("MCP Server created from config: %s", config_path)

    return server


__all__ = [
    "MCPServer",
    "ToolRegistry",
    "ResourceRegistry",
    "ToolDefinition",
    "ToolCallRequest",
    "ToolCallResponse",
    "ResourceDefinition",
    "ResourceReadRequest",
    "ResourceReadResponse",
    "create_mcp_server",
]
