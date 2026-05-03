"""Tests for the simplified configuration dialog helpers."""

from __future__ import annotations

from pathlib import Path
from tkinter import TclError

from frontend.ui_dialogs.config_dialog import (
    build_config_values_to_save,
    get_theme_mode_choices,
    run_profile_delete_flow,
    run_profile_export_flow,
    run_profile_import_flow,
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


def test_config_dialog_uses_explicit_checkbox_copy() -> None:
    """Boolean settings should explain the toggle action directly next to the checkbox."""
    source = Path("src/frontend/ui_dialogs/config_dialog.py").read_text(encoding="utf-8")
    es_locale = Path("src/locales/es.json").read_text(encoding="utf-8")
    en_locale = Path("src/locales/en.json").read_text(encoding="utf-8")

    assert 'text=t("config.general.save_audio_toggle")' in source
    assert 'text=t("config.general.log_console_toggle")' in source
    assert '"config.general.save_audio_toggle"' in es_locale
    assert '"config.general.log_console_toggle"' in es_locale
    assert '"config.general.save_audio_toggle"' in en_locale
    assert '"config.general.log_console_toggle"' in en_locale


def test_run_profile_export_flow_uses_selected_folder_and_reports_success(monkeypatch) -> None:
    """Export flow should pass the chosen directory to the profile exporter."""
    captured_path: Path | None = None
    captured_message: tuple[str, str] | None = None

    monkeypatch.setattr(
        "frontend.ui_dialogs.config_dialog.filedialog.askdirectory",
        lambda **kwargs: "C:/chosen",
    )

    def _fake_export_user_profile(export_root: Path) -> Path:
        nonlocal captured_path
        captured_path = export_root
        return export_root / "bundle"

    def _fake_showinfo(title: str, message: str, **kwargs: object) -> None:
        nonlocal captured_message
        captured_message = (title, message)

    monkeypatch.setattr(
        "frontend.ui_dialogs.config_dialog.export_user_profile",
        _fake_export_user_profile,
    )
    monkeypatch.setattr("frontend.ui_dialogs.config_dialog.messagebox.showinfo", _fake_showinfo)

    run_profile_export_flow(parent=None)

    assert captured_path == Path("C:/chosen")
    assert captured_message is not None
    assert "bundle" in captured_message[1]


def test_run_profile_import_flow_confirms_and_requests_restart(monkeypatch) -> None:
    """Import flow should confirm replacement, call the importer and request restart."""
    captured_path: Path | None = None
    captured_message: tuple[str, str] | None = None

    monkeypatch.setattr(
        "frontend.ui_dialogs.config_dialog.filedialog.askdirectory",
        lambda **kwargs: "C:/incoming",
    )
    monkeypatch.setattr(
        "frontend.ui_dialogs.config_dialog.messagebox.askyesno",
        lambda *args, **kwargs: True,
    )

    def _fake_import_user_profile(import_dir: Path) -> None:
        nonlocal captured_path
        captured_path = import_dir

    def _fake_showinfo(title: str, message: str, **kwargs: object) -> None:
        nonlocal captured_message
        captured_message = (title, message)

    monkeypatch.setattr(
        "frontend.ui_dialogs.config_dialog.import_user_profile",
        _fake_import_user_profile,
    )
    monkeypatch.setattr("frontend.ui_dialogs.config_dialog.messagebox.showinfo", _fake_showinfo)

    restart_required = run_profile_import_flow(parent=None)

    assert restart_required is True
    assert captured_path == Path("C:/incoming")
    assert captured_message is not None


def test_run_profile_import_flow_stops_when_user_cancels_confirmation(monkeypatch) -> None:
    """Import should not run when the replacement confirmation is rejected."""
    called = {"imported": False}

    monkeypatch.setattr(
        "frontend.ui_dialogs.config_dialog.filedialog.askdirectory",
        lambda **kwargs: "C:/incoming",
    )
    monkeypatch.setattr(
        "frontend.ui_dialogs.config_dialog.messagebox.askyesno",
        lambda *args, **kwargs: False,
    )
    monkeypatch.setattr(
        "frontend.ui_dialogs.config_dialog.import_user_profile",
        lambda import_dir: called.__setitem__("imported", True),
    )

    restart_required = run_profile_import_flow(parent=None)

    assert restart_required is False
    assert called["imported"] is False


def test_run_profile_delete_flow_requires_written_confirmation_and_restarts(
    monkeypatch,
) -> None:
    """Delete flow should require typing BORRAR before removing the profile."""
    calls: dict[str, object] = {}

    monkeypatch.setattr(
        "frontend.ui_dialogs.config_dialog.messagebox.askyesno",
        lambda *args, **kwargs: True,
    )
    monkeypatch.setattr(
        "frontend.ui_dialogs.config_dialog.simpledialog.askstring",
        lambda *args, **kwargs: "BORRAR",
    )
    monkeypatch.setattr(
        "frontend.ui_dialogs.config_dialog.delete_user_profile",
        lambda: calls.setdefault("deleted", True),
    )
    monkeypatch.setattr(
        "frontend.ui_dialogs.config_dialog.messagebox.showinfo",
        lambda title, message, **kwargs: calls.setdefault("message", (title, message)),
    )

    restart_required = run_profile_delete_flow(parent=None)

    assert restart_required is True
    assert calls["deleted"] is True


def test_run_profile_delete_flow_stops_when_user_cancels_first_confirmation(
    monkeypatch,
) -> None:
    """Delete should not run when the destructive confirmation is rejected."""
    called = {"deleted": False}

    monkeypatch.setattr(
        "frontend.ui_dialogs.config_dialog.messagebox.askyesno",
        lambda *args, **kwargs: False,
    )
    monkeypatch.setattr(
        "frontend.ui_dialogs.config_dialog.delete_user_profile",
        lambda: called.__setitem__("deleted", True),
    )

    restart_required = run_profile_delete_flow(parent=None)

    assert restart_required is False
    assert called["deleted"] is False


def test_run_profile_delete_flow_stops_when_written_confirmation_is_wrong(
    monkeypatch,
) -> None:
    """Delete should not run when the typed confirmation is missing or incorrect."""
    called = {"deleted": False}

    monkeypatch.setattr(
        "frontend.ui_dialogs.config_dialog.messagebox.askyesno",
        lambda *args, **kwargs: True,
    )
    monkeypatch.setattr(
        "frontend.ui_dialogs.config_dialog.simpledialog.askstring",
        lambda *args, **kwargs: "borrar",
    )
    monkeypatch.setattr(
        "frontend.ui_dialogs.config_dialog.delete_user_profile",
        lambda: called.__setitem__("deleted", True),
    )

    restart_required = run_profile_delete_flow(parent=None)

    assert restart_required is False
    assert called["deleted"] is False
