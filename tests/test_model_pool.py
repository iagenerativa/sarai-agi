"""
Tests for SARAi AGI Model Pool
===============================

Tests cover:
- LRU eviction policy
- TTL auto-unloading (hot/warm/cold)
- Dynamic quantization selection
- Working-set detection
- GGUF Context JIT optimization
- Fallback chain resilience
- Prefetch cache
- Memory management

Version: v3.5.1
"""

import time
from typing import Any, Dict
from unittest.mock import Mock, patch

import pytest

from sarai_agi.model.pool import (
    ModelPool,
    calculate_optimal_llm_params,
    calculate_timeout,
    estimate_tokens,
    get_memory_info,
    get_model_optimization_stats,
    get_model_pool,
    optimize_model_load,
)

# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def pool_config() -> Dict[str, Any]:
    """Basic ModelPool configuration."""
    return {
        'runtime': {
            'backend': 'cpu',
            'max_concurrent_llms': 2,
            'max_concurrent_skills': 3
        },
        'memory': {
            'model_ttl_seconds': 45,
            'max_ram_gb': 12,
            'ttl_hot': 300,
            'ttl_warm': 45,
            'ttl_cold': 15
        }
    }


@pytest.fixture
def pool(pool_config):
    """Fresh ModelPool instance."""
    return ModelPool(pool_config)


@pytest.fixture
def mock_model():
    """Mock model object."""
    return Mock(spec=['generate', 'get_logits'])


# ============================================================================
# Helper Function Tests
# ============================================================================

class TestHelperFunctions:
    """Tests for module-level helper functions."""

    def test_calculate_timeout_small_context(self):
        """Test timeout calculation for small context."""
        assert calculate_timeout(512) == 15  # 10 + (512/1024)*10

    def test_calculate_timeout_medium_context(self):
        """Test timeout calculation for medium context."""
        assert calculate_timeout(2048) == 30  # 10 + (2048/1024)*10

    def test_calculate_timeout_large_context(self):
        """Test timeout calculation for large context (capped)."""
        assert calculate_timeout(8192) == 60  # Capped at 60s

    def test_estimate_tokens(self):
        """Test token estimation heuristic."""
        text = "This is a test sentence with approximately twenty words here now."
        tokens = estimate_tokens(text)
        # ~4 chars per token → 65 chars / 4 ≈ 16 tokens
        assert 15 <= tokens <= 20

    def test_get_memory_info(self):
        """Test memory info retrieval."""
        mem_info = get_memory_info()

        assert 'total_gb' in mem_info
        assert 'available_gb' in mem_info
        assert 'used_gb' in mem_info
        assert 'percent' in mem_info

        # Values should be positive
        assert mem_info['total_gb'] > 0
        assert mem_info['available_gb'] >= 0


# ============================================================================
# ModelPool Initialization Tests
# ============================================================================

class TestModelPoolInit:
    """Tests for ModelPool initialization."""

    def test_init_with_config(self, pool_config):
        """Test initialization with custom config."""
        pool = ModelPool(pool_config)

        assert pool.backend == 'cpu'
        assert pool.max_models == 2
        assert pool.max_skills == 3
        assert pool.ttl_hot == 300
        assert pool.ttl_warm == 45
        assert pool.ttl_cold == 15

    def test_init_without_config(self):
        """Test initialization with default config."""
        pool = ModelPool()

        # Should use defaults
        assert pool.backend == 'cpu'
        assert pool.max_models == 2
        assert pool.ttl_warm == 45

    def test_init_empty_caches(self, pool):
        """Test that caches are empty on init."""
        assert len(pool.cache) == 0
        assert len(pool.cache_prefetch) == 0
        assert len(pool.timestamps) == 0


# ============================================================================
# Dynamic Quantization Tests
# ============================================================================

