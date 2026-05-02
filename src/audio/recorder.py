"""Audio recording for TransTools."""

from importlib import import_module
from typing import Optional, Protocol

import numpy as np

from config.env import get_env_from_schema
from utils import RecordingError, get_logger

logger = get_logger(__name__)

DEFAULT_SAMPLE_RATE = 44100


class SupportsSoundDevice(Protocol):
    """Minimal protocol for the sounddevice API used by the recorder."""

    def rec(
        self,
        frames: int,
        samplerate: int,
        channels: int,
        dtype: str,
    ) -> np.ndarray: ...

    def wait(self) -> None: ...


def _load_sounddevice() -> SupportsSoundDevice:
    """Load sounddevice lazily so non-recording flows do not require PortAudio."""
    try:
        return import_module("sounddevice")
    except (ImportError, OSError) as exc:
        logger.exception("Recording backend unavailable: %s", exc)
        raise RecordingError(
            "Recording backend unavailable: sounddevice/PortAudio is not installed or accessible."
        ) from exc


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
        sd = _load_sounddevice()
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
