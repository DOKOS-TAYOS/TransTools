"""Window utilities for TransTools."""

from tkinter import Tk, Toplevel

VERTICAL_CENTER_BIAS = 18
WINDOW_SCREEN_MARGIN = 40


def _get_window_decoration_size(window: Tk | Toplevel) -> tuple[int, int]:
    """Estimate top-level window decoration size.

    Returns:
        Tuple of (extra_width, extra_height) added by borders/title bar.
    """
    try:
        left_border = max(0, window.winfo_rootx() - window.winfo_x())
        top_border = max(0, window.winfo_rooty() - window.winfo_y())
        extra_width = left_border * 2
        extra_height = top_border + left_border
        return extra_width, extra_height
    except Exception:
        return 0, 0


def fit_window_size_to_screen(
    width: int,
    height: int,
    screen_width: int,
    screen_height: int,
    margin: int = WINDOW_SCREEN_MARGIN,
) -> tuple[int, int]:
    """Clamp a requested window size so it fits inside the current screen."""
    available_width = max(200, int(screen_width) - int(margin))
    available_height = max(200, int(screen_height) - int(margin))
    fitted_width = max(200, min(int(width), available_width))
    fitted_height = max(200, min(int(height), available_height))
    return fitted_width, fitted_height


def place_window_centered(
    window: Tk | Toplevel,
    width: int | None = None,
    height: int | None = None,
) -> None:
    """Center a Tk or Toplevel window on the screen.

    Args:
        window: Tk or Toplevel window to center.
        width: Optional width in pixels. When set with height, geometry is applied as WxH+X+Y.
        height: Optional height in pixels. When set with width, geometry is applied as WxH+X+Y.
    """
    sx = window.winfo_vrootx()
    sy = window.winfo_vrooty()
    sw = window.winfo_vrootwidth()
    sh = window.winfo_vrootheight()

    if width is not None and height is not None:
        width, height = fit_window_size_to_screen(width, height, sw, sh)
        window.geometry(f"{width}x{height}+0+0")
        window.update_idletasks()
        extra_w, extra_h = _get_window_decoration_size(window)
        actual_w = max(window.winfo_width() + extra_w, width)
        actual_h = max(window.winfo_height() + extra_h, height)
        x = max(sx, sx + (sw - actual_w) // 2)
        y = max(sy, sy + (sh - actual_h) // 2 - VERTICAL_CENTER_BIAS)
        window.geometry(f"{width}x{height}+{x}+{y}")
        return

    window.update_idletasks()
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
    extra_w, extra_h = _get_window_decoration_size(window)
    outer_w = w + extra_w
    outer_h = h + extra_h
    x = max(sx, sx + (sw - outer_w) // 2)
    y = max(sy, sy + (sh - outer_h) // 2 - VERTICAL_CENTER_BIAS)
    window.geometry(f"+{x}+{y}")
