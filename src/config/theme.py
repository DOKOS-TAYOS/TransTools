"""UI theme configuration for TransTools."""

from __future__ import annotations

import re
from dataclasses import dataclass
from tkinter import Misc, TclError, ttk
from typing import Any

from config.env import get_env_from_schema

UI_STYLE: dict[str, Any] = {}


@dataclass(frozen=True)
class ThemeSurfacePalette:
    """Derived surface colors used across interactive widgets."""

    entry_bg: str
    entry_hover: str
    panel_bg: str
    panel_border: str
    check_bg: str
    check_hover: str
    check_active: str
    check_disabled: str
    tab_bg: str
    tree_bg: str
    tree_heading_bg: str
    tree_selected_bg: str
    listbox_bg: str
    listbox_select_bg: str


@dataclass(frozen=True)
class ThemeSizing:
    """Shared sizing values for themed widgets."""

    button_padding: tuple[int, int]
    summary_button_padding: tuple[int, int]
    notebook_tab_padding: tuple[int, int]
    tree_rowheight: int
    spinbox_arrowsize: int
    check_indicator_size: int


def build_surface_palette(bg: str, btn_bg: str) -> ThemeSurfacePalette:
    """Build a consistent non-white palette for compound ttk widgets."""
    entry_bg = _adjust_hex_brightness(bg, 0.85)
    entry_hover = _adjust_hex_brightness(entry_bg, 1.2)
    panel_bg = _adjust_hex_brightness(bg, 0.92)
    panel_border = _adjust_hex_brightness(bg, 1.28)
    check_bg = _adjust_hex_brightness(bg, 1.10)
    check_hover = _adjust_hex_brightness(bg, 1.22)
    check_active = _adjust_hex_brightness(bg, 1.22)
    check_disabled = _adjust_hex_brightness(bg, 0.96)
    tab_bg = _adjust_hex_brightness(bg, 0.9)
    tree_heading_bg = _adjust_hex_brightness(bg, 0.88)

    return ThemeSurfacePalette(
        entry_bg=entry_bg,
        entry_hover=entry_hover,
        panel_bg=panel_bg,
        panel_border=panel_border,
        check_bg=check_bg,
        check_hover=check_hover,
        check_active=check_active,
        check_disabled=check_disabled,
        tab_bg=tab_bg,
        tree_bg=entry_bg,
        tree_heading_bg=tree_heading_bg,
        tree_selected_bg=btn_bg,
        listbox_bg=entry_bg,
        listbox_select_bg=btn_bg,
    )


def build_theme_sizing(font_size: int, padding: int) -> ThemeSizing:
    """Build compact shared sizing values from the active font and padding."""
    normalized_font_size = max(8, int(font_size))
    normalized_padding = max(2, int(padding))
    button_padding = (max(6, normalized_padding), max(4, normalized_padding - 2))
    summary_button_padding = (max(6, normalized_padding), max(3, normalized_padding - 3))
    notebook_tab_padding = (max(10, normalized_padding + 4), max(5, normalized_padding - 1))
    tree_rowheight = max(normalized_font_size + normalized_padding + 4, 26)
    spinbox_arrowsize = max(
        normalized_font_size,
        normalized_font_size + max(0, normalized_padding - 3),
    )
    check_indicator_size = max(12, normalized_font_size - 1)

    return ThemeSizing(
        button_padding=button_padding,
        summary_button_padding=summary_button_padding,
        notebook_tab_padding=notebook_tab_padding,
        tree_rowheight=tree_rowheight,
        spinbox_arrowsize=spinbox_arrowsize,
        check_indicator_size=check_indicator_size,
    )


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


