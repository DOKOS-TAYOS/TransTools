"""Tests for voice privacy encryption."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from core.privacy import VoicePrivacyService


def test_encrypt_decrypt_roundtrip() -> None:
    """Encrypted payload should be recoverable."""
    output_dir = Path("output").resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    key_path = output_dir / f"privacy_{uuid4().hex}.bin"
    privacy = VoicePrivacyService(key_path=key_path)
    payload = {
        "pitch_mean_hz": 210.5,
        "pitch_std_hz": 34.1,
        "pitch_min_hz": 152.0,
        "pitch_max_hz": 264.7,
    }
    token = privacy.encrypt_metrics(payload)
    decoded = privacy.decrypt_metrics(token)

    assert decoded == payload
    assert token != str(payload)
    key_path.unlink(missing_ok=True)
