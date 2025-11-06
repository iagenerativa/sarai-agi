import os
from dataclasses import dataclass


@dataclass
class LLMGatewayConfig:
    primary_provider: str
    fallback_providers: list

    # Ollama
    ollama_base_url: str
    ollama_model: str
    ollama_timeout: int

    # Local
    local_base_url: str
    local_model: str
    local_timeout: int

    # Cache
    cache_enabled: bool
    cache_ttl: int
    cache_max_size: int

    # Pooling, rate limiting, metrics
    pool_size: int
    pool_timeout: int
    rate_limit_enabled: bool

    log_level: str

    @staticmethod
    def from_env():
        def env(key, default=None):
            v = os.getenv(key)
            return default if v is None else v

        def env_bool(key, default=False):
            v = os.getenv(key)
            if v is None:
                return default
            return v.lower() in ("1", "true", "yes", "on")

        def env_int(key, default):
            v = os.getenv(key)
            try:
                return int(v) if v is not None else default
            except ValueError:
                return default

        primary = env("LLM_GATEWAY_PRIMARY_PROVIDER", "ollama")
        fallbacks = env("LLM_GATEWAY_FALLBACK_PROVIDERS", "").split(",")
        fallbacks = [f.strip() for f in fallbacks if f.strip()]

        return LLMGatewayConfig(
            primary_provider=primary,
            fallback_providers=fallbacks,
            ollama_base_url=env("LLM_GATEWAY_OLLAMA_BASE_URL", "http://localhost:11434"),
            ollama_model=env("LLM_GATEWAY_OLLAMA_MODEL", "llama3.2:latest"),
            ollama_timeout=env_int("LLM_GATEWAY_OLLAMA_TIMEOUT", 300),
            local_base_url=env("LLM_GATEWAY_LOCAL_BASE_URL", "http://localhost:8080"),
            local_model=env("LLM_GATEWAY_LOCAL_MODEL", "local-model"),
            local_timeout=env_int("LLM_GATEWAY_LOCAL_TIMEOUT", 300),
            cache_enabled=env_bool("LLM_GATEWAY_CACHE_ENABLED", True),
            cache_ttl=env_int("LLM_GATEWAY_CACHE_TTL", 3600),
            cache_max_size=env_int("LLM_GATEWAY_CACHE_MAX_SIZE", 1000),
            pool_size=env_int("LLM_GATEWAY_POOL_SIZE", 10),
            pool_timeout=env_int("LLM_GATEWAY_POOL_TIMEOUT", 30),
            rate_limit_enabled=env_bool("LLM_GATEWAY_RATE_LIMIT_ENABLED", False),
            log_level=env("LLM_GATEWAY_LOG_LEVEL", "INFO"),
        )
"""
Configuración del LLM Gateway

Gestiona la configuración centralizada del gateway desde variables de entorno.
"""

import os
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from pathlib import Path


