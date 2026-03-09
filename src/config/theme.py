"""UI theme configuration for TransTools."""

import re
from tkinter import ttk
from typing import Any

from config.env import get_env_from_schema

UI_STYLE: dict[str, Any] = {}


def _adjust_hex_brightness(hex_color: str, factor: float) -> str:
    """Adjust brightness of a hex color.

    Args:
        hex_color: Hex color (e.g. #181818).
        factor: > 1 = lighter, < 1 = darker.

    Returns:
        Adjusted hex color.
    """
    if not re.match(r"^#[0-9a-fA-F]{6}$", hex_color):
        return hex_color
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    r = max(0, min(255, int(r * factor)))
    g = max(0, min(255, int(g * factor)))
    b = max(0, min(255, int(b * factor)))
    return f"#{r:02x}{g:02x}{b:02x}"


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

    # Entry/Combobox/Spinbox: slightly darker than menu bg, hover slightly lighter
    entry_bg = _adjust_hex_brightness(bg, 0.85)
    entry_hover = _adjust_hex_brightness(entry_bg, 1.2)

    # Buttons: slightly lighter on hover
    btn_hover = _adjust_hex_brightness(btn_bg, 1.2)

    # Checkbox indicator: keep it very close to background to avoid harsh accents
    check_bg = _adjust_hex_brightness(bg, 1.10)
    check_hover = _adjust_hex_brightness(bg, 1.22)
    check_active = _adjust_hex_brightness(bg, 1.22)
    check_disabled = _adjust_hex_brightness(bg, 0.96)

    # TFrame - main background
    style.configure("TFrame", background=bg)

    # TLabel - labels
    style.configure("TLabel", background=bg, foreground=fg, font=font)

    # Small.TLabel - smaller text (e.g. descriptions)
    font_small = (UI_STYLE["font_family"], max(8, int(UI_STYLE["font_size"] * 0.65)))
    style.configure("Small.TLabel", background=bg, foreground=fg, font=font_small)

    # TButton - primary buttons
    style.configure(
        "TButton",
        background=btn_bg,
        foreground=btn_fg,
        font=font,
        padding=(8, 6),
    )
    style.map("TButton", background=[("active", btn_hover), ("pressed", btn_bg)])

    # Danger.TButton - exit/cancel (red)
    style.configure(
        "Danger.TButton",
        background=btn_bg,
        foreground=btn_fg_cancel,
        font=font,
        padding=(8, 6),
    )
    style.map("Danger.TButton", background=[("active", btn_hover), ("pressed", btn_bg)])

    # Accent.TButton - secondary (yellow)
    style.configure(
        "Accent.TButton",
        background=btn_bg,
        foreground=btn_fg_accent,
        font=font,
        padding=(8, 6),
    )
    style.map("Accent.TButton", background=[("active", btn_hover), ("pressed", btn_bg)])

    # TEntry - text input (darker than bg, lighter on hover)
    style.configure("TEntry", fieldbackground=entry_bg, foreground=fg, font=font)
    style.map("TEntry", fieldbackground=[("active", entry_hover), ("focus", entry_hover)])

    # TCombobox - dropdown (darker than bg, lighter on hover)
    style.configure(
        "TCombobox",
        fieldbackground=entry_bg,
        foreground=fg,
        background=entry_bg,
        arrowcolor=fg,
        font=font,
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", entry_bg), ("active", entry_hover)],
        background=[("active", entry_hover)],
    )
    # Combobox dropdown listbox font (must be set via option_add; style only affects field)
    root.option_add("*TCombobox*Listbox.font", f"{font[0]} {font[1]}")

    # TSpinbox - numeric spin (darker than bg, lighter on hover) (Python 3.11+)
    # Arrows height = font_size + padding  // 2to match spinbox box height
    spinbox_arrowsize = UI_STYLE["font_size"]  + UI_STYLE["padding"]// 2
    try:
        style.configure(
            "TSpinbox",
            fieldbackground=entry_bg,
            foreground=fg,
            background=entry_bg,
            arrowcolor=fg,
            arrowsize=spinbox_arrowsize,
            font=font,
        )
        style.map(
            "TSpinbox",
            fieldbackground=[("active", entry_hover), ("focus", entry_hover)],
            background=[("active", entry_hover)],
        )
    except ttk.TclError:
        pass

    # TCheckbutton - checkbox (indicatorsize = font_size for proportional look)
    style.configure(
        "TCheckbutton",
        background=bg,
        foreground=fg,
        font=font,
        indicatorsize=UI_STYLE["font_size"],
        indicatorbackground=check_bg,
        indicatorforeground=fg,
        indicatormargin=2,
    )
    style.map(
        "TCheckbutton",
        background=[("active", check_hover), ("selected", bg)],
        indicatorbackground=[
            ("selected", check_active),
            ("active", check_hover),
            ("disabled", check_disabled),
        ],
        indicatorforeground=[
            ("selected", fg),
            ("disabled", _adjust_hex_brightness(fg, 0.85) if fg.startswith("#") else fg),
        ],
    )

    # TNotebook.Tab - larger tabs for config dialog
    tab_pad_h = max(16, UI_STYLE["padding"] * 2)
    tab_pad_v = max(8, UI_STYLE["padding"])
    tab_bg = _adjust_hex_brightness(bg, 0.9)
    style.configure(
        "TNotebook",
        background=bg,
        borderwidth=0,
        tabmargins=(0, 0, 0, 0),
    )
    style.configure(
        "TNotebook.Tab",
        background=tab_bg,
        foreground=fg,
        padding=(tab_pad_h, tab_pad_v),
        font=font,
    )
    style.map("TNotebook.Tab", background=[("selected", bg), ("active", bg)])


# Initialize on import
refresh_theme()
