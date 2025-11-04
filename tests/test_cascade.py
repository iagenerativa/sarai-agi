"""
Tests for CASCADE Oracle System (ConfidenceRouter + ThinkModeClassifier)

Tests the 3-tier routing system (LFM2 → MiniCPM → Qwen-3) and think mode
classification.

Version: v3.5.1
"""

from unittest.mock import Mock

from sarai_agi.cascade import (
    ConfidenceRouter,
    ThinkModeClassifier,
    get_confidence_router,
    get_think_mode_classifier,
)

# ============================================================================
# ConfidenceRouter Tests
# ============================================================================

class TestConfidenceRouter:
    """Test CASCADE 3-tier routing logic"""

    def test_high_confidence_stays_lfm2(self):
        """Test high confidence query stays with LFM2"""
        router = ConfidenceRouter()

        decision = router.should_escalate(
            prompt="What is 2+2?",
            lfm2_response="4"
        )

        assert decision['target_model'] == 'lfm2'
        assert decision['reason'] == 'high_confidence'
        assert decision['confidence_score'] >= 0.6

    def test_low_confidence_escalates_qwen3(self):
        """Test low confidence escalates to Qwen-3"""
        router = ConfidenceRouter()

        decision = router.should_escalate(
            prompt="Explain quantum entanglement in detail",
            lfm2_response="I'm not sure about quantum physics..."
        )

        assert decision['target_model'] == 'qwen3'
        assert decision['reason'] == 'low_confidence'
        assert decision['confidence_score'] < 0.3

    def test_medium_confidence_uses_minicpm(self):
        """Test medium confidence uses MiniCPM"""
        router = ConfidenceRouter()

        # Medium length response, no strong signals
        decision = router.should_escalate(
            prompt="What is Python used for?",
            lfm2_response="Python is used for various things like web development"
        )

        # Should use MiniCPM or LFM2 (not Qwen-3)
        assert decision['target_model'] in ['lfm2', 'minicpm']
        assert decision['confidence_score'] >= 0.3

    def test_force_qwen_pattern(self):
        """Test force patterns bypass confidence check"""
        router = ConfidenceRouter()

        decision = router.should_escalate(
            prompt="Analiza en profundidad este problema",
            lfm2_response="This is a great answer"  # High confidence response
        )

        assert decision['target_model'] == 'qwen3'
        assert decision['reason'] == 'force_pattern_match'
        assert 'pattern' in decision

    def test_visual_input_routes_qwen3_vl(self):
        """Test visual input routes to Qwen3-VL"""
        router = ConfidenceRouter()

        decision = router.should_escalate(
            prompt="Describe what you see",
            lfm2_response="I see...",
            has_image=True
        )

        assert decision['target_model'] == 'qwen3_vl'
        assert decision['reason'] == 'visual_input'

    def test_visual_trigger_patterns(self):
        """Test visual trigger patterns without explicit image flag"""
        router = ConfidenceRouter()

        decision = router.should_escalate(
            prompt="Analiza este gráfico",
            lfm2_response="Response"
        )

        assert decision['target_model'] == 'qwen3_vl'
        assert decision['reason'] == 'visual_input'

    def test_confidence_calculation_low_patterns(self):
        """Test confidence decreases with uncertainty patterns"""
        router = ConfidenceRouter()

        # Response with uncertainty
        score = router._calculate_confidence(
            prompt="What is X?",
            response="I don't know, maybe it's something...",
            prompt_length=50
        )

        assert score < 0.5  # Low confidence

    def test_confidence_calculation_high_patterns(self):
        """Test confidence increases with certainty patterns"""
        router = ConfidenceRouter()

        # Definite answer
        score = router._calculate_confidence(
            prompt="Is 2+2=4?",
            response="Yes, definitely.",
            prompt_length=20
        )

        assert score > 0.7  # High confidence

    def test_short_response_long_prompt_penalty(self):
        """Test penalty for very short response to long prompt"""
        router = ConfidenceRouter()

        score = router._calculate_confidence(
            prompt="Explain in detail the theory of relativity and its implications...",
            response="Ok",
            prompt_length=150
        )

        assert score < 0.5  # Penalized for short response

    def test_should_use_vision_with_image_flag(self):
        """Test vision detection with explicit image flag"""
        router = ConfidenceRouter()

        result = router.should_use_vision("What's this?", has_image=True)

        assert result is True

    def test_should_use_vision_patterns(self):
        """Test vision detection with explicit patterns"""
        router = ConfidenceRouter()

        # Explicit pattern (verb + "la/el" + visual noun)
        assert router.should_use_vision("analiza la imagen de Python") is True
        assert router.should_use_vision("describe la foto del error") is True
        assert router.should_use_vision("qué hay en la imagen") is True

        # OCR pattern
        assert router.should_use_vision("lee el texto de la captura") is True

        # Multiple visual nouns (≥2 mentions triggers)
        assert router.should_use_vision("La imagen muestra un gráfico interesante") is True

        # No visual intent
        assert router.should_use_vision("Explain Python code") is False

    def test_should_use_code_expert_patterns(self):
        """Test code expert detection"""
        router = ConfidenceRouter()

        # Code generation
        assert router.should_use_code_expert("Genera función Python para fibonacci") is True

        # Debugging
        assert router.should_use_code_expert("Corrige este código con error") is True

        # Code block
        assert router.should_use_code_expert("```python\ndef test():\n    pass\n```") is True

        # Not code
        assert router.should_use_code_expert("What is Python?") is False

    def test_legacy_should_escalate_to_qwen(self):
        """Test backward compatibility method"""
        router = ConfidenceRouter()

        result = router.should_escalate_to_qwen(
            prompt="Test",
            lfm2_response="I don't know"
        )

        assert 'escalate' in result
        assert 'target_model' in result
        assert 'confidence_score' in result
        assert isinstance(result['escalate'], bool)

    def test_singleton_pattern(self):
        """Test get_confidence_router returns same instance"""
        router1 = get_confidence_router()
        router2 = get_confidence_router()

        assert router1 is router2


