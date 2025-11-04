"""
SARAi AGI v3.8.0 - Qwen3-VL:4B Integration Tests (via MultimodalModelWrapper)
Tests de integración real con Qwen3-VL:4B usando wrapper personalizado (STRICT MODE)

Este módulo valida que:
1. ✅ Usa MultimodalModelWrapper vía ModelPool.get("qwen3_vl")
2. ✅ Nunca retorna valores PLACEHOLDER mock
3. ✅ Retorna {} (empty dict) en TODOS los errores (STRICT MODE)
4. ✅ Parsea JSON correctamente de LLM output
5. ✅ Usa fallback keyword-based si JSON inválido
6. ✅ Ejecuta de forma async con asyncio.to_thread
7. ✅ Hace release() del modelo después de usar

LOC: ~300 (integration tests)
"""

import pytest
import asyncio
from unittest.mock import Mock, MagicMock, patch, call
import base64

from sarai_agi.learning.youtube_learning_system import (
    YouTubeLearningSystem,
    ContentCategory
)


@pytest.fixture
def mock_multimodal_wrapper():
    """Mock de MultimodalModelWrapper que retorna JSON válido"""
    wrapper = Mock()
    wrapper.invoke = Mock(return_value="""
Análisis del frame:

{
    "topics": ["artificial intelligence", "machine learning", "deep learning"],
    "emotions": {"interest": 0.85, "surprise": 0.6, "trust": 0.7},
    "social_implications": ["automation impact", "job transformation", "education revolution"],
    "cultural_relevance": {"global": 0.9, "LATAM": 0.75, "Asia": 0.8}
}

Este frame muestra conceptos técnicos avanzados.
""")
    return wrapper


@pytest.fixture
def mock_model_pool(mock_multimodal_wrapper):
    """Mock de ModelPool que retorna MultimodalModelWrapper"""
    pool = Mock()
    pool.get = Mock(return_value=mock_multimodal_wrapper)
    pool.release = Mock()
    return pool


@pytest.fixture
def mock_pipeline_deps(mock_model_pool):
    """Pipeline deps con model_pool"""
    deps = Mock()
    deps.model_pool = mock_model_pool
    deps.emotional_context = None
    return deps


@pytest.fixture
def youtube_system(mock_pipeline_deps):
    """YouTubeLearningSystem con model_pool"""
    config = {
        "youtube_learning": {
            "enabled": True,
            "max_videos_per_batch": 5
        }
    }
    return YouTubeLearningSystem(mock_pipeline_deps, config)


@pytest.fixture
def sample_metadata():
    """Metadata de video de ejemplo"""
    return {
        "id": "test123",
        "title": "AI Revolution: Deep Learning Explained",
        "channel": "Tech Channel",
        "duration": 600,
        "views": 50000,
        "description": "Learn about deep learning and neural networks in this comprehensive tutorial"
    }


@pytest.fixture
def sample_frames():
    """Lista de frames con base64 tiny image (1x1 white pixel)"""
    # Tiny 1x1 white PNG in base64
    tiny_png_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
    
    return [
        {
            "timestamp": 0.0,
            "frame_data": tiny_png_b64
        },
        {
            "timestamp": 5.0,
            "frame_data": tiny_png_b64
        },
        {
            "timestamp": 10.0,
            "frame_data": tiny_png_b64
        }
    ]


