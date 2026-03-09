"""Shared domain types for TransTools."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VoiceAnalysisResult:
    """Result of voice analysis.

    Attributes:
        pitch_mean_hz: Mean pitch (F0) in Hz.
        pitch_std_hz: Pitch standard deviation in Hz.
        pitch_min_hz: Minimum pitch in Hz.
        pitch_max_hz: Maximum pitch in Hz.
        energy_rms: RMS energy value.
        mood: [happy, sad, angry] scores in 0..1 range.
    """

    pitch_mean_hz: float
    pitch_std_hz: float
    pitch_min_hz: float
    pitch_max_hz: float
    energy_rms: float
    mood: list[float]