def configure_ttk_styles(root: Misc) -> None:
    """Configure ttk styles with colors and fonts from config.

    Uses 'clam' theme to allow custom colors (vista/xpnative often ignore them).

    Args:
        root: Tk or Toplevel widget to configure styles for.
    """
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except TclError:
        pass  # Fallback to default if clam not available

    font = (UI_STYLE["font_family"], UI_STYLE["font_size"])
    bg = UI_STYLE["bg"]
    fg = UI_STYLE["fg"]
    btn_bg = UI_STYLE["button_bg"]
    btn_fg = UI_STYLE["button_fg"]
    btn_fg_cancel = UI_STYLE["button_fg_cancel"]
    btn_fg_accent = UI_STYLE["button_fg_accent"]

    palette = build_surface_palette(bg=bg, btn_bg=btn_bg)
    sizing = build_theme_sizing(UI_STYLE["font_size"], UI_STYLE["padding"])

    # Buttons: slightly lighter on hover
    btn_hover = _adjust_hex_brightness(btn_bg, 1.2)

    # TFrame - main background
    style.configure("TFrame", background=bg)

    # TLabel - labels
    style.configure("TLabel", background=bg, foreground=fg, font=font)

    # Small.TLabel - smaller text (e.g. descriptions)
    font_small = (UI_STYLE["font_family"], max(9, int(UI_STYLE["font_size"] * 0.72)))
    style.configure("Small.TLabel", background=bg, foreground=fg, font=font_small)

    # TLabelframe - grouped areas
    style.configure(
        "TLabelframe",
        background=palette.panel_bg,
        borderwidth=1,
        relief="solid",
        bordercolor=palette.panel_border,
    )
    style.configure(
        "TLabelframe.Label",
        background=bg,
        foreground=fg,
        font=font,
    )

    # TButton - primary buttons
    style.configure(
        "TButton",
        background=btn_bg,
        foreground=btn_fg,
        font=font,
        padding=sizing.button_padding,
    )
    style.map("TButton", background=[("active", btn_hover), ("pressed", btn_bg)])

    # Danger.TButton - exit/cancel (red)
    style.configure(
        "Danger.TButton",
        background=btn_bg,
        foreground=btn_fg_cancel,
        font=font,
        padding=sizing.button_padding,
    )
    style.map("Danger.TButton", background=[("active", btn_hover), ("pressed", btn_bg)])

    # Accent.TButton - secondary (yellow)
    style.configure(
        "Accent.TButton",
        background=btn_bg,
        foreground=btn_fg_accent,
        font=font,
        padding=sizing.button_padding,
    )
    style.map("Accent.TButton", background=[("active", btn_hover), ("pressed", btn_bg)])

    # SummaryToggle.TButton - smaller control for the collapsible quick summary.
    summary_font = (UI_STYLE["font_family"], max(8, int(UI_STYLE["font_size"] * 0.78)))
    style.configure(
        "SummaryToggle.TButton",
        background=btn_bg,
        foreground=btn_fg,
        font=summary_font,
        padding=sizing.summary_button_padding,
    )
    style.map(
        "SummaryToggle.TButton",
        background=[("active", btn_hover), ("pressed", btn_bg)],
    )

    # TEntry - text input (darker than bg, lighter on hover)
    style.configure("TEntry", fieldbackground=palette.entry_bg, foreground=fg, font=font)
    style.map(
        "TEntry",
        fieldbackground=[("active", palette.entry_hover), ("focus", palette.entry_hover)],
    )

    # TCombobox - dropdown (darker than bg, lighter on hover)
    style.configure(
        "TCombobox",
        fieldbackground=palette.entry_bg,
        foreground=fg,
        background=palette.entry_bg,
        arrowcolor=fg,
        font=font,
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", palette.entry_bg), ("active", palette.entry_hover)],
        background=[("active", palette.entry_hover)],
    )
    # Combobox dropdown listbox colors must be configured via Tk options.
    root.option_add("*TCombobox*Listbox.font", f"{font[0]} {font[1]}")
    root.option_add("*TCombobox*Listbox.background", palette.listbox_bg)
    root.option_add("*TCombobox*Listbox.foreground", fg)
    root.option_add("*TCombobox*Listbox.selectBackground", palette.listbox_select_bg)
    root.option_add("*TCombobox*Listbox.selectForeground", fg)

    # TSpinbox - numeric spin (darker than bg, lighter on hover) (Python 3.11+)
    try:
        style.configure(
            "TSpinbox",
            fieldbackground=palette.entry_bg,
            foreground=fg,
            background=palette.entry_bg,
            arrowcolor=fg,
            arrowsize=sizing.spinbox_arrowsize,
            font=font,
        )
        style.map(
            "TSpinbox",
            fieldbackground=[("active", palette.entry_hover), ("focus", palette.entry_hover)],
            background=[("active", palette.entry_hover)],
        )
    except TclError:
        pass

    # TCheckbutton - checkbox (indicatorsize = font_size for proportional look)
    style.configure(
        "TCheckbutton",
        background=bg,
        foreground=fg,
        font=font,
        indicatorsize=sizing.check_indicator_size,
        indicatorbackground=palette.check_bg,
        indicatorforeground=fg,
        indicatormargin=2,
    )
    style.map(
        "TCheckbutton",
        background=[("active", palette.check_hover), ("selected", bg)],
        indicatorbackground=[
            ("selected", palette.check_active),
            ("active", palette.check_hover),
            ("disabled", palette.check_disabled),
        ],
        indicatorforeground=[
            ("selected", fg),
            ("disabled", _adjust_hex_brightness(fg, 0.85) if fg.startswith("#") else fg),
        ],
    )

    # Treeview - keep tables aligned with the application palette.
    style.configure(
        "Treeview",
        background=palette.tree_bg,
        fieldbackground=palette.tree_bg,
        foreground=fg,
        font=font,
        rowheight=sizing.tree_rowheight,
        borderwidth=0,
        relief="flat",
    )
    style.map(
        "Treeview",
        background=[("selected", palette.tree_selected_bg)],
        foreground=[("selected", fg)],
    )
    style.configure(
        "Treeview.Heading",
        background=palette.tree_heading_bg,
        foreground=fg,
        font=font,
        relief="flat",
    )
    style.map(
        "Treeview.Heading",
        background=[("active", palette.panel_bg)],
        foreground=[("active", fg)],
    )

    style.configure(
        "TNotebook",
        background=palette.panel_bg,
        borderwidth=0,
        tabmargins=(0, 0, 0, 0),
    )
    style.configure(
        "TNotebook.Tab",
        background=palette.tab_bg,
        foreground=fg,
        padding=sizing.notebook_tab_padding,
        font=font,
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", palette.panel_bg), ("active", palette.panel_bg)],
    )

    style.configure(
        "TScrollbar",
        background=palette.panel_bg,
        troughcolor=bg,
        arrowcolor=fg,
        bordercolor=palette.panel_border,
    )

    root.option_add("*Listbox.background", palette.listbox_bg)
    root.option_add("*Listbox.foreground", fg)
    root.option_add("*Listbox.selectBackground", palette.listbox_select_bg)
    root.option_add("*Listbox.selectForeground", fg)
    root.option_add("*Menu.background", palette.listbox_bg)
    root.option_add("*Menu.foreground", fg)
    root.option_add("*Menu.activeBackground", palette.listbox_select_bg)
    root.option_add("*Menu.activeForeground", fg)


def prepare_ttk_window(root: Misc) -> None:
    """Refresh the theme and reapply shared ttk styling on a window."""
    refresh_theme()
    configure_ttk_styles(root)


# Initialize on import
refresh_theme()
