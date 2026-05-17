"""Tests for voice privacy encryption."""

from __future__ import annotations

import os
import stat
from pathlib import Path
from uuid import uuid4

import pytest

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


@pytest.mark.skipif(os.name == "nt", reason="POSIX mode bits are not reliable on Windows")
def test_new_voice_key_is_private_on_posix() -> None:
    """Generated encryption keys should not be group/world-readable on POSIX systems."""
    output_dir = Path("output").resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    key_path = output_dir / f"privacy_{uuid4().hex}.key"
    try:
        VoicePrivacyService(key_path=key_path)

        mode = stat.S_IMODE(key_path.stat().st_mode)

        assert mode == 0o600
    finally:
        key_path.unlink(missing_ok=True)
