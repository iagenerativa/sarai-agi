"""Clean, synchronous LLM Gateway core implementation.

This module provides `LLMGateway`, `get_gateway()` and `reset_gateway()`.
"""
from __future__ import annotations

import threading
import hashlib
import json
import logging
from typing import List, Dict, Optional

from .config import LLMGatewayConfig
from .cache import LRUCache
from .providers import OllamaProvider, LocalProvider


logger = logging.getLogger("sarai_agi.llm_gateway.core")


class LLMGateway:
    def __init__(self, config: Optional[LLMGatewayConfig] = None):
        self.config = config or LLMGatewayConfig.from_env()
        if self.config.log_level:
            logger.setLevel(self.config.log_level)

        # create cache
        self.cache = LRUCache(max_size=self.config.cache_max_size, ttl=self.config.cache_ttl)

        # instantiate providers
        self.providers = self._init_providers()

        # ordering: primary then fallbacks
        self.provider_order = [self.config.primary_provider] + list(self.config.fallback_providers)

        self._lock = threading.Lock()

    def _init_providers(self):
        p = {}
        p["ollama"] = OllamaProvider(self.config.ollama_base_url, self.config.ollama_model, self.config.ollama_timeout)
        p["local"] = LocalProvider(self.config.local_base_url, self.config.local_model, self.config.local_timeout)
        return p

    def _cache_key(self, messages: List[Dict], **kwargs) -> str:
        s = json.dumps({"messages": messages, "kwargs": kwargs}, sort_keys=True)
        return hashlib.sha256(s.encode()).hexdigest()

    def chat(self, messages: List[Dict], use_cache: Optional[bool] = None, **kwargs) -> Dict:
        """Unified chat API (synchronous).

        - messages: list of {role, content}
        - returns dict with 'text'
        """
        use_cache = self.config.cache_enabled if use_cache is None else use_cache
        key = self._cache_key(messages, **kwargs)
        if use_cache:
            cached = self.cache.get(key)
            if cached is not None:
                logger.debug("llm_gateway: cache hit")
                return cached

        last_exc = None
        for prov_name in self.provider_order:
            prov = self.providers.get(prov_name)
            if prov is None:
                continue
            try:
                logger.debug("llm_gateway: calling provider %s", prov_name)
                resp = prov.chat(messages, **kwargs)
                if not isinstance(resp, dict):
                    resp = {"text": str(resp)}
                if use_cache:
                    self.cache.set(key, resp)
                return resp
            except Exception as e:
                logger.warning("Provider %s failed: %s", prov_name, e)
                last_exc = e
                continue

        # if all providers failed, re-raise last exception
        if last_exc:
            raise last_exc
        return {"text": ""}


_INSTANCE = None


def get_gateway(config: Optional[LLMGatewayConfig] = None) -> LLMGateway:
    global _INSTANCE
    if _INSTANCE is None:
        with threading.Lock():
            if _INSTANCE is None:
                _INSTANCE = LLMGateway(config=config)
    return _INSTANCE


def reset_gateway():
    """Resets the singleton gateway instance (useful for tests)."""
    global _INSTANCE
    _INSTANCE = None
