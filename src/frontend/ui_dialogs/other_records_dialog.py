"""Other records dialog: visits and free-form events."""

from __future__ import annotations

from datetime import date
from tkinter import BooleanVar, StringVar, Text, Toplevel, messagebox, ttk

from config import UI_STYLE
from core.context import get_app_service
from frontend.date_widgets import create_date_entry
from frontend.input_widgets import create_combobox, create_entry
from frontend.window_utils import place_window_centered
from i18n import t
from utils import DataStoreError, get_logger

logger = get_logger(__name__)


def show_other_records_dialog(parent) -> None:
    """Show dialog for visits and custom event logs.

    Args:
        parent: Parent Tk window.
    """
    app_service = get_app_service()

    dlg = Toplevel(parent)
    dlg.title(t("menu.other_records"))
    dlg.resizable(width=True, height=True)
    dlg.configure(background=UI_STYLE["bg"])

    notebook = ttk.Notebook(dlg)
    notebook.pack(fill="both", expand=True, padx=UI_STYLE["padding"], pady=UI_STYLE["padding"])

    visit_tab = ttk.Frame(notebook, padding=UI_STYLE["padding"])
    event_tab = ttk.Frame(notebook, padding=UI_STYLE["padding"])

    notebook.add(visit_tab, text=t("other.visits_tab"))
    notebook.add(event_tab, text=t("other.events_tab"))

    _build_visit_tab(visit_tab, app_service)
    _build_event_tab(event_tab, app_service)

    ttk.Button(dlg, text=t("menu.close"), command=dlg.destroy).pack(pady=6)
    dlg.transient(parent)
    dlg.minsize(620, 420)
    place_window_centered(dlg, width=760, height=520)


def _build_visit_tab(frame, app_service) -> None:
    """Create visit logging tab content."""
    visit_type_var = StringVar(value="medical")
    completed_var = BooleanVar(value=True)
    status_var = StringVar(value="")

    ttk.Label(frame, text=t("other.visit_date")).grid(column=0, row=0, sticky="w", pady=4)
    date_entry = create_date_entry(frame, width=14)
    date_entry.set_date(date.today())
    date_entry.grid(column=1, row=0, sticky="w", pady=4)

    ttk.Label(frame, text=t("other.visit_type")).grid(column=0, row=1, sticky="w", pady=4)
    create_combobox(
        frame,
        textvariable=visit_type_var,
        values=[("medical"), ("psychology")],
        state="readonly",
        width=18,
    ).grid(column=1, row=1, sticky="w", pady=4)

    ttk.Checkbutton(frame, text=t("other.visit_completed"), variable=completed_var).grid(
        column=0, row=2, columnspan=2, sticky="w", pady=4
    )

    ttk.Label(frame, text=t("other.visit_next_date")).grid(column=0, row=3, sticky="w", pady=4)
    next_entry = create_date_entry(frame, width=14)
    next_entry.set_date(date.today())
    next_entry.grid(column=1, row=3, sticky="w", pady=4)

    ttk.Label(frame, text=t("other.notes")).grid(column=0, row=4, sticky="nw", pady=4)
    notes = Text(frame, width=46, height=6)
    notes.grid(column=1, row=4, sticky="w", pady=4)

    ttk.Label(frame, textvariable=status_var, wraplength=520).grid(
        column=0, row=5, columnspan=2, sticky="w", pady=4
    )

    def _save_visit() -> None:
        try:
            app_service.add_visit_record(
                target_date=date_entry.get_date(),
                visit_type=visit_type_var.get(),
                completed=bool(completed_var.get()),
                next_visit_date=next_entry.get_date().isoformat(),
                notes=notes.get("1.0", "end").strip() or None,
            )
            status_var.set(t("other.saved_visit"))
        except ValueError:
            messagebox.showerror(t("error.generic"), t("other.invalid_date"))
        except DataStoreError as exc:
            messagebox.showerror(t("error.generic"), str(exc))
        except Exception as exc:
            logger.exception("Visit save failed: %s", exc)
            messagebox.showerror(t("error.generic"), str(exc))

    ttk.Button(frame, text=t("common.save"), command=_save_visit).grid(column=0, row=6, pady=8)


def _build_event_tab(frame, app_service) -> None:
    """Create free event logging tab content."""
    category_var = StringVar(value="general")
    tags_var = StringVar(value="")
    status_var = StringVar(value="")

    ttk.Label(frame, text=t("other.event_date")).grid(column=0, row=0, sticky="w", pady=4)
    date_entry = create_date_entry(frame, width=14)
    date_entry.set_date(date.today())
    date_entry.grid(column=1, row=0, sticky="w", pady=4)

    ttk.Label(frame, text=t("other.category")).grid(column=0, row=1, sticky="w", pady=4)
    create_entry(frame, textvariable=category_var, width=25).grid(
        column=1,
        row=1,
        sticky="w",
        pady=4,
    )

    ttk.Label(frame, text=t("other.tags")).grid(column=0, row=2, sticky="w", pady=4)
    create_entry(frame, textvariable=tags_var, width=35).grid(
        column=1,
        row=2,
        sticky="w",
        pady=4,
    )

    ttk.Label(frame, text=t("other.notes")).grid(column=0, row=3, sticky="nw", pady=4)
    notes = Text(frame, width=46, height=8)
    notes.grid(column=1, row=3, sticky="w", pady=4)

    ttk.Label(frame, textvariable=status_var, wraplength=520).grid(
        column=0, row=4, columnspan=2, sticky="w", pady=4
    )

    def _save_event() -> None:
        text = notes.get("1.0", "end").strip()
        if not text:
            messagebox.showwarning(t("error.generic"), t("other.notes_required"))
            return
        try:
            app_service.add_other_event(
                target_date=date_entry.get_date(),
                category=category_var.get().strip() or "general",
                tags_raw=tags_var.get().strip() or None,
                notes=text,
            )
            status_var.set(t("other.saved_event"))
            notes.delete("1.0", "end")
        except ValueError:
            messagebox.showerror(t("error.generic"), t("other.invalid_date"))
        except DataStoreError as exc:
            messagebox.showerror(t("error.generic"), str(exc))
        except Exception as exc:
            logger.exception("Event save failed: %s", exc)
            messagebox.showerror(t("error.generic"), str(exc))

    ttk.Button(frame, text=t("common.save"), command=_save_event).grid(column=0, row=5, pady=8)
