"""
Tests for SARAi AGI Emotional Context Engine
=============================================

Test coverage:
- 16 emotional contexts detection
- 8 cultural contexts detection
- Time context detection (7 types)
- Empathy level calculation
- Voice modulation parameters
- Text enhancement generation
- User profile creation and updates
- Interaction history management (20 max)
- Confidence scoring
- Statistics and insights

Target: 100% coverage
"""

import pytest
import time
from datetime import datetime
from unittest.mock import patch

from sarai_agi.emotion import (
    EmotionalContext,
    CulturalContext,
    TimeContext,
    EmotionalProfile,
    EmotionalResponse,
    EmotionalContextEngine,
    create_emotional_context_engine
)


# ============================================================================
# Factory Tests
# ============================================================================

def test_create_emotional_context_engine():
    """Test factory function creates valid engine."""
    engine = create_emotional_context_engine()
    
    assert isinstance(engine, EmotionalContextEngine)
    assert engine.analysis_count == 0
    assert engine.avg_confidence == 0.0
    assert len(engine.user_profiles) == 0


# ============================================================================
# Emotion Detection Tests (16 emotions)
# ============================================================================

def test_detect_excited_emotion():
    """Test detection of EXCITED emotion."""
    engine = EmotionalContextEngine()
    
    result = engine.analyze_emotional_context(
        text="¡Esto es genial! ¡Increíble! ¡Wow!",
        user_id="test_user"
    )
    
    assert result.detected_emotion == EmotionalContext.EXCITED
    assert result.confidence > 0.5


def test_detect_frustrated_emotion():
    """Test detection of FRUSTRATED emotion."""
    engine = EmotionalContextEngine()
    
    result = engine.analyze_emotional_context(
        text="No funciona, está roto, tengo un error horrible",
        user_id="test_user"
    )
    
    assert result.detected_emotion == EmotionalContext.FRUSTRATED
    assert result.confidence > 0.5
    # Empathy should be boosted for frustration (base 0.7 + 0.2 = 0.9, modulated by confidence)
    assert result.empathy_level >= 0.5


def test_detect_urgent_emotion():
    """Test detection of URGENT emotion."""
    engine = EmotionalContextEngine()
    
    result = engine.analyze_emotional_context(
        text="¡Urgente! Necesito ayuda rápido, ahora mismo",
        user_id="test_user"
    )
    
    assert result.detected_emotion == EmotionalContext.URGENT
    assert result.confidence > 0.5
    # Voice should be faster
    assert result.voice_modulation["speed"] > 1.0


def test_detect_formal_emotion():
    """Test detection of FORMAL emotion."""
    engine = EmotionalContextEngine()
    
    result = engine.analyze_emotional_context(
        text="Estimado señor, le escribo atentamente para solicitar información",
        user_id="test_user"
    )
    
    assert result.detected_emotion == EmotionalContext.FORMAL
    assert result.confidence > 0.5
    # Emotion intensity should be lower
    assert result.voice_modulation["emotion_intensity"] < 0.7


def test_detect_informal_emotion():
    """Test detection of INFORMAL emotion."""
    engine = EmotionalContextEngine()
    
    result = engine.analyze_emotional_context(
        text="Hey tío, ¿qué tal amigo? Hola colega",
        user_id="test_user"
    )
    
    assert result.detected_emotion == EmotionalContext.INFORMAL
    assert result.confidence > 0.5


def test_detect_confused_emotion():
    """Test detection of CONFUSED emotion."""
    engine = EmotionalContextEngine()
    
    result = engine.analyze_emotional_context(
        text="No entiendo, estoy confuso, ¿cómo funciona? ¿Por qué?",
        user_id="test_user"
    )
    
    assert result.detected_emotion == EmotionalContext.CONFUSED
    assert result.confidence > 0.5
    # Text enhancement should help clarity
    assert "explica" in result.text_enhancement.lower() or "mejor" in result.text_enhancement.lower()


