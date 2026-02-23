"""Window utilities for TransTools."""

from tkinter import Toplevel


def place_window_centered(toplevel: Toplevel, preserve_size: bool = False) -> None:
    """Center a Toplevel window relative to its parent or screen.

    Args:
        toplevel: Toplevel window to center.
        preserve_size: If True, only center when window has valid size.
    """
    toplevel.update_idletasks()
    w = toplevel.winfo_width()
    h = toplevel.winfo_height()
    if not preserve_size or w <= 1 or h <= 1:
        return
    parent = toplevel.master
    px = parent.winfo_rootx()
    py = parent.winfo_rooty()
    pw = parent.winfo_width()
    ph = parent.winfo_height()
    x = px + (pw - w) // 2
    y = py + (ph - h) // 2
    toplevel.geometry(f"+{x}+{y}")
