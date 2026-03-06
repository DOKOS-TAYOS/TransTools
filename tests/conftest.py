"""Shared pytest fixtures for TransTools."""

from __future__ import annotations

import sys
from pathlib import Path
from uuid import uuid4

import pytest

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from core.privacy import VoicePrivacyService  # noqa: E402
from core.repository import RepositoryPaths, StateRepository  # noqa: E402
from core.service import AppService  # noqa: E402


@pytest.fixture
def app_service() -> AppService:
    """Provide isolated AppService instance with temporary files."""
    output_dir = (ROOT / "output").resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    token = uuid4().hex
    state_file = output_dir / f"state_{token}.json"
    legacy_file = output_dir / f"legacy_{token}.json"
    key_file = output_dir / f"voice_{token}.key"
    repo = StateRepository(
        RepositoryPaths(
            state_file=state_file,
            legacy_file=legacy_file,
        )
    )
    privacy = VoicePrivacyService(key_path=key_file)
    service = AppService(
        repository=repo,
        privacy=privacy,
        contacts_seed_path=ROOT / "src" / "data" / "contacts_seed_es.json",
    )
    yield service
    for path in (state_file, legacy_file, key_file):
        try:
            path.unlink(missing_ok=True)
        except Exception:
            pass
