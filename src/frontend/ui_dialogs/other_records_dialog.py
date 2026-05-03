"""Other records dialog: visits and free-form events."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from tkinter import BooleanVar, IntVar, StringVar, Text, Tk, Toplevel, messagebox, ttk
from typing import TYPE_CHECKING

from config import UI_STYLE
from config.theme import prepare_ttk_window
from core.context import get_app_service
from frontend.date_widgets import create_date_entry
from frontend.input_widgets import create_combobox, create_entry, create_spinbox
from frontend.text_widgets import configure_notes_widget
from frontend.window_utils import expand_window_size_to_requested_layout, place_window_centered
from i18n import t
from utils import DataStoreError, get_logger

logger = get_logger(__name__)

if TYPE_CHECKING:
    from core.service import AppService


def show_other_records_dialog(
    parent: Tk | Toplevel,
    app_service: AppService | None = None,
) -> None:
    """Show dialog for visits and custom event logs.

    Args:
        parent: Parent Tk window.
    """
    app_service = app_service or get_app_service()

    dlg = Toplevel(parent)
    prepare_ttk_window(dlg)
    dlg.title(t("menu.other_records"))
    dlg.resizable(width=True, height=True)
    dlg.configure(background=UI_STYLE["bg"])

    notebook = ttk.Notebook(dlg)
    notebook.pack(fill="both", padx=UI_STYLE["padding"], pady=UI_STYLE["padding"])

    visit_tab = ttk.Frame(notebook, padding=UI_STYLE["padding"])
    event_tab = ttk.Frame(notebook, padding=UI_STYLE["padding"])

    notebook.add(visit_tab, text=t("other.visits_tab"))
    notebook.add(event_tab, text=t("other.events_tab"))

    visit_save = _build_visit_tab(visit_tab, app_service)
    event_save = _build_event_tab(event_tab, app_service)

    button_frame = ttk.Frame(dlg)
    button_frame.pack(pady=6)

    def _save_current_tab() -> None:
        current_tab = notebook.select()
        if current_tab == str(visit_tab):
            visit_save()
        elif current_tab == str(event_tab):
            event_save()

    ttk.Button(button_frame, text=t("common.save"), command=_save_current_tab).pack(
        side="left",
        padx=4,
    )
    ttk.Button(button_frame, text=t("menu.close"), command=dlg.destroy).pack(side="left", padx=4)

    dlg.transient(parent)
    dlg.update_idletasks()
    pad = int(UI_STYLE["padding"])
    tab_req_width = max(visit_tab.winfo_reqwidth(), event_tab.winfo_reqwidth())
    notebook_req_width = notebook.winfo_reqwidth()
    notebook_req_height = notebook.winfo_reqheight()
    target_width = max(760, tab_req_width + (pad * 4), notebook_req_width + (pad * 2))
    target_height = max(360, notebook_req_height + button_frame.winfo_reqheight() + (pad * 4))
    target_width, target_height = expand_window_size_to_requested_layout(
        dlg,
        target_width,
        target_height,
    )
    dlg.minsize(target_width, target_height)
    place_window_centered(dlg, width=target_width, height=target_height)


def _build_visit_tab(frame: ttk.Frame, app_service: AppService) -> Callable[[], None]:
    """Create visit logging tab content."""
    visit_type_var = StringVar(value="medical")
    status_var = StringVar(value="")
    select_next_var = BooleanVar(value=False)
    wellbeing_enabled_var = BooleanVar(value=False)
    mood_var = IntVar(value=3)
    energy_var = IntVar(value=3)
    sleep_var = IntVar(value=3)
    side_effects_var = StringVar(value="")
    wellbeing_notes_var = StringVar(value="")

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

    def _toggle_next_date() -> None:
        if select_next_var.get():
            next_entry.grid(column=1, row=0, padx=(8, 0))
        else:
            next_entry.widget.grid_remove()

    next_date_frame = ttk.Frame(frame)
    next_date_frame.grid(column=0, row=2, columnspan=2, sticky="w", pady=4)
    ttk.Checkbutton(
        next_date_frame,
        text=t("other.select_next_date"),
        variable=select_next_var,
        command=_toggle_next_date,
    ).grid(column=0, row=0)
    next_entry = create_date_entry(next_date_frame, width=14)
    next_entry.set_date(date.today())
    _toggle_next_date()

    ttk.Label(frame, text=t("other.notes")).grid(column=0, row=3, sticky="nw", pady=4)
    notes = Text(frame, width=46, height=7)
    configure_notes_widget(notes)
    notes.grid(column=1, row=3, sticky="w", pady=4)

    wellbeing_frame = ttk.LabelFrame(frame, text=t("companion.wellbeing_section"))
    wellbeing_frame.grid(column=0, row=4, columnspan=2, sticky="ew", pady=(6, 4))
    ttk.Checkbutton(
        wellbeing_frame,
        text=t("companion.save_wellbeing_with_visit"),
        variable=wellbeing_enabled_var,
    ).grid(column=0, row=0, columnspan=2, sticky="w", pady=3)
    ttk.Label(wellbeing_frame, text=t("companion.wellbeing_mood")).grid(
        column=0, row=1, sticky="w", pady=2
    )
    create_spinbox(wellbeing_frame, from_=0, to=5, width=6, textvariable=mood_var).grid(
        column=1, row=1, sticky="w", pady=2
    )
    ttk.Label(wellbeing_frame, text=t("companion.wellbeing_energy")).grid(
        column=0, row=2, sticky="w", pady=2
    )
    create_spinbox(wellbeing_frame, from_=0, to=5, width=6, textvariable=energy_var).grid(
        column=1, row=2, sticky="w", pady=2
    )
    ttk.Label(wellbeing_frame, text=t("companion.wellbeing_sleep")).grid(
        column=0, row=3, sticky="w", pady=2
    )
    create_spinbox(wellbeing_frame, from_=0, to=5, width=6, textvariable=sleep_var).grid(
        column=1, row=3, sticky="w", pady=2
    )
    ttk.Label(wellbeing_frame, text=t("companion.wellbeing_side_effects")).grid(
        column=0, row=4, sticky="w", pady=2
    )
    create_entry(wellbeing_frame, textvariable=side_effects_var, width=32).grid(
        column=1, row=4, sticky="w", pady=2
    )
    ttk.Label(wellbeing_frame, text=t("other.notes")).grid(column=0, row=5, sticky="w", pady=2)
    create_entry(wellbeing_frame, textvariable=wellbeing_notes_var, width=32).grid(
        column=1, row=5, sticky="w", pady=2
    )

    ttk.Label(frame, textvariable=status_var, wraplength=680).grid(
        column=0, row=5, columnspan=2, sticky="w", pady=4
    )

    def _save_visit() -> None:
        try:
            next_date: str | None = (
                next_entry.get_date().isoformat() if select_next_var.get() else None
            )
            target_date = date_entry.get_date()
            app_service.add_visit_record(
                target_date=target_date,
                visit_type=visit_type_var.get(),
                completed=True,
                next_visit_date=next_date,
                notes=notes.get("1.0", "end").strip() or None,
            )
            if wellbeing_enabled_var.get():
                app_service.save_wellbeing_log(
                    log_id=None,
                    target_date=target_date.isoformat(),
                    mood=mood_var.get(),
                    energy=energy_var.get(),
                    sleep=sleep_var.get(),
                    side_effects=side_effects_var.get().strip() or None,
                    notes=wellbeing_notes_var.get().strip() or None,
                    linked_source="visit",
                )
            status_var.set(t("other.saved_visit"))
        except ValueError:
            messagebox.showerror(t("error.generic"), t("other.invalid_date"))
        except DataStoreError as exc:
            messagebox.showerror(t("error.generic"), str(exc))
        except Exception as exc:
            logger.exception("Visit save failed: %s", exc)
            messagebox.showerror(t("error.generic"), str(exc))

    return _save_visit


def _build_event_tab(frame: ttk.Frame, app_service: AppService) -> Callable[[], None]:
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
    notes = Text(frame, width=46, height=7)
    configure_notes_widget(notes)
    notes.grid(column=1, row=3, sticky="w", pady=4)

    ttk.Label(frame, textvariable=status_var, wraplength=680).grid(
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

    return _save_event
