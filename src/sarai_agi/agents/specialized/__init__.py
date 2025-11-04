"""
Specialized Agents Module - Vision & Code Expert

Provides high-performance specialized agents for:
- Visual analysis (images, video, OCR, diagrams)
- Code generation with self-debug

Version: v3.5.1
"""

from .vision import VisionAgent, create_vision_agent
from .code_expert import CodeExpertAgent, get_code_expert_agent, validate_syntax

__all__ = [
    # Vision Agent
    "VisionAgent",
    "create_vision_agent",
    
    # Code Expert Agent
    "CodeExpertAgent",
    "get_code_expert_agent",
    "validate_syntax",
]

__version__ = "3.5.1"
