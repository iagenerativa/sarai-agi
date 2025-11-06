import os
import pytest
from sarai_agi.llm_gateway import get_gateway, reset_gateway
from sarai_agi.llm_gateway.cache import LRUCache

from unittest.mock import patch


def setup_function(function):
    # Ensure clean singleton for each test
    reset_gateway()


def test_cache_basic():
    c = LRUCache(max_size=2, ttl=1)
    c.set("a", 1)
    assert c.get("a") == 1
    c.set("b", 2)
    c.set("c", 3)
    # a should have been evicted
    assert c.get("a") is None


def test_singleton_gateway():
    g1 = get_gateway()
    g2 = get_gateway()
    assert g1 is g2


def test_local_provider_response():
    gw = get_gateway()
    resp = gw.chat([{"role": "user", "content": "abc"}], use_cache=False)
    assert isinstance(resp, dict)
    assert "text" in resp


def test_fallback_to_local_when_ollama_fails(monkeypatch):
    # Force primary to ollama and fallback to local
    monkeypatch.setenv("LLM_GATEWAY_PRIMARY_PROVIDER", "ollama")
    monkeypatch.setenv("LLM_GATEWAY_FALLBACK_PROVIDERS", "local")

    # Mock requests.post used by OllamaProvider to raise an exception
    with patch("sarai_agi.llm_gateway.providers.ollama.requests.post") as mock_post:
        mock_post.side_effect = Exception("connection failed")
        gw = get_gateway()
        resp = gw.chat([{"role": "user", "content": "hola"}], use_cache=False)
        assert "text" in resp


"""
Tests para LLM Gateway

Cubre gateway core, providers, cache y configuración.
"""

import pytest
import asyncio
from typing import Dict, Any, List

from sarai_agi.llm_gateway import (
    LLMGateway,
    get_gateway,
    GatewayConfig,
    get_config,
    reset_gateway,
)
from sarai_agi.llm_gateway.cache import ResponseCache
from sarai_agi.llm_gateway.providers import (
    BaseProvider,
    OllamaProvider,
)


# ============================================================================
# Tests de Configuración
# ============================================================================

def test_config_from_env(monkeypatch):
    """Test carga de configuración desde env vars"""
    monkeypatch.setenv("LLM_GATEWAY_PRIMARY_PROVIDER", "openai")
    monkeypatch.setenv("LLM_GATEWAY_FALLBACK_PROVIDERS", "ollama,local")
    monkeypatch.setenv("LLM_GATEWAY_CACHE_ENABLED", "false")
    
    config = GatewayConfig.from_env()
    
    assert config.primary_provider == "openai"
    assert config.fallback_providers == ["ollama", "local"]
    assert config.cache_enabled == False


def test_config_defaults():
    """Test valores por defecto de configuración"""
    config = GatewayConfig()
    
    assert config.primary_provider == "ollama"
    assert config.ollama_base_url == "http://localhost:11434"
    assert config.cache_enabled == True
    assert config.cache_ttl == 3600


def test_config_to_dict():
    """Test serialización de configuración"""
    config = GatewayConfig()
    config_dict = config.to_dict()
    
    assert "primary_provider" in config_dict
    assert "ollama" in config_dict
    assert config_dict["cache"]["enabled"] == True


# ============================================================================
# Tests de Cache
# ============================================================================

def test_cache_basic():
    """Test funcionalidad básica de cache"""
    cache = ResponseCache(max_size=100, ttl=3600)
    
    messages = [{"role": "user", "content": "test"}]
    model = "llama3.2"
    response = {"content": "response", "model": model}
    
    # Set
    cache.set(messages, model, response)
    
    # Get - debe existir
    cached = cache.get(messages, model)
    assert cached is not None
    assert cached["content"] == "response"
    
    # Stats
    stats = cache.stats()
    assert stats["hits"] == 1
    assert stats["misses"] == 0


def test_cache_miss():
    """Test cache miss"""
    cache = ResponseCache(max_size=100, ttl=3600)
    
    messages = [{"role": "user", "content": "test"}]
    cached = cache.get(messages, "model1")
    
    assert cached is None
    assert cache.stats()["misses"] == 1


