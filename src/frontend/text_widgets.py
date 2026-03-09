"""Helpers for multiline text widgets."""

from __future__ import annotations

from tkinter import Text

from config import UI_STYLE
from config.theme import _adjust_hex_brightness


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
