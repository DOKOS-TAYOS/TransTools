"""Support contacts dialog."""

from __future__ import annotations

import tkinter as tk
import webbrowser
from dataclasses import dataclass
from textwrap import fill
from tkinter import Tk, Toplevel, ttk
from typing import Any

from config import UI_STYLE
from config.theme import get_surface_palette, prepare_ttk_window
from core.context import get_app_service
from core.service import AppService
from frontend.window_utils import TreeColumnSpec, apply_tree_column_specs, place_window_centered
from i18n import t

CONTACT_DESCRIPTION_WRAP_WIDTH = 36
CONTACT_MIN_DESCRIPTION_LINES = 4
CONTACT_ROW_LINE_HEIGHT_EXTRA = 8
CONTACT_ROW_VERTICAL_PADDING = 10
CONTACT_MIN_ROWHEIGHT = 80


def _wrap_description(
    value: str,
    wrap_width: int = CONTACT_DESCRIPTION_WRAP_WIDTH,
) -> str:
    """Wrap long descriptions to fit inside the description column."""
    text = value.strip()
    if not text:
        return ""
    return fill(text, width=wrap_width)


@dataclass(frozen=True)
class ContactTableGeometry:
    """Sizing values used by the contacts tables."""

    rowheight: int
    description_lines: int
    style_name: str


def _count_wrapped_description_lines(
    value: str,
    wrap_width: int = CONTACT_DESCRIPTION_WRAP_WIDTH,
) -> int:
    """Return how many rendered lines a wrapped description will occupy."""
    wrapped = _wrap_description(value, wrap_width=wrap_width)
    if not wrapped:
        return 1
    return len(wrapped.splitlines())


def get_contact_tree_rowheight(
    font_size: int,
    description_lines: int = CONTACT_MIN_DESCRIPTION_LINES,
) -> int:
    """Return a row height that can hold wrapped contact descriptions."""
    normalized_lines = max(CONTACT_MIN_DESCRIPTION_LINES, int(description_lines))
    line_height = max(int(font_size) + CONTACT_ROW_LINE_HEIGHT_EXTRA, 22)
    return max(
        CONTACT_MIN_ROWHEIGHT,
        (line_height * normalized_lines) + CONTACT_ROW_VERTICAL_PADDING,
    )


def build_contact_table_geometry(
    rows: list[dict[str, str]],
    font_size: int,
) -> ContactTableGeometry:
    """Return row sizing tuned to the longest wrapped description in the table."""
    description_lines = max(
        (_count_wrapped_description_lines(str(row.get("description", ""))) for row in rows),
        default=CONTACT_MIN_DESCRIPTION_LINES,
    )
    normalized_lines = max(CONTACT_MIN_DESCRIPTION_LINES, description_lines)
    rowheight = get_contact_tree_rowheight(
        font_size=font_size,
        description_lines=normalized_lines,
    )
    return ContactTableGeometry(
        rowheight=rowheight,
        description_lines=normalized_lines,
        style_name=f"Contacts{rowheight}.Treeview",
    )


def build_contact_tree_column_specs() -> tuple[TreeColumnSpec, ...]:
    """Return explicit column widths for the contacts tables."""
    return (
        TreeColumnSpec("org", width=240, minwidth=220, anchor="w", stretch=False),
        TreeColumnSpec("type", width=150, minwidth=140, anchor="w", stretch=False),
        TreeColumnSpec("description", width=380, minwidth=320, anchor="w", stretch=True),
        TreeColumnSpec("phone", width=150, minwidth=140, anchor="w", stretch=False),
        TreeColumnSpec("email", width=280, minwidth=260, anchor="w", stretch=False),
        TreeColumnSpec("web", width=250, minwidth=240, anchor="w", stretch=False),
    )


def _normalize_web_url(value: str) -> str | None:
    """Normalize a contact website URL for browser opening."""
    url = value.strip()
    if not url:
        return None
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    return url


def _contact_type_label(value: object) -> str:
    """Map a stored contact type to a translated short label."""
    contact_type = str(value).strip()
    if not contact_type:
        return ""
    return t(f"contacts.type.{contact_type}")


def show_contacts_dialog(parent: Tk | Toplevel, app_service: AppService | None = None) -> None:
    """Show support contacts grouped by national and region.

    Args:
        parent: Parent Tk window.
    """
    resolved_app_service = app_service if app_service is not None else get_app_service()
    contacts = resolved_app_service.get_contacts()

    dlg = Toplevel(parent)
    prepare_ttk_window(dlg)
    dlg.title(t("menu.info_contacts"))
    dlg.resizable(width=True, height=True)
    dlg.configure(background=UI_STYLE["bg"])

    notebook = ttk.Notebook(dlg)
    notebook.pack(fill="both", expand=True, padx=UI_STYLE["padding"], pady=UI_STYLE["padding"])

    national_tab = ttk.Frame(notebook, padding=UI_STYLE["padding"])
    regional_tab = ttk.Frame(notebook, padding=UI_STYLE["padding"])
    notebook.add(national_tab, text=t("contacts.national"))
    notebook.add(regional_tab, text=t("contacts.regional"))

    _fill_contact_tree(
        national_tab,
        contacts.get("national", []),
    )
    _fill_regional_contacts(regional_tab, contacts.get("regional", {}))

    ttk.Button(dlg, text=t("menu.close"), command=dlg.destroy, style="Utility.TButton").pack(pady=8)
    dlg.transient(parent)
    dlg.minsize(1200, 540)
    place_window_centered(dlg, width=1440, height=700)


