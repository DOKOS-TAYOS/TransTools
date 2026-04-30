"""Tests for output path resolution, migration, and restart command building."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path
from uuid import uuid4

import main
from config.paths import get_output_dir, migrate_legacy_output_dir

ROOT = Path(__file__).resolve().parent.parent


def _make_workspace_temp_dir() -> Path:
    """Create a unique temporary directory inside the writable workspace."""
    temp_dir = (ROOT / "output" / f"test_{uuid4().hex}").resolve()
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir


def test_default_output_dir_uses_windows_appdata(monkeypatch) -> None:
    """Legacy default value should resolve to the user data directory on Windows."""
    base_dir = _make_workspace_temp_dir()
    try:
        monkeypatch.setenv("FILE_OUTPUT_DIR", "output")
        monkeypatch.setenv("APPDATA", str(base_dir / "AppData" / "Roaming"))
        monkeypatch.setattr(sys, "platform", "win32")

        resolved = get_output_dir()

        assert resolved == (base_dir / "AppData" / "Roaming" / "TransTools").resolve()
    finally:
        shutil.rmtree(base_dir, ignore_errors=True)


def test_explicit_output_dir_override_is_respected(monkeypatch) -> None:
    """Explicit FILE_OUTPUT_DIR should bypass the platform default directory."""
    base_dir = _make_workspace_temp_dir()
    try:
        custom_dir = (base_dir / "custom-output").resolve()
        monkeypatch.setenv("FILE_OUTPUT_DIR", str(custom_dir))
        monkeypatch.setenv("APPDATA", str(base_dir / "AppData" / "Roaming"))
        monkeypatch.setattr(sys, "platform", "win32")

        resolved = get_output_dir()

        assert resolved == custom_dir
    finally:
        shutil.rmtree(base_dir, ignore_errors=True)


def test_migrate_legacy_output_dir_copies_missing_files() -> None:
    """Legacy output files should be copied into the new user-data directory once."""
    base_dir = _make_workspace_temp_dir()
    try:
        legacy_dir = base_dir / "legacy-output"
        target_dir = base_dir / "user-data"
        legacy_dir.mkdir()
        legacy_files = {
            "patient_profile.json": '{"profile": "legacy"}',
            "patient_history.json": '{"records": {}}',
            ".voice_metrics.key": "secret\n",
            "trans_tools_data.json": '{"legacy": true}',
        }
        for filename, content in legacy_files.items():
            (legacy_dir / filename).write_text(content, encoding="utf-8")

        migrated = migrate_legacy_output_dir(legacy_dir=legacy_dir, target_dir=target_dir)

        assert {path.name for path in migrated} == set(legacy_files)
        for filename, content in legacy_files.items():
            assert (target_dir / filename).read_text(encoding="utf-8") == content
    finally:
        shutil.rmtree(base_dir, ignore_errors=True)


def test_migrate_legacy_output_dir_skips_existing_and_copies_missing_files() -> None:
    """Existing target files should be preserved while missing ones are still migrated."""
    base_dir = _make_workspace_temp_dir()
    try:
        legacy_dir = base_dir / "legacy-output"
        target_dir = base_dir / "user-data"
        legacy_dir.mkdir()
        target_dir.mkdir()
        (legacy_dir / "patient_profile.json").write_text('{"profile": "legacy"}', encoding="utf-8")
        (legacy_dir / "patient_history.json").write_text(
            '{"records": {"voice": []}}',
            encoding="utf-8",
        )
        existing_profile = target_dir / "patient_profile.json"
        existing_profile.write_text('{"profile": "current"}', encoding="utf-8")

        migrated = migrate_legacy_output_dir(legacy_dir=legacy_dir, target_dir=target_dir)

        assert [path.name for path in migrated] == ["patient_history.json"]
        assert existing_profile.read_text(encoding="utf-8") == '{"profile": "current"}'
        assert (target_dir / "patient_history.json").read_text(
            encoding="utf-8"
        ) == '{"records": {"voice": []}}'
    finally:
        shutil.rmtree(base_dir, ignore_errors=True)


def test_build_restart_command_uses_main_script_path(monkeypatch) -> None:
    """Restart command should relaunch the current main script, not sys.argv[0]."""
    monkeypatch.setattr(main.sys, "executable", "C:/Python/python.exe")
    monkeypatch.setattr(main.sys, "argv", ["transtools.exe"])

    command = main._build_restart_command()

    assert command[0] == "C:/Python/python.exe"
    assert Path(command[1]).resolve() == Path(main.__file__).resolve()
