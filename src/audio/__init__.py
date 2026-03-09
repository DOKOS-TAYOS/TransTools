"""Audio module for TransTools."""

from core.types import VoiceAnalysisResult

from .analyzer import analyze_audio
from .recorder import record_audio

__all__ = ["VoiceAnalysisResult", "analyze_audio", "record_audio"]