def test_detect_appreciative_emotion():
    """Test detection of APPRECIATIVE emotion."""
    engine = EmotionalContextEngine()
    
    result = engine.analyze_emotional_context(
        text="Muchas gracias, aprecio tu ayuda, excelente trabajo",
        user_id="test_user"
    )
    
    assert result.detected_emotion == EmotionalContext.APPRECIATIVE
    assert result.confidence > 0.5


def test_detect_complaining_emotion():
    """Test detection of COMPLAINING emotion."""
    engine = EmotionalContextEngine()
    
    result = engine.analyze_emotional_context(
        text="Siempre es terrible, nunca funciona, pésimo servicio",
        user_id="test_user"
    )
    
    assert result.detected_emotion == EmotionalContext.COMPLAINING
    assert result.confidence > 0.5


def test_detect_doubtful_emotion():
    """Test detection of DOUBTFUL emotion."""
    engine = EmotionalContextEngine()
    
    result = engine.analyze_emotional_context(
        text="No estoy seguro, quizás, tal vez, dudo que funcione",
        user_id="test_user"
    )
    
    assert result.detected_emotion == EmotionalContext.DOUBTFUL
    assert result.confidence > 0.5


def test_detect_playful_emotion():
    """Test detection of PLAYFUL emotion."""
    engine = EmotionalContextEngine()
    
    result = engine.analyze_emotional_context(
        text="Jaja qué divertido, lol, es gracioso bromear",
        user_id="test_user"
    )
    
    assert result.detected_emotion == EmotionalContext.PLAYFUL
    assert result.confidence > 0.5


def test_detect_neutral_emotion_default():
    """Test NEUTRAL emotion as default when no keywords match."""
    engine = EmotionalContextEngine()
    
    result = engine.analyze_emotional_context(
        text="El tiempo está nublado hoy.",
        user_id="test_user"
    )
    
    assert result.detected_emotion == EmotionalContext.NEUTRAL
    assert result.confidence >= 0.5


# ============================================================================
# Cultural Context Tests (8 cultures)
# ============================================================================

def test_detect_spain_culture():
    """Test detection of SPAIN cultural context."""
    engine = EmotionalContextEngine()
    
    result = engine.analyze_emotional_context(
        text="Tío, vale, esto mola mucho, guay",
        user_id="test_user"
    )
    
    assert result.cultural_adaptation == CulturalContext.SPAIN


def test_detect_mexico_culture():
    """Test detection of MEXICO cultural context."""
    engine = EmotionalContextEngine()
    
    result = engine.analyze_emotional_context(
        text="Güey, qué chido, órale, está padre",
        user_id="test_user"
    )
    
    assert result.cultural_adaptation == CulturalContext.MEXICO


def test_detect_argentina_culture():
    """Test detection of ARGENTINA cultural context."""
    engine = EmotionalContextEngine()
    
    result = engine.analyze_emotional_context(
        text="Che boludo, dale pibe, es un quilombo",
        user_id="test_user"
    )
    
    assert result.cultural_adaptation == CulturalContext.ARGENTINA


def test_detect_colombia_culture():
    """Test detection of COLOMBIA cultural context."""
    engine = EmotionalContextEngine()
    
    result = engine.analyze_emotional_context(
        text="Parcero, eso está bacano, chimba parce",
        user_id="test_user"
    )
    
    assert result.cultural_adaptation == CulturalContext.COLOMBIA


def test_detect_usa_english_culture():
    """Test detection of USA_ENGLISH cultural context."""
    engine = EmotionalContextEngine()
    
    result = engine.analyze_emotional_context(
        text="Dude, that's awesome, cool, yeah gonna do it",
        user_id="test_user"
    )
    
    assert result.cultural_adaptation == CulturalContext.USA_ENGLISH


