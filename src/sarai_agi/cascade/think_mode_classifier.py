"""
Think Mode Classifier - Uses LFM2-1.2B to Decide Reasoning Activation

This module uses a tiny model (LFM2) to classify prompt complexity in <500ms,
determining whether to enable step-by-step reasoning mode for Qwen-3.

Philosophy
----------
- **Tiny model (LFM2)** classifies prompt complexity in <500ms
- **Simple queries** → /no_think (fast response)
- **Complex queries** → /think (step-by-step reasoning)
- **Minimal overhead** compared to total inference latency

Example
-------
>>> from sarai_agi.cascade import ThinkModeClassifier
>>>
>>> classifier = ThinkModeClassifier()
>>>
>>> # Simple query - no think mode needed
>>> mode = classifier.classify("Hello, how are you?")
>>> print(mode)
'no_think'
>>>
>>> # Complex query - enable think mode
>>> mode = classifier.classify("Solve the equation: x^2 + 5x + 6 = 0")
>>> print(mode)
'think'

Version: v3.5.1
"""

import re
from typing import Literal


class ThinkModeClassifier:
    """
    Classifies prompts by complexity to decide think_mode

    Uses LFM2-1.2B as fast classifier (<500ms) before calling Qwen-3-8B

    Classification Strategy
    -----------------------
    1. **Fast regex check** (0ms) - Pattern matching
    2. **LFM2 classification** (<500ms) - For ambiguous cases
    3. **Length fallback** - Conservative heuristic if LFM2 unavailable

    Attributes
    ----------
    COMPLEX_PATTERNS : list[str]
        Patterns that ALWAYS require reasoning
    SIMPLE_PATTERNS : list[str]
        Patterns that NEVER require reasoning
    model_pool : ModelPool, optional
        Instance of ModelPool to load LFM2
    """

    # Patterns that ALWAYS require reasoning
    COMPLEX_PATTERNS = [
        # Mathematics
        r"\b(?:calcula|resuelve|ecuación|integral|derivada|probabilidad)\b",
        r"\d+\s*[+\-*/^]\s*\d+",  # Numerical operations
        r"\b(?:demuestr[ae]|prueba que)\b",

        # Programming
        r"\b(?:implementa|crea función|algoritmo|debug|optimiza|refactoriza|refactor)\b",
        r"```[\w]*\n",  # Code blocks
        r"\b(?:mejora el código|mejor performance)\b",

        # Logic/Reasoning
        r"\b(?:analiza|compara|evalúa|deduce|infiere|razona)\b",
        r"\b(?:pros y contras|ventajas desventajas)\b",
        r"\b(?:paso a paso|step by step|detalladamente)\b",
        r"\b(?:por qué|why|cómo funciona|how (?:does|do))\b",

        # Complex problems
        r"\b(?:diseña|arquitectura|escalabilidad|trade[-\s]?off)\b",
        r"\b(?:explica.*detalle|explain.*detail)\b",
    ]

    # Patterns that NEVER require reasoning
    SIMPLE_PATTERNS = [
        r"^¿?(?:hola|hi|hello|hey)\b",  # Greetings (with/without ¿)
        r"^¿?(?:qué tal|cómo estás|how are you)\b",
        r"^(?:gracias|thanks|thank you)\b",
        r"^(?:sí|no|ok|vale|sure)\b",  # Confirmations
    ]

    def __init__(self, model_pool=None):
        """
        Initialize classifier

        Parameters
        ----------
        model_pool : ModelPool, optional
            Instance of ModelPool to load LFM2 for classification
        """
        self.model_pool = model_pool

    def classify(self, prompt: str) -> Literal["think", "no_think"]:
        """
        Classify if prompt requires deep reasoning

        Parameters
        ----------
        prompt : str
            Prompt text to classify

        Returns
        -------
        Literal["think", "no_think"]
            - "think": Requires step-by-step reasoning (complex)
            - "no_think": Fast response sufficient (simple)

        Examples
        --------
        >>> classifier = ThinkModeClassifier()
        >>> classifier.classify("Hello!")
        'no_think'
        >>> classifier.classify("Solve: x^2 + 5x + 6 = 0")
        'think'
        """
        # STEP 1: Fast check with regex (0ms)
        prompt_lower = prompt.lower().strip()

        # 1.1 Simple patterns (high confidence)
        for pattern in self.SIMPLE_PATTERNS:
            if re.search(pattern, prompt_lower, re.IGNORECASE):
                return "no_think"

        # 1.2 Complex patterns (high confidence)
        for pattern in self.COMPLEX_PATTERNS:
            if re.search(pattern, prompt_lower, re.IGNORECASE):
                return "think"

        # STEP 2: Classification with LFM2 (ambiguous cases, <500ms)
        if self.model_pool:
            return self._classify_with_tiny(prompt)

        # STEP 3: Fallback by length (without model_pool available)
        return self._classify_by_length(prompt)

    def _classify_with_tiny(self, prompt: str) -> Literal["think", "no_think"]:
        """
        Use LFM2-1.2B to classify complexity

        Prompt to tiny model::

            Classify this question as SIMPLE or COMPLEX:
            - SIMPLE: Direct response in <50 words
            - COMPLEX: Requires analysis, calculation, code or reasoning

            Question: {prompt}
            Classification:

        Parameters
        ----------
        prompt : str
            Text to classify

        Returns
        -------
        Literal["think", "no_think"]
            - "think" if response contains "COMPLEX"
            - "no_think" if response contains "SIMPLE"
        """
        try:
            # Load LFM2 on demand
            tiny = self.model_pool.get("tiny")

            classification_prompt = f"""Classify this question as SIMPLE or COMPLEX:
- SIMPLE: Direct response in <50 words (greetings, basic facts, confirmations)
- COMPLEX: Requires analysis, calculation, code, comparison or reasoning

Question: {prompt[:500]}

Classification (respond only SIMPLE or COMPLEX):"""

            # Fast inference (temperature=0 for determinism)
            response = tiny.generate(
                classification_prompt,
                max_tokens=10,
                temperature=0.0
            )

            response_text = response.strip().upper()

            # Parse response
            if "COMPLEJA" in response_text or "COMPLEX" in response_text:
                return "think"
            elif "SIMPLE" in response_text:
                return "no_think"
            else:
                # Fallback if ambiguous response
                return self._classify_by_length(prompt)

        except Exception as e:
            print(f"⚠️ ThinkClassifier tiny fallback: {e}")
            return self._classify_by_length(prompt)

    def _classify_by_length(self, prompt: str) -> Literal["think", "no_think"]:
        """
        Simple fallback by prompt length

        Conservative heuristic:

        - **<200 chars**: Probably simple → no_think
        - **≥200 chars**: Probably complex → think

        Parameters
        ----------
        prompt : str
            Text to classify

        Returns
        -------
        Literal["think", "no_think"]
            Classification based on length
        """
        return "think" if len(prompt) >= 200 else "no_think"


def get_think_mode_classifier(model_pool=None) -> ThinkModeClassifier:
    """
    Factory function to get classifier (singleton pattern)

    Parameters
    ----------
    model_pool : ModelPool, optional
        Instance of ModelPool for LFM2 access

    Returns
    -------
    ThinkModeClassifier
        Shared instance of ThinkModeClassifier

    Example
    -------
    >>> from sarai_agi.cascade import get_think_mode_classifier
    >>> classifier = get_think_mode_classifier()
    >>> mode = classifier.classify("Solve this equation: x + 5 = 10")
    >>> print(mode)
    'think'
    """
    if not hasattr(get_think_mode_classifier, '_classifier_instance'):
        get_think_mode_classifier._classifier_instance = ThinkModeClassifier(model_pool)

    return get_think_mode_classifier._classifier_instance
