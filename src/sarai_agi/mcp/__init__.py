"""Módulo MCP (Meta Control Plane + Protocol Server).

Meta Control Plane: Routing adaptativo interno de SARAi
Protocol Server: Orquestador MCP estándar para módulos externos
"""

# Meta Control Plane (routing interno)
from .core import (
    MCP,
    MCPCache,
    MCPRules,
    create_mcp,
    get_mcp_weights,
    reload_mcp,
)
from .skills import route_to_skills

# Protocol Server (MCP standard)
from .protocol_server import (
    MCPServer,
    ToolRegistry,
    ResourceRegistry,
    ToolDefinition,
    ToolCallRequest,
    ToolCallResponse,
    ResourceDefinition,
    ResourceReadRequest,
    ResourceReadResponse,
    create_mcp_server,
)

__all__ = [
    # Meta Control Plane
    "MCP",
    "MCPCache",
    "MCPRules",
    "create_mcp",
    "get_mcp_weights",
    "reload_mcp",
    "route_to_skills",
    # Protocol Server
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