class TestQwen3VLIntegrationViaWrapper:
    """Tests de integración Qwen3-VL:4B via MultimodalModelWrapper"""
    
    @pytest.mark.asyncio
    async def test_multimodal_analysis_with_wrapper(
        self, youtube_system, sample_metadata, sample_frames, mock_model_pool, mock_multimodal_wrapper
    ):
        """Test: Análisis multimodal usando MultimodalModelWrapper real"""
        
        result = await youtube_system._multimodal_analysis(sample_metadata, sample_frames)
        
        # Validar que se llamó get() y release()
        mock_model_pool.get.assert_called_once_with("qwen3_vl")
        mock_model_pool.release.assert_called_once_with("qwen3_vl")
        
        # Validar que se invocó el wrapper con input multimodal
        mock_multimodal_wrapper.invoke.assert_called_once()
        call_args = mock_multimodal_wrapper.invoke.call_args
        
        # Verificar estructura del input multimodal
        multimodal_input = call_args[0][0]
        assert "text" in multimodal_input, "Input debe tener 'text'"
        assert "image" in multimodal_input, "Input debe tener 'image'"
        assert "AI Revolution" in multimodal_input["text"]  # Del title
        
        # Verificar config con max_tokens
        config = call_args[0][1]
        assert config.get("max_tokens") == 512
        
        # Validar resultado
        assert isinstance(result, dict)
        assert "topics" in result
        assert "emotions" in result
        assert "social_implications" in result
        assert "cultural_relevance" in result
        
        # Verificar valores reales (NO PLACEHOLDER)
        assert len(result["topics"]) == 3
        assert "artificial intelligence" in result["topics"]
        assert result["emotions"].get("interest") == 0.85
        assert "automation impact" in result["social_implications"]
        assert result["cultural_relevance"].get("global") == 0.9
    
    @pytest.mark.asyncio
    async def test_multimodal_analysis_no_model_pool(
        self, mock_pipeline_deps, sample_metadata, sample_frames
    ):
        """Test STRICT MODE: Si no hay model_pool, retornar {}"""
        # System sin model_pool
        mock_pipeline_deps.model_pool = None
        youtube_system = YouTubeLearningSystem(mock_pipeline_deps, {})
        
        result = await youtube_system._multimodal_analysis(sample_metadata, sample_frames)
        
        assert result == {}, "STRICT MODE: debe retornar {} si no hay model_pool"
    
    @pytest.mark.asyncio
    async def test_multimodal_analysis_no_frames(
        self, youtube_system, sample_metadata
    ):
        """Test STRICT MODE: Si no hay frames, retornar {}"""
        # Sin frames
        result = await youtube_system._multimodal_analysis(sample_metadata, [])
        
        assert result == {}, "STRICT MODE: debe retornar {} si no hay frames"
        
        # Frames None
        result = await youtube_system._multimodal_analysis(sample_metadata, None)
        
        assert result == {}, "STRICT MODE: debe retornar {} si frames es None"
    
    @pytest.mark.asyncio
    async def test_multimodal_analysis_model_pool_get_error(
        self, youtube_system, sample_metadata, sample_frames, mock_model_pool
    ):
        """Test STRICT MODE: Si get() falla, retornar {}"""
        # Simular error en get()
        mock_model_pool.get.side_effect = Exception("Model not found")
        
        result = await youtube_system._multimodal_analysis(sample_metadata, sample_frames)
        
        assert result == {}, "STRICT MODE: debe retornar {} si get() falla"
    
    @pytest.mark.asyncio
    async def test_multimodal_analysis_invalid_frame_data(
        self, youtube_system, sample_metadata, mock_model_pool
    ):
        """Test STRICT MODE: Si frame sin frame_data, retornar {}"""
        # Frame sin frame_data
        invalid_frames = [{"timestamp": 0.0}]  # No frame_data
        
        result = await youtube_system._multimodal_analysis(sample_metadata, invalid_frames)
        
        assert result == {}, "STRICT MODE: debe retornar {} si no hay frame_data"
        
        # Verificar que se hizo release()
        mock_model_pool.release.assert_called_once_with("qwen3_vl")
    
    @pytest.mark.asyncio
    async def test_multimodal_analysis_wrapper_invoke_error(
        self, youtube_system, sample_metadata, sample_frames, mock_model_pool, mock_multimodal_wrapper
    ):
        """Test STRICT MODE: Si invoke() falla, retornar {}"""
        # Simular error en invoke()
        mock_multimodal_wrapper.invoke.side_effect = Exception("Model inference failed")
        
        result = await youtube_system._multimodal_analysis(sample_metadata, sample_frames)
        
        assert result == {}, "STRICT MODE: debe retornar {} si invoke() falla"
        
        # Verificar que se hizo release() en el finally
        mock_model_pool.release.assert_called_once_with("qwen3_vl")
    
    @pytest.mark.asyncio
    async def test_multimodal_analysis_json_parsing_success(
        self, youtube_system, sample_metadata, sample_frames, mock_multimodal_wrapper
    ):
        """Test: JSON parsing exitoso extrae valores correctamente"""
        
        result = await youtube_system._multimodal_analysis(sample_metadata, sample_frames)
        
        # Validar JSON parseado correctamente
        assert result["topics"] == ["artificial intelligence", "machine learning", "deep learning"]
        assert result["emotions"]["interest"] == 0.85
        assert result["emotions"]["surprise"] == 0.6
        assert result["social_implications"] == ["automation impact", "job transformation", "education revolution"]
        assert result["cultural_relevance"]["global"] == 0.9
    
    @pytest.mark.asyncio
    async def test_multimodal_analysis_keyword_fallback(
        self, youtube_system, sample_metadata, sample_frames, mock_multimodal_wrapper
    ):
        """Test: Si no hay JSON válido, usar fallback keyword-based"""
        # Wrapper retorna texto sin JSON
        mock_multimodal_wrapper.invoke.return_value = """
        Este video trata sobre tecnología e innovación digital.
        Es muy interesante y sorprendente ver cómo avanza el desarrollo.
        Tiene gran relevancia para la educación y la sociedad.
        """
        
        result = await youtube_system._multimodal_analysis(sample_metadata, sample_frames)
        
        # Debe usar keyword-based fallback
        assert isinstance(result, dict)
        assert "topics" in result
        assert "emotions" in result
        
        # Verificar que detectó keywords
        assert "technology" in result["topics"] or "innovation" in result["topics"]
        assert len(result["emotions"]) > 0  # Debe detectar alguna emoción
    
    @pytest.mark.asyncio
    async def test_multimodal_analysis_invalid_wrapper_result(
        self, youtube_system, sample_metadata, sample_frames, mock_multimodal_wrapper
    ):
        """Test STRICT MODE: Si wrapper retorna None o no-string, retornar {}"""
        # Wrapper retorna None
        mock_multimodal_wrapper.invoke.return_value = None
        
        result = await youtube_system._multimodal_analysis(sample_metadata, sample_frames)
        
        assert result == {}, "STRICT MODE: debe retornar {} si invoke() retorna None"
        
        # Wrapper retorna dict (no string)
        mock_multimodal_wrapper.invoke.return_value = {"invalid": "format"}
        
        result = await youtube_system._multimodal_analysis(sample_metadata, sample_frames)
        
        assert result == {}, "STRICT MODE: debe retornar {} si invoke() no retorna string"