def _create_contact_tree(parent: Any, rows: list[dict[str, str]]) -> ttk.Treeview:
    """Create a contact table widget."""
    geometry = build_contact_table_geometry(
        rows=rows,
        font_size=int(UI_STYLE["font_size"]),
    )
    style = ttk.Style(parent)
    style.configure(
        geometry.style_name,
        rowheight=geometry.rowheight,
    )
    columns = ("org", "type", "description", "phone", "email", "web")
    tree = ttk.Treeview(
        parent,
        columns=columns,
        show="headings",
        height=14,
        style=geometry.style_name,
    )
    tree.heading("org", text=t("contacts.org"))
    tree.heading("type", text=t("contacts.type"))
    tree.heading("description", text=t("contacts.description"))
    tree.heading("phone", text=t("contacts.phone"))
    tree.heading("email", text=t("contacts.email"))
    tree.heading("web", text=t("contacts.web"))
    apply_tree_column_specs(tree, build_contact_tree_column_specs())
    return tree


def _populate_contact_tree(tree: ttk.Treeview, rows: list[dict[str, str]]) -> None:
    """Replace contact table rows."""
    for item in tree.get_children():
        tree.delete(item)

    for row in rows:
        tree.insert(
            "",
            "end",
            values=(
                row.get("organization", ""),
                _contact_type_label(row.get("type", "")),
                _wrap_description(str(row.get("description", ""))),
                row.get("phone", ""),
                row.get("email", ""),
                row.get("website", ""),
            ),
        )


def _fill_contact_tree(parent: Any, rows: list[dict[str, str]]) -> None:
    """Render contact table in a frame."""
    parent.columnconfigure(0, weight=1)
    parent.rowconfigure(0, weight=1)
    tree = _create_contact_tree(parent, rows)
    _populate_contact_tree(tree, rows)

    def _open_row_website(_event=None) -> None:
        """Open the selected row website in the browser when available."""
        selected = tree.focus()
        if not selected:
            return
        values = tree.item(selected, "values")
        if not values or len(values) < 6:
            return
        url = _normalize_web_url(str(values[5]))
        if url:
            webbrowser.open(url)

    yscroll = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
    xscroll = ttk.Scrollbar(parent, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
    tree.bind("<Double-1>", _open_row_website)
    tree.grid(column=0, row=0, sticky="nsew")
    yscroll.grid(column=1, row=0, sticky="ns")
    xscroll.grid(column=0, row=1, sticky="ew")


def _fill_regional_contacts(parent: Any, regional: dict[str, list[dict[str, str]]]) -> None:
    """Render regional contacts with selector on the left and table on the right."""
    if not regional:
        frame = ttk.Frame(parent, padding=UI_STYLE["padding"])
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text=t("contacts.no_data")).pack(anchor="w")
        return

    regions = sorted(regional.items(), key=lambda item: item[0].lower())
    palette = get_surface_palette()
    container = ttk.Frame(parent)
    container.pack(fill="both", expand=True)
    selector_frame = ttk.Frame(container)
    table_frame = ttk.Frame(container)
    selector_frame.pack(side="left", fill="y", padx=(0, UI_STYLE["padding"]))
    table_frame.pack(side="left", fill="both", expand=True)
    table_frame.columnconfigure(0, weight=1)
    table_frame.rowconfigure(0, weight=1)

    ttk.Label(selector_frame, text=t("contacts.regional")).pack(anchor="w", pady=(0, 6))

    region_list = tk.Listbox(
        selector_frame,
        exportselection=False,
        width=24,
        height=18,
        background=palette.listbox_bg,
        foreground=UI_STYLE["fg"],
        selectbackground=palette.listbox_select_bg,
        selectforeground=UI_STYLE["fg"],
        highlightbackground=palette.listbox_border,
        highlightthickness=0,
        relief="flat",
        font=(UI_STYLE["font_family"], UI_STYLE["font_size"]),
    )
    region_list.pack(fill="y", expand=True)

    all_regional_rows = [row for _region_name, region_rows in regions for row in region_rows]
    tree = _create_contact_tree(table_frame, all_regional_rows)

    def _open_row_website(_event=None) -> None:
        """Open the selected row website in the browser when available."""
        selected = tree.focus()
        if not selected:
            return
        values = tree.item(selected, "values")
        if not values or len(values) < 6:
            return
        url = _normalize_web_url(str(values[5]))
        if url:
            webbrowser.open(url)

    yscroll = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    xscroll = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
    tree.bind("<Double-1>", _open_row_website)
    tree.grid(column=0, row=0, sticky="nsew")
    yscroll.grid(column=1, row=0, sticky="ns")
    xscroll.grid(column=0, row=1, sticky="ew")

    region_names = [region for region, _rows in regions]

    def _render_selected_region(_event=None) -> None:
        """Refresh the right table with the selected region rows."""
        selection = region_list.curselection()
        if not selection:
            return
        region_name = region_names[selection[0]]
        _populate_contact_tree(tree, regional.get(region_name, []))

    for region_name in region_names:
        region_list.insert("end", region_name)

    region_list.bind("<<ListboxSelect>>", _render_selected_region)
    region_list.selection_set(0)
    _render_selected_region()
