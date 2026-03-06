"""Support contacts dialog."""

from __future__ import annotations

from tkinter import Toplevel, ttk

from config import UI_STYLE
from core.context import get_app_service
from frontend.window_utils import place_window_centered
from i18n import t


def show_contacts_dialog(parent) -> None:
    """Show support contacts grouped by national and region.

    Args:
        parent: Parent Tk window.
    """
    app_service = get_app_service()
    contacts = app_service.get_contacts()

    dlg = Toplevel(parent)
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
    dlg.minsize(760, 480)
    place_window_centered(dlg, width=900, height=620)


def _fill_contact_tree(parent, rows: list[dict]) -> None:
    """Render contact table in a frame."""
    columns = ("org", "description", "phone", "email", "web")
    tree = ttk.Treeview(parent, columns=columns, show="headings", height=14)
    tree.heading("org", text=t("contacts.org"))
    tree.heading("description", text=t("contacts.description"))
    tree.heading("phone", text=t("contacts.phone"))
    tree.heading("email", text=t("contacts.email"))
    tree.heading("web", text=t("contacts.web"))
    tree.column("org", width=180)
    tree.column("description", width=260)
    tree.column("phone", width=130)
    tree.column("email", width=200)
    tree.column("web", width=200)

    for row in rows:
        tree.insert(
            "",
            "end",
            values=(
                row.get("organization", ""),
                row.get("description", ""),
                row.get("phone", ""),
                row.get("email", ""),
                row.get("website", ""),
            ),
        )

    yscroll = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=yscroll.set)
    tree.pack(side="left", fill="both", expand=True)
    yscroll.pack(side="right", fill="y")


def _fill_regional_contacts(parent, regional: dict[str, list[dict]]) -> None:
    """Render nested regional contact notebooks."""
    notebook = ttk.Notebook(parent)
    notebook.pack(fill="both", expand=True)

    if not regional:
        frame = ttk.Frame(notebook, padding=UI_STYLE["padding"])
        ttk.Label(frame, text=t("contacts.no_data")).pack(anchor="w")
        notebook.add(frame, text=t("contacts.regional"))
        return

    for region, rows in sorted(regional.items(), key=lambda item: item[0].lower()):
        frame = ttk.Frame(notebook, padding=UI_STYLE["padding"])
        notebook.add(frame, text=region)
        _fill_contact_tree(frame, rows)

