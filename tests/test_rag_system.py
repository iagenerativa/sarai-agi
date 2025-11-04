"""
Tests para el sistema RAG (Web Cache + Web Audit + RAG Agent)

Suite de tests que valida:
- Web Cache: búsquedas, TTL, cache hit/miss
- Web Audit: logging SHA-256, HMAC, verificación de integridad
- RAG Agent: pipeline completo de 6 pasos con mocks
"""

import pytest
import json
import os
import tempfile
import hashlib
from datetime import datetime
from unittest.mock import Mock, patch

# Imports del sistema a testear
from sarai_agi.memory.web_cache import WebCache
from sarai_agi.memory.web_audit import WebAuditLogger
from sarai_agi.agents.rag import execute_rag, sentinel_response, SENTINEL_RESPONSES


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def temp_dir():
    """Directorio temporal para tests"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def mock_searxng_response():
    """Mock de respuesta exitosa de SearXNG"""
    return {
        "results": [
            {
                "title": "Clima en Tokio - AccuWeather",
                "url": "https://www.accuweather.com/tokyo",
                "content": "El clima en Tokio hoy es soleado con 22°C..."
            },
            {
                "title": "Pronóstico del tiempo en Tokio",
                "url": "https://weather.com/tokyo",
                "content": "Temperatura actual: 22°C. Máxima: 25°C, Mínima: 18°C..."
            },
            {
                "title": "Tokio Weather Forecast",
                "url": "https://openweather.org/tokyo",
                "content": "Clear skies, temperature 22°C, humidity 65%..."
            }
        ]
    }


@pytest.fixture
def web_cache(temp_dir):
    """Web Cache con directorio temporal"""
    cache = WebCache(
        searxng_url="http://localhost:8888",
        cache_dir=os.path.join(temp_dir, "web_cache"),
        ttl=3600
    )
    return cache


@pytest.fixture
def web_audit_logger(temp_dir):
    """Web Audit Logger con directorio temporal"""
    logger = WebAuditLogger(log_dir=os.path.join(temp_dir, "logs"))
    return logger


@pytest.fixture
def mock_model_pool():
    """Mock de ModelPool para tests de RAG Agent"""
    pool = Mock()

    # Mock del modelo expert que retorna una respuesta
    mock_model = Mock()
    mock_model.generate = Mock(return_value="Según las fuentes, el clima en Tokio es soleado con 22°C.")

    pool.get = Mock(return_value=mock_model)

    return pool


# ============================================================================
# TESTS WEB CACHE
# ============================================================================

class TestWebCache:
    """Tests para el módulo de Web Cache"""

    def test_cache_key_generation(self, web_cache):
        """Test: Normalización y generación de cache keys"""
        # Queries equivalentes deben generar la misma key
        query1 = "  ¿Cómo está el CLIMA en Tokio?  "
        query2 = "¿cómo está el clima en tokio?"

        key1 = web_cache._cache_key(query1)
        key2 = web_cache._cache_key(query2)

        assert key1 == key2, "Queries equivalentes deben tener la misma cache key"
        assert len(key1) == 64, "SHA-256 debe producir hash de 64 caracteres hex"

    def test_time_sensitive_detection(self, web_cache):
        """Test: Detección de queries time-sensitive"""
        time_sensitive = [
            "clima en Tokio",
            "precio de Bitcoin hoy",
            "noticias de ahora",
            "weather in London",
            "stock price AAPL"
        ]

        not_time_sensitive = [
            "historia de Roma",
            "tutorial de Python",
            "receta de paella",
            "quién fue Einstein"
        ]

        for query in time_sensitive:
            assert web_cache._is_time_sensitive(query), f"'{query}' debe ser time-sensitive"

        for query in not_time_sensitive:
            assert not web_cache._is_time_sensitive(query), f"'{query}' NO debe ser time-sensitive"

    @patch('sarai_agi.memory.web_cache.requests')
    def test_cache_miss_searxng_call(self, mock_requests, web_cache, mock_searxng_response):
        """Test: Cache miss debe llamar a SearXNG"""
        # Mock de requests.get
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json = Mock(return_value=mock_searxng_response)
        mock_requests.get = Mock(return_value=mock_response)

        # Primera búsqueda (cache miss)
        query = "¿Cómo está el clima en Tokio?"
        result = web_cache.get(query)

        # Verificaciones
        assert result is not None, "Debe retornar resultado"
        assert result["source"] == "searxng", "Fuente debe ser SearXNG"
        assert len(result["snippets"]) == 3, "Debe retornar 3 snippets (de 3 en mock)"
        assert result["query"] == query

        # Verificar que llamó a requests.get
        assert mock_requests.get.called, "Debe haber llamado a requests.get"

    @patch('sarai_agi.memory.web_cache.requests')
    def test_cache_hit_no_network_call(self, mock_requests, web_cache, mock_searxng_response):
        """Test: Cache hit NO debe llamar a SearXNG"""
        # Setup mock
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json = Mock(return_value=mock_searxng_response)
        mock_requests.get = Mock(return_value=mock_response)

        query = "¿Cómo está el clima en Tokio?"

        # Primera búsqueda (cache miss)
        result1 = web_cache.get(query)
        call_count_1 = mock_requests.get.call_count

        # Segunda búsqueda (cache hit)
        result2 = web_cache.get(query)
        call_count_2 = mock_requests.get.call_count

        # Verificaciones
        assert result1 is not None
        assert result2 is not None
        assert result2["source"] == "cache", "Segunda búsqueda debe ser desde cache"
        assert call_count_2 == call_count_1, "NO debe haber nueva llamada a SearXNG en cache hit"

    @patch('sarai_agi.memory.web_cache.is_safe_mode')
    def test_safe_mode_blocks_search(self, mock_safe_mode, web_cache):
        """Test: Safe Mode debe bloquear búsquedas web"""
        mock_safe_mode.return_value = True

        result = web_cache.get("¿Clima en Tokio?")

        assert result is None, "Safe Mode debe bloquear búsqueda (retornar None)"

    @patch('sarai_agi.memory.web_cache.requests')
    def test_searxng_timeout_handling(self, mock_requests, web_cache):
        """Test: Timeouts de SearXNG deben manejarse correctamente"""
        # Mock de timeout
        mock_requests.get = Mock(side_effect=mock_requests.Timeout("Connection timeout"))

        result = web_cache.get("¿Clima en Tokio?")

        assert result is None, "Timeout debe retornar None"

    def test_get_stats(self, web_cache):
        """Test: Estadísticas de cache"""
        stats = web_cache.get_stats()

        assert "size_bytes" in stats
        assert "entry_count" in stats
        assert "hit_rate" in stats


# ============================================================================
# TESTS WEB AUDIT
# ============================================================================

class TestWebAudit:
    """Tests para el módulo de Web Audit"""

    def test_log_web_query_creates_files(self, web_audit_logger):
        """Test: log_web_query debe crear archivos .jsonl y .sha256"""
        query = "¿Clima en Tokio?"
        search_results = {
            "source": "searxng",
            "snippets": [{"title": "Test", "url": "http://test.com", "content": "Test content"}]
        }

        web_audit_logger.log_web_query(
            query=query,
            search_results=search_results,
            response="Respuesta de prueba",
            llm_model="expert_short"
        )

        # Verificar que se crearon los archivos
        date = datetime.now().strftime("%Y-%m-%d")
        jsonl_path = os.path.join(web_audit_logger.log_dir, f"web_queries_{date}.jsonl")
        sha256_path = f"{jsonl_path}.sha256"

        assert os.path.exists(jsonl_path), "Debe crear archivo .jsonl"
        assert os.path.exists(sha256_path), "Debe crear archivo .sha256"

    def test_log_entry_structure(self, web_audit_logger):
        """Test: Estructura de entrada de log"""
        query = "Test query"
        search_results = {
            "source": "cache",
            "snippets": [
                {"title": "T1", "url": "http://1.com", "content": "C1"},
                {"title": "T2", "url": "http://2.com", "content": "C2"}
            ]
        }

        web_audit_logger.log_web_query(
            query=query,
            search_results=search_results,
            response="Test response",
            llm_model="expert_long"
        )

        # Leer el log
        date = datetime.now().strftime("%Y-%m-%d")
        jsonl_path = os.path.join(web_audit_logger.log_dir, f"web_queries_{date}.jsonl")

        with open(jsonl_path, "r") as f:
            line = f.readline()
            entry = json.loads(line)

        # Verificar campos
        assert entry["query"] == query
        assert entry["source"] == "cache"
        assert entry["snippets_count"] == 2
        assert len(entry["snippets_urls"]) == 2
        assert entry["synthesis_used"] is True
        assert entry["llm_model"] == "expert_long"
        assert "timestamp" in entry

    def test_sha256_verification(self, web_audit_logger):
        """Test: Verificación de integridad SHA-256"""
        query = "Verification test"
        search_results = {"source": "searxng", "snippets": []}

        web_audit_logger.log_web_query(
            query=query,
            search_results=search_results
        )

        # Verificar integridad
        date = datetime.now().strftime("%Y-%m-%d")
        is_valid = web_audit_logger.verify_integrity(date, log_type="web")

        assert is_valid, "Integridad debe ser válida"

    def test_corruption_detection(self, web_audit_logger):
        """Test: Detección de corrupción de logs"""
        query = "Corruption test"
        search_results = {"source": "searxng", "snippets": []}

        web_audit_logger.log_web_query(
            query=query,
            search_results=search_results
        )

        # Corromper el log (modificar una línea)
        date = datetime.now().strftime("%Y-%m-%d")
        jsonl_path = os.path.join(web_audit_logger.log_dir, f"web_queries_{date}.jsonl")

        with open(jsonl_path, "r") as f:
            line = f.read()

        # Modificar el log
        corrupted = line.replace(query, "CORRUPTED QUERY")

        with open(jsonl_path, "w") as f:
            f.write(corrupted)

        # Verificar (debe fallar)
        is_valid = web_audit_logger.verify_integrity(date, log_type="web")

        assert not is_valid, "Debe detectar corrupción"

    def test_voice_interaction_hmac(self, web_audit_logger):
        """Test: Logging de voz con HMAC"""
        input_audio_hash = hashlib.sha256(b"fake_audio_data").hexdigest()

        web_audit_logger.log_voice_interaction(
            input_audio_hash=input_audio_hash,
            detected_lang="es",
            engine_used="omni",
            response_text="Hola, ¿cómo estás?",
            hmac_secret="test-secret"
        )

        # Verificar que se crearon los archivos
        date = datetime.now().strftime("%Y-%m-%d")
        jsonl_path = os.path.join(web_audit_logger.log_dir, f"voice_interactions_{date}.jsonl")
        hmac_path = f"{jsonl_path}.hmac"

        assert os.path.exists(jsonl_path), "Debe crear archivo .jsonl de voz"
        assert os.path.exists(hmac_path), "Debe crear archivo .hmac"

    def test_anomaly_detection_trigger(self, web_audit_logger):
        """Test: Detección de anomalías debe trigger Safe Mode"""
        # Simular múltiples errores consecutivos
        for i in range(web_audit_logger.anomaly_threshold):
            web_audit_logger.log_web_query(
                query=f"Test query {i}",
                search_results=None,
                error="searxng_unavailable"
            )

        # Verificar que se incrementó el contador
        assert web_audit_logger.consecutive_errors >= web_audit_logger.anomaly_threshold


# ============================================================================
# TESTS RAG AGENT
# ============================================================================

class TestRAGAgent:
    """Tests para el RAG Agent"""

    def test_sentinel_response_structure(self):
        """Test: Estructura de respuestas Sentinel"""
        for reason in SENTINEL_RESPONSES.keys():
            response = sentinel_response(reason)

            assert "response" in response
            assert "sentinel_triggered" in response
            assert "sentinel_reason" in response
            assert "timestamp" in response
            assert response["sentinel_triggered"] is True
            assert response["sentinel_reason"] == reason

    @patch('sarai_agi.agents.rag.is_safe_mode')
    def test_safe_mode_triggers_sentinel(self, mock_safe_mode, mock_model_pool):
        """Test: Safe Mode debe trigger respuesta Sentinel"""
        mock_safe_mode.return_value = True

        state = {"input": "Test query"}
        result = execute_rag(state, mock_model_pool)

        assert result["sentinel_triggered"] is True
        assert result["sentinel_reason"] == "web_search_disabled"

    @patch('sarai_agi.agents.rag.cached_search')
    def test_search_failure_triggers_sentinel(self, mock_search, mock_model_pool):
        """Test: Fallo de búsqueda debe trigger Sentinel"""
        mock_search.return_value = None  # Simular fallo

        state = {"input": "Test query"}
        result = execute_rag(state, mock_model_pool)

        assert result["sentinel_triggered"] is True
        assert result["sentinel_reason"] == "web_search_failed"

    @patch('sarai_agi.agents.rag.cached_search')
    def test_zero_snippets_triggers_sentinel(self, mock_search, mock_model_pool):
        """Test: 0 snippets debe trigger Sentinel"""
        mock_search.return_value = {
            "source": "searxng",
            "snippets": []  # 0 snippets
        }

        state = {"input": "Test query"}
        result = execute_rag(state, mock_model_pool)

        assert result["sentinel_triggered"] is True
        assert result["sentinel_reason"] == "web_search_failed"

    @patch('sarai_agi.agents.rag.cached_search')
    @patch('sarai_agi.agents.rag.get_web_audit_logger')
    def test_successful_rag_pipeline(self, mock_audit, mock_search, mock_model_pool):
        """Test: Pipeline RAG exitoso completo"""
        # Mock de búsqueda exitosa
        mock_search.return_value = {
            "source": "searxng",
            "snippets": [
                {"title": "Test 1", "url": "http://1.com", "content": "Content 1"},
                {"title": "Test 2", "url": "http://2.com", "content": "Content 2"}
            ]
        }

        # Mock de audit logger
        mock_logger = Mock()
        mock_audit.return_value = mock_logger

        state = {"input": "¿Cómo está el clima en Tokio?"}
        result = execute_rag(state, mock_model_pool)

        # Verificaciones
        assert "response" in result
        assert result.get("sentinel_triggered", True) is False, "NO debe trigger Sentinel"
        assert "rag_metadata" in result
        assert result["rag_metadata"]["source"] == "searxng"
        assert result["rag_metadata"]["snippets_count"] == 2
        assert result["rag_metadata"]["llm_model"] in ["expert_short", "expert_long"]

        # Verificar que se llamó al modelo
        assert mock_model_pool.get.called

        # Verificar que se loggeó en audit
        assert mock_logger.log_web_query.called

    @patch('sarai_agi.agents.rag.cached_search')
    def test_long_prompt_uses_expert_long(self, mock_search, mock_model_pool):
        """Test: Prompts largos deben usar expert_long"""
        # Mock con muchos snippets (prompt largo)
        snippets = [
            {"title": f"Title {i}", "url": f"http://{i}.com", "content": "A" * 500}
            for i in range(5)  # 5 snippets de 500 chars cada uno
        ]

        mock_search.return_value = {
            "source": "searxng",
            "snippets": snippets
        }

        state = {"input": "Test query"}
        result = execute_rag(state, mock_model_pool)

        # Verificar que usó expert_long
        assert result["rag_metadata"]["llm_model"] == "expert_long"
        assert result["rag_metadata"]["prompt_length"] > 1500

    @patch('sarai_agi.agents.rag.cached_search')
    def test_model_unavailable_triggers_sentinel(self, mock_search, mock_model_pool):
        """Test: Modelo no disponible debe trigger Sentinel"""
        mock_search.return_value = {
            "source": "searxng",
            "snippets": [{"title": "T", "url": "http://t.com", "content": "C"}]
        }

        # Mock: modelo no disponible
        mock_model_pool.get = Mock(return_value=None)

        state = {"input": "Test query"}
        result = execute_rag(state, mock_model_pool)

        assert result["sentinel_triggered"] is True
        assert result["sentinel_reason"] == "model_unavailable"

    def test_empty_input_triggers_sentinel(self, mock_model_pool):
        """Test: Input vacío debe trigger Sentinel"""
        state = {"input": ""}
        result = execute_rag(state, mock_model_pool)

        assert result["sentinel_triggered"] is True


# ============================================================================
# TESTS DE INTEGRACIÓN
# ============================================================================

class TestRAGIntegration:
    """Tests de integración end-to-end"""

    @patch('sarai_agi.memory.web_cache.requests')
    @patch('sarai_agi.agents.rag.get_web_audit_logger')
    def test_full_pipeline_with_real_cache(
        self,
        mock_audit,
        mock_requests,
        temp_dir,
        mock_searxng_response,
        mock_model_pool
    ):
        """Test: Pipeline completo con cache real"""
        # Setup mock de requests
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json = Mock(return_value=mock_searxng_response)
        mock_requests.get = Mock(return_value=mock_response)

        # Setup mock de audit logger
        mock_logger = Mock()
        mock_audit.return_value = mock_logger

        # Crear cache real con temp dir
        from sarai_agi.memory import web_cache
        original_instance = web_cache._web_cache_instance
        web_cache._web_cache_instance = WebCache(
            cache_dir=os.path.join(temp_dir, "web_cache")
        )

        try:
            state = {"input": "¿Cómo está el clima en Tokio?"}
            result = execute_rag(state, mock_model_pool)

            # Verificar éxito
            assert result.get("sentinel_triggered", True) is False
            assert "response" in result
            assert result["rag_metadata"]["source"] == "searxng"

            # Segunda ejecución debe usar cache
            execute_rag(state, mock_model_pool)

            # El contador de llamadas a requests.get NO debe aumentar
            call_count = mock_requests.get.call_count

            # Tercera ejecución
            execute_rag(state, mock_model_pool)
            assert mock_requests.get.call_count == call_count, "Debe usar cache"

        finally:
            # Restaurar singleton
            web_cache._web_cache_instance = original_instance


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