# ============================================================================
# ThinkModeClassifier Tests
# ============================================================================

class TestThinkModeClassifier:
    """Test Think Mode classification logic"""

    def test_simple_greeting_no_think(self):
        """Test simple greetings don't require think mode"""
        classifier = ThinkModeClassifier()

        assert classifier.classify("Hola") == "no_think"
        assert classifier.classify("Hello!") == "no_think"
        assert classifier.classify("Gracias") == "no_think"

    def test_complex_math_requires_think(self):
        """Test math problems require think mode"""
        classifier = ThinkModeClassifier()

        assert classifier.classify("Calcula la integral de x^2") == "think"
        assert classifier.classify("Resuelve 2x + 5 = 15") == "think"
        assert classifier.classify("What is 123 * 456?") == "think"

    def test_complex_programming_requires_think(self):
        """Test programming requests require think mode"""
        classifier = ThinkModeClassifier()

        assert classifier.classify("Implementa función para ordenar array") == "think"
        assert classifier.classify("Debug this code") == "think"
        assert classifier.classify("Optimiza el algoritmo") == "think"

    def test_analysis_requires_think(self):
        """Test analysis requests require think mode"""
        classifier = ThinkModeClassifier()

        assert classifier.classify("Analiza pros y contras de Python") == "think"
        assert classifier.classify("Compara Java y C++") == "think"
        assert classifier.classify("Explica por qué esto funciona") == "think"

    def test_length_fallback_short(self):
        """Test short prompts default to no_think in fallback"""
        classifier = ThinkModeClassifier()

        # Short ambiguous prompt
        result = classifier._classify_by_length("What?")

        assert result == "no_think"

    def test_length_fallback_long(self):
        """Test long prompts default to think in fallback"""
        classifier = ThinkModeClassifier()

        # Long prompt (>200 chars)
        long_prompt = "x" * 250
        result = classifier._classify_by_length(long_prompt)

        assert result == "think"

    def test_classify_with_tiny_mock(self):
        """Test classification with LFM2 (mocked)"""
        mock_pool = Mock()
        mock_tiny = Mock()
        mock_tiny.generate = Mock(return_value="COMPLEJA")
        mock_pool.get = Mock(return_value=mock_tiny)

        classifier = ThinkModeClassifier(model_pool=mock_pool)

        result = classifier._classify_with_tiny("Ambiguous query")

        assert result == "think"
        mock_pool.get.assert_called_once_with("tiny")

    def test_classify_with_tiny_simple_response(self):
        """Test classification recognizes SIMPLE response"""
        mock_pool = Mock()
        mock_tiny = Mock()
        mock_tiny.generate = Mock(return_value="SIMPLE")
        mock_pool.get = Mock(return_value=mock_tiny)

        classifier = ThinkModeClassifier(model_pool=mock_pool)

        result = classifier._classify_with_tiny("Simple query")

        assert result == "no_think"

    def test_classify_with_tiny_fallback_on_error(self):
        """Test fallback when LFM2 fails"""
        mock_pool = Mock()
        mock_pool.get = Mock(side_effect=Exception("Model not loaded"))

        classifier = ThinkModeClassifier(model_pool=mock_pool)

        # Should fallback to length-based classification
        result = classifier._classify_with_tiny("Short")

        assert result in ["think", "no_think"]

    def test_singleton_pattern(self):
        """Test get_think_mode_classifier returns same instance"""
        classifier1 = get_think_mode_classifier()
        classifier2 = get_think_mode_classifier()

        assert classifier1 is classifier2

    def test_code_block_pattern(self):
        """Test code blocks trigger think mode"""
        classifier = ThinkModeClassifier()

        code_query = """
Fix this code:
```python
def test():
    pass
```
"""

        assert classifier.classify(code_query) == "think"


# ============================================================================
# Integration Tests
# ============================================================================

class TestCascadeIntegration:
    """Test integration between router and classifier"""

    def test_router_and_classifier_together(self):
        """Test router and classifier work together"""
        router = get_confidence_router()
        classifier = get_think_mode_classifier()

        # Simple query
        decision = router.should_escalate("Hello", "Hi there!")
        think_mode = classifier.classify("Hello")

        assert decision['target_model'] == 'lfm2'
        assert think_mode == "no_think"

        # Complex query
        decision = router.should_escalate(
            "Solve x^2 + 5x + 6",
            "I'm not sure..."
        )
        think_mode = classifier.classify("Solve x^2 + 5x + 6")

        # Should escalate and use think mode
        assert decision['target_model'] in ['qwen3', 'minicpm']
        assert think_mode == "think"
