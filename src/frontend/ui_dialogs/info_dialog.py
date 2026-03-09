"""Information dialog for TransTools."""

from __future__ import annotations

from tkinter import Toplevel, ttk

from config import UI_STYLE, __version__
from frontend.ui_dialogs.section_widgets import (
    create_collapsible_section,
    create_scrollable_content,
)
from frontend.window_utils import place_window_centered
from i18n import t


def show_info_dialog(parent) -> None:
    """Show information dialog."""
    dlg = Toplevel(parent)
    dlg.title(t("menu.info"))
    dlg.resizable(width=True, height=True)
    dlg.configure(background=UI_STYLE["bg"])

    pad = UI_STYLE["padding"]
    wraplength = 620
    scroll_container, _canvas, inner_frame = create_scrollable_content(dlg, UI_STYLE["bg"])

    create_collapsible_section(
        inner_frame,
        t("info.section_about"),
        t("info.content"),
        wraplength=wraplength,
        initially_expanded=True,
    ).pack(fill="x", padx=pad, pady=(pad, 0))

    create_collapsible_section(
        inner_frame,
        t("info.section_features"),
        t("info.features_content"),
        wraplength=wraplength,
        initially_expanded=True,
    ).pack(fill="x", padx=pad, pady=(pad, 0))

    create_collapsible_section(
        inner_frame,
        t("info.section_privacy"),
        t("info.privacy_content"),
        wraplength=wraplength,
        initially_expanded=False,
    ).pack(fill="x", padx=pad, pady=(pad, 0))

    create_collapsible_section(
        inner_frame,
        t("info.section_disclaimer"),
        t("info.disclaimer_content"),
        wraplength=wraplength,
        initially_expanded=False,
    ).pack(fill="x", padx=pad, pady=(pad, 0))

    create_collapsible_section(
        inner_frame,
        t("info.section_version"),
        t("info.version_content", version=__version__),
        wraplength=wraplength,
        initially_expanded=False,
    ).pack(fill="x", padx=pad, pady=(pad, 0))

    scroll_container.pack(fill="both", expand=True, padx=pad, pady=pad)
    ttk.Button(dlg, text=t("menu.close"), command=dlg.destroy).pack(pady=pad)

    dlg.protocol("WM_DELETE_WINDOW", dlg.destroy)
    dlg.transient(parent)
    dlg.minsize(520, 420)
    place_window_centered(dlg, width=1020, height=680)
