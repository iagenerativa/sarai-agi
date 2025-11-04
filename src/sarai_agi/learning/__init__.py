"""
SARAi AGI v3.7.0 - Learning Module
Social Learning + YouTube Analysis
"""

from .social_learning_engine import (
    SocialLearningEngine,
    LearningDomain,
    LearningInsight,
    DEFAULT_SOCIAL_LEARNING_CONFIG,
)

from .youtube_learning_system import (
    YouTubeLearningSystem,
    ContentCategory,
    YouTubeVideoAnalysis,
    DEFAULT_YOUTUBE_CONFIG,
)

__all__ = [
    "SocialLearningEngine",
    "LearningDomain",
    "LearningInsight",
    "YouTubeLearningSystem",
    "ContentCategory",
    "YouTubeVideoAnalysis",
    "DEFAULT_SOCIAL_LEARNING_CONFIG",
    "DEFAULT_YOUTUBE_CONFIG",
]
