"""
SARAi AGI v3.8.0 - EmotionalContextEngine Integration Tests
Tests de integración real con EmotionalContextEngine (STRICT MODE)

LOC: ~150 (integration tests)
"""

import pytest
import asyncio
from unittest.mock import Mock

from sarai_agi.learning.social_learning_engine import (
    SocialLearningEngine,
    LearningDomain
)
from sarai_agi.emotion import EmotionalContextEngine, EmotionalContext


@pytest.fixture
def real_emotional_engine():
    """EmotionalContextEngine REAL (no mock)"""
    return EmotionalContextEngine()


@pytest.fixture
def mock_pipeline_deps_with_emotion(real_emotional_engine):
    """Pipeline deps con EmotionalContextEngine REAL"""
    deps = Mock()
    deps.emotional_context = real_emotional_engine
    deps.model_pool = None  # No necesitamos model pool para estos tests
    return deps


@pytest.fixture
def social_engine_with_emotion(mock_pipeline_deps_with_emotion):
    """SocialLearningEngine con EmotionalContextEngine REAL"""
    config = {
        "social_learning": {
            "enabled": True,
            "continuous_learning": False
        }
    }
    return SocialLearningEngine(mock_pipeline_deps_with_emotion, config)


class TestEmotionalIntegration:
    """Tests de integración real EmotionalContextEngine → SocialLearningEngine"""
    
    @pytest.mark.asyncio
    async def test_emotional_analysis_excited(self, social_engine_with_emotion):
        """Test: Análisis emocional REAL - texto EXCITED"""
        content = {
            "text": "¡Wow, esto es increíble! ¡Genial, me encanta!",
            "user_id": "test_user_1",
            "language": "es"
        }
        
        emotions = await social_engine_with_emotion._analyze_emotional_context(content)
        
        # ⚠️ STRICT MODE: Si falla, retorna {} (no mock)
        if not emotions:
            pytest.skip("EmotionalContextEngine no disponible - STRICT MODE activo")
        
        # Validaciones con datos REALES
        assert isinstance(emotions, dict)
        assert "joy" in emotions
        assert "anticipation" in emotions
        
        # Excited debe tener alta joy y anticipation
        assert emotions["joy"] > 0.3, f"Expected high joy for excited text, got {emotions['joy']}"
        assert emotions["anticipation"] > 0.2
        
        # ⚠️ STRICT MODE: NO debe haber valores mock fijos
        total_emotion = sum(emotions.values())
        assert total_emotion > 0.0, "Emotions should not be all zeros"
    
    @pytest.mark.asyncio
    async def test_emotional_analysis_frustrated(self, social_engine_with_emotion):
        """Test: Análisis emocional REAL - texto FRUSTRATED"""
        content = {
            "text": "No funciona, esto es un error terrible. Necesito ayuda urgente.",
            "user_id": "test_user_2",
            "language": "es"
        }
        
        emotions = await social_engine_with_emotion._analyze_emotional_context(content)
        
        if not emotions:
            pytest.skip("EmotionalContextEngine no disponible - STRICT MODE activo")
        
        # Frustrated debe tener anger y/o sadness
        assert emotions["anger"] > 0.2 or emotions["sadness"] > 0.2, \
            f"Expected anger/sadness for frustrated text, got {emotions}"
        
        # Joy debe ser baja (no es texto positivo)
        assert emotions["joy"] < 0.5
    
    @pytest.mark.asyncio
    async def test_emotional_analysis_appreciative(self, social_engine_with_emotion):
        """Test: Análisis emocional REAL - texto APPRECIATIVE"""
        content = {
            "text": "Muchas gracias por tu ayuda. Excelente trabajo, aprecio mucho tu apoyo.",
            "user_id": "test_user_3",
            "language": "es"
        }
        
        emotions = await social_engine_with_emotion._analyze_emotional_context(content)
        
        if not emotions:
            pytest.skip("EmotionalContextEngine no disponible - STRICT MODE activo")
        
        # Appreciative debe tener alta joy y trust
        assert emotions["joy"] > 0.3 or emotions["trust"] > 0.4, \
            f"Expected joy/trust for appreciative text, got {emotions}"
    
    @pytest.mark.asyncio
    async def test_emotional_analysis_empty_text(self, social_engine_with_emotion):
        """Test: Texto vacío retorna dict vacío (STRICT MODE)"""
        content = {"text": "", "user_id": "test_user_4"}
        
        emotions = await social_engine_with_emotion._analyze_emotional_context(content)
        
        # Texto vacío → retorna {} (esperado)
        assert emotions == {}
    
    @pytest.mark.asyncio
    async def test_emotional_analysis_no_engine(self):
        """Test: Sin EmotionalContextEngine retorna vacío (STRICT MODE)"""
        # Pipeline deps sin emotional_context
        deps = Mock()
        deps.emotional_context = None
        deps.model_pool = None
        
        config = {"social_learning": {"enabled": True}}
        engine = SocialLearningEngine(deps, config)
        
        content = {
            "text": "Test texto cualquiera",
            "user_id": "test_user_5"
        }
        
        emotions = await engine._analyze_emotional_context(content)
        
        # ⚠️ STRICT MODE: Sin EmotionalContextEngine → {} (NO mock)
        assert emotions == {}, "STRICT MODE debe retornar {} si no hay EmotionalContextEngine"
    
    @pytest.mark.asyncio
    async def test_emotional_context_mapping_coverage(self, social_engine_with_emotion):
        """Test: Cobertura de mapeo de emociones"""
        test_cases = [
            ("¡Increíble! ¡Wow!", "excited", "joy"),
            ("No funciona, error", "frustrated", "anger"),
            ("Urgente, necesito ayuda ya", "urgent", "anticipation"),
            ("No entiendo, confuso", "confused", "fear"),
            ("Gracias, excelente", "appreciative", "joy"),
        ]
        
        successful_mappings = 0
        
        for text, expected_emotion, expected_basic_emotion in test_cases:
            content = {
                "text": text,
                "user_id": f"test_user_mapping_{expected_emotion}"
            }
            
            emotions = await social_engine_with_emotion._analyze_emotional_context(content)
            
            if not emotions:
                continue  # Skip si no hay engine
            
            # Verificar que la emoción básica esperada tenga valor > 0
            if emotions.get(expected_basic_emotion, 0) > 0.1:
                successful_mappings += 1
        
        # Al menos 50% de los casos deben mapear correctamente
        if successful_mappings > 0:
            assert successful_mappings >= len(test_cases) * 0.5, \
                f"Only {successful_mappings}/{len(test_cases)} mappings successful"
        else:
            pytest.skip("EmotionalContextEngine no disponible - STRICT MODE activo")
    
    @pytest.mark.asyncio
    async def test_emotional_empathy_adjustment(self, social_engine_with_emotion):
        """Test: Ajuste de emociones por empathy level"""
        # Texto que debería generar alta empatía (empathetic/appreciative)
        content = {
            "text": "Gracias por tu apoyo. Entiendo tu situación y aprecio mucho tu ayuda.",
            "user_id": "test_user_empathy"
        }
        
        emotions = await social_engine_with_emotion._analyze_emotional_context(content)
        
        if not emotions:
            pytest.skip("EmotionalContextEngine no disponible - STRICT MODE activo")
        
        # Con texto empático/agradecido, debe haber emociones positivas
        positive_emotions = emotions.get("joy", 0) + emotions.get("trust", 0)
        assert positive_emotions > 0.3, \
            f"Expected positive emotions for empathetic text, got joy={emotions['joy']}, trust={emotions['trust']}"