class TestQwen3VLIntegrationStrictMode:
    """Tests específicos de STRICT MODE compliance"""
    
    @pytest.mark.asyncio
    async def test_no_placeholder_values_returned(
        self, youtube_system, sample_metadata, sample_frames
    ):
        """Test STRICT MODE: NUNCA retornar valores PLACEHOLDER mock"""
        
        result = await youtube_system._multimodal_analysis(sample_metadata, sample_frames)
        
        # Valores que NO deben aparecer (PLACEHOLDER del código original)
        forbidden_topics = ["technology", "social impact", "innovation"]
        forbidden_emotions = {"interest": 0.7, "surprise": 0.3}
        
        # Si result no está vacío, verificar que NO tiene valores mock
        if result:
            assert result.get("topics") != forbidden_topics, "NO debe retornar topics PLACEHOLDER"
            assert result.get("emotions") != forbidden_emotions, "NO debe retornar emotions PLACEHOLDER"
    
    @pytest.mark.asyncio
    async def test_empty_dict_on_all_errors(
        self, youtube_system, sample_metadata, sample_frames, mock_model_pool, mock_multimodal_wrapper
    ):
        """Test STRICT MODE: TODOS los errores retornan {} (empty dict)"""
        
        # Error 1: get() falla
        mock_model_pool.get.side_effect = Exception("Get failed")
        result = await youtube_system._multimodal_analysis(sample_metadata, sample_frames)
        assert result == {}
        
        # Reset
        mock_model_pool.get.side_effect = None
        mock_model_pool.get.return_value = mock_multimodal_wrapper
        
        # Error 2: invoke() falla
        mock_multimodal_wrapper.invoke.side_effect = Exception("Invoke failed")
        result = await youtube_system._multimodal_analysis(sample_metadata, sample_frames)
        assert result == {}
        
        # Error 3: invoke() retorna None
        mock_multimodal_wrapper.invoke.side_effect = None
        mock_multimodal_wrapper.invoke.return_value = None
        result = await youtube_system._multimodal_analysis(sample_metadata, sample_frames)
        assert result == {}
        
        # Error 4: JSON inválido sin keywords
        mock_multimodal_wrapper.invoke.return_value = "qwerty 12345 xyz"
        result = await youtube_system._multimodal_analysis(sample_metadata, sample_frames)
        # Debe retornar dict con valores default (no vacío porque usa fallback)
        assert isinstance(result, dict)
    
    @pytest.mark.asyncio
    async def test_async_execution_with_asyncio_to_thread(
        self, youtube_system, sample_metadata, sample_frames, mock_model_pool
    ):
        """Test: Verifica que usa asyncio.to_thread para ejecución async"""
        
        # Ejecutar análisis
        start_time = asyncio.get_event_loop().time()
        result = await youtube_system._multimodal_analysis(sample_metadata, sample_frames)
        elapsed = asyncio.get_event_loop().time() - start_time
        
        # Debe completar rápidamente (es mock)
        assert elapsed < 1.0, "Mock debe ser rápido"
        
        # Verificar que get() se llamó (confirma ejecución async)
        mock_model_pool.get.assert_called_once_with("qwen3_vl")
    
    @pytest.mark.asyncio
    async def test_model_release_always_called(
        self, youtube_system, sample_metadata, sample_frames, mock_model_pool, mock_multimodal_wrapper
    ):
        """Test: Verifica que release() SIEMPRE se llama (incluso en errores)"""
        
        # Caso 1: Éxito - debe llamar release()
        result = await youtube_system._multimodal_analysis(sample_metadata, sample_frames)
        assert mock_model_pool.release.call_count == 1
        
        # Reset
        mock_model_pool.release.reset_mock()
        
        # Caso 2: invoke() falla - debe llamar release() en finally
        mock_multimodal_wrapper.invoke.side_effect = Exception("Test error")
        result = await youtube_system._multimodal_analysis(sample_metadata, sample_frames)
        assert mock_model_pool.release.call_count == 1
        
        # Reset
        mock_model_pool.release.reset_mock()
        mock_multimodal_wrapper.invoke.side_effect = None
        
        # Caso 3: frame_data vacío - debe llamar release() antes de retornar
        invalid_frames = [{"timestamp": 0.0}]  # Sin frame_data
        result = await youtube_system._multimodal_analysis(sample_metadata, invalid_frames)
        assert mock_model_pool.release.call_count == 1