def test_cache_lru_eviction():
    """Test eviction LRU cuando está lleno"""
    cache = ResponseCache(max_size=2, ttl=3600)
    
    # Llenar cache
    cache.set([{"role": "user", "content": "1"}], "m", {"content": "r1"})
    cache.set([{"role": "user", "content": "2"}], "m", {"content": "r2"})
    
    # Agregar tercero - debe evict el primero
    cache.set([{"role": "user", "content": "3"}], "m", {"content": "r3"})
    
    # El primero no debe estar
    assert cache.get([{"role": "user", "content": "1"}], "m") is None
    
    # El segundo y tercero sí
    assert cache.get([{"role": "user", "content": "2"}], "m") is not None
    assert cache.get([{"role": "user", "content": "3"}], "m") is not None
    
    # Verificar evictions
    assert cache.stats()["evictions"] == 1


def test_cache_ttl_expiration():
    """Test expiración por TTL"""
    import time
    
    cache = ResponseCache(max_size=100, ttl=0.1)  # 100ms TTL
    
    messages = [{"role": "user", "content": "test"}]
    cache.set(messages, "model", {"content": "response"})
    
    # Inmediatamente debe estar
    assert cache.get(messages, "model") is not None
    
    # Después del TTL no debe estar
    time.sleep(0.15)
    assert cache.get(messages, "model") is None


def test_cache_clear():
    """Test limpieza de cache"""
    cache = ResponseCache()
    
    cache.set([{"role": "user", "content": "1"}], "m", {"content": "r1"})
    cache.set([{"role": "user", "content": "2"}], "m", {"content": "r2"})
    
    assert cache.stats()["size"] == 2
    
    cache.clear()
    
    assert cache.stats()["size"] == 0
    assert cache.stats()["hits"] == 0


# ============================================================================
# Tests de Providers (Mock)
# ============================================================================

class MockProvider(BaseProvider):
    """Provider de prueba"""
    
    async def chat(self, messages, model=None, temperature=0.7, max_tokens=None, **kwargs):
        return {
            "content": "mock response",
            "model": model or self.default_model,
            "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            "finish_reason": "stop",
        }
    
    async def embed(self, text, model=None, **kwargs):
        return [0.1, 0.2, 0.3]
    
    async def health_check(self):
        return True


def test_provider_interface():
    """Test interfaz de provider"""
    provider = MockProvider({"base_url": "http://test", "default_model": "test-model"})
    
    assert provider.base_url == "http://test"
    assert provider.default_model == "test-model"


@pytest.mark.asyncio
async def test_provider_chat():
    """Test método chat de provider"""
    provider = MockProvider({"default_model": "test"})
    
    response = await provider.chat(
        messages=[{"role": "user", "content": "test"}],
        temperature=0.5
    )
    
    assert response["content"] == "mock response"
    assert response["model"] == "test"
    assert response["usage"]["total_tokens"] == 30


@pytest.mark.asyncio
async def test_provider_embed():
    """Test método embed de provider"""
    provider = MockProvider({"default_model": "test"})
    
    embedding = await provider.embed("test text")
    
    assert isinstance(embedding, list)
    assert len(embedding) == 3


# ============================================================================
# Tests de Gateway
# ============================================================================

@pytest.fixture
def gateway_with_mock():
    """Gateway con provider mock para testing"""
    config = GatewayConfig(
        primary_provider="mock",
        fallback_providers=[],
        cache_enabled=True,
    )
    
    gateway = LLMGateway(config)
    gateway._providers["mock"] = MockProvider({"default_model": "test-model"})
    gateway.provider_requests["mock"] = 0
    gateway.provider_errors["mock"] = 0
    
    yield gateway
    
    # Cleanup
    reset_gateway()


@pytest.mark.asyncio
async def test_gateway_chat(gateway_with_mock):
    """Test chat básico del gateway"""
    response = await gateway_with_mock.chat(
        messages=[{"role": "user", "content": "test"}],
        provider="mock"
    )
    
    assert response["content"] == "mock response"
    assert response["provider"] == "mock"
    assert "latency_ms" in response
    assert response["cached"] == False