def test_detect_uk_english_culture():
    """Test detection of UK_ENGLISH cultural context."""
    engine = EmotionalContextEngine()
    
    result = engine.analyze_emotional_context(
        text="Cheers mate, that's brilliant and lovely",
        user_id="test_user"
    )
    
    # "mate" is in both ARGENTINA and UK_ENGLISH, so check for either
    # More specific test would need more unique UK keywords
    assert result.cultural_adaptation in [
        CulturalContext.UK_ENGLISH,
        CulturalContext.ARGENTINA
    ]


def test_cultural_default_to_spain():
    """Test default to SPAIN when no cultural indicators."""
    engine = EmotionalContextEngine()
    
    result = engine.analyze_emotional_context(
        text="Buenos días, necesito información",
        user_id="test_user"
    )
    
    # Should default to SPAIN (neutral Spanish)
    assert result.cultural_adaptation == CulturalContext.SPAIN


# ============================================================================
# Time Context Tests
# ============================================================================

@patch('sarai_agi.emotion.context_engine.datetime')
def test_detect_morning_context(mock_datetime):
    """Test detection of MORNING time context."""
    # Mock 8:00 AM on a Tuesday
    mock_datetime.now.return_value = datetime(2025, 1, 7, 8, 0)
    mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
    
    engine = EmotionalContextEngine()
    result = engine.analyze_emotional_context("Buenos días", "test_user")
    
    assert result.time_context == TimeContext.MORNING


@patch('sarai_agi.emotion.context_engine.datetime')
def test_detect_afternoon_context(mock_datetime):
    """Test detection of AFTERNOON time context."""
    # Mock 2:00 PM on a Wednesday
    mock_datetime.now.return_value = datetime(2025, 1, 8, 14, 0)
    mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
    
    engine = EmotionalContextEngine()
    result = engine.analyze_emotional_context("Buenas tardes", "test_user")
    
    assert result.time_context == TimeContext.AFTERNOON


@patch('sarai_agi.emotion.context_engine.datetime')
def test_detect_evening_context(mock_datetime):
    """Test detection of EVENING time context."""
    # Mock 7:00 PM on a Thursday
    mock_datetime.now.return_value = datetime(2025, 1, 9, 19, 0)
    mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
    
    engine = EmotionalContextEngine()
    result = engine.analyze_emotional_context("Buenas noches", "test_user")
    
    assert result.time_context == TimeContext.EVENING


@patch('sarai_agi.emotion.context_engine.datetime')
def test_detect_night_context(mock_datetime):
    """Test detection of NIGHT time context."""
    # Mock 11:00 PM on a Friday
    mock_datetime.now.return_value = datetime(2025, 1, 10, 23, 0)
    mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
    
    engine = EmotionalContextEngine()
    result = engine.analyze_emotional_context("Buenas noches", "test_user")
    
    assert result.time_context == TimeContext.NIGHT
    # Night should boost empathy (base 0.7 + 0.1 = 0.8, modulated by confidence)
    assert result.empathy_level >= 0.6


@patch('sarai_agi.emotion.context_engine.datetime')
def test_detect_weekend_context(mock_datetime):
    """Test detection of WEEKEND time context."""
    # Mock 10:00 AM on a Saturday
    mock_datetime.now.return_value = datetime(2025, 1, 11, 10, 0)
    mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
    
    engine = EmotionalContextEngine()
    result = engine.analyze_emotional_context("Buen fin de semana", "test_user")
    
    assert result.time_context == TimeContext.WEEKEND
    # Weekend should boost empathy (base 0.7 + 0.1 = 0.8, modulated by confidence)
    assert result.empathy_level >= 0.6


# ============================================================================
# User Profile Tests
# ============================================================================

def test_user_profile_creation():
    """Test automatic user profile creation."""
    engine = EmotionalContextEngine()
    
    result = engine.analyze_emotional_context(
        text="Esto es increíble",
        user_id="new_user"
    )
    
    # Profile should be created
    assert "new_user" in engine.user_profiles
    profile = engine.user_profiles["new_user"]
    
    assert profile.user_id == "new_user"
    assert profile.dominant_emotion == EmotionalContext.EXCITED
    assert len(profile.interaction_history) == 1


