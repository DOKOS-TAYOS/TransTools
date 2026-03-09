"""Factory helpers for ttk input widgets with project font."""

from __future__ import annotations

from tkinter import TclError, ttk
from typing import Any

from config import UI_STYLE


def _project_font() -> tuple[str, int]:
    """Build the current project font tuple."""
    return (UI_STYLE["font_family"], int(UI_STYLE["font_size"]))


def create_entry(parent, **kwargs: Any) -> ttk.Entry:
    """Create ttk.Entry using project font when supported.

    Args:
        parent: Parent Tk widget.
        **kwargs: ttk.Entry options.

    Returns:
        Configured ttk.Entry instance.
    """
    options = dict(kwargs)
    options.setdefault("font", _project_font())
    try:
        return ttk.Entry(parent, **options)
    except TclError:
        options.pop("font", None)
        return ttk.Entry(parent, **options)


def create_combobox(parent, **kwargs: Any) -> ttk.Combobox:
    """Create ttk.Combobox using project font when supported.

    Args:
        parent: Parent Tk widget.
        **kwargs: ttk.Combobox options.

    Returns:
        Configured ttk.Combobox instance.
    """
    options = dict(kwargs)
    options.setdefault("font", _project_font())
    try:
        return ttk.Combobox(parent, **options)
    except TclError:
        options.pop("font", None)
        return ttk.Combobox(parent, **options)


def create_spinbox(parent, **kwargs: Any) -> ttk.Spinbox:
    """Create ttk.Spinbox using project font when supported.

    Args:
        parent: Parent Tk widget.
        **kwargs: ttk.Spinbox options.

    Returns:
        Configured ttk.Spinbox instance.
    """
    options = dict(kwargs)
    options.setdefault("font", _project_font())
    try:
        return ttk.Spinbox(parent, **options)
    except TclError:
        options.pop("font", None)
        return ttk.Spinbox(parent, **options)
