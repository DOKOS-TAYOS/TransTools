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
    panel_alt_bg: str
    panel_raised_bg: str
    panel_border: str
    panel_highlight: str
    hero_bg: str
    hero_fg: str
    hero_muted_fg: str
    muted_fg: str
    subtle_fg: str
    check_bg: str
    check_hover: str
    check_active: str
    check_disabled: str
    tab_bg: str
    tab_active_bg: str
    tree_bg: str
    tree_heading_bg: str
    tree_selected_bg: str
    listbox_bg: str
    listbox_select_bg: str
    listbox_border: str
    status_info_bg: str
    status_warn_bg: str
    status_danger_bg: str
    section_header_bg: str
    section_header_fg: str


@dataclass(frozen=True)
class ThemeSizing:
    """Shared sizing values for themed widgets."""

    button_padding: tuple[int, int]
    summary_button_padding: tuple[int, int]
    notebook_tab_padding: tuple[int, int]
    tree_rowheight: int
    spinbox_arrowsize: int
    check_indicator_size: int


def _is_hex_color(value: str) -> bool:
    """Return True when the value looks like a six-digit hex color."""
    return bool(re.match(r"^#[0-9a-fA-F]{6}$", value))


def _blend_hex_colors(base_color: str, target_color: str, factor: float) -> str:
    """Blend two hex colors using a 0-1 interpolation factor."""
    if not (_is_hex_color(base_color) and _is_hex_color(target_color)):
        return base_color

    clamped_factor = max(0.0, min(1.0, factor))
    blended_channels: list[int] = []
    for index in (1, 3, 5):
        start = int(base_color[index : index + 2], 16)
        end = int(target_color[index : index + 2], 16)
        blended_channels.append(int(start + ((end - start) * clamped_factor)))

    return "#{:02x}{:02x}{:02x}".format(*blended_channels)


def _adjust_hex_brightness(hex_color: str, factor: float) -> str:
    """Adjust brightness of a hex color."""
    if not _is_hex_color(hex_color):
        return hex_color

    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    r = max(0, min(255, int(r * factor)))
    g = max(0, min(255, int(g * factor)))
    b = max(0, min(255, int(b * factor)))
    return f"#{r:02x}{g:02x}{b:02x}"


def build_surface_palette(bg: str, btn_bg: str, fg: str | None = None) -> ThemeSurfacePalette:
    """Build a richer dark palette for ttk widgets and information panels."""
    resolved_fg = fg if fg is not None else "#cccccc"

    entry_bg = _adjust_hex_brightness(bg, 0.85)
    entry_hover = _blend_hex_colors(entry_bg, "#ffffff", 0.12)
    panel_bg = _blend_hex_colors(bg, "#ffffff", 0.06)
    panel_alt_bg = _blend_hex_colors(bg, "#ffffff", 0.12)
    panel_raised_bg = _blend_hex_colors(btn_bg, "#ffffff", 0.10)
    panel_border = _blend_hex_colors(bg, "#ffffff", 0.20)
    panel_highlight = _blend_hex_colors(btn_bg, "#6eb1c8", 0.34)
    hero_bg = _blend_hex_colors(bg, "#3890b4", 0.25)
    hero_fg = resolved_fg
    hero_muted_fg = _blend_hex_colors(resolved_fg, bg, 0.18)
    muted_fg = _blend_hex_colors(resolved_fg, bg, 0.28)
    subtle_fg = _blend_hex_colors(resolved_fg, bg, 0.42)

    check_bg = _blend_hex_colors(bg, "#ffffff", 0.12)
    check_hover = _blend_hex_colors(bg, "#ffffff", 0.18)
    check_active = panel_highlight
    check_disabled = _blend_hex_colors(bg, "#ffffff", 0.08)

    tab_bg = panel_bg
    tab_active_bg = panel_alt_bg
    tree_heading_bg = panel_alt_bg

    return ThemeSurfacePalette(
        entry_bg=entry_bg,
        entry_hover=entry_hover,
        panel_bg=panel_bg,
        panel_alt_bg=panel_alt_bg,
        panel_raised_bg=panel_raised_bg,
        panel_border=panel_border,
        panel_highlight=panel_highlight,
        hero_bg=hero_bg,
        hero_fg=hero_fg,
        hero_muted_fg=hero_muted_fg,
        muted_fg=muted_fg,
        subtle_fg=subtle_fg,
        check_bg=check_bg,
        check_hover=check_hover,
        check_active=check_active,
        check_disabled=check_disabled,
        tab_bg=tab_bg,
        tab_active_bg=tab_active_bg,
        tree_bg=entry_bg,
        tree_heading_bg=tree_heading_bg,
        tree_selected_bg=btn_bg,
        listbox_bg=entry_bg,
        listbox_select_bg=btn_bg,
        listbox_border=panel_border,
        status_info_bg=_blend_hex_colors(bg, "#23566f", 0.34),
        status_warn_bg=_blend_hex_colors(bg, "#7b5a1e", 0.34),
        status_danger_bg=_blend_hex_colors(bg, "#7f2434", 0.34),
        section_header_bg=_blend_hex_colors(bg, "#2f6e88", 0.28),
        section_header_fg=hero_fg,
    )


