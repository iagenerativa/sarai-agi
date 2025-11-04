"""
SARAi AGI v3.7.0 - Multi-Source Search Tests
Tests de búsqueda multi-fuente, verificación y consensus

LOC: ~300 (core tests, versión compacta)
"""

import pytest
import asyncio
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock, patch

from sarai_agi.search import (
    MultiSourceSearcher,
    SearchStrategy,
    VerificationLevel,
    SearchSource,
    SearchResult,
    VerifiedInformation,
)


@pytest.fixture
def mock_pipeline_deps():
    """Mock de PipelineDependencies"""
    deps = Mock()
    deps.cascade_oracle = Mock()
    deps.emotional_context = Mock()
    deps.trm_classifier = Mock(return_value={"complexity_score": 0.5})
    return deps


@pytest.fixture
def multi_source_config():
    """Configuración de prueba"""
    return {
        "search_integration": {
            "multi_source_search": {
                "enabled": True,
                "max_sources": 6,
                "verification_level": "STANDARD",
                "parallel_search": True,
                "max_concurrent_requests": 8,
                "consensus_threshold": 0.7
            },
            "source_configuration": {
                "academic_papers": {"weight": 0.9},
                "news_agencies": {"weight": 0.8},
                "technical_docs": {"weight": 0.7}
            }
        }
    }


@pytest.fixture
def multi_source_searcher(mock_pipeline_deps, multi_source_config):
    """Instancia de MultiSourceSearcher"""
    return MultiSourceSearcher(mock_pipeline_deps, multi_source_config)


class TestMultiSourceSearcher:
    """Tests para MultiSourceSearcher"""
    
    def test_initialization(self, multi_source_searcher):
        """Test: Inicialización correcta"""
        assert multi_source_searcher.max_sources == 6
        assert multi_source_searcher.verification_level == VerificationLevel.STANDARD
        assert multi_source_searcher.consensus_threshold == 0.7
        assert len(multi_source_searcher.search_sources) == 6
    
    @pytest.mark.asyncio
    async def test_analyze_query_intent_simple(self, multi_source_searcher):
        """Test: Análisis de query simple"""
        query = "What is Python?"
        analysis = await multi_source_searcher.analyze_query_intent(query)
        
        assert "query" in analysis
        assert "complexity" in analysis
        assert "strategy" in analysis
        assert analysis["query"] == query
    
    @pytest.mark.asyncio
    async def test_analyze_query_intent_complex(self, multi_source_searcher):
        """Test: Análisis de query compleja"""
        # Mock TRM classifier con alta complejidad
        multi_source_searcher.trm_classifier = Mock(
            return_value={"complexity_score": 0.85}
        )
        
        query = "How does quantum computing affect cryptography?"
        analysis = await multi_source_searcher.analyze_query_intent(query)
        
        assert analysis["complexity"] == 0.85
        assert analysis["strategy"] == SearchStrategy.EXPERT_DEEP
        assert analysis["requires_verification"] == True
    
    def test_generate_intelligent_subqueries_explanatory(self, multi_source_searcher):
        """Test: Generación de sub-queries para query explanatory"""
        query = "How does photosynthesis work?"
        analysis = {"query_type": "explanatory"}
        
        sub_queries = multi_source_searcher.generate_intelligent_subqueries(query, analysis)
        
        assert len(sub_queries) >= 2
        assert query in sub_queries
        assert any("What is" in sq for sq in sub_queries)
    
    def test_generate_intelligent_subqueries_time_sensitive(self, multi_source_searcher):
        """Test: Sub-queries para time-sensitive"""
        query = "Latest AI developments"
        analysis = {"query_type": "time_sensitive"}
        
        sub_queries = multi_source_searcher.generate_intelligent_subqueries(query, analysis)
        
        assert len(sub_queries) >= 2
        assert any("trending" in sq.lower() or "latest" in sq.lower() for sq in sub_queries)
    
    @pytest.mark.asyncio
    async def test_search_single_source_success(self, multi_source_searcher):
        """Test: Búsqueda exitosa en fuente individual"""
        source = multi_source_searcher.search_sources[0]
        query = "test query"
        
        result = await multi_source_searcher.search_single_source(source, query)
        
        assert result is not None
        assert isinstance(result, SearchResult)
        assert result.source == source
        assert result.relevance_score > 0
        assert len(result.citations) > 0
    
    @pytest.mark.asyncio
    async def test_parallel_multi_source_search(self, multi_source_searcher):
        """Test: Búsqueda paralela en múltiples fuentes"""
        sub_queries = ["query 1", "query 2"]
        
        results = await multi_source_searcher.parallel_multi_source_search(sub_queries)
        
        assert isinstance(results, list)
        # Con 2 queries × 6 fuentes = hasta 12 resultados
        assert len(results) > 0
        assert all(isinstance(r, SearchResult) for r in results)
    
    def test_identify_consensus_multiple_sources(self, multi_source_searcher):
        """Test: Identificación de consenso con múltiples fuentes"""
        facts = [
            {"content": "Fact A from source 1", "source": "source1", "weight": 0.9, "credibility": 0.95},
            {"content": "Fact A from source 2", "source": "source2", "weight": 0.8, "credibility": 0.85},
            {"content": "Fact A from source 3", "source": "source3", "weight": 0.7, "credibility": 0.80},
            {"content": "Fact B from source 1", "source": "source1", "weight": 0.9, "credibility": 0.95},
        ]
        
        consensus_facts = multi_source_searcher.identify_consensus(facts)
        
        # Fact A aparece en 3 fuentes → consenso
        assert len(consensus_facts) >= 1
        assert any("Fact A" in f["content"] for f in consensus_facts)
    
    @pytest.mark.asyncio
    async def test_cross_verify_sources_high_consensus(self, multi_source_searcher):
        """Test: Verificación cruzada con alto consenso"""
        # Mock search results con contenido similar
        search_results = []
        for i in range(4):
            source = multi_source_searcher.search_sources[i]
            result = SearchResult(
                source=source,
                content="Similar fact about AI",
                relevance_score=0.8,
                timestamp="2025-01-04T00:00:00Z",
                metadata={},
                citations=[f"http://source{i}.com"]
            )
            search_results.append(result)
        
        verified_info = await multi_source_searcher.cross_verify_sources(search_results)
        
        assert isinstance(verified_info, VerifiedInformation)
        assert verified_info.consensus_score > 0.0
        assert verified_info.sources_used == 4
        assert verified_info.confidence_level > 0.0
        assert len(verified_info.citation_graph) > 0
    
    @pytest.mark.asyncio
    async def test_cross_verify_sources_low_consensus(self, multi_source_searcher):
        """Test: Verificación con bajo consenso"""
        # Mock results con contenido diferente
        search_results = []
        for i in range(3):
            source = multi_source_searcher.search_sources[i]
            result = SearchResult(
                source=source,
                content=f"Different fact {i}",
                relevance_score=0.6,
                timestamp="2025-01-04T00:00:00Z",
                metadata={},
                citations=[f"http://source{i}.com"]
            )
            search_results.append(result)
        
        verified_info = await multi_source_searcher.cross_verify_sources(search_results)
        
        # Bajo consenso porque cada fuente tiene contenido único
        assert verified_info.consensus_score < multi_source_searcher.consensus_threshold
        assert len(verified_info.conflicting_sources) > 0
    
    @pytest.mark.asyncio
    async def test_search_full_pipeline(self, multi_source_searcher):
        """Test: Pipeline completo de búsqueda multi-fuente"""
        query = "What is machine learning?"
        context = {"user_id": "test_user", "session_id": "test_session"}
        
        verified_info = await multi_source_searcher.search(query, context)
        
        assert isinstance(verified_info, VerifiedInformation)
        assert verified_info.sources_used > 0
        assert verified_info.consensus_score >= 0.0
        assert verified_info.confidence_level >= 0.0
    
    def test_source_weights_correctly_configured(self, multi_source_searcher):
        """Test: Pesos de fuentes configurados correctamente"""
        sources = multi_source_searcher.search_sources
        
        # Verificar orden descendente de weights
        weights = [s.weight for s in sources]
        assert weights == sorted(weights, reverse=True)
        
        # Verificar academic papers tiene mayor weight
        academic = next(s for s in sources if s.name == "academic_papers")
        assert academic.weight == 0.9
        assert academic.credibility_score == 0.95


