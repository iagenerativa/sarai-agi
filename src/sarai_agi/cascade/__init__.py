"""
SARAi AGI - CASCADE Oracle System
==================================

This module implements the CASCADE Oracle 3-tier routing system that enables
intelligent model selection based on query complexity.

Components
----------
- **ConfidenceRouter**: Routes queries to LFM2, MiniCPM, or Qwen-3 based on confidence
- **ThinkModeClassifier**: Decides whether to enable step-by-step reasoning mode

CASCADE Tiers
-------------
- **Tier 1 (LFM2-1.2B)**: 80% of queries, ~1.2s latency (confidence ≥0.6)
- **Tier 2 (MiniCPM-4.1)**: 18% of queries, ~4s latency (confidence 0.3-0.6)
- **Tier 3 (Qwen-3-8B)**: 2% of queries, ~15s latency (confidence <0.3)

Example
-------
>>> from sarai_agi.cascade import ConfidenceRouter, get_think_mode_classifier
>>>
>>> # Initialize router
>>> router = ConfidenceRouter()
>>>
>>> # Route based on confidence
>>> decision = router.should_escalate("What is Python?", "Python is a language")
>>> print(decision['target_model'])  # 'lfm2' (high confidence)
>>>
>>> # Check if query needs think mode
>>> classifier = get_think_mode_classifier()
>>> mode = classifier.classify("Solve this complex equation: x^2 + 5x + 6 = 0")
>>> print(mode)  # 'think' (requires reasoning)

Version: v3.5.1
"""

from .confidence_router import (
    ConfidenceRouter,
    get_confidence_router,
)
from .think_mode_classifier import (
    ThinkModeClassifier,
    get_think_mode_classifier,
)

__all__ = [
    # Confidence Router
    "ConfidenceRouter",
    "get_confidence_router",

    # Think Mode Classifier
    "ThinkModeClassifier",
    "get_think_mode_classifier",
]

__version__ = '3.5.1'