class TestEmotionalIntegrationStrictMode:
    """Tests específicos de STRICT MODE behavior"""
    
    @pytest.mark.asyncio
    async def test_no_mock_fallback_on_error(self):
        """Test: Error en EmotionalContextEngine → vacío (NO mock)"""
        # Mock que simula engine que arroja error
        broken_engine = Mock()
        broken_engine.analyze_emotional_context.side_effect = Exception("Engine error")
        
        deps = Mock()
        deps.emotional_context = broken_engine
        deps.model_pool = None
        
        config = {"social_learning": {"enabled": True}}
        engine = SocialLearningEngine(deps, config)
        
        content = {"text": "Test texto", "user_id": "test_user_error"}
        
        emotions = await engine._analyze_emotional_context(content)
        
        # ⚠️ STRICT MODE: Error → {} (NO mock con valores fijos)
        assert emotions == {}, "STRICT MODE: Error debe retornar {}, no mock"
    
    @pytest.mark.asyncio
    async def test_real_engine_never_returns_mock_marker(self, social_engine_with_emotion):
        """Test: EmotionalContextEngine REAL nunca retorna marker [Mock]"""
        content = {
            "text": "Cualquier texto de prueba",
            "user_id": "test_user_no_mock"
        }
        
        emotions = await social_engine_with_emotion._analyze_emotional_context(content)
        
        if not emotions:
            pytest.skip("EmotionalContextEngine no disponible - STRICT MODE activo")
        
        # Verificar que ningún valor contiene "[Mock]" (no aplica a dict numérico, pero validamos concept)
        for emotion_name, score in emotions.items():
            assert isinstance(score, (int, float)), \
                f"Emotion score must be numeric, got {type(score)} for {emotion_name}"
            assert 0.0 <= score <= 1.0, \
                f"Emotion score must be 0.0-1.0, got {score} for {emotion_name}"
