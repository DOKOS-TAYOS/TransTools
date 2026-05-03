"""Tests for menu summary helpers, themed surface colors, and UI sizing."""

from __future__ import annotations

import i18n
from config.theme import ThemeSizing, ThemeSurfacePalette, build_surface_palette, build_theme_sizing
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


def test_build_surface_palette_uses_non_white_surface_colors() -> None:
    """Interactive surfaces should stay aligned with the dark theme."""
    palette = build_surface_palette(bg="#181818", btn_bg="#1F1F1F")

    assert isinstance(palette, ThemeSurfacePalette)
    assert palette.entry_bg == "#141414"
    assert palette.panel_bg == "#252525"
    assert palette.panel_alt_bg == "#333333"
    assert palette.hero_bg == "#20363f"
    assert palette.muted_fg == "#999999"
    assert palette.tree_bg == palette.entry_bg
    assert palette.listbox_bg == palette.entry_bg
    assert palette.tree_selected_bg == "#1F1F1F"


def test_build_theme_sizing_prefers_compact_defaults_for_dense_windows() -> None:
    """Shared sizing should stay readable without crowding dense dialogs."""
    sizing = build_theme_sizing(font_size=16, padding=6)

    assert isinstance(sizing, ThemeSizing)
    assert sizing.button_padding == (6, 4)
    assert sizing.summary_button_padding == (6, 3)
    assert sizing.notebook_tab_padding == (10, 5)
    assert sizing.tree_rowheight == 26
    assert sizing.spinbox_arrowsize == 19


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