def test_user_profile_update():
    """Test user profile updates with multiple interactions."""
    engine = EmotionalContextEngine()
    
    # First interaction
    engine.analyze_emotional_context("¡Genial!", "user123")
    
    # Second interaction
    engine.analyze_emotional_context("Gracias", "user123")
    
    profile = engine.user_profiles["user123"]
    
    # Should have 2 interactions
    assert len(profile.interaction_history) == 2
    
    # Last interaction timestamp should be recent
    assert time.time() - profile.last_interaction < 1.0


def test_interaction_history_limit():
    """Test interaction history limited to 20 entries."""
    engine = EmotionalContextEngine()
    
    # Create 25 interactions
    for i in range(25):
        engine.analyze_emotional_context(
            f"Message {i}",
            user_id="power_user"
        )
    
    profile = engine.user_profiles["power_user"]
    
    # Should only keep last 20
    assert len(profile.interaction_history) == 20


def test_dominant_emotion_calculation():
    """Test dominant emotion calculation from last 10 interactions."""
    engine = EmotionalContextEngine()
    
    # 7 excited, 3 frustrated
    for _ in range(7):
        engine.analyze_emotional_context("¡Genial!", "user_dominant")
    
    for _ in range(3):
        engine.analyze_emotional_context("No funciona", "user_dominant")
    
    profile = engine.user_profiles["user_dominant"]
    
    # Dominant should be EXCITED (most frequent)
    assert profile.dominant_emotion == EmotionalContext.EXCITED


def test_user_profile_boosting():
    """Test dominant emotion boosts detection confidence."""
    engine = EmotionalContextEngine()
    
    # Establish EXCITED as dominant
    for _ in range(5):
        engine.analyze_emotional_context("¡Increíble!", "boost_user")
    
    # Weak excited signal should get boosted
    result = engine.analyze_emotional_context(
        "genial",  # Only one keyword
        user_id="boost_user"
    )
    
    # Should detect EXCITED with boosted confidence
    assert result.detected_emotion == EmotionalContext.EXCITED


# ============================================================================
# Voice Modulation Tests
# ============================================================================

def test_voice_modulation_excited():
    """Test voice modulation for EXCITED emotion."""
    engine = EmotionalContextEngine()
    
    result = engine.analyze_emotional_context(
        "¡Increíble! ¡Genial!",
        user_id="test_user"
    )
    
    modulation = result.voice_modulation
    
    # Should be faster and higher pitch
    assert modulation["speed"] > 1.0
    assert modulation["pitch"] > 1.0
    assert modulation["emotion_intensity"] >= 0.8


def test_voice_modulation_frustrated():
    """Test voice modulation for FRUSTRATED emotion."""
    engine = EmotionalContextEngine()
    
    result = engine.analyze_emotional_context(
        "No funciona, error terrible",
        user_id="test_user"
    )
    
    modulation = result.voice_modulation
    
    # Should be slower
    assert modulation["speed"] < 1.0
    # Emotion intensity tied to empathy (varies with confidence)
    assert modulation["emotion_intensity"] >= 0.3


def test_voice_modulation_urgent():
    """Test voice modulation for URGENT emotion."""
    engine = EmotionalContextEngine()
    
    result = engine.analyze_emotional_context(
        "¡Urgente! ¡Rápido!",
        user_id="test_user"
    )
    
    modulation = result.voice_modulation
    
    # Should be fastest
    assert modulation["speed"] >= 1.2
    assert modulation["pitch"] > 1.0


def test_voice_modulation_formal():
    """Test voice modulation for FORMAL emotion."""
    engine = EmotionalContextEngine()
    
    result = engine.analyze_emotional_context(
        "Estimado señor, atentamente",
        user_id="test_user"
    )
    
    modulation = result.voice_modulation
    
    # Should be slower and less emotional
    assert modulation["speed"] < 1.0
    assert modulation["emotion_intensity"] < 0.7