@dataclass
class GatewayConfig:
    """Configuración del LLM Gateway"""
    
    # Provider principal
    primary_provider: str = "ollama"  # ollama, openai, anthropic, local
    
    # Providers de fallback (en orden)
    fallback_providers: list[str] = field(default_factory=lambda: ["local"])
    
    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_default_model: str = "llama3.2:latest"
    ollama_timeout: int = 300  # 5 minutos
    
    # OpenAI
    openai_api_key: Optional[str] = None
    openai_base_url: str = "https://api.openai.com/v1"
    openai_default_model: str = "gpt-4"
    openai_timeout: int = 120
    
    # Anthropic
    anthropic_api_key: Optional[str] = None
    anthropic_base_url: str = "https://api.anthropic.com"
    anthropic_default_model: str = "claude-3-5-sonnet-20241022"
    anthropic_timeout: int = 120
    
    # Local (llamada-cpp, etc.)
    local_base_url: str = "http://localhost:8080"
    local_default_model: str = "local-model"
    local_timeout: int = 300
    
    # Cache
    cache_enabled: bool = True
    cache_ttl: int = 3600  # 1 hora
    cache_max_size: int = 1000  # número de respuestas
    
    # Connection pooling
    pool_size: int = 10
    pool_timeout: int = 30
    
    # Rate limiting
    rate_limit_enabled: bool = False
    rate_limit_requests_per_minute: int = 60
    
    # Monitoring
    metrics_enabled: bool = True
    
    # Logging
    log_level: str = "INFO"
    log_requests: bool = False  # Puede ser verbose
    
    @classmethod
    def from_env(cls) -> "GatewayConfig":
        """Carga configuración desde variables de entorno"""
        
        # Parsear fallback providers
        fallback_str = os.getenv("LLM_GATEWAY_FALLBACK_PROVIDERS", "local")
        fallback_providers = [p.strip() for p in fallback_str.split(",")]
        
        return cls(
            # Provider
            primary_provider=os.getenv("LLM_GATEWAY_PRIMARY_PROVIDER", "ollama"),
            fallback_providers=fallback_providers,
            
            # Ollama
            ollama_base_url=os.getenv("LLM_GATEWAY_OLLAMA_BASE_URL", "http://localhost:11434"),
            ollama_default_model=os.getenv("LLM_GATEWAY_OLLAMA_MODEL", "llama3.2:latest"),
            ollama_timeout=int(os.getenv("LLM_GATEWAY_OLLAMA_TIMEOUT", "300")),
            
            # OpenAI
            openai_api_key=os.getenv("LLM_GATEWAY_OPENAI_API_KEY"),
            openai_base_url=os.getenv("LLM_GATEWAY_OPENAI_BASE_URL", "https://api.openai.com/v1"),
            openai_default_model=os.getenv("LLM_GATEWAY_OPENAI_MODEL", "gpt-4"),
            openai_timeout=int(os.getenv("LLM_GATEWAY_OPENAI_TIMEOUT", "120")),
            
            # Anthropic
            anthropic_api_key=os.getenv("LLM_GATEWAY_ANTHROPIC_API_KEY"),
            anthropic_base_url=os.getenv("LLM_GATEWAY_ANTHROPIC_BASE_URL", "https://api.anthropic.com"),
            anthropic_default_model=os.getenv("LLM_GATEWAY_ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"),
            anthropic_timeout=int(os.getenv("LLM_GATEWAY_ANTHROPIC_TIMEOUT", "120")),
            
            # Local
            local_base_url=os.getenv("LLM_GATEWAY_LOCAL_BASE_URL", "http://localhost:8080"),
            local_default_model=os.getenv("LLM_GATEWAY_LOCAL_MODEL", "local-model"),
            local_timeout=int(os.getenv("LLM_GATEWAY_LOCAL_TIMEOUT", "300")),
            
            # Cache
            cache_enabled=os.getenv("LLM_GATEWAY_CACHE_ENABLED", "true").lower() == "true",
            cache_ttl=int(os.getenv("LLM_GATEWAY_CACHE_TTL", "3600")),
            cache_max_size=int(os.getenv("LLM_GATEWAY_CACHE_MAX_SIZE", "1000")),
            
            # Connection pooling
            pool_size=int(os.getenv("LLM_GATEWAY_POOL_SIZE", "10")),
            pool_timeout=int(os.getenv("LLM_GATEWAY_POOL_TIMEOUT", "30")),
            
            # Rate limiting
            rate_limit_enabled=os.getenv("LLM_GATEWAY_RATE_LIMIT_ENABLED", "false").lower() == "true",
            rate_limit_requests_per_minute=int(os.getenv("LLM_GATEWAY_RATE_LIMIT_RPM", "60")),
            
            # Monitoring
            metrics_enabled=os.getenv("LLM_GATEWAY_METRICS_ENABLED", "true").lower() == "true",
            
            # Logging
            log_level=os.getenv("LLM_GATEWAY_LOG_LEVEL", "INFO"),
            log_requests=os.getenv("LLM_GATEWAY_LOG_REQUESTS", "false").lower() == "true",
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la configuración a diccionario"""
        return {
            "primary_provider": self.primary_provider,
            "fallback_providers": self.fallback_providers,
            "ollama": {
                "base_url": self.ollama_base_url,
                "default_model": self.ollama_default_model,
                "timeout": self.ollama_timeout,
            },
            "openai": {
                "base_url": self.openai_base_url,
                "default_model": self.openai_default_model,
                "timeout": self.openai_timeout,
                "api_key_set": self.openai_api_key is not None,
            },
            "anthropic": {
                "base_url": self.anthropic_base_url,
                "default_model": self.anthropic_default_model,
                "timeout": self.anthropic_timeout,
                "api_key_set": self.anthropic_api_key is not None,
            },
            "local": {
                "base_url": self.local_base_url,
                "default_model": self.local_default_model,
                "timeout": self.local_timeout,
            },
            "cache": {
                "enabled": self.cache_enabled,
                "ttl": self.cache_ttl,
                "max_size": self.cache_max_size,
            },
            "pool": {
                "size": self.pool_size,
                "timeout": self.pool_timeout,
            },
            "rate_limit": {
                "enabled": self.rate_limit_enabled,
                "requests_per_minute": self.rate_limit_requests_per_minute,
            },
            "metrics_enabled": self.metrics_enabled,
            "log_level": self.log_level,
            "log_requests": self.log_requests,
        }


# Singleton
_config: Optional[GatewayConfig] = None


def get_config() -> GatewayConfig:
    """Obtiene la configuración del gateway (singleton)"""
    global _config
    if _config is None:
        _config = GatewayConfig.from_env()
    return _config


def reload_config() -> GatewayConfig:
    """Recarga la configuración desde el entorno"""
    global _config
    _config = GatewayConfig.from_env()
    return _config
