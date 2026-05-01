"""Tests for menu summary helpers, themed surface colors, and UI sizing."""

from __future__ import annotations

import i18n
from config.theme import ThemeSizing, ThemeSurfacePalette, build_surface_palette, build_theme_sizing
from frontend.ui_main_menu import get_summary_toggle_label
from frontend.window_utils import fit_window_size_to_screen


def test_build_surface_palette_uses_non_white_surface_colors() -> None:
    """Interactive surfaces should stay aligned with the dark theme."""
    palette = build_surface_palette(bg="#181818", btn_bg="#1F1F1F")

    assert isinstance(palette, ThemeSurfacePalette)
    assert palette.entry_bg == "#141414"
    assert palette.panel_bg != "#ffffff"
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
    """Requested window geometry should shrink when the screen is smaller."""
    assert fit_window_size_to_screen(1240, 860, screen_width=1280, screen_height=800) == (
        1240,
        760,
    )


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
