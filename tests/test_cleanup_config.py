"""Tests for conservative cleanup and config behavior."""

from __future__ import annotations

import shutil
import tomllib
from pathlib import Path
from uuid import uuid4

from conftest import ROOT, _cleanup_temp_file

from config.env import ENV_SCHEMA, get_current_env_values, get_env_from_schema, write_env_file


def _make_workspace_temp_dir() -> Path:
    """Create a temporary directory inside the writable workspace."""
    temp_dir = (ROOT / "output" / f"cleanup_{uuid4().hex}").resolve()
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir


def test_get_current_env_values_omits_legacy_file_data_format() -> None:
    """Obsolete FILE_DATA_FORMAT should no longer be exposed by config helpers."""
    values = get_current_env_values()

    assert "FILE_DATA_FORMAT" not in values


def test_env_schema_only_keeps_new_visual_settings() -> None:
    """The public config schema should only expose the simplified appearance settings."""
    schema_keys = {item["key"] for item in ENV_SCHEMA}

    assert "UI_THEME_MODE" in schema_keys
    assert "UI_FONT_SIZE" in schema_keys
    assert "UI_BACKGROUND" not in schema_keys
    assert "UI_FOREGROUND" not in schema_keys
    assert "UI_BUTTON_BG" not in schema_keys
    assert "UI_BUTTON_WIDTH" not in schema_keys
    assert "UI_BUTTON_WIDTH_WIDE" not in schema_keys
    assert "UI_FONT_FAMILY" not in schema_keys
    assert "UI_PADDING" not in schema_keys


def test_get_env_from_schema_accepts_light_theme_mode(monkeypatch) -> None:
    """The new theme mode should accept the explicit light preset."""
    monkeypatch.setenv("UI_THEME_MODE", "light")

    assert get_env_from_schema("UI_THEME_MODE") == "light"


def test_get_env_from_schema_invalid_theme_mode_falls_back_to_dark(monkeypatch) -> None:
    """Invalid theme mode values should safely fall back to the default preset."""
    monkeypatch.setenv("UI_THEME_MODE", "sepia")

    assert get_env_from_schema("UI_THEME_MODE") == "dark"


def test_get_current_env_values_omits_legacy_visual_settings() -> None:
    """Only the simplified appearance keys should be emitted by config helpers."""
    values = get_current_env_values()

    assert values["UI_THEME_MODE"] in {"dark", "light"}
    assert "UI_FONT_SIZE" in values
    assert "UI_BACKGROUND" not in values
    assert "UI_FOREGROUND" not in values
    assert "UI_BUTTON_BG" not in values
    assert "UI_BUTTON_FG" not in values
    assert "UI_BUTTON_FG_CANCEL" not in values
    assert "UI_BUTTON_FG_ACCENT2" not in values
    assert "UI_BUTTON_WIDTH" not in values
    assert "UI_BUTTON_WIDTH_WIDE" not in values
    assert "UI_FONT_FAMILY" not in values
    assert "UI_PADDING" not in values


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
        assert "UI_THEME_MODE" not in content
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_write_env_file_ignores_legacy_visual_settings() -> None:
    """Writing .env should not re-emit removed appearance customization keys."""
    temp_dir = _make_workspace_temp_dir()
    try:
        env_path = temp_dir / ".env"

        write_env_file(
            env_path,
            {
                "LANGUAGE": "es",
                "UI_THEME_MODE": "light",
                "UI_FONT_SIZE": "18",
                "UI_BACKGROUND": "#ffffff",
                "UI_FONT_FAMILY": "Bahnschrift",
                "UI_PADDING": "10",
            },
        )

        content = env_path.read_text(encoding="utf-8")

        assert "UI_THEME_MODE=light" in content
        assert "UI_FONT_SIZE=18" in content
        assert "UI_BACKGROUND" not in content
        assert "UI_FONT_FAMILY" not in content
        assert "UI_PADDING" not in content
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


def test_locale_files_use_plain_utf8_without_bom() -> None:
    """Locale JSON files should stay portable UTF-8 files without a BOM prefix."""
    for locale_path in (ROOT / "src" / "locales").glob("*.json"):
        raw = locale_path.read_bytes()

        assert not raw.startswith(b"\xef\xbb\xbf"), f"{locale_path.name} should not contain BOM"