class TestDynamicQuantization:
    """Tests for auto-quantization selection (v3.4)."""

    def test_short_prompt_uses_iq3_xxs(self, pool):
        """Test short prompts get IQ3_XXS quantization."""
        short_prompt = "What is Python?"  # ~50 tokens

        params = pool.get_model_params(short_prompt)

        assert params['quantization'] == 'IQ3_XXS'
        assert params['n_ctx'] == 512
        assert params['size_mb'] == 450
        assert params['quality'] == 0.75

    def test_medium_prompt_uses_q4_k_m(self, pool):
        """Test medium prompts get Q4_K_M quantization."""
        medium_prompt = " ".join(["word"] * 300)  # ~300 tokens

        params = pool.get_model_params(medium_prompt)

        assert params['quantization'] == 'Q4_K_M'
        assert params['n_ctx'] == 2048
        assert params['size_mb'] == 700
        assert params['quality'] == 0.90

    def test_long_prompt_uses_q5_k_m(self, pool):
        """Test long prompts get Q5_K_M quantization."""
        long_prompt = " ".join(["word"] * 1000)  # ~1000 tokens

        params = pool.get_model_params(long_prompt)

        assert params['quantization'] == 'Q5_K_M'
        assert params['n_ctx'] == 4096
        assert params['size_mb'] == 850
        assert params['quality'] == 0.95

    @patch('sarai_agi.model.pool.get_memory_info')
    def test_degrades_on_low_ram(self, mock_mem_info, pool):
        """Test quantization degrades when RAM low."""
        # Mock low available RAM (< 1.5GB free required)
        mock_mem_info.return_value = {
            'total_gb': 16.0,
            'available_gb': 1.0,  # Too low for Q5_K_M
            'used_gb': 15.0,
            'percent': 93.75
        }

        long_prompt = " ".join(["word"] * 1000)
        params = pool.get_model_params(long_prompt)

        # Should degrade to IQ3_XXS despite long prompt
        assert params['quantization'] == 'IQ3_XXS'
        assert params['n_ctx'] == 512


# ============================================================================
# Working-Set Detection Tests
# ============================================================================

class TestWorkingSetDetection:
    """Tests for hot/warm/cold model state detection (v2.19)."""

    def test_new_model_is_cold(self, pool):
        """Test newly loaded model is in cold state."""
        pool.access_history['test_model'] = [time.time()]

        state = pool._get_model_state('test_model')
        assert state == 'cold'

    def test_frequent_access_makes_hot(self, pool):
        """Test ≥3 accesses in 5min makes model hot."""
        current_time = time.time()

        # Simulate 3 accesses in last 5 minutes
        pool.access_history['test_model'] = [
            current_time - 200,  # 3.3 min ago
            current_time - 100,  # 1.7 min ago
            current_time - 10    # 10s ago
        ]

        # Update should trigger hot status
        pool._update_working_set('test_model')

        state = pool._get_model_state('test_model')
        assert state == 'hot'

    def test_hot_hysteresis(self, pool):
        """Test hot status persists for hysteresis period."""
        current_time = time.time()

        # Set hot status 5 min ago (hysteresis is 15 min)
        pool.hot_until['test_model'] = current_time + 600  # 10 min remaining

        state = pool._get_model_state('test_model')
        assert state == 'hot'

    def test_working_set_window_cleanup(self, pool):
        """Test old accesses are removed from history."""
        current_time = time.time()

        # Mix of old and recent accesses
        pool.access_history['test_model'] = [
            current_time - 400,  # Outside 5min window
            current_time - 100,  # Inside window
            current_time - 10    # Inside window
        ]

        pool._update_working_set('test_model')

        # Should only keep recent 2 accesses (+ new one = 3 total)
        assert len(pool.access_history['test_model']) == 3


# ============================================================================
# TTL and LRU Tests
# ============================================================================

class TestTTLAndLRU:
    """Tests for TTL expiration and LRU eviction."""

    def test_cleanup_expired_cold_model(self, pool, mock_model):
        """Test cold models expire quickly (15s)."""
        pool.cache['cold_model'] = mock_model
        pool.timestamps['cold_model'] = time.time() - 20  # 20s ago
        pool.access_history['cold_model'] = [time.time() - 20]  # Cold state

        pool._cleanup_expired()

        assert 'cold_model' not in pool.cache

    def test_cleanup_preserves_hot_model(self, pool, mock_model):
        """Test hot models have long TTL (5min)."""
        current_time = time.time()

        pool.cache['hot_model'] = mock_model
        pool.timestamps['hot_model'] = current_time - 100  # 100s ago
        pool.hot_until['hot_model'] = current_time + 200  # Hot for 200s more

        pool._cleanup_expired()

        # Should still be in cache (100s < 300s TTL for hot)
        assert 'hot_model' in pool.cache

    def test_lru_evicts_oldest(self, pool, mock_model):
        """Test LRU evicts least recently used model."""
        # Add 2 models (at max capacity)
        pool.cache['model1'] = mock_model
        pool.cache['model2'] = mock_model
        pool.timestamps['model1'] = time.time() - 10
        pool.timestamps['model2'] = time.time() - 5  # More recent

        pool._evict_lru()

        # Should evict model1 (older)
        assert 'model1' not in pool.cache
        assert 'model2' in pool.cache


