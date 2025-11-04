"""Módulo MCP (Meta Control Plane) para routing adaptativo."""

from .core import (
    MCP,
    MCPCache,
    MCPRules,
    create_mcp,
    get_mcp_weights,
    reload_mcp,
)
from .skills import route_to_skills

__all__ = [
    "MCP",
    "MCPCache",
    "MCPRules",
    "create_mcp",
    "get_mcp_weights",
    "reload_mcp",
    "route_to_skills",
]
