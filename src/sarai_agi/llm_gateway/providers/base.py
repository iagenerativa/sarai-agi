"""
Base provider para LLM Gateway

Define interfaz común para todos los providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, AsyncIterator


class BaseProvider(ABC):
    """Clase base para providers de LLM"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Args:
            config: Configuración específica del provider
        """
        self.config = config
        self.base_url = config.get("base_url", "")
        self.default_model = config.get("default_model", "")
        self.timeout = config.get("timeout", 120)
    
    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Genera respuesta de chat
        
        Args:
            messages: Lista de mensajes [{"role": "user", "content": "..."}]
            model: Modelo a usar (usa default_model si None)
            temperature: Temperatura de generación (0-1)
            max_tokens: Máximo de tokens a generar
            **kwargs: Parámetros adicionales específicos del provider
            
        Returns:
            Respuesta en formato estándar:
            {
                "content": "texto de respuesta",
                "model": "modelo usado",
                "usage": {"prompt_tokens": X, "completion_tokens": Y, "total_tokens": Z},
                "finish_reason": "stop|length|...",
            }
        """
        pass
    
    @abstractmethod
    async def embed(
        self,
        text: str,
        model: Optional[str] = None,
        **kwargs
    ) -> List[float]:
        """
        Genera embedding de texto
        
        Args:
            text: Texto a embeddear
            model: Modelo de embeddings (usa default si None)
            **kwargs: Parámetros adicionales
            
        Returns:
            Vector de embeddings
        """
        pass
    
    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Genera respuesta de chat en streaming (opcional)
        
        Args:
            Mismos que chat()
            
        Yields:
            Chunks de texto de la respuesta
        """
        # Default: no streaming, devuelve respuesta completa
        response = await self.chat(messages, model, temperature, max_tokens, **kwargs)
        yield response["content"]
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        Verifica si el provider está disponible
        
        Returns:
            True si el provider está operativo
        """
        pass
    
    def get_default_model(self) -> str:
        """Retorna el modelo por defecto del provider"""
        return self.default_model
