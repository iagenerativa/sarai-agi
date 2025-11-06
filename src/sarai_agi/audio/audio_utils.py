"""
Utilidades de preprocesamiento de audio para STT y VAD.

Funciones para convertir cualquier formato de audio a la configuración
estándar requerida por los modelos:
- Frecuencia de muestreo: 16,000 Hz (16 kHz)
- Canales: Mono (1 canal)
- Profundidad: 16 bits PCM (int16) o float32
- Formato: Sin comprimir

Soporta conversión desde:
- MP3, M4A, OGG, FLAC (vía soundfile/librosa)
- WAV con diferentes sample rates
- Stereo → Mono
- 8kHz, 22.05kHz, 44.1kHz, 48kHz → 16kHz

Week 1 Day 1-2 | v3.8.0-dev
LOC: 120
"""

import logging
from pathlib import Path
from typing import Optional, Tuple, Union
import numpy as np

logger = logging.getLogger(__name__)

try:
    import soundfile as sf
    SOUNDFILE_AVAILABLE = True
except ImportError:
    SOUNDFILE_AVAILABLE = False
    logger.warning("soundfile not available - audio conversion limited")

try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    logger.debug("librosa not available - using soundfile only")


def preprocess_audio(
    audio_path: Union[str, Path],
    target_sr: int = 16000,
    target_channels: int = 1,
    target_dtype: str = 'float32'
) -> Tuple[np.ndarray, int]:
    """
    Preprocesa audio a formato estándar para STT/VAD.
    
    Convierte cualquier formato de audio a:
    - Sample rate: 16,000 Hz (configurable)
    - Canales: Mono (configurable)
    - Tipo: float32 o int16
    
    Args:
        audio_path: Ruta al archivo de audio (MP3, WAV, M4A, etc.)
        target_sr: Frecuencia de muestreo objetivo (default: 16000)
        target_channels: Número de canales objetivo (default: 1 = mono)
        target_dtype: Tipo de datos ('float32' o 'int16')
    
    Returns:
        Tupla (audio_data, sample_rate) donde:
        - audio_data: numpy array con audio procesado
        - sample_rate: frecuencia de muestreo (siempre == target_sr)
    
    Raises:
        ValueError: Si falta soundfile/librosa o archivo no existe
    
    Examples:
        >>> # Convertir MP3 a 16kHz mono float32
        >>> audio, sr = preprocess_audio("podcast.mp3")
        >>> assert sr == 16000
        >>> assert audio.ndim == 1  # Mono
        >>> assert audio.dtype == np.float32
        
        >>> # Convertir WAV estéreo 44.1kHz a 16kHz mono
        >>> audio, sr = preprocess_audio("music.wav", target_dtype='int16')
        >>> assert sr == 16000
        >>> assert audio.dtype == np.int16
    """
    audio_path = Path(audio_path)
    
    if not audio_path.exists():
        raise ValueError(f"Audio file not found: {audio_path}")
    
    # Estrategia 1: Usar librosa (más robusto, soporta más formatos)
    if LIBROSA_AVAILABLE:
        try:
            audio, sr = librosa.load(
                str(audio_path),
                sr=target_sr,  # Resample automático
                mono=(target_channels == 1)
            )
            
            logger.debug(
                f"Loaded with librosa: {audio_path.name} "
                f"({sr}Hz, {audio.shape}, {audio.dtype})"
            )
            
            # Convertir tipo si es necesario
            if target_dtype == 'int16' and audio.dtype != np.int16:
                audio = (audio * 32767).astype(np.int16)
            elif target_dtype == 'float32' and audio.dtype != np.float32:
                audio = audio.astype(np.float32)
            
            return audio, sr
        
        except Exception as e:
            logger.warning(f"librosa failed: {e}, trying soundfile...")
    
    # Estrategia 2: Usar soundfile (más ligero, menos formatos)
    if SOUNDFILE_AVAILABLE:
        try:
            audio, sr = sf.read(str(audio_path), dtype='float32')
            
            logger.debug(
                f"Loaded with soundfile: {audio_path.name} "
                f"({sr}Hz, {audio.shape}, {audio.dtype})"
            )
            
            # Convertir estéreo a mono si es necesario
            if audio.ndim > 1 and target_channels == 1:
                audio = np.mean(audio, axis=1)
                logger.debug("Converted stereo to mono (average)")
            
            # Resample si es necesario
            if sr != target_sr:
                if not LIBROSA_AVAILABLE:
                    logger.warning(
                        f"Sample rate mismatch ({sr}Hz vs {target_sr}Hz) "
                        f"but librosa not available. Install: pip install librosa"
                    )
                else:
                    audio = librosa.resample(
                        audio,
                        orig_sr=sr,
                        target_sr=target_sr
                    )
                    sr = target_sr
                    logger.debug(f"Resampled to {target_sr}Hz")
            
            # Convertir tipo si es necesario
            if target_dtype == 'int16' and audio.dtype != np.int16:
                audio = (audio * 32767).astype(np.int16)
            elif target_dtype == 'float32' and audio.dtype != np.float32:
                audio = audio.astype(np.float32)
            
            return audio, sr
        
        except Exception as e:
            raise ValueError(
                f"Failed to load audio with soundfile: {e}. "
                f"Try installing librosa: pip install librosa"
            )
    
    # Sin dependencias disponibles
    raise ValueError(
        "No audio library available. Install one of:\n"
        "  pip install soundfile      (recommended, lightweight)\n"
        "  pip install librosa         (full-featured, heavier)"
    )