@pytest.mark.asyncio
async def test_gateway_cache_hit(gateway_with_mock):
    """Test cache hit en gateway"""
    messages = [{"role": "user", "content": "test"}]
    
    # Primera llamada - cache miss
    response1 = await gateway_with_mock.chat(messages, provider="mock")
    assert response1["cached"] == False
    
    # Segunda llamada - cache hit
    response2 = await gateway_with_mock.chat(messages, provider="mock")
    assert response2["cached"] == True
    assert response2["content"] == response1["content"]


@pytest.mark.asyncio
async def test_gateway_fallback():
    """Test fallback a provider secundario"""
    
    class FailingProvider(BaseProvider):
        async def chat(self, *args, **kwargs):
            raise Exception("Provider failed")
        async def embed(self, *args, **kwargs):
            raise Exception("Provider failed")
        async def health_check(self):
            return False
    
    config = GatewayConfig(
        primary_provider="failing",
        fallback_providers=["mock"],
        cache_enabled=False,
    )
    
    gateway = LLMGateway(config)
    gateway._providers["failing"] = FailingProvider({"default_model": "test"})
    gateway._providers["mock"] = MockProvider({"default_model": "test"})
    gateway.provider_requests["failing"] = 0
    gateway.provider_errors["failing"] = 0
    gateway.provider_requests["mock"] = 0
    gateway.provider_errors["mock"] = 0
    
    # Debe hacer fallback a mock
    response = await gateway.chat(
        messages=[{"role": "user", "content": "test"}]
    )
    
    assert response["provider"] == "mock"
    assert gateway.total_fallbacks == 1
    
    reset_gateway()


@pytest.mark.asyncio
async def test_gateway_stats(gateway_with_mock):
    """Test estadísticas del gateway"""
    # Hacer algunas requests
    await gateway_with_mock.chat([{"role": "user", "content": "1"}], provider="mock")
    await gateway_with_mock.chat([{"role": "user", "content": "2"}], provider="mock")
    await gateway_with_mock.chat([{"role": "user", "content": "1"}], provider="mock")  # Cache hit
    
    stats = gateway_with_mock.get_stats()
    
    assert stats["total_requests"] == 3
    assert stats["providers"]["mock"]["requests"] == 2  # 1 cache hit no cuenta
    assert stats["cache"]["hits"] == 1
    assert stats["cache"]["misses"] == 2


@pytest.mark.asyncio
async def test_gateway_health_check(gateway_with_mock):
    """Test health check del gateway"""
    health = await gateway_with_mock.health_check()
    
    assert "mock" in health
    assert health["mock"] == True


def test_gateway_singleton():
    """Test patrón singleton del gateway"""
    reset_gateway()
    
    gateway1 = get_gateway()
    gateway2 = get_gateway()
    
    assert gateway1 is gateway2
    
    reset_gateway()


@pytest.mark.asyncio
async def test_gateway_embed(gateway_with_mock):
    """Test embeddings del gateway"""
    embedding = await gateway_with_mock.embed(
        text="test text",
        provider="mock"
    )
    
    assert isinstance(embedding, list)
    assert len(embedding) > 0


# ============================================================================
# Tests de Integración (requieren Ollama real)
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_ollama_real():
    """Test con Ollama real (solo si está disponible)"""
    config = GatewayConfig(
        primary_provider="ollama",
        ollama_base_url="http://localhost:11434",
        ollama_default_model="llama3.2:latest",
        cache_enabled=False,
    )
    
    gateway = LLMGateway(config)
    
    # Health check primero
    health = await gateway.health_check(provider="ollama")
    if not health.get("ollama"):
        pytest.skip("Ollama not available")
    
    # Chat
    response = await gateway.chat(
        messages=[{"role": "user", "content": "Say 'test' and nothing else"}],
        provider="ollama",
        max_tokens=10,
    )
    
    assert "content" in response
    assert len(response["content"]) > 0
    assert response["provider"] == "ollama"
    
    reset_gateway()


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (requires real LLM)"
    )
