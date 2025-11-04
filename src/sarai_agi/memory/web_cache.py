"""
SARAi AGI - Web Cache Module

Sistema de caché persistente para búsquedas web con SearXNG.
Migrado desde SARAi_v2 v2.10 con adaptaciones para arquitectura modular.

Características:
- Cache persistente con diskcache (1GB max)
- TTL dinámico: 1h general, 5min para queries time-sensitive
- Timeout 10s por búsqueda (no bloquea sistema)
- Respeto total de Safe Mode
- Hit rate objetivo: ≥95%

Uso:
    from sarai_agi.memory.web_cache import WebCache

    cache = WebCache(searxng_url="http://localhost:8888")
    results = cache.get("¿Cómo está el clima en Tokio?")

    if results:
        for snippet in results["snippets"]:
            print(f"{snippet['title']}: {snippet['content'][:100]}...")
"""

import hashlib
import logging
import os
import time
from datetime import datetime
from typing import Dict, Optional

try:
    import requests
except ImportError:
    requests = None

try:
    from diskcache import Cache
except ImportError:
    Cache = None

# Safe Mode check - adaptado para sarai-agi
# En SARAi_v2 está en core.audit, aquí lo importamos del módulo de seguridad
try:
    from sarai_agi.security.resilience import is_safe_mode
except ImportError:
    # Fallback si no está disponible
    def is_safe_mode() -> bool:
        return os.getenv("SARAI_SAFE_MODE", "false").lower() == "true"


logger = logging.getLogger(__name__)


