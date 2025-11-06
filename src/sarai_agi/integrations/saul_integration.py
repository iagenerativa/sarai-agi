"""
SARAi + SAUL Integration Module

Integra SAUL (Speech And Understanding Layer) con SARAi vía gRPC.
Reemplaza las llamadas directas a TTS con llamadas al servidor SAUL.

Usage:
    from sarai_agi.integrations.saul_integration import SAULIntegration
    
    saul = SAULIntegration(host='localhost', port=50051)
    
    # Obtener respuesta con audio
    response = saul.respond_with_audio("Hola, ¿cómo estás?")
    
    # Solo TTS
    audio_data = saul.synthesize_audio("Este es un texto")
"""

import os
import logging
from typing import Optional, Dict, Any, Union
from pathlib import Path

logger = logging.getLogger(__name__)

# Intentar importar el cliente SAUL
try:
    import sys
    # Agregar path al proyecto SAUL si existe
    saul_path = Path(__file__).parent.parent.parent.parent.parent / "saul" / "src"
    if saul_path.exists():
        sys.path.insert(0, str(saul_path))
    
    from saul.client import SAULClient
    SAUL_AVAILABLE = True
except ImportError as e:
    logger.warning(f"SAUL client not available: {e}")
    SAUL_AVAILABLE = False
    SAULClient = None


