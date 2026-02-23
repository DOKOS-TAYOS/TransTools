"""UI theme configuration for TransTools."""

from tkinter import ttk
from typing import Any

from config.env import get_env_from_schema

UI_STYLE: dict[str, Any] = {}


def _build_ui_style() -> dict[str, Any]:
    """Build UI style dict from env.

    Returns:
        Dictionary with bg, fg, padding, button_width, font_family, etc.
    """
    return {
        "bg": get_env_from_schema("UI_BACKGROUND"),
        "fg": get_env_from_schema("UI_FOREGROUND"),
        "padding": get_env_from_schema("UI_PADDING"),
        "button_width": get_env_from_schema("UI_BUTTON_WIDTH"),
        "button_width_wide": get_env_from_schema("UI_BUTTON_WIDTH_WIDE"),
        "button_bg": get_env_from_schema("UI_BUTTON_BG"),
        "button_fg": get_env_from_schema("UI_BUTTON_FG"),
        "button_fg_cancel": get_env_from_schema("UI_BUTTON_FG_CANCEL"),
        "button_fg_accent": get_env_from_schema("UI_BUTTON_FG_ACCENT2"),
        "font_family": get_env_from_schema("UI_FONT_FAMILY"),
        "font_size": get_env_from_schema("UI_FONT_SIZE"),
        "border_width": 8,
    }


def refresh_theme() -> None:
    """Refresh UI_STYLE from config.

    Rebuilds the global UI_STYLE dict from current env values.
    """
    global UI_STYLE
    UI_STYLE = _build_ui_style()


def configure_ttk_styles(root) -> None:
    """Configure ttk styles with colors and fonts from config.

    Uses 'clam' theme to allow custom colors (vista/xpnative often ignore them).

    Args:
        root: Tk or Toplevel widget to configure styles for.
    """
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except ttk.TclError:
        pass  # Fallback to default if clam not available

    font = (UI_STYLE["font_family"], UI_STYLE["font_size"])
    bg = UI_STYLE["bg"]
    fg = UI_STYLE["fg"]
    btn_bg = UI_STYLE["button_bg"]
    btn_fg = UI_STYLE["button_fg"]
    btn_fg_cancel = UI_STYLE["button_fg_cancel"]
    btn_fg_accent = UI_STYLE["button_fg_accent"]

    # TFrame - main background
    style.configure("TFrame", background=bg)

    # TLabel - labels
    style.configure("TLabel", background=bg, foreground=fg, font=font)

    # TButton - primary buttons
    style.configure(
        "TButton",
        background=btn_bg,
        foreground=btn_fg,
        font=font,
        padding=(8, 6),
    )
    style.map("TButton", background=[("active", btn_bg), ("pressed", btn_bg)])

    # Danger.TButton - exit/cancel (red)
    style.configure(
        "Danger.TButton",
        background=btn_bg,
        foreground=btn_fg_cancel,
        font=font,
        padding=(8, 6),
    )
    style.map("Danger.TButton", background=[("active", btn_bg), ("pressed", btn_bg)])

    # Accent.TButton - secondary (yellow)
    style.configure(
        "Accent.TButton",
        background=btn_bg,
        foreground=btn_fg_accent,
        font=font,
        padding=(8, 6),
    )
    style.map("Accent.TButton", background=[("active", btn_bg), ("pressed", btn_bg)])

    # TEntry - text input
    style.configure("TEntry", fieldbackground=btn_bg, foreground=fg, font=font)

    # TCombobox - dropdown
    style.configure(
        "TCombobox",
        fieldbackground=btn_bg,
        foreground=fg,
        background=btn_bg,
        arrowcolor=fg,
        font=font,
    )

    # TSpinbox - numeric spin (Python 3.11+)
    try:
        style.configure(
            "TSpinbox",
            fieldbackground=btn_bg,
            foreground=fg,
            background=btn_bg,
            arrowcolor=fg,
            font=font,
        )
    except ttk.TclError:
        pass

    # TCheckbutton - checkbox
    style.configure(
        "TCheckbutton",
        background=bg,
        foreground=fg,
        font=font,
    )


# Initialize on import
refresh_theme()
