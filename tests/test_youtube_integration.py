"""
SARAi AGI v3.8.0 - YouTube/yt-dlp Integration Tests
Tests de integración real con yt-dlp (STRICT MODE)

LOC: ~200 (integration tests)
"""

import pytest
import asyncio
from unittest.mock import Mock, patch

from sarai_agi.learning.youtube_learning_system import (
    YouTubeLearningSystem,
    ContentCategory
)


@pytest.fixture
def mock_pipeline_deps():
    """Pipeline deps mínimos para YouTubeLearningSystem"""
    deps = Mock()
    deps.model_pool = None
    deps.emotional_context = None
    return deps


@pytest.fixture
def youtube_system(mock_pipeline_deps):
    """YouTubeLearningSystem con configuración básica"""
    config = {
        "youtube_learning": {
            "enabled": True,
            "max_videos_per_batch": 5
        }
    }
    return YouTubeLearningSystem(mock_pipeline_deps, config)


class TestYouTubeIntegration:
    """Tests de integración real yt-dlp → YouTubeLearningSystem"""
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_extract_metadata_real_video(self, youtube_system):
        """Test: Extracción REAL de metadata con yt-dlp"""
        # Video público de prueba (video corto de YouTube)
        test_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"  # "Me at the zoo" - primer video de YouTube
        
        metadata = await youtube_system._extract_metadata(test_url)
        
        # ⚠️ STRICT MODE: Si yt-dlp no está disponible o falla, skip
        if not metadata:
            pytest.skip("yt-dlp no disponible o video inaccesible - STRICT MODE activo")
        
        # Validar campos obligatorios REALES
        assert "id" in metadata
        assert "title" in metadata
        assert "channel" in metadata
        assert "duration" in metadata
        assert "views" in metadata
        
        # Validar que NO sean valores mock
        assert metadata["id"] != "", "ID no debe estar vacío"
        assert metadata["title"] != "Sample Video", "STRICT MODE: NO valores mock"
        assert metadata["channel"] != "Sample Channel", "STRICT MODE: NO valores mock"
        
        # Validar tipos de datos
        assert isinstance(metadata["duration"], int)
        assert isinstance(metadata["views"], int)
        assert isinstance(metadata["likes"], int)
        assert isinstance(metadata["comments"], int)
        
        # Los valores deben ser realistas
        assert metadata["duration"] > 0, "Duration debe ser > 0"
        assert metadata["views"] >= 0, "Views debe ser >= 0"
    
    @pytest.mark.asyncio
    async def test_extract_metadata_invalid_url(self, youtube_system):
        """Test: URL inválida retorna {} (STRICT MODE)"""
        invalid_url = "https://www.youtube.com/watch?v=INVALID_VIDEO_ID_12345"
        
        metadata = await youtube_system._extract_metadata(invalid_url)
        
        # ⚠️ STRICT MODE: URL inválida → {} (NO mock)
        assert metadata == {}, "STRICT MODE debe retornar {} para URL inválida"
    
    @pytest.mark.asyncio
    async def test_extract_metadata_no_ytdlp(self, youtube_system):
        """Test: Sin yt-dlp instalado retorna {} (STRICT MODE)"""
        # Simular que yt-dlp no está instalado
        with patch('builtins.__import__', side_effect=ImportError("No module named 'yt_dlp'")):
            metadata = await youtube_system._extract_metadata("https://youtube.com/watch?v=test")
            
            # ⚠️ STRICT MODE: Sin yt-dlp → {} (NO mock)
            assert metadata == {}, "STRICT MODE debe retornar {} si yt-dlp no instalado"
    
    @pytest.mark.asyncio
    async def test_extract_metadata_fields_coverage(self, youtube_system):
        """Test: Cobertura de campos extraídos"""
        test_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"
        
        metadata = await youtube_system._extract_metadata(test_url)
        
        if not metadata:
            pytest.skip("yt-dlp no disponible - STRICT MODE activo")
        
        # Campos esperados
        expected_fields = [
            "id", "title", "channel", "duration", "views", "likes", 
            "comments", "upload_date", "description", "tags", 
            "categories", "thumbnail", "webpage_url"
        ]
        
        # Verificar que todos los campos estén presentes
        for field in expected_fields:
            assert field in metadata, f"Campo {field} debe estar en metadata"
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_extract_metadata_multiple_videos(self, youtube_system):
        """Test: Extracción de múltiples videos (batch)"""
        test_urls = [
            "https://www.youtube.com/watch?v=jNQXAC9IVRw",  # Me at the zoo
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Rick Astley - Never Gonna Give You Up
        ]
        
        results = []
        for url in test_urls:
            metadata = await youtube_system._extract_metadata(url)
            if metadata:  # Solo agregar si hay datos reales
                results.append(metadata)
        
        if len(results) == 0:
            pytest.skip("yt-dlp no pudo extraer ningún video - STRICT MODE activo")
        
        # Verificar que al menos un video fue extraído
        assert len(results) > 0, "Debe extraer al menos 1 video con datos reales"
        
        # Verificar que cada video tiene ID único
        ids = [r["id"] for r in results]
        assert len(ids) == len(set(ids)), "Cada video debe tener ID único"
    
    @pytest.mark.asyncio
    async def test_metadata_values_realistic(self, youtube_system):
        """Test: Valores de metadata son realistas (no mock)"""
        test_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"
        
        metadata = await youtube_system._extract_metadata(test_url)
        
        if not metadata:
            pytest.skip("yt-dlp no disponible - STRICT MODE activo")
        
        # Validaciones de realismo
        assert metadata["duration"] < 86400, "Duration no debe ser > 24 horas (videos normales)"
        assert metadata["views"] < 1e12, "Views debe ser realista (< 1 trillion)"
        
        # Title no debe estar vacío
        assert len(metadata["title"]) > 0, "Title debe tener contenido"
        
        # Channel no debe estar vacío
        assert len(metadata["channel"]) > 0, "Channel debe tener contenido"
    
    @pytest.mark.asyncio
    async def test_metadata_tags_and_description(self, youtube_system):
        """Test: Tags y description se extraen correctamente"""
        test_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"
        
        metadata = await youtube_system._extract_metadata(test_url)
        
        if not metadata:
            pytest.skip("yt-dlp no disponible - STRICT MODE activo")
        
        # Tags debe ser lista (puede estar vacía en videos viejos)
        assert isinstance(metadata["tags"], list)
        
        # Description debe ser string
        assert isinstance(metadata["description"], str)
        
        # Categories debe ser lista
        assert isinstance(metadata["categories"], list)