# ============================================================================
# Prefetch Cache Tests
# ============================================================================

class TestPrefetchCache:
    """Tests for prefetch cache functionality (v2.3)."""

    def test_get_checks_prefetch_first(self, pool, mock_model):
        """Test get() checks prefetch cache before loading."""
        pool.cache_prefetch['test_model'] = mock_model

        # Mock _load_with_fallback to verify it's NOT called
        pool._load_with_fallback = Mock(side_effect=RuntimeError("Should not load"))

        result = pool.get('test_model')

        assert result == mock_model
        assert 'test_model' in pool.cache
        assert 'test_model' not in pool.cache_prefetch  # Moved to main cache

    def test_prefetch_model_async(self, pool):
        """Test prefetch_model loads in background."""
        # Mock backend loader
        mock_model = Mock()
        pool._load_with_fallback = Mock(return_value=mock_model)

        pool.prefetch_model('test_model')

        assert 'test_model' in pool.cache_prefetch
        assert pool._load_with_fallback.called

    def test_prefetch_skips_if_cached(self, pool, mock_model):
        """Test prefetch skips if model already in cache."""
        pool.cache['test_model'] = mock_model

        pool._load_with_fallback = Mock()
        pool.prefetch_model('test_model')

        # Should not attempt to load
        assert not pool._load_with_fallback.called


# ============================================================================
# Context JIT Tests
# ============================================================================

class TestContextJIT:
    """Tests for GGUF Context JIT optimization (v2.19)."""

    def test_calculate_dynamic_context_short(self, pool):
        """Test dynamic context calculation for short input."""
        ctx = pool._calculate_dynamic_context(100)  # 100 tokens
        assert ctx == 512  # 100*2 = 200 → rounds to 512

    def test_calculate_dynamic_context_medium(self, pool):
        """Test dynamic context calculation for medium input."""
        ctx = pool._calculate_dynamic_context(400)  # 400 tokens
        assert ctx == 1024  # 400*2 = 800 → rounds to 1024

    def test_calculate_dynamic_context_long(self, pool):
        """Test dynamic context calculation for long input."""
        ctx = pool._calculate_dynamic_context(1500)  # 1500 tokens
        assert ctx == 4096  # 1500*2 = 3000 → rounds to 4096

    def test_get_for_prompt_reuses_expert(self, pool, mock_model):
        """Test get_for_prompt reuses loaded expert variant."""
        # Pre-load expert_long
        pool.cache['expert_long'] = mock_model
        pool.timestamps['expert_long'] = time.time()

        # Request expert_short (different context)
        pool._load_with_fallback = Mock()
        result = pool.get_for_prompt('expert_short', 'Short prompt')

        # Should reuse expert_long instead of loading expert_short
        assert result == mock_model
        assert not pool._load_with_fallback.called


# ============================================================================
# Fallback Chain Tests
# ============================================================================

class TestFallbackChain:
    """Tests for resilience fallback chain (v2.4)."""

    def test_load_with_fallback_success(self, pool, mock_model):
        """Test successful load without fallbacks."""
        pool._load_with_backend = Mock(return_value=mock_model)

        result = pool._load_with_fallback('expert_long')

        assert result == mock_model
        assert pool._load_with_backend.call_count == 1

    def test_load_with_fallback_chain(self, pool, mock_model):
        """Test fallback chain on primary failure."""
        # Primary fails, expert_short succeeds
        pool._load_with_backend = Mock(
            side_effect=[
                Exception("expert_long failed"),
                mock_model  # expert_short succeeds
            ]
        )

        result = pool._load_with_fallback('expert_long')

        assert result == mock_model
        assert pool._load_with_backend.call_count == 2

    def test_load_with_fallback_exhausted(self, pool):
        """Test all fallbacks exhausted returns None."""
        # All attempts fail
        pool._load_with_backend = Mock(side_effect=Exception("All failed"))

        result = pool._load_with_fallback('expert_long')

        assert result is None
        # expert_long + expert_short + tiny = 3 attempts
        assert pool._load_with_backend.call_count == 3