class SAULIntegration:
    """
    Integración de SAUL con SARAi
    
    Proporciona interfaz unificada para:
    - Respuestas ultra-rápidas (TRM)
    - Síntesis de voz (TTS)
    - Streaming de audio
    - Health checks
    
    Examples:
        >>> saul = SAULIntegration()
        >>> if saul.is_available():
        ...     response = saul.respond("Hola")
        ...     print(response['text'])
    """
    
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        api_key: Optional[str] = None,
        enabled: bool = True,
        fallback_mode: str = "local"  # local, error, silent
    ):
        """
        Inicializa integración con SAUL.
        
        Args:
            host: Hostname de SAUL (default: localhost o SAUL_GRPC_HOST env)
            port: Puerto de SAUL (default: 50051 o SAUL_GRPC_PORT env)
            api_key: API key para autenticación (opcional, o SAUL_API_KEY env)
            enabled: Si la integración está habilitada
            fallback_mode: Comportamiento si SAUL no está disponible:
                - "local": Usar TTS local de SARAi
                - "error": Lanzar excepción
                - "silent": Retornar None
        """
        self.enabled = enabled and SAUL_AVAILABLE
        self.fallback_mode = fallback_mode
        
        # Configuración desde env o parámetros
        self.host = host or os.getenv("SAUL_GRPC_HOST", "localhost")
        self.port = port or int(os.getenv("SAUL_GRPC_PORT", "50051"))
        self.api_key = api_key or os.getenv("SAUL_API_KEY")
        
        # Cliente SAUL
        self.client: Optional[SAULClient] = None
        
        if self.enabled:
            try:
                self.client = SAULClient(
                    host=self.host,
                    port=self.port,
                    api_key=self.api_key
                )
                logger.info(f"SAUL integration enabled: {self.host}:{self.port}")
                
                # Verificar health
                health = self.client.health_check()
                if not health.get('healthy', False):
                    logger.warning(f"SAUL service unhealthy: {health}")
                    
            except Exception as e:
                logger.error(f"Failed to connect to SAUL: {e}")
                self.enabled = False
                self.client = None
        else:
            logger.info("SAUL integration disabled")
    
    def is_available(self) -> bool:
        """Verifica si SAUL está disponible"""
        if not self.enabled or not self.client:
            return False
        
        try:
            health = self.client.health_check()
            return health.get('healthy', False)
        except Exception as e:
            logger.warning(f"SAUL health check failed: {e}")
            return False
    
    # =========================================================================
    # Core Methods - Wrappers de SAULClient
    # =========================================================================
    
    def respond(
        self,
        query: str,
        timeout: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Obtiene respuesta de texto usando TRM de SAUL.
        
        Args:
            query: Query del usuario
            timeout: Timeout en segundos
        
        Returns:
            dict con 'text', 'confidence', 'performance' o None si no disponible
        """
        if not self.enabled or not self.client:
            return self._handle_unavailable("respond")
        
        try:
            return self.client.respond(query, timeout=timeout)
        except Exception as e:
            logger.error(f"SAUL respond error: {e}")
            return self._handle_unavailable("respond", error=e)
    
    def respond_with_audio(
        self,
        query: str,
        output_file: Optional[str] = None,
        speech_speed: float = 1.0,
        timeout: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Obtiene respuesta con audio sintetizado.
        
        Args:
            query: Query del usuario
            output_file: Path para guardar audio (opcional)
            speech_speed: Velocidad de habla (0.5-2.0)
            timeout: Timeout en segundos
        
        Returns:
            dict con 'text', 'audio_data', 'audio_file', etc. o None
        """
        if not self.enabled or not self.client:
            return self._handle_unavailable("respond_with_audio")
        
        try:
            return self.client.respond_with_audio(
                query,
                output_file=output_file,
                speech_speed=speech_speed,
                timeout=timeout
            )
        except Exception as e:
            logger.error(f"SAUL respond_with_audio error: {e}")
            return self._handle_unavailable("respond_with_audio", error=e)
    
    def synthesize_audio(
        self,
        text: str,
        output_file: Optional[str] = None,
        speed: float = 1.0,
        timeout: Optional[int] = None
    ) -> Optional[Union[bytes, str]]:
        """
        Sintetiza texto a audio (solo TTS, sin TRM).
        
        Args:
            text: Texto para sintetizar
            output_file: Path para guardar (opcional)
            speed: Velocidad de habla
            timeout: Timeout en segundos
        
        Returns:
            bytes de audio, path del archivo, o None
        """
        if not self.enabled or not self.client:
            return self._handle_unavailable("synthesize_audio")
        
        try:
            response = self.client.synthesize(
                text,
                output_file=output_file,
                speed=speed,
                timeout=timeout
            )
            
            if output_file:
                return response['audio_file']
            else:
                return response['audio_data']
                
        except Exception as e:
            logger.error(f"SAUL synthesize error: {e}")
            return self._handle_unavailable("synthesize_audio", error=e)
    
    def get_health(self) -> Dict[str, Any]:
        """
        Obtiene health status de SAUL.
        
        Returns:
            dict con 'healthy', 'uptime_seconds', 'services', etc.
        """
        if not self.enabled or not self.client:
            return {'healthy': False, 'reason': 'SAUL not enabled'}
        
        try:
            return self.client.health_check()
        except Exception as e:
            logger.error(f"SAUL health check error: {e}")
            return {'healthy': False, 'error': str(e)}
    
    def get_metrics(self) -> Optional[Dict[str, Any]]:
        """
        Obtiene métricas de SAUL.
        
        Returns:
            dict con métricas o None
        """
        if not self.enabled or not self.client:
            return None
        
        try:
            return self.client.get_metrics()
        except Exception as e:
            logger.error(f"SAUL metrics error: {e}")
            return None
    
    # =========================================================================
    # Helpers
    # =========================================================================
    
    def _handle_unavailable(
        self,
        method_name: str,
        error: Optional[Exception] = None
    ) -> Optional[Any]:
        """
        Maneja casos donde SAUL no está disponible.
        
        Args:
            method_name: Nombre del método que falló
            error: Excepción si hubo error
        
        Returns:
            None, lanza excepción, o ejecuta fallback según fallback_mode
        """
        if self.fallback_mode == "error":
            msg = f"SAUL not available for {method_name}"
            if error:
                raise RuntimeError(f"{msg}: {error}") from error
            else:
                raise RuntimeError(msg)
        
        elif self.fallback_mode == "local":
            logger.warning(f"SAUL not available for {method_name}, using local fallback")
            # TODO: Implementar fallback a TTS local de SARAi
            return None
        
        else:  # silent
            logger.debug(f"SAUL not available for {method_name}, returning None")
            return None
    
    def close(self):
        """Cierra la conexión con SAUL"""
        if self.client:
            self.client.close()
            logger.info("SAUL connection closed")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


# =============================================================================
# Factory function para facilitar integración
# =============================================================================

def create_saul_integration(
    enabled: Optional[bool] = None,
    **kwargs
) -> SAULIntegration:
    """
    Factory function para crear integración SAUL.
    
    Args:
        enabled: Si está habilitado (default: True si SAUL_ENABLED env es true)
        **kwargs: Argumentos para SAULIntegration
    
    Returns:
        SAULIntegration instance
    
    Examples:
        >>> saul = create_saul_integration()
        >>> if saul.is_available():
        ...     response = saul.respond("Test")
    """
    if enabled is None:
        enabled = os.getenv("SAUL_ENABLED", "true").lower() == "true"
    
    return SAULIntegration(enabled=enabled, **kwargs)


# =============================================================================
# Integration con pipeline de SARAi
# =============================================================================

class SARAiSAULAdapter:
    """
    Adapter para integrar SAUL en el pipeline de SARAi.
    
    Permite usar SAUL como reemplazo drop-in del TTS existente.
    """
    
    def __init__(self, saul: Optional[SAULIntegration] = None):
        """
        Inicializa adapter.
        
        Args:
            saul: Instancia de SAULIntegration (se crea si no se provee)
        """
        self.saul = saul or create_saul_integration()
    
    def synthesize(
        self,
        text: str,
        speed: float = 1.0,
        output_path: Optional[str] = None
    ) -> Optional[bytes]:
        """
        Interfaz compatible con TTS de SARAi.
        
        Args:
            text: Texto para sintetizar
            speed: Velocidad de habla
            output_path: Path para guardar (opcional)
        
        Returns:
            bytes de audio o None
        """
        if not self.saul.is_available():
            logger.warning("SAUL not available, TTS synthesis skipped")
            return None
        
        result = self.saul.synthesize_audio(
            text=text,
            speed=speed,
            output_file=output_path
        )
        
        if isinstance(result, bytes):
            return result
        elif isinstance(result, str):  # Es un path
            with open(result, 'rb') as f:
                return f.read()
        else:
            return None


# =============================================================================
# Ejemplo de uso
# =============================================================================

if __name__ == "__main__":
    import json
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Crear integración
    with create_saul_integration() as saul:
        
        # Health check
        health = saul.get_health()
        print(f"\n=== SAUL Health ===")
        print(json.dumps(health, indent=2))
        
        if not saul.is_available():
            print("\n⚠️  SAUL not available")
            exit(1)
        
        # Respuesta de texto
        print(f"\n=== Text Response ===")
        response = saul.respond("Hola, ¿cómo estás?")
        if response:
            print(f"Text: {response['text']}")
            print(f"Confidence: {response['confidence']:.2f}")
            print(f"Latency: {response['performance']['total_time_ms']:.2f}ms")
        
        # Respuesta con audio
        print(f"\n=== Audio Response ===")
        response = saul.respond_with_audio(
            "¿Qué hora es?",
            output_file="test_response.wav"
        )
        if response:
            print(f"Text: {response['text']}")
            print(f"Audio file: {response['audio_file']}")
            print(f"Duration: {response['audio_duration']:.2f}s")
        
        # Solo síntesis
        print(f"\n=== TTS Synthesis ===")
        audio_file = saul.synthesize_audio(
            "Este es un texto de prueba",
            output_file="test_synth.wav"
        )
        if audio_file:
            print(f"Audio saved to: {audio_file}")
        
        # Métricas
        print(f"\n=== Metrics ===")
        metrics = saul.get_metrics()
        if metrics:
            print(json.dumps(metrics, indent=2))
