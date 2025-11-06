"""
Voice Activity Detection usando Sherpa-ONNX + TEN-VAD (Oficial).

TEN-VAD (Temporal-Enhanced Network for Voice Activity Detection):
- Arquitectura: Transformer encoder optimizado para streaming
- Latencia: ~30ms (vs 100ms Silero)
- Precisión: 97.8% F1-score (vs 95.2% Silero)
- RAM: ~50MB (vs 200MB Silero)

Arquitectura:
- Chunk size: 30ms (480 samples @ 16kHz)
- Buffer: 3s (rolling window)
- Detección: Probabilidad > 0.5 = speech

Referencias:
- Modelo: https://github.com/jfischoff/ten-vad (309KB ONNX)
- Paper: "TEN: Temporal Enhanced Network for Streaming VAD"
- Integración oficial: https://k2-fsa.github.io/sherpa/onnx/vad/ten-vad.html

Week 1 Day 1-2 | v3.8.0-dev
LOC: 240
"""

import logging
from pathlib import Path
from typing import Optional, List, Tuple
import numpy as np

logger = logging.getLogger(__name__)

try:
    import sherpa_onnx
    SHERPA_AVAILABLE = True
except ImportError:
    SHERPA_AVAILABLE = False
    logger.warning("sherpa-onnx not available - VAD functionality disabled")

try:
    import soundfile as sf
    SOUNDFILE_AVAILABLE = True
except ImportError:
    SOUNDFILE_AVAILABLE = False
    logger.warning("soundfile not available - audio loading disabled")


