"""Adaptive habits checklist dialog."""

from __future__ import annotations

from datetime import date
from tkinter import BooleanVar, StringVar, Toplevel, messagebox, ttk

from config import UI_STYLE
from core.context import get_app_service
from frontend.date_widgets import create_date_entry
from frontend.window_utils import place_window_centered
from i18n import t
from utils import DataStoreError, get_logger

logger = get_logger(__name__)


def show_habits_dialog(parent, app_service=None) -> None:
    """Show habits checklist dialog.

    Args:
        parent: Parent Tk window.
    """
    app_service = app_service or get_app_service()
    dlg = Toplevel(parent)
    dlg.title(t("menu.habits"))
    dlg.resizable(width=True, height=True)
    dlg.configure(background=UI_STYLE["bg"])

    frame = ttk.Frame(dlg, padding=UI_STYLE["padding"])
    frame.pack(fill="both", expand=True)

    ttk.Label(frame, text=t("habits.date")).grid(column=0, row=0, sticky="w", pady=4)
    date_entry = create_date_entry(frame, width=14)
    date_entry.set_date(date.today())
    date_entry.grid(column=1, row=0, sticky="w", pady=4)

    hint_var = StringVar(value=t("habits.hint"))
    ttk.Label(frame, textvariable=hint_var, wraplength=680).grid(
        column=0, row=1, columnspan=2, sticky="w", pady=4
    )

    checklist_frame = ttk.Frame(frame)
    checklist_frame.grid(column=0, row=2, columnspan=2, sticky="nsew", pady=4)

    row_vars: dict[str, BooleanVar] = {}
    status_var = StringVar(value="")
    ttk.Label(frame, textvariable=status_var, wraplength=680).grid(
        column=0, row=3, columnspan=2, sticky="w", pady=4
    )

    frame.rowconfigure(2, weight=1)
    frame.columnconfigure(1, weight=1)

    current_shown_ids: list[str] = []

    def _render_for_day() -> None:
        nonlocal current_shown_ids
        for child in checklist_frame.winfo_children():
            child.destroy()
        row_vars.clear()

        try:
            selected = app_service.get_habit_selection_for_date(date_entry.get_date())
        except ValueError:
            messagebox.showerror(t("error.generic"), t("habits.invalid_date"))
            return

        current_shown_ids = [habit["id"] for habit in selected.shown_habits]
        if not selected.shown_habits:
            ttk.Label(checklist_frame, text=t("habits.no_data")).pack(anchor="w")
            return

        hint_var.set(
            t(
                "habits.target_count",
                count=str(len(selected.shown_habits)),
            )
        )
        for habit in selected.shown_habits:
            var = BooleanVar(value=habit["id"] in selected.completed_habits)
            row_vars[habit["id"]] = var
            habit_label = t("habit.name." + habit["id"])
            ttk.Checkbutton(
                checklist_frame,
                text=habit_label,
                variable=var,
            ).pack(anchor="w", pady=2)

    def _save() -> None:
        completed = [habit_id for habit_id, var in row_vars.items() if var.get()]
        try:
            app_service.save_habit_log(
                target_date=date_entry.get_date(),
                shown_habits=current_shown_ids,
                completed_habits=completed,
            )
            status_var.set(
                t("habits.saved", done=str(len(completed)), total=str(len(current_shown_ids)))
            )
        except ValueError:
            messagebox.showerror(t("error.generic"), t("habits.invalid_date"))
        except DataStoreError as exc:
            messagebox.showerror(t("error.generic"), str(exc))
        except Exception as exc:
            logger.exception("Habit save failed: %s", exc)
            messagebox.showerror(t("error.generic"), str(exc))

    date_widget = getattr(date_entry, "widget", None)
    if date_widget is not None:
        date_widget.bind("<<DateEntrySelected>>", lambda _event: _render_for_day())

    ttk.Button(frame, text=t("common.save"), command=_save).grid(
        column=0,
        row=4,
        pady=8,
        sticky="w",
    )
    ttk.Button(frame, text=t("menu.close"), command=dlg.destroy).grid(
        column=1,
        row=4,
        pady=8,
        sticky="w",
    )

    _render_for_day()

    dlg.transient(parent)
    dlg.minsize(620, 420)
    place_window_centered(dlg, width=700, height=520)