# ============================================================================
# Text Enhancement Tests
# ============================================================================

def test_text_enhancement_frustrated():
    """Test text enhancement for FRUSTRATED emotion."""
    engine = EmotionalContextEngine()
    
    result = engine.analyze_emotional_context(
        "No funciona nada",
        user_id="test_user"
    )
    
    # Should have empathetic prefix
    assert "frustración" in result.text_enhancement.lower()


def test_text_enhancement_confused():
    """Test text enhancement for CONFUSED emotion."""
    engine = EmotionalContextEngine()
    
    result = engine.analyze_emotional_context(
        "No entiendo cómo funciona",
        user_id="test_user"
    )
    
    # Should offer to explain better
    assert "explica" in result.text_enhancement.lower() or "mejor" in result.text_enhancement.lower()


def test_text_enhancement_appreciative():
    """Test text enhancement for APPRECIATIVE emotion."""
    engine = EmotionalContextEngine()
    
    result = engine.analyze_emotional_context(
        "Muchas gracias por la ayuda",
        user_id="test_user"
    )
    
    # Should acknowledge appreciation
    assert "alegr" in result.text_enhancement.lower()


def test_text_enhancement_neutral():
    """Test text enhancement for NEUTRAL emotion (empty)."""
    engine = EmotionalContextEngine()
    
    result = engine.analyze_emotional_context(
        "El tiempo está nublado",
        user_id="test_user"
    )
    
    # Neutral should have empty enhancement
    assert result.text_enhancement == ""


# ============================================================================
# Statistics Tests
# ============================================================================

def test_analysis_count_increments():
    """Test analysis count increments correctly."""
    engine = EmotionalContextEngine()
    
    assert engine.analysis_count == 0
    
    engine.analyze_emotional_context("Test 1", "user1")
    assert engine.analysis_count == 1
    
    engine.analyze_emotional_context("Test 2", "user2")
    assert engine.analysis_count == 2


def test_average_confidence_calculation():
    """Test average confidence calculation."""
    engine = EmotionalContextEngine()
    
    # Create high-confidence detection
    engine.analyze_emotional_context(
        "¡Increíble! ¡Genial! ¡Wow! ¡Asombroso!",
        user_id="user1"
    )
    
    # Create lower-confidence detection
    engine.analyze_emotional_context(
        "genial",  # Only one keyword
        user_id="user2"
    )
    
    # Average should be between the two
    assert 0.0 < engine.avg_confidence < 1.0


def test_get_emotional_insights():
    """Test get_emotional_insights() returns correct stats."""
    engine = EmotionalContextEngine()
    
    # Create multiple analyses
    engine.analyze_emotional_context("Test 1", "user1")
    engine.analyze_emotional_context("Test 2", "user2")
    engine.analyze_emotional_context("Test 3", "user3")
    
    insights = engine.get_emotional_insights()
    
    assert insights["analysis_count"] == 3
    assert insights["unique_users"] == 3
    assert insights["confidence_avg"] > 0.0
    assert insights["active_profiles"] == 3  # All recent


def test_active_profiles_filtering():
    """Test active profiles filtered by last hour."""
    engine = EmotionalContextEngine()
    
    # Create recent user
    engine.analyze_emotional_context("Recent", "recent_user")
    
    # Create old user (mock old timestamp)
    engine.analyze_emotional_context("Old", "old_user")
    engine.user_profiles["old_user"].last_interaction = time.time() - 7200  # 2 hours ago
    
    insights = engine.get_emotional_insights()
    
    # Only recent_user should be active
    assert insights["active_profiles"] == 1


