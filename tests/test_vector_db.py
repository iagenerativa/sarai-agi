"""
Tests para el módulo Vector DB

Suite de tests que valida:
- Inicialización de backends (Qdrant, ChromaDB)
- Añadir documentos
- Búsqueda semántica top-k
- Estadísticas
- Gestión de colecciones
"""

import os
import tempfile
from unittest.mock import Mock, patch

import pytest

# Import del módulo a testear
from sarai_agi.memory.vector_db import VectorDB, get_vector_db

# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def temp_dir():
    """Directorio temporal para tests"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_documents():
    """Documentos de ejemplo para tests"""
    return [
        {
            "text": "SARAi es una AGI local híbrida",
            "metadata": {"source": "docs", "category": "intro"}
        },
        {
            "text": "El sistema usa modelos GGUF cuantizados",
            "metadata": {"source": "docs", "category": "tech"}
        },
        {
            "text": "Phoenix Skills son estrategias de prompting",
            "metadata": {"source": "docs", "category": "skills"}
        },
        {
            "text": "CASCADE ORACLE usa 3 tiers de modelos",
            "metadata": {"source": "docs", "category": "cascade"}
        },
        {
            "text": "RAG Agent integra búsqueda web con SearXNG",
            "metadata": {"source": "docs", "category": "rag"}
        }
    ]


# ============================================================================
# TESTS CHROMADB (sin dependencias externas)
# ============================================================================

class TestVectorDBChroma:
    """Tests para VectorDB con backend ChromaDB"""

    @pytest.mark.skipif(
        not os.getenv("TEST_CHROMA", "false").lower() == "true",
        reason="ChromaDB tests requieren chromadb instalado y TEST_CHROMA=true"
    )
    def test_chroma_initialization(self, temp_dir):
        """Test: Inicialización de ChromaDB"""
        db = VectorDB(
            backend="chroma",
            persist_directory=temp_dir,
            collection_name="test_collection"
        )

        assert db.backend == "chroma"
        assert db.collection_name == "test_collection"
        assert db.collection is not None

    @pytest.mark.skipif(
        not os.getenv("TEST_CHROMA", "false").lower() == "true",
        reason="ChromaDB tests requieren chromadb instalado"
    )
    def test_chroma_add_documents(self, temp_dir, sample_documents):
        """Test: Añadir documentos a ChromaDB"""
        db = VectorDB(
            backend="chroma",
            persist_directory=temp_dir
        )

        count = db.add_documents(sample_documents)

        assert count == len(sample_documents)

        # Verificar stats
        stats = db.get_stats()
        assert stats["count"] == len(sample_documents)
        assert stats["backend"] == "chroma"

    @pytest.mark.skipif(
        not os.getenv("TEST_CHROMA", "false").lower() == "true",
        reason="ChromaDB tests requieren chromadb instalado"
    )
    def test_chroma_search(self, temp_dir, sample_documents):
        """Test: Búsqueda semántica en ChromaDB"""
        db = VectorDB(
            backend="chroma",
            persist_directory=temp_dir
        )

        # Añadir documentos
        db.add_documents(sample_documents)

        # Buscar
        results = db.search("¿Qué es SARAi?", top_k=3)

        assert len(results) <= 3
        assert all("text" in r for r in results)
        assert all("score" in r for r in results)
        assert all("metadata" in r for r in results)

        # Verificar que retorna resultados ordenados por score
        if len(results) > 1:
            for i in range(len(results) - 1):
                assert results[i]["score"] >= results[i+1]["score"]


# ============================================================================
# TESTS QDRANT (con mocking)
# ============================================================================

class TestVectorDBQdrant:
    """Tests para VectorDB con backend Qdrant (mocked)"""

    @patch('sarai_agi.memory.vector_db.QdrantClient')
    def test_qdrant_initialization(self, mock_qdrant_client):
        """Test: Inicialización de Qdrant"""
        # Setup mock
        mock_client = Mock()
        mock_client.get_collections.return_value = Mock(collections=[])
        mock_qdrant_client.return_value = mock_client

        db = VectorDB(
            backend="qdrant",
            host="localhost",
            port=6333,
            collection_name="test_collection"
        )

        assert db.backend == "qdrant"
        assert db.collection_name == "test_collection"

        # Verificar que se llamó a create_collection
        assert mock_client.create_collection.called

    @patch('sarai_agi.memory.vector_db.QdrantClient')
    def test_qdrant_add_documents(self, mock_qdrant_client, sample_documents):
        """Test: Añadir documentos a Qdrant"""
        # Setup mock
        mock_client = Mock()
        mock_client.get_collections.return_value = Mock(collections=[])
        mock_qdrant_client.return_value = mock_client

        db = VectorDB(backend="qdrant")

        # Añadir documentos
        count = db.add_documents(sample_documents)

        assert count == len(sample_documents)
        assert mock_client.upsert.called

    @patch('sarai_agi.memory.vector_db.QdrantClient')
    def test_qdrant_search(self, mock_qdrant_client, sample_documents):
        """Test: Búsqueda en Qdrant"""
        # Setup mock
        mock_client = Mock()
        mock_client.get_collections.return_value = Mock(collections=[])

        # Mock de resultados de búsqueda
        mock_hit = Mock()
        mock_hit.score = 0.95
        mock_hit.payload = {
            "text": "SARAi es una AGI local",
            "metadata": {"source": "docs"},
            "timestamp": "2025-11-04T10:00:00"
        }
        mock_client.search.return_value = [mock_hit]

        mock_qdrant_client.return_value = mock_client

        db = VectorDB(backend="qdrant")

        # Buscar
        results = db.search("¿Qué es SARAi?", top_k=5)

        assert len(results) == 1
        assert results[0]["text"] == "SARAi es una AGI local"
        assert results[0]["score"] == 0.95
        assert mock_client.search.called


# ============================================================================
# TESTS GENERALES
# ============================================================================

class TestVectorDBGeneral:
    """Tests generales para VectorDB"""

    def test_invalid_backend(self):
        """Test: Backend inválido debe lanzar ValueError"""
        with pytest.raises(ValueError, match="Backend inválido"):
            VectorDB(backend="invalid_backend")

    def test_embedding_generation(self, temp_dir):
        """Test: Generación de embeddings dummy"""
        # Usar ChromaDB para test local (sin conexión externa)
        try:
            db = VectorDB(
                backend="chroma",
                persist_directory=temp_dir,
                embedding_dim=384
            )

            # Generar embedding
            text = "Test text for embedding"
            embedding = db._embed_text(text)

            # Verificar propiedades
            assert isinstance(embedding, list)
            assert len(embedding) == db.embedding_dim
            assert all(isinstance(x, float) for x in embedding)

            # Embedding debe ser determinístico
            embedding2 = db._embed_text(text)
            assert embedding == embedding2

        except ImportError:
            pytest.skip("ChromaDB no disponible")

    def test_empty_documents(self, temp_dir):
        """Test: Manejar lista vacía de documentos"""
        try:
            db = VectorDB(
                backend="chroma",
                persist_directory=temp_dir
            )

            count = db.add_documents([])
            assert count == 0

        except ImportError:
            pytest.skip("ChromaDB no disponible")

    def test_documents_without_text(self, temp_dir):
        """Test: Documentos sin campo 'text' deben ser omitidos"""
        try:
            db = VectorDB(
                backend="chroma",
                persist_directory=temp_dir
            )

            docs = [
                {"text": "Valid document"},
                {"metadata": {"source": "test"}},  # Sin texto
                {"text": "Another valid document"}
            ]

            count = db.add_documents(docs)

            # Solo debe añadir los 2 válidos
            assert count == 2

        except ImportError:
            pytest.skip("ChromaDB no disponible")

    @patch('sarai_agi.memory.vector_db.QdrantClient')
    def test_get_stats_qdrant(self, mock_qdrant_client):
        """Test: Estadísticas en Qdrant"""
        # Setup mock
        mock_client = Mock()
        mock_client.get_collections.return_value = Mock(collections=[])

        mock_collection_info = Mock()
        mock_collection_info.points_count = 42
        mock_client.get_collection.return_value = mock_collection_info

        mock_qdrant_client.return_value = mock_client

        db = VectorDB(backend="qdrant")
        stats = db.get_stats()

        assert stats["count"] == 42
        assert stats["backend"] == "qdrant"
        assert "embedding_dim" in stats


# ============================================================================
# TESTS SINGLETON
# ============================================================================

class TestVectorDBSingleton:
    """Tests para el patrón singleton"""

    def test_singleton_same_instance(self):
        """Test: get_vector_db debe retornar la misma instancia"""
        # Resetear singleton
        import sarai_agi.memory.vector_db as vdb_module
        vdb_module._vector_db_instance = None

        try:
            # Primera llamada
            with patch('sarai_agi.memory.vector_db.QdrantClient'):
                db1 = get_vector_db(backend="qdrant")

            # Segunda llamada
            db2 = get_vector_db()

            # Deben ser la misma instancia
            assert db1 is db2

        finally:
            # Limpiar singleton
            vdb_module._vector_db_instance = None

    def test_singleton_env_var(self):
        """Test: Leer backend desde variable de entorno"""
        import sarai_agi.memory.vector_db as vdb_module
        vdb_module._vector_db_instance = None

        try:
            # Configurar env var
            os.environ["VECTOR_DB_BACKEND"] = "chroma"

            with patch('sarai_agi.memory.vector_db.chromadb'):
                db = get_vector_db()

            assert db.backend == "chroma"

        finally:
            # Limpiar
            vdb_module._vector_db_instance = None
            if "VECTOR_DB_BACKEND" in os.environ:
                del os.environ["VECTOR_DB_BACKEND"]


# ============================================================================
# TESTS DE INTEGRACIÓN (opcionales)
# ============================================================================

@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("TEST_INTEGRATION", "false").lower() == "true",
    reason="Tests de integración requieren TEST_INTEGRATION=true y servicios corriendo"
)
class TestVectorDBIntegration:
    """Tests de integración con servicios reales"""

    def test_qdrant_real_connection(self):
        """Test: Conexión real a Qdrant"""
        # Requiere Qdrant corriendo en localhost:6333
        db = VectorDB(
            backend="qdrant",
            host="localhost",
            port=6333,
            collection_name="test_integration"
        )

        # Añadir documentos
        docs = [
            {"text": "Integration test document 1", "metadata": {"test": True}},
            {"text": "Integration test document 2", "metadata": {"test": True}}
        ]
        count = db.add_documents(docs)
        assert count == 2

        # Buscar
        results = db.search("integration test", top_k=5)
        assert len(results) > 0

        # Limpiar
        db.delete_collection()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
