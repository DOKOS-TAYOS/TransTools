"""Tests for conservative cleanup and config behavior."""

from __future__ import annotations

import shutil
import tomllib
from pathlib import Path
from uuid import uuid4

from conftest import ROOT, _cleanup_temp_file

from config.env import get_current_env_values, write_env_file


def _make_workspace_temp_dir() -> Path:
    """Create a temporary directory inside the writable workspace."""
    temp_dir = (ROOT / "output" / f"cleanup_{uuid4().hex}").resolve()
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir


def test_get_current_env_values_omits_legacy_file_data_format() -> None:
    """Obsolete FILE_DATA_FORMAT should no longer be exposed by config helpers."""
    values = get_current_env_values()

    assert "FILE_DATA_FORMAT" not in values


def test_write_env_file_ignores_legacy_file_data_format() -> None:
    """Writing .env should not re-emit obsolete FILE_DATA_FORMAT entries."""
    temp_dir = _make_workspace_temp_dir()
    try:
        env_path = temp_dir / ".env"

        write_env_file(
            env_path,
            {
                "LANGUAGE": "es",
                "FILE_DATA_FORMAT": "json",
                "SAVE_AUDIO": "true",
            },
        )

        content = env_path.read_text(encoding="utf-8")

        assert "LANGUAGE=es" in content
        assert "SAVE_AUDIO=true" in content
        assert "FILE_DATA_FORMAT" not in content
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_cleanup_temp_file_swallows_os_errors_for_non_files() -> None:
    """Fixture cleanup helper should tolerate paths that cannot be unlinked as files."""
    temp_dir = _make_workspace_temp_dir()
    try:
        folder_path = temp_dir / "not-a-file"
        folder_path.mkdir()

        _cleanup_temp_file(folder_path)

        assert folder_path.exists()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_pyproject_disables_cacheprovider_for_clean_windows_runs() -> None:
    """Pytest should disable cacheprovider to avoid Windows cache permission warnings."""
    pyproject_data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    pytest_options = pyproject_data["tool"]["pytest"]["ini_options"]

    assert pytest_options["addopts"] == "-p no:cacheprovider"
