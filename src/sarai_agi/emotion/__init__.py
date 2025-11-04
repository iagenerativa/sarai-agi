"""
SARAi AGI - Emotion Module
===========================

Emotional and cultural context analysis.

Exports:
    - EmotionalContext: 16 emotion enum
    - CulturalContext: 8 culture enum  
    - TimeContext: 7 time period enum
    - EmotionalProfile: User profile dataclass
    - EmotionalResponse: Analysis result dataclass
    - EmotionalContextEngine: Main engine
    - create_emotional_context_engine: Factory function
"""

from .context_engine import (
    EmotionalContext,
    CulturalContext,
    TimeContext,
    EmotionalProfile,
    EmotionalResponse,
    EmotionalContextEngine,
    create_emotional_context_engine
)

__all__ = [
    "EmotionalContext",
    "CulturalContext",
    "TimeContext",
    "EmotionalProfile",
    "EmotionalResponse",
    "EmotionalContextEngine",
    "create_emotional_context_engine"
]
