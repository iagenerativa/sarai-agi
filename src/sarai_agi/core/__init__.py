"""Core integration components for SARAi AGI."""

from .integrator import (
    create_emotion_detector_callable,
    create_integrated_pipeline,
    create_mcp_weighter_callable,
    create_prefetch_callable,
    create_response_generator_callable,
    create_router_callable,
    create_trm_classifier_callable,
)

__all__ = [
    "create_integrated_pipeline",
    "create_trm_classifier_callable",
    "create_mcp_weighter_callable",
    "create_emotion_detector_callable",
    "create_router_callable",
    "create_response_generator_callable",
    "create_prefetch_callable",
]
