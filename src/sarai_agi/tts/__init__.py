"""
TTS Streaming Module for SARAi v3.7.

Intelligent TTS streaming with minimal gaps and overlap prediction.

Components:
- SentenceSplitter: Smart sentence splitting
- TTSQueue: Streaming TTS with overlap prediction
- EWMA Predictor: Latency prediction for seamless playback

Version: v3.7.0
"""

from .sentence_splitter import SentenceSplitter, Sentence

__all__ = ['SentenceSplitter', 'Sentence']
__version__ = '3.7.0'
