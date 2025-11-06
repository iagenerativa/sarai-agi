import time
from collections import OrderedDict
from threading import Lock


class LRUCache:
    """Simple thread-safe LRU cache with TTL.

    Not optimized for huge scale; intended for small/shared response cache.
    """

    def __init__(self, max_size=1000, ttl=3600):
        self.max_size = max_size
        self.ttl = ttl
        self._data = OrderedDict()
        self._lock = Lock()

    def _purge_expired(self):
        now = time.time()
        keys_to_delete = []
        for k, (v, ts) in list(self._data.items()):
            if ts + self.ttl < now:
                keys_to_delete.append(k)
        for k in keys_to_delete:
            self._data.pop(k, None)

    def get(self, key):
        with self._lock:
            self._purge_expired()
            item = self._data.get(key)
            if item is None:
                return None
            value, ts = item
            # move to end as most recently used
            self._data.move_to_end(key)
            return value

    def set(self, key, value):
        with self._lock:
            self._purge_expired()
            if key in self._data:
                self._data.move_to_end(key)
            self._data[key] = (value, time.time())
            if len(self._data) > self.max_size:
                self._data.popitem(last=False)

    def clear(self):
        with self._lock:
            self._data.clear()
"""
Cache de respuestas del LLM Gateway

Implementa caching de respuestas con TTL y LRU eviction.
"""

import hashlib
import json
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from collections import OrderedDict


@dataclass
class CacheEntry:
    """Entrada en el cache"""
    response: Dict[str, Any]
    timestamp: float
    hits: int = 0


class ResponseCache:
    """Cache LRU con TTL para respuestas de LLM"""
    
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        """
        Args:
            max_size: Número máximo de entradas
            ttl: Time-to-live en segundos
        """
        self.max_size = max_size
        self.ttl = ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        
        # Métricas
        self.hits = 0
        self.misses = 0
        self.evictions = 0
    
    def _make_key(self, messages: List[Dict[str, str]], model: str, **kwargs) -> str:
        """Genera clave de cache desde parámetros"""
        # Serializar parámetros relevantes
        params = {
            "messages": messages,
            "model": model,
            **kwargs
        }
        
        # Hash determinista
        serialized = json.dumps(params, sort_keys=True)
        return hashlib.sha256(serialized.encode()).hexdigest()
    
    def get(self, messages: List[Dict[str, str]], model: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Obtiene respuesta del cache si existe y no expiró
        
        Args:
            messages: Mensajes de la conversación
            model: Modelo usado
            **kwargs: Parámetros adicionales
            
        Returns:
            Respuesta cacheada o None si no existe/expiró
        """
        key = self._make_key(messages, model, **kwargs)
        
        if key not in self._cache:
            self.misses += 1
            return None
        
        entry = self._cache[key]
        
        # Verificar expiración
        if time.time() - entry.timestamp > self.ttl:
            del self._cache[key]
            self.misses += 1
            return None
        
        # Cache hit - mover al final (LRU)
        self._cache.move_to_end(key)
        entry.hits += 1
        self.hits += 1
        
        return entry.response
    
    def set(self, messages: List[Dict[str, str]], model: str, response: Dict[str, Any], **kwargs):
        """
        Guarda respuesta en cache
        
        Args:
            messages: Mensajes de la conversación
            model: Modelo usado
            response: Respuesta a cachear
            **kwargs: Parámetros adicionales
        """
        key = self._make_key(messages, model, **kwargs)
        
        # Eviction LRU si está lleno
        if len(self._cache) >= self.max_size and key not in self._cache:
            self._cache.popitem(last=False)  # Remove oldest
            self.evictions += 1
        
        # Guardar entrada
        self._cache[key] = CacheEntry(
            response=response,
            timestamp=time.time()
        )
        self._cache.move_to_end(key)
    
    def invalidate(self, messages: List[Dict[str, str]], model: str, **kwargs):
        """Invalida entrada específica del cache"""
        key = self._make_key(messages, model, **kwargs)
        if key in self._cache:
            del self._cache[key]
    
    def clear(self):
        """Limpia todo el cache"""
        self._cache.clear()
        self.hits = 0
        self.misses = 0
        self.evictions = 0
    
    def stats(self) -> Dict[str, Any]:
        """Retorna estadísticas del cache"""
        total_requests = self.hits + self.misses
        hit_rate = self.hits / total_requests if total_requests > 0 else 0.0
        
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate,
            "evictions": self.evictions,
            "ttl": self.ttl,
        }
    
    def cleanup_expired(self):
        """Limpia entradas expiradas (llamar periódicamente)"""
        now = time.time()
        expired_keys = [
            key for key, entry in self._cache.items()
            if now - entry.timestamp > self.ttl
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        return len(expired_keys)
