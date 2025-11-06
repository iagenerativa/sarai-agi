"""
Audio pipeline components for SARAi v3.8.0.

Este módulo implementa el sistema de audio full-duplex con:
- Vosk STT (Speech-to-Text)
- Sherpa-ONNX VAD (Voice Activity Detection integrado)
- MeloTTS (Text-to-Speech con expresividad)
- FillerSystem (frases de relleno para turn-taking)
- Audio utilities (preprocessing, conversion)

Version: 3.8.0
Week 1 Complete: STT + VAD + TTS + Fillers + Utils
"""

from .vosk_stt import VoskSTT
from .sherpa_vad import SherpaVAD
from .melotts import MeloTTS, get_tts
from .fillers import FillerSystem, get_filler_system
from .audio_utils import (
    preprocess_audio,
    convert_to_pcm16,
    normalize_audio,
    detect_sample_rate,
    is_audio_valid
)

__all__ = [
    # STT & VAD (Day 1-2)
    "VoskSTT",
    "SherpaVAD",
    
    # TTS (Day 3-4)
    "MeloTTS",
    "get_tts",
    
    # Fillers (Day 5)
    "FillerSystem",
    "get_filler_system",
    
    # Utilities
    "preprocess_audio",
    "convert_to_pcm16",
    "normalize_audio",
    "detect_sample_rate",
    "is_audio_valid"
]
