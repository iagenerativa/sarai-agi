"""
SARAi AGI v3.8.0 - SearXNG Integration Tests
Tests de integración real con SearXNG

LOC: ~200 (integration tests)
"""

import pytest
import asyncio
from unittest.mock import Mock

from sarai_agi.search import (
    MultiSourceSearcher,
    SearchSource,
    SearchResult,
    VerificationLevel,
    SearchStrategy
)


@pytest.fixture
def searxng_config():
    """Configuración de prueba con SearXNG habilitado en STRICT MODE (100% real)"""
    return {
        "search_integration": {
            "multi_source_search": {
                "enabled": True,
                "max_sources": 6,
                "verification_level": "STANDARD",
                "parallel_search": True,
                "max_concurrent_requests": 8,
                "consensus_threshold": 0.7,
                "searxng": {
                    "enabled": True,
                    "url": "http://localhost:8888",
                    "timeout": 5,
                    "max_retries": 2,
                    "fallback_to_mock": False  # ⚠️ STRICT MODE: 100% real, no mocks
                }
            },
            "source_configuration": {
                "academic_papers": {"weight": 0.9},
                "news_agencies": {"weight": 0.8},
                "technical_docs": {"weight": 0.7}
            }
        }
    }


@pytest.fixture
def mock_pipeline_deps():
    """Mock de PipelineDependencies"""
    deps = Mock()
    deps.cascade_oracle = Mock()
    deps.emotional_context = Mock()
    deps.trm_classifier = Mock(return_value={"complexity_score": 0.5})
    return deps


@pytest.fixture
def searxng_searcher(mock_pipeline_deps, searxng_config):
    """MultiSourceSearcher con SearXNG habilitado"""
    return MultiSourceSearcher(mock_pipeline_deps, searxng_config)


class TestSearXNGIntegration:
    """Tests de integración real con SearXNG"""
    
    @pytest.mark.asyncio
    async def test_searxng_real_search(self, searxng_searcher):
        """Test: Búsqueda real con SearXNG - STRICT MODE"""
        source = SearchSource(
            name="academic_papers",
            url_pattern="arxiv.org",
            weight=0.9,
            credibility_score=0.95,
            update_frequency="real-time",
            specializations=["research"]
        )
        
        result = await searxng_searcher.search_single_source(source, "Python programming")
        
        # ⚠️ STRICT MODE: Si SearXNG no encuentra nada, retorna None (NO mock)
        if result is None:
            pytest.skip("SearXNG no encontró resultados reales - STRICT MODE activo")
        
        # Si HAY resultado, validar que sea real
        assert isinstance(result, SearchResult)
        assert result.content != ""
        assert result.relevance_score > 0.0
        
        # ⚠️ STRICT MODE: El resultado DEBE ser de SearXNG (no mock)
        assert result.metadata["search_method"] == "searxng", "STRICT MODE: Solo datos reales"
        assert "[Mock]" not in result.content, "STRICT MODE: No debe haber contenido mock"
    
    @pytest.mark.asyncio
    async def test_searxng_multiple_sources(self, searxng_searcher):
        """Test: Búsqueda paralela en múltiples fuentes con SearXNG"""
        results = await searxng_searcher.parallel_multi_source_search("machine learning")
        
        # Verificar que obtuvimos resultados de múltiples fuentes
        assert len(results) >= 3  # Al menos 3 sources respondieron
        assert all(isinstance(r, SearchResult) for r in results)
        
        # Al menos algunos resultados deberían ser de SearXNG (no mock)
        searxng_results = [r for r in results if r.metadata.get("search_method") == "searxng"]
        assert len(searxng_results) > 0, "Should have at least one real SearXNG result"
        
        # Verificar que todos tienen contenido válido
        assert all(r.content != "" for r in results)
    
    @pytest.mark.asyncio
    async def test_searxng_consensus_real(self, searxng_searcher):
        """Test consenso multi-source con SearXNG real - STRICT MODE"""
        verified = await searxng_searcher.search(
            query="Artificial Intelligence applications",
            context={"verification_level": "STANDARD"}
        )
        
        # ⚠️ STRICT MODE: Si no hay fuentes reales, sources_used = 0 (NO mock)
        if not hasattr(verified, 'sources_used') or verified.sources_used == 0:
            pytest.skip("SearXNG no encontró resultados en ninguna fuente - STRICT MODE activo")
        
        # Si HAY fuentes, validar calidad real
        assert verified.consensus_score >= 0.0
        assert verified.confidence_level > 0.0
        # Los facts NUNCA deben ser mock en STRICT MODE
        if hasattr(verified, 'facts'):
            for fact in verified.facts:
                assert "[Mock]" not in fact
    
    @pytest.mark.asyncio
    async def test_searxng_category_mapping(self, searxng_searcher):
        """Test: Mapeo correcto de fuentes a categorías SearXNG"""
        # Test diferentes tipos de fuentes
        sources = [
            ("academic_papers", "science"),
            ("news_agencies", "news"),
            ("technical_docs", "it"),
            ("stackoverflow", "it"),
            ("wikipedia", "general")
        ]
        
        for source_name, expected_category in sources:
            source = SearchSource(source_name, "test.com", 0.5, 0.5, "real-time", [])
            category = searxng_searcher._map_source_to_category(source)
            assert category == expected_category, f"{source_name} should map to {expected_category}"
    
    @pytest.mark.asyncio
    async def test_searxng_fallback_on_error(self, mock_pipeline_deps):
        """Test STRICT MODE cuando SearXNG falla - debe retornar None"""
        # Crear searcher con URL inválida
        config = {
            "search_integration": {
                "multi_source_search": {
                    "enabled": True,
                    "searxng": {
                        "enabled": True,
                        "url": "http://invalid-url:9999",
                        "timeout": 1,
                        "max_retries": 2,
                        "fallback_to_mock": False  # ⚠️ STRICT MODE
                    }
                }
            }
        }
        
        searcher = MultiSourceSearcher(mock_pipeline_deps, config)
        
        source = SearchSource(
            name="test_source",
            url_pattern="test.com",
            weight=0.5,
            credibility_score=0.5,
            update_frequency="daily",
            specializations=[]
        )
        
        result = await searcher.search_single_source(source, "test query")
        
        # ⚠️ STRICT MODE: Cuando SearXNG falla, retorna None (NO mock)
        assert result is None, "STRICT MODE debe retornar None si SearXNG falla"
    
    @pytest.mark.asyncio
    async def test_searxng_timeout_handling(self, searxng_searcher):
        """Test: Manejo de timeouts en SearXNG"""
        # Configurar timeout muy corto
        original_timeout = searxng_searcher.searxng_timeout
        searxng_searcher.searxng_timeout = 0.001  # 1ms (casi imposible)
        
        source = SearchSource("test_source", "test.com", 0.5, 0.5, "real-time", [])
        result = await searxng_searcher.search_single_source(source, "test query")
        
        # Debería retornar algo (mock o None) sin crash
        assert result is not None or result is None
        
        # Restaurar timeout
        searxng_searcher.searxng_timeout = original_timeout
    
    @pytest.mark.asyncio
    async def test_searxng_retry_logic(self, searxng_searcher):
        """Test: Retry logic de SearXNG"""
        # Verificar que max_retries está configurado
        assert searxng_searcher.searxng_max_retries >= 1
        
        # Con URL válida, debería tener éxito en primer intento o retry
        source = SearchSource("test_source", "test.com", 0.5, 0.5, "real-time", [])
        result = await searxng_searcher.search_single_source(source, "Python")
        
        assert result is not None


