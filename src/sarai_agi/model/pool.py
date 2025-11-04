"""
SARAi AGI - Model Pool with LRU/TTL Cache & Auto-Quantization
==============================================================

Intelligent model management system with:
- LRU (Least Recently Used) eviction policy
- TTL (Time To Live) automatic unloading
- Dynamic quantization selection (IQ3_XXS/Q4_K_M/Q5_K_M)
- Working-set detection for hot/warm/cold states
- GGUF Context JIT optimization
- Fallback chain for resilience

Version: v3.5.1 (migrated from SARAi v2.19 + v3.4)
Author: SARAi Team
License: MIT

Key Features
------------
1. **Adaptive Memory Management**
   - Automatic model eviction when cache full
   - TTL-based unloading (hot: 5min, warm: 45s, cold: 15s)
   - Working-set detection (≥3 accesses in 5min = hot)

2. **Dynamic Quantization** (v3.4)
   - IQ3_XXS: 450MB, tokens<200, quality=0.75
   - Q4_K_M: 700MB, tokens 200-800, quality=0.90
   - Q5_K_M: 850MB, tokens>800, quality=0.95

3. **GGUF Context JIT** (v2.19)
   - Adaptive n_ctx based on prompt size
   - Reuses loaded models across context sizes
   - Saves ~1.2GB RAM vs separate model files

4. **Resilience**
   - Fallback chain: expert_long → expert_short → tiny
   - Graceful degradation on OOM
   - Never crashes, only degrades quality

Example
-------
>>> from sarai_agi.model.pool import ModelPool
>>> pool = ModelPool()
>>> 
>>> # Get model with auto-context
>>> model = pool.get_for_prompt("expert_short", "What is Python?")
>>> # → Loads with n_ctx=512 (short prompt)
>>>
>>> # Auto-quantization
>>> params = pool.get_model_params("Write a 2000 word essay...")
>>> # → {'quantization': 'Q5_K_M', 'n_ctx': 4096}
"""

import os
import time
import gc
import logging
from typing import Dict, Any, Optional, List
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path

try:
    import psutil
except ImportError:
    psutil = None  # Graceful degradation in tests

logger = logging.getLogger(__name__)


# ============================================================================
# Auto-Quantization Configurations (v3.4)
# ============================================================================

@dataclass
class QuantizationConfig:
    """Quantization configuration with memory/quality trade-offs"""
    name: str
    size_mb: float
    tokens_per_mb: float  # Token density
    quality: float  # Relative quality (0.0 - 1.0)
    recommended_for: str


QUANTIZATION_CONFIGS = {
    'IQ3_XXS': QuantizationConfig(
        name='IQ3_XXS',
        size_mb=450,
        tokens_per_mb=2.5,  # High token density
        quality=0.75,
        recommended_for='short_prompts'
    ),
    'Q4_K_M': QuantizationConfig(
        name='Q4_K_M',
        size_mb=700,
        tokens_per_mb=1.8,  # Balanced
        quality=0.90,
        recommended_for='long_prompts'
    ),
    'Q5_K_M': QuantizationConfig(
        name='Q5_K_M',
        size_mb=850,
        tokens_per_mb=1.5,  # Low density, high quality
        quality=0.95,
        recommended_for='critical_tasks'
    )
}


# ============================================================================
# Helper Functions
# ============================================================================

def calculate_timeout(n_ctx: int) -> int:
    """
    Calculate adaptive timeout based on context size (v2.16).
    
    Formula: timeout = 10s + (n_ctx / 1024) * 10s
    
    Reference table:
    - n_ctx=512:  15s
    - n_ctx=1024: 20s
    - n_ctx=2048: 30s
    - n_ctx=4096: 50s
    - n_ctx=8192: 60s (capped)
    
    Args:
        n_ctx: Context window size
        
    Returns:
        Timeout in seconds (max 60s)
    """
    base_timeout = 10
    scaling_factor = 10
    timeout = base_timeout + (n_ctx / 1024) * scaling_factor
    return min(int(timeout), 60)


def estimate_tokens(text: str) -> int:
    """
    Estimate token count from text.
    
    Simple heuristic: ~4 chars per token on average.
    
    Args:
        text: Input text
        
    Returns:
        Estimated token count
    """
    return len(text) // 4


