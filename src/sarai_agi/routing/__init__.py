"""
Routing module for SARAi v3.7.

Tripartite routing system (Innovation #1):
- TRM (Template Response Manager)
- LLM HIGH priority
- LLM NORMAL priority

Components:
- lora_router.py: Query type classification and routing
"""

from .lora_router import LoRARouter, RoutingDecision, QueryType, Route, Priority

__all__ = [
    'LoRARouter',
    'RoutingDecision',
    'QueryType',
    'Route',
    'Priority',
]
