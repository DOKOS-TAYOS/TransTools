"""Medication register dialog."""

from __future__ import annotations

from datetime import date
from tkinter import BooleanVar, IntVar, StringVar, Text, Toplevel, messagebox, ttk

from config import UI_STYLE
from config.theme import prepare_ttk_window
from core.context import get_app_service
from frontend.date_widgets import create_date_entry
from frontend.input_widgets import create_entry, create_spinbox
from frontend.text_widgets import configure_notes_widget
from frontend.window_utils import expand_window_size_to_requested_layout, place_window_centered
from i18n import t
from utils import DataStoreError, get_logger

logger = get_logger(__name__)


def show_medication_dialog(parent, app_service=None) -> None:
    """Show medication register dialog.

    Args:
        parent: Parent Tk window.
    """
    app_service = app_service or get_app_service()
    health = app_service.get_health_config()

    dlg = Toplevel(parent)
    prepare_ttk_window(dlg)
    dlg.title(t("menu.medication_record"))
    dlg.resizable(width=False, height=False)
    dlg.configure(background=UI_STYLE["bg"])

    hour_var = StringVar(value="")
    dose_var = StringVar(value=health.get("medication_dose") or "")
    select_next_var = BooleanVar(value=False)
    wellbeing_enabled_var = BooleanVar(value=False)
    mood_var = IntVar(value=3)
    energy_var = IntVar(value=3)
    sleep_var = IntVar(value=3)
    side_effects_var = StringVar(value="")
    wellbeing_notes_var = StringVar(value="")

    frame = ttk.Frame(dlg, padding=UI_STYLE["padding"])
    ttk.Label(frame, text=t("medication.date")).grid(column=0, row=0, sticky="w", pady=3)
    date_entry = create_date_entry(frame, width=14)
    date_entry.set_date(date.today())
    date_entry.grid(column=1, row=0, sticky="w", pady=3)

    def _toggle_next_date() -> None:
        if select_next_var.get():
            next_entry.grid(column=1, row=0, padx=(8, 0))
        else:
            next_entry.widget.grid_remove()

    next_date_frame = ttk.Frame(frame)
    next_date_frame.grid(column=0, row=1, columnspan=2, sticky="w", pady=3)
    ttk.Checkbutton(
        next_date_frame,
        text=t("medication.select_next_date"),
        variable=select_next_var,
        command=_toggle_next_date,
    ).grid(column=0, row=0)
    next_entry = create_date_entry(next_date_frame, width=14)
    next_entry.set_date(date.today())
    _toggle_next_date()

    ttk.Label(frame, text=t("medication.hour")).grid(column=0, row=2, sticky="w", pady=3)
    create_entry(frame, textvariable=hour_var, width=14).grid(column=1, row=2, sticky="w", pady=3)

    ttk.Label(frame, text=t("medication.dose")).grid(column=0, row=3, sticky="w", pady=3)
    create_entry(frame, textvariable=dose_var, width=22).grid(column=1, row=3, sticky="w", pady=3)

    ttk.Label(frame, text=t("medication.notes")).grid(column=0, row=4, sticky="nw", pady=3)
    notes_text = Text(frame, width=34, height=5)
    configure_notes_widget(notes_text)
    notes_text.grid(column=1, row=4, sticky="w", pady=3)

    wellbeing_frame = ttk.LabelFrame(frame, text=t("companion.wellbeing_section"))
    wellbeing_frame.grid(column=0, row=5, columnspan=2, sticky="ew", pady=(8, 3))
    ttk.Checkbutton(
        wellbeing_frame,
        text=t("companion.save_wellbeing_with_medication"),
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
    create_entry(wellbeing_frame, textvariable=side_effects_var, width=28).grid(
        column=1, row=4, sticky="w", pady=2
    )
    ttk.Label(wellbeing_frame, text=t("other.notes")).grid(column=0, row=5, sticky="w", pady=2)
    create_entry(wellbeing_frame, textvariable=wellbeing_notes_var, width=28).grid(
        column=1, row=5, sticky="w", pady=2
    )

    status_var = StringVar(value="")
    ttk.Label(frame, textvariable=status_var).grid(
        column=0, row=6, columnspan=2, sticky="w", pady=3
    )

    def _save() -> None:
        try:
            wants_next = select_next_var.get()
            next_date: str | None = next_entry.get_date().isoformat() if wants_next else None
            target_date = date_entry.get_date()
            app_service.add_medication_record(
                target_date=target_date,
                taken=True,
                hour=hour_var.get().strip() or None,
                dose=dose_var.get().strip() or None,
                notes=notes_text.get("1.0", "end").strip() or None,
                next_medication_date=next_date,
                update_next_date=wants_next,
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
                    linked_source="medication",
                )
            status_var.set(t("medication.saved"))
        except ValueError:
            messagebox.showerror(t("error.generic"), t("medication.invalid_date"))
        except DataStoreError as exc:
            messagebox.showerror(t("error.generic"), str(exc))
        except Exception as exc:
            logger.exception("Medication save failed: %s", exc)
            messagebox.showerror(t("error.generic"), str(exc))

    ttk.Button(frame, text=t("common.save"), command=_save, width=UI_STYLE["button_width"]).grid(
        column=0, row=7, padx=4, pady=8
    )
    ttk.Button(
        frame, text=t("menu.close"), command=dlg.destroy, width=UI_STYLE["button_width"]
    ).grid(column=1, row=7, padx=4, pady=8)

    frame.pack(fill="both")
    dlg.transient(parent)
    dlg.update_idletasks()
    pad = int(UI_STYLE["padding"])
    target_width = max(520, frame.winfo_reqwidth() + (pad * 4))
    target_height = max(320, frame.winfo_reqheight() + (pad * 2))
    target_width, target_height = expand_window_size_to_requested_layout(
        dlg,
        target_width,
        target_height,
    )
    dlg.minsize(target_width, target_height)
    place_window_centered(dlg, width=target_width, height=target_height)