def get_memory_info() -> Dict[str, float]:
    """
    Get system memory information.
    
    Returns:
        dict with total_gb, available_gb, used_gb, percent
    """
    if psutil is None:
        # Fallback values for tests
        return {
            'total_gb': 16.0,
            'available_gb': 8.0,
            'used_gb': 8.0,
            'percent': 50.0
        }
    
    try:
        mem = psutil.virtual_memory()
        return {
            'total_gb': mem.total / (1024**3),
            'available_gb': mem.available / (1024**3),
            'used_gb': mem.used / (1024**3),
            'percent': mem.percent
        }
    except Exception as e:
        logger.error(f"Error getting memory info: {e}")
        return {
            'total_gb': 16.0,
            'available_gb': 8.0,
            'used_gb': 8.0,
            'percent': 50.0
        }


# ============================================================================
# Model Pool
# ============================================================================

class ModelPool:
    """
    Intelligent cache for LLM models with adaptive memory management.
    
    Key behaviors:
    - LRU eviction when cache full (max 2 concurrent models)
    - TTL-based auto-unloading (hot: 5min, warm: 45s, cold: 15s)
    - Working-set detection (≥3 accesses in 5min = hot model)
    - Dynamic quantization based on prompt size
    - GGUF Context JIT for memory efficiency
    - Fallback chain for resilience
    
    Thread Safety: Not thread-safe. Use from single thread or add locks.
    
    Attributes:
        cache: OrderedDict of loaded models (LRU order)
        cache_prefetch: Dict of prefetched models (v2.3)
        timestamps: Dict of last access times
        max_models: Max concurrent models (default: 2)
        ttl_hot/warm/cold: Time-to-live by state (300s/45s/15s)
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize ModelPool.
        
        Args:
            config: Configuration dict (optional). Keys:
                - runtime.backend: 'cpu' or 'gpu' (default: 'cpu')
                - runtime.max_concurrent_llms: Max models (default: 2)
                - runtime.max_concurrent_skills: Max skills (default: 3)
                - memory.model_ttl_seconds: Base TTL (default: 45)
                - memory.max_ram_gb: Max RAM usage (default: 12)
                - memory.ttl_hot/warm/cold: TTL by state
        """
        self.config = config or {}
        
        # Runtime configuration
        runtime_cfg = self.config.get('runtime', {})
        self.backend = runtime_cfg.get('backend', 'cpu')
        self.max_models = runtime_cfg.get('max_concurrent_llms', 2)
        self.max_skills = runtime_cfg.get('max_concurrent_skills', 3)
        
        # Memory configuration
        memory_cfg = self.config.get('memory', {})
        self.ttl = memory_cfg.get('model_ttl_seconds', 45)
        self.max_ram_gb = memory_cfg.get('max_ram_gb', 12)
        
        # TTL by model state (v2.19)
        self.ttl_hot = memory_cfg.get('ttl_hot', 300)   # 5 min for hot
        self.ttl_warm = memory_cfg.get('ttl_warm', 45)  # 45s default
        self.ttl_cold = memory_cfg.get('ttl_cold', 15)  # 15s aggressive
        
        # Caches
        self.cache: OrderedDict = OrderedDict()  # {model_name: model_object}
        self.cache_prefetch: Dict[str, Any] = {}  # {model_name: prefetched_model}
        self.timestamps: Dict[str, float] = {}   # {model_name: last_access_time}
        
        # Skills cache (v2.12)
        self.skills_cache: OrderedDict = OrderedDict()
        self.skills_timestamps: Dict[str, float] = {}
        
        # Working-set detection (v2.19)
        self.access_history: Dict[str, List[float]] = {}  # {model: [t1, t2, ...]}
        self.working_set_window = 300  # 5 minutes
        self.hot_threshold = 3  # ≥3 accesses in 5min = hot
        
        # Hot model hysteresis (v2.18+)
        self.hot_until: Dict[str, float] = {}  # {model: timestamp_until_hot}
        self.hot_hysteresis = 900  # 15 min hysteresis (prevents flapping)
        self.burst_window = 30  # 30s for burst detection
        
        # Quantization tracking (v3.4)
        self.quantization_usage = {
            'IQ3_XXS': 0,
            'Q4_K_M': 0,
            'Q5_K_M': 0
        }
        
        self.min_ram_free_gb = 1.5  # Minimum free RAM for JIT loads
        
        logger.info(
            f"[ModelPool v3.5.1] Initialized - Backend: {self.backend}, "
            f"Max models: {self.max_models}, Max skills: {self.max_skills}"
        )
        logger.info(
            f"  TTL Dynamic: hot={self.ttl_hot}s, warm={self.ttl_warm}s, "
            f"cold={self.ttl_cold}s"
        )
    
    # ========================================================================
    # Core API
    # ========================================================================
    
    def get(self, logical_name: str) -> Any:
        """
        Get model from cache or load if not exists.
        
        logical_name can be:
        - 'expert_short': SOLAR with n_ctx=512
        - 'expert_long': SOLAR with n_ctx=2048
        - 'tiny': LFM2-1.2B
        - 'qwen_omni': Qwen2.5-Omni (audio/multimodal)
        - 'qwen3_vl_4b': Qwen3-VL-4B (vision, v2.12)
        
        Auto-management:
        - Cleans up expired models (TTL)
        - Evicts LRU model if cache full
        - Checks prefetch cache first (v2.3)
        - Updates working-set tracking (v2.19)
        
        Args:
            logical_name: Logical model name
            
        Returns:
            Loaded model object
            
        Raises:
            RuntimeError: If all fallbacks fail
        """
        # Cleanup expired models
        self._cleanup_expired()
        
        # Check main cache (LRU hit)
        if logical_name in self.cache:
            self.cache.move_to_end(logical_name)
            self.timestamps[logical_name] = time.time()
            self._update_working_set(logical_name)
            
            state = self._get_model_state(logical_name)
            logger.debug(f"[ModelPool] Cache hit: {logical_name} (state={state})")
            return self.cache[logical_name]
        
        # Check prefetch cache (v2.3)
        if logical_name in self.cache_prefetch:
            logger.info(f"✅ Prefetch HIT: {logical_name} already loaded")
            self.cache[logical_name] = self.cache_prefetch.pop(logical_name)
            self.timestamps[logical_name] = time.time()
            self._update_working_set(logical_name)
            return self.cache[logical_name]
        
        # Cache full → evict LRU
        if len(self.cache) >= self.max_models:
            self._evict_lru()
        
        # Load with fallback chain (v2.4)
        model = self._load_with_fallback(logical_name, prefetch=False)
        
        if model is None:
            raise RuntimeError(f"❌ All fallbacks failed for {logical_name}")
        
        self.cache[logical_name] = model
        self.timestamps[logical_name] = time.time()
        self._update_working_set(logical_name)
        
        logger.info(f"[ModelPool] {logical_name} loaded. Cache: {list(self.cache.keys())}")
        return model
    
    def get_for_prompt(self, logical_name: str, prompt_text: str) -> Any:
        """
        Get model optimized for prompt size (GGUF Context JIT, v2.19).
        
        Automatically selects optimal n_ctx:
        - Short prompts (≤400 tokens): n_ctx=512 → saves RAM
        - Long prompts (>400 tokens): n_ctx adaptive up to 2048
        
        Reuses loaded models across context sizes to avoid reloading.
        
        Args:
            logical_name: Model name (e.g., "expert_short")
            prompt_text: Prompt text for token counting
            
        Returns:
            Model loaded with optimal n_ctx
            
        Example:
            >>> pool = ModelPool()
            >>> model = pool.get_for_prompt("expert_short", "What is Python?")
            >>> # → n_ctx=512 (short prompt)
        """
        # Estimate prompt tokens
        input_tokens = estimate_tokens(prompt_text)
        
        # Calculate optimal context
        optimal_ctx = self._calculate_dynamic_context(input_tokens)
        
        # Resolve actual logical name with context
        if logical_name.startswith("expert"):
            actual_logical_name = "expert_short" if optimal_ctx <= 512 else "expert_long"
            
            # Check if another expert variant is cached (reuse to avoid reload)
            cached_expert = None
            for cached_name in self.cache.keys():
                if cached_name.startswith("expert"):
                    cached_expert = cached_name
                    break
            
            if cached_expert:
                logger.debug(f"[ModelPool] Reusing {cached_expert} (avoids reload)")
                return self.get(cached_expert)
            
            logical_name = actual_logical_name
        
        # Cleanup + cache check
        self._cleanup_expired()
        
        if logical_name in self.cache:
            self.cache.move_to_end(logical_name)
            self.timestamps[logical_name] = time.time()
            self._update_working_set(logical_name)
            state = self._get_model_state(logical_name)
            logger.debug(
                f"[ModelPool] Cache hit: {logical_name} "
                f"(state={state}, ctx={optimal_ctx})"
            )
            return self.cache[logical_name]
        
        # Check prefetch
        if logical_name in self.cache_prefetch:
            logger.info(f"✅ Prefetch HIT: {logical_name} (ctx={optimal_ctx})")
            self.cache[logical_name] = self.cache_prefetch.pop(logical_name)
            self.timestamps[logical_name] = time.time()
            self._update_working_set(logical_name)
            return self.cache[logical_name]
        
        # Cache full → evict LRU
        if len(self.cache) >= self.max_models:
            self._evict_lru()
        
        # Load with Context JIT (pass input_tokens)
        model = self._load_with_fallback(
            logical_name,
            prefetch=False,
            input_tokens=input_tokens
        )
        
        if model is None:
            raise RuntimeError(f"❌ All fallbacks failed for {logical_name}")
        
        self.cache[logical_name] = model
        self.timestamps[logical_name] = time.time()
        self._update_working_set(logical_name)
        
        logger.info(
            f"[ModelPool] {logical_name} loaded with Context JIT "
            f"(ctx={optimal_ctx}, tokens={input_tokens})"
        )
        logger.info(f"  Cache: {list(self.cache.keys())}")
        return model
    
    def get_model_params(self, prompt_text: str) -> Dict[str, Any]:
        """
        Calculate optimal model parameters based on prompt (v3.4).
        
        Auto-quantization logic:
        - tokens < 200:  IQ3_XXS (450MB), n_ctx=512
        - tokens < 800:  Q4_K_M (700MB), n_ctx=2048
        - tokens >= 800: Q5_K_M (850MB), n_ctx=4096
        
        Checks available RAM and degrades quantization if insufficient.
        
        Args:
            prompt_text: Input prompt
            
        Returns:
            dict with keys:
                - quantization: str ('IQ3_XXS', 'Q4_K_M', 'Q5_K_M')
                - size_mb: float
                - n_ctx: int
                - token_count: int
                - quality: float (0.0-1.0)
                - available_ram_gb: float
                - recommended_for: str
        """
        # Count tokens
        token_count = estimate_tokens(prompt_text)
        
        # Get memory info
        mem_info = get_memory_info()
        available_gb = mem_info['available_gb']
        
        # Select optimal quantization
        if token_count < 200:
            optimal_config = QUANTIZATION_CONFIGS['IQ3_XXS']
            n_ctx = 512
        elif token_count < 800:
            optimal_config = QUANTIZATION_CONFIGS['Q4_K_M']
            n_ctx = 2048
        else:
            optimal_config = QUANTIZATION_CONFIGS['Q5_K_M']
            n_ctx = 4096
        
        # Check RAM availability
        required_ram_gb = optimal_config.size_mb / 1024
        
        if available_gb < required_ram_gb + self.min_ram_free_gb:
            # Insufficient RAM → degrade to IQ3_XXS
            logger.warning(
                f"Insufficient RAM ({available_gb:.1f}GB), "
                f"degrading quantization"
            )
            optimal_config = QUANTIZATION_CONFIGS['IQ3_XXS']
            n_ctx = 512
        
        # Update stats
        self.quantization_usage[optimal_config.name] += 1
        
        return {
            'quantization': optimal_config.name,
            'size_mb': optimal_config.size_mb,
            'n_ctx': n_ctx,
            'token_count': token_count,
            'quality': optimal_config.quality,
            'available_ram_gb': available_gb,
            'recommended_for': optimal_config.recommended_for
        }
    
    def prefetch_model(self, logical_name: str) -> None:
        """
        Prefetch model in background (called by Prefetcher, v2.3).
        
        Loads model into separate prefetch cache to avoid blocking
        main cache. Model is moved to main cache on first `get()`.
        
        Args:
            logical_name: Model to prefetch
        """
        if logical_name in self.cache or logical_name in self.cache_prefetch:
            return  # Already loaded
        
        try:
            logger.info(f"🔄 Prefetching {logical_name}...")
            model = self._load_with_fallback(logical_name, prefetch=True)
            if model:
                self.cache_prefetch[logical_name] = model
                logger.info(f"✅ Prefetch complete: {logical_name}")
        except Exception as e:
            logger.warning(f"⚠️ Prefetch failed for {logical_name}: {e}")
    
    def release(self, logical_name: str) -> None:
        """
        Manually release model from cache.
        
        Useful for immediate memory reclamation after one-shot operations.
        
        Args:
            logical_name: Model to release
        """
        if logical_name in self.cache:
            del self.cache[logical_name]
            del self.timestamps[logical_name]
            if logical_name in self.access_history:
                del self.access_history[logical_name]
            if logical_name in self.hot_until:
                del self.hot_until[logical_name]
            
            gc.collect()
            logger.info(f"[ModelPool] Released: {logical_name}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get pool statistics.
        
        Returns:
            dict with cache size, loaded models, quantization usage, etc.
        """
        return {
            'cache_size': len(self.cache),
            'prefetch_size': len(self.cache_prefetch),
            'loaded_models': list(self.cache.keys()),
            'prefetched_models': list(self.cache_prefetch.keys()),
            'quantization_usage': self.quantization_usage.copy(),
            'memory_info': get_memory_info(),
            'hot_models': [
                name for name, until_ts in self.hot_until.items()
                if time.time() < until_ts
            ]
        }
    
    # ========================================================================
    # Internal Methods
    # ========================================================================
    
    def _cleanup_expired(self) -> None:
        """Remove models that exceeded TTL."""
        current_time = time.time()
        expired = []
        
        for model_name, last_access in self.timestamps.items():
            # Get TTL for model state
            state = self._get_model_state(model_name)
            if state == 'hot':
                ttl = self.ttl_hot
            elif state == 'warm':
                ttl = self.ttl_warm
            else:  # cold
                ttl = self.ttl_cold
            
            if current_time - last_access > ttl:
                expired.append(model_name)
        
        for model_name in expired:
            logger.info(f"[ModelPool] TTL expired: {model_name}")
            self.release(model_name)
    
    def _evict_lru(self) -> None:
        """Evict least recently used model."""
        if not self.cache:
            return
        
        # Get LRU model (first in OrderedDict)
        lru_model = next(iter(self.cache))
        logger.info(f"[ModelPool] LRU eviction: {lru_model}")
        self.release(lru_model)
    
    def _update_working_set(self, model_name: str) -> None:
        """Update working-set tracking (v2.19)."""
        current_time = time.time()
        
        if model_name not in self.access_history:
            self.access_history[model_name] = []
        
        # Add current access
        self.access_history[model_name].append(current_time)
        
        # Remove accesses outside window
        cutoff_time = current_time - self.working_set_window
        self.access_history[model_name] = [
            t for t in self.access_history[model_name]
            if t > cutoff_time
        ]
        
        # Check if hot (≥3 accesses in 5min)
        if len(self.access_history[model_name]) >= self.hot_threshold:
            # Set hot status with hysteresis
            self.hot_until[model_name] = current_time + self.hot_hysteresis
            logger.debug(f"[ModelPool] {model_name} is HOT")
    
    def _get_model_state(self, model_name: str) -> str:
        """Get model state: 'hot', 'warm', or 'cold'."""
        current_time = time.time()
        
        # Check hot status with hysteresis
        if model_name in self.hot_until:
            if current_time < self.hot_until[model_name]:
                return 'hot'
        
        # Check working-set
        if model_name in self.access_history:
            recent_accesses = len(self.access_history[model_name])
            if recent_accesses >= self.hot_threshold:
                return 'warm'
        
        return 'cold'
    
    def _calculate_dynamic_context(self, input_tokens: int) -> int:
        """Calculate optimal n_ctx based on input tokens (v2.19)."""
        # Add buffer for generation (e.g., 2x input)
        total_tokens = input_tokens * 2
        
        # Round up to next power of 2 (512, 1024, 2048, 4096)
        if total_tokens <= 512:
            return 512
        elif total_tokens <= 1024:
            return 1024
        elif total_tokens <= 2048:
            return 2048
        else:
            return 4096
    
    def _load_with_fallback(
        self,
        logical_name: str,
        prefetch: bool = False,
        input_tokens: Optional[int] = None
    ) -> Optional[Any]:
        """
        Load model with fallback chain (v2.4 + v2.19).
        
        Fallback chain:
        - expert_long → expert_short → tiny
        - expert_short → tiny
        - tiny → (no fallback, last resort)
        - qwen_omni → (no fallback)
        - qwen3_vl_4b → (no fallback)
        
        Args:
            logical_name: Requested model
            prefetch: If this is prefetch or normal load
            input_tokens: Tokens for Context JIT (v2.19)
            
        Returns:
            Loaded model or None if all fallbacks fail
        """
        fallback_chain = {
            "expert_long": ["expert_short", "tiny"],
            "expert_short": ["tiny"],
            "tiny": [],
            "qwen_omni": [],
            "qwen3_vl_4b": []
        }
        
        # Try requested model
        try:
            logger.info(f"[ModelPool] Loading {logical_name} (backend: {self.backend})...")
            model = self._load_with_backend(logical_name, prefetch, input_tokens)
            logger.info(f"✅ {logical_name} loaded successfully")
            return model
        except Exception as e:
            logger.warning(f"⚠️ Error loading {logical_name}: {e}")
            
            # Try fallbacks
            fallbacks = fallback_chain.get(logical_name, [])
            
            for fallback_name in fallbacks:
                try:
                    logger.info(f"🔄 Trying fallback: {fallback_name}")
                    model = self._load_with_backend(fallback_name, prefetch, input_tokens)
                    logger.info(f"✅ Fallback successful: {fallback_name}")
                    return model
                except Exception as e:
                    logger.warning(f"⚠️ Fallback {fallback_name} failed: {e}")
                    continue
            
            # All fallbacks exhausted
            return None
    
    def _load_with_backend(
        self,
        logical_name: str,
        prefetch: bool = False,
        input_tokens: Optional[int] = None
    ) -> Any:
        """
        Load model with appropriate backend (CPU/GPU).
        
        This is a stub implementation. In production, this would:
        1. Check self.backend ('cpu' or 'gpu')
        2. Load GGUF with llama-cpp-python for CPU
        3. Load 4-bit with transformers for GPU
        4. Use input_tokens for Context JIT
        
        Args:
            logical_name: Model name
            prefetch: If prefetch (use fewer threads)
            input_tokens: Tokens for dynamic n_ctx
            
        Returns:
            Loaded model object
            
        Raises:
            NotImplementedError: Stub implementation
        """
        # Stub for migration - actual implementation requires:
        # - llama-cpp-python for CPU backend
        # - transformers + bitsandbytes for GPU backend
        # - Model path resolution from config
        # - GGUF file handling
        
        raise NotImplementedError(
            "Model loading backend not implemented in migration stub. "
            "Production implementation requires llama-cpp-python or "
            "transformers with appropriate model files."
        )


# ============================================================================
# Singleton Instance
# ============================================================================

_model_pool_instance: Optional[ModelPool] = None


def get_model_pool(config: Optional[Dict[str, Any]] = None) -> ModelPool:
    """
    Get singleton ModelPool instance.
    
    Args:
        config: Configuration dict (only used on first call)
        
    Returns:
        ModelPool singleton
    """
    global _model_pool_instance
    
    if _model_pool_instance is None:
        _model_pool_instance = ModelPool(config)
    
    return _model_pool_instance


# ============================================================================
# Compatibility Functions (v3.4)
# ============================================================================

def calculate_optimal_llm_params(prompt_text: str) -> Dict[str, Any]:
    """Calculate optimal model parameters for prompt (v3.4 compatibility)."""
    pool = get_model_pool()
    return pool.get_model_params(prompt_text)


def get_model_optimization_stats() -> Dict[str, Any]:
    """Get optimization statistics (v3.4 compatibility)."""
    pool = get_model_pool()
    return pool.get_stats()


def optimize_model_load(
    prompt: str,
    current_model: Optional[str] = None
) -> Dict[str, Any]:
    """
    Optimize model load based on prompt (v3.4 micro-improvement 3).
    
    Implements:
    - Prompt size detection
    - Memory availability check
    - Automatic quantization selection
    - JIT model loading
    
    Args:
        prompt: Input prompt
        current_model: Currently loaded model (if any)
        
    Returns:
        dict with model_params, needs_reload, optimization_applied
    """
    pool = get_model_pool()
    params = pool.get_model_params(prompt)
    
    # Check if reload needed
    needs_reload = (
        current_model is None or
        current_model != params['quantization']
    )
    
    return {
        'model_params': params,
        'needs_reload': needs_reload,
        'current_model': current_model,
        'optimization_applied': True
    }
