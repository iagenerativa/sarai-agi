"""
Tests for Vosk Speech-to-Text (STT) implementation.

STRICT MODE: Sin mocks, solo tests reales con archivos de audio.

Test coverage:
- Model loading (existente y faltante)
- File transcription (WAV, mono, 16kHz)
- Streaming transcription (chunks)
- Partial results
- Confidence calculation
- Graceful degradation (sin modelo, archivo inválido)

Version: 3.8.0
"""

import pytest
from pathlib import Path
import wave
import struct
import tempfile

from src.sarai_agi.audio.vosk_stt import VoskSTT, get_vosk_stt


# Configuración
MODEL_PATH = Path(__file__).parent.parent / "models" / "audio" / "vosk-model-small-es-0.42"
SAMPLE_RATE = 16000


def create_test_wav(duration_sec: float = 1.0, frequency: int = 440) -> Path:
    """
    Crea archivo WAV de prueba (tono puro).
    
    Args:
        duration_sec: Duración en segundos
        frequency: Frecuencia del tono (Hz)
    
    Returns:
        Path: Path al archivo temporal creado
    """
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    temp_path = Path(temp_file.name)
    
    with wave.open(str(temp_path), "wb") as wf:
        wf.setnchannels(1)  # Mono
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(SAMPLE_RATE)
        
        # Generate sine wave
        num_samples = int(SAMPLE_RATE * duration_sec)
        for i in range(num_samples):
            value = int(32767 * 0.3 * (i % (SAMPLE_RATE // frequency)) / (SAMPLE_RATE // frequency))
            wf.writeframes(struct.pack('<h', value))
    
    return temp_path


class TestVoskSTTInitialization:
    """Tests para inicialización de VoskSTT."""
    
    def test_init_with_existing_model(self):
        """Test: Inicialización con modelo existente."""
        if not MODEL_PATH.exists():
            pytest.skip(f"Vosk model not found at {MODEL_PATH}")
        
        stt = VoskSTT(model_path=MODEL_PATH)
        assert stt.is_available(), "STT should be available with valid model"
        assert stt.model is not None, "Model should be loaded"
    
    def test_init_with_missing_model(self):
        """Test: Inicialización con modelo faltante (graceful degradation)."""
        stt = VoskSTT(model_path="/nonexistent/path/to/model")
        assert not stt.is_available(), "STT should not be available with missing model"
        assert stt.model is None, "Model should be None"
    
    def test_init_with_default_model_path(self):
        """Test: Inicialización con path por defecto."""
        stt = VoskSTT()  # Usa default path
        # No crash, incluso si modelo no existe
        assert stt is not None
    
    def test_singleton_pattern(self):
        """Test: Patrón singleton para instancia global."""
        if not MODEL_PATH.exists():
            pytest.skip(f"Vosk model not found at {MODEL_PATH}")
        
        stt1 = get_vosk_stt(MODEL_PATH)
        stt2 = get_vosk_stt(MODEL_PATH)
        assert stt1 is stt2, "Should return same instance (singleton)"


class TestVoskSTTFileTranscription:
    """Tests para transcripción de archivos."""
    
    def test_transcribe_existing_wav_file(self):
        """Test: Transcribir archivo WAV válido."""
        if not MODEL_PATH.exists():
            pytest.skip(f"Vosk model not found at {MODEL_PATH}")
        
        stt = VoskSTT(model_path=MODEL_PATH)
        if not stt.is_available():
            pytest.skip("Vosk STT not available")
        
        # Create test audio (silent, will return empty or noise)
        test_wav = create_test_wav(duration_sec=0.5)
        
        try:
            result = stt.transcribe_file(test_wav)
            
            # Graceful degradation: siempre retorna dict
            assert isinstance(result, dict), "Should return dict"
            assert "text" in result or result == {}, "Should have 'text' key or be empty"
            
            # Confidence opcional (puede no existir si texto vacío)
            if result:
                assert "confidence" in result, "Should have 'confidence' if text exists"
                assert 0.0 <= result["confidence"] <= 1.0, "Confidence should be 0-1"
        
        finally:
            test_wav.unlink()  # Cleanup
    
    def test_transcribe_missing_file(self):
        """Test: Transcribir archivo inexistente (graceful degradation)."""
        if not MODEL_PATH.exists():
            pytest.skip(f"Vosk model not found at {MODEL_PATH}")
        
        stt = VoskSTT(model_path=MODEL_PATH)
        if not stt.is_available():
            pytest.skip("Vosk STT not available")
        
        result = stt.transcribe_file("/nonexistent/audio.wav")
        assert result == {}, "Should return empty dict for missing file"
    
    def test_transcribe_without_model(self):
        """Test: Transcribir sin modelo cargado (graceful degradation)."""
        stt = VoskSTT(model_path="/nonexistent/model")
        
        test_wav = create_test_wav()
        try:
            result = stt.transcribe_file(test_wav)
            assert result == {}, "Should return empty dict without model"
        finally:
            test_wav.unlink()


class TestVoskSTTStreamingTranscription:
    """Tests para transcripción en streaming."""
    
    def test_transcribe_chunk_partial(self):
        """Test: Transcribir chunk con resultado parcial."""
        if not MODEL_PATH.exists():
            pytest.skip(f"Vosk model not found at {MODEL_PATH}")
        
        stt = VoskSTT(model_path=MODEL_PATH)
        if not stt.is_available():
            pytest.skip("Vosk STT not available")
        
        # Create small audio chunk (100ms)
        test_wav = create_test_wav(duration_sec=0.1)
        
        try:
            # Read audio as bytes
            with wave.open(str(test_wav), "rb") as wf:
                audio_bytes = wf.readframes(wf.getnframes())
            
            # Process chunk (not final)
            result = stt.transcribe_chunk(audio_bytes, is_final=False)
            
            # Should return partial or empty
            assert isinstance(result, dict), "Should return dict"
            # Can have "partial" or be empty (if no speech)
        
        finally:
            test_wav.unlink()
    
    def test_transcribe_chunk_final(self):
        """Test: Transcribir chunk con resultado final."""
        if not MODEL_PATH.exists():
            pytest.skip(f"Vosk model not found at {MODEL_PATH}")
        
        stt = VoskSTT(model_path=MODEL_PATH)
        if not stt.is_available():
            pytest.skip("Vosk STT not available")
        
        test_wav = create_test_wav(duration_sec=0.1)
        
        try:
            with wave.open(str(test_wav), "rb") as wf:
                audio_bytes = wf.readframes(wf.getnframes())
            
            # Process chunk (final)
            result = stt.transcribe_chunk(audio_bytes, is_final=True)
            
            assert isinstance(result, dict), "Should return dict"
            # Final result should have "text" (puede ser vacío)
            if result:
                assert "text" in result, "Final result should have 'text'"
        
        finally:
            test_wav.unlink()
    
    def test_streaming_reset(self):
        """Test: Reset de recognizer para nueva transcripción."""
        if not MODEL_PATH.exists():
            pytest.skip(f"Vosk model not found at {MODEL_PATH}")
        
        stt = VoskSTT(model_path=MODEL_PATH)
        if not stt.is_available():
            pytest.skip("Vosk STT not available")
        
        # Process some audio
        test_wav = create_test_wav(duration_sec=0.1)
        try:
            with wave.open(str(test_wav), "rb") as wf:
                audio_bytes = wf.readframes(wf.getnframes())
            
            stt.transcribe_chunk(audio_bytes)
            
            # Reset
            stt.reset()
            assert stt.recognizer is None, "Recognizer should be None after reset"
        
        finally:
            test_wav.unlink()


class TestVoskSTTStrictMode:
    """Tests para STRICT MODE (sin excepciones)."""
    
    def test_empty_audio_chunk(self):
        """Test: Chunk vacío retorna dict sin crash."""
        if not MODEL_PATH.exists():
            pytest.skip(f"Vosk model not found at {MODEL_PATH}")
        
        stt = VoskSTT(model_path=MODEL_PATH)
        if not stt.is_available():
            pytest.skip("Vosk STT not available")
        
        result = stt.transcribe_chunk(b"")
        # Acepta {} o {"partial": ""} (ambos válidos para chunk vacío)
        assert isinstance(result, dict), "Should return dict"
        assert result in [{}, {"partial": ""}], "Empty chunk should return empty or partial=''"
    
    def test_invalid_audio_data(self):
        """Test: Audio inválido retorna {} sin crash."""
        if not MODEL_PATH.exists():
            pytest.skip(f"Vosk model not found at {MODEL_PATH}")
        
        stt = VoskSTT(model_path=MODEL_PATH)
        if not stt.is_available():
            pytest.skip("Vosk STT not available")
        
        # Random bytes (no valid audio)
        result = stt.transcribe_chunk(b"random_garbage_data_not_audio")
        
        # Should not crash, graceful degradation
        assert isinstance(result, dict), "Should return dict even with invalid data"


# Fixture para cleanup
@pytest.fixture(autouse=True)
def cleanup_temp_files():
    """Auto-cleanup de archivos temporales."""
    yield
    # Cleanup handled by individual tests using try/finally
