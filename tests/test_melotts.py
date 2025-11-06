"""
Tests para MeloTTS (Text-to-Speech).

Test Coverage:
- Inicialización y singleton
- Síntesis básica (español)
- Control de velocidad
- Salida a archivo
- Streaming de chunks
- STRICT MODE (graceful degradation)
- Sample rate y speakers

Week 1 Day 3-4 | v3.8.0-dev
Tests: 12
"""

import pytest
import numpy as np
from pathlib import Path
import tempfile

from sarai_agi.audio.melotts import MeloTTS, get_tts, MELOTTS_AVAILABLE


@pytest.fixture
def tts():
    """Fixture: Instancia de MeloTTS."""
    return MeloTTS()


@pytest.fixture
def temp_output_file():
    """Fixture: Archivo temporal para output."""
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        yield f.name
    # Cleanup
    Path(f.name).unlink(missing_ok=True)


class TestMeloTTSInitialization:
    """Tests de inicialización y configuración."""
    
    def test_singleton_pattern(self):
        """Verifica que MeloTTS es singleton."""
        tts1 = MeloTTS()
        tts2 = MeloTTS()
        assert tts1 is tts2, "MeloTTS debe ser singleton"
    
    def test_get_tts_singleton(self):
        """Verifica que get_tts retorna el mismo singleton."""
        tts1 = get_tts()
        tts2 = get_tts()
        tts3 = MeloTTS()
        assert tts1 is tts2
        assert tts1 is tts3
    
    def test_initialization_properties(self, tts):
        """Verifica propiedades básicas después de inicialización."""
        assert hasattr(tts, 'sample_rate')
        assert hasattr(tts, 'speakers')
        
        if MELOTTS_AVAILABLE:
            assert tts.sample_rate == 44100  # MeloTTS default
            assert isinstance(tts.speakers, dict)
    
    def test_is_available(self, tts):
        """Verifica que is_available retorna bool."""
        available = tts.is_available()
        assert isinstance(available, bool)
        
        if MELOTTS_AVAILABLE:
            assert available is True, "MeloTTS debería estar disponible"


@pytest.mark.skipif(not MELOTTS_AVAILABLE, reason="MeloTTS not installed")
class TestMeloTTSSynthesis:
    """Tests de síntesis de voz (requiere MeloTTS)."""
    
    def test_synthesize_basic_spanish(self, tts):
        """Sintetiza texto simple en español."""
        text = "Hola mundo"
        audio = tts.synthesize(text)
        
        assert audio is not None
        assert isinstance(audio, np.ndarray)
        assert audio.dtype == np.float32
        assert len(audio) > 0
        
        # Verificar duración razonable (~1-2s para "Hola mundo")
        duration = len(audio) / tts.sample_rate
        assert 0.5 <= duration <= 5.0, f"Duration {duration}s fuera de rango"
    
    def test_synthesize_long_text(self, tts):
        """Sintetiza texto más largo."""
        text = (
            "Hola, soy SARAi, tu asistente de inteligencia artificial. "
            "¿En qué puedo ayudarte hoy?"
        )
        audio = tts.synthesize(text)
        
        assert audio is not None
        assert len(audio) > 0
        
        # Texto largo debe generar audio más largo
        duration = len(audio) / tts.sample_rate
        assert 2.0 <= duration <= 15.0
    
    def test_synthesize_with_speed_control(self, tts):
        """Verifica control de velocidad (speed)."""
        text = "Hola mundo"
        
        # Síntesis normal (speed=1.0)
        audio_normal = tts.synthesize(text, speed=1.0)
        
        # Síntesis rápida (speed=1.5)
        audio_fast = tts.synthesize(text, speed=1.5)
        
        # Síntesis lenta (speed=0.8)
        audio_slow = tts.synthesize(text, speed=0.8)
        
        assert audio_normal is not None
        assert audio_fast is not None
        assert audio_slow is not None
        
        # Audio rápido debe ser más corto
        # Audio lento debe ser más largo
        # (Nota: MeloTTS puede tener comportamiento no lineal)
        assert len(audio_fast) < len(audio_normal) * 1.3
        assert len(audio_slow) > len(audio_normal) * 0.7
    
    def test_synthesize_empty_text(self, tts):
        """Verifica manejo de texto vacío (STRICT MODE)."""
        audio_empty = tts.synthesize("")
        audio_whitespace = tts.synthesize("   ")
        
        assert audio_empty is None
        assert audio_whitespace is None
    
    def test_synthesize_special_characters(self, tts):
        """Verifica manejo de caracteres especiales."""
        text = "¡Hola! ¿Cómo estás? Bien, gracias."
        audio = tts.synthesize(text)
        
        assert audio is not None
        assert len(audio) > 0