class WebCache:
    """
    Cache persistente de búsquedas web con SearXNG local

    Configuración recomendada:
    - SearXNG: docker run -d -p 8888:8080 searxng/searxng
    - TTL: 3600s (1h) para queries generales, 300s (5min) para time-sensitive
    - Max snippets: 5 (balance entre contexto y RAM)

    Args:
        searxng_url: URL del servidor SearXNG (default: http://localhost:8888)
        cache_dir: Directorio para cache persistente (default: state/web_cache)
        ttl: Time-to-live en segundos para cache (default: 3600)
        max_snippets: Máximo de snippets a retornar (default: 5)
        search_timeout: Timeout para búsquedas en segundos (default: 10)
    """

    def __init__(
        self,
        searxng_url: str = "http://localhost:8888",
        cache_dir: str = "state/web_cache",
        ttl: int = 3600,
        max_snippets: int = 5,
        search_timeout: int = 10
    ):
        self.searxng_url = searxng_url.rstrip('/')
        self.ttl = ttl
        self.max_snippets = max_snippets
        self.search_timeout = search_timeout

        # Inicializar cache solo si diskcache está disponible
        if Cache is not None:
            os.makedirs(cache_dir, exist_ok=True)
            self.cache = Cache(cache_dir, size_limit=1024**3)  # 1GB max
        else:
            logger.warning("diskcache no disponible, cache deshabilitado")
            self.cache = None

        # Verificar requests
        if requests is None:
            logger.error("requests no disponible, búsquedas web deshabilitadas")

    def _normalize_query(self, query: str) -> str:
        """Normaliza query para cache key (lowercase, strip)"""
        return query.lower().strip()

    def _cache_key(self, query: str) -> str:
        """Genera key SHA-256 para diskcache"""
        normalized = self._normalize_query(query)
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()

    def _is_time_sensitive(self, query: str) -> bool:
        """
        Detecta si la query requiere datos recientes (TTL reducido)

        Ejemplos time-sensitive:
        - "clima en Tokio"
        - "precio de Bitcoin"
        - "noticias de hoy"
        - "resultados del partido"

        Returns:
            True si la query es time-sensitive (TTL 5min)
        """
        time_keywords = [
            "clima", "weather", "precio", "price", "stock",
            "noticias", "news", "hoy", "today", "ahora", "now",
            "partido", "match", "resultado", "score", "live",
            "temperatura", "temperature", "forecast", "pronóstico"
        ]
        query_lower = query.lower()
        return any(kw in query_lower for kw in time_keywords)

    def get(self, query: str) -> Optional[Dict]:
        """
        Obtiene resultados de búsqueda (cache o SearXNG)

        Args:
            query: Query de búsqueda del usuario

        Returns:
            {
                "query": str,
                "snippets": List[Dict],  # [{"title": "", "url": "", "content": ""}]
                "timestamp": str,
                "source": "cache" | "searxng"
            }
            None si Safe Mode activo, fallo total, o dependencias no disponibles
        """
        # GARANTÍA 1: Respeto de Safe Mode
        if is_safe_mode():
            logger.warning("Web cache: Safe Mode activo, búsqueda bloqueada")
            return None

        # GARANTÍA 2: Verificar dependencias
        if requests is None:
            logger.error("requests no disponible, no se puede buscar")
            return None

        # GARANTÍA 3: Búsqueda en cache
        if self.cache is not None:
            cache_key = self._cache_key(query)
            cached_result = self.cache.get(cache_key)

            if cached_result is not None:
                # Verificar si TTL aún válido
                age = time.time() - cached_result["cache_timestamp"]
                ttl = 300 if self._is_time_sensitive(query) else self.ttl

                if age < ttl:
                    logger.info(f"Cache HIT: '{query[:60]}...' (age: {age:.1f}s)")
                    cached_result["source"] = "cache"
                    return cached_result
                else:
                    logger.info(f"Cache EXPIRED: '{query[:60]}...' (age: {age:.1f}s > {ttl}s)")

        # GARANTÍA 4: Búsqueda en SearXNG (cache miss o expirado)
        logger.info(f"Cache MISS: '{query[:60]}...', buscando en SearXNG...")

        try:
            # Construir request a SearXNG
            search_url = f"{self.searxng_url}/search"
            params = {
                "q": query,
                "format": "json",
                "language": "es",
                "time_range": "",
                "safesearch": "1"
            }

            response = requests.get(
                search_url,
                params=params,
                timeout=self.search_timeout
            )

            if response.status_code != 200:
                logger.error(f"SearXNG error: status {response.status_code}")
                return None

            data = response.json()
            results = data.get("results", [])

            if not results:
                logger.warning(f"SearXNG retornó 0 resultados para '{query[:60]}...'")
                return None

            # Construir snippets (max: self.max_snippets)
            snippets = []
            for result in results[:self.max_snippets]:
                snippet = {
                    "title": result.get("title", "Sin título"),
                    "url": result.get("url", ""),
                    "content": result.get("content", "")
                }
                snippets.append(snippet)

            # Construir resultado
            search_result = {
                "query": query,
                "snippets": snippets,
                "timestamp": datetime.now().isoformat(),
                "source": "searxng",
                "cache_timestamp": time.time()
            }

            # Guardar en cache
            if self.cache is not None:
                cache_key = self._cache_key(query)
                self.cache.set(cache_key, search_result)
                logger.info(f"Cached: '{query[:60]}...' ({len(snippets)} snippets)")

            return search_result

        except requests.Timeout:
            logger.error(f"SearXNG timeout ({self.search_timeout}s) para '{query[:60]}...'")
            return None

        except requests.RequestException as e:
            logger.error(f"SearXNG request error: {e}")
            return None

        except Exception as e:
            logger.error(f"Búsqueda web error inesperado: {e}")
            return None

    def clear_cache(self):
        """Limpia todo el cache"""
        if self.cache is not None:
            self.cache.clear()
            logger.info("Cache web limpiado completamente")

    def get_stats(self) -> Dict:
        """
        Obtiene estadísticas del cache

        Returns:
            {
                "size_bytes": int,
                "entry_count": int,
                "hit_rate": float  # Aproximado, si diskcache lo soporta
            }
        """
        if self.cache is None:
            return {"size_bytes": 0, "entry_count": 0, "hit_rate": 0.0}

        try:
            stats = {
                "size_bytes": self.cache.volume(),
                "entry_count": len(self.cache),
                "hit_rate": 0.0  # diskcache no trackea hit rate nativamente
            }
            return stats
        except Exception as e:
            logger.error(f"Error obteniendo stats de cache: {e}")
            return {"size_bytes": 0, "entry_count": 0, "hit_rate": 0.0}


# Singleton global para reutilización
_web_cache_instance: Optional[WebCache] = None


def get_web_cache(
    searxng_url: Optional[str] = None,
    **kwargs
) -> WebCache:
    """
    Factory function para obtener instancia singleton de WebCache

    Args:
        searxng_url: URL de SearXNG (default desde env SEARXNG_URL o localhost)
        **kwargs: Argumentos adicionales para WebCache()

    Returns:
        Instancia singleton de WebCache
    """
    global _web_cache_instance

    if _web_cache_instance is None:
        # Leer de variable de entorno si no se especifica
        if searxng_url is None:
            searxng_url = os.getenv("SEARXNG_URL", "http://localhost:8888")

        _web_cache_instance = WebCache(searxng_url=searxng_url, **kwargs)

    return _web_cache_instance


def cached_search(query: str) -> Optional[Dict]:
    """
    Convenience function para búsqueda con cache singleton

    Args:
        query: Query de búsqueda

    Returns:
        Resultados de búsqueda o None
    """
    cache = get_web_cache()
    return cache.get(query)