def convert_to_pcm16(audio: np.ndarray) -> bytes:
    """
    Convierte array numpy a bytes PCM 16-bit (para Vosk).
    
    Args:
        audio: Array numpy (float32 o int16)
    
    Returns:
        Bytes en formato PCM 16-bit
    
    Examples:
        >>> audio = np.array([0.1, 0.2, -0.1], dtype=np.float32)
        >>> pcm_bytes = convert_to_pcm16(audio)
        >>> assert len(pcm_bytes) == 3 * 2  # 3 samples * 2 bytes
    """
    if audio.dtype == np.float32 or audio.dtype == np.float64:
        # Convertir float [-1, 1] a int16 [-32768, 32767]
        audio = (audio * 32767).astype(np.int16)
    elif audio.dtype != np.int16:
        audio = audio.astype(np.int16)
    
    return audio.tobytes()


def normalize_audio(audio: np.ndarray, target_level: float = 0.7) -> np.ndarray:
    """
    Normaliza el volumen del audio a nivel objetivo.
    
    Args:
        audio: Array numpy de audio
        target_level: Nivel pico objetivo (0.0-1.0, default: 0.7)
    
    Returns:
        Audio normalizado
    
    Examples:
        >>> audio = np.array([0.1, 0.5, -0.3], dtype=np.float32)
        >>> normalized = normalize_audio(audio, target_level=0.8)
        >>> assert np.max(np.abs(normalized)) <= 0.8
    """
    if len(audio) == 0:
        return audio
    
    peak = np.max(np.abs(audio))
    
    if peak == 0:
        return audio
    
    # Calcular ganancia para alcanzar target_level
    gain = target_level / peak
    
    # Aplicar ganancia (limitar a target_level para evitar clipping)
    return np.clip(audio * gain, -target_level, target_level)


def detect_sample_rate(audio_path: Union[str, Path]) -> int:
    """
    Detecta la frecuencia de muestreo de un archivo de audio.
    
    Args:
        audio_path: Ruta al archivo de audio
    
    Returns:
        Frecuencia de muestreo en Hz
    
    Examples:
        >>> sr = detect_sample_rate("audio.wav")
        >>> print(f"Sample rate: {sr}Hz")
    """
    audio_path = Path(audio_path)
    
    if not audio_path.exists():
        raise ValueError(f"Audio file not found: {audio_path}")
    
    if SOUNDFILE_AVAILABLE:
        try:
            info = sf.info(str(audio_path))
            return info.samplerate
        except Exception as e:
            logger.warning(f"soundfile.info failed: {e}")
    
    if LIBROSA_AVAILABLE:
        try:
            _, sr = librosa.load(str(audio_path), sr=None, duration=0.1)
            return sr
        except Exception as e:
            logger.warning(f"librosa.load failed: {e}")
    
    raise ValueError("Cannot detect sample rate - no audio library available")


def is_audio_valid(
    audio: np.ndarray,
    sample_rate: int,
    min_duration_ms: int = 100,
    max_silence_ratio: float = 0.95
) -> bool:
    """
    Valida que el audio tenga contenido útil.
    
    Args:
        audio: Array numpy de audio
        sample_rate: Frecuencia de muestreo
        min_duration_ms: Duración mínima en milisegundos
        max_silence_ratio: Ratio máximo de silencio (0.0-1.0)
    
    Returns:
        True si el audio es válido, False si es demasiado corto o silencioso
    
    Examples:
        >>> audio = np.random.randn(16000).astype('float32')  # 1s @ 16kHz
        >>> assert is_audio_valid(audio, 16000, min_duration_ms=500)
    """
    # Verificar duración mínima
    min_samples = int(sample_rate * min_duration_ms / 1000)
    if len(audio) < min_samples:
        logger.warning(
            f"Audio too short: {len(audio)} samples "
            f"(need {min_samples} for {min_duration_ms}ms)"
        )
        return False
    
    # Verificar que no sea todo silencio
    threshold = 0.01  # Umbral de silencio
    silence_samples = np.sum(np.abs(audio) < threshold)
    silence_ratio = silence_samples / len(audio)
    
    if silence_ratio > max_silence_ratio:
        logger.warning(
            f"Audio mostly silent: {silence_ratio:.1%} "
            f"(max {max_silence_ratio:.1%})"
        )
        return False
    
    return True
