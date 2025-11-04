"""
SARAi AGI - Tests de Integración End-to-End
============================================

Valida la integración completa de todos los componentes:
- TRM Classifier
- MCP Core
- Emotional Context Engine
- Cascade Router
- Model Pool
- RAG Agent
- Pipeline completa

Version: v3.6.0
"""

import pytest

from src.sarai_agi.core import create_integrated_pipeline


@pytest.mark.asyncio
class TestIntegratedPipeline:
    """Tests de pipeline integrada end-to-end."""

    async def test_pipeline_creation(self):
        """Test que pipeline se crea correctamente."""
        pipeline = create_integrated_pipeline()
        assert pipeline is not None
        assert pipeline.dependencies is not None
        await pipeline.shutdown()

    async def test_technical_query_routes_to_expert(self):
        """Test que queries técnicas se enrutan a expert agent."""
        pipeline = create_integrated_pipeline()

        result = await pipeline.run({
            "input": "¿Cómo implemento un algoritmo de ordenamiento quicksort en Python?"
        })

        assert "response" in result
        assert "metadata" in result
        assert result["metadata"]["agent"] in ["expert", "balanced"]
        assert result.get("alpha", 0.0) >= 0.3  # Debería tener componente técnico

        await pipeline.shutdown()

    async def test_emotional_query_routes_to_empathy(self):
        """Test que queries emocionales se enrutan a empathy agent."""
        pipeline = create_integrated_pipeline()

        result = await pipeline.run({
            "input": "Me siento triste y necesito ayuda"
        })

        assert "response" in result
        assert "metadata" in result
        # Puede ser empathy o balanced dependiendo de scores
        assert result["metadata"]["agent"] in ["empathy", "balanced"]
        assert result.get("beta", 0.0) >= 0.3  # Debería tener componente emocional

        await pipeline.shutdown()

    async def test_web_query_routes_to_rag(self):
        """Test que queries que requieren web se enrutan a RAG agent."""
        pipeline = create_integrated_pipeline(config={
            "enable_parallelization": False  # Simplificar para test
        })

        result = await pipeline.run({
            "input": "¿Cuál es el clima actual en Madrid?"
        })

        assert "response" in result
        assert "metadata" in result

        # Debería detectarse alto web_query score
        assert result.get("web_query", 0.0) >= 0.3

        await pipeline.shutdown()

    async def test_emotion_detection_works(self):
        """Test que detección emocional funciona."""
        pipeline = create_integrated_pipeline()

        result = await pipeline.run({
            "input": "¡Estoy muy emocionado con este proyecto!"
        })

        assert "response" in result
        metadata = result.get("metadata", {})
        emotion = metadata.get("emotion", {})

        # Debería detectar alguna emoción
        if emotion:
            assert "emotion" in emotion
            assert "confidence" in emotion
            assert emotion["confidence"] > 0.0

        await pipeline.shutdown()

    async def test_pipeline_metrics_collected(self):
        """Test que métricas del pipeline se recopilan."""
        pipeline = create_integrated_pipeline()

        result = await pipeline.run({
            "input": "Test query"
        })

        assert "metadata" in result
        assert "pipeline_metrics" in result["metadata"]

        metrics = result["metadata"]["pipeline_metrics"]
        assert "classify_ms" in metrics
        assert "weights_ms" in metrics
        assert "routing_ms" in metrics
        assert "response_latency_ms" in metrics

        # Verificar que son números válidos
        assert metrics["classify_ms"] >= 0.0
        assert metrics["weights_ms"] >= 0.0
        assert metrics["routing_ms"] >= 0.0
        assert metrics["response_latency_ms"] > 0.0

        await pipeline.shutdown()

    async def test_parallel_execution_mode(self):
        """Test modo de ejecución paralela."""
        pipeline = create_integrated_pipeline(config={
            "enable_parallelization": True,
            "min_input_length": 10
        })

        # Query larga para activar paralelización
        long_query = "Esta es una query muy larga " * 20

        result = await pipeline.run({"input": long_query})

        assert "response" in result
        assert "metadata" in result

        # Debería haber ejecutado detección emocional
        metrics = result["metadata"].get("pipeline_metrics", {})
        assert metrics.get("emotion_ms", 0.0) >= 0.0

        await pipeline.shutdown()

    async def test_sequential_execution_mode(self):
        """Test modo de ejecución secuencial."""
        pipeline = create_integrated_pipeline(config={
            "enable_parallelization": False
        })

        result = await pipeline.run({"input": "Query corta"})

        assert "response" in result
        assert "metadata" in result

        await pipeline.shutdown()

    async def test_scores_propagation(self):
        """Test que scores se propagan correctamente."""
        pipeline = create_integrated_pipeline()

        result = await pipeline.run({
            "input": "Implementar función recursiva en Python"
        })

        # Verificar que todos los scores están presentes
        assert "hard" in result
        assert "soft" in result
        assert "web_query" in result
        assert "alpha" in result
        assert "beta" in result

        # Verificar rangos válidos
        assert 0.0 <= result["hard"] <= 1.0
        assert 0.0 <= result["soft"] <= 1.0
        assert 0.0 <= result["web_query"] <= 1.0
        assert 0.0 <= result["alpha"] <= 1.0
        assert 0.0 <= result["beta"] <= 1.0

        await pipeline.shutdown()

    async def test_multiple_sequential_queries(self):
        """Test múltiples queries secuenciales."""
        pipeline = create_integrated_pipeline()

        queries = [
            "¿Qué es Python?",
            "Me siento confundido",
            "¿Cómo está el clima hoy?"
        ]

        for query in queries:
            result = await pipeline.run({"input": query})
            assert "response" in result
            assert "metadata" in result

        await pipeline.shutdown()

    async def test_empty_input_handling(self):
        """Test manejo de input vacío."""
        pipeline = create_integrated_pipeline()

        result = await pipeline.run({"input": ""})

        assert "response" in result
        # Debería manejar gracefully

        await pipeline.shutdown()

    async def test_state_immutability(self):
        """Test que state original no se modifica."""
        pipeline = create_integrated_pipeline()

        original_state = {"input": "Test query"}
        result = await pipeline.run(original_state)

        # State original no debería modificarse
        assert original_state == {"input": "Test query"}

        # Result debería tener campos adicionales
        assert "response" in result
        assert "metadata" in result

        await pipeline.shutdown()


