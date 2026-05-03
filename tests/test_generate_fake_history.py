"""Tests for fake patient history generation."""

from __future__ import annotations

import importlib.util
import random
import sys
from datetime import date
from pathlib import Path
from types import ModuleType
from uuid import uuid4

from core.privacy import VoicePrivacyService

ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = ROOT / "scripts" / "generate_fake_history.py"
OUTPUT_DIR = ROOT / "output"


def _load_script_module() -> ModuleType:
    """Load the fake history script as an importable module for testing."""
    spec = importlib.util.spec_from_file_location("generate_fake_history_script", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Could not load script module from {SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _create_test_key_path() -> Path:
    """Create an isolated key path inside the workspace output directory."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR / f"fake-history-test-{uuid4().hex}.key"


def test_build_fake_history_matches_current_schema_and_reaches_today() -> None:
    """Generated history should cover today's range and include current record collections."""
    module = _load_script_module()
    key_path = _create_test_key_path()
    privacy = VoicePrivacyService(key_path=key_path)
    today = date(2026, 5, 3)
    try:
        history = module.build_fake_history(
            start=date(2026, 1, 1),
            end=today,
            privacy=privacy,
            catalog_ids=["hidratarse", "dormir", "caminar", "respirar"],
            existing_voice=[
                {
                    "id": "real-voice-1",
                    "recorded_at": "2026-05-02T10:30:00Z",
                    "target_date": "2026-05-02",
                    "energy_rms": 0.0031,
                    "mood_auto": {"happy": 0.2, "sad": 0.6, "angry": 0.2},
                    "mood_self": None,
                    "tone_encrypted": "preserved",
                    "audio_saved_path": "audio/real-voice-1.wav",
                }
            ],
            rng=random.Random(123),
        )

        assert history["schema_version"] == 1
        assert set(history["records"]) == {
            "appointment_preps",
            "habits",
            "medication",
            "milestones",
            "other_events",
            "roadmap_items",
            "visits",
            "voice",
            "wellbeing_logs",
        }
        assert max(row["date"] for row in history["records"]["medication"]) == today.isoformat()
        assert max(row["date"] for row in history["records"]["habits"]) == today.isoformat()
        assert any(row["id"] == "real-voice-1" for row in history["records"]["voice"])
        assert history["records"]["appointment_preps"]
        assert history["records"]["wellbeing_logs"]
        assert history["records"]["milestones"]
    finally:
        key_path.unlink(missing_ok=True)


def test_build_fake_history_keeps_upcoming_companion_items() -> None:
    """Generated history should include future-facing companion data for the dashboard."""
    module = _load_script_module()
    key_path = _create_test_key_path()
    privacy = VoicePrivacyService(key_path=key_path)
    today = date(2026, 5, 3)
    try:
        history = module.build_fake_history(
            start=date(2026, 1, 1),
            end=today,
            privacy=privacy,
            catalog_ids=["hidratarse", "dormir", "caminar", "respirar"],
            existing_voice=[],
            rng=random.Random(321),
        )

        assert any(
            row["target_date"] > today.isoformat() and not row["is_completed"]
            for row in history["records"]["appointment_preps"]
        )
    finally:
        key_path.unlink(missing_ok=True)
