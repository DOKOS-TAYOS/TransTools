"""Tests for the simplified configuration dialog helpers."""

from __future__ import annotations

from pathlib import Path
from tkinter import TclError

from frontend.ui_dialogs.config_dialog import (
    build_config_values_to_save,
    get_theme_mode_choices,
)


class _BrokenTkInt:
    """Stand-in for a Tk variable that raises when read."""

    def get(self) -> int:
        """Raise the same error Tk emits for invalid numeric widget contents."""
        raise TclError("expected integer but got invalid text")


def test_get_theme_mode_choices_offer_day_and_night_modes() -> None:
    """The simplified UI should only expose the two supported theme presets."""
    assert get_theme_mode_choices() == (
        ("dark", "config.ui.theme_mode_dark"),
        ("light", "config.ui.theme_mode_light"),
    )


def test_build_config_values_to_save_keeps_only_supported_visual_keys() -> None:
    """Saving settings should persist only the new appearance contract."""
    values = build_config_values_to_save(
        {
            "LANGUAGE": "en",
            "FILE_OUTPUT_DIR": "output",
            "SAVE_AUDIO": "false",
            "RECORD_DURATION_SEC": "8",
            "LOG_LEVEL": "INFO",
            "LOG_CONSOLE": "false",
            "UI_BACKGROUND": "#10161B",
            "UI_BUTTON_WIDTH": "12",
            "UI_FONT_FAMILY": "Bahnschrift",
        },
        language="es",
        output_dir="custom-output",
        save_audio=True,
        record_duration_sec=12,
        log_level="debug",
        log_console=True,
        ui_theme_mode="light",
        ui_font_size=19,
    )

    assert values["LANGUAGE"] == "es"
    assert values["FILE_OUTPUT_DIR"] == "custom-output"
    assert values["SAVE_AUDIO"] == "true"
    assert values["RECORD_DURATION_SEC"] == "12"
    assert values["LOG_LEVEL"] == "DEBUG"
    assert values["LOG_CONSOLE"] == "true"
    assert values["UI_THEME_MODE"] == "light"
    assert values["UI_FONT_SIZE"] == "19"
    assert "UI_BACKGROUND" not in values
    assert "UI_BUTTON_WIDTH" not in values
    assert "UI_FONT_FAMILY" not in values


def test_build_config_values_to_save_normalizes_invalid_visual_inputs() -> None:
    """Invalid appearance values should fall back to the supported defaults."""
    values = build_config_values_to_save(
        {},
        language="",
        output_dir="",
        save_audio=False,
        record_duration_sec=400,
        log_level="",
        log_console=False,
        ui_theme_mode="sepia",
        ui_font_size=3,
    )

    assert values["LANGUAGE"] == "es"
    assert values["FILE_OUTPUT_DIR"] == "output"
    assert values["SAVE_AUDIO"] == "false"
    assert values["RECORD_DURATION_SEC"] == "60"
    assert values["LOG_LEVEL"] == "INFO"
    assert values["LOG_CONSOLE"] == "false"
    assert values["UI_THEME_MODE"] == "dark"
    assert values["UI_FONT_SIZE"] == "8"


def test_build_config_values_to_save_tolerates_invalid_tk_numeric_values() -> None:
    """Saving should keep working when a Tk numeric field currently contains invalid text."""
    values = build_config_values_to_save(
        {},
        language="es",
        output_dir="output",
        save_audio=False,
        record_duration_sec=_BrokenTkInt(),
        log_level="INFO",
        log_console=False,
        ui_theme_mode="dark",
        ui_font_size=_BrokenTkInt(),
    )

    assert values["RECORD_DURATION_SEC"] == "10"
    assert values["UI_FONT_SIZE"] == "16"


def test_config_dialog_uses_shared_combobox_factory() -> None:
    """Config dropdowns should go through the shared Combobox factory used elsewhere in the app."""
    source = Path("src/frontend/ui_dialogs/config_dialog.py").read_text(encoding="utf-8")

    assert "create_combobox(" in source
    assert "ttk.Combobox(" not in source