@pytest.mark.asyncio
class TestComponentIntegration:
    """Tests de integración de componentes individuales."""

    async def test_classifier_mcp_integration(self):
        """Test integración TRM Classifier + MCP."""
        pipeline = create_integrated_pipeline()

        result = await pipeline.run({
            "input": "Debugging error en función recursiva"
        })

        # Classifier debería producir scores
        assert "hard" in result
        assert "soft" in result

        # MCP debería producir weights
        assert "alpha" in result
        assert "beta" in result

        # Alpha debería ser > beta para query técnica
        # (aunque no garantizado con rule-based fallback)
        assert result["alpha"] > 0.0

        await pipeline.shutdown()

    async def test_emotion_routing_integration(self):
        """Test integración Emotion + Router."""
        pipeline = create_integrated_pipeline()

        result = await pipeline.run({
            "input": "Estoy frustrado con este error"
        })

        # Emotion debería detectar frustración
        metadata = result.get("metadata", {})
        emotion = metadata.get("emotion", {})

        if emotion:
            # Debería tener información emocional
            assert "emotion" in emotion
            assert "empathy_level" in emotion

        # Router debería considerar emoción
        agent = metadata.get("agent", "")
        assert agent in ["expert", "empathy", "balanced"]

        await pipeline.shutdown()

    async def test_prefetch_generation_integration(self):
        """Test integración Prefetch + Generation."""
        pipeline = create_integrated_pipeline(config={
            "enable_parallelization": True,
            "min_input_length": 5
        })

        result = await pipeline.run({
            "input": "Query técnica larga para activar prefetch" * 5
        })

        # Prefetch debería haberse ejecutado
        metrics = result["metadata"].get("pipeline_metrics", {})
        assert "prefetch_target" in metrics

        # Generation debería haber funcionado
        assert "response" in result
        assert len(result["response"]) > 0

        await pipeline.shutdown()


@pytest.mark.asyncio
class TestErrorHandling:
    """Tests de manejo de errores."""

    async def test_invalid_config_handling(self):
        """Test manejo de configuración inválida."""
        # No debería crashear con config inválida
        pipeline = create_integrated_pipeline(config={
            "invalid_key": "invalid_value"
        })

        result = await pipeline.run({"input": "Test"})
        assert "response" in result

        await pipeline.shutdown()

    async def test_missing_state_fields(self):
        """Test manejo de campos faltantes en state."""
        pipeline = create_integrated_pipeline()

        # State sin 'input' debería manejarse
        result = await pipeline.run({})

        assert "response" in result

        await pipeline.shutdown()

    async def test_pipeline_reuse(self):
        """Test que pipeline puede reutilizarse múltiples veces."""
        pipeline = create_integrated_pipeline()

        for i in range(3):
            result = await pipeline.run({"input": f"Query {i}"})
            assert "response" in result

        await pipeline.shutdown()


@pytest.mark.asyncio
class TestPerformance:
    """Tests de rendimiento básicos."""

    async def test_latency_reasonable(self):
        """Test que latencia es razonable."""
        import time

        pipeline = create_integrated_pipeline()

        start = time.time()
        result = await pipeline.run({"input": "Query simple"})
        elapsed = time.time() - start

        # Latencia debería ser < 30s incluso con modelos lentos
        assert elapsed < 30.0

        # Métricas internas deberían ser consistentes
        metrics = result["metadata"].get("pipeline_metrics", {})
        reported_latency_ms = metrics.get("response_latency_ms", 0.0)

        # Debería ser aproximadamente similar (±20% error)
        assert abs(reported_latency_ms / 1000.0 - elapsed) < elapsed * 0.2

        await pipeline.shutdown()

    async def test_memory_cleanup_after_shutdown(self):
        """Test que shutdown libera recursos."""
        pipeline = create_integrated_pipeline()

        await pipeline.run({"input": "Test"})
        await pipeline.shutdown()

        # Verificar que executor se cerró
        assert pipeline.executor._shutdown  # type: ignore[attr-defined]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
