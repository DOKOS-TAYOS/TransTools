"""Window utilities for TransTools."""

from tkinter import Tk, Toplevel


def place_window_centered(
    window: Tk | Toplevel,
    preserve_size: bool = False,
    width: int | None = None,
    height: int | None = None,
) -> None:
    """Center a Tk or Toplevel window on the screen.

    Args:
        window: Tk or Toplevel window to center.
        preserve_size: If True, only center when window has valid size (kept for API compatibility).
        width: Optional width in pixels. When set with height, geometry is applied as WxH+X+Y.
        height: Optional height in pixels. When set with width, geometry is applied as WxH+X+Y.
    """
    window.update_idletasks()
    sw = window.winfo_screenwidth()
    sh = window.winfo_screenheight()

    if width is not None and height is not None:
        x = max(0, (sw - width) // 2)
        y = max(0, (sh - height) // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")
        return

    w = window.winfo_width()
    h = window.winfo_height()
    if w <= 1 or h <= 1:
        w = window.winfo_reqwidth()
        h = window.winfo_reqheight()
    if w <= 1 or h <= 1:
        window.update()
        w = max(window.winfo_width(), window.winfo_reqwidth())
        h = max(window.winfo_height(), window.winfo_reqheight())
    if w <= 1 or h <= 1:
        return
    x = max(0, (sw - w) // 2)
    y = max(0, (sh - h) // 2)
    window.geometry(f"+{x}+{y}")
