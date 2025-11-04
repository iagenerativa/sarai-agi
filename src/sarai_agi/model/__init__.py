"""
SARAi AGI - Model Management Module
====================================

This module provides intelligent model management for SARAi AGI, including:

- **ModelPool**: LRU/TTL cache with auto-quantization
- **Unified Model Wrapper**: Universal abstraction for 8 backends
- **QuantizationSelector**: Dynamic quantization selection
- **CASCADE Oracle**: 3-tier intelligent routing system
- Dynamic quantization selection (IQ3_XXS/Q4_K_M/Q5_K_M)
- Working-set detection (hot/warm/cold states)
- GGUF Context JIT optimization
- Fallback chains for resilience

Example
-------
>>> from sarai_agi.model import ModelPool, get_model, calculate_optimal_llm_params
>>> 
>>> # Initialize pool
>>> pool = ModelPool()
>>> 
>>> # Get model via unified wrapper
>>> solar = get_model("solar")  # Returns CascadeWrapper
>>> response = solar.invoke("What is Python?")
>>> 
>>> # Get model with auto-context
>>> model = pool.get_for_prompt("expert_short", "What is Python?")
>>> 
>>> # Check optimal quantization
>>> params = calculate_optimal_llm_params("Write a long essay...")
>>> print(params['quantization'])  # 'Q5_K_M'

Version: v3.5.1
"""

from .quantization_selector import (
    DynamicQuantizationSelector,
    QuantizationDecision,
    QuantizationLevel,
)

from .pool import (
    ModelPool,
    get_model_pool,
    calculate_optimal_llm_params,
    get_model_optimization_stats,
    optimize_model_load,
    calculate_timeout,
    estimate_tokens,
    get_memory_info,
    QUANTIZATION_CONFIGS,
    QuantizationConfig
)

from .wrapper import (
    UnifiedModelWrapper,
    GGUFModelWrapper,
    TransformersModelWrapper,
    MultimodalModelWrapper,
    OllamaModelWrapper,
    OpenAIAPIWrapper,
    EmbeddingModelWrapper,
    ModelRegistry,
    CascadeWrapper,
    get_model,
    get_cascade_wrapper,
    list_available_models,
)

__all__ = [
    # Quantization
    "DynamicQuantizationSelector",
    "QuantizationDecision",
    "QuantizationLevel",
    "QUANTIZATION_CONFIGS",
    "QuantizationConfig",
    
    # Model Pool
    "ModelPool",
    "get_model_pool",
    "calculate_optimal_llm_params",
    "get_model_optimization_stats",
    "optimize_model_load",
    "calculate_timeout",
    "estimate_tokens",
    "get_memory_info",
    
    # Unified Wrapper (v3.5.1)
    "UnifiedModelWrapper",
    "GGUFModelWrapper",
    "TransformersModelWrapper",
    "MultimodalModelWrapper",
    "OllamaModelWrapper",
    "OpenAIAPIWrapper",
    "EmbeddingModelWrapper",
    "ModelRegistry",
    "CascadeWrapper",
    "get_model",
    "get_cascade_wrapper",
    "list_available_models",
]

__version__ = '3.5.1'
