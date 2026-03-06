"""Audio analysis for TransTools - pitch and acoustic features."""

from dataclasses import dataclass

import librosa
import numpy as np

from utils import AnalysisError, get_logger

logger = get_logger(__name__)


@dataclass
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
    mood: list[float]  # [happy, sad, angry]


def analyze_audio(
    audio: np.ndarray,
    sample_rate: int,
) -> VoiceAnalysisResult:
    """Analyze audio for pitch (F0) and energy.

    Args:
        audio: Float32 mono audio.
        sample_rate: Sample rate in Hz.

    Returns:
        VoiceAnalysisResult with pitch stats and energy.

    Raises:
        AnalysisError: If analysis fails.
    """
    try:
        # Resample to 22050 if needed (librosa works well at this rate)
        if sample_rate != 22050:
            audio = librosa.resample(
                audio.astype(np.float32),
                orig_sr=sample_rate,
                target_sr=22050,
            )
            sample_rate = 22050

        # Pitch (F0) via pyin
        f0, voiced_flag, voiced_probs = librosa.pyin(
            audio,
            fmin=librosa.note_to_hz("C2"),  # ~65 Hz
            fmax=librosa.note_to_hz("C7"),  # ~2093 Hz
            sr=sample_rate,
        )

        # Filter out unvoiced (NaN)
        f0_voiced = f0[~np.isnan(f0)]
        if len(f0_voiced) == 0:
            pitch_mean = 0.0
            pitch_std = 0.0
            pitch_min = 0.0
            pitch_max = 0.0
            logger.warning("No voiced frames detected in audio")
        else:
            pitch_mean = float(np.mean(f0_voiced))
            pitch_std = float(np.std(f0_voiced))
            pitch_min = float(np.min(f0_voiced))
            pitch_max = float(np.max(f0_voiced))

        # Energy RMS
        rms = librosa.feature.rms(y=audio)[0]
        energy_rms = float(np.mean(rms)) if len(rms) > 0 else 0.0

        mood = _estimate_mood_heuristic(
            pitch_std_hz=pitch_std,
            pitch_min_hz=pitch_min,
            pitch_max_hz=pitch_max,
            energy_rms=energy_rms,
        )

        return VoiceAnalysisResult(
            pitch_mean_hz=pitch_mean,
            pitch_std_hz=pitch_std,
            pitch_min_hz=pitch_min,
            pitch_max_hz=pitch_max,
            energy_rms=energy_rms,
            mood=mood,
        )
    except Exception as e:
        logger.exception("Analysis failed: %s", e)
        raise AnalysisError(f"Analysis failed: {e}") from e


def _estimate_mood_heuristic(
    pitch_std_hz: float,
    pitch_min_hz: float,
    pitch_max_hz: float,
    energy_rms: float,
) -> list[float]:
    """Estimate mood scores heuristically from acoustic features.

    This is a lightweight offline heuristic. It is not a medical model and should
    only be used as supportive trend data.

    Args:
        pitch_std_hz: Pitch standard deviation.
        pitch_min_hz: Minimum detected pitch.
        pitch_max_hz: Maximum detected pitch.
        energy_rms: RMS energy level.

    Returns:
        [happy, sad, angry] values normalized in 0..1.
    """
    energy_norm = max(0.0, min(1.0, energy_rms / 0.15))
    variation = max(0.0, min(1.0, pitch_std_hz / 70.0))
    spread = max(0.0, min(1.0, (pitch_max_hz - pitch_min_hz) / 260.0))

    happy = 0.15 + (0.55 * energy_norm) + (0.30 * variation)
    sad = 0.20 + (0.65 * (1.0 - energy_norm)) + (0.15 * (1.0 - variation))
    angry = 0.10 + (0.60 * energy_norm) + (0.30 * spread)

    values = [happy, sad, angry]
    values = [max(0.0, min(1.0, value)) for value in values]
    s = sum(values)
    if s == 0:
        return [0.0, 0.0, 0.0]
    return [value / s for value in values]
