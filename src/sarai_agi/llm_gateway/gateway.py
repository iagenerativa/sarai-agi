"""Core LLM Gateway.

Provides a singleton `get_gateway()` and LLMGateway class with a simple
`chat()` method that consults cache, uses primary provider and fallbacks.
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


logger = logging.getLogger("sarai_agi.llm_gateway")


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
        """Unified chat API.

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
"""
LLM Gateway Core

Gateway centralizado para acceso a múltiples providers de LLMs.
Implementa singleton pattern, fallback automático, caching y métricas.
"""

import logging
import time
from typing import Dict, Any, List, Optional, AsyncIterator
from .config import GatewayConfig, get_config
from .cache import ResponseCache
from .providers import (
    BaseProvider,
    OllamaProvider,
    OpenAIProvider,
    AnthropicProvider,
    LocalProvider,
)


logger = logging.getLogger(__name__)


class LLMGateway:
    """
    Gateway centralizado para LLMs
    
    Proporciona acceso unificado a múltiples providers con fallback automático,
    caching de respuestas, y métricas de uso.
    
    Ejemplo:
        ```python
        from sarai_agi.llm_gateway import get_gateway
        
        gateway = get_gateway()
        
        # Chat simple
        response = await gateway.chat(
            messages=[{"role": "user", "content": "Hola"}]
        )
        print(response["content"])
        
        # Con provider específico
        response = await gateway.chat(
            messages=[{"role": "user", "content": "Explica Python"}],
            provider="openai",
            model="gpt-4"
        )
        
        # Streaming
        async for chunk in gateway.stream_chat(
            messages=[{"role": "user", "content": "Cuenta un cuento"}]
        ):
            print(chunk, end="", flush=True)
        
        # Embeddings
        vector = await gateway.embed("texto a embeddear")
        
        # Estadísticas
        stats = gateway.get_stats()
        print(f"Cache hit rate: {stats['cache']['hit_rate']:.1%}")
        ```
    """
    
    def __init__(self, config: Optional[GatewayConfig] = None):
        """
        Args:
            config: Configuración del gateway (usa get_config() si None)
        """
        self.config = config or get_config()
        self._providers: Dict[str, BaseProvider] = {}
        self._cache: Optional[ResponseCache] = None
        
        # Métricas
        self.total_requests = 0
        self.total_errors = 0
        self.total_fallbacks = 0
        self.provider_requests: Dict[str, int] = {}
        self.provider_errors: Dict[str, int] = {}
        
        # Setup logging
        logging.basicConfig(
            level=getattr(logging, self.config.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Inicializar
        self._setup_providers()
        self._setup_cache()
        
        logger.info(f"LLM Gateway initialized with primary provider: {self.config.primary_provider}")
    
    def _setup_providers(self):
        """Inicializa providers configurados"""
        
        # Ollama
        if "ollama" in [self.config.primary_provider] + self.config.fallback_providers:
            self._providers["ollama"] = OllamaProvider({
                "base_url": self.config.ollama_base_url,
                "default_model": self.config.ollama_default_model,
                "timeout": self.config.ollama_timeout,
            })
            self.provider_requests["ollama"] = 0
            self.provider_errors["ollama"] = 0
            logger.debug("Ollama provider initialized")
        
        # OpenAI
        if self.config.openai_api_key and \
           "openai" in [self.config.primary_provider] + self.config.fallback_providers:
            self._providers["openai"] = OpenAIProvider({
                "base_url": self.config.openai_base_url,
                "default_model": self.config.openai_default_model,
                "timeout": self.config.openai_timeout,
                "api_key": self.config.openai_api_key,
            })
            self.provider_requests["openai"] = 0
            self.provider_errors["openai"] = 0
            logger.debug("OpenAI provider initialized")
        
        # Anthropic
        if self.config.anthropic_api_key and \
           "anthropic" in [self.config.primary_provider] + self.config.fallback_providers:
            self._providers["anthropic"] = AnthropicProvider({
                "base_url": self.config.anthropic_base_url,
                "default_model": self.config.anthropic_default_model,
                "timeout": self.config.anthropic_timeout,
                "api_key": self.config.anthropic_api_key,
            })
            self.provider_requests["anthropic"] = 0
            self.provider_errors["anthropic"] = 0
            logger.debug("Anthropic provider initialized")
        
        # Local
        if "local" in [self.config.primary_provider] + self.config.fallback_providers:
            self._providers["local"] = LocalProvider({
                "base_url": self.config.local_base_url,
                "default_model": self.config.local_default_model,
                "timeout": self.config.local_timeout,
            })
            self.provider_requests["local"] = 0
            self.provider_errors["local"] = 0
            logger.debug("Local provider initialized")
        
        if not self._providers:
            logger.warning("No providers initialized!")
    
    def _setup_cache(self):
        """Inicializa el cache de respuestas"""
        if self.config.cache_enabled:
            self._cache = ResponseCache(
                max_size=self.config.cache_max_size,
                ttl=self.config.cache_ttl
            )
            logger.debug(f"Response cache enabled (max_size={self.config.cache_max_size}, ttl={self.config.cache_ttl}s)")
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        provider: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        use_cache: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Genera respuesta de chat
        
        Args:
            messages: Lista de mensajes [{"role": "user", "content": "..."}]
            model: Modelo específico a usar (usa default del provider si None)
            provider: Provider específico (usa primary + fallback si None)
            temperature: Temperatura de generación (0-1)
            max_tokens: Máximo de tokens a generar
            use_cache: Si debe usar cache (default True)
            **kwargs: Parámetros adicionales del provider
            
        Returns:
            Respuesta en formato estándar:
            {
                "content": "texto de respuesta",
                "model": "modelo usado",
                "provider": "provider usado",
                "usage": {...},
                "finish_reason": "stop|length",
                "cached": True/False,
                "latency_ms": 123.4,
            }
        """
        self.total_requests += 1
        start_time = time.time()
        
        # Verificar cache
        if use_cache and self._cache:
            cached = self._cache.get(messages, model or "default", **kwargs)
            if cached:
                latency_ms = (time.time() - start_time) * 1000
                logger.debug(f"Cache hit for request (latency={latency_ms:.1f}ms)")
                cached["cached"] = True
                cached["latency_ms"] = latency_ms
                return cached
        
        # Determinar providers a intentar
        if provider:
            providers_to_try = [provider] if provider in self._providers else []
        else:
            providers_to_try = [self.config.primary_provider] + self.config.fallback_providers
            providers_to_try = [p for p in providers_to_try if p in self._providers]
        
        if not providers_to_try:
            raise ValueError(f"No valid providers available (requested: {provider})")
        
        # Intentar con cada provider
        last_error = None
        for idx, provider_name in enumerate(providers_to_try):
            if idx > 0:
                self.total_fallbacks += 1
                logger.warning(f"Falling back to provider: {provider_name}")
            
            try:
                provider_instance = self._providers[provider_name]
                self.provider_requests[provider_name] += 1
                
                if self.config.log_requests:
                    logger.info(f"Request to {provider_name}: {len(messages)} messages, model={model}")
                
                # Llamar al provider
                response = await provider_instance.chat(
                    messages=messages,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )
                
                # Agregar metadata
                latency_ms = (time.time() - start_time) * 1000
                response["provider"] = provider_name
                response["cached"] = False
                response["latency_ms"] = latency_ms
                
                # Cachear respuesta
                if use_cache and self._cache:
                    self._cache.set(messages, model or "default", response, **kwargs)
                
                logger.debug(f"Successful response from {provider_name} (latency={latency_ms:.1f}ms)")
                return response
                
            except Exception as e:
                last_error = e
                self.provider_errors[provider_name] += 1
                self.total_errors += 1
                logger.error(f"Error with provider {provider_name}: {e}")
                
                # Si no hay más providers, re-raise
                if idx == len(providers_to_try) - 1:
                    raise
        
        # No debería llegar aquí
        raise last_error or RuntimeError("All providers failed")
    
    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        provider: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Genera respuesta en streaming
        
        Args:
            Mismos que chat() (excepto use_cache)
            
        Yields:
            Chunks de texto de la respuesta
        """
        self.total_requests += 1
        
        # Determinar provider
        if provider:
            provider_name = provider if provider in self._providers else None
        else:
            # Solo primary provider para streaming (no fallback)
            provider_name = self.config.primary_provider if self.config.primary_provider in self._providers else None
        
        if not provider_name:
            raise ValueError(f"No valid provider for streaming (requested: {provider})")
        
        try:
            provider_instance = self._providers[provider_name]
            self.provider_requests[provider_name] += 1
            
            if self.config.log_requests:
                logger.info(f"Streaming request to {provider_name}: {len(messages)} messages")
            
            async for chunk in provider_instance.stream_chat(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            ):
                yield chunk
                
        except Exception as e:
            self.provider_errors[provider_name] += 1
            self.total_errors += 1
            logger.error(f"Streaming error with provider {provider_name}: {e}")
            raise
    
    async def embed(
        self,
        text: str,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        **kwargs
    ) -> List[float]:
        """
        Genera embeddings de texto
        
        Args:
            text: Texto a embeddear
            model: Modelo de embeddings (usa default si None)
            provider: Provider específico (usa primary si None)
            **kwargs: Parámetros adicionales
            
        Returns:
            Vector de embeddings
        """
        self.total_requests += 1
        
        # Determinar provider
        if provider:
            provider_name = provider if provider in self._providers else None
        else:
            provider_name = self.config.primary_provider if self.config.primary_provider in self._providers else None
        
        if not provider_name:
            raise ValueError(f"No valid provider for embeddings (requested: {provider})")
        
        try:
            provider_instance = self._providers[provider_name]
            self.provider_requests[provider_name] += 1
            
            return await provider_instance.embed(text=text, model=model, **kwargs)
            
        except Exception as e:
            self.provider_errors[provider_name] += 1
            self.total_errors += 1
            logger.error(f"Embedding error with provider {provider_name}: {e}")
            raise
    
    async def health_check(self, provider: Optional[str] = None) -> Dict[str, bool]:
        """
        Verifica health de providers
        
        Args:
            provider: Provider específico (verifica todos si None)
            
        Returns:
            Dict con status de cada provider {provider_name: is_healthy}
        """
        if provider:
            providers_to_check = [provider] if provider in self._providers else []
        else:
            providers_to_check = list(self._providers.keys())
        
        results = {}
        for provider_name in providers_to_check:
            try:
                is_healthy = await self._providers[provider_name].health_check()
                results[provider_name] = is_healthy
            except Exception as e:
                logger.error(f"Health check failed for {provider_name}: {e}")
                results[provider_name] = False
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de uso del gateway
        
        Returns:
            Dict con métricas de uso, cache, providers, etc.
        """
        stats = {
            "total_requests": self.total_requests,
            "total_errors": self.total_errors,
            "total_fallbacks": self.total_fallbacks,
            "error_rate": self.total_errors / self.total_requests if self.total_requests > 0 else 0.0,
            "providers": {
                name: {
                    "requests": self.provider_requests.get(name, 0),
                    "errors": self.provider_errors.get(name, 0),
                    "error_rate": (
                        self.provider_errors.get(name, 0) / self.provider_requests.get(name, 1)
                        if self.provider_requests.get(name, 0) > 0 else 0.0
                    ),
                }
                for name in self._providers.keys()
            },
            "config": {
                "primary_provider": self.config.primary_provider,
                "fallback_providers": self.config.fallback_providers,
                "cache_enabled": self.config.cache_enabled,
            },
        }
        
        if self._cache:
            stats["cache"] = self._cache.stats()
        
        return stats
    
    def clear_cache(self):
        """Limpia el cache de respuestas"""
        if self._cache:
            self._cache.clear()
            logger.info("Response cache cleared")


# Singleton instance
_gateway: Optional[LLMGateway] = None


def get_gateway(config: Optional[GatewayConfig] = None) -> LLMGateway:
    """
    Obtiene la instancia singleton del gateway
    
    Args:
        config: Configuración personalizada (usa get_config() si None)
        
    Returns:
        Instancia única del LLMGateway
    """
    global _gateway
    if _gateway is None:
        _gateway = LLMGateway(config)
    return _gateway
    

def reset_gateway():
    """Resets the singleton gateway instance (useful for tests)."""
    global _INSTANCE
    _INSTANCE = None

