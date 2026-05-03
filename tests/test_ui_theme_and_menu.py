"""Tests for menu summary helpers, themed surface colors, and UI sizing."""

from __future__ import annotations

import tkinter
from pathlib import Path
from typing import Any, cast

import i18n
from config.theme import (
    UI_STYLE,
    ThemeChrome,
    ThemePreset,
    ThemeSizing,
    ThemeSurfacePalette,
    build_combobox_listbox_font_value,
    build_surface_palette,
    build_theme_chrome,
    build_theme_sizing,
    get_theme_preset,
    refresh_theme,
)
from frontend.ui_main_menu import build_menu_sections, get_summary_toggle_label
from frontend.window_utils import expand_window_size_to_requested_layout, fit_window_size_to_screen


class _FakeRequestedWindow:
    """Simple stand-in for requested-size window calculations."""

    def __init__(self, req_width: int, req_height: int) -> None:
        self._req_width = req_width
        self._req_height = req_height

    def winfo_reqwidth(self) -> int:
        """Return the requested width used by layout calculations."""
        return self._req_width

    def winfo_reqheight(self) -> int:
        """Return the requested height used by layout calculations."""
        return self._req_height


def test_get_theme_preset_returns_dark_mode_by_name() -> None:
    """Dark mode should remain a first-class fixed preset."""
    preset = get_theme_preset("dark")

    assert isinstance(preset, ThemePreset)
    assert preset.mode == "dark"
    assert preset.bg == "#10161B"
    assert preset.fg == "#F2F5F7"
    assert preset.button_bg == "#1E2D38"


def test_get_theme_preset_returns_light_mode_by_name() -> None:
    """Light mode should expose a distinct fixed preset for the whole UI."""
    preset = get_theme_preset("light")

    assert isinstance(preset, ThemePreset)
    assert preset.mode == "light"
    assert preset.bg == "#F5F7FA"
    assert preset.fg == "#16202A"
    assert preset.button_bg == "#DCE5EC"
    assert preset.chart_line == "#2E6F91"
    assert preset.calendar_activity_bg == "#D7EAF7"


def test_build_combobox_listbox_font_value_handles_system_font_names_with_spaces() -> None:
    """Combobox popdown font values must stay valid when the system font family contains spaces."""
    font_value = build_combobox_listbox_font_value("Segoe UI", 16)

    assert font_value == ("Segoe UI", 16)
    assert cast(Any, tkinter)._stringify(font_value) == "{{Segoe UI} 16}"


def test_build_surface_palette_uses_non_white_surface_colors() -> None:
    """Interactive surfaces should stay aligned with the active theme surfaces."""
    palette = build_surface_palette(bg="#10161B", btn_bg="#1E2D38", fg="#F2F5F7")

    assert isinstance(palette, ThemeSurfacePalette)
    assert palette.entry_bg == "#0d1216"
    assert palette.panel_bg == "#1e2328"
    assert palette.panel_alt_bg == "#2c3136"
    assert palette.hero_bg == "#1a3441"
    assert palette.muted_fg == "#b2b6b9"
    assert palette.tree_bg == palette.entry_bg
    assert palette.listbox_bg == palette.entry_bg
    assert palette.tree_selected_bg == "#1E2D38"


def test_build_surface_palette_uses_dark_borders_in_light_mode() -> None:
    """Light mode should still render shared widget borders with a dark contrasting stroke."""
    palette = build_surface_palette(bg="#F5F7FA", btn_bg="#DCE5EC", fg="#16202A")

    assert palette.panel_border == "#92989e"
    assert palette.listbox_border == "#92989e"


def test_build_theme_chrome_enables_visible_outlines_in_light_mode() -> None:
    """Light mode should outline cards and buttons instead of leaving them visually flat."""
    chrome = build_theme_chrome("light")

    assert isinstance(chrome, ThemeChrome)
    assert chrome.card_borderwidth == 1
    assert chrome.card_relief == "solid"
    assert chrome.button_borderwidth == 1
    assert chrome.button_relief == "solid"