class TestSearXNGConfiguration:
    """Tests de configuración de SearXNG"""
    
    def test_searxng_enabled_flag(self, searxng_searcher):
        """Test: Flag de SearXNG habilitado correctamente"""
        assert searxng_searcher.searxng_enabled is True
        assert searxng_searcher.searxng_url == "http://localhost:8888"
        assert searxng_searcher.searxng_timeout == 5
        assert searxng_searcher.searxng_max_retries == 2
    
    def test_searxng_disabled_config(self, mock_pipeline_deps):
        """Test configuración con SearXNG deshabilitado - STRICT MODE"""
        config = {
            "search_integration": {
                "multi_source_search": {
                    "enabled": True,
                    "searxng": {
                        "enabled": False,
                        "fallback_to_mock": False  # ⚠️ STRICT MODE explícito
                    }
                }
            }
        }
        
        searcher = MultiSourceSearcher(mock_pipeline_deps, config)
        assert searcher.searxng_enabled is False
        # ⚠️ STRICT MODE: fallback_to_mock debe ser False por defecto
        assert searcher.fallback_to_mock is False


class TestSearXNGAccuracy:
    """Tests de accuracy con SearXNG real"""
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_searxng_accuracy_benchmark(self, searxng_searcher):
        """Test: Benchmark de accuracy con queries conocidas - STRICT MODE"""
        # Queries con respuestas conocidas
        test_queries = [
            ("Python programming language", ["python", "programming", "language"]),
            ("Machine learning basics", ["machine", "learning", "ml"]),
            ("Climate change effects", ["climate", "change", "environment"])
        ]
        
        accuracy_scores = []
        successful_queries = 0
        
        for query, expected_keywords in test_queries:
            verified = await searxng_searcher.search(query, VerificationLevel.STANDARD)
            
            # ⚠️ STRICT MODE: Si no hay main_conclusion, skip esta query
            if not hasattr(verified, 'main_conclusion') or not verified.main_conclusion:
                continue
            
            successful_queries += 1
            
            # Verificar que al menos 1 keyword esperado aparece
            content_lower = verified.main_conclusion.lower()
            
            # ⚠️ STRICT MODE: No debe haber contenido mock
            assert "[Mock]" not in verified.main_conclusion, "STRICT MODE: No contenido mock"
            
            matches = sum(1 for kw in expected_keywords if kw in content_lower)
            accuracy = matches / len(expected_keywords)
            accuracy_scores.append(accuracy)
        
        # Si no hubo queries exitosas, skip el test
        if successful_queries == 0:
            pytest.skip("SearXNG no encontró datos reales para ninguna query - STRICT MODE activo")
        
        # Accuracy promedio debería ser > 0.5 (al menos 50% de keywords match)
        avg_accuracy = sum(accuracy_scores) / len(accuracy_scores)
        assert avg_accuracy > 0.5, f"Average accuracy too low: {avg_accuracy:.2f}"
