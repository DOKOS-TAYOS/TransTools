"""Tests for full-profile export and import flows."""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import pytest
from conftest import ROOT

import core.profile_transfer as profile_transfer
from core.profile_transfer import delete_user_profile, export_user_profile, import_user_profile
from utils import DataStoreError

_VALID_KEY_NEW = "RZeTFqmP9EXwiLQvUK05RU3dPzPuvt1AqlmdcE_Kl8I="
_VALID_KEY_OLD = "UDAhcV8DAUwSFNQIszzbEmgDhviHdINDA9HLf_TLAf0="


def _write_text(path: Path, content: str) -> None:
    """Create a UTF-8 text file inside a test directory."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _make_workspace_temp_dir() -> Path:
    """Create a unique temporary directory inside the writable workspace."""
    temp_dir = (ROOT / "output" / f"profile_transfer_{uuid4().hex}").resolve()
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir


def test_export_user_profile_copies_profile_history_key_and_audio() -> None:
    """A profile export should copy the whole local dataset into a timestamped folder."""
    temp_dir = _make_workspace_temp_dir()
    try:
        source_dir = temp_dir / "source"
        export_root = temp_dir / "exports"
        _write_text(source_dir / "patient_profile.json", '{"name":"Alex"}')
        _write_text(source_dir / "patient_history.json", '{"records":[]}')
        _write_text(source_dir / ".voice_metrics.key", "secret-key")
        _write_text(source_dir / "audio" / "clip.wav", "fake-audio")

        exported_dir = export_user_profile(
            export_root=export_root,
            source_dir=source_dir,
            now=datetime(2026, 5, 3, 12, 34, 56),
        )

        assert exported_dir == export_root / "transtools_export_20260503_123456"
        assert (exported_dir / "patient_profile.json").read_text(
            encoding="utf-8"
        ) == '{"name":"Alex"}'
        assert (exported_dir / "patient_history.json").read_text(
            encoding="utf-8"
        ) == '{"records":[]}'
        assert (exported_dir / ".voice_metrics.key").read_text(encoding="utf-8") == "secret-key"
        assert (exported_dir / "audio" / "clip.wav").read_text(encoding="utf-8") == "fake-audio"
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_import_user_profile_replaces_existing_profile_and_audio() -> None:
    """Importing a profile should replace the local managed files completely."""
    temp_dir = _make_workspace_temp_dir()
    try:
        import_dir = temp_dir / "incoming"
        target_dir = temp_dir / "current"
        _write_text(import_dir / "patient_profile.json", '{"name":"New"}')
        _write_text(import_dir / "patient_history.json", '{"records":{"voice":[],"medication":[]}}')
        _write_text(import_dir / ".voice_metrics.key", _VALID_KEY_NEW)
        _write_text(import_dir / "audio" / "new.wav", "new-audio")

        _write_text(target_dir / "patient_profile.json", '{"name":"Old"}')
        _write_text(target_dir / "patient_history.json", '{"records":{"voice":[{"id":"old"}]}}')
        _write_text(target_dir / ".voice_metrics.key", _VALID_KEY_OLD)
        _write_text(target_dir / "audio" / "old.wav", "old-audio")

        import_user_profile(import_dir=import_dir, target_dir=target_dir)

        assert (target_dir / "patient_profile.json").read_text(encoding="utf-8") == '{"name":"New"}'
        assert (target_dir / "patient_history.json").read_text(
            encoding="utf-8"
        ) == '{"records":{"voice":[],"medication":[]}}'
        assert (target_dir / ".voice_metrics.key").read_text(encoding="utf-8") == _VALID_KEY_NEW
        assert (target_dir / "audio" / "new.wav").read_text(encoding="utf-8") == "new-audio"
        assert not (target_dir / "audio" / "old.wav").exists()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_import_user_profile_rejects_incomplete_export() -> None:
    """Import should fail fast when an export folder misses essential files."""
    temp_dir = _make_workspace_temp_dir()
    try:
        import_dir = temp_dir / "incoming"
        _write_text(import_dir / "patient_profile.json", '{"name":"Alex"}')
        _write_text(import_dir / ".voice_metrics.key", "secret-key")

        with pytest.raises(DataStoreError):
            import_user_profile(import_dir=import_dir, target_dir=temp_dir / "current")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_import_user_profile_rejects_invalid_json_bundle_without_touching_target() -> None:
    """Import should fail before mutating the target when profile JSON is corrupt."""
    temp_dir = _make_workspace_temp_dir()
    try:
        import_dir = temp_dir / "incoming"
        target_dir = temp_dir / "current"
        _write_text(import_dir / "patient_profile.json", '{"name":')
        _write_text(import_dir / "patient_history.json", '{"records":[]}')
        _write_text(
            import_dir / ".voice_metrics.key",
            "X5ZvTSD4F5wWq3Mf8lL4-b9r3oUQj4nmgz2BNo9U7j8=",
        )

        _write_text(target_dir / "patient_profile.json", '{"name":"Old"}')
        _write_text(target_dir / "patient_history.json", '{"records":{"voice":[{"id":"old"}]}}')
        _write_text(target_dir / ".voice_metrics.key", _VALID_KEY_OLD)

        with pytest.raises(DataStoreError):
            import_user_profile(import_dir=import_dir, target_dir=target_dir)

        assert (target_dir / "patient_profile.json").read_text(encoding="utf-8") == '{"name":"Old"}'
        assert (target_dir / "patient_history.json").read_text(
            encoding="utf-8"
        ) == '{"records":{"voice":[{"id":"old"}]}}'
        assert (target_dir / ".voice_metrics.key").read_text(encoding="utf-8") == _VALID_KEY_OLD
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_import_user_profile_rejects_invalid_key_bundle_without_touching_target() -> None:
    """Import should fail before mutating the target when the local key is unusable."""
    temp_dir = _make_workspace_temp_dir()
    try:
        import_dir = temp_dir / "incoming"
        target_dir = temp_dir / "current"
        _write_text(import_dir / "patient_profile.json", '{"name":"New"}')
        _write_text(import_dir / "patient_history.json", '{"records":{"voice":[],"medication":[]}}')
        _write_text(import_dir / ".voice_metrics.key", "not-a-valid-key")

        _write_text(target_dir / "patient_profile.json", '{"name":"Old"}')
        _write_text(target_dir / "patient_history.json", '{"records":{"voice":[{"id":"old"}]}}')
        _write_text(target_dir / ".voice_metrics.key", _VALID_KEY_OLD)

        with pytest.raises(DataStoreError):
            import_user_profile(import_dir=import_dir, target_dir=target_dir)

        assert (target_dir / "patient_profile.json").read_text(encoding="utf-8") == '{"name":"Old"}'
        assert (target_dir / "patient_history.json").read_text(
            encoding="utf-8"
        ) == '{"records":{"voice":[{"id":"old"}]}}'
        assert (target_dir / ".voice_metrics.key").read_text(encoding="utf-8") == _VALID_KEY_OLD
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_import_user_profile_rolls_back_when_a_replace_fails(monkeypatch) -> None:
    """Import should restore the previous profile when a managed replacement fails."""
    temp_dir = _make_workspace_temp_dir()
    try:
        import_dir = temp_dir / "incoming"
        target_dir = temp_dir / "current"
        _write_text(import_dir / "patient_profile.json", '{"name":"New"}')
        _write_text(import_dir / "patient_history.json", '{"records":{"voice":[],"medication":[]}}')
        _write_text(
            import_dir / ".voice_metrics.key",
            "X5ZvTSD4F5wWq3Mf8lL4-b9r3oUQj4nmgz2BNo9U7j8=",
        )
        _write_text(import_dir / "audio" / "new.wav", "new-audio")

        _write_text(target_dir / "patient_profile.json", '{"name":"Old"}')
        _write_text(target_dir / "patient_history.json", '{"records":{"voice":[{"id":"old"}]}}')
        _write_text(target_dir / ".voice_metrics.key", _VALID_KEY_OLD)
        _write_text(target_dir / "audio" / "old.wav", "old-audio")

        real_replace_file = profile_transfer._replace_file
        replace_calls = {"count": 0}

        def flaky_replace_file(source: Path, destination: Path) -> None:
            replace_calls["count"] += 1
            if replace_calls["count"] == 2:
                raise PermissionError("history file locked")
            real_replace_file(source, destination)

        monkeypatch.setattr(profile_transfer, "_replace_file", flaky_replace_file)

        with pytest.raises(DataStoreError):
            import_user_profile(import_dir=import_dir, target_dir=target_dir)

        assert (target_dir / "patient_profile.json").read_text(encoding="utf-8") == '{"name":"Old"}'
        assert (target_dir / "patient_history.json").read_text(
            encoding="utf-8"
        ) == '{"records":{"voice":[{"id":"old"}]}}'
        assert (target_dir / ".voice_metrics.key").read_text(encoding="utf-8") == _VALID_KEY_OLD
        assert (target_dir / "audio" / "old.wav").read_text(encoding="utf-8") == "old-audio"
        assert not (target_dir / "audio" / "new.wav").exists()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_delete_user_profile_removes_profile_history_key_and_audio() -> None:
    """Deleting a profile should clear all managed local user data."""
    temp_dir = _make_workspace_temp_dir()
    try:
        target_dir = temp_dir / "current"
        _write_text(target_dir / "patient_profile.json", '{"name":"Alex"}')
        _write_text(target_dir / "patient_history.json", '{"records":["day-1"]}')
        _write_text(target_dir / ".voice_metrics.key", "secret-key")
        _write_text(target_dir / "audio" / "clip.wav", "fake-audio")

        delete_user_profile(target_dir=target_dir)

        assert not (target_dir / "patient_profile.json").exists()
        assert not (target_dir / "patient_history.json").exists()
        assert not (target_dir / ".voice_metrics.key").exists()
        assert not (target_dir / "audio").exists()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
