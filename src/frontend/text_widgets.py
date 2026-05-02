"""Helpers for multiline text widgets."""

from __future__ import annotations

from tkinter import Text

from config import UI_STYLE
from config.theme import _adjust_hex_brightness, get_surface_palette


def configure_notes_widget(widget: Text) -> None:
    """Apply project colors to multiline notes widgets."""
    palette = get_surface_palette()
    border_color = palette.panel_border
    widget.configure(
        background=palette.entry_bg,
        foreground=UI_STYLE["fg"],
        insertbackground=UI_STYLE["fg"],
        selectbackground=_adjust_hex_brightness(palette.entry_bg, 1.18),
        selectforeground=UI_STYLE["fg"],
        highlightbackground=border_color,
        highlightcolor=palette.panel_highlight,
        highlightthickness=1,
        relief="flat",
        borderwidth=0,
        font=(UI_STYLE["font_family"], UI_STYLE["font_size"]),
    )
