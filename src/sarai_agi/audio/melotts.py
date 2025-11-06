"""
Text-to-Speech usando MeloTTS (Multi-lingual High-Quality TTS).

MeloTTS (MyShell.ai + MIT):
- Idiomas: Español, Inglés (4 acentos), Francés, Chino, Japonés, Coreano
- Calidad: Alta (MOS >4.0 estimado)
- Latencia: CPU real-time (~200-300ms para frases cortas)
- RAM: ~200-400MB (modelo español)
- Licencia: MIT (comercial OK)

Características:
- Síntesis en español nativo
- Control de velocidad (speed 0.5-2.0)
- CPU-only inference (sin GPU necesaria)
- Streaming-ready (chunks de texto)

Referencias:
- GitHub: https://github.com/myshell-ai/MeloTTS
- Paper: Zhao, Wenliang et al. "MeloTTS: High-quality Multi-lingual Multi-accent Text-to-Speech" (2023)
- HuggingFace: https://huggingface.co/myshell-ai

Week 1 Day 3-4 | v3.8.0-dev
LOC: 250
"""

import logging
from pathlib import Path
from typing import Optional, Union, List
import numpy as np
import sys

logger = logging.getLogger(__name__)

# Agregar MeloTTS al path si existe
_melo_path = Path(__file__).parent.parent.parent.parent / "models" / "MeloTTS"
if _melo_path.exists() and str(_melo_path) not in sys.path:
    sys.path.insert(0, str(_melo_path))

try:
    from melo.api import TTS as MeloTTSModel
    import torch
    MELOTTS_AVAILABLE = True
except ImportError:
    MELOTTS_AVAILABLE = False
    logger.warning("MeloTTS not available - TTS functionality disabled")

try:
    import soundfile as sf
    SOUNDFILE_AVAILABLE = True
except ImportError:
    SOUNDFILE_AVAILABLE = False
    logger.warning("soundfile not available - cannot save TTS output")