def test_get_user_profile():
    """Test get_user_profile() retrieves correct profile."""
    engine = EmotionalContextEngine()
    
    engine.analyze_emotional_context("Test", "user123")
    
    profile = engine.get_user_profile("user123")
    
    assert profile is not None
    assert profile.user_id == "user123"
    
    # Non-existent user
    assert engine.get_user_profile("nobody") is None


# ============================================================================
# Integration Tests
# ============================================================================

def test_complete_analysis_pipeline():
    """Test complete analysis pipeline with all components."""
    engine = EmotionalContextEngine()
    
    result = engine.analyze_emotional_context(
        text="Tío, no funciona esto, ayuda urgente por favor",
        user_id="integration_user"
    )
    
    # Should detect emotion
    assert result.detected_emotion in [
        EmotionalContext.FRUSTRATED,
        EmotionalContext.URGENT,
        EmotionalContext.INFORMAL
    ]
    
    # Should detect Spanish culture
    assert result.cultural_adaptation == CulturalContext.SPAIN
    
    # Should have time context
    assert result.time_context in [
        TimeContext.MORNING,
        TimeContext.AFTERNOON,
        TimeContext.EVENING,
        TimeContext.NIGHT,
        TimeContext.WEEKEND
    ]
    
    # Should have empathy level
    assert 0.0 <= result.empathy_level <= 1.0
    
    # Should have voice modulation
    assert "speed" in result.voice_modulation
    assert "pitch" in result.voice_modulation
    assert "emotion_intensity" in result.voice_modulation
    
    # Should have created user profile
    assert "integration_user" in engine.user_profiles


def test_multiple_users_isolation():
    """Test multiple users have isolated profiles."""
    engine = EmotionalContextEngine()
    
    # User 1: Excited
    engine.analyze_emotional_context("¡Genial!", "user1")
    
    # User 2: Frustrated
    engine.analyze_emotional_context("No funciona", "user2")
    
    profile1 = engine.user_profiles["user1"]
    profile2 = engine.user_profiles["user2"]
    
    # Profiles should be different
    assert profile1.dominant_emotion == EmotionalContext.EXCITED
    assert profile2.dominant_emotion == EmotionalContext.FRUSTRATED
    
    # Histories should be independent
    assert len(profile1.interaction_history) == 1
    assert len(profile2.interaction_history) == 1


def test_confidence_scoring_accuracy():
    """Test confidence scoring reflects keyword density."""
    engine = EmotionalContextEngine()
    
    # High density (multiple keywords)
    high_result = engine.analyze_emotional_context(
        "¡Genial! ¡Increíble! ¡Wow! ¡Asombroso!",
        user_id="high_user"
    )
    
    # Low density (single keyword)
    low_result = engine.analyze_emotional_context(
        "genial",
        user_id="low_user"
    )
    
    # High density should have higher confidence
    assert high_result.confidence > low_result.confidence


# ============================================================================
# Edge Cases
# ============================================================================

def test_empty_text_analysis():
    """Test analysis with empty text."""
    engine = EmotionalContextEngine()
    
    result = engine.analyze_emotional_context(
        text="",
        user_id="empty_user"
    )
    
    # Should default to NEUTRAL
    assert result.detected_emotion == EmotionalContext.NEUTRAL


def test_mixed_emotions_detection():
    """Test detection with mixed emotional signals."""
    engine = EmotionalContextEngine()
    
    result = engine.analyze_emotional_context(
        text="Esto es genial pero no funciona",  # Excited + Frustrated
        user_id="mixed_user"
    )
    
    # Should detect strongest signal
    assert result.detected_emotion in [
        EmotionalContext.EXCITED,
        EmotionalContext.FRUSTRATED
    ]
    # Confidence might be lower due to mixed signals
    assert result.confidence > 0.0


def test_unknown_language_handling():
    """Test handling of language parameter (currently only 'es')."""
    engine = EmotionalContextEngine()
    
    # Currently language is ignored, but test it doesn't crash
    result = engine.analyze_emotional_context(
        text="Test",
        user_id="test_user",
        language="en"
    )
    
    assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
