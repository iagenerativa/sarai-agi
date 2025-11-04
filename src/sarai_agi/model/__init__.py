"""
SARAi AGI - Model Management Module
====================================

This module provides intelligent model management for SARAi AGI, including:

- **ModelPool**: LRU/TTL cache with auto-quantization
- **QuantizationSelector**: Dynamic quantization selection
- Dynamic quantization selection (IQ3_XXS/Q4_K_M/Q5_K_M)
- Working-set detection (hot/warm/cold states)
- GGUF Context JIT optimization
- Fallback chains for resilience

Example
-------
>>> from sarai_agi.model import ModelPool, calculate_optimal_llm_params
>>> 
>>> # Initialize pool
>>> pool = ModelPool()
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

__all__ = [
    # Quantization (existing)
    "DynamicQuantizationSelector",
    "QuantizationDecision",
    "QuantizationLevel",
    
    # Model Pool (new v3.5.1)
    'ModelPool',
    'QuantizationConfig',
    'get_model_pool',
    'calculate_optimal_llm_params',
    'get_model_optimization_stats',
    'optimize_model_load',
    'calculate_timeout',
    'estimate_tokens',
    'get_memory_info',
    'QUANTIZATION_CONFIGS',
]

__version__ = '3.5.1'
