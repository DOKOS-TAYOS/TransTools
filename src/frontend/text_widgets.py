"""Helpers for multiline text widgets."""

from __future__ import annotations

import re
from tkinter import Text

from config import UI_STYLE


def _adjust_hex_brightness(hex_color: str, factor: float) -> str:
    """Adjust brightness of a hex color."""
    if not re.match(r"^#[0-9a-fA-F]{6}$", hex_color):
        return hex_color
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    r = max(0, min(255, int(r * factor)))
    g = max(0, min(255, int(g * factor)))
    b = max(0, min(255, int(b * factor)))
    return f"#{r:02x}{g:02x}{b:02x}"


def configure_notes_widget(widget: Text) -> None:
    """Apply project colors to multiline notes widgets."""
    border_color = UI_STYLE["fg"]
    widget.configure(
        background=UI_STYLE["bg"],
        foreground=UI_STYLE["fg"],
        insertbackground=UI_STYLE["fg"],
        selectbackground=_adjust_hex_brightness(UI_STYLE["bg"], 1.16),
        selectforeground=UI_STYLE["fg"],
        highlightbackground=border_color,
        highlightcolor=border_color,
        highlightthickness=1,
        relief="flat",
        borderwidth=0,
        font=(UI_STYLE["font_family"], UI_STYLE["font_size"]),
    )
