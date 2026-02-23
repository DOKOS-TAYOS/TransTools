"""Audio module for TransTools."""

from .analyzer import VoiceAnalysisResult, analyze_audio
from .recorder import record_audio

__all__ = ["VoiceAnalysisResult", "analyze_audio", "record_audio"]