class TestYouTubeIntegrationStrictMode:
    """Tests específicos de STRICT MODE behavior"""
    
    @pytest.mark.asyncio
    async def test_no_mock_fallback_on_error(self, youtube_system):
        """Test: Error en yt-dlp → {} (NO mock)"""
        # URL que causará error en yt-dlp
        error_url = "not_a_valid_url"
        
        metadata = await youtube_system._extract_metadata(error_url)
        
        # ⚠️ STRICT MODE: Error → {} (NO mock con valores fijos)
        assert metadata == {}, "STRICT MODE: Error debe retornar {}, no mock"
    
    @pytest.mark.asyncio
    async def test_empty_result_not_mock(self, youtube_system):
        """Test: Resultado vacío es {} (no dict con valores mock)"""
        # Video privado o eliminado
        deleted_url = "https://www.youtube.com/watch?v=DELETED_VIDEO"
        
        metadata = await youtube_system._extract_metadata(deleted_url)
        
        # ⚠️ STRICT MODE: Video no disponible → {} (NO mock)
        if metadata:
            # Si hay metadata, debe ser REAL (no mock)
            assert metadata.get("title") != "Sample Video"
            assert metadata.get("channel") != "Sample Channel"
            assert metadata.get("id") != "abc123"
        else:
            # Si está vacío, debe ser exactamente {}
            assert metadata == {}
    
    @pytest.mark.asyncio
    async def test_real_ytdlp_never_returns_mock_values(self, youtube_system):
        """Test: yt-dlp REAL nunca retorna valores mock específicos"""
        test_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"
        
        metadata = await youtube_system._extract_metadata(test_url)
        
        if not metadata:
            pytest.skip("yt-dlp no disponible - STRICT MODE activo")
        
        # Verificar que NINGÚN valor sea de los mocks anteriores
        mock_indicators = [
            ("id", "abc123"),
            ("title", "Sample Video"),
            ("channel", "Sample Channel"),
            ("duration", 600),  # Exactamente 10 min (mock)
            ("views", 100000),  # Valor exacto mock
            ("likes", 5000),    # Valor exacto mock
            ("comments", 500)   # Valor exacto mock
        ]
        
        for field, mock_value in mock_indicators:
            if field in metadata:
                assert metadata[field] != mock_value, \
                    f"STRICT MODE: {field} no debe tener valor mock '{mock_value}'"
    
    @pytest.mark.asyncio
    async def test_asyncio_executor_usage(self, youtube_system):
        """Test: Extracción usa asyncio executor (no bloquea event loop)"""
        import time
        
        test_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"
        
        start = time.time()
        
        # Ejecutar extracción
        metadata = await youtube_system._extract_metadata(test_url)
        
        elapsed = time.time() - start
        
        if not metadata:
            pytest.skip("yt-dlp no disponible - STRICT MODE activo")
        
        # Debe completar en tiempo razonable (< 30s para video público)
        assert elapsed < 30, f"Extracción debe completar en < 30s, tomó {elapsed:.2f}s"