# ============================================================================
# Singleton Tests
# ============================================================================

class TestSingleton:
    """Tests for singleton pattern."""

    def test_get_model_pool_returns_singleton(self):
        """Test get_model_pool returns same instance."""
        pool1 = get_model_pool()
        pool2 = get_model_pool()

        assert pool1 is pool2

    def test_singleton_persists_state(self):
        """Test singleton maintains state across calls."""
        pool = get_model_pool()
        pool.cache['test'] = Mock()

        pool2 = get_model_pool()
        assert 'test' in pool2.cache


# ============================================================================
# Compatibility Functions Tests
# ============================================================================

class TestCompatibilityFunctions:
    """Tests for v3.4 compatibility functions."""

    def test_calculate_optimal_llm_params(self):
        """Test calculate_optimal_llm_params wrapper."""
        params = calculate_optimal_llm_params("Short prompt")

        assert 'quantization' in params
        assert 'n_ctx' in params
        assert 'token_count' in params

    def test_get_model_optimization_stats(self):
        """Test get_model_optimization_stats wrapper."""
        stats = get_model_optimization_stats()

        assert 'cache_size' in stats
        assert 'loaded_models' in stats
        assert 'quantization_usage' in stats

    def test_optimize_model_load_new_model(self):
        """Test optimize_model_load with no current model."""
        result = optimize_model_load("Test prompt", current_model=None)

        assert result['needs_reload'] is True
        assert result['optimization_applied'] is True

    def test_optimize_model_load_same_model(self):
        """Test optimize_model_load with matching model."""
        result = optimize_model_load("Short", current_model='IQ3_XXS')

        # Short prompt → IQ3_XXS, so no reload needed
        assert result['needs_reload'] is False


# ============================================================================
# Integration Tests
# ============================================================================

class TestModelPoolIntegration:
    """End-to-end integration tests."""

    def test_full_workflow_with_cache(self, pool, mock_model):
        """Test complete workflow: load → cache hit → eviction → fallback."""
        pool._load_with_backend = Mock(return_value=mock_model)

        # 1. Initial load
        model1 = pool.get('tiny')
        assert model1 == mock_model
        assert len(pool.cache) == 1

        # 2. Cache hit
        model2 = pool.get('tiny')
        assert model2 == mock_model
        assert pool._load_with_backend.call_count == 1  # No reload

        # 3. Fill cache (max 2)
        pool.get('expert_short')
        assert len(pool.cache) == 2

        # 4. Trigger eviction
        pool.get('expert_long')
        assert len(pool.cache) == 2  # LRU evicted
        assert 'tiny' not in pool.cache  # Oldest evicted

    def test_quantization_usage_tracking(self, pool):
        """Test quantization usage is tracked."""
        pool.get_model_params("Short")  # IQ3_XXS
        pool.get_model_params(" ".join(["word"] * 300))  # Q4_K_M
        pool.get_model_params(" ".join(["word"] * 1000))  # Q5_K_M

        stats = pool.get_stats()
        usage = stats['quantization_usage']

        assert usage['IQ3_XXS'] == 1
        assert usage['Q4_K_M'] == 1
        assert usage['Q5_K_M'] == 1

    def test_release_cleans_all_state(self, pool, mock_model):
        """Test release() removes all traces of model."""
        pool.cache['test'] = mock_model
        pool.timestamps['test'] = time.time()
        pool.access_history['test'] = [time.time()]
        pool.hot_until['test'] = time.time() + 1000

        pool.release('test')

        assert 'test' not in pool.cache
        assert 'test' not in pool.timestamps
        assert 'test' not in pool.access_history
        assert 'test' not in pool.hot_until


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
