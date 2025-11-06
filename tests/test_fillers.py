"""
Tests para FillerSystem (frases de relleno).

Test Coverage:
- Inicialización y cache
- Generación de fillers
- Categorías (thinking, waiting, confirming, generic)
- Variación (evitar repetición)
- Cache management
- STRICT MODE

Week 1 Day 5 | v3.8.0-dev
Tests: 10
"""

import pytest
import numpy as np
from pathlib import Path
import tempfile
import shutil

from sarai_agi.audio.fillers import FillerSystem, get_filler_system, MELOTTS_AVAILABLE


@pytest.fixture
def temp_cache_dir():
    """Fixture: Directorio temporal para cache."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def filler_system(temp_cache_dir):
    """Fixture: FillerSystem con cache temporal."""
    return FillerSystem(
        cache_dir=temp_cache_dir,
        auto_generate=False  # No generar automáticamente en tests
    )


class TestFillerSystemInitialization:
    """Tests de inicialización."""
    
    def test_initialization_basic(self, temp_cache_dir):
        """Verifica inicialización básica."""
        fillers = FillerSystem(cache_dir=temp_cache_dir, auto_generate=False)
        
        assert fillers is not None
        assert fillers._cache_dir == temp_cache_dir
        assert temp_cache_dir.exists()
    
    def test_filler_categories_defined(self, filler_system):
        """Verifica que todas las categorías están definidas."""
        assert 'thinking' in FillerSystem.FILLERS
        assert 'waiting' in FillerSystem.FILLERS
        assert 'confirming' in FillerSystem.FILLERS
        assert 'generic' in FillerSystem.FILLERS
        
        # Verificar que hay fillers en cada categoría
        for category, fillers in FillerSystem.FILLERS.items():
            assert len(fillers) > 0, f"Category {category} is empty"
    
    def test_get_filler_system_singleton(self):
        """Verifica que get_filler_system retorna singleton."""
        fs1 = get_filler_system()
        fs2 = get_filler_system()
        assert fs1 is fs2
    
    def test_is_available(self, filler_system):
        """Verifica método is_available."""
        available = filler_system.is_available()
        assert isinstance(available, bool)
        
        if MELOTTS_AVAILABLE:
            assert available is True


@pytest.mark.skipif(not MELOTTS_AVAILABLE, reason="MeloTTS not installed")
class TestFillerGeneration:
    """Tests de generación de fillers (requiere MeloTTS)."""
    
    def test_generate_single_filler(self, temp_cache_dir):
        """Genera un único filler y verifica cache."""
        fillers = FillerSystem(cache_dir=temp_cache_dir, auto_generate=False)
        
        # Generar thinking filler
        audio = fillers.get_thinking_filler()
        
        assert audio is not None
        assert isinstance(audio, np.ndarray)
        assert audio.dtype == np.float32
        assert len(audio) > 0
        
        # Verificar que se guardó en cache en disco
        cache_files = list(temp_cache_dir.glob("*.npy"))
        assert len(cache_files) >= 1
    
    def test_cache_reuse(self, temp_cache_dir):
        """Verifica que se reutiliza cache en disco."""
        fillers = FillerSystem(cache_dir=temp_cache_dir, auto_generate=False)
        
        # Primera carga (genera)
        audio1 = fillers.get_waiting_filler()
        cache_files_before = list(temp_cache_dir.glob("*.npy"))
        
        # Limpiar cache en memoria
        fillers.clear_cache()
        
        # Segunda carga (debe usar cache en disco)
        audio2 = fillers.get_waiting_filler()
        cache_files_after = list(temp_cache_dir.glob("*.npy"))
        
        # Mismo número de archivos (no generó nuevo)
        assert len(cache_files_after) == len(cache_files_before)
        
        # Audio debe ser similar
        assert audio1 is not None
        assert audio2 is not None
        assert len(audio1) == len(audio2)


@pytest.mark.skipif(not MELOTTS_AVAILABLE, reason="MeloTTS not installed")
class TestFillerCategories:
    """Tests de categorías de fillers."""
    
    def test_thinking_filler(self, filler_system):
        """Obtiene filler de pensamiento."""
        audio = filler_system.get_thinking_filler()
        
        if audio is not None:
            assert isinstance(audio, np.ndarray)
            assert len(audio) > 0
    
    def test_waiting_filler(self, filler_system):
        """Obtiene filler de espera."""
        audio = filler_system.get_waiting_filler()
        
        if audio is not None:
            assert isinstance(audio, np.ndarray)
            assert len(audio) > 0
    
    def test_confirming_filler(self, filler_system):
        """Obtiene filler de confirmación."""
        audio = filler_system.get_confirming_filler()
        
        if audio is not None:
            assert isinstance(audio, np.ndarray)
            assert len(audio) > 0
    
    def test_random_filler(self, filler_system):
        """Obtiene filler aleatorio."""
        audio = filler_system.get_random_filler()
        
        if audio is not None:
            assert isinstance(audio, np.ndarray)
            assert len(audio) > 0


@pytest.mark.skipif(not MELOTTS_AVAILABLE, reason="MeloTTS not installed")
class TestFillerVariation:
    """Tests de variación (evitar repetición)."""
    
    def test_avoid_repetition(self, filler_system):
        """Verifica que evita repetir el mismo filler consecutivamente."""
        # Obtener varios fillers de la misma categoría
        fillers = []
        for _ in range(5):
            audio = filler_system.get_thinking_filler()
            if audio is not None:
                fillers.append(audio)
        
        # Si hay múltiples fillers en la categoría, no deberían ser todos iguales
        if len(FillerSystem.FILLERS['thinking']) > 1 and len(fillers) >= 2:
            # Al menos uno debería ser diferente en longitud
            lengths = [len(f) for f in fillers]
            assert len(set(lengths)) > 1, "All fillers have same length (likely repeated)"


class TestFillerCacheManagement:
    """Tests de gestión de cache."""
    
    def test_clear_cache(self, filler_system):
        """Verifica que clear_cache limpia memoria."""
        # Generar un filler (carga en memoria)
        if MELOTTS_AVAILABLE:
            filler_system.get_thinking_filler()
            
            # Verificar que hay algo en cache
            cache_size_before = len(filler_system._audio_cache)
            
            # Limpiar
            filler_system.clear_cache()
            
            # Verificar limpieza
            assert len(filler_system._audio_cache) == 0
    
    def test_regenerate_all(self, temp_cache_dir):
        """Verifica regeneración completa."""
        if not MELOTTS_AVAILABLE:
            pytest.skip("MeloTTS not available")
        
        fillers = FillerSystem(cache_dir=temp_cache_dir, auto_generate=False)
        
        # Generar algunos fillers
        fillers.get_thinking_filler()
        fillers.get_waiting_filler()
        
        cache_files_before = list(temp_cache_dir.glob("*.npy"))
        assert len(cache_files_before) >= 2
        
        # Regenerar
        fillers.regenerate_all()
        
        # Debería haber regenerado todos
        cache_files_after = list(temp_cache_dir.glob("*.npy"))
        assert len(cache_files_after) >= len(cache_files_before)


class TestFillerStrictMode:
    """Tests de STRICT MODE (sin MeloTTS)."""
    
    def test_unavailable_tts_returns_none(self, temp_cache_dir):
        """Si MeloTTS no disponible, get_filler retorna None."""
        fillers = FillerSystem(cache_dir=temp_cache_dir, auto_generate=False)
        
        if not MELOTTS_AVAILABLE:
            audio = fillers.get_thinking_filler()
            assert audio is None
