"""Application information dialog (technical/product info)."""

from __future__ import annotations

from tkinter import Tk, Toplevel, ttk

from config import UI_STYLE, __version__
from config.theme import get_surface_palette, prepare_ttk_window
from frontend.ui_dialogs.section_widgets import (
    create_collapsible_section,
    create_scrollable_content,
)
from frontend.window_utils import place_window_centered
from i18n import t


def show_app_info_dialog(parent: Tk | Toplevel) -> None:
    """Show app information dialog."""
    dlg = Toplevel(parent)
    prepare_ttk_window(dlg)
    palette = get_surface_palette()
    dlg.title(t("menu.app_info"))
    dlg.resizable(width=True, height=True)
    dlg.configure(background=UI_STYLE["bg"])

    pad = UI_STYLE["padding"]
    wraplength = 920
    scroll_container, _canvas, inner_frame = create_scrollable_content(dlg, palette.panel_bg)

    create_collapsible_section(
        inner_frame,
        t("appinfo.section_about"),
        t("appinfo.content"),
        wraplength=wraplength,
        initially_expanded=True,
    ).pack(fill="x", padx=pad, pady=(pad, 0))

    create_collapsible_section(
        inner_frame,
        t("appinfo.section_privacy"),
        t("appinfo.privacy"),
        wraplength=wraplength,
        initially_expanded=True,
    ).pack(fill="x", padx=pad, pady=(pad, 0))

    create_collapsible_section(
        inner_frame,
        t("appinfo.section_usage"),
        t("appinfo.usage"),
        wraplength=wraplength,
        initially_expanded=False,
    ).pack(fill="x", padx=pad, pady=(pad, 0))

    create_collapsible_section(
        inner_frame,
        t("appinfo.section_license"),
        t("appinfo.license"),
        wraplength=wraplength,
        initially_expanded=False,
    ).pack(fill="x", padx=pad, pady=(pad, 0))

    create_collapsible_section(
        inner_frame,
        t("appinfo.section_version"),
        t("appinfo.version", version=__version__),
        wraplength=wraplength,
        initially_expanded=False,
    ).pack(fill="x", padx=pad, pady=(pad, 0))

    scroll_container.pack(fill="both", expand=True, padx=pad, pady=pad)
    ttk.Button(
        dlg,
        text=t("menu.close"),
        command=dlg.destroy,
        style="Utility.TButton",
    ).pack(pady=pad)

    dlg.protocol("WM_DELETE_WINDOW", dlg.destroy)
    dlg.transient(parent)
    dlg.minsize(760, 760)
    place_window_centered(dlg, width=1120, height=840)
