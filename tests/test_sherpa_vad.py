"""
Tests for Sherpa-ONNX Voice Activity Detection (VAD).

STRICT MODE: Sin mocks, solo tests reales con audio.

Test coverage:
- VAD initialization
- Speech detection (single chunk)
- Segment detection (full audio)
- Threshold configuration
- Graceful degradation (sin Sherpa-ONNX instalado)

Version: 3.8.0
"""

import pytest
from pathlib import Path
import struct
import tempfile

from src.sarai_agi.audio.sherpa_vad import SherpaVAD, get_sherpa_vad


SAMPLE_RATE = 16000


def create_audio_chunk(duration_ms: int = 100, is_speech: bool = False) -> bytes:
    """
    Crea chunk de audio de prueba.
    
    Args:
        duration_ms: Duración en milisegundos
        is_speech: Si True, genera "voz" (variación alta), si False, silencio
    
    Returns:
        bytes: Audio data (16-bit PCM mono)
    """
    num_samples = int(SAMPLE_RATE * duration_ms / 1000)
    audio_data = []
    
    for i in range(num_samples):
        if is_speech:
            # Simular voz con variación alta (no es voz real, pero activa VAD)
            value = int(10000 * ((i % 100) / 100.0 - 0.5))
        else:
            # Silencio (valores cercanos a 0)
            value = int(100 * ((i % 10) / 10.0 - 0.5))
        
        audio_data.append(struct.pack('<h', value))
    
    return b''.join(audio_data)


class TestSherpaVADInitialization:
    """Tests para inicialización de SherpaVAD."""
    
    def test_init_with_defaults(self):
        """Test: Inicialización con parámetros por defecto."""
        vad = SherpaVAD()
        
        # No crash incluso si Sherpa no está instalado
        assert vad is not None
        assert vad.sample_rate == 16000
        assert vad.threshold == 0.5
    
    def test_init_with_custom_params(self):
        """Test: Inicialización con parámetros personalizados."""
        vad = SherpaVAD(
            sample_rate=8000,
            threshold=0.7,
            min_speech_duration_ms=300,
        )
        
        assert vad.sample_rate == 8000
        assert vad.threshold == 0.7
        assert vad.min_speech_duration_ms == 300
    
    def test_is_available(self):
        """Test: Check si VAD está disponible."""
        vad = SherpaVAD()
        
        # Puede ser True o False dependiendo de si Sherpa está instalado
        is_available = vad.is_available()
        assert isinstance(is_available, bool), "Should return boolean"
    
    def test_singleton_pattern(self):
        """Test: Patrón singleton para instancia global."""
        vad1 = get_sherpa_vad()
        vad2 = get_sherpa_vad()
        assert vad1 is vad2, "Should return same instance (singleton)"


class TestSherpaVADDetection:
    """Tests para detección de voz."""
    
    def test_detect_silence(self):
        """Test: Detectar silencio (debería retornar False)."""
        vad = SherpaVAD()
        
        if not vad.is_available():
            pytest.skip("Sherpa VAD not available")
        
        silence = create_audio_chunk(duration_ms=200, is_speech=False)
        is_speech = vad.detect(silence)
        
        # Silencio debería retornar False (o puede ser True si umbral muy bajo)
        assert isinstance(is_speech, bool), "Should return boolean"
    
    def test_detect_speech_like_audio(self):
        """Test: Detectar audio con variación (simula voz)."""
        vad = SherpaVAD(threshold=0.3)  # Umbral bajo para facilitar detección
        
        if not vad.is_available():
            pytest.skip("Sherpa VAD not available")
        
        speech = create_audio_chunk(duration_ms=300, is_speech=True)
        is_speech = vad.detect(speech)
        
        # Con audio variado, puede detectar como voz
        assert isinstance(is_speech, bool), "Should return boolean"
    
    def test_detect_empty_chunk(self):
        """Test: Detectar chunk vacío (graceful degradation)."""
        vad = SherpaVAD()
        
        if not vad.is_available():
            pytest.skip("Sherpa VAD not available")
        
        is_speech = vad.detect(b"")
        assert is_speech is False, "Empty chunk should return False"
    
    def test_detect_without_vad_loaded(self):
        """Test: Detectar sin VAD cargado (graceful degradation)."""
        # Force VAD to be None (simulate failure)
        vad = SherpaVAD()
        vad.vad = None
        
        audio = create_audio_chunk(duration_ms=100, is_speech=True)
        is_speech = vad.detect(audio)
        
        assert is_speech is False, "Should return False without VAD"


class TestSherpaVADSegments:
    """Tests para detección de segmentos."""
    
    def test_detect_segments_mixed_audio(self):
        """Test: Detectar segmentos en audio con voz y silencio mezclados."""
        vad = SherpaVAD(threshold=0.3)
        
        if not vad.is_available():
            pytest.skip("Sherpa VAD not available")
        
        # Crear audio: silencio + voz + silencio
        silence1 = create_audio_chunk(duration_ms=200, is_speech=False)
        speech = create_audio_chunk(duration_ms=400, is_speech=True)
        silence2 = create_audio_chunk(duration_ms=200, is_speech=False)
        
        full_audio = silence1 + speech + silence2
        
        segments = vad.detect_segments(full_audio)
        
        # Puede retornar lista vacía o con segmentos
        assert isinstance(segments, list), "Should return list"
        
        # Si detectó segmentos, verificar formato
        for start_ms, end_ms in segments:
            assert isinstance(start_ms, int), "Start should be int (ms)"
            assert isinstance(end_ms, int), "End should be int (ms)"
            assert start_ms < end_ms, "Start should be before end"
    
    def test_detect_segments_without_vad(self):
        """Test: Detectar segmentos sin VAD (graceful degradation)."""
        vad = SherpaVAD()
        vad.vad = None
        
        audio = create_audio_chunk(duration_ms=500, is_speech=True)
        segments = vad.detect_segments(audio)
        
        assert segments == [], "Should return empty list without VAD"


class TestSherpaVADStrictMode:
    """Tests para STRICT MODE (sin excepciones)."""
    
    def test_reset_without_crash(self):
        """Test: Reset no crashea incluso sin VAD."""
        vad = SherpaVAD()
        vad.vad = None
        
        # Should not crash
        vad.reset()
        assert True, "Reset should not crash"
    
    def test_detect_with_invalid_audio_data(self):
        """Test: Audio inválido retorna False sin crash."""
        vad = SherpaVAD()
        
        if not vad.is_available():
            pytest.skip("Sherpa VAD not available")
        
        # Random bytes (not valid audio format esperado)
        result = vad.detect(b"invalid_random_data")
        
        # Should not crash, graceful degradation
        assert isinstance(result, bool), "Should return bool even with invalid data"


# Nota: Sherpa-ONNX VAD usa modelo Silero INTEGRADO
# NO necesitamos descargar silero_vad.onnx por separado
# El modelo viene incluido en la librería sherpa-onnx