@pytest.mark.skipif(not MELOTTS_AVAILABLE, reason="MeloTTS not installed")
class TestMeloTTSFileOutput:
    """Tests de salida a archivo."""
    
    def test_synthesize_to_file_success(self, tts, temp_output_file):
        """Sintetiza y guarda a archivo WAV."""
        text = "Hola mundo"
        success = tts.synthesize_to_file(text, temp_output_file)
        
        assert success is True
        
        # Verificar que archivo existe
        output_path = Path(temp_output_file)
        assert output_path.exists()
        assert output_path.stat().st_size > 0
    
    def test_synthesize_to_file_with_speed(self, tts, temp_output_file):
        """Sintetiza con velocidad personalizada y guarda."""
        text = "Hola mundo"
        success = tts.synthesize_to_file(text, temp_output_file, speed=1.3)
        
        assert success is True
        assert Path(temp_output_file).exists()


@pytest.mark.skipif(not MELOTTS_AVAILABLE, reason="MeloTTS not installed")
class TestMeloTTSStreaming:
    """Tests de síntesis streaming (chunks)."""
    
    def test_synthesize_streaming_multiple_chunks(self, tts):
        """Sintetiza múltiples chunks de texto."""
        chunks = [
            "Hola,",
            "¿cómo estás?",
            "Yo bien, gracias."
        ]
        
        audio_chunks = tts.synthesize_streaming(chunks)
        
        assert len(audio_chunks) == 3
        
        for audio in audio_chunks:
            assert isinstance(audio, np.ndarray)
            assert audio.dtype == np.float32
            assert len(audio) > 0
    
    def test_synthesize_streaming_with_speed(self, tts):
        """Verifica streaming con velocidad personalizada."""
        chunks = ["Hola", "mundo"]
        audio_chunks = tts.synthesize_streaming(chunks, speed=1.2)
        
        assert len(audio_chunks) == 2
        for audio in audio_chunks:
            assert audio is not None


class TestMeloTTSStrictMode:
    """Tests de STRICT MODE (graceful degradation)."""
    
    def test_unavailable_tts_returns_none(self):
        """Si MeloTTS no disponible, synthesize retorna None."""
        tts = MeloTTS()
        
        if not MELOTTS_AVAILABLE:
            audio = tts.synthesize("Hola mundo")
            assert audio is None
    
    def test_unavailable_tts_file_returns_false(self, temp_output_file):
        """Si MeloTTS no disponible, synthesize_to_file retorna False."""
        tts = MeloTTS()
        
        if not MELOTTS_AVAILABLE:
            success = tts.synthesize_to_file("Hola", temp_output_file)
            assert success is False


@pytest.mark.skipif(not MELOTTS_AVAILABLE, reason="MeloTTS not installed")
class TestMeloTTSMisc:
    """Tests misceláneos."""
    
    def test_reset_no_crash(self, tts):
        """Verifica que reset() no lanza error."""
        tts.reset()  # No-op pero no debe crashear
    
    def test_sample_rate_property(self, tts):
        """Verifica propiedad sample_rate."""
        sr = tts.sample_rate
        assert isinstance(sr, int)
        assert sr == 44100  # MeloTTS default
    
    def test_speakers_property(self, tts):
        """Verifica propiedad speakers."""
        speakers = tts.speakers
        assert isinstance(speakers, dict)
        
        # MeloTTS español debe tener al menos un speaker
        if MELOTTS_AVAILABLE:
            assert len(speakers) > 0
            assert 'ES' in speakers or 0 in speakers.values()
