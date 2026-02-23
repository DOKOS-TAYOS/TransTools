"""Audio recording for TransTools."""

from typing import Optional

import numpy as np
import sounddevice as sd

from config.env import get_env_from_schema
from utils import RecordingError, get_logger

logger = get_logger(__name__)

DEFAULT_SAMPLE_RATE = 44100


def record_audio(
    duration_sec: Optional[float] = None,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
) -> tuple[np.ndarray, int]:
    """Record audio from default microphone.

    Args:
        duration_sec: Recording duration in seconds. If None, uses config.
        sample_rate: Sample rate in Hz.

    Returns:
        Tuple of (audio_data, sample_rate). audio_data is float32 mono.

    Raises:
        RecordingError: If recording fails.
    """
    if duration_sec is None:
        duration_sec = float(get_env_from_schema("RECORD_DURATION_SEC"))

    try:
        logger.info("Recording for %.1f seconds...", duration_sec)
        recording = sd.rec(
            int(duration_sec * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype="float32",
        )
        sd.wait()
        logger.info("Recording finished")
        return recording.flatten(), sample_rate
    except Exception as e:
        logger.exception("Recording failed: %s", e)
        raise RecordingError(f"Recording failed: {e}") from e
