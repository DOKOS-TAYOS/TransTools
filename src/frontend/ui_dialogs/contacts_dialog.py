"""Support contacts dialog."""

from __future__ import annotations

import tkinter as tk
import webbrowser
from textwrap import fill
from tkinter import Toplevel, ttk

from config import UI_STYLE
from config.theme import prepare_ttk_window
from core.context import get_app_service
from frontend.window_utils import place_window_centered
from i18n import t


def _wrap_description(value: str) -> str:
    """Wrap long descriptions to fit inside the description column."""
    text = value.strip()
    if not text:
        return ""
    return fill(text, width=30)


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


def show_contacts_dialog(parent, app_service=None) -> None:
    """Show support contacts grouped by national and region.

    Args:
        parent: Parent Tk window.
    """
    app_service = app_service or get_app_service()
    contacts = app_service.get_contacts()

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

    ttk.Button(dlg, text=t("menu.close"), command=dlg.destroy).pack(pady=8)
    dlg.transient(parent)
    dlg.minsize(1120, 520)
    place_window_centered(dlg, width=1280, height=680)


def _create_contact_tree(parent) -> ttk.Treeview:
    """Create a contact table widget."""
    style = ttk.Style(parent)
    style.configure(
        "Contacts.Treeview",
        rowheight=max(48, (UI_STYLE["font_size"] * 3) + 8),
    )
    columns = ("org", "type", "description", "phone", "email", "web")
    tree = ttk.Treeview(
        parent,
        columns=columns,
        show="headings",
        height=14,
        style="Contacts.Treeview",
    )
    tree.heading("org", text=t("contacts.org"))
    tree.heading("type", text=t("contacts.type"))
    tree.heading("description", text=t("contacts.description"))
    tree.heading("phone", text=t("contacts.phone"))
    tree.heading("email", text=t("contacts.email"))
    tree.heading("web", text=t("contacts.web"))
    tree.column("org", width=170)
    tree.column("type", width=130)
    tree.column("description", width=220)
    tree.column("phone", width=130)
    tree.column("email", width=180)
    tree.column("web", width=180)
    return tree


def _populate_contact_tree(tree: ttk.Treeview, rows: list[dict]) -> None:
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


def _fill_contact_tree(parent, rows: list[dict]) -> None:
    """Render contact table in a frame."""
    tree = _create_contact_tree(parent)
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
    tree.configure(yscrollcommand=yscroll.set)
    tree.bind("<Double-1>", _open_row_website)
    tree.pack(side="left", fill="both", expand=True)
    yscroll.pack(side="right", fill="y")


def _fill_regional_contacts(parent, regional: dict[str, list[dict]]) -> None:
    """Render regional contacts with selector on the left and table on the right."""
    if not regional:
        frame = ttk.Frame(parent, padding=UI_STYLE["padding"])
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text=t("contacts.no_data")).pack(anchor="w")
        return

    regions = sorted(regional.items(), key=lambda item: item[0].lower())
    container = ttk.Frame(parent)
    container.pack(fill="both", expand=True)
    selector_frame = ttk.Frame(container)
    table_frame = ttk.Frame(container)
    selector_frame.pack(side="left", fill="y", padx=(0, UI_STYLE["padding"]))
    table_frame.pack(side="left", fill="both", expand=True)

    ttk.Label(selector_frame, text=t("contacts.regional")).pack(anchor="w", pady=(0, 6))

    region_list = tk.Listbox(
        selector_frame,
        exportselection=False,
        width=24,
        height=18,
        background=UI_STYLE["bg"],
        foreground=UI_STYLE["fg"],
        selectbackground=UI_STYLE["button_bg"],
        selectforeground=UI_STYLE["fg"],
        highlightthickness=0,
        relief="flat",
        font=(UI_STYLE["font_family"], UI_STYLE["font_size"]),
    )
    region_list.pack(fill="y", expand=True)

    tree = _create_contact_tree(table_frame)

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
    tree.configure(yscrollcommand=yscroll.set)
    tree.bind("<Double-1>", _open_row_website)
    tree.pack(side="left", fill="both", expand=True)
    yscroll.pack(side="right", fill="y")

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