def test_build_theme_sizing_derives_compact_defaults_from_font_size() -> None:
    """Shared sizing should be derived from the general font size only."""
    sizing = build_theme_sizing(font_size=16)

    assert isinstance(sizing, ThemeSizing)
    assert sizing.button_padding == (6, 4)
    assert sizing.summary_button_padding == (6, 3)
    assert sizing.notebook_tab_padding == (10, 5)
    assert sizing.tree_rowheight == 26
    assert sizing.spinbox_arrowsize == 19


def test_build_theme_sizing_scales_up_with_larger_fonts() -> None:
    """The derived metrics should grow when the user increases the base font size."""
    sizing = build_theme_sizing(font_size=24)

    assert sizing.button_padding == (9, 7)
    assert sizing.summary_button_padding == (9, 6)
    assert sizing.notebook_tab_padding == (13, 8)
    assert sizing.tree_rowheight == 37
    assert sizing.spinbox_arrowsize == 30


def test_refresh_theme_ignores_legacy_font_family_env(monkeypatch) -> None:
    """Theme refresh should resolve a system font instead of honoring removed env settings."""
    monkeypatch.setenv("UI_THEME_MODE", "light")
    monkeypatch.setenv("UI_FONT_SIZE", "18")
    monkeypatch.setenv("UI_FONT_FAMILY", "Imaginary Font")

    refresh_theme()

    assert UI_STYLE["theme_mode"] == "light"
    assert UI_STYLE["font_size"] == 18
    assert isinstance(UI_STYLE["font_family"], str)
    assert UI_STYLE["font_family"]
    assert UI_STYLE["font_family"] != "Imaginary Font"
    assert UI_STYLE["chart_line"] == "#2E6F91"
    assert UI_STYLE["calendar_activity_bg"] == "#D7EAF7"


def test_fit_window_size_to_screen_clamps_oversized_dialogs() -> None:
    """Requested window geometry should leave extra vertical room on smaller screens."""
    assert fit_window_size_to_screen(1240, 860, screen_width=1280, screen_height=800) == (
        1240,
        728,
    )


def test_expand_window_size_to_requested_layout_preserves_footer_space() -> None:
    """Dynamic dialogs should never be smaller than the layout Tk actually requests."""
    window = _FakeRequestedWindow(req_width=685, req_height=621)

    assert expand_window_size_to_requested_layout(window, 760, 617) == (760, 621)


def test_get_summary_toggle_label_closed_state_uses_expand_copy(
    monkeypatch,
) -> None:
    """Collapsed summary should invite the user to open it."""
    monkeypatch.setattr(i18n, "_current_lang", "es")

    assert get_summary_toggle_label(is_expanded=False) == "Mostrar resumen rápido"


def test_get_summary_toggle_label_open_state_uses_collapse_copy(
    monkeypatch,
) -> None:
    """Expanded summary should offer a hide action."""
    monkeypatch.setattr(i18n, "_current_lang", "en")

    assert get_summary_toggle_label(is_expanded=True) == "Hide quick summary"


def test_build_menu_sections_groups_actions_by_priority() -> None:
    """The premium landing page should separate primary, support, and utility actions."""
    sections = build_menu_sections()

    assert tuple(section["title_key"] for section in sections) == (
        "menu.section_capture",
        "menu.section_support",
        "menu.section_settings",
    )
    assert tuple(item["action_key"] for item in sections[0]["items"]) == (
        "voice_study",
        "medication",
        "other_records",
        "habits",
    )
    assert tuple(item["label_key"] for item in sections[2]["items"]) == (
        "menu.config",
        "menu.exit",
    )
    assert tuple(section["columns"] for section in sections) == (2, 1, 2)


def test_main_menu_keeps_companion_entry_only_in_support_section() -> None:
    """The landing page should not duplicate the companion entry outside the support section."""
    source = Path("src/frontend/ui_main_menu.py").read_text(encoding="utf-8")

    assert source.count('"action_key": "companion"') == 1
    assert 'text=t("menu.companion")' not in source