def get_surface_palette() -> ThemeSurfacePalette:
    """Build the current palette from the active UI style."""
    return build_surface_palette(
        bg=str(UI_STYLE["bg"]),
        btn_bg=str(UI_STYLE["button_bg"]),
        fg=str(UI_STYLE["fg"]),
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


def _build_ui_style() -> dict[str, Any]:
    """Build UI style dict from env."""
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
    """Refresh UI_STYLE from config."""
    global UI_STYLE
    UI_STYLE = _build_ui_style()


def _configure_button_style(
    style: ttk.Style,
    style_name: str,
    *,
    background: str,
    foreground: str,
    hover_background: str,
    pressed_background: str,
    font: tuple[str, int],
    padding: tuple[int, int],
) -> None:
    """Configure a button style with filled surfaces."""
    style.configure(
        style_name,
        background=background,
        foreground=foreground,
        font=font,
        padding=padding,
        borderwidth=1,
        relief="flat",
        focusthickness=1,
        focuscolor=hover_background,
    )
    style.map(
        style_name,
        background=[
            ("disabled", pressed_background),
            ("pressed", pressed_background),
            ("active", hover_background),
        ],
        foreground=[("disabled", foreground)],
    )


def configure_ttk_styles(root: Misc) -> None:
    """Configure ttk styles with colors and fonts from config."""
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except TclError:
        pass

    font = (str(UI_STYLE["font_family"]), int(UI_STYLE["font_size"]))
    font_small = (str(UI_STYLE["font_family"]), max(9, int(UI_STYLE["font_size"]) - 3))
    title_font = (str(UI_STYLE["font_family"]), max(16, int(UI_STYLE["font_size"]) + 5), "bold")
    section_font = (str(UI_STYLE["font_family"]), max(12, int(UI_STYLE["font_size"]) + 1), "bold")
    bg = str(UI_STYLE["bg"])
    fg = str(UI_STYLE["fg"])
    btn_bg = str(UI_STYLE["button_bg"])

    palette = get_surface_palette()
    sizing = build_theme_sizing(int(UI_STYLE["font_size"]), int(UI_STYLE["padding"]))

    btn_hover = _blend_hex_colors(btn_bg, "#ffffff", 0.14)
    btn_pressed = _blend_hex_colors(btn_bg, bg, 0.10)

    style.configure("TFrame", background=bg)
    style.configure("App.TFrame", background=bg)
    style.configure("Card.TFrame", background=palette.panel_bg, relief="flat", borderwidth=0)
    style.configure(
        "RaisedCard.TFrame",
        background=palette.panel_alt_bg,
        relief="flat",
        borderwidth=0,
    )
    style.configure("Toolbar.TFrame", background=palette.panel_bg, relief="flat", borderwidth=0)

    style.configure("TLabel", background=bg, foreground=fg, font=font)
    style.configure("Small.TLabel", background=bg, foreground=palette.muted_fg, font=font_small)
    style.configure("Muted.TLabel", background=bg, foreground=palette.muted_fg, font=font)
    style.configure("Card.TLabel", background=palette.panel_bg, foreground=fg, font=font)
    style.configure(
        "CardMuted.TLabel",
        background=palette.panel_bg,
        foreground=palette.muted_fg,
        font=font,
    )
    style.configure(
        "CardTitle.TLabel",
        background=palette.panel_bg,
        foreground=fg,
        font=section_font,
    )
    style.configure(
        "HeroTitle.TLabel",
        background=palette.hero_bg,
        foreground=palette.hero_fg,
        font=title_font,
    )
    style.configure(
        "HeroSubtitle.TLabel",
        background=palette.hero_bg,
        foreground=palette.hero_muted_fg,
        font=font,
    )
    style.configure(
        "HeroMeta.TLabel",
        background=palette.hero_bg,
        foreground=palette.hero_muted_fg,
        font=font_small,
    )
    style.configure(
        "SectionHeading.TLabel",
        background=palette.panel_bg,
        foreground=palette.muted_fg,
        font=(str(UI_STYLE["font_family"]), max(9, int(UI_STYLE["font_size"]) - 2), "bold"),
    )
    style.configure(
        "SummaryBody.TLabel",
        background=palette.panel_bg,
        foreground=fg,
        font=font,
    )

    style.configure(
        "TLabelframe",
        background=palette.panel_bg,
        borderwidth=1,
        relief="solid",
        bordercolor=palette.panel_border,
    )
    style.configure(
        "TLabelframe.Label",
        background=palette.panel_bg,
        foreground=fg,
        font=font,
    )

    _configure_button_style(
        style,
        "TButton",
        background=btn_bg,
        foreground=fg,
        hover_background=btn_hover,
        pressed_background=btn_pressed,
        font=font,
        padding=sizing.button_padding,
    )
    _configure_button_style(
        style,
        "MenuCard.TButton",
        background=palette.panel_alt_bg,
        foreground=fg,
        hover_background=_blend_hex_colors(palette.panel_alt_bg, "#ffffff", 0.10),
        pressed_background=palette.panel_bg,
        font=font,
        padding=(sizing.button_padding[0] + 1, sizing.button_padding[1]),
    )
    _configure_button_style(
        style,
        "Utility.TButton",
        background=palette.panel_bg,
        foreground=fg,
        hover_background=palette.panel_alt_bg,
        pressed_background=btn_pressed,
        font=font,
        padding=sizing.button_padding,
    )
    _configure_button_style(
        style,
        "Danger.TButton",
        background=palette.status_danger_bg,
        foreground=fg,
        hover_background=_blend_hex_colors(palette.status_danger_bg, "#ffffff", 0.10),
        pressed_background=_blend_hex_colors(palette.status_danger_bg, bg, 0.16),
        font=font,
        padding=sizing.button_padding,
    )
    _configure_button_style(
        style,
        "Accent.TButton",
        background=palette.status_warn_bg,
        foreground=fg,
        hover_background=_blend_hex_colors(palette.status_warn_bg, "#ffffff", 0.08),
        pressed_background=_blend_hex_colors(palette.status_warn_bg, bg, 0.16),
        font=font,
        padding=sizing.button_padding,
    )
    _configure_button_style(
        style,
        "SummaryToggle.TButton",
        background=palette.panel_bg,
        foreground=palette.muted_fg,
        hover_background=palette.panel_alt_bg,
        pressed_background=palette.panel_bg,
        font=(str(UI_STYLE["font_family"]), max(8, int(UI_STYLE["font_size"]) - 3)),
        padding=sizing.summary_button_padding,
    )

    style.configure(
        "TEntry",
        fieldbackground=palette.entry_bg,
        foreground=fg,
        insertcolor=fg,
        bordercolor=palette.panel_border,
        lightcolor=palette.panel_border,
        darkcolor=palette.panel_border,
        font=font,
    )
    style.map(
        "TEntry",
        fieldbackground=[("active", palette.entry_hover), ("focus", palette.entry_hover)],
        bordercolor=[("focus", palette.panel_highlight)],
    )

    style.configure(
        "TCombobox",
        fieldbackground=palette.entry_bg,
        foreground=fg,
        background=palette.entry_bg,
        arrowcolor=fg,
        bordercolor=palette.panel_border,
        lightcolor=palette.panel_border,
        darkcolor=palette.panel_border,
        font=font,
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", palette.entry_bg), ("active", palette.entry_hover)],
        background=[("active", palette.entry_hover)],
        bordercolor=[("focus", palette.panel_highlight)],
    )
    root.option_add("*TCombobox*Listbox.font", f"{font[0]} {font[1]}")
    root.option_add("*TCombobox*Listbox.background", palette.listbox_bg)
    root.option_add("*TCombobox*Listbox.foreground", fg)
    root.option_add("*TCombobox*Listbox.selectBackground", palette.listbox_select_bg)
    root.option_add("*TCombobox*Listbox.selectForeground", fg)

    try:
        style.configure(
            "TSpinbox",
            fieldbackground=palette.entry_bg,
            foreground=fg,
            background=palette.entry_bg,
            arrowcolor=fg,
            arrowsize=sizing.spinbox_arrowsize,
            bordercolor=palette.panel_border,
            lightcolor=palette.panel_border,
            darkcolor=palette.panel_border,
            font=font,
        )
        style.map(
            "TSpinbox",
            fieldbackground=[("active", palette.entry_hover), ("focus", palette.entry_hover)],
            background=[("active", palette.entry_hover)],
            bordercolor=[("focus", palette.panel_highlight)],
        )
    except TclError:
        pass

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
        background=[("active", bg), ("selected", bg)],
        indicatorbackground=[
            ("selected", palette.check_active),
            ("active", palette.check_hover),
            ("disabled", palette.check_disabled),
        ],
        indicatorforeground=[("selected", fg), ("disabled", palette.muted_fg)],
    )

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
        borderwidth=0,
    )
    style.map(
        "Treeview.Heading",
        background=[("active", palette.panel_raised_bg)],
        foreground=[("active", fg)],
    )

    style.configure(
        "TNotebook",
        background=bg,
        borderwidth=0,
        tabmargins=(0, 0, 0, 0),
    )
    style.configure(
        "TNotebook.Tab",
        background=palette.tab_bg,
        foreground=palette.muted_fg,
        padding=sizing.notebook_tab_padding,
        font=font,
        borderwidth=0,
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", palette.tab_active_bg), ("active", palette.panel_alt_bg)],
        foreground=[("selected", fg), ("active", fg)],
    )

    style.configure(
        "TScrollbar",
        background=palette.panel_alt_bg,
        troughcolor=palette.panel_bg,
        arrowcolor=fg,
        bordercolor=palette.panel_border,
        darkcolor=palette.panel_alt_bg,
        lightcolor=palette.panel_alt_bg,
    )

    root.option_add("*Listbox.background", palette.listbox_bg)
    root.option_add("*Listbox.foreground", fg)
    root.option_add("*Listbox.selectBackground", palette.listbox_select_bg)
    root.option_add("*Listbox.selectForeground", fg)
    root.option_add("*Listbox.highlightThickness", 0)
    root.option_add("*Menu.background", palette.listbox_bg)
    root.option_add("*Menu.foreground", fg)
    root.option_add("*Menu.activeBackground", palette.listbox_select_bg)
    root.option_add("*Menu.activeForeground", fg)


def prepare_ttk_window(root: Misc) -> None:
    """Refresh the theme and reapply shared ttk styling on a window."""
    refresh_theme()
    configure_ttk_styles(root)


refresh_theme()