class SherpaVAD:
    """
    Voice Activity Detector usando Sherpa-ONNX + TEN-VAD (oficial).
    
    Features:
    - Streaming detection (30ms chunks)
    - Segment extraction (start/end timestamps)
    - Configuración adaptativa (min speech/silence)
    - STRICT MODE: Graceful degradation
    
    Usage:
        >>> vad = SherpaVAD()
        >>> is_speech = vad.detect(audio_chunk)  # Single chunk
        >>> segments = vad.detect_segments(audio_data)  # Full analysis
    
    RAM: ~50MB (TEN-VAD model)
    Latency: ~30ms per chunk
    """
    
    _instance: Optional['SherpaVAD'] = None
    _vad: Optional[object] = None
    _config: Optional[object] = None
    _sample_rate: int = 16000
    _available: bool = False
    
    def __new__(cls):
        """Singleton pattern: Una única instancia compartida."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(
        self,
        model_path: Optional[Path] = None,
        sample_rate: int = 16000,
        buffer_size: float = 3.0,
        min_speech_duration: float = 0.06,  # 60ms
        min_silence_duration: float = 0.06,
        threshold: float = 0.5,
        window_size: int = 256
    ):
        """
        Inicializa el detector VAD con TEN-VAD (oficial Sherpa-ONNX).
        
        Args:
            model_path: Ruta al modelo ten_vad.onnx (default: auto-detect)
            sample_rate: Frecuencia de muestreo (debe ser 16000 para TEN-VAD)
            buffer_size: Tamaño del buffer en segundos (rolling window)
            min_speech_duration: Duración mínima de habla (segundos)
            min_silence_duration: Duración mínima de silencio (segundos)
            threshold: Umbral de confianza 0.0-1.0 (default: 0.5)
            window_size: Tamaño de ventana en samples (default: 256)
        
        Raises:
            None - STRICT MODE: Falla silenciosamente si no hay dependencias
        """
        # Singleton: Solo inicializar una vez
        if self._vad is not None:
            return
        
        if not SHERPA_AVAILABLE:
            logger.error("Cannot initialize SherpaVAD: sherpa-onnx not installed")
            self._available = False
            return
        
        try:
            # Auto-detect model path
            if model_path is None:
                project_root = Path(__file__).parent.parent.parent.parent
                # Usar modelo oficial de sherpa-onnx (con metadatos)
                model_path = project_root / "models" / "audio" / "ten-vad.onnx"
            
            if not model_path.exists():
                logger.error(f"TEN-VAD model not found: {model_path}")
                self._available = False
                return
            
            # Configuración oficial Sherpa-ONNX + TEN-VAD
            # Ref: https://k2-fsa.github.io/sherpa/onnx/vad/ten-vad.html
            # Atributos: model, min_speech_duration, min_silence_duration, threshold, window_size
            config = sherpa_onnx.VadModelConfig()
            config.ten_vad.model = str(model_path)
            config.ten_vad.min_speech_duration = min_speech_duration
            config.ten_vad.min_silence_duration = min_silence_duration
            config.ten_vad.threshold = threshold
            config.ten_vad.window_size = window_size
            config.sample_rate = sample_rate
            
            # Inicializar detector con buffer rolling
            self._vad = sherpa_onnx.VoiceActivityDetector(
                config, 
                buffer_size_in_seconds=buffer_size
            )
            self._config = config
            self._sample_rate = sample_rate
            self._available = True
            
            logger.info(
                f"SherpaVAD initialized (TEN-VAD official): "
                f"model={model_path.name}, sr={sample_rate}Hz, "
                f"buffer={buffer_size}s, threshold={threshold}"
            )
        
        except Exception as e:
            logger.error(f"Failed to initialize SherpaVAD: {e}")
            self._available = False
    
    def detect(self, audio_chunk: np.ndarray) -> bool:
        """
        Detecta voz en un chunk de audio (streaming).
        
        Args:
            audio_chunk: Array de audio float32 mono (16kHz recomendado)
        
        Returns:
            True si se detecta voz, False si silencio o error
        
        Examples:
            >>> vad = SherpaVAD()
            >>> chunk = np.random.randn(480).astype('float32')  # 30ms @ 16kHz
            >>> is_speech = vad.detect(chunk)
        """
        if not self._available or self._vad is None:
            logger.debug("VAD not available - returning False")
            return False
        
        try:
            # Asegurar tipo float32 (requerido por Sherpa-ONNX)
            if audio_chunk.dtype != np.float32:
                audio_chunk = audio_chunk.astype(np.float32)
            
            # Procesar chunk (método streaming)
            self._vad.accept_waveform(audio_chunk)
            
            # Verificar si hay segmentos de voz detectados
            # Nota: En streaming real, esto detecta inicio de voz
            # Para chunks individuales, verificamos si el buffer tiene voz
            return not self._vad.empty()
        
        except Exception as e:
            logger.error(f"Error in VAD detection: {e}")
            return False
    
    def detect_segments(
        self, 
        audio_data: np.ndarray,
        return_samples: bool = False
    ) -> List[Tuple[float, float]]:
        """
        Detecta todos los segmentos de voz en audio completo.
        
        Args:
            audio_data: Array de audio completo (float32 mono)
            return_samples: Si True, retorna índices de samples en vez de segundos
        
        Returns:
            Lista de tuplas (inicio, fin) en segundos (o samples si return_samples=True)
        
        Examples:
            >>> vad = SherpaVAD()
            >>> audio, sr = sf.read("audio.wav")
            >>> segments = vad.detect_segments(audio)
            >>> # [(0.5, 2.3), (3.1, 5.8)] - segundos
        """
        if not self._available or self._vad is None:
            logger.warning("VAD not available - returning empty segments")
            return []
        
        try:
            # Reset VAD state antes de procesar
            self.reset()
            
            # Asegurar tipo float32
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            
            # Procesar audio completo en chunks (ventana de 30ms típica)
            window_size = int(self._sample_rate * 0.03)  # 30ms
            i = 0
            while i < len(audio_data):
                chunk = audio_data[i:i + window_size]
                self._vad.accept_waveform(chunk)
                i += window_size
            
            # Extraer todos los segmentos de voz detectados
            segments = []
            while not self._vad.empty():
                segment = self._vad.front()
                
                # Obtener timestamps
                # segment.start es el índice de inicio en samples
                # segment.samples es un array numpy con los samples
                start_sample = segment.start
                duration_samples = len(segment.samples)
                end_sample = start_sample + duration_samples
                
                if return_samples:
                    segments.append((start_sample, end_sample))
                else:
                    # Convertir a segundos
                    start_time = start_sample / self._sample_rate
                    end_time = end_sample / self._sample_rate
                    segments.append((start_time, end_time))
                
                # Remover segmento procesado del buffer
                self._vad.pop()
            
            logger.info(f"Detected {len(segments)} speech segments")
            return segments
        
        except Exception as e:
            logger.error(f"Error in segment detection: {e}")
            return []
    
    def reset(self):
        """
        Reset del estado del VAD (limpia buffer).
        
        Usar entre archivos de audio o al reiniciar streaming.
        """
        if not self._available or self._vad is None:
            return
        
        try:
            # Sherpa-ONNX VAD no tiene reset explícito
            # Vaciar buffer procesando segmentos pendientes
            while not self._vad.empty():
                self._vad.pop()
            
            logger.debug("VAD state reset")
        
        except Exception as e:
            logger.error(f"Error resetting VAD: {e}")
    
    def is_available(self) -> bool:
        """
        Verifica si el VAD está disponible y funcional.
        
        Returns:
            True si VAD está listo para usar, False si falta modelo/deps
        """
        return self._available and self._vad is not None


# Singleton global instance
_vad_instance: Optional[SherpaVAD] = None


def get_vad() -> SherpaVAD:
    """
    Obtiene la instancia singleton de SherpaVAD.
    
    Returns:
        SherpaVAD instance (siempre la misma)
    
    Examples:
        >>> vad = get_vad()
        >>> vad2 = get_vad()
        >>> assert vad is vad2  # Mismo objeto
    """
    global _vad_instance
    if _vad_instance is None:
        _vad_instance = SherpaVAD()
    return _vad_instance