class TestVerificationLevel:
    """Tests para VerificationLevel enum"""
    
    def test_verification_levels_exist(self):
        """Test: Niveles de verificación existen"""
        assert VerificationLevel.BASIC.value == 1
        assert VerificationLevel.STANDARD.value == 2
        assert VerificationLevel.COMPREHENSIVE.value == 3


class TestSearchStrategy:
    """Tests para SearchStrategy enum"""
    
    def test_search_strategies_exist(self):
        """Test: Estrategias de búsqueda existen"""
        assert SearchStrategy.EXPERT_DEEP.value == "expert_deep"
        assert SearchStrategy.RAPID_SCAN.value == "rapid_scan"
        assert SearchStrategy.EMOTIONAL_CONTEXT.value == "emotional"
        assert SearchStrategy.TECHNICAL_FOCUS.value == "technical"


@pytest.mark.integration
class TestMultiSourceIntegration:
    """Tests de integración multi-source"""
    
    @pytest.mark.asyncio
    async def test_graceful_degradation_on_source_failure(self, multi_source_searcher):
        """Test: Degradación elegante si fuentes fallan"""
        query = "test query"
        context = {}
        
        # Mock some sources to fail
        with patch.object(
            multi_source_searcher,
            'search_single_source',
            side_effect=[None, None, SearchResult(
                source=multi_source_searcher.search_sources[0],
                content="Valid result",
                relevance_score=0.7,
                timestamp="2025-01-04T00:00:00Z",
                metadata={},
                citations=["http://source.com"]
            )]
        ):
            verified_info = await multi_source_searcher.search(query, context)
            
            # Sistema debe degradar pero aún retornar resultado
            assert verified_info is not None
            assert verified_info.sources_used >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