class MeloTTS:
    """
    Text-to-Speech usando MeloTTS (español nativo).
    
    Features:
    - Síntesis en español de alta calidad
    - Control de velocidad (0.5x - 2.0x)
    - CPU real-time inference
    - Streaming chunks de texto
    - STRICT MODE: Graceful degradation
    
    Usage:
        >>> tts = MeloTTS()
        >>> audio = tts.synthesize("Hola mundo", speed=1.0)
        >>> # audio: numpy array float32 @ 44100Hz
        
        >>> # Guardar a archivo
        >>> tts.synthesize_to_file("Hola mundo", "output.wav")
        
        >>> # Streaming (múltiples chunks)
        >>> chunks = ["Hola,", "¿cómo estás?", "Yo bien, gracias."]
        >>> for chunk in chunks:
        ...     audio = tts.synthesize(chunk)
        ...     # Reproducir audio inmediatamente
    
    RAM: ~200-400MB (modelo español)
    Latency: ~200-300ms (frases cortas en CPU)
    Sample Rate: 44100Hz (default MeloTTS)
    """
    
    _instance: Optional['MeloTTS'] = None
    _model: Optional[object] = None
    _language: str = 'ES'
    _sample_rate: int = 44100  # MeloTTS default
    _available: bool = False
    
    def __new__(cls):
        """Singleton pattern: Una única instancia compartida."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(
        self,
        language: str = 'ES',
        device: str = 'cpu',
        speed: float = 1.2,  # Acelerado por defecto para más naturalidad
        sdp_ratio: float = 0.2,  # Stochastic Duration Predictor (variabilidad prosódica)
        noise_scale: float = 0.6,  # Expresividad de pitch/tono
        noise_scale_w: float = 0.8  # Expresividad de duración
    ):
        """
        Inicializa MeloTTS para síntesis de voz.
        
        Args:
            language: Código de idioma ('ES', 'EN', 'FR', 'ZH', 'JP', 'KR')
            device: Dispositivo de inferencia ('cpu', 'cuda', 'auto')
            speed: Velocidad de habla por defecto (0.5-2.0)
                   1.2 = 20% más rápido (recomendado para español)
            sdp_ratio: Ratio de variabilidad prosódica (0.0-1.0)
                       ↑ = más natural/variable, ↓ = más monótono
            noise_scale: Escala de variación de pitch/tono (0.0-1.0)
                         ↑ = más expresivo, ↓ = más plano
            noise_scale_w: Escala de variación de duración (0.0-1.0)
                           ↑ = más dinámico, ↓ = más uniforme
        
        Raises:
            None - STRICT MODE: Falla silenciosamente si no hay dependencias
        """
        # Singleton: Solo inicializar una vez
        if self._model is not None:
            return
        
        if not MELOTTS_AVAILABLE:
            logger.error("Cannot initialize MeloTTS: melo package not installed")
            logger.info("Install: cd models && git clone https://github.com/myshell-ai/MeloTTS.git && cd MeloTTS && pip install -e .")
            self._available = False
            return
        
        try:
            logger.info(f"Initializing MeloTTS (language={language}, device={device})...")
            
            # Inicializar modelo
            self._model = MeloTTSModel(language=language, device=device)
            self._language = language
            self._sample_rate = 44100  # MeloTTS default
            self._default_speed = speed
            self._default_sdp_ratio = sdp_ratio
            self._default_noise_scale = noise_scale
            self._default_noise_scale_w = noise_scale_w
            self._available = True
            
            # Obtener speaker IDs disponibles
            self._speaker_ids = self._model.hps.data.spk2id
            logger.info(
                f"MeloTTS initialized: language={language}, "
                f"speakers={list(self._speaker_ids.keys())}, "
                f"sample_rate={self._sample_rate}Hz, "
                f"speed={speed:.1f}x, expressiveness=(sdp={sdp_ratio}, "
                f"noise={noise_scale}, noise_w={noise_scale_w})"
            )
        
        except Exception as e:
            logger.error(f"Failed to initialize MeloTTS: {e}")
            self._available = False
    
    def synthesize(
        self,
        text: str,
        speed: Optional[float] = None,
        speaker: Optional[str] = None,
        sdp_ratio: Optional[float] = None,
        noise_scale: Optional[float] = None,
        noise_scale_w: Optional[float] = None
    ) -> Optional[np.ndarray]:
        """
        Sintetiza texto a audio (en memoria).
        
        Args:
            text: Texto a sintetizar (español)
            speed: Velocidad de habla (0.5-2.0, default: 1.2x)
            speaker: ID del speaker (default: primer speaker del idioma)
            sdp_ratio: Variabilidad prosódica (0.0-1.0, default: 0.2)
            noise_scale: Expresividad de pitch (0.0-1.0, default: 0.6)
            noise_scale_w: Expresividad de duración (0.0-1.0, default: 0.8)
        
        Returns:
            Audio como numpy array float32, o None si error
        
        Examples:
            >>> tts = MeloTTS()
            >>> # Síntesis normal (expresiva y acelerada)
            >>> audio = tts.synthesize("Hola mundo")
            >>> 
            >>> # Síntesis muy expresiva
            >>> audio = tts.synthesize(
            ...     "¡Hola! ¿Cómo estás?",
            ...     speed=1.3,
            ...     noise_scale=0.8,  # Más variación de tono
            ...     noise_scale_w=0.9  # Más variación de ritmo
            ... )
            >>> 
            >>> # Síntesis monótona (robot-like)
            >>> audio = tts.synthesize(
            ...     "Información técnica",
            ...     noise_scale=0.2,  # Menos expresividad
            ...     noise_scale_w=0.3
            ... )
        """
        if not self._available or self._model is None:
            logger.warning("MeloTTS not available - returning None")
            return None
        
        if not text or len(text.strip()) == 0:
            logger.warning("Empty text provided - returning None")
            return None
        
        try:
            # Usar parámetros especificados o defaults
            speed = speed if speed is not None else self._default_speed
            sdp_ratio = sdp_ratio if sdp_ratio is not None else self._default_sdp_ratio
            noise_scale = noise_scale if noise_scale is not None else self._default_noise_scale
            noise_scale_w = noise_scale_w if noise_scale_w is not None else self._default_noise_scale_w
            
            # Usar speaker especificado o default (primer speaker)
            if speaker is None:
                speaker_id = list(self._speaker_ids.values())[0]
            elif isinstance(speaker, str):
                # self._speaker_ids es un dict {'ES': 0, ...}
                speaker_id = self._speaker_ids[speaker] if speaker in self._speaker_ids else list(self._speaker_ids.values())[0]
            else:
                speaker_id = speaker  # Ya es un ID numérico
            
            # Generar audio con parámetros de expresividad
            # MeloTTS requiere un archivo de salida, usamos temporal
            import tempfile
            import os
            import soundfile as sf
            
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                output_path_tmp = f.name
            
            try:
                # Generar audio a archivo temporal
                self._model.tts_to_file(
                    text,
                    speaker_id,
                    output_path_tmp,
                    speed=speed,
                    sdp_ratio=sdp_ratio,
                    noise_scale=noise_scale,
                    noise_scale_w=noise_scale_w,
                    quiet=True
                )
                
                # Leer audio del archivo
                audio, sr = sf.read(output_path_tmp)
                
                # Convertir a mono si es stereo
                if len(audio.shape) > 1:
                    audio = audio.mean(axis=1)
                
                if len(audio) == 0:
                    logger.warning(f"No audio generated for text: {text[:50]}...")
                    return None
                
            finally:
                # Limpiar archivo temporal
                if os.path.exists(output_path_tmp):
                    os.unlink(output_path_tmp)
            
            logger.debug(
                f"Synthesized {len(text)} chars → {len(audio)} samples "
                f"({len(audio)/self._sample_rate:.2f}s) "
                f"[speed={speed:.1f}x, expr=(sdp={sdp_ratio:.1f}, "
                f"noise={noise_scale:.1f}, noise_w={noise_scale_w:.1f})]"
            )
            
            return audio.astype(np.float32)
        
        except Exception as e:
            logger.error(f"Error in TTS synthesis: {e}")
            return None
    
    def synthesize_to_file(
        self,
        text: str,
        output_path: Union[str, Path],
        speed: Optional[float] = None,
        speaker: Optional[str] = None,
        sdp_ratio: Optional[float] = None,
        noise_scale: Optional[float] = None,
        noise_scale_w: Optional[float] = None
    ) -> bool:
        """
        Sintetiza texto y guarda directamente a archivo.
        
        Args:
            text: Texto a sintetizar
            output_path: Ruta del archivo de salida (.wav)
            speed: Velocidad de habla
            speaker: ID del speaker
            sdp_ratio: Variabilidad prosódica
            noise_scale: Expresividad de pitch
            noise_scale_w: Expresividad de duración
        
        Returns:
            True si éxito, False si error
        
        Examples:
            >>> tts = MeloTTS()
            >>> # Síntesis expresiva
            >>> success = tts.synthesize_to_file(
            ...     "¡Hola! ¿Cómo estás?",
            ...     "output.wav",
            ...     speed=1.3,
            ...     noise_scale=0.8
            ... )
        """
        if not self._available or self._model is None:
            logger.warning("MeloTTS not available - cannot synthesize")
            return False
        
        try:
            # Usar parámetros especificados o defaults
            speed = speed if speed is not None else self._default_speed
            sdp_ratio = sdp_ratio if sdp_ratio is not None else self._default_sdp_ratio
            noise_scale = noise_scale if noise_scale is not None else self._default_noise_scale
            noise_scale_w = noise_scale_w if noise_scale_w is not None else self._default_noise_scale_w
            
            # Usar speaker especificado o default
            if speaker is None:
                speaker = list(self._speaker_ids.values())[0]
            elif isinstance(speaker, str):
                speaker = self._speaker_ids.get(speaker, list(self._speaker_ids.values())[0])
            
            # Generar y guardar
            self._model.tts_to_file(
                text,
                speaker,
                str(output_path),
                speed=speed,
                sdp_ratio=sdp_ratio,
                noise_scale=noise_scale,
                noise_scale_w=noise_scale_w,
                quiet=True
            )
            
            logger.info(
                f"Synthesized to file: {output_path} "
                f"[speed={speed:.1f}x, expr=(sdp={sdp_ratio:.1f}, "
                f"noise={noise_scale:.1f}, noise_w={noise_scale_w:.1f})]"
            )
            return True
        
        except Exception as e:
            logger.error(f"Error saving TTS to file: {e}")
            return False
    
    def synthesize_streaming(
        self,
        text_chunks: List[str],
        speed: Optional[float] = None
    ) -> List[np.ndarray]:
        """
        Sintetiza múltiples chunks de texto (para streaming).
        
        Args:
            text_chunks: Lista de chunks de texto
            speed: Velocidad de habla
        
        Returns:
            Lista de arrays de audio (uno por chunk)
        
        Examples:
            >>> tts = MeloTTS()
            >>> chunks = ["Hola,", "¿cómo estás?", "Yo bien."]
            >>> audio_chunks = tts.synthesize_streaming(chunks)
            >>> for audio in audio_chunks:
            ...     # Reproducir cada chunk inmediatamente
            ...     play_audio(audio)
        """
        audio_chunks = []
        
        for chunk in text_chunks:
            audio = self.synthesize(chunk, speed=speed)
            if audio is not None:
                audio_chunks.append(audio)
        
        return audio_chunks
    
    def reset(self):
        """
        Reset del modelo (libera memoria si es necesario).
        
        Nota: MeloTTS no necesita reset explícito entre síntesis.
        """
        logger.debug("MeloTTS reset (no-op)")
    
    def is_available(self) -> bool:
        """
        Verifica si TTS está disponible y funcional.
        
        Returns:
            True si TTS está listo, False si falta modelo/deps
        """
        return self._available and self._model is not None
    
    def get_sample_rate(self) -> int:
        """
        Obtiene la frecuencia de muestreo del audio generado.
        
        Returns:
            Sample rate en Hz (default 44100)
        """
        return self._sample_rate
    
    @property
    def sample_rate(self) -> int:
        """Frecuencia de muestreo del audio generado."""
        return self._sample_rate
    
    @property
    def speakers(self) -> dict:
        """Diccionario de speakers disponibles."""
        if self._model is not None:
            return self._speaker_ids
        return {}


# Singleton global instance
_tts_instance: Optional[MeloTTS] = None


def get_tts() -> MeloTTS:
    """
    Obtiene la instancia singleton de MeloTTS.
    
    Returns:
        MeloTTS instance (siempre la misma)
    
    Examples:
        >>> tts = get_tts()
        >>> tts2 = get_tts()
        >>> assert tts is tts2  # Mismo objeto
    """
    global _tts_instance
    if _tts_instance is None:
        _tts_instance = MeloTTS()
    return _tts_instance
