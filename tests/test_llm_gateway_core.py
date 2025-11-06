import os
import pytest
from sarai_agi.llm_gateway import get_gateway, reset_gateway
from sarai_agi.llm_gateway.cache import LRUCache

from unittest.mock import patch


def setup_function(function):
    # Ensure clean singleton for each test
    reset_gateway()
    # Prefer local provider in unit tests (avoids hitting external Ollama)
    os.environ.setdefault("LLM_GATEWAY_PRIMARY_PROVIDER", "local")


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
